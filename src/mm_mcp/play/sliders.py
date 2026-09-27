"""Bridge between a cookbook material's exposed subgraph parameters and web
sliders. Each retrofitted material has one or more `type: "graph"` nodes; each
carries a `remote` node (gen_parameters) whose `widgets` are the author-chosen
exposed parameters. This module turns those widgets, plus the catalog's per-param
ranges, into slider specs, and applies a set of slider values back onto a graph.
"""
import copy

# Material Maker param type -> slider kind.
_KIND = {
    "float": "float",
    "int": "int",
    "size": "int",
    "enum": "enum",
    "boolean": "bool",
    "color": "color",
    "gradient": "color",
}


def _remote_widgets(subgraph_node: dict) -> list[dict]:
    for inner in subgraph_node.get("nodes", []):
        if inner.get("type") == "remote":
            return inner.get("widgets", [])
    return []


def _internal_type(subgraph_node: dict, node_name: str) -> str | None:
    for inner in subgraph_node.get("nodes", []):
        if inner.get("name") == node_name:
            return inner.get("type")
    return None


def _param_def(catalog: dict, node_type: str, param_name: str) -> dict | None:
    node = catalog.get(node_type)
    if not node:
        return None
    for p in node.get("parameters", []):
        if p.get("name") == param_name:
            return p
    return None


def _links(widget: dict) -> list[dict]:
    """Every (node, widget) an exposed control drives. Material Maker lets one
    control link several inner params (e.g. a size driving scale_x and
    scale_y), so all of them move together."""
    return [{"node": l.get("node"), "widget": l.get("widget")}
            for l in widget.get("linked_widgets") or []] or [{"node": None, "widget": None}]


def derive_sliders(graph: dict, catalog: dict) -> list[dict]:
    """One slider spec per exposed widget across all subgraph nodes in `graph`.

    `slot_id` (e.g. "param0") is only unique within one subgraph; two
    subgraphs in the same material can both expose a "param0". Each slider's
    `id` (f"{subgraph_node_name}/{slot_id}") is unique across the whole
    material and is the key `apply_values` and the play API use to address
    one control without affecting any other subgraph.
    """
    sliders: list[dict] = []
    for node in graph.get("nodes", []):
        if node.get("type") != "graph":
            continue
        node_name = node.get("name", "")
        group = node.get("label") or node_name
        params = node.get("parameters", {})
        for widget in _remote_widgets(node):
            slot_id = widget.get("name")
            if not slot_id:
                continue
            if widget.get("type") == "named_parameter":
                # Carries its own float range (a host widget widened past its
                # inner node's slider); the inner params read "$<slot_id>",
                # so the only thing to set is the subgraph's own parameter.
                bindings = [{"node": node_name, "widget": slot_id}]
                pdef = {k: widget.get(k) for k in ("min", "max", "step")}
                kind = "float"
            else:
                bindings = _links(widget)
                inode_name, iparam = bindings[0]["node"], bindings[0]["widget"]
                itype = _internal_type(node, inode_name)
                pdef = _param_def(catalog, itype, iparam) if itype else None
                kind = _KIND.get((pdef or {}).get("type"), "float")
            sliders.append({
                "id": f"{node_name}/{slot_id}",
                "subgraph": node_name,
                "group": group,
                "slot_id": slot_id,
                "label": widget.get("shortdesc") or slot_id,
                "kind": kind,
                "min": (pdef or {}).get("min"),
                "max": (pdef or {}).get("max"),
                "step": (pdef or {}).get("step"),
                "value": params.get(slot_id),
                "binding": bindings[0],
                "bindings": bindings,
            })
    return sliders


def apply_values(graph: dict, values: dict) -> dict:
    """Write id->value (id = f"{subgraph_node_name}/{slot_id}", see
    `derive_sliders`) into exactly the one subgraph that owns that id.
    Returns a new graph; the input is not mutated. Unknown ids are ignored.
    Values are addressed by the unique per-slider id, not by the
    subgraph-local slot_id, so a value never fans out to another subgraph
    that happens to reuse the same slot_id (e.g. two subgraphs both
    exposing "param0")."""
    out = copy.deepcopy(graph)
    for node in out.get("nodes", []):
        if node.get("type") != "graph":
            continue
        node_name = node.get("name", "")
        widgets = _remote_widgets(node)
        by_slot = {w.get("name"): w for w in widgets}
        for slot_id, widget in by_slot.items():
            sid = f"{node_name}/{slot_id}"
            if sid not in values:
                continue
            value = values[sid]
            targets = {(b["node"], b["widget"]) for b in _links(widget)}
            for inner in node.get("nodes", []):
                for inode_name, iparam in targets:
                    if inner.get("name") == inode_name:
                        inner.setdefault("parameters", {})[iparam] = value
                if inner.get("type") == "remote":
                    inner.setdefault("parameters", {})[slot_id] = value
            node.setdefault("parameters", {})[slot_id] = value
    return out
