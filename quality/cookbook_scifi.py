"""Cookbook growth: sci-fi panel authoring recipes -- a category with no
frozen-set precedent at all (nearest bundled examples are metal_pattern_2/3,
which are undocumented in the frozen set or AUTHORING.md). Introduces the
`pattern` node family (x/y wave generators combined via a mix mode) as a new
lever alongside weave/voronoi/perlin/fbm. Same informal convention as
cookbook_fabrics.py / cookbook_organics.py -- 1 variant per material, no
scorecard gate. Outputs land under quality/authored/cookbook-scifi/<case>/v1.ptex.

Note: Material's `emission_tex` port (port 3) is NOT worth wiring for these
recipes -- the render pipeline's "Godot/Godot 4 Standard" export target only
produces albedo/normal/heightmap/orm, so an emission-only "glowing panel"
material would be invisible in the actual 4-map product output. Stuck to
albedo/normal/roughness/metallic effects that the render pipeline actually
captures.

Run: python quality/cookbook_scifi.py
Then: python quality/render_cookbook.py cookbook-scifi
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import (load_example, node, set_gradient, set_param, add_node,
                             rewire, save_variant, group_into_subgraph)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-scifi"


def _new_graph() -> dict:
    """Minimal valid .ptex shape for a from-scratch graph (no donor to clone).
    Matches a real Material Maker .ptex's top-level keys -- validate_graph
    only really needs nodes+connections, but this mirrors the real on-disk
    shape rather than a stripped-down guess."""
    return {"type": "graph", "name": "graph", "label": "Graph",
            "node_position": {"x": 0, "y": 0}, "parameters": {},
            "connections": [], "nodes": []}


def build_sf01_hull_plating(catalog: dict) -> str:
    """Diamond-plate hull panel: clone `metal_pattern_2` (a bundled example
    with a working grid-line normal chain, but NO albedo texture at all --
    it relies entirely on Material's flat scalar albedo_color). Graft the
    same grid pattern (blend_0's output) into a new colorize -> Material
    albedo so panel seams read as visibly darker, not just normal-lit.
    Proactive param4=0: blend_0's inputs are pattern generators (analytic),
    same directly-fed shape as every other flat-normal blocker case."""
    g = load_example("metal_pattern_2")
    add_node(g, "colorize_alb", "colorize", {})
    set_gradient(g, "colorize_alb", [
        (0.0, 0.14, 0.15, 0.17),   # dark seam
        (1.0, 0.62, 0.64, 0.68),   # light steel plate
    ])
    add_node(g, "colorize_rgh", "colorize", {})
    set_gradient(g, "colorize_rgh", [    # seams duller than plate faces
        (0.0, 0.55, 0.55, 0.55),
        (1.0, 0.30, 0.30, 0.30),
    ])
    g["connections"] += [
        {"from": "blend_0", "from_port": 0, "to": "colorize_alb", "to_port": 0},
        {"from": "colorize_alb", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "blend_0", "from_port": 0, "to": "colorize_rgh", "to_port": 0},
        {"from": "colorize_rgh", "from_port": 0, "to": "Material", "to_port": 2},
    ]
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.45)

    # metal_pattern_2's own pattern chain (pattern_0/pattern_1 -> colorize_0
    # -> transform_2 -> blend_0) is unmodified structurally, so none of those
    # nodes have an explicit builder-set value of their own; blend_0's output
    # is what colorize_alb recolors, so folding the whole donor chain into
    # the albedo group gives it an anchor (colorize_alb's explicit gradient)
    # rather than leaving a group with only untouched donor defaults.
    # blend_0 also feeds normal_map_0 and colorize_rgh outside this group --
    # the single-upstream-node-feeds-multiple-groups case the retrofit's
    # standing guidance calls out, producing extra boundary output ports on
    # blend_0's single port, which is expected.
    group_into_subgraph(
        g, ["pattern_0", "pattern_1", "colorize_0", "transform_2", "blend_0",
            "colorize_alb"],
        "panel_pattern", "Panel Pattern",
        [("colorize_alb", "gradient", "param0", "Seam color")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_rgh", "normal_map_0"], "surface_finish", "Surface Finish",
        [("colorize_rgh", "gradient", "param0", "Seam roughness contrast"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "sf01_hull_plating", 1)


def build_sf02_hazard_stripe_panel(catalog: dict) -> str:
    """Diagonal yellow/black hazard stripe panel, built fresh (no donor has
    stripes). `pattern` node: x_wave=Square for alternating bars, y_wave=
    Constant so bars run along Y before rotation. Feed through `colorize`
    FIRST (converts pattern's 'f' output to 'rgba', hard-thresholded into
    yellow/black) THEN `transform` (rotate 45) -- matches metal_pattern_2's
    own wiring order; feeding transform directly from a 'f' source is a
    port-type mismatch (transform's input is rgba)."""
    g = _new_graph()
    add_node(g, "pattern_0", "pattern",
             {"mix": 0, "x_wave": 2, "x_scale": 14, "y_wave": 4, "y_scale": 1})
    add_node(g, "colorize_0", "colorize", {})
    set_gradient(g, "colorize_0", [
        (0.0, 0.06, 0.06, 0.05),
        (0.48, 0.06, 0.06, 0.05),
        (0.52, 0.95, 0.74, 0.05),
        (1.0, 0.95, 0.74, 0.05),
    ])
    add_node(g, "transform_0", "transform",
             {"rotate": 45, "repeat": True, "scale_x": 1, "scale_y": 1,
              "translate_x": 0, "translate_y": 0})
    add_node(g, "colorize_rgh", "colorize", {})
    set_gradient(g, "colorize_rgh", [    # matte paint either color, near-flat
        (0.0, 0.62, 0.62, 0.62),
        (1.0, 0.58, 0.58, 0.58),
    ])
    add_node(g, "normal_map_0", "normal_map",
             {"param0": 10, "param1": 0.15, "param2": 0, "param4": 0})
    add_node(g, "Material", "material", {"metallic": 0})
    g["connections"] += [
        {"from": "pattern_0", "from_port": 0, "to": "colorize_rgh", "to_port": 0},
        {"from": "colorize_rgh", "from_port": 0, "to": "Material", "to_port": 2},
        {"from": "pattern_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "transform_0", "to_port": 0},
        {"from": "transform_0", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "transform_0", "from_port": 0, "to": "normal_map_0", "to_port": 0},
        {"from": "normal_map_0", "from_port": 0, "to": "Material", "to_port": 4},
    ]

    # Built from scratch, so every node here has an explicit builder value.
    # pattern_0 feeds colorize_rgh directly in addition to the stripe chain
    # below (the single-upstream-node-feeds-multiple-groups case) -- that
    # produces an extra boundary output port on pattern_0, expected.
    group_into_subgraph(
        g, ["pattern_0", "colorize_0", "transform_0"], "stripe_pattern",
        "Stripe Pattern",
        [("pattern_0", "x_scale", "param0", "Stripe count"),
         ("colorize_0", "gradient", "param1", "Stripe colors"),
         ("transform_0", "rotate", "param2", "Stripe angle")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_rgh", "normal_map_0"], "surface_finish", "Surface Finish",
        [("colorize_rgh", "gradient", "param0", "Surface sheen"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "sf02_hazard_stripe_panel", 1)


def build_sf03_circuit_board(catalog: dict) -> str:
    """PCB circuit board: dark green base, thin bright traces (fine `pattern`
    Square wave, hard-thresholded, reused as its own mask), plus a few
    brighter chip blocks on top. PARTIAL, not a clean HIT -- see the
    AUTHORING.md writeup for the two dead ends this went through and the
    real bug still unresolved (trace stripes faintly bleed through the chip
    shapes even where the mask should be fully opaque). Kept the recipe
    because "camo-patched circuit board" is a usable enough sci-fi texture,
    not because the underlying issue is understood."""
    g = _new_graph()
    add_node(g, "perlin_0", "perlin", {"scale_x": 6, "scale_y": 6, "iterations": 3})
    add_node(g, "colorize_base", "colorize", {})
    set_gradient(g, "colorize_base", [
        (0.0, 0.03, 0.10, 0.05),
        (1.0, 0.05, 0.16, 0.08),
    ])
    add_node(g, "pattern_traces", "pattern",
             {"mix": 0, "x_wave": 2, "x_scale": 28, "y_wave": 4, "y_scale": 1})
    add_node(g, "colorize_traces", "colorize", {})
    set_gradient(g, "colorize_traces", [
        (0.0, 0, 0, 0), (0.48, 0, 0, 0),
        (0.52, 0.72, 0.55, 0.20), (1.0, 0.72, 0.55, 0.20),
    ])
    # Same split-mask fix as the chips (below): colorize_traces' "on" value is
    # gold (luminance ~0.57), so reusing it as the port-2 opacity made the
    # traces only ~57% opaque and the dark base bled ~43% through them (muted
    # olive traces). A hard 0/1 mask on the SAME pattern threshold makes the
    # gold traces solid. The 0.48->0.52 band is kept (not razor-thin) because
    # the `pattern` wave IS continuous at stripe edges, so the band gives real
    # edge anti-aliasing here (unlike the flat-per-cell voronoi chip mask).
    add_node(g, "colorize_traces_mask", "colorize", {})
    set_gradient(g, "colorize_traces_mask", [
        (0.0, 0, 0, 0), (0.48, 0, 0, 0),
        (0.52, 1, 1, 1), (1.0, 1, 1, 1),
    ])
    add_node(g, "blend_traces", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "voronoi_chips", "voronoi",
             {"scale_x": 18, "scale_y": 18, "randomness": 1, "intensity": 1,
              "stretch_x": 1, "stretch_y": 1})
    add_node(g, "colorize_chips", "colorize", {})
    set_gradient(g, "colorize_chips", [    # smaller/sparser cells this time
        # near-hard step (was a 0.70->0.74 ramp): voronoi port 2 is FLAT per
        # cell, so a wide ramp doesn't anti-alias edges, it just leaves cells
        # whose random lands mid-band as faint partial chips. Same tight
        # threshold on the mask below keeps colour and opacity in lockstep.
        (0.0, 0, 0, 0), (0.735, 0, 0, 0),
        (0.74, 0.65, 0.66, 0.68), (1.0, 0.65, 0.66, 0.68),
    ])
    # ROOT-CAUSE FIX for the long-standing trace-bleed-through bug: blend's
    # opacity is `amount * a($uv)` (see blend.mmg), where `a` is the port-2
    # mask. This recipe used to feed colorize_chips (the CHIP ALBEDO, whose
    # "on" value is 0.65 gray) as that mask, so chips rendered at only ~0.65
    # opacity and ~35% of the trace stripes bled straight through them. Split
    # the mask off from the albedo: a hard 0/1 mask on the same voronoi
    # threshold drives opacity, colorize_chips still drives colour.
    add_node(g, "colorize_chips_mask", "colorize", {})
    set_gradient(g, "colorize_chips_mask", [
        (0.0, 0, 0, 0), (0.735, 0, 0, 0),
        (0.74, 1, 1, 1), (1.0, 1, 1, 1),
    ])
    add_node(g, "blend_chips", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "colorize_rgh", "colorize", {})
    set_gradient(g, "colorize_rgh", [    # traces/chips glossier than base
        (0.0, 0.55, 0.55, 0.55),
        (1.0, 0.25, 0.25, 0.25),
    ])
    add_node(g, "normal_map_0", "normal_map",
             {"param0": 10, "param1": 0.15, "param2": 0, "param4": 0})
    add_node(g, "Material", "material", {"metallic": 0.15})
    g["connections"] += [
        {"from": "perlin_0", "from_port": 0, "to": "colorize_base", "to_port": 0},
        {"from": "pattern_traces", "from_port": 0, "to": "colorize_traces", "to_port": 0},
        {"from": "pattern_traces", "from_port": 0, "to": "colorize_traces_mask", "to_port": 0},
        {"from": "colorize_traces", "from_port": 0, "to": "blend_traces", "to_port": 0},
        {"from": "colorize_base", "from_port": 0, "to": "blend_traces", "to_port": 1},
        {"from": "colorize_traces_mask", "from_port": 0, "to": "blend_traces", "to_port": 2},
        {"from": "voronoi_chips", "from_port": 2, "to": "colorize_chips", "to_port": 0},
        {"from": "voronoi_chips", "from_port": 2, "to": "colorize_chips_mask", "to_port": 0},
        {"from": "colorize_chips", "from_port": 0, "to": "blend_chips", "to_port": 0},
        {"from": "blend_traces", "from_port": 0, "to": "blend_chips", "to_port": 1},
        {"from": "colorize_chips_mask", "from_port": 0, "to": "blend_chips", "to_port": 2},
        {"from": "blend_chips", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "blend_chips", "from_port": 0, "to": "colorize_rgh", "to_port": 0},
        {"from": "colorize_rgh", "from_port": 0, "to": "Material", "to_port": 2},
        {"from": "blend_traces", "from_port": 0, "to": "normal_map_0", "to_port": 0},
        {"from": "normal_map_0", "from_port": 0, "to": "Material", "to_port": 4},
    ]

    # Grouping care for the documented blend/opacity-mask bug (see the
    # colorize_traces_mask/colorize_chips_mask comments above and
    # AUTHORING.md): `blend`'s opacity is amount * the port-2 mask, and this
    # recipe's whole fix was splitting each mask off into its OWN hard 0/1
    # colorize rather than reusing the albedo colorize as the mask. Each
    # mask colorize here has exactly ONE consumer (its own blend's port 2),
    # unlike o06's colorize_3 (a genuinely shared 3-way signal) -- so each
    # mask is grouped together with the blend it feeds and nothing else,
    # keeping the mask -> blend port-2 connection fully INTERNAL to one
    # subgraph (group_into_subgraph copies internal connections verbatim, so
    # this cannot change from/to/port). Critically, neither mask colorize's
    # gradient is exposed as a friendly parameter below -- only the ALBEDO
    # colorize's gradient is exposed in each group, so an end user turning a
    # "trace color"/"chip color" knob can never touch the hard-threshold
    # opacity mask that the bug fix depends on. Verified after building via
    # renders_match against this material's own pre-retrofit baseline (see
    # the task report) rather than assuming the general process's 0.0-diff
    # track record carries over automatically.
    group_into_subgraph(
        g, ["perlin_0", "colorize_base", "pattern_traces", "colorize_traces",
            "colorize_traces_mask", "blend_traces"],
        "circuit_traces", "Circuit Traces",
        [("colorize_base", "gradient", "param0", "Board color"),
         ("pattern_traces", "x_scale", "param1", "Trace density"),
         ("colorize_traces", "gradient", "param2", "Trace color")],
        catalog,
    )
    group_into_subgraph(
        g, ["voronoi_chips", "colorize_chips", "colorize_chips_mask", "blend_chips"],
        "chip_blocks", "Chip Blocks",
        [("voronoi_chips", "scale_x", "param0", "Chip size"),
         ("colorize_chips", "gradient", "param1", "Chip color")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_rgh", "normal_map_0"], "surface_finish", "Surface Finish",
        [("colorize_rgh", "gradient", "param0", "Surface sheen"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "sf03_circuit_board", 1)


def build_sf04_vent_grille_panel(catalog: dict) -> str:
    """Perforated square-hole vent grille: ONE `pattern` node with BOTH
    x_wave and y_wave set to Square and mix=Min gives a grid of small square
    holes in a single node (Min of two square waves = their intersection).
    Distinct from man01's hexagonal grating (beehive-based) -- this is a
    square punch pattern, a different bundled-example gap entirely."""
    g = _new_graph()
    add_node(g, "pattern_holes", "pattern",
             {"mix": 3, "x_wave": 2, "x_scale": 10, "y_wave": 2, "y_scale": 10})
    add_node(g, "colorize_0", "colorize", {})
    set_gradient(g, "colorize_0", [
        (0.0, 0.03, 0.03, 0.03),   # punched-through hole, dark
        (0.55, 0.03, 0.03, 0.03),
        (0.60, 0.58, 0.59, 0.61),  # surrounding steel
        (1.0, 0.58, 0.59, 0.61),
    ])
    add_node(g, "colorize_rgh", "colorize", {})
    set_gradient(g, "colorize_rgh", [    # holes duller (recessed grime) than plate
        (0.0, 0.65, 0.65, 0.65),
        (1.0, 0.35, 0.35, 0.35),
    ])
    add_node(g, "normal_map_0", "normal_map",
             {"param0": 10, "param1": 0.5, "param2": 0, "param4": 0})
    add_node(g, "Material", "material", {"metallic": 1})
    g["connections"] += [
        {"from": "pattern_holes", "from_port": 0, "to": "colorize_0", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "pattern_holes", "from_port": 0, "to": "colorize_rgh", "to_port": 0},
        {"from": "colorize_rgh", "from_port": 0, "to": "Material", "to_port": 2},
        {"from": "pattern_holes", "from_port": 0, "to": "normal_map_0", "to_port": 0},
        {"from": "normal_map_0", "from_port": 0, "to": "Material", "to_port": 4},
    ]

    # Built from scratch; pattern_holes feeds colorize_rgh and normal_map_0
    # directly in addition to colorize_0 below (single-upstream-node-feeds-
    # multiple-groups case), producing extra boundary output ports on
    # pattern_holes, expected.
    group_into_subgraph(
        g, ["pattern_holes", "colorize_0"], "hole_pattern", "Hole Pattern",
        [("pattern_holes", "x_scale", "param0", "Hole density"),
         ("colorize_0", "gradient", "param1", "Hole vs plate color")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_rgh", "normal_map_0"], "surface_finish", "Surface Finish",
        [("colorize_rgh", "gradient", "param0", "Recess roughness"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "sf04_vent_grille_panel", 1)


BUILDERS = {
    "sf01_hull_plating": build_sf01_hull_plating,
    "sf02_hazard_stripe_panel": build_sf02_hazard_stripe_panel,
    "sf03_circuit_board": build_sf03_circuit_board,
    "sf04_vent_grille_panel": build_sf04_vent_grille_panel,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    # Loaded once per script run (not once per builder), same as
    # cookbook_organics.py -- all 4 materials need it for group_into_subgraph.
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
