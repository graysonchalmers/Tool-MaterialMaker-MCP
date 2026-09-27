"""Cookbook growth: stone/masonry-category authoring recipes beyond the
frozen 15-case Phase 3 test set (`s01_red_brick_wall`/`s02_gray_granite`/
`s03_cracked_concrete` are already frozen there -- see docs/evidence/phase3/test_set.json's
freeze note; this is additive, not an edit to those cases). Informal: 1
variant per material, no scorecard gate. Reuses author_helpers.py's graph-surgery
helpers; outputs land under quality/authored/cookbook-stone/<case>/v1.ptex,
same layout convention as the Phase 3 iterations.

Run: python -m quality.cookbook_stone
Then `python -m quality.render_cookbook` renders each variant for inspection.
"""
import math
import sys

from quality.author_helpers import (load_example, set_gradient, set_param, save_variant,
                             add_node, rewire, drop_conn, retype, node, _grad,
                             group_into_subgraph, take_variant, rename_nodes,
                             place, tidy_ports, link_also)
from quality import author  # shared builder base; regression guard is promote_cookbook --check

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-stone"

# Shared donor mapping for the dry_earth-voronoi-plate family (s07 cobblestone,
# s08 dry stone wall, s10 flagstone, s11 marble). voronoi_0 is the crack-network
# generator whose port1 fan-out (colorize_1 -> warp_0 -> blend_0) draws the
# plate/joint pattern; the relief chain (perlin_1/colorize_3/perlin_0/
# colorize_0/colorize_4/blend_1/colorize/normal_map_0) is dry_earth's original
# height/roughness path, folded together per _group_paving_stone's docstring.
# colorize_0 is orphaned in s07/s08/s10 once blend_0's port1 is rewired onto
# colorize_cobble (see that docstring) -- s11 marble never rewires it, so it
# overrides colorize_0/perlin_0/colorize_3 below (build_s11_marble docstring).
_DRY_EARTH_NAMES = {
    "voronoi_0": "PlateCells",
    "colorize_1": "PlateEdges",
    "warp_0": "JointWarp",
    "blend_0": "JointComposite",
    "perlin_1": "ReliefNoiseCoarse",
    "colorize_3": "ReliefContrast",
    "perlin_0": "ReliefNoiseFine",
    "colorize_0": "ReliefFineUnused",
    "colorize_4": "ReliefRamp",
    "blend_1": "ReliefComposite",
    "colorize": "ReliefHeight",
    "normal_map_0": "StoneNormal",
}


def _group_paving_stone(g: dict, catalog: dict, *, relief_label: str = None) -> None:
    """Shared grouping for the dry_earth-voronoi-plate paving stones
    (s07_cobblestone; s08_dry_stone_wall and s10_flagstone, since retired into
    s07's presets), which all clone
    `dry_earth` and add the same `colorize_cobble` (per-plate tone,
    replacing `colorize_0` as `blend_0`'s port1/background) plus a
    `perlin_grain` surface-detail overlay (`blend_grain`, Multiply, over the
    final albedo).

    `warp_0` is kept in the Stone Color group with `blend_0`, the thing it
    most directly and visibly feeds (the crack/joint pattern that reads as
    mortar). Its `amount` is never exposed as a friendly parameter here --
    per the category-wide caution, this donor's `warp_0.amount` is the
    single most render-sensitive knob in the whole category (haze vs. clean
    joints on these paving mats, or the flowing-vein look on s11_marble), so
    it stays a build-time tuning constant baked into the recipe, not
    something opened up for casual retuning.

    dry_earth's original `colorize_0` (fed by `perlin_0`) is orphaned once
    `blend_0`'s port1 is rewired onto `colorize_cobble` -- still present in
    the graph with no consumer, so it is folded into the relief chain here
    since it shares `perlin_0` with `blend_1`. That relief/roughness chain
    (`perlin_1`, `colorize_3`, `perlin_0`, `colorize_0`, `colorize_4`,
    `blend_1`, `colorize`, `normal_map_0`) carries no builder-set parameter
    of its own unless `relief_label` is given (only s10 tunes
    `normal_map_0.param1`) -- for s07/s08 it is folded into the Stone Color
    group instead of standing alone with zero exposed parameters, per the
    standing rule that every group needs at least one."""
    stone_members = ["voronoi_0", "colorize_1", "colorize_cobble", "warp_0", "blend_0"]
    relief_members = ["perlin_1", "colorize_3", "perlin_0", "colorize_0",
                       "colorize_4", "blend_1", "colorize", "normal_map_0"]
    stone_exposed = [
        ("voronoi_0", "scale_x", "param0", "Stone size"),
        ("colorize_cobble", "gradient", "param1", "Stone color"),
        ("blend_0", "amount", "param2", "Joint depth"),
    ]
    if relief_label:
        group_into_subgraph(g, stone_members, "stone_color", "Stone Color",
                             stone_exposed, catalog)
        group_into_subgraph(g, relief_members, "relief", "Relief",
                             [("normal_map_0", "param1", "param0", relief_label)],
                             catalog)
    else:
        group_into_subgraph(g, stone_members + relief_members,
                             "stone_and_relief", "Stone & Relief",
                             stone_exposed, catalog)
    group_into_subgraph(g, ["perlin_grain", "colorize_grain", "blend_grain"],
                         "surface_grain", "Surface Grain",
                         [("perlin_grain", "scale_x", "param0", "Grain scale"),
                          ("colorize_grain", "gradient", "param1", "Grain contrast")],
                         catalog)



def build_s05_hex_stone_tile(catalog: dict) -> str:
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

    # Subgraph grouping. blend/blend_grain_alb/blend_grain_rgh carry no
    # port2 mask (unconnected -> default 1.0), so their "amount"s are plain
    # uniform mixes -- blend/blend_grain_* stay at their donor default
    # amount (untouched by this builder), no polarity trap to trace.
    # uniform_greyscale (metallic=0, explicit) is left top-level, same as
    # other categories' untouched single-scalar metallic nodes.
    group_into_subgraph(g, ["beehive_2", "colorize_2", "colorize", "blend",
                             "colorize_3", "normal_map"],
                         "hex_pattern", "Hex Pattern",
                         [("beehive_2", "sx", "param0", "Tile width"),
                          ("beehive_2", "sy", "param1", "Tile height")],
                         catalog)
    group_into_subgraph(g, ["colorize_5", "colorize_4"],
                         "stone_finish", "Stone Color & Roughness",
                         [("colorize_5", "gradient", "param0", "Stone color"),
                          ("colorize_4", "gradient", "param1", "Roughness")],
                         catalog)
    group_into_subgraph(g, ["perlin_grain", "colorize_grain_alb", "colorize_grain_rgh",
                             "blend_grain_alb", "blend_grain_rgh"],
                         "surface_grain", "Surface Grain",
                         [("perlin_grain", "scale_x", "param0", "Grain scale"),
                          ("perlin_grain", "iterations", "param1", "Grain detail")],
                         catalog)
    rename_nodes(g, {
        "beehive_2": "HexLayout",
        "colorize_2": "HexFaceMask",
        "colorize": "HexEdgeMask",
        "blend": "HexFieldComposite",
        "colorize_3": "HexAO",
        "normal_map": "HexNormal",
        "colorize_5": "StoneColor",
        "colorize_4": "StoneRoughness",
        "uniform_greyscale": "NonMetallic",
        "perlin_grain": "GrainNoise",
        "colorize_grain_alb": "GrainContrastAlbedo",
        "colorize_grain_rgh": "GrainContrastRoughness",
        "blend_grain_alb": "AlbedoComposite",
        "blend_grain_rgh": "RoughnessComposite",
    })
    return save_variant(g, _LABEL, "s05_hex_stone_tile", 1)



