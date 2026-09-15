"""Static (no-render) audit for a real root-caused bug class: a cookbook
material whose albedo relief source and normal relief source come from
DIFFERENT pattern generators, so the surface relief does not line up with
the color grain. Root-caused in s02_gray_granite (2026-09-14): albedo comes
from `fleck_color/FleckCells` (a voronoi), normal comes from a separate
`stone_relief/ReliefCells` (a different voronoi instance) -- disjoint
sources, so the bump never tracks the color.

This is pure static graph analysis over the tracked `.ptex` JSON -- no
Godot, no rendering. See docs/superpowers/sdd/2026-09-14-showcase-lighting-
refresh/task-A-brief.md for the full design and graph-model background.

Graph model (verified against a real cookbook file):
- A `.ptex` is `{"nodes": [...], "connections": [...], ...}`. Each
  connection is `{"from": <name>, "from_port": int, "to": <name>,
  "to_port": int}`.
- The single node with type == "material" is the output
  (mm_mcp.graph.find_material_node). On it, input port 0 = albedo, input
  port 4 = normal (verified: granite wires its `stone_relief` subgraph's
  normal output to Material port 4 and its `fleck_color` subgraph's albedo
  output to port 0).
- A node with type == "graph" is a subgraph carrying its own nested `nodes`
  + `connections`. Inside it:
  - `gen_inputs` (type "ios") is the INPUT proxy -- an inner connection
    whose `from` is `gen_inputs` port K means "this consumes the
    subgraph's external input port K"; to continue tracing upstream, jump
    OUT to the external connection feeding this subgraph node's
    `to_port == K` in the ENCLOSING scope.
  - `gen_outputs` (type "ios") is the OUTPUT proxy -- the inner connection
    whose `to` is `gen_outputs` port N produces the subgraph's external
    output port N; to trace what feeds external output N, find the inner
    connection with `to == "gen_outputs"` and `to_port == N` and start
    from its `from` node.
  - `gen_parameters` (type "remote") is exposed params -- irrelevant to
    dataflow tracing, never visited here.
- "Pattern generators" (the "sources" this audit cares about) are nodes
  whose `type` is in `_NOISE_PATTERN_NODES`, the curated list already
  maintained by quality/node_usage_audit.py for the same node vocabulary.

Traversal is exact dataflow reachability, not "reachable by any wire into
the subgraph": if a subgraph node has an external input that is wired
internally to a dead branch that never reaches the output port actually
used, that external feeder is correctly NOT counted as a source (see
docs/evidence/normal_albedo_audit.md's note on granite's own
`FleckBlendUnused` node for a real example of this).

Run: python -m quality.normal_albedo_audit
"""
import json
import os
import sys
from pathlib import Path

from mm_mcp.graph import find_material_node

from quality.node_usage_audit import _NOISE_PATTERN_NODES

_ALBEDO_PORT = 0
_NORMAL_PORT = 4


def _index_by_name(nodes: list) -> dict:
    return {n["name"]: n for n in nodes if "name" in n}


def _explore(scope_stack: list, node_name: str, port: int, visited: set, sources: set) -> None:
    """Walk upstream from (node_name, port) in the current (innermost)
    scope, adding path-qualified pattern-generator ids to `sources`.

    scope_stack[-1] is the current scope: a dict with `nodes_by_name`,
    `connections`, `prefix` (qualifier prepended to node names found in
    this scope) and `entry_name` (this subgraph's own node name as seen
    from the enclosing scope; None for the root scope).
    """
    scope_id = id(scope_stack[-1])
    key = (scope_id, node_name, port)
    if key in visited:
        return
    visited.add(key)

    scope = scope_stack[-1]
    nodes_by_name = scope["nodes_by_name"]
    connections = scope["connections"]
    prefix = scope["prefix"]

    for conn in connections:
        if conn.get("to") != node_name or conn.get("to_port", 0) != port:
            continue
        from_name = conn.get("from")
        from_port = conn.get("from_port", 0)
        from_node = nodes_by_name.get(from_name)
        if from_node is None:
            continue
        ftype = from_node.get("type")

        if ftype == "ios" and from_name == "gen_inputs":
            # Jump out to the enclosing scope: this subgraph's own external
            # input port `from_port` is fed by whatever connects to this
            # subgraph node (scope["entry_name"]) at that port, one level up.
            if len(scope_stack) < 2 or scope["entry_name"] is None:
                continue
            outer_stack = scope_stack[:-1]
            _explore(outer_stack, scope["entry_name"], from_port, visited, sources)

        elif ftype == "graph":
            inner_nodes = from_node.get("nodes", [])
            inner_conns = from_node.get("connections", [])
            inner_frame = {
                "nodes_by_name": _index_by_name(inner_nodes),
                "connections": inner_conns,
                "prefix": prefix + from_name + "/",
                "entry_name": from_name,
            }
            inner_stack = scope_stack + [inner_frame]
            _explore(inner_stack, "gen_outputs", from_port, visited, sources)

        else:
            if ftype in _NOISE_PATTERN_NODES:
                sources.add(prefix + from_name)
            # Keep exploring upstream of this node across every input port
            # that actually feeds it, in case a source feeds a source.
            in_ports = {c.get("to_port", 0) for c in connections if c.get("to") == from_name}
            for p in in_ports:
                _explore(scope_stack, from_name, p, visited, sources)


