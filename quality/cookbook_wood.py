"""Cookbook growth: wood-category authoring recipes beyond the frozen 15-case
Phase 3 test set (`w01_oak_planks`/`w02_weathered_barn_wood` are frozen there
already -- see docs/evidence/phase3/test_set.json's freeze note; this is additive, not an
edit to those cases). Informal: 1 variant per material, no scorecard gate.
Reuses author_helpers.py's graph-surgery helpers; outputs land under
quality/authored/cookbook-wood/<case>/v1.ptex, same layout convention as the
Phase 3 iterations.

Run: python -m quality.cookbook_wood
Then `python -m quality.render_cookbook` renders each variant for inspection.
"""
import sys

from quality.author_helpers import (load_example, set_gradient, set_param, add_node, rewire,
                             save_variant, _grad, group_into_subgraph, rename_nodes,
                             retype, drop_conn)

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

# KNOWN ISSUE (flagged 2026-09-14, not fixed here): the shared `wood` donor
# wires its GrainMask blend straight into Material's metallic port instead of
# a near-zero scalar, producing a spatially-varying (~0.04-0.58) metallic
# channel identically in w04_driftwood_gray, w05_dark_walnut, and
# w06_burled_wood. Tracked as follow-up task_21359777 and in HANDOFF.md; the
# fix is a drop_conn + set_param(Material, "metallic", 0) across all three
# builders (same pattern already used for cookbook_terrain.py's t01 fix).

_LABEL = "cookbook-wood"

# Worked mapping for the `wooden_floor` donor (used by w03) and the paint
# overlay w03 adds. See docs/AUTHORING.md and the 2026-09-06 role-naming
# convention.
_WOODEN_FLOOR_NAMES = {
    "bricks_0": "PlankLayout",          # rows x columns of planks with mortar gaps
    "perlin_0": "GrainNoise",           # the grain field
    "decompose_0": "PlankUVSplit",      # per-plank random -> x/y offsets
    "transform_1": "PerPlankGrainOffset",
    "colorize_0": "WoodColor",          # albedo ramp painted over the plank mask
    "blend_0": "GrainOverPlanks",       # grain multiplied over the coloured planks
    "uniform_0": "NonMetallic",         # flat black into the metallic port
    "combine_0": "CombineUnused",       # dead in the donor (no consumer)
    "normal_map_0": "PlankNormal",
}
_PAINT_OVERLAY_NAMES = {
    "perlin_pm": "WearNoise",
    "colorize_pm": "PaintMask",         # hard 0/1 mask, blend port 2
    "paint_alb": "PaintColor",
    "paint_rgh": "PaintRoughness",
    "blend_alb": "AlbedoComposite",
    "blend_rgh": "RoughnessComposite",
}

# Worked mapping for the `wood` donor (w04, w05; also the base of the
# Phase-3 barn wood). colorize_2 is albedo, colorize_0 is roughness,
# blend_0 is the grain mask feeding four consumers, the three perlins and
# the voronoi ring pattern plus its colorize and the two warps build the
# grain (docs/AUTHORING.md's wood lever).
_WOOD_NAMES = {
    "perlin_0": "GrainNoiseFine",
    "perlin_1": "GrainNoiseCoarse",
    "perlin_2": "GrainWobble",
    "voronoi_0": "RingPattern",
    "colorize_1": "RingContrast",
    "warp_0": "GrainWarp",
    "warp_1": "RingWarp",
    "blend_0": "GrainMask",
    "colorize_2": "WoodColor",
    "colorize_0": "GrainRoughness",
    "normal_map_0": "GrainNormal",
}


