"""Cookbook: bare-metal category. Both materials are Phase-3 heroes folded in
from the retired examples/ folder (2026-09-05): the graphs come unchanged
from quality/author.py's frozen builders via take_variant; these builders
only group them into named subgraphs. Outputs land under
quality/authored/cookbook-metal/<case>/v1.ptex.

Run: python quality/cookbook_metal.py
Then: python quality/promote_cookbook.py cookbook-metal
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import author  # frozen Phase-3 builders; called, never edited
from author_helpers import save_variant, take_variant, group_into_subgraph

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-metal"


def build_m01_weathered_copper(catalog: dict) -> str:
    """Weathered copper (was examples/m01_weathered_copper, iter1 variant 1):
    `rusted_metal`'s two-layer blend recolored, base gray -> copper, patches
    orange rust -> green verdigris, patch mask unchanged. Grouped into the
    three ideas the donor is built from: where the patches are, what the two
    metals look like, and how rough each is."""
    g = take_variant(author.build_m01_weathered_copper, _LABEL, 1)
    group_into_subgraph(
        g, ["perlin_2", "colorize_3", "colorize_4"],
        "patina_pattern", "Patina Pattern",
        [("perlin_2", "scale_x", "param0", "Patch size"),
         ("colorize_3", "gradient", "param1", "Patina coverage")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_1", "colorize_2", "colorize_1", "blend_0"],
        "copper_color", "Copper Color",
        [("colorize_2", "gradient", "param0", "Copper color"),
         ("colorize_1", "gradient", "param1", "Verdigris color")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_0", "colorize_0", "blend_1"],
        "surface_finish", "Surface Finish",
        [("colorize_0", "gradient", "param0", "Roughness")],
        catalog,
    )
    return save_variant(g, _LABEL, "m01_weathered_copper", 1)


def build_m02_brushed_aluminum(catalog: dict) -> str:
    """Brushed aluminum (was examples/m02_brushed_aluminum, iter1 variant 2):
    `wood` clone with the grain straightened (blend_0's second input fed from
    the straight perlin_2 instead of the knot warp), finer longer streaks,
    neutral gray albedo, uniform metallic (the grain-driven metallic wire is
    dropped so the scalar 1 applies), low anisotropic roughness, and shallow
    brush-scratch relief via normal_map param4=0. The straightening leaves
    wood's knot-warp chain (perlin_0, perlin_1, warp_0, voronoi_0, colorize_1,
    warp_1) connected to nothing downstream; it is grouped separately and
    labeled as the unused donor leftover rather than deleted, so the graph
    still tells the "wood grain became brushed metal" story."""
    g = take_variant(author.build_m02_brushed_aluminum, _LABEL, 2)
    group_into_subgraph(
        g, ["perlin_2", "blend_0", "colorize_2", "colorize_0", "normal_map_0"],
        "brushed_finish", "Brushed Finish",
        [("perlin_2", "scale_x", "param0", "Streak length"),
         ("perlin_2", "scale_y", "param1", "Streak density"),
         ("colorize_2", "gradient", "param2", "Aluminum color"),
         ("colorize_0", "gradient", "param3", "Roughness"),
         ("normal_map_0", "param1", "param4", "Scratch depth")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_0", "perlin_1", "warp_0", "voronoi_0", "colorize_1", "warp_1"],
        "wood_knot_leftover", "Wood Donor Leftover (unused)",
        [],
        catalog,
    )
    return save_variant(g, _LABEL, "m02_brushed_aluminum", 1)


BUILDERS = {
    "m01_weathered_copper": build_m01_weathered_copper,
    "m02_brushed_aluminum": build_m02_brushed_aluminum,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    catalog = build_catalog(load_config().nodes_dir)  # once per run, threaded through
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
