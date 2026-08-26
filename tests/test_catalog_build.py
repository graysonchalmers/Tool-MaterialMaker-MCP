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
