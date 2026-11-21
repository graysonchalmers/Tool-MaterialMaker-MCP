from copy import deepcopy

import pytest

from mm_mcp.authoring import GraphEditError, describe_graph, patch_graph
from mm_mcp.validator import validate_graph


CATALOG = {"material": {"type": "material", "inputs": [{"name": "depth_tex", "type": "f"}],
                        "outputs": [], "parameters": []}}


def native_graph():
    return {"type": "graph", "nodes": [
        {"name": "SubstrateLayout", "type": "shader", "node_position": {"x": 4, "y": 8},
         "parameters": {"joints": 0.022}, "shader_model": {
             "parameters": [{"name": "joints", "type": "float", "label": "Mortar joints",
                             "min": 0, "max": 0.15, "step": 0.001, "default": 0.022}],
             "outputs": [{"type": "f", "shortdesc": "Physical height", "f": "$joints"}],
         }},
        {"name": "Material", "type": "material"},
        {"name": "ExportHeight16", "type": "export", "parameters": {
            "suffix": "$project-height16", "size": 11, "format": 0,
        }},
    ], "connections": [
        {"from": "SubstrateLayout", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "SubstrateLayout", "from_port": 0, "to": "ExportHeight16", "to_port": 0},
    ]}


def test_describe_graph_returns_named_native_controls_and_exports():
    description = describe_graph(native_graph(), CATALOG)
    control = next(control for control in description["controls"] if control["id"] == "SubstrateLayout/joints")
    assert {key: control[key] for key in ("label", "value", "type")} == {
        "label": "Mortar joints", "value": 0.022, "type": "float",
    }
    assert description["nodes"][0]["outputs"][0]["name"] == "Physical height"
    assert "shader_model" not in description["nodes"][0]
    assert description["exports"][-1] == {
        "node": "ExportHeight16", "type": "export", "suffix": "$project-height16",
        "size_exponent": 11, "format": "PNG",
    }


def test_patch_graph_updates_typed_fields_without_losing_native_data():
    source = native_graph()
    original = deepcopy(source)
    result = patch_graph(source, [
        {"op": "set_param", "node": "SubstrateLayout", "parameter": "Mortar joints", "value": 0.031},
        {"op": "set_param", "node": "ExportHeight16", "parameter": "format", "value": "exr"},
        {"op": "connect", "from_node": "SubstrateLayout", "from_port": "Physical height",
         "to_node": "ExportHeight16", "to_port": "in"},
    ], CATALOG)
    revised = result["graph"]
    assert source == original
    assert revised["nodes"][0]["parameters"]["joints"] == 0.031
    assert revised["nodes"][0]["shader_model"] == original["nodes"][0]["shader_model"]
    assert revised["nodes"][0]["node_position"] == original["nodes"][0]["node_position"]
    assert revised["nodes"][2]["parameters"]["format"] == 3
    assert result["diff"][0] == {"op": "set_param", "node": "SubstrateLayout", "parameter": "joints",
                                  "before": 0.022, "after": 0.031}
    assert result["diff"][2]["after"] == original["connections"][1]
    assert not validate_graph(revised, CATALOG, strict=True)


def test_patch_graph_reports_alternatives_and_does_not_apply_failed_batch():
    graph = native_graph()
    initial = deepcopy(graph)
    with pytest.raises(GraphEditError) as failure:
        patch_graph(graph, [
            {"op": "set_param", "node": "SubstrateLayout", "parameter": "joints", "value": 0.03},
            {"op": "set_param", "node": "ExportHeight16", "parameter": "format", "value": "TIFF"},
        ], CATALOG)
    assert failure.value.problem["code"] == "invalid_enum_label"
    assert failure.value.problem["edit_index"] == 1
    assert failure.value.problem["alternatives"] == ["PNG", "JPG", "WEBP", "EXR"]
    assert graph == initial


def test_patch_graph_resolves_nested_path_and_port_choices():
    graph = native_graph()
    nested = {"name": "Structure", "type": "graph", "nodes": [deepcopy(graph["nodes"][0])], "connections": []}
    graph["nodes"].append(nested)
    result = patch_graph(graph, [
        {"op": "set_param", "node": "Structure/SubstrateLayout", "parameter": "joints", "value": 0.03},
    ], CATALOG)
    assert result["graph"]["nodes"][-1]["nodes"][0]["parameters"]["joints"] == 0.03
    assert graph["nodes"][0]["parameters"]["joints"] == 0.022
    with pytest.raises(GraphEditError) as failure:
        patch_graph(graph, [
            {"op": "connect", "from_node": "SubstrateLayout", "from_port": "height",
             "to_node": "Material", "to_port": "depth_tex"},
        ], CATALOG)
    assert failure.value.problem["code"] == "unknown_port"
    assert failure.value.problem["alternatives"][0]["name"] == "Physical height"


@pytest.mark.parametrize("suffix", ["../outside", "../../outside.png", "..\\outside", "/tmp/abs", "C:relative"])
def test_native_export_path_is_checked_in_both_validation_modes_and_patch(suffix):
    graph = native_graph()
    graph["nodes"][-1]["parameters"]["suffix"] = suffix
    for strict in (False, True):
        assert any(problem["code"] == "unsafe_export_filename"
                   for problem in validate_graph(graph, CATALOG, strict=strict))
    with pytest.raises(GraphEditError) as failure:
        patch_graph(native_graph(), [
            {"op": "set_param", "node": "ExportHeight16", "parameter": "suffix", "value": suffix},
        ], CATALOG)
    assert failure.value.problem["code"] == "unsafe_export_filename"


def test_strict_validator_checks_native_shader_port_types_and_structure():
    graph = native_graph()
    graph["nodes"][0]["parameters"]["joints"] = "wider"
    graph["nodes"][0]["shader_model"]["outputs"][0]["type"] = "sdf2d"
    graph["nodes"].append(deepcopy(graph["nodes"][0]))
    graph["connections"].append(deepcopy(graph["connections"][0]))
    findings = validate_graph(graph, CATALOG, strict=True)
    assert {item["code"] for item in findings} == {
        "invalid_parameter_type", "duplicate_node_name", "duplicate_input_connection", "incompatible_port_types",
    }
    assert validate_graph({"nodes": [], "connections": []}, CATALOG, strict=True)[0]["code"] == "missing_output"


def test_patch_graph_supports_and_preserves_native_compact_connections():
    graph = native_graph()
    graph["connections"] = {edge["to"]: {str(edge["to_port"]): {
        "node": edge["from"], "port": edge["from_port"],
    }} for edge in graph["connections"]}
    result = patch_graph(graph, [
        {"op": "disconnect", "from_node": "SubstrateLayout", "from_port": "Physical height",
         "to_node": "Material", "to_port": "depth_tex"},
    ], CATALOG)
    assert result["graph"]["connections"] == {"ExportHeight16": {"0": {"node": "SubstrateLayout", "port": 0}}}
    assert set(graph["connections"]) == {"Material", "ExportHeight16"}


def test_patch_enforces_exposed_numeric_ranges_but_legacy_values_are_advisory():
    graph = native_graph()
    with pytest.raises(GraphEditError) as failure:
        patch_graph(graph, [
            {"op": "set_param", "node": "SubstrateLayout", "parameter": "joints", "value": 4},
        ], CATALOG)
    assert failure.value.problem["code"] == "parameter_out_of_range"
    assert failure.value.problem["alternatives"] == [{"min": 0, "max": 0.15, "step": 0.001}]
    graph["nodes"][0]["parameters"]["joints"] = 4
    assert validate_graph(graph, CATALOG, strict=True)[0]["severity"] == "warning"
