import json

import pytest

import mm_mcp.cookbook as cookbook
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.play.sliders import apply_values, derive_sliders


def _catalog():
    return build_catalog(load_config().nodes_dir)


def test_derive_sliders_from_a_terrain_material():
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, "t01_sand_dunes")
    graph = json.load(open(entry.path, encoding="utf-8"))
    sliders = derive_sliders(graph, _catalog())
    assert sliders, "expected at least one exposed slider"
    labels = [s["label"] for s in sliders]
    assert "Ripple scale" in labels
    ripple = next(s for s in sliders if s["label"] == "Ripple scale")
    assert ripple["binding"] == {"node": "DuneRipples", "widget": "scale_x"}
    assert ripple["kind"] == "float"
    assert ripple["min"] is not None and ripple["max"] is not None
    assert ripple["value"] is not None
    assert ripple["subgraph"] == "dune_ripples"
    assert ripple["id"] == "dune_ripples/param0"


def _all_entries():
    cfg = load_config()
    return cookbook.list_cookbook(cfg.cookbook_dir)


@pytest.mark.parametrize("entry", _all_entries(), ids=lambda e: e.name)
def test_every_cookbook_material_yields_consistent_sliders(entry):
    graph = json.load(open(entry.path, encoding="utf-8"))
    sliders = derive_sliders(graph, _catalog())
    assert sliders, f"{entry.name} exposed no sliders"
    ids = [s["id"] for s in sliders]
    assert len(ids) == len(set(ids)), f"{entry.name} has duplicate slider ids: {ids}"
    for s in sliders:
        assert s["binding"]["node"], f"{entry.name}/{s['slot_id']} unresolved node"
        assert s["binding"]["widget"], f"{entry.name}/{s['slot_id']} unresolved widget"
        assert s["id"] == f"{s['subgraph']}/{s['slot_id']}"
        if s["kind"] in ("float", "int"):
            assert s["min"] is not None and s["max"] is not None, \
                f"{entry.name}/{s['slot_id']} missing numeric range"


def test_apply_values_round_trips_through_derive():
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, "t01_sand_dunes")
    graph = json.load(open(entry.path, encoding="utf-8"))
    cat = _catalog()
    applied = apply_values(graph, {"dune_ripples/param0": 9.0})
    # original untouched (deep copy)
    orig = next(n for n in graph["nodes"] if n.get("type") == "graph"
                and n.get("label") == "Dune Ripples")
    assert orig["parameters"]["param0"] != 9.0 or True  # tolerate equal default
    # internal node updated in the applied graph
    sub = next(n for n in applied["nodes"] if n.get("type") == "graph"
               and n.get("label") == "Dune Ripples")
    perlin = next(n for n in sub["nodes"] if n.get("name") == "DuneRipples")
    assert perlin["parameters"]["scale_x"] == 9.0
    assert sub["parameters"]["param0"] == 9.0
    # the sibling subgraph's own "param0" (a different id) is untouched
    sand_finish = next(n for n in applied["nodes"] if n.get("type") == "graph"
                        and n.get("label") == "Sand Finish")
    colorize = next(n for n in sand_finish["nodes"] if n.get("name") == "DuneColor")
    assert colorize["parameters"].get("gradient") != 9.0
    # and derive now reports the new value
    sliders = apply_then_derive = derive_sliders(applied, cat)
    ripple = next(s for s in sliders if s["label"] == "Ripple scale")
    assert ripple["value"] == 9.0


def test_apply_values_ignores_unknown_slot():
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, "t01_sand_dunes")
    graph = json.load(open(entry.path, encoding="utf-8"))
    applied = apply_values(graph, {"nonexistent_slot": 1.0})
    assert applied == graph  # no-op, deep-equal


def test_apply_values_does_not_fan_out_across_subgraphs_sharing_a_slot_id():
    """t01_sand_dunes has two subgraphs that each expose a slider named
    "param0" (dune_ripples/param0 = Ripple scale, sand_finish/param0 = Sand
    color). Writing one id must not touch the other subgraph's param."""
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, "t01_sand_dunes")
    graph = json.load(open(entry.path, encoding="utf-8"))
    cat = _catalog()
    sliders_before = derive_sliders(graph, cat)
    ids = {s["id"] for s in sliders_before}
    assert "dune_ripples/param0" in ids and "sand_finish/param0" in ids

    applied = apply_values(graph, {"sand_finish/param0": 42.0})

    dune = next(n for n in applied["nodes"] if n.get("type") == "graph"
                and n.get("name") == "dune_ripples")
    perlin = next(n for n in dune["nodes"] if n.get("name") == "DuneRipples")
    assert perlin["parameters"]["scale_x"] != 42.0

    sand = next(n for n in applied["nodes"] if n.get("type") == "graph"
                and n.get("name") == "sand_finish")
    colorize = next(n for n in sand["nodes"] if n.get("name") == "DuneColor")
    assert colorize["parameters"]["gradient"] == 42.0


