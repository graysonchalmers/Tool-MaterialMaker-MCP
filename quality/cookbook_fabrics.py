"""Cookbook growth: fabric-category authoring recipes beyond the frozen 15-case
Phase 3 test set (see quality/test_set.json's freeze note -- this is additive,
not an edit to those cases). Informal: 1 variant per material, no scorecard
gate. Reuses author.py's graph-surgery helpers; outputs land under
quality/authored/cookbook-fabrics/<case>/v1.ptex, same layout convention as
the Phase 3 iterations.

Run: python quality/cookbook_fabrics.py
Then quality/render_cookbook.py renders each variant for inspection.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author import load_example, node, set_gradient, set_param, retype, rewire, add_node, save_variant

_LABEL = "cookbook-fabrics"


def build_f03_canvas_burlap() -> str:
    """Coarse plain-weave burlap/canvas: retype crocodile_skin's generator to
    `weave` (over/under plain weave, one output). Low width leaves visible
    gaps between thick jute threads. Natural tan, high roughness. Directly-fed
    analytic generator -> normal_map param4=0 fix, moderate strength for the
    coarse thread relief."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "weave", {"columns": 10, "rows": 10, "width": 0.62})
    set_gradient(g, "colorize_1", [    # natural tan, darker in the weave gaps
        (0.0, 0.35, 0.29, 0.19),
        (1.0, 0.68, 0.58, 0.40),
    ])
    set_gradient(g, "colorize_3", [    # matte, coarse-fiber roughness
        (0.0, 0.82, 0.82, 0.82),
        (1.0, 0.95, 0.95, 0.95),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.4, "param2": 0, "param4": 0}
    return save_variant(g, _LABEL, "f03_canvas_burlap", 1)


def build_f04_wool_knit() -> str:
    """Chunky wool knit: retype the generator to `weave` at a COARSE scale
    with near-max width (few, wide ribs, almost no gap) so it reads as thick
    blocky yarn rows rather than a fine thread grid. (Tried `weave2` with a
    stitch offset first -- it renders a crisp herringbone/basket diagonal,
    not loop softness; this catalog has no true loop-knit generator, so
    coarse+soft is the closest stand-in.) Heathered oatmeal via a 3-stop
    ramp (ply color variation), very high matte roughness. Softer normal
    strength than canvas -- meant to read as rounded ribs, not sharp
    thread crossings."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "weave", {"columns": 6, "rows": 7, "width": 0.94})
    set_gradient(g, "colorize_1", [    # heathered oatmeal wool
        (0.0, 0.55, 0.50, 0.42),
        (0.5, 0.68, 0.63, 0.54),
        (1.0, 0.50, 0.45, 0.38),
    ])
    set_gradient(g, "colorize_3", [    # very matte
        (0.0, 0.88, 0.88, 0.88),
        (1.0, 0.97, 0.97, 0.97),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.3, "param2": 0, "param4": 0}
    return save_variant(g, _LABEL, "f04_wool_knit", 1)


def build_f05_silk_satin() -> str:
    """Silk/satin: retype the generator to `diagonal_weave` at a FINE scale
    (near-invisible weave, unlike denim's coarse twill) so the differentiator
    is glossy low roughness + saturated low-contrast jewel-tone albedo, not
    visible thread texture. Normal strength kept very low -- just enough
    faint sheen-line variation to read as woven fabric, not flat plastic."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "diagonal_weave", {"size": 48})
    set_gradient(g, "colorize_1", [    # deep emerald, low-contrast for sheen
        (0.0, 0.02, 0.25, 0.15),
        (1.0, 0.10, 0.42, 0.28),
    ])
    set_gradient(g, "colorize_3", [    # glossy
        (0.0, 0.12, 0.12, 0.12),
        (1.0, 0.22, 0.22, 0.22),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.08, "param2": 0, "param4": 0}
    return save_variant(g, _LABEL, "f05_silk_satin", 1)


def build_f06_velvet() -> str:
    """Velvet: NOT a weave graft -- a soft fibrous pile has no grid pattern.
    First try was the granite speckle lever (voronoi PORT 2, flat per-cell
    random): at voronoi's max scale (32) the cells are still ~60px wide on a
    2048px render, so it read as mottled/faceted crystal, not soft fiber
    noise. Grafting a `fast_blur_shader` to soften it hit an invalid-shader
    render failure (rgb->rgba port mismatch, not worth chasing for a 1-off).
    Fix that actually works: retype the generator to `perlin` instead --
    continuous, no hard cell edges, and iterations (octaves) adds fine
    high-frequency grain on top of the base noise for a fiber-like texture.
    Deep saturated wine color, high roughness, very subtle normal (soft
    nap, not hard relief)."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "perlin",
           {"scale_x": 32, "scale_y": 32, "iterations": 8, "persistence": 0.6})
    set_gradient(g, "colorize_1", [    # deep saturated wine/crimson
        (0.0, 0.24, 0.02, 0.05),
        (1.0, 0.38, 0.05, 0.09),
    ])
    set_gradient(g, "colorize_3", [    # matte with a little sheen-catch variation
        (0.0, 0.75, 0.75, 0.75),
        (1.0, 0.90, 0.90, 0.90),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.12, "param2": 0, "param4": 0}
    return save_variant(g, _LABEL, "f06_velvet", 1)


BUILDERS = {
    "f03_canvas_burlap": build_f03_canvas_burlap,
    "f04_wool_knit": build_f04_wool_knit,
    "f05_silk_satin": build_f05_silk_satin,
    "f06_velvet": build_f06_velvet,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
