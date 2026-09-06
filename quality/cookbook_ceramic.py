"""Cookbook: ceramic category. Phase-3 hero folded in from the retired
examples/ folder (2026-09-05): the graph comes unchanged from
quality/author.py's shared builder via take_variant; this builder only groups
it. Outputs land under quality/authored/cookbook-ceramic/<case>/v1.ptex.

Run: python -m quality.cookbook_ceramic
Then: python -m quality.promote_cookbook cookbook-ceramic
"""
import sys

from quality import author  # shared builder base; regression guard is promote_cookbook --check
from quality.author_helpers import save_variant, take_variant, group_into_subgraph, rename_nodes

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-ceramic"

# `beehive` donor mapping for man02. beehive_2 produces the clean hex value
# (port 0, rewired to drive albedo/roughness directly) and a per-cell random
# tone (port 1); colorize_2/colorize convert those two into the inputs mixed
# by blend for the relief pathway (normal + height), which man02's albedo
# and roughness no longer read from since they were rewired straight off
# beehive_2. Material port 6 is depth_tex (height), fed by colorize_3.
_MAN02_NAMES = {
    "beehive_2": "HexLayout",
    "colorize_5": "TileColor",       # albedo: tile + thin grout line
    "colorize_4": "GlazeRoughness",  # roughness: inverted (glazed face, rough grout)
    "colorize_2": "StructureTone",   # hex-value tone feeding the relief blend
    "colorize": "CellRandomTone",    # per-cell random tone feeding the relief blend
    "blend": "ReliefBlend",          # mixes the two tones for normal + height
    "normal_map": "GroutNormal",
    "colorize_3": "GroutDepth",      # feeds Material's depth_tex port
    "uniform_greyscale": "NonMetallic",
}


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
    rename_nodes(g, _MAN02_NAMES)
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
