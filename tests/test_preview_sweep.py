import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

from PIL import Image
import pytest

from mm_mcp import preview
from mm_mcp import render as render_mod
from mm_mcp.config import Config


def _write_frame(directory, index, *, size=(8, 8), image_format="PNG"):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"frame_{index:03d}.png"
    with Image.new("RGB", size, color=(index * 60, 20, 40)) as image:
        image.save(path, format=image_format)
    return path


def _write_frames(directory, indices=(0, 1, 2)):
    for index in indices:
        _write_frame(directory, index)


@pytest.fixture
def sweep(tmp_path):
    inputs = tmp_path / "inputs"
    maps = tuple(str(_write_frame(inputs, index)) for index in range(3))
    outdir = tmp_path / "published"
    outdir.mkdir()
    gif_path = outdir / "material_sweep.gif"
    with Image.new("RGB", (8, 8), color="purple") as image:
        image.save(gif_path, format="GIF")
    cfg = Config(
        godot_binary="godot", console_binary="godot-console", project_path="",
        output_dir=str(outdir), nodes_dir="", examples_dir="",
        live_overlay_dir="", allowed_roots=[],
    )
    return SimpleNamespace(maps=maps, outdir=outdir, gif_path=gif_path,
                           old_gif=gif_path.read_bytes(), cfg=cfg)


def _render(sweep, **options):
    kwargs = dict(outdir=str(sweep.outdir), basename="material", frames=3, cfg=sweep.cfg)
    kwargs.update(options)
    return preview.render_preview_sweep(*sweep.maps, **kwargs)


def _mock_render(monkeypatch, produce=_write_frames, returncode=0):
    calls = []

    def run(cmd, timeout, *, before_attempt=None):
        if before_attempt is not None:
            before_attempt()
        directory = Path(next(arg.split("=", 1)[1] for arg in cmd
                              if arg.startswith("--sweep-outdir=")))
        calls.append(SimpleNamespace(cmd=cmd, timeout=timeout, directory=directory))
        produce(directory)
        return subprocess.CompletedProcess(cmd, returncode, "render log\n", "diagnostic\n")

    monkeypatch.setattr(preview, "_run_godot", run)
    return calls


def _assert_failure_preserves_output(sweep, result):
    assert not result.ok
    assert result.image is None
    assert result.frame_count == 0
    assert result.error
    assert sweep.gif_path.read_bytes() == sweep.old_gif
    assert set(sweep.outdir.iterdir()) == {sweep.gif_path}


def test_nonzero_exit_with_partial_frames_preserves_previous_gif(monkeypatch, sweep):
    _mock_render(monkeypatch, lambda directory: _write_frames(directory, (0,)), returncode=7)

    result = _render(sweep)

    _assert_failure_preserves_output(sweep, result)
    assert "Godot exited 7" in result.error
    assert result.log_tail == "render log\ndiagnostic"


@pytest.mark.parametrize("names", [
    [],
    ["frame_000.png"],
    ["frame_000.png", "frame_002.png"],
    ["frame_00.png", "frame_001.png", "frame_002.png"],
    ["frame_000.png", "frame_001.png", "frame_002.PNG"],
    ["frame_000.png", "frame_001.png", "frame_002.png", "extra.png"],
])
def test_zero_exit_requires_exact_requested_frame_sequence(monkeypatch, sweep, names):
    def produce(directory):
        directory.mkdir(parents=True, exist_ok=True)
        for index, name in enumerate(names):
            _write_frame(directory, index).rename(directory / name)

    _mock_render(monkeypatch, produce)

    _assert_failure_preserves_output(sweep, _render(sweep))


def test_timeout_cleans_staging_and_preserves_previous_gif(monkeypatch, sweep):
    def timeout(directory):
        _write_frame(directory, 0)
        raise render_mod._GodotTimeout

    _mock_render(monkeypatch, timeout)

    result = _render(sweep)

    _assert_failure_preserves_output(sweep, result)
    assert "timed out after 90s" in result.error


