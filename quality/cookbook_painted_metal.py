"""Cookbook growth: painted-metal category authoring recipes beyond the frozen
15-case Phase 3 test set. Additive, not an edit to the frozen metals
(`m01`/`m02`/`m03` live in quality/test_set.json). Informal: 1 variant per
material, no scorecard gate. Reuses author_helpers.py's graph-surgery helpers; outputs
land under quality/authored/cookbook-painted-metal/<case>/v1.ptex.

The whole family is surface-finish, which risks five gray panels that differ
only in gloss. Each material is built around a distinct STRUCTURAL read, not
just a roughness number:
  pm01 powder coat  -> fine dense orange-peel micro-bumps, matte
  pm02 auto enamel  -> near-mirror flat, faint per-cell fleck
  pm03 chipped      -> the chip mask IS the structure; chips expose BARE metal
  pm04 hammertone   -> medium rounded dimple field (strongest structural read)
  pm05 scuffed      -> directional brushed scuffing with a clear horizontal axis

Two PBR-correctness rules baked in throughout:
  1. Metallic is a dielectric-vs-metal DECISION, never global. Paint => 0;
     only pm03's exposed bare metal is metallic 1, driven by the chip mask.
     A globally-metallic painted panel renders near-black in the preview scene.
  2. Every chip/wear mask fed to a `blend`'s port 2 is a HARD 0/1 step, never a
     mid-value albedo colorize -- a blend's opacity is `amount * port2`, so a
     mid-value mask makes the top layer semi-transparent (the sf03 bug). See
     docs/AUTHORING.md.

Normal-map note: rock/wood donors feed their normal from a directly-fed
analytic generator, so `normal_map_0.param4` must be 0 (raw edge_detect) for
real relief; the default 1 (buffered) renders flat. See f01/s02 in author.py.

Run: python quality/cookbook_painted_metal.py
Then quality/render_one.py cookbook-painted-metal <case> renders one for review.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import (load_example, set_gradient, set_param, save_variant,
                    add_node, rewire, drop_conn, node, _grad)

_LABEL = "cookbook-painted-metal"


def build_pm01_powder_coat(iter_label: str) -> list[str]:
    """Safety-yellow powder coat: matte paint with a fine, dense orange-peel
    micro-bump. CLONE rock (isotropic voronoi->warp->normal chain). Make the
    NORMAL voronoi (voronoi_1) fine and dense so the bumps read as orange-peel
    pebbling rather than rock lumps; low relief for a subtle skin, not craters.
    Flat-ish yellow albedo, metallic 0 (paint is a dielectric), matte
    roughness."""
    g = load_example("rock")
    # fine dense bump field -> orange peel (rock's default cells are big lumps).
    # rock's warp_0 (amount 0.3, coarse scale-4 perlin) smears the cells into
    # wormy ridges -- flatten it hard so the cells stay round and pebbly.
    set_param(g, "warp_0", "amount", 0.03)
    set_param(g, "voronoi_1", "scale_x", 44)
    set_param(g, "voronoi_1", "scale_y", 44)
    set_param(g, "voronoi_0", "scale_x", 44)
    set_param(g, "voronoi_0", "scale_y", 44)
    set_gradient(g, "colorize_0", [            # albedo: industrial safety yellow
        (0.0, 0.78, 0.60, 0.03),               # slightly shaded pit
        (0.5, 0.92, 0.73, 0.06),
        (1.0, 0.97, 0.80, 0.10)])              # lit bump crest
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])   # metallic 0
    set_gradient(g, "colorize_2", [            # roughness: matte
        (0.0, 0.62, 0.62, 0.62), (1.0, 0.72, 0.72, 0.72)])
    set_param(g, "normal_map_0", "param4", 0)  # raw edge_detect -> real relief
    set_param(g, "normal_map_0", "param1", 0.12)  # shallow orange-peel skin
    return [save_variant(g, iter_label, "pm01_powder_coat", 1)]


def build_pm02_automotive_enamel(iter_label: str) -> list[str]:
    """Deep automotive red enamel: near-mirror clearcoat over a faint metallic
    fleck. CLONE rock. The albedo is driven off voronoi_0's per-cell random
    (port 2 = rand3) at a fine scale so each tiny cell is a slightly different
    red -> the faint flake sparkle. Very low roughness for the mirror clearcoat,
    near-flat normal (the clearcoat is glassy, not textured), metallic 0 (the
    dielectric clearcoat dominates the surface response)."""
    g = load_example("rock")
    set_param(g, "voronoi_0", "scale_x", 60)   # very fine cells -> flake speckle
    set_param(g, "voronoi_0", "scale_y", 60)
    set_param(g, "voronoi_0", "randomness", 1)
    rewire(g, "colorize_0", 0, "voronoi_0", 2)  # albedo <- per-cell random red
    set_gradient(g, "colorize_0", [            # deep automotive red, faint spread
        (0.0, 0.28, 0.01, 0.02),
        (0.5, 0.42, 0.02, 0.03),
        (1.0, 0.55, 0.04, 0.05)])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])   # metallic 0
    set_gradient(g, "colorize_2", [            # roughness: near-mirror clearcoat
        (0.0, 0.07, 0.07, 0.07), (1.0, 0.11, 0.11, 0.11)])
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.04)  # near-flat glassy coat
    return [save_variant(g, iter_label, "pm02_automotive_enamel", 1)]


def build_pm03_chipped_paint(iter_label: str) -> list[str]:
    """Faded appliance-green paint chipped to BARE METAL (distinct from the
    frozen combo01, which chips to RUST). CLONE rusted_metal for its ready-made
    two-layer metal base, recolor that base to bare steel, then composite a flat
    green paint coat OVER it through a hard irregular chip mask:
      - chip mask: perlin thresholded to a HARD 0/1 (paint the majority, chips
        the minority worn spots);
      - paint => albedo green, roughness smooth, metallic 0;
      - bare metal (in chips) => steel albedo, rougher, metallic 1.
    Metallic is the key PBR point: it is the INVERSE of the paint mask (1 where
    metal shows, 0 under paint), NOT global. A slight relief lip is added at the
    paint/chip boundary so chips read as physically stepped, not just recolored.
    """
    g = load_example("rusted_metal")
    # recolor the donor's two metal layers to bare steel (was orange rust)
    set_gradient(g, "colorize_2", [(0.0, 0.50, 0.51, 0.53),   # base steel
                                   (1.0, 0.60, 0.61, 0.63)])
    set_gradient(g, "colorize_1", [(0.0, 0.40, 0.41, 0.43),   # darker steel tone
                                   (1.0, 0.50, 0.51, 0.53)])

    # ONE hard chip mask drives everything. Blend semantics (verified against
    # this donor by render): a blend shows port-1 where the mask is 0 and port-0
    # where the mask is 1. So paint (green) goes on port 1 as the MAJORITY, and
    # mask_chip is 1 only in the minority worn spots -> metal (port 0) shows
    # there. mask_chip=1 where perlin is LOW (< ~0.30) so chips are ~20-25%.
    add_node(g, "perlin_chip", "perlin",
             {"scale_x": 5, "scale_y": 5, "iterations": 5})
    add_node(g, "mask_chip", "colorize",        # 1 = chip (bare metal), minority
             {"gradient": _grad([(0.27, 1, 1, 1), (0.33, 0, 0, 0)])})
    add_node(g, "paint_alb", "colorize",        # flat faded appliance green
             {"gradient": _grad([(0.0, 0.28, 0.44, 0.28),
                                 (1.0, 0.34, 0.50, 0.33)])})
    add_node(g, "paint_rgh", "colorize",        # flat, smooth painted sheen
             {"gradient": _grad([(0.0, 0.34, 0.34, 0.34),
                                 (1.0, 0.36, 0.36, 0.36)])})
    add_node(g, "blend_alb", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "blend_rgh", "blend", {"blend_type": 0, "amount": 1})
    # a slight step at the chip edge: hard mask -> normal so paint sits proud
    add_node(g, "normal_chip", "normal_map",
             {"param0": 10, "param1": 0.30, "param2": 0, "param4": 0})

    g["connections"] += [
        {"from": "perlin_chip", "from_port": 0, "to": "mask_chip", "to_port": 0},
        {"from": "perlin_chip", "from_port": 0, "to": "paint_alb", "to_port": 0},
        {"from": "perlin_chip", "from_port": 0, "to": "paint_rgh", "to_port": 0},
        # albedo: metal (port 0, shows in chips) under green paint (port 1, the
        # majority), opacity = hard chip mask
        {"from": "blend_0", "from_port": 0, "to": "blend_alb", "to_port": 0},
        {"from": "paint_alb", "from_port": 0, "to": "blend_alb", "to_port": 1},
        {"from": "mask_chip", "from_port": 0, "to": "blend_alb", "to_port": 2},
        # roughness: metal roughness (blend_1:0) in chips, smooth paint elsewhere
        {"from": "blend_1", "from_port": 0, "to": "blend_rgh", "to_port": 0},
        {"from": "paint_rgh", "from_port": 0, "to": "blend_rgh", "to_port": 1},
        {"from": "mask_chip", "from_port": 0, "to": "blend_rgh", "to_port": 2},
        # chip-edge relief
        {"from": "mask_chip", "from_port": 0, "to": "normal_chip", "to_port": 0},
    ]
    rewire(g, "Material", 0, "blend_alb", 0)     # albedo <- paint-over-metal
    rewire(g, "Material", 1, "mask_chip", 0)     # metallic <- chip mask (metal=1)
    rewire(g, "Material", 2, "blend_rgh", 0)     # roughness <- paint-over-metal
    rewire(g, "Material", 4, "normal_chip", 0)   # normal <- chip-edge step
    return [save_variant(g, iter_label, "pm03_chipped_paint", 1)]


def build_pm04_hammertone(iter_label: str) -> list[str]:
    """Hammered bronze-gray 'hammertone' paint: the classic dimpled hammer-blow
    finish. CLONE rock and use its voronoi->warp->normal chain, but at a MEDIUM
    cell size so the rounded cells read as hammer dimples (bigger than pm01's
    orange peel, smaller than rock's lumps), with a deeper relief than any other
    material in this family -- the dimples are the whole point. Bronze-gray
    albedo with per-cell tonal variation so dimples catch the light; metallic 0
    (it is paint), semi-gloss roughness for the metallic-looking sheen."""
    g = load_example("rock")
    set_param(g, "voronoi_1", "scale_x", 14)   # medium dimples (the structure)
    set_param(g, "voronoi_1", "scale_y", 14)
    set_param(g, "voronoi_0", "scale_x", 14)
    set_param(g, "voronoi_0", "scale_y", 14)
    set_gradient(g, "colorize_0", [            # bronze-gray, dimples catch light
        (0.0, 0.20, 0.18, 0.14),               # dimple pit (shaded)
        (0.5, 0.34, 0.30, 0.23),
        (1.0, 0.46, 0.41, 0.31)])              # crest (lit bronze)
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])   # metallic 0
    set_gradient(g, "colorize_2", [            # semi-gloss sheen
        (0.0, 0.26, 0.26, 0.26), (1.0, 0.36, 0.36, 0.36)])
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.42)  # deep hammer dimples
    return [save_variant(g, iter_label, "pm04_hammertone", 1)]


def build_pm05_scuffed_panel(iter_label: str) -> list[str]:
    """Faded utility-blue painted panel, scuffed along a clear horizontal axis.
    CLONE wood (directional grain -> working normal chain), the same donor m02
    brushed aluminum used, but keep it PAINT: straighten the grain into parallel
    scuff streaks (feed blend_0:1 from the straight perlin_2, killing wood's
    knot warp), stretch long/fine, recolor faded blue with lighter worn streaks,
    metallic 0 (drop the grain-driven metallic map AND set the scalar to 0),
    shallow directional normal for scuffs rather than deep grain."""
    g = load_example("wood")
    rewire(g, "blend_0", 1, "perlin_2", 0)     # straighten: no knot warp
    # long, CLEAN horizontal scuffs: high scale_x/low scale_y for the axis, but
    # FEW iterations (2) so the streaks read as smooth brushed lines rather than
    # the grainy fbm noise 8 octaves produced.
    set_param(g, "perlin_2", "scale_x", 48)
    set_param(g, "perlin_2", "scale_y", 2)
    set_param(g, "perlin_2", "iterations", 2)
    set_gradient(g, "colorize_2", [            # albedo: faded utility blue + scuff
        (0.0, 0.16, 0.25, 0.36),               # base paint
        (0.55, 0.22, 0.31, 0.42),
        (1.0, 0.44, 0.51, 0.58)])              # brighter worn/scuffed streak
    set_gradient(g, "colorize_0", [            # roughness: paint, scuffs rougher
        (0.0, 0.42, 0.42, 0.42), (1.0, 0.64, 0.64, 0.64)])
    drop_conn(g, "Material", 1)                # no metallic map...
    node(g, "Material")["parameters"]["metallic"] = 0   # ...and scalar 0 (paint)
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.30)  # deeper directional scuffs
    return [save_variant(g, iter_label, "pm05_scuffed_panel", 1)]


BUILDERS = {
    "pm01_powder_coat": build_pm01_powder_coat,
    "pm02_automotive_enamel": build_pm02_automotive_enamel,
    "pm03_chipped_paint": build_pm03_chipped_paint,
    "pm04_hammertone": build_pm04_hammertone,
    "pm05_scuffed_panel": build_pm05_scuffed_panel,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        paths = BUILDERS[case](_LABEL)
        print(f"{case}: {len(paths)} variant(s)")
        for p in paths:
            print("  ", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
