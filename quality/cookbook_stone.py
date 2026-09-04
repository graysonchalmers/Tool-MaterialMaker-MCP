"""Cookbook growth: stone/masonry-category authoring recipes beyond the
frozen 15-case Phase 3 test set (`s01_red_brick_wall`/`s02_gray_granite`/
`s03_cracked_concrete` are already frozen there -- see quality/test_set.json's
freeze note; this is additive, not an edit to those cases). Informal: 1
variant per material, no scorecard gate. Reuses author_helpers.py's graph-surgery
helpers; outputs land under quality/authored/cookbook-stone/<case>/v1.ptex,
same layout convention as the Phase 3 iterations.

Run: python quality/cookbook_stone.py
Then quality/render_cookbook.py renders each variant for inspection.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import load_example, set_gradient, set_param, save_variant, add_node, rewire, _grad

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


def build_s07_cobblestone() -> str:
    """True irregular cobblestone -- the voronoi-plate approach the
    s05_hex_stone_tile docstring flagged as untried (backlog C). CLONE
    `dry_earth`, whose voronoi crack-network gives genuinely irregular,
    variously-sized plates with recessed cracks between them -- exactly the
    irregularity beehive's perfectly-regular hex grid could never produce.
    dry_earth is already the proven donor for s03 cracked concrete (a flat
    recolor); here we go further and give each plate its own stone tone so the
    plates read as separate cobbles, not one cracked slab.

    Levers:
    - voronoi_0 scale 4 -> 6: dry_earth's default plates are paving-slab huge;
      6 makes cobble-sized stones (still irregular, the whole point).
    - per-cobble tone: feed voronoi_0 PORT 2 (rand3, per-cell random -- the
      same lever s02 granite v2 / s05 / s06 use) into a multi-tone stone
      gradient, then REWIRE it in as blend_0's base (port 1) in place of the
      flat perlin earth. Each plate now gets a different gray/tan/brown/slate
      tone.
    - the existing warped-crack Multiply overlay (blend_0 port 0, unchanged)
      still darkens the inter-plate cracks -- now reading as recessed mortar
      shadow between cobbles. blend_0 amount 0.4 -> 0.6 for deeper, more
      clearly recessed mortar lines than dry_earth's subtle staining.
    - fine perlin grain multiplied over the albedo (the s05/s06 detail lever,
      no mask so the unconnected opacity port is a uniform 1.0) so each cobble
      shows real surface grain, not a flat per-plate tone.
    Relief (dry_earth's crack->height->normal chain) is kept as-is: worn
    cobbles have flat-ish tops and deep mortar gaps, which is what this chain
    already produces. Non-metal: dry_earth has no metallic input connected."""
    g = load_example("dry_earth")
    set_param(g, "voronoi_0", "scale_x", 6)    # cobble-sized irregular plates
    set_param(g, "voronoi_0", "scale_y", 6)
    # per-cobble tone from the per-cell random (port 2) -> varied stone colors.
    # A high-contrast test gradient proved port 2 gives each plate a distinct
    # flat value; the first pass looked muted only because this spread was too
    # narrow. Widened across value AND hue (charcoal -> limestone -> sandstone
    # -> granite -> brown) so cobbles read as genuinely different stones.
    add_node(g, "colorize_cobble", "colorize",
             {"gradient": _grad([
                 (0.0,  0.20, 0.19, 0.18),   # dark charcoal slate
                 (0.22, 0.42, 0.39, 0.35),   # mid warm gray
                 (0.44, 0.62, 0.60, 0.55),   # light limestone
                 (0.62, 0.55, 0.46, 0.35),   # warm tan sandstone
                 (0.80, 0.38, 0.40, 0.44),   # cool blue-gray granite
                 (1.0,  0.34, 0.28, 0.23),   # dark brown
             ])})
    g["connections"].append(
        {"from": "voronoi_0", "from_port": 2, "to": "colorize_cobble", "to_port": 0})
    # swap the flat earth base for per-cobble stone; keep the crack overlay
    rewire(g, "blend_0", 1, "colorize_cobble", 0)
    set_param(g, "blend_0", "amount", 0.6)     # deeper recessed mortar than dry_earth's 0.4
    # dry_earth's warp (0.4) is tuned for chaotic mud cracks: at this strength it
    # smears the crack shadows into broad gray washes ACROSS plate interiors (a
    # test render isolated the haze to this chain, not the tone gradient). Drop
    # it hard so mortar stays a thin, clean line between cobbles with just a
    # slight organic wobble, not a haze.
    set_param(g, "warp_0", "amount", 0.12)
    # fine per-stone surface grain, multiplied over albedo (s05/s06 lever)
    add_node(g, "perlin_grain", "perlin", {"scale_x": 40, "scale_y": 40, "iterations": 5})
    add_node(g, "colorize_grain", "colorize",
             {"gradient": _grad([(0.0, 0.82, 0.82, 0.82), (1.0, 1.0, 1.0, 1.0)])})
    add_node(g, "blend_grain", "blend", {"blend_type": 2, "amount": 1})   # Multiply
    g["connections"] += [
        {"from": "perlin_grain", "from_port": 0, "to": "colorize_grain", "to_port": 0},
        {"from": "blend_0", "from_port": 0, "to": "blend_grain", "to_port": 0},
        {"from": "colorize_grain", "from_port": 0, "to": "blend_grain", "to_port": 1},
    ]
    rewire(g, "Material", 0, "blend_grain", 0)   # albedo <- grain-multiplied cobbles
    return save_variant(g, _LABEL, "s07_cobblestone", 1)


def build_s08_dry_stone_wall() -> str:
    """Dry-stone / fieldstone wall: irregular stones tightly packed with thin
    dark dry-stack gaps (no mortar), weathered gray. Same voronoi-plate donor
    as s07 cobblestone, deliberately retuned to read as a different material,
    not a recolor:
    - scale 6 -> 8: smaller, denser, more numerous stones than the paving cobbles.
    - warp stays at s07's haze-free 0.12: a first pass at 0.20 (chasing more
      angular edges) just brought back the broad crack-smear haze without
      actually sharpening corners -- voronoi cells are already polygonal, so the
      angular fieldstone read comes from the cell shape, not the warp.
    - palette shifts warm tan -> cool weathered GRAY with subtle mossy and brown
      accents (the loudest read that these aren't the same stones as s07). The
      green is kept restrained -- pushed further it tips into a camo-grid look
      (the same trap s05 hit).
    - gaps stay thin and dark (blend_0 Multiply 0.6) -- a dry stack shows a
      tight recessed shadow line, not s07's wider mortar joint feel.
    Keeps s07's strong per-stone relief (chunky individual stones is exactly the
    fieldstone look) and the fine perlin surface grain. Honest limit: pure
    voronoi has no horizontal coursing, so this reads as random rubble/fieldstone
    packing, not neatly coursed drystone -- flagged rather than oversold."""
    g = load_example("dry_earth")
    set_param(g, "voronoi_0", "scale_x", 8)    # smaller, denser stones than cobbles
    set_param(g, "voronoi_0", "scale_y", 8)
    add_node(g, "colorize_cobble", "colorize",
             {"gradient": _grad([
                 (0.0,  0.22, 0.23, 0.22),   # dark wet gray
                 (0.25, 0.40, 0.41, 0.40),   # mid weathered gray
                 (0.45, 0.58, 0.58, 0.56),   # light gray
                 (0.62, 0.50, 0.47, 0.40),   # tan-gray
                 (0.80, 0.43, 0.45, 0.40),   # restrained mossy gray (not camo green)
                 (1.0,  0.30, 0.29, 0.26),   # dark brown-gray
             ])})
    g["connections"].append(
        {"from": "voronoi_0", "from_port": 2, "to": "colorize_cobble", "to_port": 0})
    rewire(g, "blend_0", 1, "colorize_cobble", 0)
    set_param(g, "blend_0", "amount", 0.6)     # thin, dark dry-stack gap shadow
    set_param(g, "warp_0", "amount", 0.12)     # haze-free (0.20 smeared, no angularity gain)
    add_node(g, "perlin_grain", "perlin", {"scale_x": 48, "scale_y": 48, "iterations": 5})
    add_node(g, "colorize_grain", "colorize",
             {"gradient": _grad([(0.0, 0.82, 0.82, 0.82), (1.0, 1.0, 1.0, 1.0)])})
    add_node(g, "blend_grain", "blend", {"blend_type": 2, "amount": 1})   # Multiply
    g["connections"] += [
        {"from": "perlin_grain", "from_port": 0, "to": "colorize_grain", "to_port": 0},
        {"from": "blend_0", "from_port": 0, "to": "blend_grain", "to_port": 0},
        {"from": "colorize_grain", "from_port": 0, "to": "blend_grain", "to_port": 1},
    ]
    rewire(g, "Material", 0, "blend_grain", 0)
    return save_variant(g, _LABEL, "s08_dry_stone_wall", 1)


def build_s09_ashlar_wall() -> str:
    """Ashlar / castle block wall: neatly cut rectangular stone blocks laid in
    courses with fine recessed joints -- the REGULAR, quarried counterpart to
    s08's random fieldstone. This is where the masonry set leaves the
    voronoi-plate cluster: a `Bricks`-node donor gives true coursed rectangular
    blocks that voronoi never can. CLONE `stone_wall` (already a Bricks-driven
    stone wall with per-brick relief + a per-brick random tone channel on
    Bricks port 1, the brick analogue of voronoi port 2), and retune:
    - Bricks columns 3x6 -> 4x4: fewer, larger, squarer ashlar blocks instead of
      stone_wall's tall thin bricks. Keep row_offset 0.5 (broken/coursed joints,
      the classic ashlar bond) and the 0.15 bevel (chamfered cut-stone edges).
    - mortar joint kept fine (0.06): dressed ashlar has tight joints, not the
      fat mortar of rough brickwork.
    - recolor the per-block tone ramp (colorize_1, fed by Bricks port 1) toward
      dressed limestone/sandstone/gray and TEMPER stone_wall's rustic orange
      block so the wall reads as cut castle stone, not weathered rubble -- still
      per-block varied so no two blocks match.
    Relief, mortar mask and non-metal setup are stone_wall's, unchanged."""
    g = load_example("stone_wall")
    set_param(g, "Bricks", "columns", 4)    # squarer, larger ashlar blocks
    set_param(g, "Bricks", "rows", 4)
    set_param(g, "Bricks", "mortar", 0.06)  # fine dressed joint
    set_param(g, "Bricks", "bevel", 0.18)   # chamfered cut-stone edge
    # per-block dressed-stone tones (Bricks port 1 random via colorize_1); the
    # stops still alternate light/dark so adjacent blocks contrast, but the warm
    # orange block is pulled back to a tan sandstone.
    set_gradient(g, "colorize_1", [
        (0.0,  0.60, 0.59, 0.56),   # light limestone
        (0.15, 0.30, 0.29, 0.27),   # dark joint-shadowed block
        (0.35, 0.68, 0.63, 0.55),   # pale sandstone
        (0.55, 0.34, 0.32, 0.29),   # dark gray block
        (0.75, 0.56, 0.53, 0.47),   # mid warm gray
        (1.0,  0.50, 0.43, 0.34),   # tan sandstone (was rustic orange)
    ])
    return save_variant(g, _LABEL, "s09_ashlar_wall", 1)


