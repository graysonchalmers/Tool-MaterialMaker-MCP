"""Cookbook growth: stone/masonry-category authoring recipes beyond the
frozen 15-case Phase 3 test set (`s01_red_brick_wall`/`s02_gray_granite`/
`s03_cracked_concrete` are already frozen there -- see quality/test_set.json's
freeze note; this is additive, not an edit to those cases). Informal: 1
variant per material, no scorecard gate. Reuses author.py's graph-surgery
helpers; outputs land under quality/authored/cookbook-stone/<case>/v1.ptex,
same layout convention as the Phase 3 iterations.

Run: python quality/cookbook_stone.py
Then quality/render_cookbook.py renders each variant for inspection.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author import load_example, set_gradient, set_param, save_variant, add_node, rewire, _grad

_LABEL = "cookbook-stone"


def build_s04_scattered_river_stones() -> str:
    """Scattered river stones / pebble bed: rounded stones sitting IN a sand
    matrix with visible gaps between them, not edge-to-edge packed. This is
    the softer, more organic sibling to s06_river_pebbles (which is a solid
    packed mosaic, no gaps) -- Grayson asked for something "softer, like
    river stone, maybe even pebbles" in place of the original concrete
    recipe here. (Concrete's approach -- CLONE `rock`, crush voronoi_0 to
    scale 2 for soft unpatterned staining -- is preserved in AUTHORING.md's
    session history if a poured-concrete recipe is wanted again later; this
    slot is now stones-in-sand, not concrete.)

    CLONE `rock` again, but instead of blending two fields together for a
    flat mottled look (the concrete approach) or filling the whole frame
    with stone cells (s06), THRESHOLD voronoi_0's own distance field
    (port 0, high at cell centers, low near cell borders) into a hard mask:
    high = stone, low = sand gap. Stone albedo comes from voronoi_0's
    per-cell random output (port 2) through a pale, low-contrast natural
    gradient -- softer/lighter than s06's darker slate-to-brown spread, per
    "softer." Sand fills the gaps with perlin-driven warm tan variation.
    Normal relief kept gentle (`param1` ~0.35, lower than s06's 0.6) for
    smooth, water-worn stones rather than s06's more pronounced bulge."""
    g = load_example("rock")
    set_param(g, "voronoi_0", "scale_x", 9)
    set_param(g, "voronoi_0", "scale_y", 9)
    set_param(g, "voronoi_0", "randomness", 1)
    set_param(g, "voronoi_1", "scale_x", 9)
    set_param(g, "voronoi_1", "scale_y", 9)
    set_param(g, "voronoi_1", "randomness", 1)
    set_param(g, "voronoi_1", "intensity", 1)

    # stone-vs-sand mask straight from the distance field, thresholded hard.
    # voronoi_0 port0 is F1 (distance to nearest seed): LOW at cell centers,
    # HIGH toward cell edges. First try had this backwards (low->0, high->1),
    # which painted tiny sand DOTS at the centers with stone filling
    # everywhere else -- exactly inverted from "rounded stones in sand."
    # Flipped: low F1 (near center) -> mask 1 (stone), high F1 (near the
    # inter-cell network) -> mask 0 (sand).
    add_node(g, "colorize_gap", "colorize",
             {"gradient": _grad([(0.30, 1, 1, 1), (0.42, 0, 0, 0)])})
    # stone albedo: per-cell random -> pale, soft natural tones (lighter/
    # lower-contrast than s06's darker slate/brown spread -- these are
    # smaller, softer, water-worn stones, not s06's larger tumbled rocks)
    add_node(g, "colorize_stone", "colorize",
             {"gradient": _grad([
                 (0.0, 0.42, 0.40, 0.37),
                 (0.35, 0.58, 0.55, 0.50),
                 (0.65, 0.50, 0.49, 0.50),
                 (1.0, 0.60, 0.56, 0.49),
             ])})
    # sand fill: warm tan, driven by the existing perlin_0 for soft variation
    add_node(g, "colorize_sand", "colorize",
             {"gradient": _grad([(0.0, 0.62, 0.54, 0.40), (1.0, 0.70, 0.62, 0.47)])})
    add_node(g, "blend_stones", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "colorize_rgh_sand", "colorize",
             {"gradient": _grad([(0.0, 0.78, 0.78, 0.78), (1.0, 0.85, 0.85, 0.85)])})
    add_node(g, "colorize_rgh_stone", "colorize",
             {"gradient": _grad([(0.0, 0.42, 0.42, 0.42), (1.0, 0.55, 0.55, 0.55)])})
    add_node(g, "blend_rgh", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "voronoi_0", "from_port": 0, "to": "colorize_gap", "to_port": 0},
        {"from": "voronoi_0", "from_port": 2, "to": "colorize_stone", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "colorize_sand", "to_port": 0},
        {"from": "colorize_stone", "from_port": 0, "to": "blend_stones", "to_port": 0},
        {"from": "colorize_sand", "from_port": 0, "to": "blend_stones", "to_port": 1},
        {"from": "colorize_gap", "from_port": 0, "to": "blend_stones", "to_port": 2},
        {"from": "perlin_0", "from_port": 0, "to": "colorize_rgh_stone", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "colorize_rgh_sand", "to_port": 0},
        {"from": "colorize_rgh_stone", "from_port": 0, "to": "blend_rgh", "to_port": 0},
        {"from": "colorize_rgh_sand", "from_port": 0, "to": "blend_rgh", "to_port": 1},
        {"from": "colorize_gap", "from_port": 0, "to": "blend_rgh", "to_port": 2},
    ]
    rewire(g, "Material", 0, "blend_stones", 0)
    rewire(g, "Material", 2, "blend_rgh", 0)
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])   # non-metal
    set_param(g, "warp_0", "amount", 0.12)
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.35)   # gentler bulge than s06's 0.6
    return save_variant(g, _LABEL, "s04_scattered_river_stones", 1)


