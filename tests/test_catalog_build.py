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