def build_s10_flagstone() -> str:
    """Flagstone / slate paving: large flat irregular slabs with tight joints,
    cool slate tones. Same dry_earth voronoi-plate donor as s07, tuned in the
    OPPOSITE direction on every axis so it reads as flat quarried paving, not
    rounded cobbles:
    - scale 6 -> 4 (dry_earth's own default): big slabs, a few large plates
      across the frame instead of many small cobbles.
    - normal_map strength 0.99 -> 0.5: FLAT slab tops. Cobbles bulge; flagstones
      are sawn flat, so the relief should live almost entirely in the recessed
      joints, not a dome across each slab.
    - warp kept at the haze-free 0.12: clean joint lines with a slight natural
      wobble.
    - palette shifts to cool blue-grays / green-gray slate (vs s07's warm tans),
      low-contrast because slate slabs are fairly uniform -- per-slab variation
      is a subtle tonal shift, not the strong hue spread the cobbles wanted."""
    g = load_example("dry_earth")
    set_param(g, "voronoi_0", "scale_x", 4)    # big flat slabs
    set_param(g, "voronoi_0", "scale_y", 4)
    add_node(g, "colorize_cobble", "colorize",
             {"gradient": _grad([
                 (0.0,  0.18, 0.20, 0.23),   # dark charcoal-blue slate
                 (0.30, 0.30, 0.34, 0.38),   # slate blue-gray
                 (0.55, 0.42, 0.44, 0.46),   # mid gray
                 (0.78, 0.34, 0.40, 0.38),   # green-gray slate
                 (1.0,  0.48, 0.50, 0.54),   # light blue-gray
             ])})
    g["connections"].append(
        {"from": "voronoi_0", "from_port": 2, "to": "colorize_cobble", "to_port": 0})
    rewire(g, "blend_0", 1, "colorize_cobble", 0)
    set_param(g, "blend_0", "amount", 0.6)     # recessed joint shadow
    set_param(g, "warp_0", "amount", 0.12)     # clean joints, no haze
    set_param(g, "normal_map_0", "param1", 0.5)  # FLAT slab tops (vs cobbles' 0.99 bulge)
    add_node(g, "perlin_grain", "perlin", {"scale_x": 40, "scale_y": 40, "iterations": 5})
    add_node(g, "colorize_grain", "colorize",
             {"gradient": _grad([(0.0, 0.85, 0.85, 0.85), (1.0, 1.0, 1.0, 1.0)])})
    add_node(g, "blend_grain", "blend", {"blend_type": 2, "amount": 1})   # Multiply
    g["connections"] += [
        {"from": "perlin_grain", "from_port": 0, "to": "colorize_grain", "to_port": 0},
        {"from": "blend_0", "from_port": 0, "to": "blend_grain", "to_port": 0},
        {"from": "colorize_grain", "from_port": 0, "to": "blend_grain", "to_port": 1},
    ]
    rewire(g, "Material", 0, "blend_grain", 0)
    return save_variant(g, _LABEL, "s10_flagstone", 1)