def build_w03_painted_wood_siding(catalog: dict) -> str:
    """Painted plank siding, paint worn off in patches to reveal the boards.
    CLONE `wooden_floor` (NOT `wood`), because siding needs visible BOARD
    STRUCTURE to read as siding at all -- wooden_floor's `bricks_0` (10 rows,
    1 column) gives horizontal planks with mortar-line gaps, and its
    `blend_0` output already carries plank albedo + relief. Then composite a
    weathered off-white paint coat over `blend_0` through an irregular
    perlin-threshold mask (same masked-composite lever as
    combo01_rusted_painted_steel), so where paint is worn the real boards
    show through. The plank normal from wooden_floor is left untouched, so
    the board seams stay physically present under both paint and bare wood.

    History (three donors, this is the fourth pass): the first three versions
    cloned `wood` (pure vertical grain, NO board structure) and read as
    abstract cow-hide / paint-splatter blobs no matter how the mask was
    tuned, because nothing in `wood` says "boards." (Along the way, a
    razor-thin mask threshold + a stark white-vs-dark-grain palette also
    produced visible `blend`-edge speckle -- see the s05/`blend` opacity
    note in AUTHORING.md; widening the band fixed that but not the
    doesn't-read-as-siding problem.) Grayson flagged the wood-donor version
    as "something's not quite right." The real fix was the DONOR, not the
    mask: on a planked base it reads as painted siding immediately. Paint
    kept a warm off-white (not pure white, which looked like missing
    texture) and the exposed wood warmed up so the worn boards read as
    natural timber."""
    g = load_example("wooden_floor")
    # Warm the exposed plank wood (wooden_floor's default is a dark, oddly
    # cool reddish ramp) so where paint has worn off it reads as real timber.
    set_gradient(g, "colorize_0", [
        (0.0, 0.16, 0.10, 0.05),    # dark grain line between/along boards
        (0.15, 0.42, 0.28, 0.15),   # mid plank wood
        (1.0, 0.55, 0.38, 0.22),    # lighter plank face
    ])
    # Paint-over composite: weathered off-white coat, worn away by a mask.
    add_node(g, "perlin_pm", "perlin", {"scale_x": 12, "scale_y": 9, "iterations": 4})
    add_node(g, "colorize_pm", "colorize",
             {"gradient": _grad([(0.55, 0, 0, 0), (0.72, 1, 1, 1)])})
    add_node(g, "paint_alb", "colorize",
             {"gradient": _grad([(0.0, 0.84, 0.83, 0.79), (1.0, 0.94, 0.93, 0.89)])})
    add_node(g, "paint_rgh", "colorize",
             {"gradient": _grad([(0.0, 0.40, 0.40, 0.40), (1.0, 0.44, 0.44, 0.44)])})
    add_node(g, "blend_alb", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "blend_rgh", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "perlin_pm", "from_port": 0, "to": "colorize_pm", "to_port": 0},
        {"from": "perlin_pm", "from_port": 0, "to": "paint_alb", "to_port": 0},
        {"from": "perlin_pm", "from_port": 0, "to": "paint_rgh", "to_port": 0},
        {"from": "blend_0", "from_port": 0, "to": "blend_alb", "to_port": 0},   # bare planks
        {"from": "paint_alb", "from_port": 0, "to": "blend_alb", "to_port": 1},
        {"from": "colorize_pm", "from_port": 0, "to": "blend_alb", "to_port": 2},
        {"from": "blend_0", "from_port": 0, "to": "blend_rgh", "to_port": 0},
        {"from": "paint_rgh", "from_port": 0, "to": "blend_rgh", "to_port": 1},
        {"from": "colorize_pm", "from_port": 0, "to": "blend_rgh", "to_port": 2},
    ]
    rewire(g, "Material", 0, "blend_alb", 0)   # albedo <- paint-over-planks
    rewire(g, "Material", 2, "blend_rgh", 0)   # roughness <- paint-over-planks

    # Group the 16-node tangle (10 from the wooden_floor donor + 6 for the
    # paint-over composite) into two named subgraphs: the bare-plank
    # generation chain (structure + AO + the plank normal, which the
    # docstring notes is deliberately left untouched by paint) and the
    # paint-coat-over-planks composite. normal_map_0 reads the plank relief
    # from blend_0 and feeds Material's normal port directly -- it belongs
    # with board_structure (it IS the plank's own relief, unaffected by
    # paint) rather than with the paint chain. combine_0 is dead code
    # inherited from the wooden_floor donor (no downstream connection,
    # confirmed by inspecting the built graph) -- folded into
    # board_structure with its source uniform_0 rather than left as an
    # orphaned top-level node, same precedent as gl01_frosted_glass's dead
    # colorize_3.
    group_into_subgraph(
        g,
        ["bricks_0", "decompose_0", "transform_1", "perlin_0", "colorize_0",
         "blend_0", "uniform_0", "combine_0", "normal_map_0"],
        "board_structure", "Board Structure",
        [("colorize_0", "gradient", "param0", "Wood color")],
        catalog,
    )
    group_into_subgraph(
        g,
        ["perlin_pm", "colorize_pm", "paint_alb", "paint_rgh", "blend_alb", "blend_rgh"],
        "paint_overlay", "Paint Overlay",
        [("paint_alb", "gradient", "param0", "Paint color"),
         ("perlin_pm", "scale_x", "param1", "Wear grain size"),
         ("colorize_pm", "gradient", "param2", "Wear coverage")],
        catalog,
    )
    rename_nodes(g, {**_WOODEN_FLOOR_NAMES, **_PAINT_OVERLAY_NAMES})
    return save_variant(g, _LABEL, "w03_painted_wood_siding", 1)


