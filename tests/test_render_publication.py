"""Publication failures tested with real tiny PNGs and a fake Godot process."""
from io import BytesIO
import json
from pathlib import Path
import subprocess

from PIL import Image
import pytest

from mm_mcp import preview, render


def _png(color="red", size=8, mode="RGB"):
    data = BytesIO()
    Image.new(mode, (size, size), color).save(data, format="PNG")
    return data.getvalue()


def _godot(monkeypatch, outcomes):
    """Only replace the process boundary; exercise the actual retry runner."""
    outcomes = iter(outcomes)
    calls = []

    class Process:
        def __init__(self, cmd, stdout, stderr):
            outcome = next(outcomes)
            calls.append(cmd)
            preview_arg = next((arg for arg in cmd if arg.startswith("--out=")), None)
            image = (Path(preview_arg.split("=", 1)[1]) if preview_arg else
                     Path(cmd[cmd.index("-o") + 1]) / "sample_albedo.png")
            image.parent.mkdir(parents=True, exist_ok=True)
            if outcome != "missing":
                content = b"corrupt PNG" if outcome == "corrupt" else _png(
                    size=4 if outcome == "wrong_size" else 8)
                if outcome == "truncated":
                    content = content[:len(content) // 2]
                image.write_bytes(content)
            if not preview_arg:
                (image.parent / "sample.tres").write_text("new engine material")
                if outcome == "empty_channel":
                    (image.parent / "sample_normal.png").touch()
                if outcome == "success":
                    # Some export profiles create metadata or helper scripts.
                    metadata = image.parent / "metadata"
                    metadata.mkdir()
                    (metadata / "material.py").write_text("engine helper")
                    (image.parent / "sample_heightmap.png").write_bytes(_png(5, mode="I;16"))
            self.returncode = {"nonzero": 1, "crash": 3221225477}.get(outcome, 0)
            self.timeout = outcome == "timeout"
            stderr.write(b"renderer diagnostic\n")

        def wait(self, timeout):
            if self.timeout:
                self.timeout = False
                raise subprocess.TimeoutExpired("godot", timeout)
            return self.returncode

        def kill(self):
            pass

    monkeypatch.setattr(render.subprocess, "Popen", Process)
    return calls


@pytest.mark.parametrize("outcome", [
    "nonzero", "missing", "corrupt", "truncated", "wrong_size", "empty_channel", "timeout",
])
def test_failed_batch_preserves_previous_export(tmp_path, monkeypatch, outcome):
    previous = {"sample_albedo.png": _png("blue"),
                "sample.ptex": b'{"previous": true}', "sample.tres": b"old material"}
    for name, content in previous.items():
        (tmp_path / name).write_bytes(content)
    _godot(monkeypatch, [outcome])

    result = render.render({"nodes": []}, size=8, outdir=str(tmp_path), basename="sample")

    assert not result.ok, result
    assert result.images == []
    assert result.error
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == previous
    if outcome == "nonzero":
        assert "exited 1" in result.error
        assert "renderer diagnostic" in result.log_tail


def test_success_publishes_engine_files_and_resolves_relative_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = _godot(monkeypatch, ["success"])
    graph = {"nodes": [], "connections": []}
    result = render.render(graph, size=8, outdir="output", basename="sample", target="Unity/URP")

    assert result.ok, result.error
    cmd = calls[0]
    assert Path(cmd[cmd.index("--export-material") + 1]).is_absolute()
    assert Path(cmd[cmd.index("-o") + 1]).is_absolute()
    assert cmd[cmd.index("--target") + 1] == "Unity/URP"
    output = tmp_path / "output"
    assert set(result.images) == {str(output / "sample_albedo.png"),
                                  str(output / "sample_heightmap.png")}
    assert json.loads((output / "sample.ptex").read_text()) == graph
    assert (output / "sample.tres").read_text() == "new engine material"
    assert (output / "metadata/material.py").read_text() == "engine helper"
    assert not list(output.glob(".render-*"))


@pytest.mark.parametrize("is_preview", [False, True])
def test_retry_cannot_reuse_the_crashed_attempts_output(tmp_path, monkeypatch, is_preview):
    calls = _godot(monkeypatch, ["crash", "missing"])
    output = tmp_path / "output"
    if is_preview:
        inputs = _preview_inputs(tmp_path)
        result = preview.render_preview(*inputs, outdir=str(output), basename="sample")
    else:
        result = render.render({"nodes": []}, size=8, outdir=str(output), basename="sample")
    assert len(calls) == 2
    assert not result.ok, result
    assert list(output.iterdir()) == []


def _preview_inputs(tmp_path):
    result = []
    for name in ("albedo", "normal", "orm"):
        path = tmp_path / f"{name}.png"
        path.write_bytes(_png())
        result.append(str(path))
    return result


@pytest.mark.parametrize("outcome", ["nonzero", "missing", "corrupt", "truncated", "timeout"])
def test_failed_preview_preserves_previous_image(tmp_path, monkeypatch, outcome):
    inputs = _preview_inputs(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    previous = _png("blue")
    image = output / "sample_preview.png"
    image.write_bytes(previous)
    _godot(monkeypatch, [outcome])

    result = preview.render_preview(*inputs, outdir=str(output), basename="sample")

    assert not result.ok, result
    assert result.image is None
    assert image.read_bytes() == previous
    assert list(output.iterdir()) == [image]


def test_successful_preview_publishes_decoded_png(tmp_path, monkeypatch):
    inputs = _preview_inputs(tmp_path)
    _godot(monkeypatch, ["success"])
    monkeypatch.chdir(tmp_path)
    result = preview.render_preview(*inputs, outdir="output", basename="sample")
    assert result.ok, result.error
    image = tmp_path / "output/sample_preview.png"
    assert result.image == str(image)
    assert image.read_bytes() == _png()
    assert list(image.parent.iterdir()) == [image]


def test_unreal_helper_references_published_textures(tmp_path, monkeypatch):
    def fake_run(cmd, timeout, before_attempt=None):
        if before_attempt:
            before_attempt()
        stage = Path(cmd[cmd.index("-o") + 1])
        texture = stage / "sample_albedo.png"
        texture.write_bytes(_png())
        # Match Material Maker's Unreal/Unreal Engine 5 template: it embeds
        # $(path_prefix), whereas Godot and Unity mostly use relative names.
        (stage / "sample.py").write_text(
            f"mm.import_texture('{texture.as_posix()}', '/Game/Textures')\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render, "_run_godot", fake_run)
    result = render.render({"nodes": []}, size=8, outdir=str(tmp_path),
                           basename="sample", target="Unreal/Unreal Engine 5")
    assert result.ok, result.error
    helper = (tmp_path / "sample.py").read_text(encoding="utf-8")
    assert (tmp_path / "sample_albedo.png").as_posix() in helper
    assert ".render-" not in helper


def test_staging_preserves_document_relative_input_textures(tmp_path, monkeypatch):
    original_image = _png("red")
    (tmp_path / "texture.png").write_bytes(original_image)
    graph = {"nodes": [{"name": "image", "type": "image", "parameters": {
        "image": "%PROJECT_PATH%/texture.png",
    }}]}

    def fake_run(cmd, timeout, before_attempt=None):
        if before_attempt:
            before_attempt()
        source = Path(cmd[cmd.index("--export-material") + 1])
        applied = json.loads(source.read_text(encoding="utf-8"))
        parameter = applied["nodes"][0]["parameters"]["image"]
        # Material Maker resolves this token against the loaded document's
        # directory, not the process cwd or the selected output directory.
        image = Path(parameter.replace("%PROJECT_PATH%", source.parent.as_posix()))
        rendered = Path(cmd[cmd.index("-o") + 1]) / "sample_albedo.png"
        rendered.write_bytes(image.read_bytes() if image.is_file() else _png("black"))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render, "_run_godot", fake_run)
    result = render.render(graph, size=8, outdir=str(tmp_path), basename="sample")
    assert result.ok, result.error
    assert Path(result.images[0]).read_bytes() == original_image
    assert json.loads((tmp_path / "sample.ptex").read_text()) == graph


def test_dynamic_texture_buffers_keep_their_source_dimensions(tmp_path, monkeypatch):
    image = BytesIO()
    Image.new("RGB", (16, 8), "red").save(image, format="PNG")

    def fake_run(cmd, timeout, before_attempt=None):
        if before_attempt:
            before_attempt()
        stage = Path(cmd[cmd.index("-o") + 1])
        (stage / "sample_texture_0.png").write_bytes(image.getvalue())
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render, "_run_godot", fake_run)
    result = render.render({"nodes": [{"type": "material_dynamic"}]}, size=256,
                           outdir=str(tmp_path), basename="sample")
    assert result.ok, result.error
    assert Path(result.images[0]).read_bytes() == image.getvalue()


def test_rerender_keeps_native_protected_materials_and_metadata(tmp_path, monkeypatch):
    previous = {"sample.tres": b"user material edits", "sample.mat": b"old material GUIDs",
                "sample_albedo.png.meta": b"original texture GUID", "sample.gltf": b"edited scene"}
    for name, content in previous.items():
        (tmp_path / name).write_bytes(content)
    (tmp_path / "sample.py").write_text("old unprotected helper")

    def fake_run(cmd, timeout, before_attempt=None):
        if before_attempt:
            before_attempt()
        stage = Path(cmd[cmd.index("-o") + 1])
        (stage / "sample_albedo.png").write_bytes(_png())
        for name in previous:
            # Native CLI skips existing products marked prompt_overwrite.
            path = stage / name
            if not path.exists():
                path.write_bytes(b"regenerated material or metadata")
        (stage / "sample.py").write_text("new unprotected helper")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render, "_run_godot", fake_run)
    result = render.render({"nodes": []}, size=8, outdir=str(tmp_path), basename="sample")
    assert result.ok, result.error
    assert {name: (tmp_path / name).read_bytes() for name in previous} == previous
    assert (tmp_path / "sample.py").read_text() == "new unprotected helper"
