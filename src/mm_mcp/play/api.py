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
    """Map slot_id->value to per-node live changes, using the derived bindings.
    slot_id is only unique within a subgraph (multiple subgraphs can each
    expose "param0"), and apply_values() already fans a value out to every
    matching subgraph on the headless graph, so this mirrors that fan-out for
    the live path rather than picking one. This is a real cross-subgraph
    collision inherited from derive_sliders/apply_values (Tasks 2-3), not
    something fixed here; see the task-5 report."""
    changes = []
    for s in sliders.derive_sliders(graph, catalog):
        slot_id = s["slot_id"]
        if slot_id in values:
            changes.append({"node": s["binding"]["node"],
                            "widget": s["binding"]["widget"], "value": values[slot_id]})
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