def build_s07_cobblestone(catalog: dict) -> str:
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
    already produces. (Correction: dry_earth DOES wire metallic_tex, from
    colorize_3 on perlin_1, 0-0.52; kept exactly as shipped.)

    PAVED-STONE HOST (2026-09-27): absorbs s08_dry_stone_wall and
    s10_flagstone. Those two are this same graph with different
    parameters and no node of their own, so nothing is carried in; the host
    exposes the parameters they tuned (Stone size now drives scale_x AND
    scale_y, Grain scale likewise, Relief strength = StoneNormal.param1),
    and each preset renders its original exactly (0 px, 2048 maps). Every
    new layer defaults to a no-op, so the default is today's s07 exactly
    (0 px on albedo/normal/orm/heightmap):
    - Joint width (Stone Layout): border distance / max(2 x width, 0.1)
      before PlateEdges, upstream of JointWarp, so joint shade and groove
      move together. 0.5 = shipped width.
    - Tones follow joints (Stone Layout): ToneWarp, JointWarp's twin on the
      cell random, mixed in by math; 1 puts every tone edge on a joint.
    - Top flatness (Stone Surface): pulls the fine relief noise toward 0.5,
      so tops go flat while joints keep full depth.
    - Mortar (Mortar fill, Mortar color): relief reads max(w, fill) and one
      mask smoothstep(clamp((fill - w) x 8)) paints the mortar colour where
      the relief is mortar; the colour varies with the same surface noise.
    Every height op is a math node (no new f->rgba->f round trip). Presets
    are on the card (cookbook/stone/s07_cobblestone.md, "Feature layers")."""
    g = load_example("dry_earth")
    # Direct normal path (2026-09-27): the donor's buffered param4=1 races to a
    # flat normal headless; param4=0 at the same param1 matches within 0.37/255.
    set_param(g, "normal_map_0", "param4", 0)
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

    # --- Host refactor ---
    # dry_earth's flat-earth colorize_0 has had no consumer since blend_0's
    # background was rewired onto colorize_cobble; drop it.
    g["connections"] = [c for c in g["connections"] if c["to"] != "colorize_0"]
    g["nodes"] = [n for n in g["nodes"] if n["name"] != "colorize_0"]

    # --- Joint width (Stone Layout) ---
    # PlateEdges ramps 0 -> 1 over 0.064 of the voronoi border distance, so
    # the joint is a fixed fraction of the cell: bigger stones, wider joints.
    # Dividing the border distance by (2 x Joint width) before PlateEdges
    # scales that band on its own. Upstream of JointWarp, so the dark joint
    # in the albedo and the groove in the relief (both read the warped band)
    # move together. Joint width 0.5 divides by exactly 1.0; the 0.1 floor
    # keeps a slider at 0 from dividing by zero.
    add_node(g, "JointWidth", "math", {"op": 2, "default_in1": 0.5, "default_in2": 2})  # A*B
    add_node(g, "JointWidthFloor", "math", {"op": 14, "default_in2": 0.1})              # max(A, B)
    add_node(g, "JointScale", "math", {"op": 3})                                        # A/B
    g["connections"] += [
        {"from": "JointWidth", "from_port": 0, "to": "JointWidthFloor", "to_port": 0},
        {"from": "voronoi_0", "from_port": 1, "to": "JointScale", "to_port": 0},
        {"from": "JointWidthFloor", "from_port": 0, "to": "JointScale", "to_port": 1},
    ]
    rewire(g, "colorize_1", 0, "JointScale", 0)

    # --- Tone registration (Stone Layout) ---
    # JointWarp displaces the joints but StoneColor reads the UNwarped cell
    # random, so some tone boundaries sit inside a stone instead of on a
    # joint (all three dry_earth pavings ship this; thin joints expose it).
    # ToneWarp is JointWarp's twin (same params, same JointWarpNoise) on the
    # cell random, so its cell edges land on the warped joints. Math nodes
    # mix it in: random + (warped - random) x amount, which is the unwarped
    # random exactly at 0.
    add_node(g, "ToneWarp", "warp", dict(node(g, "warp_0")["parameters"]))
    add_node(g, "ToneDelta", "math", {"op": 1})                          # warped - random
    add_node(g, "ToneShift", "math", {"op": 2, "default_in2": 0})        # delta x amount
    add_node(g, "StoneTone", "math", {"op": 0})                          # random + shift
    g["connections"] += [
        {"from": "voronoi_0", "from_port": 2, "to": "ToneWarp", "to_port": 0},
        {"from": "perlin_1", "from_port": 0, "to": "ToneWarp", "to_port": 1},
        {"from": "ToneWarp", "from_port": 0, "to": "ToneDelta", "to_port": 0},
        {"from": "voronoi_0", "from_port": 2, "to": "ToneDelta", "to_port": 1},
        {"from": "ToneDelta", "from_port": 0, "to": "ToneShift", "to_port": 0},
        {"from": "voronoi_0", "from_port": 2, "to": "StoneTone", "to_port": 0},
        {"from": "ToneShift", "from_port": 0, "to": "StoneTone", "to_port": 1},
    ]
    rewire(g, "colorize_cobble", 0, "StoneTone", 0)

    # --- Top flatness (Stone Surface) ---
    # The relief is 0.5 x ReliefNoiseFine (rough 10-octave noise, everywhere)
    # plus 0.5 x the joint groove. Pulling that noise toward its mid value
    # 0.5 flattens the stone tops while the joints keep their full depth:
    # the "relief lives in the joints" s10 wanted, where s10's own lever
    # (normal strength 0.5) halved the joints too. noise + (0.5 - noise) x
    # flatness is the noise exactly at 0.
    add_node(g, "TopNoiseDelta", "math", {"op": 1, "default_in1": 0.5})  # 0.5 - noise
    add_node(g, "TopFlatten", "math", {"op": 2, "default_in2": 0})       # delta x flatness
    add_node(g, "TopNoise", "math", {"op": 0})                           # noise + that
    g["connections"] += [
        {"from": "perlin_0", "from_port": 0, "to": "TopNoiseDelta", "to_port": 1},
        {"from": "TopNoiseDelta", "from_port": 0, "to": "TopFlatten", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "TopNoise", "to_port": 0},
        {"from": "TopFlatten", "from_port": 0, "to": "TopNoise", "to_port": 1},
    ]
    rewire(g, "blend_1", 0, "TopNoise", 0)

    # --- Mortar ---
    # The joint band w (JointWarp: 0 at the joint centre, 1 on the stone)
    # is a V-groove in the relief. Mortar fills it to a flat level L
    # ("Mortar fill"): the relief reads max(w, L), so the groove floor rises
    # to L and meets the stone in a crease at w = L, and ONE mask,
    # smoothstep(clamp((L - w) x 8)), puts the mortar colour exactly where
    # the relief is mortar. Its colour varies with the surface noise that
    # textures the mortar's relief. L = 0 is a no-op: max(w, 0) = w and the
    # mask is 0 (w is never below 0). 0 = open dry-laid joints (every
    # original's look), 1 = mortar flush with the stone tops.
    add_node(g, "MortarLevel", "uniform_greyscale", {"color": 0})
    add_node(g, "MortarRelief", "math", {"op": 14})                              # max(w, L)
    add_node(g, "MortarDepth", "math", {"op": 1})                                # L - w
    add_node(g, "MortarRamp", "math", {"op": 2, "default_in2": _MORTAR_EDGE, "clamp": True})
    add_node(g, "MortarMask", "math", {"op": 20, "clamp": True})                 # smoothstep
    add_node(g, "MortarColor", "colorize", {"gradient": _grad(_MORTAR_COLOR)})
    add_node(g, "MortarColorComposite", "blend", {"blend_type": 0, "amount": 1})  # 0 = Normal
    g["connections"] += [
        {"from": "warp_0", "from_port": 0, "to": "MortarRelief", "to_port": 0},
        {"from": "MortarLevel", "from_port": 0, "to": "MortarRelief", "to_port": 1},
        {"from": "MortarLevel", "from_port": 0, "to": "MortarDepth", "to_port": 0},
        {"from": "warp_0", "from_port": 0, "to": "MortarDepth", "to_port": 1},
        {"from": "MortarDepth", "from_port": 0, "to": "MortarRamp", "to_port": 0},
        {"from": "MortarRamp", "from_port": 0, "to": "MortarMask", "to_port": 0},
        {"from": "TopNoise", "from_port": 0, "to": "MortarColor", "to_port": 0},
        # mask 1 shows port 0 (mortar), mask 0 shows port 1 (the stones)
        {"from": "MortarColor", "from_port": 0, "to": "MortarColorComposite", "to_port": 0},
        {"from": "blend_0", "from_port": 0, "to": "MortarColorComposite", "to_port": 1},
        {"from": "MortarMask", "from_port": 0, "to": "MortarColorComposite", "to_port": 2},
    ]
    rewire(g, "colorize_4", 0, "MortarRelief", 0)
    rewire(g, "blend_grain", 0, "MortarColorComposite", 0)

    # Seed-bearing noises keep the positions they have always had: voronoi_0,
    # perlin_0 and perlin_1 the dry_earth donor's own, perlin_grain (0, 0) of
    # its subgraph. Only nodes with no seed move.
    place(g, {
        # stone_layout
        "JointWidth": (-165, -330), "JointWidthFloor": (75, -330), "JointScale": (75, -130),
        "colorize_1": (300, -130), "warp_0": (530, -30),
        "ToneWarp": (75, 250), "ToneDelta": (300, 250), "ToneShift": (530, 250),
        "StoneTone": (760, 150),
        # stone_color
        "colorize_cobble": (250, -250),
        # stone_surface
        "TopNoiseDelta": (300, -450), "TopFlatten": (530, -450), "TopNoise": (760, -360),
        # mortar
        "MortarColor": (300, -150), "MortarLevel": (0, 300), "MortarRelief": (300, 100),
        "MortarDepth": (300, 350), "MortarRamp": (550, 350), "MortarMask": (800, 350),
        "MortarColorComposite": (1050, -50),
        # surface_grain
        "colorize_grain": (250, -150), "blend_grain": (500, -50)})

    group_into_subgraph(g, ["voronoi_0", "JointWidth", "JointWidthFloor", "JointScale",
                             "colorize_1", "perlin_1", "warp_0",
                             "ToneWarp", "ToneDelta", "ToneShift", "StoneTone"],
                         "stone_layout", "Stone Layout",
                         [("voronoi_0", "scale_x", "param0", "Stone size"),
                          ("JointWidth", "default_in1", "param1", "Joint width"),
                          ("ToneShift", "default_in2", "param2", "Tones follow joints")],
                         catalog)
    link_also(g, "stone_layout", "param0", "voronoi_0", "scale_y")
    tidy_ports(g, "stone_layout", [],
               [("warp_0", 0, "joints"), ("StoneTone", 0, "stone_tone"),
                ("perlin_1", 0, "warp_noise")], catalog)
    group_into_subgraph(g, ["colorize_cobble", "blend_0", "colorize_3"],
                         "stone_color", "Stone Color",
                         [("colorize_cobble", "gradient", "param0", "Stone color"),
                          ("blend_0", "amount", "param1", "Joint depth")],
                         catalog)
    tidy_ports(g, "stone_color",
               [("stone_layout", 0, "joints"), ("stone_layout", 1, "stone_tone"),
                ("stone_layout", 2, "warp_noise")],
               [("blend_0", 0, "albedo"), ("colorize_3", 0, "metallic")], catalog)
    group_into_subgraph(g, ["perlin_0", "TopNoiseDelta", "TopFlatten", "TopNoise"],
                         "stone_surface", "Stone Surface",
                         [("TopFlatten", "default_in2", "param0", "Top flatness")],
                         catalog)
    tidy_ports(g, "stone_surface", [], [("TopNoise", 0, "surface")], catalog)
    group_into_subgraph(g, ["MortarLevel", "MortarRelief", "MortarDepth", "MortarRamp",
                             "MortarMask", "MortarColor", "MortarColorComposite"],
                         "mortar", "Mortar",
                         [("MortarLevel", "color", "param0", "Mortar fill"),
                          ("MortarColor", "gradient", "param1", "Mortar color")],
                         catalog)
    tidy_ports(g, "mortar",
               [("stone_layout", 0, "joints"), ("stone_color", 0, "albedo"),
                ("stone_surface", 0, "surface")],
               [("MortarColorComposite", 0, "albedo"), ("MortarRelief", 0, "joints")], catalog)
    group_into_subgraph(g, ["colorize_4", "blend_1", "colorize", "normal_map_0"],
                         "relief", "Relief",
                         [("normal_map_0", "param1", "param0", "Relief strength")],
                         catalog)
    tidy_ports(g, "relief", [("mortar", 1, "joints"), ("stone_surface", 0, "surface")],
               [("normal_map_0", 0, "normal"), ("blend_1", 0, "depth")], catalog)
    group_into_subgraph(g, ["perlin_grain", "colorize_grain", "blend_grain"],
                         "surface_grain", "Surface Grain",
                         [("perlin_grain", "scale_x", "param0", "Grain scale"),
                          ("colorize_grain", "gradient", "param1", "Grain contrast")],
                         catalog)
    link_also(g, "surface_grain", "param0", "perlin_grain", "scale_y")
    tidy_ports(g, "surface_grain", [("mortar", 0, "albedo")],
               [("blend_grain", 0, "albedo")], catalog)

    place(node(g, "stone_layout"), {
        "gen_inputs": (-450, 250), "gen_parameters": (-450, -330), "gen_outputs": (1050, 0)})
    place(node(g, "stone_color"), {
        "gen_inputs": (-50, 0), "gen_parameters": (-50, -300), "gen_outputs": (800, -50)})
    place(node(g, "stone_surface"), {
        "gen_inputs": (-250, -360), "gen_parameters": (56, -600), "gen_outputs": (1000, -360)})
    place(node(g, "mortar"), {
        "gen_inputs": (-300, 100), "gen_parameters": (-300, 400), "gen_outputs": (1350, 50)})
    place(node(g, "relief"), {
        "gen_inputs": (-50, 150), "gen_parameters": (-50, -250), "gen_outputs": (1000, 150)})
    place(node(g, "surface_grain"), {
        "gen_inputs": (-300, -100), "gen_parameters": (-300, 150), "gen_outputs": (750, -50)})
    # Top level reads as a layer stack, left to right into Material. The
    # collapsed nodes carry seed_int 0, so moving them moves no seeds.
    place(g, {"stone_layout": (-900, 0), "stone_color": (-600, -200),
              "stone_surface": (-900, 300), "mortar": (-300, 0),
              "surface_grain": (0, -200), "relief": (0, 200), "Material": (300, 0)})
    rename_nodes(g, _S07_NAMES)
    return save_variant(g, _LABEL, "s07_cobblestone", 1)


# Mortar colour: a mid warm-gray mortar, varied by the surface noise. Kept
# a step darker than the light stones (0.55-0.62) so a filled joint still
# separates them under the lit preview; a light lime mortar washed out.
_MORTAR_COLOR = [
    (0.0, 0.30, 0.29, 0.27),
    (1.0, 0.44, 0.42, 0.39),
]
# MortarMask = smoothstep(clamp((L - w) x 8)): the colour reaches full
# mortar within an eighth of the joint ramp below the fill level.
_MORTAR_EDGE = 8

# s07 host names: _DRY_EARTH_NAMES (shared with s08/s10/s11, left as is)
# with two misnomers corrected for the host. perlin_1 has never fed the
# relief here: it is JointWarp's displacement and the metallic source.
# colorize_3 is that metallic variation (dry_earth wires it to Material's
# metallic_tex, 0-0.52), not a relief contrast.
_S07_NAMES = {
    **{k: v for k, v in _DRY_EARTH_NAMES.items() if k != "colorize_0"},
    "perlin_1": "JointWarpNoise",
    "colorize_3": "StoneMetallic",
    "colorize_cobble": "StoneColor",
    "perlin_grain": "GrainNoise",
    "colorize_grain": "GrainContrast",
    "blend_grain": "GrainOverStone",
}



def build_s09_ashlar_wall(catalog: dict) -> str:
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
    # Direct normal path (2026-09-27): the donor's buffered param4=1 races to a
    # flat normal headless; param4=0 at the same param1 matches within 0.37/255.
    set_param(g, "normal_map_0", "param4", 0)
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

    # Deep Parallax: route the relief chain into Material.to_port 6
    # (depth_tex). NOTE: to_port 6 was NOT unconnected before this change --
    # stone_wall's own donor graph already fed colorize_6 into depth_tex, so
    # every stone_wall-descended cookbook material has been silently
    # exporting a real heightmap_enabled=true .tres all along
    # (verified by rendering the pre-this-change committed .ptex). Tried
    # tapping blend_2 directly (the plan's literal suggestion, bypassing the
    # colorize step) and rendered it: WRONG polarity -- blend_2's raw signal
    # is high at the mortar joints, so a raw tap makes joints bulge OUT and
    # block faces sink IN, backwards for a masonry wall. colorize_6 applies
    # exactly the inverting gradient (white at low blend_2 / block faces,
    # black at high blend_2 / joints) that makes the polarity correct: block
    # faces raised, joints recessed. So the explicit choice here is
    # colorize_6, not blend_2 -- this makes deliberate and explicit
    # (independent of whatever the stone_wall donor happens to wire) a
    # connection that used to be an unexamined accident of that donor graph.
    # rewire() (not append) because a connection into this port already
    # exists -- two connections into one to_port would be malformed.
    rewire(g, "Material", 6, "colorize_6", 0)
    # depth_scale: donor default (0.2) -> heightmap_scale 5.0 on export
    # (Godot 4 Standard target multiplies by 25.0). Bumped to a masonry-scale
    # starting point; tuned for real in Step 4's visual pass.
    set_param(g, "Material", "depth_scale", 0.3)

    # Subgraph grouping. `stone_wall`'s own blend_0 is a genuine masked
    # blend, port sources traced from its raw connections before grouping:
    # port0(s1)=colorize_1 (block tone, fed by blend_1's per-brick random),
    # port1(s2)=colorize_0 (mortar tone, fed by Perlin), port2(mask)=
    # colorize_2 (the Warp'd Bricks shape, high inside each brick face and
    # low at the joints) -- so mask-high shows the block tone and mask-low
    # shows the mortar tone, the expected read for cut stone with dark
    # joints (not the sf03/l02-style reversal). blend_1 (Perlin + Bricks
    # port1 random -> colorize_1) and blend_2 (Warp + Perlin -> the height/
    # AO/depth fan-out) both carry no port2 mask (unconnected -> uniform
    # 1.0), plain amount mixes, untouched by this builder. Neither blend's
    # wiring is modified here, only regrouped -- verified unchanged by
    # `renders_match` below. `uniform_0` (metallic constant) and the
    # unnamed "394" shader-preview node are left top-level, matching the
    # precedent for untouched single-purpose nodes feeding one port
    # directly. The relief/AO/depth chain (blend_2, colorize_6, colorize_4,
    # normal_map_0) carries no builder-set parameter of its own, so it is
    # folded into the color group rather than left standing with zero
    # exposed parameters.
    group_into_subgraph(g, ["Bricks", "perlin_0", "Warp", "colorize_2", "colorize_7"],
                         "block_layout", "Block Layout",
                         [("Bricks", "columns", "param0", "Block size"),
                          ("Bricks", "mortar", "param1", "Joint width"),
                          ("Bricks", "bevel", "param2", "Edge chamfer")],
                         catalog)
    group_into_subgraph(g, ["Perlin", "colorize_0", "blend_1", "colorize_1",
                             "blend_0", "blend_2", "colorize_6", "colorize_4",
                             "normal_map_0"],
                         "block_finish", "Block & Mortar Finish",
                         [("colorize_1", "gradient", "param0", "Block color")],
                         catalog)
    rename_nodes(g, {
        "Bricks": "BlockLayout",
        "Warp": "BlockWarp",
        "perlin_0": "BlockWarpNoise",
        "colorize_2": "JointMask",
        "colorize_7": "JointRoughness",
        "Perlin": "SurfaceNoise",
        "colorize_0": "MortarColor",
        "blend_1": "PerBlockRandom",
        "colorize_1": "BlockColor",
        "blend_0": "AlbedoComposite",
        "blend_2": "ReliefComposite",
        "colorize_4": "BlockAO",
        "colorize_6": "BlockHeight",
        "normal_map_0": "BlockNormal",
        "uniform_0": "NonMetallic",
        "394": "ShaderPreviewUnused",
    })
    return save_variant(g, _LABEL, "s09_ashlar_wall", 1)



def build_s11_marble(catalog: dict) -> str:
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
    # Direct normal path (2026-09-27): the donor's buffered param4=1 races to a
    # flat normal headless; param4=0 at the same param1 matches within 0.37/255.
    set_param(g, "normal_map_0", "param4", 0)

    # Subgraph grouping. Unlike s07/s08/s10, this builder never rewires the
    # donor -- colorize_0 (not colorize_cobble) is still blend_0's port1
    # background exactly as dry_earth ships it, so warp_0 stays paired with
    # blend_0, its most direct and most visible consumer here (the flowing
    # crack/vein network). warp_0.amount is 0.5 -- HIGH, deliberately, the
    # single most sensitive value in this whole category ("IS the look"
    # rather than haze to kill) -- so it is emphatically NOT exposed as a
    # friendly parameter; verified below with an extra-scrutiny
    # renders_match check (actual diff value, not just pass/fail) per the
    # category caution. colorize_3 (metallic, zeroed) stays an unexposed
    # member of the relief group -- "make this non-metal marble metallic"
    # isn't a friendly knob worth surfacing.
    group_into_subgraph(g, ["voronoi_0", "colorize_1", "warp_0", "perlin_0",
                             "colorize_0", "blend_0"],
                         "marble_veins", "Marble Base & Veins",
                         [("voronoi_0", "scale_x", "param0", "Vein scale"),
                          ("colorize_0", "gradient", "param1", "Base color"),
                          ("blend_0", "amount", "param2", "Vein softness")],
                         catalog)
    group_into_subgraph(g, ["perlin_1", "colorize_3", "colorize_4", "blend_1",
                             "colorize", "normal_map_0"],
                         "marble_relief", "Relief & Metallic",
                         [("normal_map_0", "param1", "param0", "Vein relief")],
                         catalog)
    rename_nodes(g, {
        **_DRY_EARTH_NAMES,
        "colorize_0": "StoneColor",   # active marble base cream here, not orphaned
        "perlin_0": "BaseNoise",      # feeds StoneColor directly, not relief-fine-noise
        "colorize_3": "NonMetallic",  # metallic zeroed here, not the relief-contrast role
    })
    return save_variant(g, _LABEL, "s11_marble", 1)


def build_s02_gray_granite(catalog: dict) -> str:
    """Polished gray granite, folded in from the Phase-3 hero set (was
    examples/s02_gray_granite, iter1 variant 2). The graph itself is
    author.build_s02_gray_granite's v2 unchanged: a `rock` clone whose albedo
    colorize is fed straight from voronoi_0's per-cell random output (port 2)
    at a fine cell scale, so each cell is a flat random gray fleck, with the
    normal_map param4=0 fix for real polished-stone micro-relief. This
    builder only GROUPS it: three named subgraphs so a person opening it sees
    fleck color, surface finish, and relief instead of 8 raw nodes.
    perlin_0 stays top-level because it feeds both the color group (blend_0)
    and the finish group (colorize_1, colorize_2).

    2026-09-14 normal/albedo alignment fix (see author.py's docstring for the
    root cause): the normal now derives from voronoi_0 port 2 too -- the same
    per-cell random already driving FleckColor -- instead of a separate
    relief voronoi that could never share its cell layout. voronoi_0 stays
    INSIDE fleck_color (group_into_subgraph auto-creates a second gen_outputs
    port for its second external consumer, the same mechanism that already
    lets it feed both blend_0 internally and normal_map_0 externally), so
    fleck_color now has two outputs: FleckColor's albedo and the raw per-cell
    random feeding stone_relief. stone_relief shrinks to just normal_map_0
    (voronoi_1/perlin_1/warp_0 no longer exist, see author.py)."""
    g = take_variant(author.build_s02_gray_granite, _LABEL, 2)
    group_into_subgraph(
        g, ["voronoi_0", "blend_0", "colorize_0"],
        "fleck_color", "Fleck Color",
        [("voronoi_0", "scale_x", "param0", "Fleck density"),
         ("colorize_0", "gradient", "param1", "Fleck colors")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_1", "colorize_2"],
        "surface_finish", "Surface Finish",
        [("colorize_2", "gradient", "param0", "Polish (roughness)")],
        catalog,
    )
    group_into_subgraph(
        g, ["normal_map_0"],
        "stone_relief", "Stone Relief",
        [("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    rename_nodes(g, {
        "voronoi_0": "FleckCells",
        "blend_0": "FleckBlendUnused",
        "colorize_0": "FleckColor",
        "colorize_1": "NonMetallic",
        "colorize_2": "PolishRoughness",
        "normal_map_0": "GraniteNormal",
        "perlin_0": "SurfaceNoise",
    })
    return save_variant(g, _LABEL, "s02_gray_granite", 1)


def build_s13_polished_marble(catalog: dict) -> str:
    """Polished Carrara-style marble, MOVED IN from the terrain category
    (was `t09_marbled_silt`, quality/cookbook_terrain.py). Grayson's verdict
    on that material's render: the fbm-turbulence swirl reads as marble, so
    embrace it -- keep the exact same base (`crocodile_skin` donor, `voronoi_0`
    retyped to `fbm` with a Perlin+folds turbulence basis) and rework it into
    a proper polished stone: classic white/gray Carrara palette, low glossy
    roughness, zero metallic, and a near-flat relief, instead of terrain's
    warm tan/sand "dried mineral wash" read.

    This is deliberately a DIFFERENT technique from `s11_marble` (which warps
    `dry_earth`'s voronoi crack network hard, per that builder's docstring,
    "the flow IS the look"). s11's veins come from a distance-field crack
    network pushed through heavy warp; s13's veins come from a folded fbm
    turbulence field with no voronoi cells anywhere in the graph. Keeping
    both gives the stone category two structurally distinct marble recipes,
    which is the point of preserving this fbm-turbulence proof rather than
    discarding it once the terrain slot moved on.

    Changes from `t09_marbled_silt`, all pointed at "polished stone" rather
    than "dry ground":

    - **Vein-retune fix (this pass)**: Grayson's verdict on the first stone
      render was TERRAZZO/speckled granite, not flowing Carrara veins. Root
      cause 1: `scale_x`/`scale_y` at 3 still made many small folded features
      per unit surface, not a handful of large meandering ones -- dropped to
      1.8 (a smaller MM scale number means larger features) so only a few
      major ridges span the sphere. `folds` bumped 2 -> 3 to make the fold
      geometry itself meander more (a different lever from feature count),
      while `iterations` dropped 5 -> 4 to hold fine-octave graininess down
      rather than let the extra fold complexity reintroduce speckle.
      Root cause 2: the albedo gradient's dark/transition region ate roughly
      56% of the fbm value range (0.0-0.28 and 0.72-1.0), so a wide swath of
      the field rendered as some shade of gray, reading as many small dark
      flecks instead of a few thin lines. Narrowed the vein-plus-transition
      band to 12% on each end (0.0-0.12, 0.88-1.0) and widened the near-white
      plateau to 76% of the range (0.12-0.88) so only the sparse fold
      extremes go dark.
    - Palette: classic white/gray Carrara, not t09's warm tan/rust. Base
      plateau near-white (~0.86-0.90) now spans the wide 0.12-0.88 middle of
      the gradient, with the vein core a charcoal grey (~0.16-0.17, darker
      than the prior cool-gray 0.32-0.35 so the thin lines read as crisp dark
      strokes) confined to a narrow band at each extreme (0.0-0.05, 0.95-1.0)
      with a short transition (0.05-0.12, 0.88-0.95) -- not a 50/50 split,
      which is what made the prior warm-toned pass at this shape read as burl
      wood rather than stone, and not the too-broad transition that made the
      first Carrara pass read as terrazzo.
    - Roughness: `MarbleRoughness` now reads the SAME raw fbm field as the
      albedo (this donor's shape feeds `colorize_0`/`colorize_1`/`colorize_3`
      all straight from `voronoi_0` port 0, so no rewiring is needed), with a
      narrow polished-marble band (0.20 field / 0.30 at the vein bands) in
      place of t09's flat near-white matte ramp -- a genuine roughness
      TEXTURE, not a bare scalar, so an ORM map still exports; the veins read
      a touch rougher than the polished field, matching real ground-and-
      polished stone where the veins take the polish slightly differently.
      Its gradient breakpoints (0.05/0.12/0.88/0.95) mirror the retuned
      albedo gradient's so the rougher band lines up with the vein band.
    - Metallic: `NonMetallic` (`uniform_0`) left at its untouched 0 -- marble
      is a dielectric, verified via the ORM metallic channel approach if a
      render is taken.
    - Relief: `MarbleNormal`'s `param1` dropped 0.25 -> 0.08 (`param4=0`
      unchanged, the standing flat-normal fix) -- polished marble is nearly
      flat, so the veins should be the faintest whisper of relief, not
      terrain's gentle swell."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "fbm",
           {"noise": 1, "scale_x": 1.8, "scale_y": 1.8, "folds": 3,
            "iterations": 4, "persistence": 0.5})
    set_gradient(g, "colorize_1", [    # classic white/gray Carrara: thin sparse veins
        (0.0,  0.16, 0.16, 0.17),   # charcoal vein core
        (0.05, 0.55, 0.55, 0.56),   # quick vein-edge transition
        (0.12, 0.88, 0.88, 0.86),   # near-white base plateau begins
        (0.88, 0.90, 0.90, 0.88),   # near-white base plateau (light variation)
        (0.95, 0.55, 0.55, 0.56),   # quick vein-edge transition
        (1.0,  0.16, 0.16, 0.17),   # charcoal vein core
    ])
    set_gradient(g, "colorize_3", [    # polished sheen, veins a touch rougher
        (0.0,  0.30, 0.30, 0.30),
        (0.05, 0.26, 0.26, 0.26),
        (0.12, 0.20, 0.20, 0.20),
        (0.88, 0.20, 0.20, 0.20),
        (0.95, 0.26, 0.26, 0.26),
        (1.0,  0.30, 0.30, 0.30),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.08, "param2": 0, "param4": 0}

    group_into_subgraph(g, ["voronoi_0", "colorize_1"],
                         "marble_veins", "Marble Veins",
                         [("voronoi_0", "scale_x", "param0", "Vein scale"),
                          ("colorize_1", "gradient", "param1", "Vein color")],
                         catalog)
    group_into_subgraph(g, ["colorize_0", "colorize_3", "normal_map_0"],
                         "polished_finish", "Polished Finish",
                         [("colorize_3", "gradient", "param0", "Roughness"),
                          ("normal_map_0", "param1", "param1", "Vein relief")],
                         catalog)
    rename_nodes(g, {
        "voronoi_0": "MarbleVeins",     # fbm Perlin+folds turbulence, retuned from t09
        "colorize_1": "VeinColor",
        "colorize_3": "MarbleRoughness",
        "colorize_0": "MarbleHeight",
        "normal_map_0": "MarbleNormal",
        "uniform_0": "NonMetallic",
    })
    return save_variant(g, _LABEL, "s13_polished_marble", 1)


def build_s12_eroded_sandstone(catalog: dict) -> str:
    """Water-eroded sandstone: horizontal sediment strata smeared into
    diagonal erosion runs, built FROM SCRATCH (no donor -- nothing else in
    the cookbook has this topology, and it needs its own).

    **Why `directional_warp`, not `slope_blur`.** The phase plan originally
    named `slope_blur` for this recipe. `slope_blur.mmg` is a compound graph
    built entirely from two `buffer` nodes sandwiching an `edge_detect`
    shader (`buffer -> edge_detect_3_3_2 -> buffer_2`, no unbuffered
    bypass), and `buffer` nodes compile a compute shader at load time --
    this project's headless `--export-material` pipeline cannot drive that
    (see `build_swatch_slope_blur`'s docstring in `quality/debug_swatches.py`
    for the proof: valid graph, all-black render). `directional_warp` has no
    such trap -- it is a plain per-pixel UV offset by a constant
    `angle`/`strength` (no map inputs needed, verified with `describe_node`
    and pixel-checked in `build_swatch_directional_warp`) -- and its
    displacement behavior is exactly the "smear a layered field along a
    constant direction" effect real water erosion needs, so it is a better
    fit for this material, not just a workaround.

    **Banded sediment base -- restored to distinct, legible strata (round
    2 fix, see below).** `SedimentNoise` is a `perlin` with `scale_x=4` (low
    -- few large horizontal-ish features) and `scale_y=14` (high again --
    more, thinner, clearly separated bands; raised back up from the
    de-wood pass's 9, which had softened the strata into a mottle), 3
    iterations and `persistence=0.62`. `SedimentBands` colorizes it through
    a 10-stop palette built as five flat COLOR PLATEAUS joined by soft
    (~0.08-wide) transitions -- pale buff / pale tan / muted rust / light
    warm grey / pale sandy highlight -- instead of a hard step or a fully
    smooth ramp, so each stratum still reads as a distinct band but fades
    gradually into its neighbor (round 3 fix, see below). Still
    lower-saturation/higher-value than a wood palette (pale, cool, dry),
    per the de-wood fix.

    **Fix (round 1: controller render read as polished wood, not
    sandstone).** The first pass's fine high-frequency bands + saturated
    warm-brown palette + glossy mid roughness, once smeared by
    `directional_warp`, read exactly like continuous wood grain. Fixed by:
    (1) matte roughness -- see below; (2) a fine `GritNoise` perlin
    multiplied subtly over the albedo (see below) so the surface reads as
    gritty stone, not smooth grain; (3) a paler/cooler/desaturated palette;
    (4) chunkier bands (`scale_y` dropped 16->9) so the base had broad
    bands for the warp to smear, not fine continuous lines.

    **Fix (round 2: controller render read as travertine/limestone mottle,
    strata washed out).** Pulling the banding down in round 1 overcorrected
    -- the sediment layers stopped reading as distinct strata at all. Fixed
    by (1) raising `SedimentNoise.scale_y` back up (9 -> 14, more/thinner
    bands) while keeping `scale_x` low (still 4, stretched horizontal
    bands); (2) replacing `SedimentBands`' smooth 6-stop ramp with the
    10-stop hard-plateau gradient above, so individual layers are visible as
    distinct color bands rather than a soft gradient; (3) trimming
    `ErosionWarp.strength` 0.62 -> 0.5 so the now-thinner, higher-contrast
    layers get smeared into legible erosion runs rather than dissolved back
    into a mottle. The matte roughness, grit, and pale/cool palette from
    round 1 are all kept unchanged.

    **Fix (round 3: controller read the band edges as too hard-edged /
    posterized, like topographic contour lines).** Round 2's 10-stop
    gradient joined its five color plateaus with hard ~0.02-wide cuts,
    which read as crisp, almost cartographic steps rather than natural
    geology. Softened by widening each of the four transition zones from
    ~0.02 to ~0.08 (the four paired near-coincident stops moved apart:
    0.19/0.21 -> 0.16/0.24, 0.40/0.42 -> 0.37/0.45, 0.61/0.63 -> 0.58/0.66,
    0.82/0.84 -> 0.79/0.87), so each layer now fades gradually into the
    next instead of stepping. All 5 colors, their order, and their
    approximate plateau centers are unchanged; only the transition width
    moved, trading round 2's "5 flat plateaus / hard cuts" look for
    "5 distinct layers / soft edges" -- still clearly banded, not washed
    back into round 1's smooth mottle. `SedimentNoise.scale_y`,
    `ErosionWarp.strength`/`angle`, the matte roughness, and the grit are
    all unchanged from round 2.

    **Directional erosion.** `ErosionWarp` (`directional_warp`) takes
    `SedimentBands`' RGBA output directly on its `in#` port (port 0) --
    proven valid by `dry_earth`'s own `warp_0`, which reads an RGBA colorize
    the same way. `anglemap`/`strengthmap` (ports 1/2) are left unconnected
    so the node uses its own constant defaults, giving a clean, repeatable
    displacement from `angle`/`strength` alone (per `describe_node` and the
    task brief). `angle=-58` (a steep diagonal, not the swatch's horizontal
    0) and `strength=0.5` (moderate -- trimmed from round 1's 0.62 per the
    round-2 fix above) smear the horizontal bands into diagonal streaks --
    the strata read as if water ran down the face and dragged the layers
    with it, smeared but still legible as layers, not erased.

    **Relief and roughness both read the eroded field, not the pre-warp
    one** -- `ErosionWarp`'s output feeds both `ReliefHeight` (a plain 0->1
    ramp) and `SandstoneRoughness` (a narrow MATTE band, 0.80-0.88 -- raised
    substantially from the first pass's 0.52-0.70 glossy-leaning band, which
    was a big part of the wood-sheen misread; sandstone is not glossy), the
    same "RGBA warp output straight into an f-typed `colorize` input"
    pattern `dry_earth` uses for `warp_0 -> colorize_4`. So the bump map and
    the roughness variation both carry the erosion streaks, not just the
    albedo -- a stone face that has been eroded reads that erosion in its
    surface relief and finish, not only its color. `SandstoneNormal`
    (`normal_map`) keeps `param4=0` (the project's standing flat-normal fix
    for a directly-fed analytic source) with a moderate `param1=0.3` --
    gentle relief, not a deep bulge; this is a worn stone face, not chunky
    cobbles. Non-metal: `Material.metallic` is set to 0 as a plain scalar
    (port 1 left unconnected), the same convention
    `_from_scratch_noise_material` and `s11_marble`'s roughness use when no
    texture is wired to a port -- the scalar applies directly.

    **Surface grit.** `GritNoise` is a fine perlin (`scale_x=42`,
    `scale_y=42`, 5 iterations -- the same fine-grain idiom `s05`/`s06`/
    `s07`/`s08`/`s10` already use in this file for per-stone surface grain),
    `GritContrast` colorizes it to a narrow, subtle multiply band
    (0.88-1.0), and `AlbedoGrit` (`blend`, `blend_type=2` Multiply,
    `amount=1`, port 2 mask left unconnected so the opacity defaults to a
    uniform 1.0 -- no threshold/speckle risk) multiplies it over
    `ErosionWarp`'s eroded albedo before `Material` port 0. Continuous smooth
    grain reads as wood; a fine gritty micro-texture reads as stone, so this
    is the second (with the matte roughness) biggest lever against the wood
    misread.

    **How this differs from the rest of the stone category.** Every other
    stone recipe differentiates through a spatial CELL pattern (voronoi
    plates/cracks for s07/s08/s10/s11, a hex grid for s05, Bricks courses
    for s09) or per-cell/per-fleck random color (s02, s04, s06). This one has
    no cells at all -- its structure is a directional smear of horizontal
    layers, the one distortion technique (`directional_warp`) nothing else
    in the cookbook uses. That keeps it visually and structurally distinct
    rather than reading as another rocky-blob variant."""
    g = {
        "connections": [],
        "nodes": [
            {"name": "perlin_bands", "type": "perlin",
             "node_position": {"x": 0, "y": 0},
             "parameters": {"scale_x": 4, "scale_y": 14, "iterations": 3,
                            "persistence": 0.62}},
            {"name": "colorize_bands", "type": "colorize",
             "node_position": {"x": 260, "y": 0},
             "parameters": {"gradient": _grad([
                 (0.00, 0.74, 0.68, 0.58),   # pale buff (plateau)
                 (0.16, 0.74, 0.68, 0.58),   # pale buff (plateau end)
                 (0.24, 0.80, 0.74, 0.64),   # -> pale tan, soft transition
                 (0.37, 0.80, 0.74, 0.64),   # pale tan (plateau)
                 (0.45, 0.60, 0.48, 0.38),   # -> muted rust, soft transition
                 (0.58, 0.60, 0.48, 0.38),   # muted rust (plateau)
                 (0.66, 0.70, 0.64, 0.55),   # -> light warm grey, soft transition
                 (0.79, 0.70, 0.64, 0.55),   # light warm grey (plateau)
                 (0.87, 0.84, 0.78, 0.68),   # -> pale sandy highlight, soft transition
                 (1.00, 0.84, 0.78, 0.68),   # pale sandy highlight (plateau)
             ])}},
            {"name": "directional_warp_0", "type": "directional_warp",
             "node_position": {"x": 520, "y": 0},
             "parameters": {"angle": -58, "strength": 0.5}},
            {"name": "colorize_relief", "type": "colorize",
             "node_position": {"x": 780, "y": -140},
             "parameters": {"gradient": _grad([(0.0, 0, 0, 0), (1.0, 1, 1, 1)])}},
            {"name": "normal_map_0", "type": "normal_map",
             "node_position": {"x": 1040, "y": -140},
             "parameters": {"param0": 10, "param1": 0.3, "param2": 0, "param4": 0}},
            {"name": "colorize_rough", "type": "colorize",
             "node_position": {"x": 780, "y": 140},
             "parameters": {"gradient": _grad([
                 (0.0, 0.80, 0.80, 0.80), (1.0, 0.88, 0.88, 0.88)])}},
            {"name": "perlin_grit", "type": "perlin",
             "node_position": {"x": 780, "y": 320},
             "parameters": {"scale_x": 42, "scale_y": 42, "iterations": 5}},
            {"name": "colorize_grit", "type": "colorize",
             "node_position": {"x": 1040, "y": 320},
             "parameters": {"gradient": _grad([
                 (0.0, 0.88, 0.88, 0.88), (1.0, 1.0, 1.0, 1.0)])}},
            {"name": "blend_grit", "type": "blend",
             "node_position": {"x": 1300, "y": 160},
             "parameters": {"blend_type": 2, "amount": 1}},   # Multiply
            {"name": "Material", "type": "material",
             "node_position": {"x": 1560, "y": 0},
             "export_paths": {},
             "parameters": {
                 "albedo_color": {"a": 1, "r": 1, "g": 1, "b": 1, "type": "Color"},
                 "ao": 1, "depth_scale": 1, "emission_energy": 1,
                 "metallic": 0, "normal": 1, "roughness": 1,
                 "size": 11, "sss": 0}},
        ],
    }
    g["connections"] = [
        {"from": "perlin_bands", "from_port": 0, "to": "colorize_bands", "to_port": 0},
        {"from": "colorize_bands", "from_port": 0, "to": "directional_warp_0", "to_port": 0},
        {"from": "directional_warp_0", "from_port": 0, "to": "colorize_relief", "to_port": 0},
        {"from": "colorize_relief", "from_port": 0, "to": "normal_map_0", "to_port": 0},
        {"from": "normal_map_0", "from_port": 0, "to": "Material", "to_port": 4},
        {"from": "directional_warp_0", "from_port": 0, "to": "colorize_rough", "to_port": 0},
        {"from": "colorize_rough", "from_port": 0, "to": "Material", "to_port": 2},
        {"from": "perlin_grit", "from_port": 0, "to": "colorize_grit", "to_port": 0},
        {"from": "directional_warp_0", "from_port": 0, "to": "blend_grit", "to_port": 0},
        {"from": "colorize_grit", "from_port": 0, "to": "blend_grit", "to_port": 1},
        {"from": "blend_grit", "from_port": 0, "to": "Material", "to_port": 0},
    ]

    group_into_subgraph(g, ["perlin_bands", "colorize_bands"],
                         "sediment_layers", "Sediment Layers",
                         [("perlin_bands", "scale_y", "param0", "Layer frequency"),
                          ("colorize_bands", "gradient", "param1", "Sediment color")],
                         catalog)
    group_into_subgraph(g, ["directional_warp_0", "colorize_relief", "normal_map_0",
                             "colorize_rough"],
                         "erosion_relief", "Erosion & Relief",
                         [("directional_warp_0", "angle", "param0", "Erosion angle"),
                          ("directional_warp_0", "strength", "param1", "Erosion strength"),
                          ("normal_map_0", "param1", "param2", "Relief strength"),
                          ("colorize_rough", "gradient", "param3", "Roughness")],
                         catalog)
    group_into_subgraph(g, ["perlin_grit", "colorize_grit", "blend_grit"],
                         "surface_grit", "Surface Grit",
                         [("perlin_grit", "scale_x", "param0", "Grit scale")],
                         catalog)
    rename_nodes(g, {
        "perlin_bands": "SedimentNoise",
        "colorize_bands": "SedimentBands",
        "directional_warp_0": "ErosionWarp",
        "colorize_relief": "ReliefHeight",
        "normal_map_0": "SandstoneNormal",
        "colorize_rough": "SandstoneRoughness",
        "perlin_grit": "GritNoise",
        "colorize_grit": "GritContrast",
        "blend_grit": "AlbedoGrit",
    })
    return save_variant(g, _LABEL, "s12_eroded_sandstone", 1)


def build_s14_wet_river_stone(catalog: dict) -> str:
    """Wet river stone, and the river-pebble HOST (2026-09-27): one material
    carrying exposed feature layers in place of s04, s06 and t08. Every
    layer defaults OFF (its mask is 0), so the default graph renders the
    same wet stone as the pre-host s14, pixel for pixel.

    Base (the pre-host s14, unchanged in look): CLONE `rock`, big voronoi
    cells (PebbleCells, scale 7) as rounded pebbles through s06's analytic
    coin-profile dome (cos -> clamp -> smoothstep, zero control points so no
    ring banding under the param4=0 normal), plus s06's TWO-SCALE mix: a
    finer voronoi (SmallStoneCells, 18) with its own dome nestled at 0.65 and
    max-composited, so small stones fill the big ones' seams. Top flatness
    1.0 (s06 uses 1.5) keeps curvature on the tops. Wet finish: dark
    near-black palette, roughness masked by the same height field (glossy
    0.08 crevices, semi-wet 0.20-0.38 tops) and split into wet/damp patches
    by a large perlin (PatchNoise). Dielectric (metallic 0): reflections
    come from Godot's default specular term.

    Host refactor (render-identical, proven by a 2048 full-image diff):
    - StoneRandomMix mixes the two cell sizes' RANDOM values (SmallStoneMask
      is exactly 0 or 1) before one palette colorize, where the pre-host
      graph colorized each size and mixed after. Same pixels, and one
      gradient per palette now covers both stone sizes.
    - Pebble size / Small stone size / Wet patch scale / Grain scale drive
      scale_x AND scale_y; Top flatness drives both dome chains. Material
      Maker applies every linked widget; mm-play binds only the first
      (scale_x / the big dome).
    - Packing (new param on Stone Profile, from t08_riverbed_pebbles' packed
      plates): 0 = round pebbles (the dome reads F1, distance to the cell
      seed), 1 = packed polygon plates (the dome reads 0.604 - distance to
      the cell border, so it falls to zero on the straight borders). Same
      coin profile either way; Top flatness sets how flat the plate top is.

    Layers, in data-flow order (each its own subgraph, one mask each):
    - Dry Layer (from s06_river_pebbles): `Dryness` 0-1 is the opacity of
      two blends, albedo toward the Dry color palette (s06's, in Stone
      Color) and roughness toward s06's dry finish (DryStoneRoughness
      0.42-0.60 on the tops, DrySeamRoughness 0.86-0.93 grit in the seams,
      split by the same height field that makes the relief). Mid values read
      as damp stone.
    - Surface Grain (from s06): s06's GrainNoise/GrainContrast, times
      `Grain amount`, multiplied into the albedo AND added into the height
      (0.15 * amount), so the grain in the colour and the grit in the relief
      are the same pixels. GrainNoise sits at (0, 0) of its subgraph: seed
      0, the same field s06 ships.
    - Contact Gaps (from t08_riverbed_pebbles): t08's PebbleEdges band
      (0.064 wide on PebbleCells' Borders output), times `Gap depth`, is ONE
      ContactMask that darkens the albedo toward black and cuts the height,
      so a joint is dark exactly where it is recessed (the same result as
      t08's Multiply at that amount). t08's 0.02 ContactWarp is left out
      (invisible at that amount).
    - Sediment Bed (from s04_scattered_river_stones): sand fills everything
      below `Bed level`. One BedMask, smoothstep(clamp((level - height) *
      4)), drives the albedo to s04's sand colour, the roughness to s04's
      sand roughness, and the height up to the flat bed level, so the
      stones poke out of a flat sand bed and the sand's colour edge is its
      relief edge. Level 0 is a no-op (the height is never below 0).
    Order matters: grain and gaps come before the bed, so sand fills the
    joints and covers the grain; the bed composites last. Every height op
    is a math node, so the height stays greyscale end to end and a layer at
    0 adds an exact 0 (the default render is bit-identical, not 1-LSB).

    Presets that reach each absorbed look are on the card
    (cookbook/stone/s14_wet_river_stone.md, "Feature layers")."""
    g = load_example("rock")
    set_param(g, "voronoi_0", "scale_x", 7)
    set_param(g, "voronoi_0", "scale_y", 7)
    set_param(g, "voronoi_0", "randomness", 1)
    set_gradient(g, "colorize_0", _S14_WET_COLOR)
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])   # non-metal
    add_node(g, "dome_curve", "math",
             {"op": 16, "default_in2": 2.6, "clamp": True})   # 16 = cos(A*B)
    add_node(g, "dome_flatten", "math",
             {"op": 2, "default_in2": 1.0, "clamp": True})    # 2 = A*B, clamp [0,1]
    add_node(g, "dome_smooth", "math", {"op": 20, "clamp": True})  # 20 = smoothstep(0,1,A)
    g["connections"] += [
        {"from": "dome_curve", "from_port": 0, "to": "dome_flatten", "to_port": 0},
        {"from": "dome_flatten", "from_port": 0, "to": "dome_smooth", "to_port": 0},
    ]
    # PACKING (from t08_riverbed_pebbles' packed plates): the dome reads the
    # distance to the cell SEED (F1, round pebbles) by default. Packing blends
    # that input toward (edge - distance to the cell BORDER), which reaches
    # the dome's zero (cos(2.6 * 0.604) = 0) exactly on the straight voronoi
    # borders, so the same coin profile becomes a polygon plate that fills
    # its cell. Math nodes, F1 + (plate - F1) * packing: Packing 0 adds an
    # exact 0, so the default is bit-identical.
    add_node(g, "plate_distance", "math",
             {"op": 1, "default_in1": _PLATE_EDGE, "clamp": True})   # edge - border distance
    add_node(g, "shape_delta", "math", {"op": 1})                    # plate - F1
    add_node(g, "packing_offset", "math", {"op": 2, "default_in2": 0})  # delta * Packing
    add_node(g, "dome_input", "math", {"op": 0})                     # F1 + offset
    g["connections"] += [
        {"from": "voronoi_0", "from_port": 1, "to": "plate_distance", "to_port": 1},
        {"from": "plate_distance", "from_port": 0, "to": "shape_delta", "to_port": 0},
        {"from": "voronoi_0", "from_port": 0, "to": "shape_delta", "to_port": 1},
        {"from": "shape_delta", "from_port": 0, "to": "packing_offset", "to_port": 0},
        {"from": "voronoi_0", "from_port": 0, "to": "dome_input", "to_port": 0},
        {"from": "packing_offset", "from_port": 0, "to": "dome_input", "to_port": 1},
        {"from": "dome_input", "from_port": 0, "to": "dome_curve", "to_port": 0},
    ]
    add_node(g, "voronoi_fine", "voronoi",
             {"scale_x": 18, "scale_y": 18, "randomness": 1})
    add_node(g, "dome_curve_f", "math", {"op": 16, "default_in2": 2.6, "clamp": True})
    add_node(g, "dome_flatten_f", "math", {"op": 2, "default_in2": 1.0, "clamp": True})
    add_node(g, "dome_smooth_f", "math", {"op": 20, "clamp": True})
    add_node(g, "dome_fine_low", "math", {"op": 2, "default_in2": 0.65})   # nestle lower
    add_node(g, "dome_mix", "math", {"op": 14})                            # 14 = max(coarse, fine)
    add_node(g, "sel_fine", "math", {"op": 15})                            # 15 = A<B (coarse < fine)
    g["connections"] += [
        {"from": "voronoi_fine", "from_port": 0, "to": "dome_curve_f", "to_port": 0},
        {"from": "dome_curve_f", "from_port": 0, "to": "dome_flatten_f", "to_port": 0},
        {"from": "dome_flatten_f", "from_port": 0, "to": "dome_smooth_f", "to_port": 0},
        {"from": "dome_smooth_f", "from_port": 0, "to": "dome_fine_low", "to_port": 0},
        {"from": "dome_smooth", "from_port": 0, "to": "dome_mix", "to_port": 0},
        {"from": "dome_fine_low", "from_port": 0, "to": "dome_mix", "to_port": 1},
        {"from": "dome_smooth", "from_port": 0, "to": "sel_fine", "to_port": 0},
        {"from": "dome_fine_low", "from_port": 0, "to": "sel_fine", "to_port": 1},
    ]
    # Per-stone random value across both stone sizes: sel_fine is exactly 0 or
    # 1, so mixing the two cells' random colours BEFORE the colorize gives the
    # same pixels as colorizing each and mixing after (the pre-host graph),
    # with one palette node per palette instead of two kept in sync.
    add_node(g, "stone_random", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "voronoi_fine", "from_port": 2, "to": "stone_random", "to_port": 0},
        {"from": "voronoi_0", "from_port": 2, "to": "stone_random", "to_port": 1},
        {"from": "sel_fine", "from_port": 0, "to": "stone_random", "to_port": 2},
    ]
    rewire(g, "colorize_0", 0, "stone_random", 0)
    drop_conn(g, "warp_0", 0)
    drop_conn(g, "warp_0", 1)
    g["nodes"] = [n for n in g["nodes"]
                  if n["name"] not in ("voronoi_1", "perlin_1", "warp_0")]
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.6)
    # Wet finish: water pools low, so crevices are glossiest; PatchNoise
    # splits whole regions into wet and damp patches.
    set_gradient(g, "colorize_2", [        # WetRoughness
        (0.0,  0.08, 0.08, 0.08),
        (0.35, 0.14, 0.14, 0.14),
        (1.0,  0.20, 0.20, 0.20),
    ])
    rewire(g, "colorize_2", 0, "dome_mix", 0)
    add_node(g, "colorize_damp", "colorize", {"gradient": _grad([   # DampPatchRoughness
        (0.0,  0.20, 0.20, 0.20),
        (0.35, 0.30, 0.30, 0.30),
        (1.0,  0.38, 0.38, 0.38),
    ])})
    add_node(g, "perlin_patch", "perlin",
             {"scale_x": 3, "scale_y": 3, "iterations": 2})   # large-scale patchiness
    add_node(g, "colorize_patch", "colorize", {"gradient": _grad([
        (0.0, 0, 0, 0), (0.40, 0, 0, 0), (0.60, 1, 1, 1), (1.0, 1, 1, 1),
    ])})   # soft threshold: 1 = wet patch, 0 = damp patch
    add_node(g, "blend_patch", "blend", {"blend_type": 0, "amount": 1})   # Mix
    g["connections"] += [
        {"from": "dome_mix", "from_port": 0, "to": "colorize_damp", "to_port": 0},
        {"from": "perlin_patch", "from_port": 0, "to": "colorize_patch", "to_port": 0},
        {"from": "colorize_2", "from_port": 0, "to": "blend_patch", "to_port": 0},
        {"from": "colorize_damp", "from_port": 0, "to": "blend_patch", "to_port": 1},
        {"from": "colorize_patch", "from_port": 0, "to": "blend_patch", "to_port": 2},
    ]

    # --- Dry layer (s06) ---
    add_node(g, "DryStoneColor", "colorize", {"gradient": _grad(_S06_DRY_COLOR)})
    add_node(g, "Dryness", "uniform_greyscale", {"color": 0})
    add_node(g, "DryColorComposite", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "DryStoneRoughness", "colorize",
             {"gradient": _grad([(0.0, 0.42, 0.42, 0.42), (1.0, 0.60, 0.60, 0.60)])})
    add_node(g, "DrySeamRoughness", "colorize",
             {"gradient": _grad([(0.0, 0.86, 0.86, 0.86), (1.0, 0.93, 0.93, 0.93)])})
    add_node(g, "DryRoughnessMix", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "DryRoughnessComposite", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "stone_random", "from_port": 0, "to": "DryStoneColor", "to_port": 0},
        {"from": "DryStoneColor", "from_port": 0, "to": "DryColorComposite", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "DryColorComposite", "to_port": 1},
        {"from": "Dryness", "from_port": 0, "to": "DryColorComposite", "to_port": 2},
        {"from": "perlin_0", "from_port": 0, "to": "DryStoneRoughness", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "DrySeamRoughness", "to_port": 0},
        # dome_mix is 1 on the tops, 0 in the seams: tops show port 0
        {"from": "DryStoneRoughness", "from_port": 0, "to": "DryRoughnessMix", "to_port": 0},
        {"from": "DrySeamRoughness", "from_port": 0, "to": "DryRoughnessMix", "to_port": 1},
        {"from": "dome_mix", "from_port": 0, "to": "DryRoughnessMix", "to_port": 2},
        {"from": "DryRoughnessMix", "from_port": 0, "to": "DryRoughnessComposite", "to_port": 0},
        {"from": "blend_patch", "from_port": 0, "to": "DryRoughnessComposite", "to_port": 1},
        {"from": "Dryness", "from_port": 0, "to": "DryRoughnessComposite", "to_port": 2},
    ]

    # --- Surface grain (s06) ---
    add_node(g, "GrainNoise", "perlin", {"scale_x": 40, "scale_y": 40, "iterations": 5})
    add_node(g, "GrainContrast", "colorize",
             {"gradient": _grad([(0.0, 0.82, 0.82, 0.82), (1.0, 1.0, 1.0, 1.0)])})
    add_node(g, "GrainAmount", "uniform_greyscale", {"color": 0})
    add_node(g, "GrainColorComposite", "blend", {"blend_type": 2, "amount": 1})  # 2 = Multiply
    add_node(g, "GrainWeight", "math", {"op": 2, "default_in2": _GRAIN_HEIGHT})  # amount * 0.15
    add_node(g, "GrainHeight", "math", {"op": 2})                                # grain * weight
    add_node(g, "GrainReliefHeight", "math", {"op": 0})                          # height + grain
    g["connections"] += [
        {"from": "GrainNoise", "from_port": 0, "to": "GrainContrast", "to_port": 0},
        {"from": "GrainContrast", "from_port": 0, "to": "GrainColorComposite", "to_port": 0},
        {"from": "DryColorComposite", "from_port": 0, "to": "GrainColorComposite", "to_port": 1},
        {"from": "GrainAmount", "from_port": 0, "to": "GrainColorComposite", "to_port": 2},
        {"from": "GrainAmount", "from_port": 0, "to": "GrainWeight", "to_port": 0},
        {"from": "GrainNoise", "from_port": 0, "to": "GrainHeight", "to_port": 0},
        {"from": "GrainWeight", "from_port": 0, "to": "GrainHeight", "to_port": 1},
        {"from": "dome_mix", "from_port": 0, "to": "GrainReliefHeight", "to_port": 0},
        {"from": "GrainHeight", "from_port": 0, "to": "GrainReliefHeight", "to_port": 1},
    ]

    # --- Contact gaps (t08) ---
    # t08's PebbleEdges band on the Borders output, inverted so it reads 1 in
    # the gap; times Gap depth it is ONE ContactMask that darkens the albedo
    # toward black and cuts the height (height * (1 - mask)), so a joint is
    # dark exactly where it is recessed. Blend Normal toward black at opacity
    # m equals t08's Multiply by the edge band at amount m. Height stays a
    # greyscale (math) signal so the default is bit-identical.
    add_node(g, "ContactEdges", "colorize",
             {"gradient": _grad([(0.0, 1, 1, 1), (0.064, 0, 0, 0)])})
    add_node(g, "GapDepth", "uniform_greyscale", {"color": 0})
    add_node(g, "ContactMask", "math", {"op": 2})                          # edges * depth
    add_node(g, "GapShade", "uniform", {"color": {"a": 1, "r": 0, "g": 0, "b": 0, "type": "Color"}})
    add_node(g, "ContactColorComposite", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "ContactHeightKeep", "math", {"op": 1, "default_in1": 1})  # 1 - mask
    add_node(g, "ContactHeight", "math", {"op": 2})                        # height * keep
    g["connections"] += [
        {"from": "voronoi_0", "from_port": 1, "to": "ContactEdges", "to_port": 0},
        {"from": "ContactEdges", "from_port": 0, "to": "ContactMask", "to_port": 0},
        {"from": "GapDepth", "from_port": 0, "to": "ContactMask", "to_port": 1},
        {"from": "GapShade", "from_port": 0, "to": "ContactColorComposite", "to_port": 0},
        {"from": "GrainColorComposite", "from_port": 0, "to": "ContactColorComposite", "to_port": 1},
        {"from": "ContactMask", "from_port": 0, "to": "ContactColorComposite", "to_port": 2},
        {"from": "ContactMask", "from_port": 0, "to": "ContactHeightKeep", "to_port": 1},
        {"from": "GrainReliefHeight", "from_port": 0, "to": "ContactHeight", "to_port": 0},
        {"from": "ContactHeightKeep", "from_port": 0, "to": "ContactHeight", "to_port": 1},
    ]

    # --- Sediment bed (s04) ---
    # BedMask = smoothstep(clamp((level - height) * 4)) is the opacity of the
    # sand colour and roughness blends, and fills the height toward the
    # level: height + clamp(level - height) * mask. The smoothstep removes
    # the clamp's two slope kinks, which the param4=0 normal drew as a thin
    # ring around every stone (s06's coin-profile lesson). Level 0 changes
    # nothing (the height is never below 0, so the mask is 0 and the fill
    # adds 0).
    add_node(g, "BedLevel", "uniform_greyscale", {"color": 0})
    add_node(g, "BedDepth", "math", {"op": 1, "clamp": True})                  # 1 = A-B: level - height
    add_node(g, "BedRamp", "math", {"op": 2, "default_in2": _BED_EDGE, "clamp": True})
    add_node(g, "BedMask", "math", {"op": 20, "clamp": True})                 # 20 = smoothstep
    add_node(g, "BedColor", "colorize",
             {"gradient": _grad([(0.0, 0.62, 0.54, 0.40), (1.0, 0.70, 0.62, 0.47)])})
    add_node(g, "BedRoughness", "colorize",
             {"gradient": _grad([(0.0, 0.78, 0.78, 0.78), (1.0, 0.85, 0.85, 0.85)])})
    add_node(g, "BedColorComposite", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "BedRoughnessComposite", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "BedFill", "math", {"op": 2})                                  # depth * mask
    add_node(g, "BedHeight", "math", {"op": 0})                                # height + fill
    g["connections"] += [
        {"from": "BedLevel", "from_port": 0, "to": "BedDepth", "to_port": 0},
        {"from": "ContactHeight", "from_port": 0, "to": "BedDepth", "to_port": 1},
        {"from": "BedDepth", "from_port": 0, "to": "BedRamp", "to_port": 0},
        {"from": "BedRamp", "from_port": 0, "to": "BedMask", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "BedColor", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "BedRoughness", "to_port": 0},
        {"from": "BedColor", "from_port": 0, "to": "BedColorComposite", "to_port": 0},
        {"from": "ContactColorComposite", "from_port": 0, "to": "BedColorComposite", "to_port": 1},
        {"from": "BedMask", "from_port": 0, "to": "BedColorComposite", "to_port": 2},
        {"from": "BedRoughness", "from_port": 0, "to": "BedRoughnessComposite", "to_port": 0},
        {"from": "DryRoughnessComposite", "from_port": 0, "to": "BedRoughnessComposite", "to_port": 1},
        {"from": "BedMask", "from_port": 0, "to": "BedRoughnessComposite", "to_port": 2},
        {"from": "BedDepth", "from_port": 0, "to": "BedFill", "to_port": 0},
        {"from": "BedMask", "from_port": 0, "to": "BedFill", "to_port": 1},
        {"from": "ContactHeight", "from_port": 0, "to": "BedHeight", "to_port": 0},
        {"from": "BedFill", "from_port": 0, "to": "BedHeight", "to_port": 1},
    ]
    rewire(g, "Material", 0, "BedColorComposite", 0)
    rewire(g, "Material", 2, "BedRoughnessComposite", 0)
    rewire(g, "normal_map_0", 0, "BedHeight", 0)

    # Layout (flat graph, before grouping; each position is inside the
    # subgraph the node ends up in). Seed-bearing noises keep their pre-host
    # positions so their seeds, and the cells, are unchanged: voronoi_0
    # (117, 448) and perlin_0 (105, 305) are the rock donor's own;
    # voronoi_fine, perlin_patch and GrainNoise sit at (0, 0) of their
    # subgraphs (GrainNoise's seed is then s06's).
    place(g, {
        # stone_profile
        "plate_distance": (-750, -500), "shape_delta": (-500, -500),
        "packing_offset": (-250, -500), "dome_input": (0, -300),
        "dome_curve": (250, -250), "dome_flatten": (500, -250), "dome_smooth": (750, -250),
        "dome_curve_f": (250, 0), "dome_flatten_f": (500, 0), "dome_smooth_f": (750, 0),
        "dome_fine_low": (1000, 0), "dome_mix": (1250, -200), "sel_fine": (1250, 50),
        "stone_random": (1500, 250),
        # stone_color
        "colorize_0": (0, 0), "DryStoneColor": (0, 250),
        # material_finish
        "colorize_2": (250, -350), "colorize_damp": (250, -175), "colorize_patch": (250, 0),
        "blend_patch": (550, -200), "colorize_1": (250, 250),
        # dry_layer
        "DryStoneRoughness": (0, 150), "DrySeamRoughness": (0, 320), "Dryness": (0, 500),
        "DryColorComposite": (300, -100), "DryRoughnessMix": (300, 220),
        "DryRoughnessComposite": (600, 300),
        # surface_grain
        "GrainNoise": (0, 0), "GrainContrast": (250, -150), "GrainAmount": (0, 300),
        "GrainWeight": (250, 300), "GrainHeight": (500, 200),
        "GrainColorComposite": (550, -150), "GrainReliefHeight": (800, 150),
        # contact_gaps
        "ContactEdges": (0, 0), "GapDepth": (0, 250), "GapShade": (250, -150),
        "ContactMask": (250, 100), "ContactColorComposite": (550, -100),
        "ContactHeightKeep": (550, 200), "ContactHeight": (800, 250),
        # sediment_bed
        "BedColor": (0, -200), "BedRoughness": (0, 0), "BedLevel": (0, 400),
        "BedDepth": (250, 350), "BedRamp": (500, 350), "BedMask": (750, 550),
        "BedColorComposite": (1000, -200), "BedRoughnessComposite": (1000, 50),
        "BedFill": (1000, 450), "BedHeight": (1250, 300),
    })

    group_into_subgraph(g, ["voronoi_0", "blend_0", "perlin_0"],
                         "pebble_pattern", "Pebble Pattern",
                         [("voronoi_0", "scale_x", "param0", "Pebble size")],
                         catalog)
    link_also(g, "pebble_pattern", "param0", "voronoi_0", "scale_y")
    tidy_ports(g, "pebble_pattern", [],
               [("perlin_0", 0, "noise"), ("voronoi_0", 0, "cells"),
                ("voronoi_0", 1, "borders"), ("voronoi_0", 2, "cell_random")], catalog)
    group_into_subgraph(g, ["plate_distance", "shape_delta", "packing_offset", "dome_input",
                             "dome_curve", "dome_flatten", "dome_smooth",
                             "voronoi_fine", "dome_curve_f", "dome_flatten_f",
                             "dome_smooth_f", "dome_fine_low", "dome_mix",
                             "sel_fine", "stone_random"],
                         "stone_profile", "Stone Profile",
                         [("voronoi_fine", "scale_x", "param0", "Small stone size"),
                          ("dome_fine_low", "default_in2", "param1", "Small stone height"),
                          ("dome_flatten", "default_in2", "param2", "Top flatness"),
                          ("packing_offset", "default_in2", "param3", "Packing")],
                         catalog)
    link_also(g, "stone_profile", "param0", "voronoi_fine", "scale_y")
    link_also(g, "stone_profile", "param2", "dome_flatten_f", "default_in2")
    tidy_ports(g, "stone_profile",
               [("pebble_pattern", 1, "cells"), ("pebble_pattern", 2, "borders"),
                ("pebble_pattern", 3, "cell_random")],
               [("dome_mix", 0, "height"), ("stone_random", 0, "stone_random")], catalog)
    group_into_subgraph(g, ["colorize_0", "DryStoneColor"], "stone_color", "Stone Color",
                         [("colorize_0", "gradient", "param0", "Wet color"),
                          ("DryStoneColor", "gradient", "param1", "Dry color")],
                         catalog)
    tidy_ports(g, "stone_color", [("stone_profile", 1, "stone_random")],
               [("colorize_0", 0, "wet_albedo"), ("DryStoneColor", 0, "dry_albedo")], catalog)
    group_into_subgraph(g, ["colorize_1", "colorize_2", "colorize_damp",
                             "perlin_patch", "colorize_patch", "blend_patch"],
                         "material_finish", "Wet Finish",
                         [("colorize_2", "gradient", "param0", "Wet crevice roughness"),
                          ("colorize_damp", "gradient", "param1", "Damp patch roughness"),
                          ("perlin_patch", "scale_x", "param2", "Wet patch scale")],
                         catalog)
    link_also(g, "material_finish", "param2", "perlin_patch", "scale_y")
    tidy_ports(g, "material_finish",
               [("pebble_pattern", 0, "noise"), ("stone_profile", 0, "height")],
               [("colorize_1", 0, "metallic"), ("blend_patch", 0, "roughness")], catalog)
    group_into_subgraph(g, ["Dryness", "DryColorComposite", "DryStoneRoughness",
                             "DrySeamRoughness", "DryRoughnessMix", "DryRoughnessComposite"],
                         "dry_layer", "Dry Layer",
                         [("Dryness", "color", "param0", "Dryness"),
                          ("DryStoneRoughness", "gradient", "param1", "Dry stone roughness"),
                          ("DrySeamRoughness", "gradient", "param2", "Dry seam roughness")],
                         catalog)
    tidy_ports(g, "dry_layer",
               [("stone_color", 0, "wet_albedo"), ("stone_color", 1, "dry_albedo"),
                ("material_finish", 1, "wet_roughness"), ("pebble_pattern", 0, "noise"),
                ("stone_profile", 0, "height")],
               [("DryColorComposite", 0, "albedo"), ("DryRoughnessComposite", 0, "roughness")],
               catalog)
    group_into_subgraph(g, ["GrainNoise", "GrainContrast", "GrainAmount", "GrainColorComposite",
                             "GrainWeight", "GrainHeight", "GrainReliefHeight"],
                         "surface_grain", "Surface Grain",
                         [("GrainAmount", "color", "param0", "Grain amount"),
                          ("GrainNoise", "scale_x", "param1", "Grain scale")],
                         catalog)
    link_also(g, "surface_grain", "param1", "GrainNoise", "scale_y")
    tidy_ports(g, "surface_grain",
               [("dry_layer", 0, "albedo"), ("stone_profile", 0, "height")],
               [("GrainColorComposite", 0, "albedo"), ("GrainReliefHeight", 0, "height")],
               catalog)
    group_into_subgraph(g, ["ContactEdges", "GapDepth", "ContactMask", "GapShade",
                             "ContactColorComposite", "ContactHeightKeep", "ContactHeight"],
                         "contact_gaps", "Contact Gaps",
                         [("GapDepth", "color", "param0", "Gap depth")],
                         catalog)
    tidy_ports(g, "contact_gaps",
               [("pebble_pattern", 2, "borders"), ("surface_grain", 0, "albedo"),
                ("surface_grain", 1, "height")],
               [("ContactColorComposite", 0, "albedo"), ("ContactHeight", 0, "height")],
               catalog)
    group_into_subgraph(g, ["BedLevel", "BedDepth", "BedRamp", "BedMask", "BedColor", "BedRoughness",
                             "BedColorComposite", "BedRoughnessComposite", "BedFill", "BedHeight"],
                         "sediment_bed", "Sediment Bed",
                         [("BedLevel", "color", "param0", "Bed level"),
                          ("BedColor", "gradient", "param1", "Bed color"),
                          ("BedRoughness", "gradient", "param2", "Bed roughness")],
                         catalog)
    tidy_ports(g, "sediment_bed",
               [("pebble_pattern", 0, "noise"), ("contact_gaps", 0, "albedo"),
                ("dry_layer", 1, "roughness"), ("contact_gaps", 1, "height")],
               [("BedColorComposite", 0, "albedo"), ("BedRoughnessComposite", 0, "roughness"),
                ("BedHeight", 0, "height")],
               catalog)
    group_into_subgraph(g, ["normal_map_0"], "relief", "Relief",
                         [("normal_map_0", "param1", "param0", "Relief strength")],
                         catalog)
    tidy_ports(g, "relief", [("sediment_bed", 2, "height")],
               [("normal_map_0", 0, "normal")], catalog)

    # Inner canvases: park the proxies group_into_subgraph centres on the
    # members at the edges, clear of the hand-placed nodes.
    place(node(g, "pebble_pattern"), {
        "gen_inputs": (-250, 250), "gen_parameters": (-250, 450), "gen_outputs": (600, 380)})
    place(node(g, "stone_profile"), {
        "gen_inputs": (-1050, -250), "gen_parameters": (-1050, 150), "gen_outputs": (1800, 0)})
    place(node(g, "stone_color"), {
        "gen_inputs": (-350, 100), "gen_parameters": (-350, 350), "gen_outputs": (350, 100)})
    place(node(g, "material_finish"), {
        "gen_inputs": (-300, -250), "gen_parameters": (-300, 450), "gen_outputs": (850, 0)})
    place(node(g, "dry_layer"), {
        "gen_inputs": (-400, 0), "gen_parameters": (-400, 450), "gen_outputs": (900, 100)})
    place(node(g, "surface_grain"), {
        "gen_inputs": (-350, -150), "gen_parameters": (-350, 300), "gen_outputs": (1050, 0)})
    place(node(g, "contact_gaps"), {
        "gen_inputs": (-350, 0), "gen_parameters": (-350, 300), "gen_outputs": (1050, 50)})
    place(node(g, "sediment_bed"), {
        "gen_inputs": (-350, 100), "gen_parameters": (-350, 450), "gen_outputs": (1550, 50)})
    # Top level reads as a layer stack, left to right into Material. The
    # collapsed nodes carry seed_int 0, so moving them moves no seeds.
    place(g, {
        "pebble_pattern": (-900, 0), "stone_profile": (-600, 0),
        "stone_color": (-300, -200), "material_finish": (-300, 250),
        "dry_layer": (0, 0), "surface_grain": (300, 0), "contact_gaps": (600, 0),
        "sediment_bed": (900, 0), "relief": (1200, 150), "Material": (1500, 0),
    })
    rename_nodes(g, _S14_NAMES)
    return save_variant(g, _LABEL, "s14_wet_river_stone", 1)