def build_w04_driftwood_gray(catalog: dict) -> str:
    """Bleached coastal driftwood: pale silvery-gray, low saturation, smoothed
    by weathering rather than rough like barn wood. Pure recolor of `wood`'s
    already-working albedo/roughness ramps (same lever as w02 barn wood) --
    no structural change, since wood's relief chain already renders real
    grain relief out of the box."""
    g = load_example("wood")
    set_gradient(g, "colorize_2", [    # bleached silvery-gray, low saturation
        (0.0, 0.52, 0.51, 0.49),
        (0.5, 0.66, 0.65, 0.63),
        (1.0, 0.42, 0.41, 0.40),
    ])
    set_gradient(g, "colorize_0", [    # weather-smoothed, moderate roughness
        (0.0, 0.55, 0.55, 0.55), (1.0, 0.72, 0.72, 0.72)])

    # Group `wood`'s 11-node graph into two named subgraphs: the noise/
    # pattern generator that produces the grain mask (blend_0's output) plus
    # the albedo colorize that paints it (colorize_2 -- both this builder's
    # explicit gradient calls sit at a colorize node, so colorize_2's
    # "Wood color" knob lives with the generator that feeds it), and the two
    # remaining surface-mapping nodes (roughness ramp + relief). blend_0
    # feeds 4 consumers (normal_map_0, colorize_0, colorize_2, and Material
    # port 1 directly); colorize_2 rides along with it into wood_grain so
    # that group carries a real knob rather than exposing nothing, while
    # surface_finish keeps its own knob (colorize_0's roughness gradient).
    group_into_subgraph(
        g,
        ["perlin_0", "perlin_1", "perlin_2", "voronoi_0", "colorize_1",
         "warp_0", "warp_1", "blend_0", "colorize_2"],
        "wood_grain", "Wood Grain",
        [("colorize_2", "gradient", "param0", "Wood color")],
        catalog,
    )
    group_into_subgraph(
        g,
        ["colorize_0", "normal_map_0"],
        "surface_finish", "Surface Finish",
        [("colorize_0", "gradient", "param0", "Finish sheen")],
        catalog,
    )
    rename_nodes(g, _WOOD_NAMES)
    return save_variant(g, _LABEL, "w04_driftwood_gray", 1)


