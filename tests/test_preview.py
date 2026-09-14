import json
import os
import pytest
from PIL import Image
from mm_mcp.config import load_config
from mm_mcp.render import render
from mm_mcp.preview import (
    render_preview, _build_command,
    render_preview_sweep, _build_sweep_command, _frames_to_gif,
)

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


def test_build_sweep_command_includes_sweep_flags():
    cmd = _build_sweep_command(cfg, "/a/albedo.png", "/a/normal.png", "/a/orm.png",
                                "/out/x_sweep_frames", frames=24, tile=1.0)
    assert "--sweep-outdir=/out/x_sweep_frames" in cmd
    assert "--sweep-frames=24" in cmd
    assert "--albedo=/a/albedo.png" in cmd
    assert not any(c.startswith("--out=") for c in cmd)


def test_build_sweep_command_defaults_to_precession():
    cmd = _build_sweep_command(cfg, "/a/albedo.png", "/a/normal.png", "/a/orm.png",
                                "/out/x_sweep_frames", frames=24, tile=1.0)
    assert "--sweep-kind=precess" in cmd
    assert "--cone=18.0" in cmd


def test_build_sweep_command_passes_azimuth_and_cone_through():
    cmd = _build_sweep_command(cfg, "/a/albedo.png", "/a/normal.png", "/a/orm.png",
                                "/out/x_sweep_frames", frames=24, tile=1.0,
                                sweep_kind="azimuth", cone=30.0)
    assert "--sweep-kind=azimuth" in cmd
    assert "--cone=30.0" in cmd


def test_render_preview_sweep_missing_albedo_returns_error(tmp_path):
    normal = tmp_path / "normal.png"
    orm = tmp_path / "orm.png"
    normal.write_text("x")
    orm.write_text("x")
    result = render_preview_sweep(str(tmp_path / "nope_albedo.png"), str(normal), str(orm))
    assert not result.ok
    assert "albedo" in result.error
    assert "nope_albedo.png" in result.error


def test_render_preview_sweep_missing_normal_returns_error(tmp_path):
    albedo = tmp_path / "albedo.png"
    orm = tmp_path / "orm.png"
    albedo.write_text("x")
    orm.write_text("x")
    result = render_preview_sweep(str(albedo), str(tmp_path / "nope_normal.png"), str(orm))
    assert not result.ok
    assert "normal" in result.error
    assert "nope_normal.png" in result.error


def test_render_preview_sweep_missing_orm_returns_error(tmp_path):
    albedo = tmp_path / "albedo.png"
    normal = tmp_path / "normal.png"
    albedo.write_text("x")
    normal.write_text("x")
    result = render_preview_sweep(str(albedo), str(normal), str(tmp_path / "nope_orm.png"))
    assert not result.ok
    assert "orm" in result.error
    assert "nope_orm.png" in result.error


def test_frames_to_gif_assembles_looping_animated_gif(tmp_path):
    frame_paths = []
    for i in range(4):
        p = tmp_path / f"frame_{i:03d}.png"
        Image.new("RGB", (8, 8), color=(i * 10, 0, 0)).save(p)
        frame_paths.append(str(p))
    gif_path = str(tmp_path / "out.gif")

    _frames_to_gif(frame_paths, gif_path, frame_duration_ms=80)

    assert os.path.isfile(gif_path)
    with Image.open(gif_path) as gif:
        assert gif.n_frames == 4
        assert gif.info.get("loop") == 0
        gif.seek(0)
        assert gif.info.get("duration") == 80


def _gif_frame(gif_path: str, index: int) -> Image.Image:
    with Image.open(gif_path) as gif:
        gif.seek(index)
        return gif.convert("RGB").copy()


def _mean_abs_diff(a: Image.Image, b: Image.Image) -> float:
    from PIL import ImageChops, ImageStat
    diff = ImageChops.difference(a, b)
    channel_means = ImageStat.Stat(diff).mean
    return sum(channel_means) / len(channel_means)


@pytest.mark.integration
def test_render_preview_sweep_light_actually_moves_between_frames(tmp_path):
    """Guards against a sweep that renders N visually-identical frames (e.g.
    from too few settle-frame waits after rotating the light) -- frame count
    and GIF validity alone don't prove the light moved, which is the entire
    point of the feature."""
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

    result = render_preview_sweep(maps["albedo"], maps["normal"], maps["orm"],
                                   outdir=str(tmp_path), basename="bricks_move", frames=8)
    assert result.ok, result.error or result.log_tail

    first = _gif_frame(result.image, 0)
    quarter_turn = _gif_frame(result.image, 2)
    opposite = _gif_frame(result.image, 4)
    assert _mean_abs_diff(first, quarter_turn) > 3.0
    assert _mean_abs_diff(first, opposite) > 3.0


@pytest.mark.integration
def test_render_preview_sweep_produces_gif_with_requested_frame_count(tmp_path):
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

    result = render_preview_sweep(maps["albedo"], maps["normal"], maps["orm"],
                                   outdir=str(tmp_path), basename="bricks", frames=4)
    assert result.ok, result.error or result.log_tail
    assert result.frame_count == 4
    assert os.path.getsize(result.image) > 0
    with Image.open(result.image) as gif:
        assert gif.n_frames == 4
    assert not os.path.isdir(os.path.join(str(tmp_path), "bricks_sweep_frames"))


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