@pytest.mark.parametrize("damage", ["unreadable", "truncated", "bad-crc", "jpeg", "size"])
def test_invalid_frame_prevents_publication(monkeypatch, sweep, damage):
    def produce(directory):
        _write_frames(directory)
        path = directory / "frame_002.png"
        if damage == "unreadable":
            path.write_bytes(b"not an image")
        elif damage == "truncated":
            path.write_bytes(path.read_bytes()[:50])
        elif damage == "bad-crc":
            data = bytearray(path.read_bytes())
            offset = data.index(b"IDAT")
            length = int.from_bytes(data[offset - 4:offset], "big")
            data[offset + 4 + length] ^= 1
            path.write_bytes(data)
        elif damage == "jpeg":
            _write_frame(directory, 2, image_format="JPEG")
        else:
            _write_frame(directory, 2, size=(9, 8))

    _mock_render(monkeypatch, produce)

    result = _render(sweep)

    _assert_failure_preserves_output(sweep, result)
    assert result.log_tail == "render log\ndiagnostic"


def test_encoder_failure_preserves_previous_gif(monkeypatch, sweep):
    _mock_render(monkeypatch)

    def fail_encode(frame_paths, gif_path, frame_duration_ms):
        Path(gif_path).write_bytes(b"partial GIF")
        raise OSError("encoder failed")

    monkeypatch.setattr(preview, "_frames_to_gif", fail_encode)

    result = _render(sweep)

    _assert_failure_preserves_output(sweep, result)
    assert "encoder failed" in result.error


@pytest.mark.parametrize("duration", [655_360, 10 ** 400], ids=["gif-overflow", "float-overflow"])
def test_unencodable_duration_returns_failure(monkeypatch, sweep, duration):
    _mock_render(monkeypatch)

    _assert_failure_preserves_output(sweep, _render(sweep, frame_duration_ms=duration))


def test_publish_failure_preserves_previous_gif(monkeypatch, sweep):
    _mock_render(monkeypatch)

    def fail_replace(source, destination):
        raise OSError("destination is locked")

    monkeypatch.setattr(preview.os, "replace", fail_replace)

    result = _render(sweep)

    _assert_failure_preserves_output(sweep, result)
    assert "destination is locked" in result.error


def test_output_directory_error_returns_failure(monkeypatch, sweep):
    blocked = sweep.outdir.parent / "not-a-directory"
    blocked.write_text("occupied")
    _mock_render(monkeypatch, lambda directory: pytest.fail("Godot must not run"))

    result = _render(sweep, outdir=str(blocked / "output"))

    _assert_failure_preserves_output(sweep, result)


def test_success_atomically_replaces_gif_and_cleans_staging(monkeypatch, sweep):
    def produce(directory):
        assert sweep.gif_path.read_bytes() == sweep.old_gif
        _write_frames(directory)

    calls = _mock_render(monkeypatch, produce)
    published = []
    real_replace = os.replace

    def replace(source, destination):
        source = Path(source)
        assert source.is_relative_to(sweep.outdir)
        assert source.parent != sweep.outdir
        assert Path(destination) == sweep.gif_path
        assert sweep.gif_path.read_bytes() == sweep.old_gif
        with Image.open(source) as gif:
            assert gif.n_frames == 3
            for index in range(3):
                gif.seek(index)
                gif.load()
        published.append(source)
        real_replace(source, destination)

    monkeypatch.setattr(preview.os, "replace", replace)

    result = _render(sweep)

    assert result.ok, result.error
    assert result.image == str(sweep.gif_path)
    assert result.frame_count == 3
    assert result.log_tail == "render log\ndiagnostic"
    assert len(published) == 1
    assert not published[0].exists()
    assert not calls[0].directory.exists()
    assert set(sweep.outdir.iterdir()) == {sweep.gif_path}
    with Image.open(result.image) as gif:
        assert gif.n_frames == 3
        assert gif.info["loop"] == 0
        for index in range(3):
            gif.seek(index)
            assert gif.info["duration"] == 80
            with gif.convert("RGB") as frame:
                assert frame.getpixel((0, 0)) == (index * 60, 20, 40)


def test_separate_sweeps_use_distinct_private_directories(monkeypatch, sweep):
    calls = _mock_render(monkeypatch)

    assert _render(sweep).ok
    assert _render(sweep).ok

    directories = [call.directory for call in calls]
    assert directories[0] != directories[1]
    assert all(directory.is_relative_to(sweep.outdir) for directory in directories)
    assert all(not directory.exists() for directory in directories)