def build_w05_dark_walnut(catalog: dict) -> str:
    """Rich dark walnut, semi-gloss furniture finish: deep saturated brown
    grain with more contrast than oak, lower roughness than barn wood (a
    finished/sealed surface, not raw weathered timber). Pure recolor of
    `wood`'s working chain, same lever as w04/w02."""
    g = load_example("wood")
    set_gradient(g, "colorize_2", [    # deep walnut brown, dark grain lines
        (0.0, 0.12, 0.07, 0.04),
        (0.5, 0.28, 0.16, 0.09),
        (1.0, 0.40, 0.24, 0.14),
    ])
    set_gradient(g, "colorize_0", [    # semi-gloss, sealed finish
        (0.0, 0.18, 0.18, 0.18), (1.0, 0.34, 0.34, 0.34)])

    # Same grouping as w04_driftwood_gray (both clone `wood`'s identical
    # 11-node graph, differing only in the two gradients this builder sets)
    # -- see that function's comment for why colorize_2 rides into wood_grain
    # alongside blend_0.
    group_into_subgraph(
        g,
        ["perlin_0", "perlin_1", "perlin_2", "voronoi_0", "colorize_1",
         "warp_0", "warp_1", "blend_0", "colorize_2"],
        "wood_grain", "Wood Grain",
        [("colorize_2", "gradient", "param0", "Wood color")],
        catalog,
    )
    group_into_subgraph(
        g,
        ["colorize_0", "normal_map_0"],
        "surface_finish", "Surface Finish",
        [("colorize_0", "gradient", "param0", "Finish sheen")],
        catalog,
    )
    rename_nodes(g, _WOOD_NAMES)
    return save_variant(g, _LABEL, "w05_dark_walnut", 1)


# Naming for w06_burled_wood: same `wood` donor as w04/w05, but the
# voronoi_0/colorize_1 ring-pattern chain is REMOVED (not folded in as dead
# code like w03's combine_0 -- that was inherited from a donor, this dead
# code would be introduced BY this edit, so it is deleted outright) and a
# new low-frequency perlin (`perlin_3`) is added as the swirl displacement
# feeding the retyped warp2 node. warp_1 keeps its position in the chain but
# its role changes from "RingWarp" to "BurlSwirl".
_WOOD_BURL_NAMES = {
    "perlin_0": "GrainNoiseFine",
    "perlin_1": "GrainNoiseCoarse",
    "perlin_2": "GrainWobble",
    "perlin_3": "SwirlField",
    "warp_0": "GrainWarp",
    "warp_1": "BurlSwirl",
    "blend_0": "GrainMask",
    "colorize_2": "WoodColor",
    "colorize_0": "GrainRoughness",
    "normal_map_0": "GrainNormal",
}


