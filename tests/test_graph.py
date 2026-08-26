from mm_mcp.graph import Graph


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
