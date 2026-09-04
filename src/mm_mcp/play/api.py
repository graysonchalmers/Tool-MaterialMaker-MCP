"""Pure request handlers for the play surface. Each takes already-parsed input
and returns JSON-serializable data; no socket, no HTTP. Errors are data."""
import json
import os

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
    result = render_fn(applied, changes, size, cfg, outdir)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or "render failed"}
    return {"ok": True, "path": result.get("path"),
            "maps": [os.path.basename(p) for p in result.get("images", [])]}
