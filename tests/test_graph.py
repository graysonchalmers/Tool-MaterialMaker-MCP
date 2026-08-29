import pytest

from mm_mcp.graph import find_material_node, isolate_node_output


def _simple_graph_ptex():
    """A minimal three-node ptex (perlin -> colorize -> material) used as the
    fixture for the find_material_node / isolate_node_output tests below.
    Built as a plain dict on purpose: this is exactly the .ptex on-disk shape
    those functions consume (nodes + connections), with no authoring-helper
    layer in between."""
    return {
        "type": "graph", "name": "graph", "label": "Graph",
        "node_position": {"x": 0, "y": 0}, "parameters": {},
        "nodes": [
            {"name": "perlin_0", "type": "perlin",
             "node_position": {"x": 0, "y": 0}, "parameters": {}},
            {"name": "mask_0", "type": "colorize",
             "node_position": {"x": 300, "y": 0}, "parameters": {}},
            {"name": "Material", "type": "material",
             "node_position": {"x": 600, "y": 0}, "parameters": {}},
        ],
        "connections": [
            {"from": "perlin_0", "from_port": 0, "to": "mask_0", "to_port": 0},
            {"from": "mask_0", "from_port": 0, "to": "Material", "to_port": 0},
        ],
    }


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
