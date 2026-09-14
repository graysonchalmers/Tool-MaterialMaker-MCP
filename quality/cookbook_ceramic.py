"""Cookbook: ceramic category. Phase-3 hero folded in from the retired
examples/ folder (2026-09-05): the graph comes unchanged from
quality/author.py's shared builder via take_variant; this builder only groups
it. Outputs land under quality/authored/cookbook-ceramic/<case>/v1.ptex.

Run: python -m quality.cookbook_ceramic
Then: python -m quality.promote_cookbook cookbook-ceramic
"""
import sys

from quality import author  # shared builder base; regression guard is promote_cookbook --check
from quality.author_helpers import (save_variant, take_variant, group_into_subgraph, rename_nodes,
                     set_gradient, set_param, retype, add_node, _grad,
                     _from_scratch_noise_material)

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


_MAN03_NAMES = {
    "perlin_0": "MosaicTiles",     # placeholder perlin, retyped to skewed_bricks below
    "colorize_0": "TileColor",
    "normal_map_0": "MosaicNormal",
    "rough_const": "RoughnessConst",
}


def build_man03_mosaic_tile(catalog: dict) -> str:
    """Hand-set mosaic tile: the first cookbook material to use
    `skewed_bricks`, a standalone brick-tile generator with per-tile
    positional jitter (all three of its inputs -- mortar_map/bevel_map/
    round_map -- are optional `f` maps with function defaults, so it works
    without a donor). Built from scratch via `_from_scratch_noise_material`
    (no donor has this topology), then `retype()`d from the placeholder
    `perlin_0` to `skewed_bricks` -- the same connection-safe swap
    `t09_rippled_wet_sand`/`t10_packed_dirt` use, since `skewed_bricks`' port
    0 ("Bricks Pattern", a plain `f` grayscale) matches `perlin`'s output.
    Params are `skewed_bricks`' own catalog defaults (verified via
    `describe_node`): `randomness=1` is the key differentiator from the
    category's existing `man02_ceramic_hex_tiles` (a perfectly regular hex
    grid built from `beehive`, zero per-cell jitter) -- at `randomness=1`
    each brick's vertical cut is offset from a perfect grid line, so courses
    read as hand-set/reclaimed rather than machine-uniform.

    VERIFICATION (isolated single-node render of the retyped node via the
    MCP `render_node_output` tool, at 512x512, un-recolored so the raw
    0..1 scalar shows as grayscale): the render is a clean rectangular
    running-bond brick grid (6 rows / 3 columns, staggered by `offset=0.5`)
    with each vertical mortar seam visibly skewed/slanted rather than
    straight -- the jitter from `randomness=1` is plainly visible course to
    course, distinct in kind from `man02`'s dead-straight hex edges. Each
    brick also shows a soft diagonal bevel facet (light/shadow split) from
    the `bevel=0.1` param, giving individual bricks a slight embossed
    look rather than flat rectangles.

    Measured histogram (96x96 sample grid) informed the gradient stops
    below: 32.5% of samples are exactly 0 (deep mortar interior) and this
    plateau is already ~33% by position 0.10, so grout is held flat through
    pos 0.12; 50% of samples are exactly 1.0 (deep tile-face interior), and
    the climb from the mortar plateau to a majority-face reading happens
    across roughly pos 0.12-0.30 (cumulative count only reaches 36% by pos
    0.50, then jumps to 47.5% by pos 0.60), so the albedo/roughness ramps
    both finish by pos 0.30 -- past that point the signal is overwhelmingly
    face pixels, so holding flat from 0.30 to 1.0 does not clip a
    significant band of mid-tones.

    Palette: warm ivory/earth-tone tile face (not `man02`'s stark white, to
    keep the two hero ceramics visually distinct) with a near-black warm
    grout line. Roughness deviates from the "flat roughness texture" recipe
    in the shared shape above: like `man02`'s `colorize_4`, `rough_const` is
    wired from the SAME retyped field (`perlin_0`/`skewed_bricks`) rather
    than a flat two-point same-value gradient, with its gradient stops at
    the identical positions as the albedo ramp but inverted (high roughness
    on the grout, low/glazed roughness on the tile face) -- a flat scalar
    would light the recessed grout and the glazed face identically, losing
    the ceramic contrast the brief calls for."""
    g = _from_scratch_noise_material(
        {"scale_x": 4, "scale_y": 4},  # placeholder; retyped to skewed_bricks below
        [(0.0, 0.10, 0.09, 0.08), (1.0, 0.10, 0.09, 0.08)],  # placeholder, overwritten below
        metallic=0.0, roughness=0.5, normal_amount=0.4)
    retype(g, "perlin_0", "skewed_bricks", {
        "rows": 6, "columns": 3, "offset": 0.5, "randomness": 1,
        "mortar": 0.1, "bevel": 0.1, "round": 0, "corner": 0.3})
    set_param(g, "normal_map_0", "param4", 0)
    set_gradient(g, "colorize_0", [                              # albedo: ivory tile, dark grout
        (0.0, 0.10, 0.09, 0.08),   # grout (near-black, warm)
        (0.12, 0.10, 0.09, 0.08),  # hold flat through the measured mortar plateau
        (0.30, 0.85, 0.79, 0.66),  # fast ramp to tile color
        (1.0, 0.92, 0.87, 0.74)])  # tile face (warm ivory)
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([                                # roughness: inverted vs albedo
                 (0.0, 0.78, 0.78, 0.78),   # grout: rough
                 (0.12, 0.78, 0.78, 0.78),  # hold flat through the mortar plateau
                 (0.30, 0.14, 0.14, 0.14),  # fast ramp to glazed
                 (1.0, 0.08, 0.08, 0.08)])})  # tile face: glazed (low roughness)
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})
    group_into_subgraph(
        g, ["perlin_0", "colorize_0"], "mosaic_pattern", "Mosaic Pattern",
        [("perlin_0", "rows", "param0", "Rows"),
         ("perlin_0", "randomness", "param1", "Jitter"),
         ("colorize_0", "gradient", "param2", "Tile and grout color")],
        catalog,
    )
    group_into_subgraph(
        g, ["normal_map_0", "rough_const"], "mosaic_finish", "Mosaic Finish",
        [("normal_map_0", "param1", "param0", "Grout depth"),
         ("rough_const", "gradient", "param1", "Roughness")],
        catalog,
    )
    rename_nodes(g, _MAN03_NAMES)
    return save_variant(g, _LABEL, "man03_mosaic_tile", 1)


BUILDERS = {
    "man02_ceramic_hex_tiles": build_man02_ceramic_hex_tiles,
    "man03_mosaic_tile": build_man03_mosaic_tile,
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
