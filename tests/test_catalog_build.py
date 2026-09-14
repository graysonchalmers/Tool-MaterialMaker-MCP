import glob
import json
import tempfile
import os
import types

import mm_mcp.catalog_builder as catalog_builder
from mm_mcp.catalog_builder import build_catalog, SPECIAL_TYPES
from mm_mcp.config import load_config

cfg = load_config()


def test_catalog_has_core_nodes():
    cat = build_catalog(cfg.nodes_dir)
    assert len(cat) > 300
    for t in ("blend", "colorize", "perlin", "material"):
        assert t in cat


def test_material_node_has_texture_inputs():
    cat = build_catalog(cfg.nodes_dir)
    mat = cat["material"]
    names = [i["name"] for i in mat["inputs"]]
    assert names[0] == "albedo_tex"
    assert "roughness_tex" in names


def test_special_types_present():
    assert "graph" in SPECIAL_TYPES
    assert "comment" in SPECIAL_TYPES


def test_named_parameter_widget_resolves_its_own_inline_range():
    """directional_noise.mmg's 'n_scale' widget is a bare 'named_parameter'
    with no linked_widgets at all -- its min/max/step/default live directly
    on the widget dict. dirt.mmg's 'd_scale' widget is the same shape. Both
    must resolve to a real numeric range, not None."""
    cat = build_catalog(cfg.nodes_dir)
    n_scale = {p["name"]: p for p in cat["directional_noise"]["parameters"]}["n_scale"]
    assert n_scale["min"] == 1
    assert n_scale["max"] == 8

    d_scale = {p["name"]: p for p in cat["dirt"]["parameters"]}["d_scale"]
    assert d_scale["min"] == 1
    assert d_scale["max"] == 8


def test_linked_control_resolves_through_a_type_referenced_inner_node():
    """crystal.mmg's 'param0' widget links to an inner node named 'voronoi'
    whose 'type' is 'voronoi' -- a plain type reference, not an inline shader
    node with its own embedded shader_model. Resolving it requires looking up
    the separately-parsed 'voronoi' catalog entry's own 'scale_x' parameter,
    whose real range (per voronoi.mmg) is min=1, max=32."""
    cat = build_catalog(cfg.nodes_dir)
    param0 = {p["name"]: p for p in cat["crystal"]["parameters"]}["param0"]
    assert param0["min"] == 1
    assert param0["max"] == 32


def test_build_catalog_resolves_compound_to_compound_links_order_independently(monkeypatch):
    """binary_smooth.mmg's 'smooth' widget links (via linked_control) to
    fast_blur's 'param1' -- ANOTHER compound node's parameter, not a leaf's.
    fast_blur.param1 itself only resolves once fast_blur has been
    re-resolved against the full catalog (it links to the leaf-referenced
    fast_blur_shader.sigma, min=1/max=256/step=1/default=1).

    A pass-2 implementation that sweeps generic nodes only ONCE gives a
    different answer for binary_smooth.smooth depending on whether
    binary_smooth or fast_blur happens to be visited first in that sweep --
    and that visitation order tracks glob.glob()'s file order, which the
    stdlib does not guarantee to be sorted or stable across platforms. This
    is exactly the class of bug the crystal/voronoi (compound-to-LEAF) case
    cannot catch, because a leaf's parameters are already fully resolved
    after pass 1 regardless of order.

    Build the catalog under forward and reversed glob order (a real
    monkeypatch of catalog_builder's glob.glob, not just this one entry)
    and assert both agree, and both fully resolve."""
    real_files = glob.glob(os.path.join(cfg.nodes_dir, "*.mmg"))
    assert real_files, "expected to find real .mmg fixture files"

    def build_with_file_order(files):
        monkeypatch.setattr(
            catalog_builder, "glob",
            types.SimpleNamespace(glob=lambda *a, **k: list(files)),
        )
        return build_catalog(cfg.nodes_dir)

    cat_forward = build_with_file_order(real_files)
    cat_reversed = build_with_file_order(list(reversed(real_files)))

    for label, cat in (("forward", cat_forward), ("reversed", cat_reversed)):
        smooth = {p["name"]: p for p in cat["binary_smooth"]["parameters"]}["smooth"]
        assert smooth.get("min") == 1, f"{label} order: smooth.min unresolved"
        assert smooth.get("max") == 256, f"{label} order: smooth.max unresolved"
        assert smooth.get("step") == 1, f"{label} order: smooth.step unresolved"

    assert cat_forward == cat_reversed


def test_build_catalog_skips_malformed_files(capsys):
    """Verify that malformed .mmg files are skipped with a warning, and valid ones are included."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a malformed JSON file (invalid JSON)
        malformed_path = os.path.join(tmpdir, "malformed.mmg")
        with open(malformed_path, "w", encoding="utf-8") as fh:
            fh.write("{ invalid json ")

        # Create a valid minimal shader_model file
        valid_path = os.path.join(tmpdir, "valid_minimal.mmg")
        valid_data = {
            "shader_model": {
                "inputs": [],
                "outputs": [],
                "parameters": []
            }
        }
        with open(valid_path, "w", encoding="utf-8") as fh:
            json.dump(valid_data, fh)

        # Build catalog from the temp directory
        cat = build_catalog(tmpdir)

        # Verify malformed file was skipped
        assert "malformed" not in cat

        # Verify valid file was included
        assert "valid_minimal" in cat
        assert cat["valid_minimal"]["type"] == "valid_minimal"

        # Verify warning was printed to stderr
        captured = capsys.readouterr()
        assert "WARNING: skipping malformed.mmg" in captured.err
        assert "JSON" in captured.err or "json" in captured.err or "Expecting" in captured.err
