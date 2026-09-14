import json
import tempfile
import os

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
