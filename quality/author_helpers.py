"""Pure graph-surgery helpers for cookbook authoring.

Everything here is pure graph-JSON surgery against the catalog vocabulary; no
Godot. One home for the ~10 helpers shared by author.py's builders and every
quality/cookbook_<category>.py / debug_swatches.py / noise_gallery.py
consumer. Import as `from quality.author_helpers import ...`.
"""
import copy
import json
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
from mm_mcp.config import load_config

_CFG = load_config()
_EX = _ROOT / "quality" / "donors"


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


def take_variant(builder, label: str, keep_n: int) -> dict:
    """Run a Phase-3 `author.py` builder under a cookbook label and keep ONE of
    its variants. `builder(label)` writes v1.ptex, v2.ptex, ... under
    quality/authored/<label>/<case>/ and returns their paths; this loads the
    `v{keep_n}.ptex` one, deletes every variant file the builder wrote (the
    caller re-saves the grouped graph as v1, and promote_cookbook.py only
    ever reads v1), and returns the graph so the caller can
    group_into_subgraph it and re-save it as v1."""
    paths = builder(label)
    wanted = f"v{keep_n}.ptex"
    keep = next((p for p in paths if os.path.basename(p) == wanted), None)
    if keep is None:
        raise FileNotFoundError(f"{builder.__name__}({label!r}) produced no {wanted}: {paths}")
    with open(keep, encoding="utf-8") as fh:
        graph = json.load(fh)
    for p in paths:
        if os.path.exists(p):
            os.remove(p)
    return graph


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


RESERVED_NODE_NAMES = frozenset({"Material", "gen_inputs", "gen_outputs", "gen_parameters"})


def _levels(graph: dict):
    """Yield (level_label, node_list, connection_list) for the top level and
    every nested `graph` node, depth first."""
    yield "", graph["nodes"], graph["connections"]
    for n in graph["nodes"]:
        if n.get("type") == "graph":
            yield from ((n["name"] if not lbl else f"{n['name']}/{lbl}", nodes, conns)
                        for lbl, nodes, conns in _levels(n))


def rename_nodes(graph: dict, mapping: dict) -> None:
    """Rename nodes in place at every level of `graph` (top level and inside
    every `graph`-type subgraph): the node's `name`, both ends of every
    connection at that level, and every `linked_widgets[].node` reference on
    any node at that level. `node_position` is never touched, so Material
    Maker's position-derived seeds (and therefore the renders) are unchanged.

    Subgraph (`type == "graph"`) nodes are never renamed; mm-play slider ids
    depend on their names.

    Validates the whole mapping before changing anything:
      KeyError   - a source name exists at no level
      ValueError - a source or target is reserved, a source or target names a
                   subgraph node, or a target already names a sibling at the
                   level where the source lives
    """
    bad_reserved = [k for k in mapping if k in RESERVED_NODE_NAMES] + \
                   [v for v in mapping.values() if v in RESERVED_NODE_NAMES]
    if bad_reserved:
        raise ValueError(f"reserved node names cannot be renamed or used: {sorted(set(bad_reserved))}")
    found = {}
    graph_names_by_level = {}
    for label, nodes, _ in _levels(graph):
        names = {n["name"] for n in nodes}
        graph_names_by_level[label] = {n["name"] for n in nodes if n.get("type") == "graph"}
        level_sources = [old for old in mapping if old in names]
        for old in level_sources:
            found.setdefault(old, []).append((label, names, level_sources))
    missing = [k for k in mapping if k not in found]
    if missing:
        raise KeyError(f"nodes not found at any level: {sorted(missing)}")
    bad_subgraph_sources = [old for old, levels in found.items()
                            if any(old in graph_names_by_level[label] for label, _, _ in levels)]
    if bad_subgraph_sources:
        raise ValueError(f"subgraph nodes cannot be renamed: {sorted(set(bad_subgraph_sources))}")
    bad_subgraph_targets = [(old, new) for old, new in mapping.items()
                            for label, _, _ in found[old]
                            if new in graph_names_by_level[label]]
    if bad_subgraph_targets:
        raise ValueError(f"cannot rename to a subgraph node's name: {sorted(set(bad_subgraph_targets))}")
    for old, new in mapping.items():
        for label, names, level_sources in found[old]:
            where = label or "top level"
            if new in names and new != old:
                raise ValueError(f"{where}: cannot rename {old!r} to {new!r}, a sibling already has that name")
            other_targets = {mapping[other] for other in level_sources if other != old}
            if new in other_targets:
                raise ValueError(f"{where}: cannot rename {old!r} to {new!r}, another node in this "
                                  f"mapping at the same level also targets {new!r}")
    for _, nodes, conns in _levels(graph):
        for n in nodes:
            n["name"] = mapping.get(n["name"], n["name"])
            for w in n.get("widgets", []) or []:
                for lw in w.get("linked_widgets", []) or []:
                    lw["node"] = mapping.get(lw["node"], lw["node"])
        for c in conns:
            c["from"] = mapping.get(c["from"], c["from"])
            c["to"] = mapping.get(c["to"], c["to"])