_S14_WET_COLOR = [
    (0.0,  0.05, 0.05, 0.05),   # near-black wet slate
    (0.28, 0.10, 0.08, 0.07),   # dark wet brown
    (0.52, 0.14, 0.13, 0.12),   # dark warm gray
    (0.74, 0.09, 0.10, 0.11),   # dark cool blue-gray
    (1.0,  0.06, 0.05, 0.05),   # near-black
]
# s06_river_pebbles' dry daylight palette: the Dry Layer's target colour.
_S06_DRY_COLOR = [
    (0.0,  0.18, 0.17, 0.16),   # dark slate pebble
    (0.28, 0.34, 0.30, 0.26),   # brown-gray
    (0.52, 0.52, 0.48, 0.42),   # warm tan
    (0.74, 0.44, 0.45, 0.47),   # cool blue-gray
    (1.0,  0.30, 0.27, 0.24),   # dark brown
]
# s06's grain-into-relief weight (GrainHeight = grain * 0.15 at Grain amount 1).
_GRAIN_HEIGHT = 0.15
# Sediment bed edge: BedMask = smoothstep(clamp((level - height) * 4)), so the sand
# fades in over the quarter of the height range just below the bed level,
# close to s04's soft stone edge (its mask ramps over F1 0.30-0.42).
_BED_EDGE = 4
# The dome reaches zero where cos(2.6 * A) = 0, i.e. A = pi / 5.2 = 0.604;
# Packing's plate input is (0.604 - border distance), zero ON the border.
_PLATE_EDGE = math.pi / 5.2

