import json
import os
import time
import pytest
from mm_mcp.config import load_config
from mm_mcp.render import render, _build_command, _collect_fresh_images, _snapshot_pngs

cfg = load_config()


def test_snapshot_pngs_records_matching_files_and_skips_others(tmp_path):
    """_snapshot_pngs captures {filename: mtime} for existing <basename>_*.png
    files only -- non-matching names and non-png files are excluded, so a
    later _collect_fresh_images call sees the right prior state."""
    (tmp_path / "brick_albedo.png").write_text("a")
    (tmp_path / "brick_normal.png").write_text("n")
    (tmp_path / "other_albedo.png").write_text("x")  # wrong basename
    (tmp_path / "brick_notes.txt").write_text("t")   # not a png

    snap = _snapshot_pngs(str(tmp_path), "brick")
    assert set(snap.keys()) == {"brick_albedo.png", "brick_normal.png"}
    assert all(isinstance(v, float) for v in snap.values())


def test_collect_fresh_images_ignores_stale_files(tmp_path):
    """Stale files with unchanged mtime are not collected."""
    # Create a file and record its mtime
    stale_file = tmp_path / "brick_albedo.png"
    stale_file.write_text("old content")
    mtime_before = os.path.getmtime(stale_file)

    # Snapshot dict has the file with its old mtime
    before = {"brick_albedo.png": mtime_before}

    # Collect with the snapshot - should not include the stale file
    fresh = _collect_fresh_images(str(tmp_path), "brick", before)
    assert fresh == []


def test_collect_fresh_images_includes_new_files(tmp_path):
    """New files absent from snapshot are collected."""
    # Create a new file that was not in the snapshot
    new_file = tmp_path / "brick_normal.png"
    new_file.write_text("new content")

    before = {}  # Empty snapshot - no prior files

    fresh = _collect_fresh_images(str(tmp_path), "brick", before)
    assert len(fresh) == 1
    assert str(new_file) in fresh


def test_collect_fresh_images_includes_modified_files(tmp_path):
    """Existing files with advanced mtime are collected."""
    # Create a file and snapshot it
    file_path = tmp_path / "brick_heightmap.png"
    file_path.write_text("initial content")
    mtime_before = os.path.getmtime(file_path)

    before = {"brick_heightmap.png": mtime_before}

    # Sleep to ensure time advances
    time.sleep(0.01)

    # Modify the file (advances mtime)
    file_path.write_text("modified content")
    mtime_after = os.path.getmtime(file_path)
    assert mtime_after > mtime_before

    fresh = _collect_fresh_images(str(tmp_path), "brick", before)
    assert len(fresh) == 1
    assert str(file_path) in fresh


def test_collect_fresh_images_prefix_collision_guard(tmp_path):
    """basename='brick' does NOT collect 'bricks_albedo.png'."""
    # Create a file matching a different basename's pattern
    file_path = tmp_path / "bricks_albedo.png"
    file_path.write_text("content")

    before = {}

    # Collect with basename="brick" - should NOT match "bricks_albedo.png"
    fresh = _collect_fresh_images(str(tmp_path), "brick", before)
    assert fresh == []


def test_collect_fresh_images_excludes_zero_byte_files(tmp_path):
    """Zero-byte files are excluded from results."""
    # Create an empty file
    empty_file = tmp_path / "brick_orm.png"
    empty_file.write_text("")

    before = {}

    fresh = _collect_fresh_images(str(tmp_path), "brick", before)
    assert fresh == []


def test_collect_fresh_images_ignores_non_png_files(tmp_path):
    """Non-PNG files are not collected even if they match the basename."""
    # Create a non-PNG file matching the basename pattern
    non_png = tmp_path / "brick_albedo.txt"
    non_png.write_text("content")

    before = {}

    fresh = _collect_fresh_images(str(tmp_path), "brick", before)
    assert fresh == []


class _FakeProc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_godot_retries_a_transient_crash_then_returns_success(monkeypatch):
    from mm_mcp import render as render_mod
    codes = [3221225477, 0]  # a transient access-violation crash, then success
    calls = {"n": 0}

    def _fake_run(cmd, **kw):
        rc = codes[calls["n"]]
        calls["n"] += 1
        return _FakeProc(rc)

    monkeypatch.setattr(render_mod.subprocess, "run", _fake_run)
    proc = render_mod._run_godot(["godot"], 10)
    assert proc.returncode == 0
    assert calls["n"] == 2  # retried exactly once past the transient crash


def test_run_godot_does_not_retry_a_non_transient_returncode(monkeypatch):
    from mm_mcp import render as render_mod
    calls = {"n": 0}

    def _fake_run(cmd, **kw):
        calls["n"] += 1
        return _FakeProc(1)  # an ordinary, non-transient failure

    monkeypatch.setattr(render_mod.subprocess, "run", _fake_run)
    proc = render_mod._run_godot(["godot"], 10)
    assert proc.returncode == 1
    assert calls["n"] == 1  # a normal exit code is not retried


def test_run_godot_raises_godot_timeout_on_timeout(monkeypatch):
    import subprocess
    from mm_mcp import render as render_mod

    def _fake_run(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))

    monkeypatch.setattr(render_mod.subprocess, "run", _fake_run)
    with pytest.raises(render_mod._GodotTimeout):
        render_mod._run_godot(["godot"], 10)


def test_log_tail_returns_the_last_lines_of_combined_output():
    from mm_mcp import render as render_mod
    proc = _FakeProc(0, stdout="a\nb\nc\n", stderr="d\ne")
    assert render_mod._log_tail(proc, lines=3) == "c\nd\ne"


def test_build_command_uses_long_target_flag():
    """Godot's CLI parser only recognizes --target, not -t (silently a
    no-op for -t, confirmed empirically against a real Godot binary)."""
    cmd = _build_command(cfg, "C:/out/bricks.ptex", "Unity/URP", "C:/out", 512)
    assert "--target" in cmd
    idx = cmd.index("--target")
    assert cmd[idx + 1] == "Unity/URP"
    assert "-t" not in cmd


def test_build_command_defaults_preserved():
    """Positional shape (path/export-material/output/size flags) is
    unchanged by the --target fix."""
    cmd = _build_command(cfg, "C:/out/bricks.ptex", "Godot/Godot 4 Standard", "C:/out", 256)
    assert cmd == [
        cfg.console_binary, "--path", cfg.project_path,
        "--export-material", "C:/out/bricks.ptex",
        "--target", "Godot/Godot 4 Standard",
        "-o", "C:/out", "--size", "256",
    ]


@pytest.mark.integration
def test_render_bundled_example_produces_pngs(tmp_path):
    src = os.path.join(cfg.examples_dir, "bricks.ptex")
    with open(src, encoding="utf-8") as fh:
        ptex = json.load(fh)
    result = render(ptex, size=256, outdir=str(tmp_path), basename="bricks")
    assert result.ok, result.error or result.log_tail
    assert len(result.images) >= 1
    for img in result.images:
        assert os.path.getsize(img) > 0
