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


def test_compound_param_resolves_range_from_linked_inner_shader_node():
    """normal_map is a compound ("generic") node: no shader_model of its own,
    just a nested graph. Its remote widget param1 ("Strength") is wired via
    linked_widgets to edge_detect_1.amount, an inline shader node whose own
    shader_model declares min/max/step. The compound param should carry that
    real range through, not leave it null."""
    node = parse_node(_mmg("normal_map"))
    params = {p["name"]: p for p in node["parameters"]}
    strength = params["param1"]
    assert strength["desc"] == "Strength"  # own name/desc kept
    assert strength["type"] == "float"
    assert strength["min"] == 0
    assert strength["max"] == 2
    assert strength["step"] == 0.01
    # The real default is normal_map's own remote-node value (1), not
    # edge_detect_1.amount's default (0.5) -- see
    # test_compound_param_default_comes_from_remote_node_not_linked_inner_node
    # in test_catalog_build.py for the general rule.
    assert strength["default"] == 1


def test_compound_param_falls_back_to_none_when_inner_node_unresolvable():
    """normal_map's param0 ("Resolution") links to the 'buffer' inner node,
    which has no inline shader_model (buffer is a SPECIAL_TYPE). Resolution
    must gracefully fall back to an unranged param, not crash."""
    node = parse_node(_mmg("normal_map"))
    params = {p["name"]: p for p in node["parameters"]}
    resolution = params["param0"]
    assert resolution["desc"] == "Resolution"
    assert resolution["type"] is None
    assert resolution.get("min") is None
    assert resolution.get("max") is None


def test_parse_noncontiguous_enum_uses_index_range_not_underlying_values():
    """wavelet_noise's `type` enum has NON-contiguous underlying `value`
    fields: "Add 1/2/3" -> "1"/"2"/"3" and "Mult 2/3" -> "-2"/"-3". It is
    tempting to derive the valid range from those literals (which would give
    -3..3), but that is wrong: Material Maker stores an enum parameter as an
    *ordinal index* into the values list and, at shader-generation time,
    looks up values[index].value (gen_shader.gd:527-529 and
    sdf_builder.gd:120). An index <0 or >=len is clamped to 0. So the valid
    range is the index range [0, len-1], and to select "Mult 3" a graph must
    store index 4 (which noise_gallery.py already does), NOT the literal -3.
    This test pins that: min/max are the index bounds, not the value bounds."""
    node = parse_node(_mmg("wavelet_noise"))
    params = {p["name"]: p for p in node["parameters"]}
    t = params["type"]
    assert t["type"] == "enum"
    assert t["values"] == ["Add 1", "Add 2", "Add 3", "Mult 2", "Mult 3"]
    assert t["min"] == 0
    assert t["max"] == 4  # 5 options -> index range 0..4, never -3..3


def test_enum_captures_confusable_numeric_literals():
    """wavelet_noise.type is the trap that produced the t09 bug: its .mmg
    entries carry numeric `value` literals ("1","2","3","-2","-3") that do NOT
    equal their ordinal index (Material Maker stores the index, so "Mult 3" is
    index 4, not -3). Capture those literals so the validator can name the
    intended index when an author types the raw literal."""
    node = parse_node(_mmg("wavelet_noise"))
    params = {p["name"]: p for p in node["parameters"]}
    t = params["type"]
    assert t["type"] == "enum"
    assert t["value_literals"] == ["1", "2", "3", "-2", "-3"]


def test_enum_with_name_literals_has_no_value_literals():
    """blend.blend_type's literals are plain names ("normal", "multiply", ...),
    not numbers, so nobody can confuse a literal with an index. Such an enum
    must NOT carry value_literals - the field is only for numeric, index-
    mismatched literals, keeping the catalog lean for the common case."""
    node = parse_node(_mmg("blend"))
    bt = {p["name"]: p for p in node["parameters"]}["blend_type"]
    assert "value_literals" not in bt
