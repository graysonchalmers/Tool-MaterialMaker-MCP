"""Pure request handlers for the play surface. Each takes already-parsed input
and returns JSON-serializable data; no socket, no HTTP. Errors are data."""
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
import zipfile

from mm_mcp import cookbook
from mm_mcp.play import renderer, sliders


def list_materials(cfg) -> dict:
    entries = cookbook.list_cookbook(cfg.cookbook_dir)
    return {"ok": True,
            "materials": [{"name": e.name, "category": e.category} for e in entries]}


def _load_graph(cfg, name):
    entry = cookbook.find_cookbook(cfg.cookbook_dir, name)
    if entry is None:
        return None, {"ok": False, "error": f"unknown material: {name}"}
    with open(entry.path, encoding="utf-8") as fh:
        return json.load(fh), None


def get_material(cfg, catalog, name) -> dict:
    graph, err = _load_graph(cfg, name)
    if err:
        return err
    return {"ok": True, "name": name,
            "sliders": sliders.derive_sliders(graph, catalog)}


def _changes_for(graph, catalog, values):
    """Map id->value to per-node live changes, using the derived bindings.
    `values` is keyed by each slider's unique `id` (f"{subgraph_node_name}/
    {slot_id}", see sliders.derive_sliders), so each change is addressed to
    exactly the one subgraph/node/widget it belongs to. No fan-out to other
    subgraphs that happen to share the same slot_id."""
    by_id = {s["id"]: s for s in sliders.derive_sliders(graph, catalog)}
    changes = []
    for sid, value in values.items():
        s = by_id.get(sid)
        if s:
            changes.append({"node": s["binding"]["node"],
                            "widget": s["binding"]["widget"], "value": value})
    return changes


def render_request(cfg, catalog, body, outdir, render_fn=renderer.render_material) -> dict:
    name = body.get("material_id")
    values = body.get("values") or {}
    size = int(body.get("size") or 256)
    graph, err = _load_graph(cfg, name)
    if err:
        return err
    applied = sliders.apply_values(graph, values)
    changes = _changes_for(graph, catalog, values)
    graph_json = json.dumps(applied, indent=1)
    preview_id = uuid.uuid4().hex
    root = Path(outdir).resolve() / "previews"
    try:
        root.mkdir(parents=True, exist_ok=True)
        # A renderer gets its own directory. Publish the whole completed result
        # together, so another request cannot replace its maps during download.
        with tempfile.TemporaryDirectory(prefix=".render-", dir=root) as stage:
            stage = Path(stage)
            result = render_fn(applied, changes, size, cfg, str(stage), material_id=name)
            if not result.get("ok"):
                return {"ok": False, "error": result.get("error") or "render failed"}
            images = [Path(p).resolve() for p in result.get("images", [])]
            if not images or any(
                p.parent != stage or p.suffix.lower() != ".png"
                or not p.is_file() or p.stat().st_size == 0 for p in images
            ):
                return {"ok": False, "error": "renderer did not produce private preview maps"}
            maps = [p.name for p in images]
            if len(set(maps)) != len(maps):
                return {"ok": False, "error": "renderer returned duplicate preview maps"}
            with zipfile.ZipFile(stage / "download.zip", "w", zipfile.ZIP_DEFLATED) as z:
                for p in images:
                    z.write(p, p.name)
                z.writestr(f"{name}.ptex", graph_json)
            receipt = {"material_id": name, "values": values, "size": size,
                       "path": result.get("path"), "maps": maps}
            (stage / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            os.replace(stage, root / preview_id)
        return {"ok": True, "path": result.get("path"),
                "preview_id": preview_id, "maps": maps}
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


def _load_preview(outdir, preview_id):
    if not isinstance(preview_id, str) or not re.fullmatch(r"[0-9a-f]{32}", preview_id):
        raise ValueError("invalid preview id")
    directory = Path(outdir).resolve() / "previews" / preview_id
    receipt = json.loads((directory / "receipt.json").read_text(encoding="utf-8"))
    return directory, receipt


def map_bytes(outdir, preview_id, name):
    """Only serve maps listed in a completed render's receipt."""
    try:
        directory, receipt = _load_preview(outdir, preview_id)
        if name in receipt["maps"]:
            return (directory / name).read_bytes()
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def export(cfg, catalog, body, outdir):
    """Download the saved maps and applied graph of a completed preview.

    `preview_id` comes from render_request. A material id or new control values
    cannot reconstruct a prior render and are deliberately insufficient here.
    Returns (zip_bytes, filename), or (None, error) for an unavailable preview.
    """
    try:
        directory, receipt = _load_preview(outdir, body.get("preview_id"))
        return (directory / "download.zip").read_bytes(), f'{receipt["material_id"]}.zip'
    except (OSError, ValueError, KeyError, TypeError):
        return None, "unknown or incomplete preview; render the material before downloading"