def _boundary_port_type(catalog: dict, node_type: str, port: int, *, is_input: bool) -> str:
    entry = catalog.get(node_type, {})
    ports = entry.get("inputs" if is_input else "outputs", [])
    if port < len(ports):
        return ports[port].get("type") or "f"
    return "f"


def group_into_subgraph(graph: dict, member_names: list, name: str, label: str,
                         exposed: list, catalog: dict) -> None:
    """Collapse `member_names` (and the connections between them) into one
    node of type "graph", replacing them in `graph` in place. `exposed` is a
    list of (internal_node_name, internal_param_name, slot_id, friendly_label)
    tuples; each becomes one widget on the collapsed node's Parameters remote."""
    member_set = set(member_names)
    all_conns = graph["connections"]
    internal = [c for c in all_conns
                if c["from"] in member_set and c["to"] in member_set]
    incoming = [c for c in all_conns
                if c["to"] in member_set and c["from"] not in member_set]
    outgoing = [c for c in all_conns
                if c["from"] in member_set and c["to"] not in member_set]
    untouched = [c for c in all_conns
                 if c["from"] not in member_set and c["to"] not in member_set]
    member_nodes = [n for n in graph["nodes"] if n["name"] in member_set]

    inner_conns = list(internal)
    gen_inputs_ports, outer_incoming = [], []
    for i, c in enumerate(incoming):
        target = node(graph, c["to"])
        port_type = _boundary_port_type(catalog, target["type"], c["to_port"], is_input=True)
        gen_inputs_ports.append({"name": f"in{i}", "type": port_type, "group_size": 0})
        inner_conns.append({"from": "gen_inputs", "from_port": i,
                             "to": c["to"], "to_port": c["to_port"]})
        outer_incoming.append({"from": c["from"], "from_port": c["from_port"],
                                "to": name, "to_port": i})

    gen_outputs_ports, outer_outgoing = [], []
    for o, c in enumerate(outgoing):
        source = node(graph, c["from"])
        port_type = _boundary_port_type(catalog, source["type"], c["from_port"], is_input=False)
        gen_outputs_ports.append({"name": f"out{o}", "type": port_type, "group_size": 0})
        inner_conns.append({"from": c["from"], "from_port": c["from_port"],
                             "to": "gen_outputs", "to_port": o})
        outer_outgoing.append({"from": name, "from_port": o,
                                "to": c["to"], "to_port": c["to_port"]})

    widgets, params = [], {}
    for internal_node_name, internal_param_name, slot_id, friendly_label in exposed:
        inode = node(graph, internal_node_name)
        params[slot_id] = inode.get("parameters", {}).get(internal_param_name)
        widgets.append({
            "name": slot_id, "shortdesc": friendly_label, "label": "",
            "type": "linked_control",
            "linked_widgets": [{"node": internal_node_name, "widget": internal_param_name}],
        })

    xs = [n["node_position"]["x"] for n in member_nodes] or [0]
    ys = [n["node_position"]["y"] for n in member_nodes] or [0]
    centroid = {"x": sum(xs) / len(xs), "y": sum(ys) / len(ys)}

    collapsed = {
        "name": name, "label": label, "type": "graph",
        "node_position": centroid, "parameters": dict(params), "seed_int": 0,
        "nodes": [
            {"name": "gen_inputs", "type": "ios",
             "node_position": {"x": centroid["x"] - 400, "y": centroid["y"]},
             "parameters": {}, "ports": gen_inputs_ports, "seed": 0, "seed_locked": True},
            {"name": "gen_outputs", "type": "ios",
             "node_position": {"x": centroid["x"] + 400, "y": centroid["y"]},
             "parameters": {}, "ports": gen_outputs_ports, "seed": 0},
            {"name": "gen_parameters", "type": "remote",
             "node_position": {"x": centroid["x"] - 400, "y": centroid["y"] + 200},
             "parameters": dict(params), "seed": 0, "widgets": widgets},
            *member_nodes,
        ],
        "connections": inner_conns,
    }

    graph["nodes"] = [n for n in graph["nodes"] if n["name"] not in member_set] + [collapsed]
    graph["connections"] = untouched + outer_incoming + outer_outgoing


