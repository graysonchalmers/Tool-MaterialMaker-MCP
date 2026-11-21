from hashlib import sha256
from math import sqrt
from struct import pack

from PIL import Image
import pytest

from mm_mcp.material_feedback import build_material_feedback, measure_normal_height


def make_maps(directory, *, base_offset=0):
    directory.mkdir()
    names = ("baseColor", "normal", "orm", "height", "susceptibility")
    paths = {name: directory / f"{name}.png" for name in names}
    size = (4, 4)
    base = Image.new("RGB", size)
    base.putdata([(base_offset + 5 * x,) * 3 for _ in range(4) for x in range(4)])
    base.save(paths["baseColor"])
    Image.new("RGB", size, (128, 128, 255)).save(paths["normal"])
    Image.new("RGBA", size, (255, 130, 0, 255)).save(paths["orm"])
    heights = [30000 + 31 * x for _ in range(4) for x in range(4)]
    Image.frombytes("I;16", size, pack("<16H", *heights)).save(paths["height"])
    Image.new("RGB", size, (1, 2, 3)).save(paths["susceptibility"])
    return paths


def test_feedback_shows_both_variants_and_measures_unmodified_maps(tmp_path):
    candidate = make_maps(tmp_path / "candidate", base_offset=150)
    baseline = make_maps(tmp_path / "baseline")
    all_paths = list(candidate.values()) + list(baseline.values())
    before = {path: sha256(path.read_bytes()).digest() for path in all_paths}
    preview = tmp_path / "comparison.png"
    evidence = build_material_feedback(
        candidate,
        preview,
        repeat_metres=(8, 4),
        height_range_metres=0.032,
        baseline_maps=baseline,
        baseline_repeat_metres=(4, 4),
    )

    assert evidence["image"] == str(preview)
    assert evidence["previewSpanMetres"] == [24.0, pytest.approx(10.9333)]
    assert evidence["grazingPreviewSpanMetres"][0] < evidence["previewSpanMetres"][0]
    with Image.open(preview) as image:
        assert image.size == (evidence["imageWidth"], evidence["imageHeight"])
        assert image.getpixel((36, 80))[0] < 25
        assert image.getpixel((410, 80))[0] > 140
    assert evidence["baseline"]["repeatMetres"] == [4, 4]
    assert evidence["candidate"]["repeatMetres"] == [8, 4]
    diagnostics = evidence["candidate"]
    assert diagnostics["normalHeightMeanDot"] > 0.99998
    assert diagnostics["normalHeightSamples"] == 16
    assert diagnostics["mapSeams"]["baseColor"]["x"]["edgeToInteriorRatio"] == 3
    assert diagnostics["mapSeams"]["height"]["x"] == {
        "edgeStep": pytest.approx(93 / 65535),
        "interiorStep": pytest.approx(31 / 65535, abs=1e-8),
        "edgeToInteriorRatio": 3,
    }
    assert diagnostics["mapSeams"]["height"]["y"]["edgeStep"] == 0
    assert {path: sha256(path.read_bytes()).digest() for path in all_paths} == before


def test_normal_height_checks_periodic_green_channel_sign():
    size = (4, 4)
    heights = [5000, 23000, 54000, 26000]
    height = Image.frombytes("I;16", size, pack("<16H", *(value for value in heights for _ in heights)))
    normals = Image.new("RGB", size)
    encoded = []
    for y, value in enumerate(heights):
        dy = (heights[(y + 1) % len(heights)] - value) * 4 / 65535
        length = sqrt(1 + dy * dy)
        encoded.extend([(128, round(127.5 + 127.5 * dy / length), round(127.5 + 127.5 / length))] * 4)
    normals.putdata(encoded)
    correct = measure_normal_height(normals, height, [1, 1], 1, max_samples=None)
    normals.putdata([(r, 255 - g, b) for r, g, b in encoded])
    flipped = measure_normal_height(normals, height, [1, 1], 1, max_samples=None)

    assert correct["samples"] == 16
    assert correct["minDot"] > 0.99997
    assert correct["meanDot"] > 0.99997
    assert flipped["meanDot"] < 0.0


def test_missing_or_conflicting_output_keeps_input_and_prior_preview(tmp_path):
    maps = make_maps(tmp_path / "candidate")
    preview = tmp_path / "comparison.png"
    preview.write_bytes(b"previous comparison")
    color = maps["baseColor"].read_bytes()
    with pytest.raises(ValueError, match="distinct from each input"):
        build_material_feedback(maps, maps["baseColor"], repeat_metres=(1, 1), height_range_metres=0.1)
    del maps["normal"]
    with pytest.raises(ValueError, match="missing material maps: normal"):
        build_material_feedback(maps, preview, repeat_metres=(1, 1), height_range_metres=0.1)
    assert preview.read_bytes() == b"previous comparison"
    assert maps["baseColor"].read_bytes() == color
