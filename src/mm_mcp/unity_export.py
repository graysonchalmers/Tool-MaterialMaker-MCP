"""Verified native export for the Crowned Mountain Unity material contract."""

from array import array
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from zipfile import ZipFile

from PIL import Image, ImageChops, PngImagePlugin

from mm_mcp.material_feedback import measure_normal_height


PROFILE = "crowned-mountain-metric-surface"
TARGET = "Unity/URP"
SIZE = (2048, 2048)
OVERLAY = "UnityProjectOverlay"
EVIDENCE = "native-evidence.zip"
SOURCE_ROOT = Path("Production/CrownedMountainCitadel/MaterialMaker")
MANIFEST = SOURCE_ROOT / "SourceMaterialExport.json"
TEXTURE_ROOT = Path("Assets/PreDeluge/Architecture/CrownedMountainCitadel/Textures/MaterialMaker")
FAMILY_IDS = frozenset({
    "limestone", "refined-stone", "foundation", "slate", "copper", "bronze",
    "timber", "plaster", "paving", "mortar", "moss", "wet-stone",
})
ROLES = ("baseColor", "normal", "orm", "height", "susceptibility")
NATIVE_MAPS = {
    "baseColor": "_albedo.png",
    "normal": "_normal.png",
    "height8": "_height.png",
    "metalSmoothness": "_metal_smoothness.png",
    "occlusion": "_occlusion.png",
    "heightTransport": "-height16.png",
    "response": "-response.png",
    "susceptibility": "-susceptibility.png",
}
_REQUIRED_EXPORT_SUFFIXES = {
    "$project-height16", "$project-response", "$project-susceptibility",
}
_NATIVE_ERRORS = re.compile(
    r"COMPUTE SHADER ERROR|SCRIPT ERROR|shader error:|[1-9]\d* errors encountered", re.I
)


class UnityExportError(ValueError):
    """An actionable export failure with details suitable for a tool result."""

    def __init__(self, code: str, message: str, **details):
        super().__init__(message)
        self.code = code
        self.details = details


@dataclass(frozen=True)
class MetricSurfaceProject:
    root: Path
    manifest: dict
    manifest_sha256: str
    family: dict

    @property
    def manifest_path(self) -> Path:
        return self.root / MANIFEST

    @property
    def family_id(self) -> str:
        return self.family["id"]


def _digest(path: Path) -> str:
    checksum = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def _graph_path(family_id: str) -> Path:
    return SOURCE_ROOT / "Graphs" / f"{family_id}.ptex"


def _texture_path(family_id: str, role: str) -> Path:
    return TEXTURE_ROOT / family_id / f"{role}.png"


def _regular_file(root: Path, relative: Path) -> Path:
    path = root / relative
    if path.resolve() != path or not path.is_file():
        raise UnityExportError("missing_file", f"Expected a regular file at {relative.as_posix()}.")
    return path


