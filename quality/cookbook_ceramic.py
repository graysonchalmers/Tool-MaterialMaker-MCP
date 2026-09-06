"""Cookbook: ceramic category. Phase-3 hero folded in from the retired
examples/ folder (2026-09-05): the graph comes unchanged from
quality/author.py's frozen builder via take_variant; this builder only groups
it. Outputs land under quality/authored/cookbook-ceramic/<case>/v1.ptex.

Run: python -m quality.cookbook_ceramic
Then: python -m quality.promote_cookbook cookbook-ceramic
"""
import sys

from quality import author  # frozen Phase-3 builders; called, never edited
from quality.author_helpers import save_variant, take_variant, group_into_subgraph

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-ceramic"


def build_man02_ceramic_hex_tiles(catalog: dict) -> str:
    """White ceramic hexagon tiles (was examples/man02_ceramic_hex_tiles,
    iter1 variant 1): `beehive` clone, non-metallic, faces recolored white
    with a thin dark grout band, roughness inverted (glazed faces, rough
    grout), hex relief kept so grout reads recessed. Grouped into the tile
    pattern (what you see) and the tile relief (what you feel);
    `uniform_greyscale` (metallic 0) stays top-level as a single
    donor-default constant."""
    g = take_variant(author.build_man02_ceramic_hex_tiles, _LABEL, 1)
    group_into_subgraph(
        g, ["beehive_2", "colorize_5", "colorize_4"],
        "tile_pattern", "Tile Pattern",
        [("beehive_2", "sx", "param0", "Tiles across"),
         ("beehive_2", "sy", "param1", "Tiles down"),
         ("colorize_5", "gradient", "param2", "Tile and grout color"),
         ("colorize_4", "gradient", "param3", "Glaze roughness")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_2", "colorize", "blend", "normal_map", "colorize_3"],
        "tile_relief", "Tile Relief",
        [("normal_map", "param1", "param0", "Grout depth"),
         ("blend", "amount", "param1", "Edge softness")],
        catalog,
    )
    return save_variant(g, _LABEL, "man02_ceramic_hex_tiles", 1)


BUILDERS = {
    "man02_ceramic_hex_tiles": build_man02_ceramic_hex_tiles,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
