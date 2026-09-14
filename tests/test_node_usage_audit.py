"""quality.node_usage_audit must run clean against the real cookbook and
produce sane, well-typed output. This is a reporting tool, not a graph --
see quality/noise_gallery.py's docstring for why noise coverage isn't
pixel-testable, so there is no render/pixel assertion here."""
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

from quality.node_usage_audit import audit, _NOISE_PATTERN_NODES


def test_noise_pattern_nodes_are_all_real_catalog_types():
    # One-directional guard only: every curated name must exist as a real
    # Material Maker node type (catches typos, deletions, stale names). It
    # does NOT assert completeness -- whether some other real generator node
    # belongs in the set stays a manual judgment call (see the module
    # docstring), not something this test decides.
    catalog = build_catalog(load_config().nodes_dir)
    missing = _NOISE_PATTERN_NODES - set(catalog)
    assert not missing, f"_NOISE_PATTERN_NODES has stale/typo'd names: {sorted(missing)}"


def test_audit_partitions_noise_pattern_nodes_used_vs_unused():
    report = audit()
    used = set(report["noise_used"])
    unused = set(report["noise_unused"])
    assert used | unused == _NOISE_PATTERN_NODES
    assert used.isdisjoint(unused)


def test_perlin_and_voronoi_are_used():
    # The two base generators every early cookbook material leaned on
    # (2026-09-01 finding); a regression here means the subgraph recursion
    # broke, since both generators now live one level inside a group.
    report = audit()
    assert "perlin" in report["noise_used"]
    assert "voronoi" in report["noise_used"]


def test_materials_by_type_lists_real_cookbook_ids():
    report = audit()
    assert len(report["materials_by_type"]["perlin"]) > 0
    for material_id in report["materials_by_type"]["perlin"]:
        assert isinstance(material_id, str) and material_id