def build_s05_hex_stone_tile() -> str:
    """Natural-toned hex stone tile / mosaic paving: reuse beehive's hex
    relief chain, same lever as man01_metal_grating/man02_ceramic_hex_tiles,
    keeping the DEFAULT per-cell-random blend (man02 rewired it away for
    uniform ceramic tiles -- here the per-cell randomness is what makes each
    tile read as a naturally different stone, not a repeating single color).
    A multi-stop earth gradient spread across the mask's value range gives
    tiles a genuine tone spread (cool gray, warm tan, dark gray); the low
    end stays a thin dark band for recessed mortar/gaps.

    NOT true irregular cobblestone -- honest miss, worth flagging rather than
    overselling. First attempt at the default hex scale (sx=20/sy=12) plus a
    wide dark-mortar band read as a busy dark digital-camo grid, not stone;
    fixed the proportions by shrinking sx/sy to 7/5 (big cobbles, not a fine
    grid) and narrowing the dark band to a thin edge (0.0-0.08, matching
    man01's actual ratio) so stone dominates coverage. That fix makes a
    good-looking natural-toned stone MOSAIC, but beehive's hex grid is
    perfectly regular -- real cobblestone/crazy-paving has irregular,
    variously-sized stones, which this doesn't have. A voronoi-plate
    approach (like dry_earth's cracked-plate network, recolored to stone
    tones with per-plate variation) would likely get genuine irregularity;
    untried here, open item for whoever wants true cobblestone next."""
    g = load_example("beehive")
    set_param(g, "beehive_2", "sx", 7)    # big rounded cobbles, not a fine grid
    set_param(g, "beehive_2", "sy", 5)
    set_param(g, "uniform_greyscale", "color", 0.0)   # non-metal
    set_gradient(g, "colorize_5", [                    # albedo: mortar -> varied stone
        (0.0, 0.15, 0.14, 0.13),    # recessed mortar/gap, dark, thin band only
        (0.08, 0.16, 0.15, 0.14),
        (0.14, 0.45, 0.42, 0.38),   # transition into stone
        (0.40, 0.56, 0.50, 0.42),   # warm tan stone
        (0.65, 0.43, 0.43, 0.45),   # cool gray stone
        (0.88, 0.50, 0.46, 0.39),   # another warm variant near the top
    ])
    set_gradient(g, "colorize_4", [                    # roughness: rough mortar, rough-ish stone
        (0.08, 0.85, 0.85, 0.85),
        (0.14, 0.58, 0.58, 0.58),
        (0.88, 0.64, 0.64, 0.64),
    ])
    # Grayson's feedback on the first pass: reads flat, needs another level of
    # detail. Each hex face was a single uniform color -- add a fine perlin
    # speckle multiplied over the albedo/roughness so individual stones show
    # real surface grain, not just a flat per-tile tone. Multiply blend with
    # NO mask connected (the "a" port's own unconnected default is 1.0, a
    # uniform full-strength effect) -- no threshold involved, so none of the
    # w03 mask-edge speckle risk applies here.
    add_node(g, "perlin_grain", "perlin", {"scale_x": 48, "scale_y": 48, "iterations": 5})
    add_node(g, "colorize_grain_alb", "colorize",
             {"gradient": _grad([(0.0, 0.80, 0.80, 0.80), (1.0, 1.0, 1.0, 1.0)])})
    add_node(g, "colorize_grain_rgh", "colorize",
             {"gradient": _grad([(0.0, 0.85, 0.85, 0.85), (1.0, 1.05, 1.05, 1.05)])})
    add_node(g, "blend_grain_alb", "blend", {"blend_type": 2, "amount": 1})  # Multiply
    add_node(g, "blend_grain_rgh", "blend", {"blend_type": 2, "amount": 1})
    g["connections"] += [
        {"from": "perlin_grain", "from_port": 0, "to": "colorize_grain_alb", "to_port": 0},
        {"from": "perlin_grain", "from_port": 0, "to": "colorize_grain_rgh", "to_port": 0},
        {"from": "colorize_5", "from_port": 0, "to": "blend_grain_alb", "to_port": 0},
        {"from": "colorize_grain_alb", "from_port": 0, "to": "blend_grain_alb", "to_port": 1},
        {"from": "colorize_4", "from_port": 0, "to": "blend_grain_rgh", "to_port": 0},
        {"from": "colorize_grain_rgh", "from_port": 0, "to": "blend_grain_rgh", "to_port": 1},
    ]
    rewire(g, "Material", 0, "blend_grain_alb", 0)   # albedo <- grain-multiplied stone
    rewire(g, "Material", 2, "blend_grain_rgh", 0)   # roughness <- grain-multiplied
    return save_variant(g, _LABEL, "s05_hex_stone_tile", 1)


