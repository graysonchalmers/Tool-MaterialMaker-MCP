"""Read-only metrics for a .ptex graph, for the inspect_project tool.

Deliberately tolerant (never raises on a malformed graph) and independent of
the node catalog: this answers "what is in this file" for a hand-edited .ptex
coming back through the round-trip loop, not "is it valid" (that is validator).
"""

import hashlib


def inspect_ptex(ptex: dict, file_bytes: bytes | None = None) -> dict:
    nodes = ptex.get("nodes", []) or []
    connections = ptex.get("connections", []) or []
    histogram: dict[str, int] = {}
    material_outputs: list[str] = []
    for n in nodes:
        t = n.get("type", "<untyped>")
        histogram[t] = histogram.get(t, 0) + 1
        if t == "material":
            material_outputs.append(n.get("name", "<unnamed>"))
    return {
        "sha256": hashlib.sha256(file_bytes).hexdigest() if file_bytes is not None else None,
        "node_count": len(nodes),
        "connection_count": len(connections),
        "node_types": dict(sorted(histogram.items())),
        "material_outputs": material_outputs,
    }