_S14_NAMES = {
    "voronoi_0": "PebbleCells",
    "perlin_0": "SurfaceNoise",
    "blend_0": "PebbleBlendUnused",
    "colorize_0": "WetStoneColor",
    "colorize_1": "NonMetallic",
    "colorize_2": "WetRoughness",
    "colorize_damp": "DampPatchRoughness",
    "perlin_patch": "PatchNoise",
    "colorize_patch": "PatchMask",
    "blend_patch": "RoughnessPatchComposite",
    "dome_curve": "DomeCurve",
    "dome_flatten": "DomeFlatten",
    "dome_smooth": "DomeSmooth",
    "voronoi_fine": "SmallStoneCells",
    "dome_curve_f": "SmallDomeCurve",
    "dome_flatten_f": "SmallDomeFlatten",
    "dome_smooth_f": "SmallDomeSmooth",
    "dome_fine_low": "SmallStoneHeight",
    "dome_mix": "StoneHeightMix",
    "sel_fine": "SmallStoneMask",
    "stone_random": "StoneRandomMix",
    "normal_map_0": "PebbleNormal",
    "plate_distance": "PlateDistance",
    "shape_delta": "ShapeDelta",
    "packing_offset": "PackingOffset",
    "dome_input": "DomeInput",
}


BUILDERS = {
    "s02_gray_granite": build_s02_gray_granite,
    "s05_hex_stone_tile": build_s05_hex_stone_tile,
    "s07_cobblestone": build_s07_cobblestone,
    "s09_ashlar_wall": build_s09_ashlar_wall,
    "s11_marble": build_s11_marble,
    "s12_eroded_sandstone": build_s12_eroded_sandstone,
    "s13_polished_marble": build_s13_polished_marble,
    "s14_wet_river_stone": build_s14_wet_river_stone,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    # Loaded once per script run (not once per builder), same convention as
    # cookbook_leather.py/cookbook_fabrics.py -- all 8 materials need it for
    # group_into_subgraph.
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
