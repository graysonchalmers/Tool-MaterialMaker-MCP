"""Bridge between a cookbook material's exposed subgraph parameters and web
sliders. Each retrofitted material has one or more `type: "graph"` nodes; each
carries a `remote` node (gen_parameters) whose `widgets` are the author-chosen
exposed parameters. This module turns those widgets, plus the catalog's per-param
ranges, into slider specs, and applies a set of slider values back onto a graph.
"""
from typing import Any

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


def derive_sliders(graph: dict, catalog: dict) -> list[dict]:
    """One slider spec per exposed widget across all subgraph nodes in `graph`."""
    sliders: list[dict] = []
    for node in graph.get("nodes", []):
        if node.get("type") != "graph":
            continue
        group = node.get("label") or node.get("name", "")
        params = node.get("parameters", {})
        for widget in _remote_widgets(node):
            slot_id = widget.get("name")
            if not slot_id:
                continue
            linked = (widget.get("linked_widgets") or [{}])[0]
            inode_name = linked.get("node")
            iparam = linked.get("widget")
            itype = _internal_type(node, inode_name)
            pdef = _param_def(catalog, itype, iparam) if itype else None
            kind = _KIND.get((pdef or {}).get("type"), "float")
            sliders.append({
                "group": group,
                "slot_id": slot_id,
                "label": widget.get("shortdesc") or slot_id,
                "kind": kind,
                "min": (pdef or {}).get("min"),
                "max": (pdef or {}).get("max"),
                "step": (pdef or {}).get("step"),
                "value": params.get(slot_id),
                "binding": {"node": inode_name, "widget": iparam},
            })
    return sliders