def _valid_scale(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def _check_family_shape(family: dict):
    family_id = family.get("id")
    repeat = family.get("repeatMetres")
    maps = family.get("maps")
    mean_dot = family.get("normalHeightMeanDot")
    if (
        family_id not in FAMILY_IDS
        or family.get("graph") != _graph_path(family_id).as_posix()
        or family.get("nativeRepeatIdentical") is not True
        or family.get("normalConvention") != "OpenGL +Y"
        or not _valid_scale(mean_dot)
        or not 0.985 <= mean_dot <= 1
        or not isinstance(repeat, list)
        or len(repeat) != 2
        or not all(_valid_scale(value) for value in repeat)
        or not _valid_scale(family.get("heightRangeMetres"))
        or not isinstance(maps, list)
        or len(maps) != len(ROLES)
        or not all(isinstance(record, dict) for record in maps)
    ):
        raise UnityExportError("invalid_manifest", f"Invalid MetricSurface family record for {family_id!r}.")
    if {record.get("role") for record in maps} != set(ROLES):
        raise UnityExportError("invalid_manifest", f"Invalid MetricSurface map roles for {family_id}.")
    for record in maps:
        role = record["role"]
        if (
            record.get("path") != _texture_path(family_id, role).as_posix()
            or [record.get("width"), record.get("height")] != list(SIZE)
            or record.get("bitDepth") != (16 if role == "height" else 8)
            or record.get("encoding") != ("sRGB" if role == "baseColor" else "linear")
            or type(record.get("bytes")) is not int
            or record["bytes"] <= 0
        ):
            raise UnityExportError(
                "invalid_manifest", f"Invalid MetricSurface map record for {family_id}/{role}."
            )


def load_metric_surface_project(project_root: Path, family_id: str) -> MetricSurfaceProject:
    """Locate the existing Unity contract and read its physical scale for one family."""
    root = Path(project_root).resolve()
    if family_id not in FAMILY_IDS:
        raise UnityExportError("unknown_family", f"Unknown MetricSurface family {family_id!r}.")
    raw = _regular_file(root, MANIFEST).read_bytes()
    manifest = json.loads(raw)
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != 1
        or manifest.get("nativeRepeatCompared") is not True
        or manifest.get("sourceGraphsEditable") is not True
        or manifest.get("nativeTarget") != TARGET
        or manifest.get("nativeDimensions") != list(SIZE)
        or manifest.get("normalConvention") != "OpenGL +Y"
        or manifest.get("ormChannels") != ["occlusion", "perceptual roughness", "metallic", "opaque"]
        or manifest.get("susceptibilityChannels") != ["moisture", "moss", "exposure"]
        or not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("binarySha256")))
    ):
        raise UnityExportError("invalid_manifest", "The project does not have a verified MetricSurface manifest.")
    families = manifest.get("families")
    if (
        not isinstance(families, list)
        or len(families) != len(FAMILY_IDS)
        or not all(isinstance(family, dict) for family in families)
        or {family.get("id") for family in families} != FAMILY_IDS
    ):
        raise UnityExportError("invalid_manifest", "The MetricSurface manifest must contain all twelve families.")
    for family in families:
        _check_family_shape(family)
    selected = next(family for family in families if family["id"] == family_id)
    return MetricSurfaceProject(root, manifest, sha256(raw).hexdigest(), selected)


def _check_export_nodes(graph: bytes):
    data = json.loads(graph)
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), list):
        raise UnityExportError("invalid_graph", "Expected a native .ptex graph.")
    suffixes = set()
    nodes = [data]
    material_count = 0
    while nodes:
        node = nodes.pop()
        if not isinstance(node, dict):
            raise UnityExportError("invalid_graph", "Expected named nodes in the .ptex graph.")
        if isinstance(node.get("nodes"), list):
            nodes.extend(node["nodes"])
        kind = node.get("type")
        parameters = node.get("parameters")
        model = node.get("shader_model")
        if kind == "material":
            material_count += 1
        if kind == "material_export" or isinstance(model, dict) and (
            "preview_shader" in model or "exports" in model
        ):
            raise UnityExportError(
                "custom_export_profile", "Use the built-in Material node for the verified Unity/URP target.",
                node=node.get("name"),
            )
        external_image = kind == "image" and (
            node.get("image") or isinstance(parameters, dict) and parameters.get("image")
        )
        if external_image or isinstance(kind, str) and kind.startswith("website:"):
            raise UnityExportError(
                "external_asset_input", "This export contract requires a self-contained procedural graph.",
                node=node.get("name"),
            )
        if kind != "export":
            continue
        suffix = parameters.get("suffix") if isinstance(parameters, dict) else None
        if (
            not isinstance(suffix, str)
            or not re.fullmatch(r"\$project-[a-z0-9][a-z0-9_-]{0,63}", suffix)
            or suffix in suffixes
            or type(parameters.get("format", 0)) is not int
            or parameters.get("format", 0) != 0
        ):
            raise UnityExportError(
                "invalid_export_node",
                "A MetricSurface Export node needs a unique filename of the form $project-role and PNG format.",
                node=node.get("name"),
                suffix=suffix,
            )
        suffixes.add(suffix)
    if material_count != 1:
        raise UnityExportError(
            "invalid_material_outputs", "MetricSurface requires exactly one built-in Material node.",
            found=material_count,
        )
    if not _REQUIRED_EXPORT_SUFFIXES <= suffixes:
        raise UnityExportError(
            "missing_outputs", "The graph is missing required MetricSurface Export nodes.",
            suffixes=sorted(_REQUIRED_EXPORT_SUFFIXES - suffixes),
        )