def build_w06_burled_wood(catalog: dict) -> str:
    """Burled wood: rich walnut-burl palette, broad SWIRLING/knotted figure
    instead of the straight parallel grain w04/w05's unmodified `wood` chain
    already produces. Clones `wood` (same donor as w04/w05) and retypes
    `warp_1` -- the donor's SECOND warp in the `wood_grain` chain, which in
    the unmodified donor distorts the grain field by a thresholded voronoi
    ring pattern (`RingWarp`, growth-ring/cathedral figure) -- to `warp2`.

    `warp2` is a Distortion-vocabulary Transform node (MM's own `tree_item`
    taxonomy: "warp" -> "Transform/Warp"), NOT one of the noise/pattern
    generator nodes `quality/node_usage_audit.py`'s `_NOISE_PATTERN_NODES`
    list counts -- so this material does not move that script's coverage
    numbers, unlike every other material this round. Noted here so a future
    reader checking the audit for `warp2` usage does not conclude it is
    unused.

    The donor's `voronoi_0` -> `colorize_1` ring-pattern chain (the
    displacement `warp_1` used before this edit) is deleted outright rather
    than folded into a subgraph as `*Unused`, the way w03's inherited
    `combine_0` and the cookbook's other donor-dead-code cases are handled
    (that remains the dominant convention here, see e.g. `cookbook_metal.py`,
    `cookbook_painted_metal.py`, `cookbook_stone.py`). This builder's case is
    a local deviation, not a rule: the pair becomes dead code only because of
    this specific edit (it did not arrive dead with the donor), so deleting
    it felt like the more honest choice for this one node pair, not a
    project-wide policy that dead code introduced by an edit must always be
    deleted. In its place, a new low-frequency `perlin`
    (`perlin_3`, scale_x=scale_y=2 -- roughly isotropic and an order of
    magnitude coarser than `GrainNoiseFine`'s scale_x=32) feeds `warp2`'s
    port-1 displacement input, producing broad, roughly circular swirls
    instead of voronoi's cell-boundary rings.

    `warp2`'s `amount` (verified range 0..1 via describe_node, unlike
    `warp`'s unbounded `amount` -- `debug_swatches.py::build_swatch_warp2`'s
    0.3 is well below `warp`'s own 1.0-amount swatch) is pushed to 0.65: high
    enough that the swirl dominates the underlying grain (a lower value
    tested during iteration read as only a subtle wobble, closer to
    `warp_0`'s existing wave than a distinct burl figure), but short of the
    0.9-1.0 range where the field started folding into illegible noise.

    Palette: richer contrast than w05's dark walnut, with a near-black
    "burl eye" low point and a warm honey-brown high point so the swirl
    pattern itself reads as figure, not just a recolor. Same semi-gloss
    roughness ramp as w05 (a finished/sealed furniture surface, not raw
    timber)."""
    g = load_example("wood")

    # Remove the ring-pattern displacement this builder replaces, then the
    # now-orphaned generator chain that fed it (see docstring).
    drop_conn(g, "warp_1", 1)
    drop_conn(g, "colorize_1", 0)
    g["nodes"] = [n for n in g["nodes"] if n["name"] not in ("voronoi_0", "colorize_1")]

    # New low-frequency displacement field for the burl swirl.
    add_node(g, "perlin_3", "perlin",
             {"scale_x": 2, "scale_y": 2, "iterations": 3, "persistence": 0.5})
    g["connections"].append(
        {"from": "perlin_3", "from_port": 0, "to": "warp_1", "to_port": 1})
    retype(g, "warp_1", "warp2", {"mode": 0, "amount": 0.65})

    set_gradient(g, "colorize_2", [    # walnut-burl: near-black eye to honey-brown streak
        (0.0, 0.08, 0.05, 0.03),
        (0.3, 0.22, 0.12, 0.06),
        (0.55, 0.42, 0.24, 0.12),
        (0.8, 0.30, 0.16, 0.08),
        (1.0, 0.15, 0.08, 0.04),
    ])
    set_gradient(g, "colorize_0", [    # semi-gloss, sealed finish (same as w05)
        (0.0, 0.18, 0.18, 0.18), (1.0, 0.34, 0.34, 0.34)])

    # Same two-subgraph split as w04/w05, minus the removed voronoi/colorize_1
    # pair, plus the new perlin_3 swirl-displacement node.
    group_into_subgraph(
        g,
        ["perlin_0", "perlin_1", "perlin_2", "perlin_3",
         "warp_0", "warp_1", "blend_0", "colorize_2"],
        "wood_grain", "Wood Grain",
        [("colorize_2", "gradient", "param0", "Wood color")],
        catalog,
    )
    group_into_subgraph(
        g,
        ["colorize_0", "normal_map_0"],
        "surface_finish", "Surface Finish",
        [("colorize_0", "gradient", "param0", "Finish sheen")],
        catalog,
    )
    rename_nodes(g, _WOOD_BURL_NAMES)
    return save_variant(g, _LABEL, "w06_burled_wood", 1)


BUILDERS = {
    "w03_painted_wood_siding": build_w03_painted_wood_siding,
    "w04_driftwood_gray": build_w04_driftwood_gray,
    "w05_dark_walnut": build_w05_dark_walnut,
    "w06_burled_wood": build_w06_burled_wood,
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
