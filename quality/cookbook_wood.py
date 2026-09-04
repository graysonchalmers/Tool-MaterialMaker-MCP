"""Cookbook growth: wood-category authoring recipes beyond the frozen 15-case
Phase 3 test set (`w01_oak_planks`/`w02_weathered_barn_wood` are frozen there
already -- see quality/test_set.json's freeze note; this is additive, not an
edit to those cases). Informal: 1 variant per material, no scorecard gate.
Reuses author_helpers.py's graph-surgery helpers; outputs land under
quality/authored/cookbook-wood/<case>/v1.ptex, same layout convention as the
Phase 3 iterations.

Run: python quality/cookbook_wood.py
Then quality/render_cookbook.py renders each variant for inspection.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import (load_example, set_gradient, set_param, add_node, rewire,
                             save_variant, _grad, group_into_subgraph)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-wood"


def build_w03_painted_wood_siding() -> str:
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

    catalog = build_catalog(load_config().nodes_dir)
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
    return save_variant(g, _LABEL, "w03_painted_wood_siding", 1)


def build_w04_driftwood_gray() -> str:
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
    catalog = build_catalog(load_config().nodes_dir)
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
    return save_variant(g, _LABEL, "w04_driftwood_gray", 1)


def build_w05_dark_walnut() -> str:
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
    catalog = build_catalog(load_config().nodes_dir)
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
    return save_variant(g, _LABEL, "w05_dark_walnut", 1)


BUILDERS = {
    "w03_painted_wood_siding": build_w03_painted_wood_siding,
    "w04_driftwood_gray": build_w04_driftwood_gray,
    "w05_dark_walnut": build_w05_dark_walnut,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