def trace_sources(ptex: dict, material_input_port: int) -> set:
    """Path-qualified pattern-generator source ids feeding `material_input_port`
    on the graph's single Material node, tracing back through connections
    and descending/ascending through subgraph gen_inputs/gen_outputs proxies.
    Pure, no I/O."""
    material = find_material_node(ptex)
    root_frame = {
        "nodes_by_name": _index_by_name(ptex.get("nodes", [])),
        "connections": ptex.get("connections", []),
        "prefix": "",
        "entry_name": None,
    }
    sources: set = set()
    visited: set = set()
    _explore([root_frame], material["name"], material_input_port, visited, sources)
    return sources


def audit_graph(ptex: dict) -> dict:
    """{"albedo_sources", "normal_sources", "flagged"} for one material
    graph. Flagged iff both source sets are non-empty AND disjoint -- a flat
    albedo or an unconnected normal has nothing to line up, so it is not
    flagged."""
    albedo_sources = trace_sources(ptex, _ALBEDO_PORT)
    normal_sources = trace_sources(ptex, _NORMAL_PORT)
    flagged = bool(albedo_sources) and bool(normal_sources) and albedo_sources.isdisjoint(normal_sources)
    return {
        "albedo_sources": sorted(albedo_sources),
        "normal_sources": sorted(normal_sources),
        "flagged": flagged,
    }


def _default_cookbook_dir() -> str:
    try:
        from mm_mcp.config import load_config
        return load_config().cookbook_dir or "cookbook"
    except Exception:
        return "cookbook"


def audit_cookbook(cookbook_dir=None) -> list:
    """audit_graph over every <category>/<id>.ptex under cookbook_dir
    (default: the repo cookbook/, honoring MM_COOKBOOK_DIR via
    mm_mcp.config when available). Returns a list of
    {"id", "category", "albedo_sources", "normal_sources", "flagged"},
    flagged-first then alphabetical by id."""
    if cookbook_dir is None:
        cookbook_dir = _default_cookbook_dir()
    cookbook_dir = Path(cookbook_dir)
    results = []
    if cookbook_dir.is_dir():
        for category_dir in sorted(p for p in cookbook_dir.iterdir() if p.is_dir()):
            for ptex_path in sorted(category_dir.glob("*.ptex")):
                with open(ptex_path, encoding="utf-8") as fh:
                    ptex = json.load(fh)
                report = audit_graph(ptex)
                results.append({
                    "id": ptex_path.stem,
                    "category": category_dir.name,
                    **report,
                })
    results.sort(key=lambda r: (not r["flagged"], r["id"]))
    return results


def _format_sources(sources: list) -> str:
    return ", ".join(sources) if sources else "(none)"


def main(argv=None) -> int:
    results = audit_cookbook()
    flagged = [r for r in results if r["flagged"]]
    lines = []
    for r in results:
        tag = "FLAG" if r["flagged"] else "ok  "
        lines.append(
            f"{tag}  {r['category']}/{r['id']}: "
            f"albedo=[{_format_sources(r['albedo_sources'])}] "
            f"vs normal=[{_format_sources(r['normal_sources'])}]"
        )
    summary = f"{len(flagged)}/{len(results)} flagged"
    print("\n".join(lines))
    print(f"\n{summary}")

    md_lines = [
        "# Normal/albedo source-mismatch audit",
        "",
        "Static (no-render) check: does a material's normal-map relief come",
        "from the same pattern-generator source(s) as its albedo, so the",
        "bump lines up with the color grain? Flagged = both sides have a",
        "pattern-generator source and the two sets are disjoint.",
        "",
        f"**{summary}**",
        "",
        "| Flagged | Material | Albedo sources | Normal sources |",
        "|---|---|---|---|",
    ]
    for r in results:
        flag_cell = "YES" if r["flagged"] else ""
        md_lines.append(
            f"| {flag_cell} | {r['category']}/{r['id']} | "
            f"{_format_sources(r['albedo_sources'])} | "
            f"{_format_sources(r['normal_sources'])} |"
        )
    out_path = Path("docs/evidence/normal_albedo_audit.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