def build_s11_marble() -> str:
    """Polished marble: a cream base with soft flowing gray veins, glossy and
    smooth -- the one masonry material that leaves the coursed/paved family
    entirely. Same dry_earth donor, but used for its VEIN STRUCTURE, not its
    plates: the warped crack network, pushed hard, reads as marble veining
    rather than mortar joints. Every lever inverts the paving recipes:
    - voronoi scale 3: few, large cells -> a few big sweeping veins, not a dense
      joint grid.
    - warp 0.12 -> 0.5: HIGH. On the paving mats this smear was haze to kill;
      on marble the flow IS the look -- soft cloudy veins wandering across the slab.
    - NO per-cell tone (no colorize_cobble): marble is one uniform stone, not a
      mosaic of differently-coloured pieces. Base is a near-white cream
      (colorize_0), veins are a soft gray from the crack Multiply eased to 0.5.
    - metallic zeroed (colorize_3 -> all black) and roughness dropped to 0.15 on
      the Material node: polished stone is non-metal but glossy, the one low-
      roughness material in the set.
    - normal strength 0.99 -> 0.1: marble is smooth; veins are a whisper of
      relief, not recessed joints.
    Honest scope: this is soft Carrara-style veining, not the angular fragments
    of breccia marble (which the un-warped voronoi cells would actually suit)."""
    g = load_example("dry_earth")
    set_param(g, "voronoi_0", "scale_x", 3)    # few large sweeping veins
    set_param(g, "voronoi_0", "scale_y", 3)
    set_param(g, "warp_0", "amount", 0.5)      # HIGH: flowing marble veins (haze is the look here)
    # cream base (no per-cell tone) with a whisper of warm variation
    set_gradient(g, "colorize_0", [
        (0.0, 0.86, 0.85, 0.82),
        (1.0, 0.93, 0.93, 0.90),
    ])
    set_param(g, "blend_0", "amount", 0.5)     # soft gray veins, not black cracks
    set_gradient(g, "colorize_3", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])  # metallic 0 (non-metal)
    set_param(g, "Material", "roughness", 0.15)  # polished (roughness port is unconnected)
    set_param(g, "normal_map_0", "param1", 0.1)  # smooth: veins barely raised
    return save_variant(g, _LABEL, "s11_marble", 1)


BUILDERS = {
    "s04_scattered_river_stones": build_s04_scattered_river_stones,
    "s05_hex_stone_tile": build_s05_hex_stone_tile,
    "s06_river_pebbles": build_s06_river_pebbles,
    "s07_cobblestone": build_s07_cobblestone,
    "s08_dry_stone_wall": build_s08_dry_stone_wall,
    "s09_ashlar_wall": build_s09_ashlar_wall,
    "s10_flagstone": build_s10_flagstone,
    "s11_marble": build_s11_marble,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
