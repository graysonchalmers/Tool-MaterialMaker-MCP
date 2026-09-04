import os
from mm_mcp.play import api
from mm_mcp.config import load_config
from mm_mcp.catalog_builder import build_catalog


def _cfg():
    return load_config()


def _catalog(cfg):
    return build_catalog(cfg.nodes_dir)


def test_list_materials_returns_all_cookbook_entries():
    out = api.list_materials(_cfg())
    assert out["ok"]
    names = [m["name"] for m in out["materials"]]
    assert "t01_sand_dunes" in names
    assert all("category" in m for m in out["materials"])


def test_get_material_returns_sliders():
    cfg = _cfg()
    out = api.get_material(cfg, _catalog(cfg), "t01_sand_dunes")
    assert out["ok"]
    assert any(s["label"] == "Ripple scale" for s in out["sliders"])


def test_get_material_unknown_is_error_data():
    cfg = _cfg()
    out = api.get_material(cfg, _catalog(cfg), "does_not_exist")
    assert out["ok"] is False and "error" in out


def test_render_request_applies_values_and_calls_renderer(tmp_path):
    cfg = _cfg()

    def fake_render(applied_graph, changes, size, cfg, outdir, **kw):
        # assert the value was applied into the graph before rendering
        sub = next(n for n in applied_graph["nodes"]
                   if n.get("type") == "graph" and n.get("label") == "Dune Ripples")
        perlin = next(n for n in sub["nodes"] if n.get("name") == "perlin_2")
        assert perlin["parameters"]["scale_x"] == 12.0
        assert {"node": "perlin_2", "widget": "scale_x", "value": 12.0} in changes
        assert changes == [{"node": "perlin_2", "widget": "scale_x", "value": 12.0}]
        # the sibling subgraph's own "param0" (a different id) must be untouched
        sand_finish = next(n for n in applied_graph["nodes"]
                            if n.get("type") == "graph" and n.get("label") == "Sand Finish")
        colorize = next(n for n in sand_finish["nodes"] if n.get("name") == "colorize_2")
        assert colorize["parameters"].get("gradient") != 12.0
        p = os.path.join(outdir, "play_albedo.png")
        open(p, "wb").close()
        return {"ok": True, "path": "headless", "images": [p], "error": None}

    body = {"material_id": "t01_sand_dunes", "values": {"dune_ripples/param0": 12.0},
            "size": 256}
    out = api.render_request(cfg, _catalog(cfg), body, str(tmp_path),
                             render_fn=fake_render)
    assert out["ok"] and out["path"] == "headless"
    assert out["maps"] == ["play_albedo.png"]


def test_render_request_unknown_material_is_error_data(tmp_path):
    cfg = _cfg()
    body = {"material_id": "nope", "values": {}, "size": 256}
    out = api.render_request(cfg, _catalog(cfg), body, str(tmp_path))
    assert out["ok"] is False and "error" in out
