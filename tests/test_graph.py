import pytest

from mm_mcp.graph import Graph, find_material_node, isolate_node_output


def test_build_minimal_graph_to_ptex():
    g = Graph()
    g.add_node("perlin_0", "perlin", {"scale_x": 4, "scale_y": 4}, x=0, y=0)
    g.add_node("colorize_0", "colorize", {}, x=300, y=0)
    g.add_node("Material", "material", {}, x=600, y=0)
    g.connect("perlin_0", 0, "colorize_0", 0)
    g.connect("colorize_0", 0, "Material", 0)
    ptex = g.to_ptex()
    assert ptex["type"] == "graph"
    assert len(ptex["nodes"]) == 3
    assert len(ptex["connections"]) == 2
    names = {n["name"] for n in ptex["nodes"]}
    assert names == {"perlin_0", "colorize_0", "Material"}
    c0 = ptex["connections"][0]
    assert c0 == {"from": "perlin_0", "from_port": 0,
                  "to": "colorize_0", "to_port": 0}


def test_roundtrip_from_ptex():
    g = Graph()
    g.add_node("a", "perlin", {}, 0, 0)
    d = g.to_ptex()
    g2 = Graph.from_ptex(d)
    assert g2.to_ptex()["nodes"][0]["type"] == "perlin"


def _simple_graph_ptex():
    g = Graph()
    g.add_node("perlin_0", "perlin", {}, 0, 0)
    g.add_node("mask_0", "colorize", {}, 300, 0)
    g.add_node("Material", "material", {}, 600, 0)
    g.connect("perlin_0", 0, "mask_0", 0)
    g.connect("mask_0", 0, "Material", 0)
    return g.to_ptex()


def test_find_material_node_returns_the_material_node():
    ptex = _simple_graph_ptex()
    material = find_material_node(ptex)
    assert material["name"] == "Material"
    assert material["type"] == "material"


def test_find_material_node_raises_when_none_present():
    ptex = _simple_graph_ptex()
    ptex["nodes"] = [n for n in ptex["nodes"] if n["type"] != "material"]
    with pytest.raises(ValueError, match="found 0"):
        find_material_node(ptex)


def test_find_material_node_raises_when_multiple_present():
    ptex = _simple_graph_ptex()
    ptex["nodes"].append({"name": "Material2", "type": "material",
                           "node_position": {"x": 0, "y": 0}, "parameters": {}})
    with pytest.raises(ValueError, match="found 2"):
        find_material_node(ptex)


def test_isolate_node_output_rewires_node_into_albedo():
    ptex = _simple_graph_ptex()
    isolated = isolate_node_output(ptex, "perlin_0")
    conns = isolated["connections"]
    assert {"from": "perlin_0", "from_port": 0,
            "to": "Material", "to_port": 0} in conns
    # the original mask_0 -> Material connection is gone
    assert not any(c["to"] == "Material" and c["to_port"] == 0
                   and c["from"] == "mask_0" for c in conns)
    # unrelated connections survive untouched
    assert {"from": "perlin_0", "from_port": 0,
            "to": "mask_0", "to_port": 0} in conns


def test_isolate_node_output_honors_the_requested_port():
    ptex = _simple_graph_ptex()
    isolated = isolate_node_output(ptex, "perlin_0", port=2)
    assert {"from": "perlin_0", "from_port": 2,
            "to": "Material", "to_port": 0} in isolated["connections"]


def test_isolate_node_output_does_not_mutate_input():
    ptex = _simple_graph_ptex()
    original_connections = [dict(c) for c in ptex["connections"]]
    isolate_node_output(ptex, "perlin_0")
    assert ptex["connections"] == original_connections


def test_isolate_node_output_raises_for_unknown_node():
    ptex = _simple_graph_ptex()
    with pytest.raises(ValueError, match="no node named 'nope'"):
        isolate_node_output(ptex, "nope")


def test_isolate_node_output_raises_when_no_material_node():
    ptex = _simple_graph_ptex()
    ptex["nodes"] = [n for n in ptex["nodes"] if n["type"] != "material"]
    with pytest.raises(ValueError, match="found 0"):
        isolate_node_output(ptex, "perlin_0")
