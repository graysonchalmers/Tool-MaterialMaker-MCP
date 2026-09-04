import json
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