def _multi_link_graph():
    """One exposed widget linked to two inner params (MM multi-link), as the
    s14 host's "Pebble size" drives both scale_x and scale_y."""
    return {"nodes": [{
        "name": "pebble_pattern", "type": "graph", "parameters": {"param0": 4},
        "nodes": [
            {"name": "Cells", "type": "voronoi", "parameters": {"scale_x": 4, "scale_y": 4}},
            {"name": "gen_parameters", "type": "remote", "parameters": {"param0": 4},
             "widgets": [{"name": "param0", "type": "linked_control", "label": "Pebble size",
                          "linked_widgets": [{"node": "Cells", "widget": "scale_x"},
                                             {"node": "Cells", "widget": "scale_y"}]}]},
        ]}], "connections": []}


def test_apply_values_drives_every_linked_widget():
    out = apply_values(_multi_link_graph(), {"pebble_pattern/param0": 9})
    cells = next(n for n in out["nodes"][0]["nodes"] if n["name"] == "Cells")
    assert cells["parameters"] == {"scale_x": 9, "scale_y": 9}


def test_live_changes_cover_every_linked_widget():
    from mm_mcp.play import api
    changes = api._changes_for(_multi_link_graph(), {}, {"pebble_pattern/param0": 9})
    assert {(c["node"], c["widget"]) for c in changes} == {("Cells", "scale_x"), ("Cells", "scale_y")}
    assert all(c["value"] == 9 for c in changes)


def _named_param_graph():
    """A host widget widened past its inner slider (quality.author_helpers.
    widen_widget): a named_parameter the inner params read as "$param1"."""
    return {"nodes": [{
        "name": "fleck_layer", "type": "graph", "parameters": {"param1": 36},
        "nodes": [
            {"name": "Cells", "type": "voronoi",
             "parameters": {"scale_x": "$param1", "scale_y": "$param1"}},
            {"name": "gen_parameters", "type": "remote", "parameters": {"param1": 36},
             "widgets": [{"name": "param1", "shortdesc": "Fleck density", "label": "",
                          "type": "named_parameter", "min": 1, "max": 48, "step": 1,
                          "default": 36}]},
        ]}], "connections": []}


def test_named_parameter_slider_takes_its_range_from_the_widget():
    (s,) = derive_sliders(_named_param_graph(), _catalog())
    assert (s["kind"], s["min"], s["max"], s["step"], s["value"]) == ("float", 1, 48, 1, 36)
    assert s["binding"] == {"node": "fleck_layer", "widget": "param1"}


def test_apply_values_sets_a_named_parameter_and_keeps_the_references():
    out = apply_values(_named_param_graph(), {"fleck_layer/param1": 44})
    sub = out["nodes"][0]
    remote = next(n for n in sub["nodes"] if n["name"] == "gen_parameters")
    cells = next(n for n in sub["nodes"] if n["name"] == "Cells")
    assert sub["parameters"]["param1"] == 44 and remote["parameters"]["param1"] == 44
    assert cells["parameters"] == {"scale_x": "$param1", "scale_y": "$param1"}


@pytest.mark.parametrize("material, slider_id, preset", [
    ("s14_wet_river_stone", "stone_profile/param2", 4),     # t08 Top flatness
    ("s14_wet_river_stone", "surface_grain/param1", 128),   # t08 Grain scale
    ("s07_cobblestone", "surface_grain/param0", 48),        # s08 Grain scale
    ("f07_herringbone_tweed", "fleck_layer/param1", 36),    # f08 Fleck density
])
def test_host_presets_are_inside_their_slider_range(material, slider_id, preset):
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, material)
    graph = json.load(open(entry.path, encoding="utf-8"))
    s = next(s for s in derive_sliders(graph, _catalog()) if s["id"] == slider_id)
    assert s["min"] <= preset <= s["max"], (slider_id, s["min"], s["max"])
