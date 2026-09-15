"""TDD tests for quality.normal_albedo_audit -- the static (no-render) audit
that flags cookbook materials whose albedo relief source and normal relief
source come from disjoint pattern-generator sets (root-caused in
s02_gray_granite: albedo from FleckCells/voronoi, normal from a separate
ReliefCells/voronoi, so the relief does not line up with the color grain).

Fixtures are synthetic minimal ptex dicts (deterministic, not coupled to
cookbook contents) except test_granite_is_flagged, which is the real-anchor
regression test for the known bug.
"""
import os

from quality.normal_albedo_audit import audit_graph, trace_sources


def test_disjoint_sources_flagged():
    ptex = {
        "nodes": [
            {"name": "A", "type": "voronoi", "parameters": {}},
            {"name": "chain", "type": "colorize", "parameters": {}},
            {"name": "B", "type": "perlin", "parameters": {}},
            {"name": "Material", "type": "material", "parameters": {}},
        ],
        "connections": [
            {"from": "A", "from_port": 0, "to": "chain", "to_port": 0},
            {"from": "chain", "from_port": 0, "to": "Material", "to_port": 0},
            {"from": "B", "from_port": 0, "to": "Material", "to_port": 4},
        ],
    }
    result = audit_graph(ptex)
    assert result["flagged"] is True
    albedo = set(result["albedo_sources"])
    normal = set(result["normal_sources"])
    assert albedo == {"A"}
    assert normal == {"B"}
    assert albedo.isdisjoint(normal)


def test_shared_source_not_flagged():
    ptex = {
        "nodes": [
            {"name": "A", "type": "voronoi", "parameters": {}},
            {"name": "colorize1", "type": "colorize", "parameters": {}},
            {"name": "normal_map1", "type": "normal_map", "parameters": {}},
            {"name": "Material", "type": "material", "parameters": {}},
        ],
        "connections": [
            {"from": "A", "from_port": 0, "to": "colorize1", "to_port": 0},
            {"from": "colorize1", "from_port": 0, "to": "Material", "to_port": 0},
            {"from": "A", "from_port": 0, "to": "normal_map1", "to_port": 0},
            {"from": "normal_map1", "from_port": 0, "to": "Material", "to_port": 4},
        ],
    }
    result = audit_graph(ptex)
    assert result["flagged"] is False
    assert set(result["albedo_sources"]) == {"A"}
    assert set(result["normal_sources"]) == {"A"}


def test_flat_albedo_not_flagged():
    ptex = {
        "nodes": [
            {"name": "FlatColor", "type": "uniform", "parameters": {}},
            {"name": "B", "type": "voronoi", "parameters": {}},
            {"name": "Material", "type": "material", "parameters": {}},
        ],
        "connections": [
            {"from": "FlatColor", "from_port": 0, "to": "Material", "to_port": 0},
            {"from": "B", "from_port": 0, "to": "Material", "to_port": 4},
        ],
    }
    result = audit_graph(ptex)
    assert result["albedo_sources"] == []
    assert result["flagged"] is False


def test_subgraph_traversal():
    """Cover both a self-contained subgraph (generator inside, wired straight
    to gen_outputs) feeding albedo, and a subgraph that consumes an EXTERNAL
    input via gen_inputs feeding normal."""
    ptex = {
        "nodes": [
            {
                "name": "sg",
                "type": "graph",
                "parameters": {},
                "nodes": [
                    {"name": "gen_inputs", "type": "ios", "parameters": {}, "ports": []},
                    {"name": "gen_outputs", "type": "ios", "parameters": {}, "ports": [{"name": "out0", "type": "rgba"}]},
                    {"name": "InnerVoronoi", "type": "voronoi", "parameters": {}},
                ],
                "connections": [
                    {"from": "InnerVoronoi", "from_port": 0, "to": "gen_outputs", "to_port": 0},
                ],
            },
            {
                "name": "ExtA",
                "type": "voronoi",
                "parameters": {},
            },
            {
                "name": "sg2",
                "type": "graph",
                "parameters": {},
                "nodes": [
                    {"name": "gen_inputs", "type": "ios", "parameters": {}, "ports": [{"name": "in0", "type": "f"}]},
                    {"name": "gen_outputs", "type": "ios", "parameters": {}, "ports": [{"name": "out0", "type": "rgba"}]},
                    {"name": "Colorize", "type": "colorize", "parameters": {}},
                ],
                "connections": [
                    {"from": "gen_inputs", "from_port": 0, "to": "Colorize", "to_port": 0},
                    {"from": "Colorize", "from_port": 0, "to": "gen_outputs", "to_port": 0},
                ],
            },
            {"name": "Material", "type": "material", "parameters": {}},
        ],
        "connections": [
            {"from": "sg", "from_port": 0, "to": "Material", "to_port": 0},
            {"from": "ExtA", "from_port": 0, "to": "sg2", "to_port": 0},
            {"from": "sg2", "from_port": 0, "to": "Material", "to_port": 4},
        ],
    }
    result = audit_graph(ptex)
    assert set(result["albedo_sources"]) == {"sg/InnerVoronoi"}
    assert set(result["normal_sources"]) == {"ExtA"}
    assert result["flagged"] is True

    # trace_sources directly, matching the public API
    assert trace_sources(ptex, 0) == {"sg/InnerVoronoi"}
    assert trace_sources(ptex, 4) == {"ExtA"}


def test_granite_normal_matches_albedo():
    """Real-anchor regression test. Originally the root-caused bug (albedo
    from FleckCells/voronoi_0, normal from a separate ReliefCells/voronoi_1
    that could never share a cell layout -- flagged True). Fixed 2026-09-14
    by feeding normal_map_0 from voronoi_0 port 2, the same per-cell random
    already driving the albedo, so the relief now registers with the color.
    If this ever flags again, the fix regressed -- someone rewired the
    normal back onto a disjoint source."""
    import json

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo_root, "cookbook", "stone", "s02_gray_granite.ptex")
    with open(path, encoding="utf-8") as fh:
        ptex = json.load(fh)
    result = audit_graph(ptex)
    assert result["flagged"] is False
    albedo = set(result["albedo_sources"])
    normal = set(result["normal_sources"])
    assert albedo and normal
    assert albedo & normal
