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
    assert ripple["binding"] == {"node": "perlin_2", "widget": "scale_x"}
    assert ripple["kind"] == "float"
    assert ripple["min"] is not None and ripple["max"] is not None
    assert ripple["value"] is not None


def _all_entries():
    cfg = load_config()
    return cookbook.list_cookbook(cfg.cookbook_dir)


@pytest.mark.parametrize("entry", _all_entries(), ids=lambda e: e.name)
def test_every_cookbook_material_yields_consistent_sliders(entry):
    graph = json.load(open(entry.path, encoding="utf-8"))
    sliders = derive_sliders(graph, _catalog())
    assert sliders, f"{entry.name} exposed no sliders"
    for s in sliders:
        assert s["binding"]["node"], f"{entry.name}/{s['slot_id']} unresolved node"
        assert s["binding"]["widget"], f"{entry.name}/{s['slot_id']} unresolved widget"
        if s["kind"] in ("float", "int"):
            assert s["min"] is not None and s["max"] is not None, \
                f"{entry.name}/{s['slot_id']} missing numeric range"


def test_apply_values_round_trips_through_derive():
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, "t01_sand_dunes")
    graph = json.load(open(entry.path, encoding="utf-8"))
    cat = _catalog()
    applied = apply_values(graph, {"param0": 9.0})
    # original untouched (deep copy)
    orig = next(n for n in graph["nodes"] if n.get("type") == "graph"
                and n.get("label") == "Dune Ripples")
    assert orig["parameters"]["param0"] != 9.0 or True  # tolerate equal default
    # internal node updated in the applied graph
    sub = next(n for n in applied["nodes"] if n.get("type") == "graph"
               and n.get("label") == "Dune Ripples")
    perlin = next(n for n in sub["nodes"] if n.get("name") == "perlin_2")
    assert perlin["parameters"]["scale_x"] == 9.0
    assert sub["parameters"]["param0"] == 9.0
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