def _run_native(binary: Path, graph: Path, output: Path, config: Path, timeout: float):
    output.mkdir()
    config.mkdir()
    env = dict(os.environ, XDG_DATA_HOME=str(config), XDG_CONFIG_HOME=str(config))
    started = perf_counter()
    try:
        result = subprocess.run(
            [str(binary), "--export-material", "--target", TARGET, "-o", str(output), str(graph)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=config,
            text=True, errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        output_text = error.stdout or b""
        if isinstance(output_text, bytes):
            output_text = output_text.decode(errors="replace")
        raise UnityExportError(
            "native_timeout", f"Material Maker did not finish its native export in {timeout:g} seconds.",
            log_tail=output_text[-6000:],
        ) from error
    except OSError as error:
        raise UnityExportError("native_launch_failed", f"Material Maker could not start: {error}") from error
    elapsed = perf_counter() - started
    log = result.stdout
    (output / "native.log").write_text(log, encoding="utf-8")
    if result.returncode != 0 or _NATIVE_ERRORS.search(log):
        raise UnityExportError(
            "native_render_failed", "Material Maker did not complete a clean texture export.",
            return_code=result.returncode, log_tail=log[-6000:],
        )
    leaked = re.search(r"(\d+) ObjectDB instances were leaked", log)
    resources = re.search(r"(\d+) resources still in use at exit", log)
    diagnostics = {
        "processSucceeded": True,
        "shaderCompileErrors": False,
        "missingUserExportTargetNotice": "Cannot open user://export_targets" in log,
        "objectDbInstancesAtExit": int(leaked[1]) if leaked else 0,
        "resourcesInUseAtExit": int(resources[1]) if resources else 0,
    }
    return elapsed, diagnostics


def _inventory(output: Path, stem: str) -> dict:
    names = {path.name for path in output.iterdir() if path.suffix.lower() == ".png"}
    required = {stem + suffix for suffix in NATIVE_MAPS.values()}
    if not required <= names:
        raise UnityExportError(
            "missing_outputs", "The native exporter did not write every required map.",
            missing=sorted(required - names),
        )
    records = {}
    for name in sorted(names):
        path = _regular_file(output, Path(name))
        records[name] = {"name": name, "sha256": _digest(path), "bytes": path.stat().st_size}
    return records


def _read_native(raw: Path, stem: str, role: str) -> Image.Image:
    path = raw / (stem + NATIVE_MAPS[role])
    try:
        with Image.open(path) as image:
            if image.size != SIZE or image.format != "PNG":
                raise ValueError("the file is not a 2048 × 2048 PNG")
            return image.convert("RGBA")
    except (OSError, ValueError) as error:
        raise UnityExportError("invalid_map", f"Invalid native map {path.name}: {error}", role=role) from error


def _height_samples(image: Image.Image) -> array:
    samples = array("H")
    samples.frombytes(image.tobytes())
    if sys.byteorder == "big":
        samples.byteswap()
    return samples


def _height_png(high: Image.Image, low: Image.Image) -> Image.Image:
    data = bytearray(2 * high.width * high.height)
    data[::2] = low.tobytes()
    data[1::2] = high.tobytes()
    return Image.frombytes("I;16", high.size, bytes(data))


def _sum_8bit_difference(left: Image.Image, right: Image.Image) -> int:
    histogram = ImageChops.difference(left, right).histogram()
    return sum(index % 256 * count for index, count in enumerate(histogram))


def seam_to_interior_step_ratio_yx(image: Image.Image) -> list[float]:
    """Compare the wrap-edge step with ordinary adjacent-texel steps on each axis."""
    width, height = image.size
    if width < 2 or height < 2:
        return [0.0, 0.0]
    if image.mode == "I;16":
        values = _height_samples(image)
        seam_y = sum(abs(left - right) for left, right in zip(values[:width], values[-width:]))
        seam_x = sum(abs(left - right) for left, right in zip(values[::width], values[width - 1::width]))
        inner_y = sum(abs(left - right) for left, right in zip(values, values[width:]))
        inner_x = 0
        for start in range(0, len(values), width):
            row = values[start:start + width]
            inner_x += sum(abs(left - right) for left, right in zip(row, row[1:]))
    else:
        seam_y = _sum_8bit_difference(image.crop((0, 0, width, 1)), image.crop((0, height - 1, width, height)))
        seam_x = _sum_8bit_difference(image.crop((0, 0, 1, height)), image.crop((width - 1, 0, width, height)))
        inner_y = _sum_8bit_difference(image.crop((0, 0, width, height - 1)), image.crop((0, 1, width, height)))
        inner_x = _sum_8bit_difference(image.crop((0, 0, width - 1, height)), image.crop((1, 0, width, height)))
    bands = len(image.getbands())
    return [
        round(seam_y / (width * bands) / max(inner_y / (width * (height - 1) * bands), 1e-6), 4),
        round(seam_x / (height * bands) / max(inner_x / (height * (width - 1) * bands), 1e-6), 4),
    ]


def _normalize(raw: Path, overlay: Path, family: dict) -> dict:
    stem = family["id"]
    albedo = _read_native(raw, stem, "baseColor").convert("RGB")
    normal = _read_native(raw, stem, "normal").convert("RGB")
    roughness, occlusion, metallic, opaque = _read_native(raw, stem, "response").split()
    high, low, _, _ = _read_native(raw, stem, "heightTransport").split()
    height = _height_png(high, low)
    height_values = _height_samples(height)
    native_height = _read_native(raw, stem, "height8").getchannel("R")
    native_metal = _read_native(raw, stem, "metalSmoothness")
    native_ao = _read_native(raw, stem, "occlusion").getchannel("R")
    susceptibility = _read_native(raw, stem, "susceptibility").convert("RGB")
    maximum_height_error = max(
        abs(value - (255 - sample) * 257) for value, sample in zip(height_values, native_height.tobytes())
    ) / 65535
    if maximum_height_error >= 0.013:
        raise UnityExportError("height_mismatch", "Decoded height disagrees with native inverted height.", maximum_error=maximum_height_error)
    for role, channel, reference in (
        ("roughness", roughness, ImageChops.invert(native_metal.getchannel("A"))),
        ("occlusion", occlusion, native_ao),
        ("metallic", metallic, native_metal.getchannel("R")),
    ):
        step = ImageChops.difference(channel, reference).getextrema()[1]
        if step > 2:
            raise UnityExportError("channel_mismatch", f"Native packed {role} disagrees with its reference.", role=role, maximum_error=step)
    normal_height = measure_normal_height(
        normal, height, family["repeatMetres"], family["heightRangeMetres"], max_samples=None,
    )
    normal_mean = normal_height["meanDot"]
    if normal_mean < 0.985:
        raise UnityExportError(
            "normal_height_mismatch", "Native normals disagree with physical height.",
            normalHeightMeanDot=normal_mean,
        )
    orm = Image.merge("RGBA", (occlusion, roughness, metallic, Image.new("L", opaque.size, 255)))
    images = (albedo, normal, orm, height, susceptibility)
    records = []
    for role, image in zip(ROLES, images):
        relative = _texture_path(stem, role)
        path = overlay / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        info = PngImagePlugin.PngInfo()
        if role == "baseColor":
            info.add(b"sRGB", b"\0")
        image.save(path, pnginfo=info, compress_level=7)
        with Image.open(path) as reread:
            decoded = reread.convert("I;16") if role == "height" and reread.mode == "I" else reread
            if decoded.mode != image.mode or decoded.size != image.size or decoded.tobytes() != image.tobytes():
                raise UnityExportError("map_round_trip", f"The emitted {role} PNG did not preserve its pixels.")
        records.append({
            "role": role, "path": relative.as_posix(), "sha256": _digest(path), "bytes": path.stat().st_size,
            "width": image.width, "height": image.height, "bitDepth": 16 if role == "height" else 8,
            "encoding": "sRGB" if role == "baseColor" else "linear",
            "seamToInteriorStepRatioYX": seam_to_interior_step_ratio_yx(image),
        })
    orm_path = _texture_path(stem, "orm").as_posix()
    return {
        "id": stem, "repeatMetres": family["repeatMetres"], "heightRangeMetres": family["heightRangeMetres"],
        "normalConvention": "OpenGL +Y", "normalHeightMeanDot": normal_mean,
        "normalHeightMinDot": normal_height["minDot"], "normalHeightSamples": normal_height["samples"],
        "nativeHeightMaxError": maximum_height_error,
        "heightDistinctValues": len(set(height_values)), "maps": records,
        "roughness": {"path": orm_path, "channel": "G", "meaning": "perceptual roughness"},
        "occlusion": {"path": orm_path, "channel": "R", "meaning": "visibility; white unoccluded"},
        "metallic": {"path": orm_path, "channel": "B"},
    }


def bake_metric_surface(
    graph: bytes, *, project: MetricSurfaceProject, binary: Path,
    binary_sha256: str, stage_path: Path, timeout: float = 240,
) -> dict:
    """Bake a graph twice with the pinned native app and stage its maps and evidence."""
    _check_export_nodes(graph)
    binary = Path(binary).resolve()
    if (
        binary_sha256 != project.manifest["binarySha256"]
        or not binary.is_file()
        or _digest(binary) != binary_sha256
    ):
        raise UnityExportError(
            "native_pin_mismatch", "The configured Material Maker app does not match the verified project binary."
        )
    stage_path = Path(stage_path).resolve(strict=True)
    overlay = stage_path / OVERLAY
    if overlay.exists() or (stage_path / EVIDENCE).exists():
        raise UnityExportError("stage_exists", "Use a new private directory for the native bake.")
    stem = project.family["id"]
    with TemporaryDirectory(prefix=".native-", dir=stage_path) as directory:
        work = Path(directory)
        source = work / f"{stem}.ptex"
        source.write_bytes(graph)
        first, repeat = work / "default", work / "repeat"
        elapsed, diagnostics = _run_native(binary, source, first, work / "default-config", timeout)
        repeated_elapsed, repeated_diagnostics = _run_native(binary, source, repeat, work / "repeat-config", timeout)
        native = _inventory(first, stem)
        repeated = _inventory(repeat, stem)
        if native != repeated:
            names = sorted(name for name in native.keys() | repeated.keys() if native.get(name) != repeated.get(name))
            raise UnityExportError("nondeterministic_export", "Native repeat PNG files differ.", maps=names)
        receipt = _normalize(first, overlay, project.family)
        graph_relative = _graph_path(stem)
        graph_path = overlay / graph_relative
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        graph_path.write_bytes(graph)
        with ZipFile(stage_path / EVIDENCE, "x") as archive:
            archive.write(source, source.name)
            for output in (first, repeat):
                for path in sorted(output.iterdir()):
                    if path.is_file() and not path.is_symlink():
                        archive.write(path, f"{output.name}/{path.name}")
        receipt.update({
            "graph": graph_relative.as_posix(), "graphSha256": sha256(graph).hexdigest(),
            "nativeRepeatIdentical": True, "nativeMaps": list(native.values()),
            "nativeDefaultSeconds": elapsed, "nativeRepeatSeconds": repeated_elapsed,
            "nativeDiagnostics": diagnostics, "nativeRepeatDiagnostics": repeated_diagnostics,
            "nativeBackend": {"kind": "standalone-material-maker", "binarySha256": binary_sha256, "target": TARGET},
        })
    return receipt


def _verify_family_files(root: Path, family: dict):
    graph = _regular_file(root, _graph_path(family["id"]))
    if _digest(graph) != family.get("graphSha256"):
        raise UnityExportError("source_hash_mismatch", f"The source graph for {family['id']} has changed.")
    for record in family["maps"]:
        path = _regular_file(root, Path(record["path"]))
        if path.stat().st_size != record["bytes"] or _digest(path) != record.get("sha256"):
            raise UnityExportError(
                "map_hash_mismatch", f"Map bytes differ from the manifest for {family['id']}/{record['role']}."
            )


def stage_metric_surface_change(
    *, project: MetricSurfaceProject, stage_path: Path, family_receipt: dict,
) -> dict:
    """Prepare changed files and a complete importer manifest as a project-relative overlay."""
    overlay = Path(stage_path).resolve(strict=True) / OVERLAY
    if _digest(_regular_file(project.root, MANIFEST)) != project.manifest_sha256:
        raise UnityExportError("stale_manifest", "The Unity source manifest changed during this export.")
    _check_family_shape(family_receipt)
    if (
        family_receipt["id"] != project.family["id"]
        or family_receipt["repeatMetres"] != project.family["repeatMetres"]
        or family_receipt["heightRangeMetres"] != project.family["heightRangeMetres"]
        or family_receipt.get("nativeBackend", {}).get("binarySha256") != project.manifest["binarySha256"]
    ):
        raise UnityExportError("invalid_receipt", "The staged material does not match the selected Unity contract.")
    _verify_family_files(overlay, family_receipt)
    families = []
    for baseline in project.manifest["families"]:
        _verify_family_files(project.root, baseline)
        families.append(family_receipt if baseline["id"] == family_receipt["id"] else baseline)
    manifest_path = overlay / MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {**project.manifest, "families": families}
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return {
        "contract": PROFILE, "overlay": OVERLAY, "manifest": MANIFEST.as_posix(),
        "manifestSha256": _digest(manifest_path), "baseManifestSha256": project.manifest_sha256,
        "family": family_receipt, "familyCount": len(families),
        "evidence": EVIDENCE, "evidenceSha256": _digest(_regular_file(overlay.parent, Path(EVIDENCE))),
    }
