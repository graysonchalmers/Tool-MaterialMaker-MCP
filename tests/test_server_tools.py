import json
import os
import pytest
from mm_mcp import server
from mm_mcp.config import load_config

cfg = load_config()


def test_first_albedo_picks_the_albedo_output():
    imgs = ["/out/x_normal.png", "/out/x_albedo.png", "/out/x_orm.png"]
    assert server._first_albedo(imgs) == "/out/x_albedo.png"


def test_first_albedo_returns_none_when_no_albedo_present():
    assert server._first_albedo(["/out/x_normal.png", "/out/x_orm.png"]) is None


def test_list_node_types_includes_blend():
    assert "blend" in server.list_node_types()


def test_describe_node_returns_ports():
    d = server.describe_node("blend")
    assert [i["name"] for i in d["inputs"]] == ["s1", "s2", "a"]


def test_validate_flags_unknown_type():
    ptex = {"type": "graph", "nodes": [{"name": "x", "type": "nope", "parameters": {}}],
            "connections": []}
    errs = [p for p in server.validate(ptex) if p["severity"] == "error"]
    assert errs


def test_list_and_load_example():
    names = server.list_examples()
    assert "bricks" in names
    d = server.load_example("bricks")
    assert d["type"] == "graph"


def test_save_graph_writes_file(tmp_path):
    ptex = {"type": "graph", "nodes": [], "connections": []}
    out = os.path.join(str(tmp_path), "mat.ptex")
    server.save_graph(ptex, out)
    assert os.path.exists(out)
    with open(out, encoding="utf-8") as fh:
        assert json.load(fh)["type"] == "graph"


def test_render_graph_forwards_target_to_render(monkeypatch):
    """render_graph's target param must reach render(), not get dropped —
    this is what actually lets a caller pick Unity/Unreal instead of Godot."""
    captured = {}

    def fake_render(ptex, size=512, outdir=None, basename="material",
                     target="Godot/Godot 4 Standard", cfg=None):
        captured["target"] = target
        from mm_mcp.render import RenderResult
        return RenderResult(ok=True, images=["fake.png"])

    monkeypatch.setattr(server, "render", fake_render)
    ptex = {"type": "graph", "nodes": [], "connections": []}
    server.render_graph(ptex, target="Unity/URP")
    assert captured["target"] == "Unity/URP"


def test_render_graph_defaults_to_godot_target(monkeypatch):
    captured = {}

    def fake_render(ptex, size=512, outdir=None, basename="material",
                     target="Godot/Godot 4 Standard", cfg=None):
        captured["target"] = target
        from mm_mcp.render import RenderResult
        return RenderResult(ok=True, images=["fake.png"])

    monkeypatch.setattr(server, "render", fake_render)
    ptex = {"type": "graph", "nodes": [], "connections": []}
    server.render_graph(ptex)
    assert captured["target"] == "Godot/Godot 4 Standard"


def test_render_preview_missing_map_returns_error_as_data(tmp_path):
    albedo = tmp_path / "albedo.png"
    albedo.write_text("x")
    result = server.render_preview(str(albedo), str(tmp_path / "nope_normal.png"),
                                    str(tmp_path / "nope_orm.png"))
    assert result["ok"] is False
    assert result["image"] is None
    assert "normal" in result["error"]


def _simple_ptex():
    return {"type": "graph", "connections": [
        {"from": "perlin_0", "from_port": 0, "to": "Material", "to_port": 0},
    ], "nodes": [
        {"name": "perlin_0", "type": "perlin", "node_position": {"x": 0, "y": 0}, "parameters": {}},
        {"name": "Material", "type": "material", "node_position": {"x": 300, "y": 0}, "parameters": {}},
    ]}