def test_legacy_frame_directory_is_untouched(monkeypatch, sweep):
    legacy = sweep.outdir / "material_sweep_frames"
    legacy.mkdir()
    marker = legacy / "keep.txt"
    marker.write_text("another run owns these files")
    _mock_render(monkeypatch)

    assert _render(sweep).ok

    assert marker.read_text() == "another run owns these files"
    assert set(sweep.outdir.iterdir()) == {sweep.gif_path, legacy}


def test_failed_first_sweep_does_not_publish_partial_gif(monkeypatch, sweep):
    sweep.gif_path.unlink()
    _mock_render(monkeypatch, lambda directory: _write_frames(directory, (0,)), returncode=1)

    result = _render(sweep)

    assert not result.ok
    assert not sweep.gif_path.exists()
    assert list(sweep.outdir.iterdir()) == []


@pytest.mark.parametrize("last_frames", [(0,), (0, 1, 2)])
def test_transient_crash_retry_cannot_reuse_previous_frames(monkeypatch, sweep, last_frames):
    starts = []

    class Popen:
        def __init__(self, cmd, **kwargs):
            directory = Path(next(arg.split("=", 1)[1] for arg in cmd
                                  if arg.startswith("--sweep-outdir=")))
            directory.mkdir(parents=True, exist_ok=True)
            starts.append(set(directory.iterdir()))
            self.returncode = 3221225477 if len(starts) == 1 else 0
            _write_frames(directory, (0, 1, 2) if len(starts) == 1 else last_frames)

        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(render_mod.subprocess, "Popen", Popen)

    result = _render(sweep)

    assert starts == [set(), set()]
    if len(last_frames) == 3:
        assert result.ok, result.error
        assert result.frame_count == 3
        assert set(sweep.outdir.iterdir()) == {sweep.gif_path}
    else:
        _assert_failure_preserves_output(sweep, result)


@pytest.mark.parametrize("basename", ["", ".", "..", "../escaped", "nested/name",
                                     r"..\escaped", "C:escaped", "\0", None])
def test_invalid_basename_is_rejected_before_render(monkeypatch, sweep, basename):
    _mock_render(monkeypatch, lambda directory: pytest.fail("Godot must not run"))

    result = _render(sweep, basename=basename)

    _assert_failure_preserves_output(sweep, result)
    assert "basename" in result.error


def test_absolute_basename_cannot_escape_output(monkeypatch, sweep):
    _mock_render(monkeypatch, lambda directory: pytest.fail("Godot must not run"))

    result = _render(sweep, basename=str(sweep.outdir.parent / "escaped"))

    _assert_failure_preserves_output(sweep, result)
    assert not (sweep.outdir.parent / "escaped_sweep.gif").exists()


@pytest.mark.parametrize("option", ["frames", "frame_duration_ms"])
@pytest.mark.parametrize("value", [0, -1, 1.5, "3", True, None])
def test_invalid_frame_options_are_rejected_before_render(monkeypatch, sweep, option, value):
    _mock_render(monkeypatch, lambda directory: pytest.fail("Godot must not run"))

    result = _render(sweep, **{option: value})

    _assert_failure_preserves_output(sweep, result)
    assert option in result.error


def test_caller_relative_paths_and_sweep_options_are_preserved(monkeypatch, sweep):
    monkeypatch.chdir(sweep.outdir.parent)
    calls = _mock_render(monkeypatch)
    relative_maps = [os.path.relpath(path) for path in sweep.maps]

    result = preview.render_preview_sweep(
        *relative_maps, outdir="published", basename="material", tile=1.25,
        frames=3, frame_duration_ms=120, sweep_kind="azimuth", cone=30.0, cfg=sweep.cfg,
    )

    assert result.ok, result.error
    assert result.image == str(sweep.gif_path)
    for label, path in zip(("albedo", "normal", "orm"), sweep.maps):
        assert f"--{label}={path}" in calls[0].cmd
    assert "--sweep-frames=3" in calls[0].cmd
    assert "--tile=1.25" in calls[0].cmd
    assert "--sweep-kind=azimuth" in calls[0].cmd
    assert "--cone=30.0" in calls[0].cmd
    assert calls[0].timeout == 90
    with Image.open(result.image) as gif:
        assert gif.info["duration"] == 120
