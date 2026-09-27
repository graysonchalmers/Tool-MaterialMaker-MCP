import io
import json
import os
import zipfile
from pathlib import Path

import pytest
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
        perlin = next(n for n in sub["nodes"] if n.get("name") == "DuneRipples")
        assert perlin["parameters"]["scale_x"] == 12.0
        assert {"node": "DuneRipples", "widget": "scale_x", "value": 12.0} in changes
        assert changes == [{"node": "DuneRipples", "widget": "scale_x", "value": 12.0}]
        # the sibling subgraph's own "param0" (a different id) must be untouched
        sand_finish = next(n for n in applied_graph["nodes"]
                            if n.get("type") == "graph" and n.get("label") == "Sand Finish")
        colorize = next(n for n in sand_finish["nodes"] if n.get("name") == "DuneColor")
        assert colorize["parameters"].get("gradient") != 12.0
        p = os.path.join(outdir, "play_albedo.png")
        Path(p).write_bytes(b"rendered-map")
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


def test_export_zips_maps_and_ptex(tmp_path):
    cfg = _cfg()
    rendered = []

    def fake_render(graph, changes, size, cfg, outdir, **kw):
        rendered.append(graph)
        path = Path(outdir) / "play_albedo.png"
        path.write_bytes(str(len(rendered)).encode())
        return {"ok": True, "path": "headless", "images": [str(path)]}

    # A previous material's outputs must never enter this download.
    (tmp_path / "unrelated_normal.png").write_bytes(b"old-map")
    first = api.render_request(cfg, {}, {
        "material_id": "t01_sand_dunes", "values": {"dune_ripples/param0": 12.0},
        "size": 256,
    }, str(tmp_path), render_fn=fake_render)
    assert first.get("preview_id"), first
    second = api.render_request(cfg, {}, {
        "material_id": "t01_sand_dunes", "values": {"dune_ripples/param0": 24.0},
        "size": 1024,
    }, str(tmp_path), render_fn=fake_render)
    assert second["preview_id"] != first["preview_id"]

    # Export uses the saved result even after a later render or cookbook edit.
    cfg.cookbook_dir = str(tmp_path / "no-longer-available")
    data, fname = api.export(cfg, {}, {"preview_id": first["preview_id"]}, str(tmp_path))
    assert fname == "t01_sand_dunes.zip"
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert set(z.namelist()) == {"play_albedo.png", "t01_sand_dunes.ptex"}
        assert z.read("play_albedo.png") == b"1"
        assert json.loads(z.read("t01_sand_dunes.ptex")) == rendered[0]


@pytest.mark.parametrize("preview_id", [None, "missing", "../outside", "a" * 32])
def test_export_requires_a_completed_preview(tmp_path, preview_id):
    data, error = api.export(_cfg(), {}, {
        "material_id": "t01_sand_dunes", "preview_id": preview_id,
    }, str(tmp_path))
    assert data is None
    assert "preview" in error


@pytest.mark.parametrize("failure", ["failed", "missing", "outside", "exception"])
def test_incomplete_render_does_not_publish_a_preview(tmp_path, failure):
    def fake_render(graph, changes, size, cfg, outdir, **kw):
        path = Path(outdir) / "play_albedo.png"
        if failure == "outside":
            path = tmp_path / "elsewhere.png"
        if failure != "missing":
            path.write_bytes(b"partial")
        if failure == "exception":
            raise OSError("renderer unavailable")
        return {"ok": failure != "failed", "images": [str(path)], "error": "failed"}

    result = api.render_request(_cfg(), {}, {"material_id": "t01_sand_dunes"},
                                str(tmp_path), render_fn=fake_render)
    assert result["ok"] is False
    assert not result.get("preview_id")
    assert not list(tmp_path.rglob("receipt.json"))
    assert not list(tmp_path.rglob("play_albedo.png"))


def test_export_unknown_material_is_error_data(tmp_path):
    cfg = _cfg()
    data, fname = api.export(cfg, _catalog(cfg),
                             {"material_id": "nope", "values": {}}, str(tmp_path))
    assert data is None and fname
