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
                    add_node, rewire, drop_conn, node, _grad, group_into_subgraph)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-painted-metal"


def _group_rock_family(g, catalog, *, pattern_name, pattern_label, density_label,
                        finish_roughness_label, relief_label):
    """Shared grouping for pm01/pm02/pm04: all three clone `rock` and keep
    its identical voronoi->warp->normal chain untouched structurally (only
    scale/gradient/param values differ). All three also carry `rock`'s own
    `blend_0` node, which is NOT a paint-over-metal composite (that pattern
    is pm03's) -- it is the donor's own noise-mix step, combining two
    channels of `voronoi_0` through a `perlin_0`-driven mask, entirely
    untouched by any of these three builders. Per the task's blend caution,
    its port sources were traced from each material's serialized
    connections before grouping:
      pm01/pm04: port0 <- voronoi_0:0, port1 <- voronoi_0:1,
                 port2(mask) <- perlin_0:0, output -> colorize_0 (albedo).
      pm02:      same port0/1/2 sources, but colorize_0 was rewired to read
                 voronoi_0:2 directly instead, so blend_0's output feeds
                 NOTHING (a harmless dead end, not a wiring bug introduced
                 here -- see build_pm02_automotive_enamel's docstring).
    In every case all three of blend_0's inputs (voronoi_0, perlin_0) are
    placed in the SAME group as blend_0 itself, so port0/port1/port2 are
    all internal to the collapsed subgraph -- only blend_0's single output
    edge crosses the group boundary, which is the safe shape the caution
    is about (no partial-input grouping that could straddle a mask
    boundary)."""
    group_into_subgraph(
        g, ["voronoi_0", "voronoi_1", "warp_0", "perlin_0", "perlin_1", "blend_0",
            "colorize_0"],
        pattern_name, pattern_label,
        [("colorize_0", "gradient", "param0", "Paint color"),
         ("voronoi_0", "scale_x", "param1", density_label)],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_1", "colorize_2", "normal_map_0"], "surface_finish",
        "Surface Finish",
        [("colorize_2", "gradient", "param0", finish_roughness_label),
         ("normal_map_0", "param1", "param1", relief_label)],
        catalog,
    )


def build_pm01_powder_coat(catalog: dict) -> str:
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

    _group_rock_family(
        g, catalog, pattern_name="orange_peel_pattern",
        pattern_label="Orange Peel Pattern", density_label="Peel density",
        finish_roughness_label="Roughness", relief_label="Relief strength",
    )
    return save_variant(g, _LABEL, "pm01_powder_coat", 1)


def build_pm02_automotive_enamel(catalog: dict) -> str:
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

    # rewire() above redirected colorize_0's albedo source from blend_0's
    # output to voronoi_0:2 directly, so blend_0 (still present, still
    # carrying rock's own voronoi_0/perlin_0-driven mix) now feeds nothing
    # at all -- a harmless dead end, not introduced by this retrofit. It
    # still rides into the pattern group below with its full port0/port1/
    # port2 sources internal (see _group_rock_family's docstring).
    _group_rock_family(
        g, catalog, pattern_name="flake_pattern", pattern_label="Flake Pattern",
        density_label="Fleck density", finish_roughness_label="Clearcoat gloss",
        relief_label="Coat smoothness",
    )
    return save_variant(g, _LABEL, "pm02_automotive_enamel", 1)


