"""Immutable graph revisions, project previews, and Unity staging."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from threading import Lock
from uuid import uuid4

from mm_mcp.authoring import describe_graph, patch_graph
from mm_mcp.config import Config
from mm_mcp.material_feedback import build_material_feedback
from mm_mcp.unity_export import (
    OVERLAY,
    PROFILE,
    bake_metric_surface,
    load_metric_surface_project,
    stage_metric_surface_change,
)
from mm_mcp.validator import validate_graph

_DIGEST = re.compile(r"[a-f0-9]{64}")
_PREVIEW_ID = re.compile(r"[a-f0-9]{32}")
_NATIVE_RENDER_LOCK = Lock()


class ProjectWorkflowError(ValueError):
    def __init__(self, code: str, message: str, *, where: str = "", problems: list | None = None):
        super().__init__(message)
        self.code = code
        self.where = where
        self.problems = problems


def approved_source(path: str | Path, cfg: Config) -> Path:
    """Resolve an explicitly approved project source, including symlink targets."""
    source = Path(path).resolve()
    if not any(source.is_relative_to(Path(root).resolve()) for root in cfg.project_read_roots):
        raise ProjectWorkflowError(
            "project_source_denied",
            "Path is outside MM_PROJECT_READ_ROOTS. Register the source directory in the server configuration.",
            where=str(path),
        )
    return source


def is_project_source(path: str, cfg: Config) -> bool:
    source = Path(path).resolve()
    return any(source.is_relative_to(Path(root).resolve()) for root in cfg.project_read_roots)


def _store(cfg: Config, name: str) -> Path:
    if not cfg.project_stage_root:
        raise ProjectWorkflowError("staging_unconfigured", "Set MM_PROJECT_STAGE_ROOT to a dedicated staging directory.")
    root = Path(cfg.project_stage_root).resolve()
    directory = root / name
    if directory.resolve() != directory:
        raise ProjectWorkflowError("invalid_staging_directory", "Staging subdirectories cannot be symlinks.", where=str(directory))
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _json_bytes(data: dict) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _graph(raw: bytes) -> dict:
    graph = json.loads(raw)
    if not isinstance(graph, dict):
        raise ProjectWorkflowError("invalid_graph", "The .ptex root must be an object.")
    return graph


def _save_revision(raw: bytes, cfg: Config) -> str:
    digest = hashlib.sha256(raw).hexdigest()
    directory = _store(cfg, "graphs")
    destination = directory / (digest + ".ptex")
    if destination.is_file() and not destination.is_symlink() and destination.read_bytes() == raw:
        return digest
    with tempfile.TemporaryDirectory(dir=directory, prefix=".revision-") as temporary:
        draft = Path(temporary) / "graph.ptex"
        draft.write_bytes(raw)
        draft.replace(destination)
    return digest


def _load_revision(revision: str, cfg: Config) -> bytes:
    if not _DIGEST.fullmatch(revision):
        raise ProjectWorkflowError("invalid_revision", "Use the revision ID returned when opening or patching a graph.")
    path = _store(cfg, "graphs") / (revision + ".ptex")
    if path.is_symlink() or not path.is_file():
        raise ProjectWorkflowError("revision_not_found", "Graph revision is unavailable in this server's staging directory.", where=revision)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != revision:
        raise ProjectWorkflowError("revision_corrupted", "Stored graph revision failed its SHA-256 check.", where=revision)
    return raw


def _validate_for_export(graph: dict, catalog: dict) -> list:
    problems = validate_graph(graph, catalog, strict=True)
    if any(problem["severity"] == "error" for problem in problems):
        raise ProjectWorkflowError("graph_validation_failed", "The graph has blocking validation errors.", problems=problems)
    return problems


def open_project_graph(path: str, cfg: Config, catalog: dict) -> dict:
    source = approved_source(path, cfg)
    if source.suffix.lower() != ".ptex":
        raise ProjectWorkflowError("invalid_graph_path", "Choose a .ptex source file.", where=str(source))
    raw = source.read_bytes()
    graph = _graph(raw)
    problems = validate_graph(graph, catalog, strict=True)
    if any(problem["severity"] == "error" for problem in problems):
        raise ProjectWorkflowError("graph_validation_failed", "The graph has blocking validation errors.", where=str(source), problems=problems)
    description = describe_graph(graph, catalog)
    return {
        "ok": True,
        "path": str(source),
        "revision": _save_revision(raw, cfg),
        "problems": problems,
        **description,
    }


def apply_project_patch(revision: str, edits: list[dict], cfg: Config, catalog: dict) -> dict:
    raw = _load_revision(revision, cfg)
    graph = _graph(raw)
    result = patch_graph(graph, edits, catalog)
    updated = raw if result["graph"] == graph else _json_bytes(result["graph"])
    return {
        "ok": True,
        "previous_revision": revision,
        "revision": _save_revision(updated, cfg),
        "diff": result["diff"],
    }


def native_binary(cfg: Config) -> Path:
    if not cfg.native_binary or not _DIGEST.fullmatch(cfg.native_binary_sha256):
        raise ProjectWorkflowError(
            "native_backend_unconfigured",
            "Set MM_NATIVE_BINARY and MM_NATIVE_BINARY_SHA256 to a pinned standalone Material Maker executable.",
        )
    path = Path(cfg.native_binary).resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ProjectWorkflowError("native_backend_unavailable", "Configured Material Maker executable is unavailable.", where=str(path))
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != cfg.native_binary_sha256:
        raise ProjectWorkflowError("native_backend_pin_mismatch", "Material Maker executable SHA-256 differs from the configured pin.", where=str(path))
    return path


def _engine_version(binary: str | Path) -> str:
    result = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=10, check=True)
    return result.stdout.strip() or result.stderr.strip()


def project_capabilities(cfg: Config, project_path: str | None = None) -> dict:
    native = {"backend": "material_maker_app", "available": False}
    try:
        binary = native_binary(cfg)
        native.update(
            available=True,
            executable=str(binary),
            engine_version=_engine_version(binary),
            sha256=cfg.native_binary_sha256,
            export_profiles=[{"id": PROFILE, "native_target": "Unity/URP"}],
        )
    except (ProjectWorkflowError, OSError, subprocess.SubprocessError) as exc:
        native["message"] = str(exc)
    godot = {"backend": "godot_source_checkout", "project_path": cfg.project_path}
    try:
        godot["engine_version"] = _engine_version(cfg.console_binary)
    except (OSError, subprocess.SubprocessError) as exc:
        godot["message"] = str(exc)
    access = {"read_roots": cfg.project_read_roots, "staging_root": cfg.project_stage_root or None}
    if project_path is not None:
        try:
            source = approved_source(project_path, cfg)
            access.update(path=str(source), source_readable=source.exists() and os.access(source, os.R_OK))
        except ProjectWorkflowError as exc:
            access.update(path=project_path, source_readable=False, message=str(exc))
    return {"ok": True, "access": access, "render_backends": [godot, native]}


def make_project_preview(
    revision: str, project_root: str, family_id: str, profile: str, cfg: Config, catalog: dict
) -> dict:
    if profile != PROFILE:
        raise ProjectWorkflowError("unknown_profile", "Choose a profile reported by project_capabilities.", where=profile)
    binary = native_binary(cfg)
    root = approved_source(project_root, cfg)
    raw = _load_revision(revision, cfg)
    problems = _validate_for_export(_graph(raw), catalog)
    project = load_metric_surface_project(root, family_id)
    baseline = {record["role"]: root / record["path"] for record in project.family["maps"]}
    previews = _store(cfg, "previews")
    preview_id = uuid4().hex
    with tempfile.TemporaryDirectory(dir=previews, prefix=".working-") as temporary:
        draft = Path(temporary) / "preview"
        draft.mkdir()
        with _NATIVE_RENDER_LOCK:
            receipt = bake_metric_surface(
                raw,
                project=project,
                binary=binary,
                binary_sha256=cfg.native_binary_sha256,
                stage_path=draft,
            )
        candidate = {record["role"]: draft / OVERLAY / record["path"] for record in receipt["maps"]}
        feedback = build_material_feedback(
            candidate,
            draft / "preview.png",
            repeat_metres=receipt["repeatMetres"],
            height_range_metres=receipt["heightRangeMetres"],
            baseline_maps=baseline,
        )
        # Record relative artifact paths so the preview can be copied as a unit.
        feedback["image"] = "preview.png"
        metadata = {
            "profile": profile,
            "revision": revision,
            "project_root": str(root),
            "source_manifest_sha256": project.manifest_sha256,
            "family": receipt,
            "feedback": feedback,
        }
        (draft / "preview.json").write_bytes(_json_bytes(metadata))
        destination = previews / preview_id
        draft.replace(destination)
    return {
        "ok": True,
        "preview_id": preview_id,
        "revision": revision,
        "profile": profile,
        "family_id": family_id,
        "problems": problems,
        "feedback": {**feedback, "image": str(destination / "preview.png")},
    }


def stage_project_export(preview_id: str, cfg: Config) -> dict:
    if not _PREVIEW_ID.fullmatch(preview_id):
        raise ProjectWorkflowError("invalid_preview", "Use a preview ID returned by preview_project_graph.")
    source = _store(cfg, "previews") / preview_id
    if source.is_symlink() or not (source / "preview.json").is_file():
        raise ProjectWorkflowError("preview_not_found", "The verified preview is unavailable.", where=preview_id)
    info = json.loads((source / "preview.json").read_bytes())
    root = approved_source(info["project_root"], cfg)
    project = load_metric_surface_project(root, info["family"]["id"])
    if project.manifest_sha256 != info["source_manifest_sha256"]:
        raise ProjectWorkflowError("source_manifest_changed", "The Unity source manifest changed. Preview the graph again before staging.")
    exports = _store(cfg, "exports")
    export_id = uuid4().hex
    with tempfile.TemporaryDirectory(dir=exports, prefix=".working-") as temporary:
        draft = Path(temporary) / "export"
        shutil.copytree(source, draft)
        result = stage_metric_surface_change(project=project, stage_path=draft, family_receipt=info["family"])
        destination = exports / export_id
        draft.replace(destination)
    return {
        "ok": True,
        **result,
        "export_id": export_id,
        "preview_id": preview_id,
        "revision": info["revision"],
        "profile": info["profile"],
        "stage_path": str(destination),
    }
