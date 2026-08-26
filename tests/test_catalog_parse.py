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


def test_generic_input_expansion_produces_distinct_dicts():
    """mwf_mix has '#'-suffixed inputs (h#, c#, orm#, em#, nm#) repeated
    generic_size times. Each repeated entry must be its own dict object,
    not the same dict aliased multiple times -- mutating one repetition
    must not affect the others."""
    node = parse_node(_mmg("mwf_mix"))
    names = [i["name"] for i in node["inputs"]]
    assert names.count("h#") == 2  # generic_size == 2 for mwf_mix

    h_entries = [i for i in node["inputs"] if i["name"] == "h#"]
    assert len(h_entries) == 2
    assert h_entries[0] is not h_entries[1]

    h_entries[0]["name"] = "h0"
    assert h_entries[1]["name"] == "h#"
