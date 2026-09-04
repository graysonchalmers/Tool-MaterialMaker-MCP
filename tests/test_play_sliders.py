import json

import pytest

import mm_mcp.cookbook as cookbook
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.play.sliders import derive_sliders


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
