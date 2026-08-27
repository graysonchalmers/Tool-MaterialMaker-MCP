import json
import os
import pytest
from mm_mcp.config import load_config
from mm_mcp.render import render
from mm_mcp.preview import render_preview, _build_command

cfg = load_config()


def test_build_command_includes_tile_flag():
    cmd = _build_command(cfg, "/a/albedo.png", "/a/normal.png", "/a/orm.png",
                          "/out/x_preview.png", tile=2.5)
    assert "--tile=2.5" in cmd


def test_build_command_defaults_tile_to_one():
    cmd = _build_command(cfg, "/a/albedo.png", "/a/normal.png", "/a/orm.png",
                          "/out/x_preview.png", tile=1.0)
    assert "--tile=1.0" in cmd


def test_render_preview_missing_albedo_returns_error(tmp_path):
    normal = tmp_path / "normal.png"
    orm = tmp_path / "orm.png"
    normal.write_text("x")
    orm.write_text("x")
    result = render_preview(str(tmp_path / "nope_albedo.png"), str(normal), str(orm))
    assert not result.ok
    assert "albedo" in result.error
    assert "nope_albedo.png" in result.error


def test_render_preview_missing_normal_returns_error(tmp_path):
    albedo = tmp_path / "albedo.png"
    orm = tmp_path / "orm.png"
    albedo.write_text("x")
    orm.write_text("x")
    result = render_preview(str(albedo), str(tmp_path / "nope_normal.png"), str(orm))
    assert not result.ok
    assert "normal" in result.error
    assert "nope_normal.png" in result.error


def test_render_preview_missing_orm_returns_error(tmp_path):
    albedo = tmp_path / "albedo.png"
    normal = tmp_path / "normal.png"
    albedo.write_text("x")
    normal.write_text("x")
    result = render_preview(str(albedo), str(normal), str(tmp_path / "nope_orm.png"))
    assert not result.ok
    assert "orm" in result.error
    assert "nope_orm.png" in result.error


@pytest.mark.integration
def test_render_preview_produces_nonempty_png(tmp_path):
    src = os.path.join(cfg.examples_dir, "bricks.ptex")
    with open(src, encoding="utf-8") as fh:
        ptex = json.load(fh)
    render_result = render(ptex, size=256, outdir=str(tmp_path), basename="bricks")
    assert render_result.ok, render_result.error or render_result.log_tail

    maps = {}
    for img in render_result.images:
        for key in ("albedo", "normal", "orm"):
            if img.endswith(f"_{key}.png"):
                maps[key] = img

    result = render_preview(maps["albedo"], maps["normal"], maps["orm"],
                             outdir=str(tmp_path), basename="bricks")
    assert result.ok, result.error or result.log_tail
    assert os.path.getsize(result.image) > 0


@pytest.mark.integration
def test_render_preview_accepts_paths_relative_to_caller_cwd(tmp_path):
    """Godot's own path resolution for --path <preview_project> is not the
    same as the calling process's OS cwd, so a caller-relative path (the
    normal case: an assistant passes back whatever render_graph returned)
    must be made absolute before it's handed to the subprocess, or textures
    silently fail to load while the tool still reports ok=True."""
    src = os.path.join(cfg.examples_dir, "bricks.ptex")
    with open(src, encoding="utf-8") as fh:
        ptex = json.load(fh)
    render_result = render(ptex, size=256, outdir=str(tmp_path), basename="bricks")
    assert render_result.ok, render_result.error or render_result.log_tail

    maps = {}
    for img in render_result.images:
        for key in ("albedo", "normal", "orm"):
            if img.endswith(f"_{key}.png"):
                maps[key] = img

    cwd = os.getcwd()
    rel = {k: os.path.relpath(v, cwd) for k, v in maps.items()}

    result = render_preview(rel["albedo"], rel["normal"], rel["orm"],
                             outdir=str(tmp_path), basename="relcheck")
    assert result.ok, result.error or result.log_tail
    assert "ERROR" not in result.log_tail, result.log_tail
    assert os.path.getsize(result.image) > 0