def test_render_node_output_returns_the_albedo_image(monkeypatch):
    captured = {}

    def fake_render(ptex, size=512, outdir=None, basename="node_output",
                     target="Godot/Godot 4 Standard", cfg=None):
        captured["ptex"] = ptex
        from mm_mcp.render import RenderResult
        return RenderResult(ok=True, images=[
            "out/node_output_albedo.png", "out/node_output_normal.png",
            "out/node_output_heightmap.png", "out/node_output_orm.png",
        ])

    monkeypatch.setattr(server, "render", fake_render)
    result = server.render_node_output(_simple_ptex(), "perlin_0")
    assert result["ok"] is True
    assert result["image"] == "out/node_output_albedo.png"
    assert result["error"] is None
    # the rewired graph, not the original, must be what actually rendered
    conns = captured["ptex"]["connections"]
    assert {"from": "perlin_0", "from_port": 0, "to": "Material", "to_port": 0} in conns


def test_render_node_output_unknown_node_is_a_data_error(monkeypatch):
    called = []
    monkeypatch.setattr(server, "render", lambda *a, **k: called.append(1))
    result = server.render_node_output(_simple_ptex(), "nope")
    assert result["ok"] is False
    assert result["image"] is None
    assert "nope" in result["error"]
    assert not called  # render() must never be reached


def test_render_node_output_render_failure_is_forwarded(monkeypatch):
    def fake_render(ptex, size=512, outdir=None, basename="node_output",
                     target="Godot/Godot 4 Standard", cfg=None):
        from mm_mcp.render import RenderResult
        return RenderResult(ok=False, error="Godot exited 1", log_tail="boom")

    monkeypatch.setattr(server, "render", fake_render)
    result = server.render_node_output(_simple_ptex(), "perlin_0")
    assert result["ok"] is False
    assert result["image"] is None
    assert result["error"] == "Godot exited 1"
    assert result["log_tail"] == "boom"


def test_render_node_output_missing_albedo_output_is_an_error(monkeypatch):
    def fake_render(ptex, size=512, outdir=None, basename="node_output",
                     target="Godot/Godot 4 Standard", cfg=None):
        from mm_mcp.render import RenderResult
        return RenderResult(ok=True, images=["out/node_output_normal.png"])

    monkeypatch.setattr(server, "render", fake_render)
    result = server.render_node_output(_simple_ptex(), "perlin_0")
    assert result["ok"] is False
    assert result["image"] is None
    assert "albedo" in result["error"]


@pytest.mark.integration
def test_render_node_output_bundled_example_produces_a_real_image():
    ptex = server.load_example("bricks")
    result = server.render_node_output(ptex, "colorize_2", size=256,
                                        basename="node_probe")
    assert result["ok"], result["error"] or result.get("log_tail")
    assert result["image"].endswith("_albedo.png")
    assert os.path.getsize(result["image"]) > 0


import os as _os
from mm_mcp import server as _server


def _with_roots(monkeypatch, roots):
    monkeypatch.setenv("MM_ALLOWED_ROOTS", _os.pathsep.join(roots))
    _server._reset()


def test_save_graph_returns_ok_dict(tmp_path):
    ptex = {"type": "graph", "nodes": [], "connections": []}
    out = os.path.join(str(tmp_path), "mat.ptex")
    res = _server.save_graph(ptex, out)
    assert res["ok"] is True
    assert os.path.exists(out)


def test_save_graph_blocks_path_outside_roots(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    _with_roots(monkeypatch, [str(allowed)])
    outside = os.path.join(str(tmp_path), "elsewhere.ptex")
    res = _server.save_graph({"type": "graph", "nodes": [], "connections": []}, outside)
    assert res["ok"] is False
    assert not os.path.exists(outside)
    monkeypatch.delenv("MM_ALLOWED_ROOTS", raising=False)
    _server._reset()


def test_save_graph_allows_path_inside_roots(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    _with_roots(monkeypatch, [str(allowed)])
    inside = os.path.join(str(allowed), "mat.ptex")
    res = _server.save_graph({"type": "graph", "nodes": [], "connections": []}, inside)
    assert res["ok"] is True
    assert os.path.exists(inside)
    monkeypatch.delenv("MM_ALLOWED_ROOTS", raising=False)
    _server._reset()


def test_load_example_rejects_traversal_name():
    res = _server.load_example("../../etc/passwd")
    assert isinstance(res, dict) and res.get("ok") is False


def test_render_graph_rejects_traversal_basename():
    ptex = _server.load_example("bricks")
    res = _server.render_graph(ptex, basename="../../evil")
    assert res["ok"] is False
    assert "error" in res
