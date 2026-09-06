import copy
import pytest
from quality.author_helpers import rename_nodes


def _flat():
    return {
        "nodes": [
            {"name": "Material", "type": "material", "parameters": {}},
            {"name": "perlin_0", "type": "perlin", "parameters": {}},
            {"name": "colorize_0", "type": "colorize", "parameters": {}},
        ],
        "connections": [
            {"from": "perlin_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
            {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
        ],
    }


def _grouped():
    return {
        "nodes": [
            {"name": "Material", "type": "material", "parameters": {}},
            {"name": "grain", "label": "Grain", "type": "graph", "parameters": {"param0": 4},
             "nodes": [
                 {"name": "gen_inputs", "type": "ios", "parameters": {}, "ports": []},
                 {"name": "gen_outputs", "type": "ios", "parameters": {}, "ports": []},
                 {"name": "gen_parameters", "type": "remote", "parameters": {"param0": 4},
                  "widgets": [{"name": "param0", "shortdesc": "Scale", "label": "",
                               "type": "linked_control",
                               "linked_widgets": [{"node": "perlin_0", "widget": "scale_x"}]}]},
                 {"name": "perlin_0", "type": "perlin", "parameters": {"scale_x": 4}},
                 {"name": "colorize_0", "type": "colorize", "parameters": {}},
             ],
             "connections": [
                 {"from": "perlin_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
                 {"from": "colorize_0", "from_port": 0, "to": "gen_outputs", "to_port": 0},
             ]},
        ],
        "connections": [
            {"from": "grain", "from_port": 0, "to": "Material", "to_port": 0},
        ],
    }


def test_renames_top_level_node_and_both_connection_ends():
    g = _flat()
    rename_nodes(g, {"perlin_0": "GrainNoise", "colorize_0": "WoodColor"})
    assert [n["name"] for n in g["nodes"]] == ["Material", "GrainNoise", "WoodColor"]
    assert g["connections"] == [
        {"from": "GrainNoise", "from_port": 0, "to": "WoodColor", "to_port": 0},
        {"from": "WoodColor", "from_port": 0, "to": "Material", "to_port": 0},
    ]


def test_renames_inside_subgraph_including_linked_widgets():
    g = _grouped()
    rename_nodes(g, {"perlin_0": "GrainNoise", "colorize_0": "WoodColor"})
    sub = g["nodes"][1]
    names = [n["name"] for n in sub["nodes"]]
    assert names == ["gen_inputs", "gen_outputs", "gen_parameters", "GrainNoise", "WoodColor"]
    assert sub["connections"][0] == {"from": "GrainNoise", "from_port": 0, "to": "WoodColor", "to_port": 0}
    remote = sub["nodes"][2]
    assert remote["widgets"][0]["linked_widgets"][0]["node"] == "GrainNoise"
    # the subgraph node itself and the outer wiring are untouched
    assert sub["name"] == "grain"
    assert g["connections"] == [{"from": "grain", "from_port": 0, "to": "Material", "to_port": 0}]


def test_does_not_touch_node_position_or_parameters():
    g = _grouped()
    g["nodes"][1]["nodes"][3]["node_position"] = {"x": 12.5, "y": -3}
    before = copy.deepcopy(g["nodes"][1]["nodes"][3])
    rename_nodes(g, {"perlin_0": "GrainNoise"})
    after = g["nodes"][1]["nodes"][3]
    assert after["node_position"] == before["node_position"]
    assert after["parameters"] == before["parameters"]


def test_unknown_source_name_raises_keyerror():
    with pytest.raises(KeyError):
        rename_nodes(_flat(), {"nope_0": "Whatever"})


def test_target_collision_with_sibling_raises_valueerror():
    with pytest.raises(ValueError):
        rename_nodes(_flat(), {"perlin_0": "colorize_0"})


@pytest.mark.parametrize("bad", ["Material", "gen_inputs", "gen_outputs", "gen_parameters"])
def test_reserved_names_cannot_be_source_or_target(bad):
    with pytest.raises(ValueError):
        rename_nodes(_grouped(), {bad: "X"})
    with pytest.raises(ValueError):
        rename_nodes(_grouped(), {"perlin_0": bad})


def test_mapping_applied_atomically_when_one_key_is_bad():
    g = _flat()
    with pytest.raises(KeyError):
        rename_nodes(g, {"perlin_0": "GrainNoise", "missing_0": "X"})
    assert [n["name"] for n in g["nodes"]] == ["Material", "perlin_0", "colorize_0"]


def test_two_sources_to_the_same_target_at_one_level_raise_valueerror():
    g = _flat()
    with pytest.raises(ValueError):
        rename_nodes(g, {"perlin_0": "Same", "colorize_0": "Same"})
    assert [n["name"] for n in g["nodes"]] == ["Material", "perlin_0", "colorize_0"]
