"""Pure graph-surgery helpers for Phase 3 authoring and cookbook growth.

Everything here is pure graph-JSON surgery against the catalog vocabulary; no
Godot. Split out of quality/author.py (2026-09-03) so the ~10 helpers below
have one home shared by author.py's own Phase 3 builders and every
quality/cookbook_<category>.py / debug_swatches.py / noise_gallery.py
consumer, instead of living inside author.py alongside Phase-3-specific
material builders that only author.py itself uses.
"""
import copy
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
from mm_mcp.config import load_config

_CFG = load_config()
_EX = Path(_CFG.examples_dir)


def load_example(name: str) -> dict:
    with open(_EX / f"{name}.ptex", encoding="utf-8") as fh:
        return json.load(fh)


def node(graph: dict, name: str) -> dict:
    for n in graph["nodes"]:
        if n["name"] == name:
            return n
    raise KeyError(f"node {name!r} not in graph")


def set_gradient(graph: dict, node_name: str, colors: list) -> None:
    """Replace a colorize node's gradient points.

    colors: list of (pos, r, g, b) with 0..1 floats. Alpha forced to 1.
    """
    pts = [{"a": 1, "r": r, "g": g, "b": b, "pos": pos}
           for (pos, r, g, b) in colors]
    node(graph, node_name)["parameters"]["gradient"] = {
        "interpolation": 1, "points": pts, "type": "Gradient",
    }


def set_param(graph: dict, node_name: str, key: str, value) -> None:
    node(graph, node_name).setdefault("parameters", {})[key] = value


def save_variant(graph: dict, iter_label: str, case_id: str, n: int) -> str:
    out = _ROOT / "quality" / "authored" / iter_label / case_id
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"v{n}.ptex"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=1)
    return str(path)


def _grad(points):
    return {"interpolation": 1, "type": "Gradient",
            "points": [{"a": 1, "r": r, "g": g, "b": b, "pos": p}
                       for (p, r, g, b) in points]}


def _from_scratch_noise_material(perlin_params, albedo_points, *,
                                 metallic=0.0, roughness=0.5, normal_amount=0.3):
    """A minimal, valid noise->colorize->material graph:
    perlin -> colorize(albedo) -> Material.albedo, perlin -> normal_map ->
    Material.normal (so the normal isn't flat), with scalar metallic/roughness.
    Node skeletons match the shapes Godot's loader expects (verified vs
    rusted_metal / wooden_floor)."""
    nodes = [
        {"name": "perlin_0", "type": "perlin",
         "node_position": {"x": 0, "y": 0}, "parameters": dict(perlin_params)},
        {"name": "colorize_0", "type": "colorize",
         "node_position": {"x": 300, "y": -60},
         "parameters": {"gradient": _grad(albedo_points)}},
        # normal_map is a COMPOUND node: its real params are param0 (buffer
        # size 2^n), param1 (STRENGTH, default 1 — this is what drives relief),
        # param2, param4. Earlier stray keys (amount/size/param3) were ignored,
        # and param1=0.2 rendered a near-flat normal. Map relief -> param1.
        {"name": "normal_map_0", "type": "normal_map",
         "node_position": {"x": 300, "y": 160},
         "parameters": {"param0": 10, "param1": normal_amount,
                        "param2": 0, "param4": 1}},
        {"name": "Material", "type": "material",
         "node_position": {"x": 620, "y": 40},
         "export_paths": {},
         "parameters": {
             "albedo_color": {"a": 1, "r": 1, "g": 1, "b": 1, "type": "Color"},
             "ao": 1, "depth_scale": 1, "emission_energy": 1,
             "metallic": metallic, "normal": 1, "roughness": roughness,
             "size": 11, "sss": 0}},
    ]
    connections = [
        {"from": "perlin_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "normal_map_0", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "normal_map_0", "from_port": 0, "to": "Material", "to_port": 4},
    ]
    return {"connections": connections, "nodes": nodes}


def rewire(graph: dict, to_node: str, to_port: int, from_node: str,
           from_port: int) -> None:
    """Repoint the connection feeding (to_node, to_port) to a new source."""
    for c in graph["connections"]:
        if c["to"] == to_node and c["to_port"] == to_port:
            c["from"] = from_node
            c["from_port"] = from_port
            return
    graph["connections"].append(
        {"from": from_node, "from_port": from_port,
         "to": to_node, "to_port": to_port})


def drop_conn(graph: dict, to_node: str, to_port: int) -> None:
    """Remove the connection feeding (to_node, to_port), if any."""
    graph["connections"] = [
        c for c in graph["connections"]
        if not (c["to"] == to_node and c["to_port"] == to_port)]


def retype(graph: dict, node_name: str, new_type: str, params: dict) -> None:
    """Swap a node's type and replace its parameters. Connections that
    reference it keep working as long as the new type's output port 0 is
    compatible with what the old one fed."""
    nd = node(graph, node_name)
    nd["type"] = new_type
    nd["parameters"] = dict(params)


def add_node(graph: dict, name: str, ntype: str, params: dict) -> None:
    graph["nodes"].append({"name": name, "type": ntype,
                           "node_position": {"x": 0, "y": 0},
                           "parameters": dict(params)})
