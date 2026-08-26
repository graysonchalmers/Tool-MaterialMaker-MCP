"""Cookbook growth: terrain authoring recipes -- ground/landscape materials
beyond o01 moss / o02 mud (which are already terrain-adjacent but organic-
growth focused). Same informal convention as the other cookbook_*.py files
-- 1 variant per material, no scorecard gate. Outputs land under
quality/authored/cookbook-terrain/<case>/v1.ptex.

Run: python quality/cookbook_terrain.py
Then: python quality/render_cookbook.py cookbook-terrain
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author import (load_example, node, set_gradient, set_param, retype,
                     rewire, drop_conn, add_node, save_variant)

_LABEL = "cookbook-terrain"


def build_t01_sand_dunes() -> str:
    """Sand dunes: clone `wood` UNMODIFIED structurally (like o03 bark) --
    dune ripples are organic and wavy, so KEEP the knot-warp chain rather
    than straightening it like m02 aluminum. Widen perlin_2's scale for
    broad, slow-rolling ripples instead of tight wood grain. Warm sand tan,
    high roughness. wood's own normal chain already works unmodified."""
    g = load_example("wood")
    set_param(g, "perlin_2", "scale_x", 7)
    set_param(g, "perlin_2", "scale_y", 3)
    set_param(g, "perlin_2", "iterations", 5)
    set_gradient(g, "colorize_2", [    # warm sand tan
        (0.0, 0.52, 0.40, 0.23),
        (0.5, 0.68, 0.55, 0.34),
        (1.0, 0.78, 0.65, 0.42),
    ])
    set_gradient(g, "colorize_0", [    # matte sand
        (0.0, 0.78, 0.78, 0.78),
        (1.0, 0.92, 0.92, 0.92),
    ])
    return save_variant(g, _LABEL, "t01_sand_dunes", 1)


def build_t02_fresh_snow() -> str:
    """Fresh snow: clone `rock` and KEEP its smooth blobby structure (per
    AUTHORING.md's own rule: a smooth source is fine when the target is
    genuinely near-flat -- snow drifts are exactly that case, like s02
    granite reused rock for the same reason). Recolor albedo near-white
    with a faint cold blue-gray in the low points, force near-zero
    metallic (perlin_0 feeds it directly by default, wrong for snow), keep
    roughness fairly high but not maximal (snow has a little sheen).
    Proactive param4=0 on the normal chain (rock's own warp_0->normal_map_0
    is a directly-fed analytic chain, the same shape s02 granite had to fix)
    but at LOW strength -- soft drifts, not stone-scale relief."""
    g = load_example("rock")
    set_gradient(g, "colorize_0", [    # near-white, cold shadow in the low points
        (0.0, 0.72, 0.76, 0.82),
        (0.5, 0.88, 0.90, 0.94),
        (1.0, 0.97, 0.97, 0.99),
    ])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])  # non-metal
    set_gradient(g, "colorize_2", [    # slight sheen, not max-matte
        (0.0, 0.35, 0.35, 0.35),
        (1.0, 0.55, 0.55, 0.55),
    ])
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.18)
    return save_variant(g, _LABEL, "t02_fresh_snow", 1)


def build_t03_gravel() -> str:
    """Gravel: clone `rock`, reuse s02 granite's v2 lever (voronoi port 2 =
    rand3, flat per-cell random -> albedo, bypassing the smooth blend) but
    at PEBBLE scale (14, vs granite's fine-fleck 44) and a wider earthy
    gray/tan/brown palette instead of granite's grayscale. Stronger
    param4=0 relief than granite -- loose gravel is bumpier than a
    polished slab."""
    g = load_example("rock")
    set_param(g, "voronoi_0", "scale_x", 14)
    set_param(g, "voronoi_0", "scale_y", 14)
    set_param(g, "voronoi_0", "randomness", 1)
    rewire(g, "colorize_0", 0, "voronoi_0", 2)
    set_gradient(g, "colorize_0", [    # varied gray/tan/brown pebbles
        (0.0, 0.22, 0.20, 0.17),
        (0.30, 0.42, 0.38, 0.32),
        (0.55, 0.55, 0.50, 0.42),
        (0.80, 0.35, 0.28, 0.20),
        (1.0, 0.48, 0.46, 0.44),
    ])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])
    set_gradient(g, "colorize_2", [
        (0.0, 0.55, 0.55, 0.55),
        (1.0, 0.82, 0.82, 0.82),
    ])
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.55)
    return save_variant(g, _LABEL, "t03_gravel", 1)


def build_t04_grass_field() -> str:
    """Grass field: clone rusted_metal's two-layer masked-blend structure --
    the same template o06 lichen-on-rock already proved twice now -- and
    recolor to soil+grass. Unlike lichen (sparse patches on a dominant
    base), grass should be the DOMINANT layer with dirt only showing
    through in patches.

    First attempt moved the mask threshold DOWN (0.22, by analogy with how
    o06/m01 "widen" their patch layer by lowering the threshold) expecting
    more grass coverage. Rendered almost the opposite: near-total soil with
    only tiny green flecks (checked the normal map too -- nearly flat,
    confirming the mask was saturated one way across ~all of the image, not
    a gradual shift). Reasoning about blend_type's exact mix formula and
    colorize's duplicate-point step extrapolation didn't resolve which
    direction was right for THIS specific base/patch/threshold combination,
    so the fix was empirical: flip the threshold UP instead (0.65) and
    re-render. That flip alone produced the intended dominant-grass-with-
    dirt-patches look on the first try. Lesson: don't trust threshold
    direction by analogy across cases -- render and look.

    Same metallic gotcha as lichen: drop_conn + force scalar 0. Same
    normal_map graft off the mask for grass-clump relief."""
    g = load_example("rusted_metal")
    set_gradient(g, "colorize_2", [    # base -> bare soil
        (0.0, 0.18, 0.12, 0.07),
        (1.0, 0.32, 0.23, 0.14),
    ])
    set_gradient(g, "colorize_1", [    # patch -> grass green (the dominant layer)
        (0.0, 0.10, 0.22, 0.06),
        (1.0, 0.30, 0.48, 0.14),
    ])
    set_gradient(g, "colorize_3", [(0.65, 0, 0, 0), (0.65, 1, 1, 1)])  # grass dominant
    drop_conn(g, "Material", 1)
    set_param(g, "Material", "metallic", 0)
    add_node(g, "normal_map_grass", "normal_map",
             {"param0": 9, "param1": 0.3, "param2": 0, "param4": 0})
    g["connections"].append(
        {"from": "colorize_3", "from_port": 0, "to": "normal_map_grass", "to_port": 0})
    g["connections"].append(
        {"from": "normal_map_grass", "from_port": 0, "to": "Material", "to_port": 4})
    return save_variant(g, _LABEL, "t04_grass_field", 1)


BUILDERS = {
    "t01_sand_dunes": build_t01_sand_dunes,
    "t02_fresh_snow": build_t02_fresh_snow,
    "t03_gravel": build_t03_gravel,
    "t04_grass_field": build_t04_grass_field,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