# --- Host-material layout helpers (lifted from cookbook_metal.py, 2026-09-27,
# when the second host, s14, needed them). They only tidy a graph that
# group_into_subgraph already built; they never change what renders. ---

def place(level: dict, positions: dict) -> None:
    """Give nodes at one graph level an explicit node_position. add_node parks
    every new node at (0, 0), and Material Maker seeds a node from its
    position, so for a noise node a position is also a seed choice."""
    for name, (x, y) in positions.items():
        node(level, name)["node_position"] = {"x": x, "y": y}


def _output_type(g: dict, name: str, port: int, catalog: dict) -> str:
    src = node(g, name)
    if src["type"] == "graph":
        return node(src, "gen_outputs")["ports"][port]["type"]
    outs = catalog.get(src["type"], {}).get("outputs", [])
    return (outs[port].get("type") if port < len(outs) else None) or "f"


def tidy_ports(g: dict, sub_name: str, inputs: list, outputs: list, catalog: dict) -> None:
    """group_into_subgraph gives every wire that crosses the boundary its own
    port, so one signal read by two nodes on the far side shows up as two
    identical ports. Merge the ports that carry the same signal and name
    them, so the collapsed node reads as "brush in, albedo/roughness/height
    out" in Material Maker. An input port takes the type its source
    produces, so the signal is converted (rgba -> f) only where a consumer
    inside needs it, exactly as before grouping. A separate helper on
    purpose: changing group_into_subgraph itself would re-port every other
    cookbook graph.

    inputs:  [(outer_source_node, outer_source_port, port_name), ...]
    outputs: [(inner_source_node, inner_source_port, port_name), ...]
    List order is the new port order; each list must cover exactly the
    distinct signals that cross the boundary."""
    sub = node(g, sub_name)
    gin, gout = node(sub, "gen_inputs"), node(sub, "gen_outputs")

    old_in = {c["to_port"]: (c["from"], c["from_port"])
              for c in g["connections"] if c["to"] == sub_name}
    order = [(n, p) for n, p, _ in inputs]
    assert set(old_in.values()) == set(order), (sub_name, "inputs", old_in, order)
    in_types = {(n, p): _output_type(g, n, p, catalog) for n, p in order}
    for c in sub["connections"]:
        if c["from"] == "gen_inputs":
            c["from_port"] = order.index(old_in[c["from_port"]])
    g["connections"] = [c for c in g["connections"] if c["to"] != sub_name] + [
        {"from": n, "from_port": p, "to": sub_name, "to_port": i}
        for i, (n, p) in enumerate(order)]
    gin["ports"] = [{"name": name, "type": in_types[(n, p)], "group_size": 0}
                    for n, p, name in inputs]

    old_out = {c["to_port"]: (c["from"], c["from_port"])
               for c in sub["connections"] if c["to"] == "gen_outputs"}
    order = [(n, p) for n, p, _ in outputs]
    assert set(old_out.values()) == set(order), (sub_name, "outputs", old_out, order)
    out_types = {}
    for old, src in sorted(old_out.items()):
        out_types.setdefault(src, gout["ports"][old]["type"])
    for c in g["connections"]:
        if c["from"] == sub_name:
            c["from_port"] = order.index(old_out[c["from_port"]])
    sub["connections"] = [c for c in sub["connections"] if c["to"] != "gen_outputs"] + [
        {"from": n, "from_port": p, "to": "gen_outputs", "to_port": i}
        for i, (n, p) in enumerate(order)]
    gout["ports"] = [{"name": name, "type": out_types[(n, p)], "group_size": 0}
                     for n, p, name in outputs]


