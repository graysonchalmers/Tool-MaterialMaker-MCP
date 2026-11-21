import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from PIL import Image

from mm_mcp import unity_export


def _write(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


@pytest.fixture
def metric_project(tmp_path, monkeypatch):
    monkeypatch.setattr(unity_export, "SIZE", (4, 4))
    root = tmp_path / "unity"
    binary = _write(tmp_path / "material-maker", b"native executable fixture")
    binary_sha = unity_export._digest(binary)
    families = []
    for family_id in sorted(unity_export.FAMILY_IDS):
        graph = unity_export._graph_path(family_id)
        graph_source = _write(root / graph, b'{"nodes": []}')
        maps = []
        for role in unity_export.ROLES:
            path = _write(root / unity_export._texture_path(family_id, role), role.encode())
            maps.append({
                "role": role, "path": path.relative_to(root).as_posix(),
                "sha256": unity_export._digest(path), "bytes": path.stat().st_size,
                "width": 4, "height": 4, "bitDepth": 16 if role == "height" else 8,
                "encoding": "sRGB" if role == "baseColor" else "linear",
            })
        families.append({
            "id": family_id, "graph": graph.as_posix(), "graphSha256": unity_export._digest(graph_source),
            "repeatMetres": [8, 8], "heightRangeMetres": 0.032, "normalConvention": "OpenGL +Y",
            "normalHeightMeanDot": 0.999, "nativeRepeatIdentical": True, "maps": maps,
        })
    manifest = {
        "schema": 1, "binarySha256": binary_sha, "nativeTarget": "Unity/URP", "nativeDimensions": [4, 4],
        "normalConvention": "OpenGL +Y", "ormChannels": ["occlusion", "perceptual roughness", "metallic", "opaque"],
        "susceptibilityChannels": ["moisture", "moss", "exposure"], "sourceGraphsEditable": True,
        "nativeRepeatCompared": True, "families": families,
    }
    _write(root / unity_export.MANIFEST, json.dumps(manifest).encode())
    project = unity_export.load_metric_surface_project(root, "refined-stone")
    stage = tmp_path / "stage"
    stage.mkdir()
    return project, stage, binary, binary_sha


def _graph(*, extra_nodes=()) -> bytes:
    return json.dumps({
        "nodes": [{"name": "Material", "type": "material"}] + [
            {"name": role, "type": "export", "parameters": {"suffix": "$project-" + role, "format": 0}}
            for role in ("height16", "response", "susceptibility")
        ] + list(extra_nodes),
    }).encode()


def _fake_native(*, variance=False):
    def run(_binary, graph, output, _config, _timeout):
        output.mkdir()
        colors = {
            "baseColor": (80, 90, 100, 255),
            "normal": (128, 128, 255, 255),
            "heightTransport": (0x12, 0x34, 0, 255),
            "height8": (255 - 0x12,) * 3 + (255,),
            "metalSmoothness": (15, 0, 0, 255 - 111),
            "occlusion": (75, 0, 0, 255),
            "response": (111, 75, 15, 1),
            "susceptibility": (4, 5, 6, 255),
        }
        if variance and output.name == "repeat":
            colors["baseColor"] = (90, 90, 100, 255)
        for role, color in colors.items():
            name = graph.stem + unity_export.NATIVE_MAPS[role]
            Image.new("RGBA", unity_export.SIZE, color).save(output / name)
        (output / "native.log").write_text("fixture log")
        return 0.01, {"processSucceeded": True}
    return run


def _bake(fixture, monkeypatch, *, variance=False):
    project, stage, binary, binary_sha = fixture
    monkeypatch.setattr(unity_export, "_run_native", _fake_native(variance=variance))
    return unity_export.bake_metric_surface(
        _graph(), project=project, binary=binary, binary_sha256=binary_sha, stage_path=stage,
    )


def test_verified_native_maps_and_full_unity_overlay(metric_project, monkeypatch):
    project, stage, _, _ = metric_project
    original_manifest = project.manifest_path.read_bytes()
    receipt = _bake(metric_project, monkeypatch)
    result = unity_export.stage_metric_surface_change(project=project, stage_path=stage, family_receipt=receipt)
    overlay = stage / result["overlay"]
    output_manifest = json.loads((overlay / result["manifest"]).read_bytes())

    assert project.manifest_path.read_bytes() == original_manifest
    assert result["familyCount"] == len(output_manifest["families"]) == 12
    assert result["baseManifestSha256"] == project.manifest_sha256
    assert result["family"] == receipt
    assert receipt["nativeRepeatIdentical"] and receipt["normalHeightMeanDot"] > 0.99
    assert receipt["normalHeightSamples"] == 16
    assert receipt["heightDistinctValues"] == 1
    assert (overlay / receipt["graph"]).read_bytes() == _graph()
    for family in output_manifest["families"]:
        if family["id"] != "refined-stone":
            assert family in project.manifest["families"]
        unity_export._verify_family_files(overlay if family["id"] == "refined-stone" else project.root, family)

    paths = {item["role"]: overlay / item["path"] for item in receipt["maps"]}
    with Image.open(paths["height"]) as image:
        assert image.getextrema() == (0x1234, 0x1234)
    with Image.open(paths["orm"]) as image:
        assert image.getpixel((0, 0)) == (75, 111, 15, 255)
        assert "srgb" not in image.info
    with Image.open(paths["baseColor"]) as image:
        assert image.info["srgb"] == 0
    with ZipFile(stage / result["evidence"]) as archive:
        assert archive.read("default/refined-stone-height16.png") == archive.read("repeat/refined-stone-height16.png")
        assert archive.read("repeat/native.log") == b"fixture log"


def test_repeat_mismatch_stops_before_staging(metric_project, monkeypatch):
    _, stage, _, _ = metric_project
    with pytest.raises(unity_export.UnityExportError) as error:
        _bake(metric_project, monkeypatch, variance=True)
    assert error.value.code == "nondeterministic_export"
    assert error.value.details["maps"] == ["refined-stone_albedo.png"]
    assert not list(stage.iterdir())


@pytest.mark.parametrize("path", ["../escape", "$project-../escape", "$project-$node", "$project-response"])
def test_unsafe_export_suffix_is_rejected_in_nested_graphs(path):
    graph = _graph(extra_nodes=[{
        "name": "Subgraph", "type": "graph", "nodes": [
            {"name": "Unexpected", "type": "export", "parameters": {"suffix": path, "format": 0}},
        ],
    }])
    with pytest.raises(unity_export.UnityExportError) as error:
        unity_export._check_export_nodes(graph)
    assert error.value.code == "invalid_export_node"
    assert error.value.details["node"] == "Unexpected" or path == "$project-response"


@pytest.mark.parametrize(("node", "code"), [
    ({"type": "shader", "shader_model": {"exports": {}}}, "custom_export_profile"),
    ({"type": "image", "parameters": {"image": "input.png"}}, "external_asset_input"),
    ({"type": "website:example"}, "external_asset_input"),
    ({"type": "material"}, "invalid_material_outputs"),
])
def test_native_profile_requires_a_single_self_contained_material(node, code):
    with pytest.raises(unity_export.UnityExportError) as error:
        unity_export._check_export_nodes(_graph(extra_nodes=[node]))
    assert error.value.code == code


def test_staging_refuses_changed_baseline_map(metric_project, monkeypatch):
    project, stage, _, _ = metric_project
    receipt = _bake(metric_project, monkeypatch)
    _write(project.root / unity_export._texture_path("slate", "orm"), b"changed")
    with pytest.raises(unity_export.UnityExportError) as error:
        unity_export.stage_metric_surface_change(project=project, stage_path=stage, family_receipt=receipt)
    assert error.value.code == "map_hash_mismatch"
    assert not (stage / unity_export.OVERLAY / unity_export.MANIFEST).exists()
