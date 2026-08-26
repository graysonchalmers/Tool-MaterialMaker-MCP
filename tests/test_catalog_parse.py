import os
from mm_mcp.catalog_builder import parse_node
from mm_mcp.config import load_config

cfg = load_config()


def _mmg(name):
    return os.path.join(cfg.nodes_dir, name + ".mmg")


def test_parse_blend_inputs_and_ports():
    node = parse_node(_mmg("blend"))
    assert node["type"] == "blend"
    names = [i["name"] for i in node["inputs"]]
    assert names == ["s1", "s2", "a"]  # port order matters
    assert node["outputs"][0]["type"] == "rgba"


def test_parse_blend_enum_param():
    node = parse_node(_mmg("blend"))
    params = {p["name"]: p for p in node["parameters"]}
    bt = params["blend_type"]
    assert bt["type"] == "enum"
    assert len(bt["values"]) == 15
    assert bt["min"] == 0 and bt["max"] == 14
    amount = params["amount"]
    assert amount["type"] == "float"
    assert amount["min"] == 0 and amount["max"] == 1