def link_also(g: dict, sub_name: str, slot_id: str, node_name: str, widget: str) -> None:
    """Make one exposed subgraph parameter drive a second inner parameter,
    e.g. a "Pebble size" that sets both scale_x and scale_y. Material Maker
    writes a linked_control to every entry of linked_widgets; the first
    entry stays the primary one (mm-play's slider binds only that one)."""
    remote = node(node(g, sub_name), "gen_parameters")
    widget_def = next(w for w in remote["widgets"] if w["name"] == slot_id)
    widget_def["linked_widgets"].append({"node": node_name, "widget": widget})


def widen_widget(g: dict, sub_name: str, slot_id: str, maximum: float,
                 catalog: dict) -> None:
    """Give one exposed subgraph parameter its own slider range, wider than
    its inner node type allows (e.g. a "Grain scale" preset of 128 on a
    perlin whose scale slider stops at 32).

    A linked_control always copies its range from the linked node type's
    definition, so it cannot be widened. This converts the widget to a
    Material Maker named_parameter (min, step and the current value taken
    from the old primary link, `maximum` as the new max) and writes
    "$<slot_id>" into every inner parameter it was linked to. Material Maker
    substitutes the named value there, so the graph renders the same
    numbers; mm-play reads the range off the widget. The linked_widgets key
    is dropped, not emptied: MM's loader deletes a widget whose
    linked_widgets resolves to an empty list."""
    sub = node(g, sub_name)
    remote = node(sub, "gen_parameters")
    widget = next(w for w in remote["widgets"] if w["name"] == slot_id)
    links = widget["linked_widgets"]
    primary = node(sub, links[0]["node"])
    pdef = next(p for p in catalog[primary["type"]]["parameters"]
                if p["name"] == links[0]["widget"])
    value = remote["parameters"][slot_id]
    if pdef.get("type") != "float" or maximum <= pdef["max"]:
        raise ValueError(f"{sub_name}/{slot_id}: only a float widget can be widened, "
                         f"to a max above its {pdef.get('max')}")
    if not pdef["min"] <= value <= maximum:
        raise ValueError(f"{sub_name}/{slot_id}: value {value} outside "
                         f"[{pdef['min']}, {maximum}]")
    for link in links:
        node(sub, link["node"])["parameters"][link["widget"]] = "$" + slot_id
    shortdesc = widget["shortdesc"]
    widget.clear()
    widget.update({"name": slot_id, "shortdesc": shortdesc, "label": "",
                   "type": "named_parameter", "min": pdef["min"], "max": maximum,
                   "step": pdef["step"], "default": value})