def build_pm03_chipped_paint(catalog: dict) -> str:
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

    # This is the material the task's blend caution is specifically about.
    # THREE blend nodes exist here; every one had its port0/port1/port2
    # sources traced from the serialized connections before deciding a
    # grouping (not assumed from the docstring/comments above, which
    # predate this retrofit):
    #   blend_0  (donor rusted_metal's own two-tone metal mix, untouched
    #             structurally): port0 <- colorize_2 (steel base),
    #             port1 <- colorize_1 (darker steel), port2(mask)
    #             <- colorize_3 (perlin_2-driven). Output -> blend_alb:0.
    #   blend_1  (donor's second metal-layer mix, untouched structurally,
    #             constant amount=0.5, no port2 connection -> uses the
    #             node's own default mask=1.0): port0 <- colorize_4
    #             (<- colorize_3), port1 <- colorize_0 (<- perlin_0).
    #             Output -> blend_rgh:0.
    #   blend_alb/blend_rgh (the actual paint-over-metal composite, per
    #             the module docstring's PBR rule 2): port0 <- blend_0/
    #             blend_1 (bare metal side), port1 <- paint_alb/paint_rgh
    #             (paint side, the MAJORITY), port2(mask) <- mask_chip
    #             (1 only in the minority chip spots, per the pinned
    #             blend-port rule: mask=1 shows port0/metal, mask=0 shows
    #             port1/paint).
    #
    # bare_metal_base groups blend_0 AND blend_1 together with every one of
    # their port0/port1/port2 sources (colorize_0-4, perlin_0-2), so both
    # blends are fully self-contained -- only their single output edges
    # (-> blend_alb:0, -> blend_rgh:0) cross the group boundary. chip_mask
    # and paint_layer each hold one side of the paint/metal composite's
    # remaining two inputs. paint_metal_composite then holds blend_alb and
    # blend_rgh themselves, with ALL THREE of each one's inputs external
    # (from bare_metal_base, paint_layer, and chip_mask respectively) --
    # group_into_subgraph preserves each incoming connection's own to_port
    # independently, so this cannot swap which external source lands on
    # port0 vs port1 vs port2. Neither mask_chip's gradient nor the
    # perlin_chip threshold band is exposed as a friendly parameter
    # anywhere (only perlin_chip's scale and the two ALBEDO/roughness
    # paint colorizes are), so no end-user knob can touch the hard 0/1
    # mask the chip-vs-paint split depends on. Verified after building via
    # renders_match against this material's own pre-retrofit baseline
    # (see the task report), not assumed from this reasoning alone.
    group_into_subgraph(
        g, ["perlin_0", "perlin_1", "perlin_2", "colorize_0", "colorize_1",
            "colorize_2", "colorize_3", "colorize_4", "blend_0", "blend_1"],
        "bare_metal_base", "Bare Metal Base",
        [("colorize_2", "gradient", "param0", "Bare metal color"),
         ("colorize_1", "gradient", "param1", "Metal shadow tone")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_chip", "mask_chip"], "chip_mask", "Chip Mask",
        [("perlin_chip", "scale_x", "param0", "Chip pattern scale")],
        catalog,
    )
    group_into_subgraph(
        g, ["paint_alb", "paint_rgh"], "paint_layer", "Paint Layer",
        [("paint_alb", "gradient", "param0", "Paint color"),
         ("paint_rgh", "gradient", "param1", "Paint sheen")],
        catalog,
    )
    group_into_subgraph(
        g, ["blend_alb", "blend_rgh", "normal_chip"], "paint_metal_composite",
        "Paint/Metal Composite",
        [("normal_chip", "param1", "param0", "Chip edge relief")],
        catalog,
    )
    return save_variant(g, _LABEL, "pm03_chipped_paint", 1)


def build_pm04_hammertone(catalog: dict) -> str:
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

    _group_rock_family(
        g, catalog, pattern_name="hammer_dimple_pattern",
        pattern_label="Hammer Dimple Pattern", density_label="Dimple size",
        finish_roughness_label="Sheen", relief_label="Dimple depth",
    )
    return save_variant(g, _LABEL, "pm04_hammertone", 1)


def build_pm05_scuffed_panel(catalog: dict) -> str:
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

    # blend_0 here is `wood`'s own node (blend_type=2/Multiply, amount=1,
    # port2 unconnected -> uses the node's own default mask=1.0): port0
    # <- perlin_2, port1 <- perlin_2 (the rewire() above pointed BOTH
    # blend_0 inputs at the same straightened perlin, killing the donor's
    # knot-warp branch -- see the docstring above). With mask=1.0 constant,
    # blend_type=Multiply computes port0*port1 = perlin_2 squared, a real
    # (if degenerate) content transform, not a masked paint-over-metal
    # composite -- there is no "which layer is on top" question here since
    # both content inputs are the same source. Its old knot-warp inputs
    # (perlin_0, perlin_1, warp_0, voronoi_0, colorize_1, warp_1) are now a
    # dead branch with no path to Material at all (an existing donor-derived
    # quirk from the rewire, not introduced by this retrofit) -- folded into
    # the same pattern group as scuff_pattern rather than left as loose
    # top-level nodes, matching cookbook_organics.py's o03_tree_bark
    # precedent for this identical wood-donor member set.
    group_into_subgraph(
        g, ["perlin_0", "perlin_1", "warp_0", "voronoi_0", "colorize_1",
            "warp_1", "perlin_2", "blend_0", "colorize_2"],
        "scuff_pattern", "Scuff Pattern",
        [("colorize_2", "gradient", "param0", "Paint color"),
         ("perlin_2", "scale_x", "param1", "Scuff length")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_0", "normal_map_0"], "surface_finish", "Surface Finish",
        [("colorize_0", "gradient", "param0", "Roughness contrast"),
         ("normal_map_0", "param1", "param1", "Scuff depth")],
        catalog,
    )
    return save_variant(g, _LABEL, "pm05_scuffed_panel", 1)


BUILDERS = {
    "pm01_powder_coat": build_pm01_powder_coat,
    "pm02_automotive_enamel": build_pm02_automotive_enamel,
    "pm03_chipped_paint": build_pm03_chipped_paint,
    "pm04_hammertone": build_pm04_hammertone,
    "pm05_scuffed_panel": build_pm05_scuffed_panel,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    # Loaded once per script run (not once per builder), same as
    # cookbook_scifi.py/cookbook_organics.py -- all 5 materials need it for
    # group_into_subgraph.
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