def build_s06_river_pebbles() -> str:
    """Natural river stones / pebbles: rounded, tightly-packed smooth stones
    in varied natural tones, the organic counterpart to s05's regular hex
    tile. CLONE `rock` (same donor as s02 granite -- it already has a voronoi
    albedo chain AND a working voronoi->warp->normal_map relief chain), but
    tune for BIG rounded cells instead of granite's fine flecks:

    - voronoi_0/voronoi_1 scale dropped to ~7 (big pebble-sized cells, vs
      granite's 40+ fine flecks). A voronoi distance field bulges high at
      cell centers and drops to a crevice at borders, so at this scale each
      cell reads as one rounded stone with a dark gap around it.
    - albedo fed from voronoi_0 PORT 2 (rand3 per-cell random) through a
      multi-tone natural-stone gradient, so each pebble is a genuinely
      different tone (gray, tan, brown, slate) rather than one flat color --
      the same per-cell-random lever s02 granite v2 and s05 hex tile use.
    - normal strength raised (param1 ~0.6, param4=0 for the directly-fed
      analytic source) so the pebbles visibly bulge, not the near-flat
      relief granite/concrete want.
    - a fine perlin grain multiplied over albedo for per-stone surface
      texture, same detail lever added to s05 after Grayson's "needs another
      level of detail" note -- a smooth pebble still has fine mineral grain.
    Non-metal, moderate roughness (wet-looking river stone is a touch
    glossier than dry fieldstone, kept mid-range)."""
    g = load_example("rock")
    # big pebble-sized cells on both the albedo and the normal voronoi
    set_param(g, "voronoi_0", "scale_x", 7)
    set_param(g, "voronoi_0", "scale_y", 7)
    set_param(g, "voronoi_0", "randomness", 1)
    set_param(g, "voronoi_1", "scale_x", 7)
    set_param(g, "voronoi_1", "scale_y", 7)
    set_param(g, "voronoi_1", "randomness", 1)
    set_param(g, "voronoi_1", "intensity", 1)
    # albedo <- per-cell random -> varied natural stone tones per pebble
    rewire(g, "colorize_0", 0, "voronoi_0", 2)
    set_gradient(g, "colorize_0", [
        (0.0, 0.18, 0.17, 0.16),    # dark slate pebble
        (0.28, 0.34, 0.30, 0.26),   # brown-gray
        (0.52, 0.52, 0.48, 0.42),   # warm tan
        (0.74, 0.44, 0.45, 0.47),   # cool blue-gray
        (1.0, 0.30, 0.27, 0.24),    # dark brown
    ])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])   # non-metal
    set_gradient(g, "colorize_2", [            # mid roughness, faint wet sheen
        (0.0, 0.42, 0.42, 0.42), (1.0, 0.60, 0.60, 0.60)])
    # pronounced rounded pebble relief (directly-fed analytic -> param4=0)
    set_param(g, "warp_0", "amount", 0.2)
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.6)
    # fine per-stone surface grain, multiplied over the albedo (no mask, so
    # the unconnected opacity port defaults to a uniform 1.0 -- same detail
    # lever as s05, no threshold/speckle risk)
    add_node(g, "perlin_grain", "perlin", {"scale_x": 40, "scale_y": 40, "iterations": 5})
    add_node(g, "colorize_grain", "colorize",
             {"gradient": _grad([(0.0, 0.82, 0.82, 0.82), (1.0, 1.0, 1.0, 1.0)])})
    add_node(g, "blend_grain", "blend", {"blend_type": 2, "amount": 1})   # Multiply
    g["connections"] += [
        {"from": "perlin_grain", "from_port": 0, "to": "colorize_grain", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "blend_grain", "to_port": 0},
        {"from": "colorize_grain", "from_port": 0, "to": "blend_grain", "to_port": 1},
    ]
    rewire(g, "Material", 0, "blend_grain", 0)   # albedo <- grain-multiplied pebbles
    return save_variant(g, _LABEL, "s06_river_pebbles", 1)


BUILDERS = {
    "s04_scattered_river_stones": build_s04_scattered_river_stones,
    "s05_hex_stone_tile": build_s05_hex_stone_tile,
    "s06_river_pebbles": build_s06_river_pebbles,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
