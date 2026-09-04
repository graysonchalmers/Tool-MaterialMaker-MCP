"""Cookbook growth: glass authoring recipes -- the first entry authored from a
reference PHOTO rather than a text prompt, proving out the "Authoring from a
reference photo" workflow in docs/AUTHORING.md. Same informal convention as
the other cookbook_*.py files -- 1 variant per material, no scorecard gate.
Outputs land under quality/authored/cookbook-glass/<case>/v1.ptex.

Run: python quality/cookbook_glass.py
Then: python quality/render_cookbook.py cookbook-glass
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import (load_example, set_gradient, set_param, drop_conn,
                     save_variant, add_node, _grad)

_LABEL = "cookbook-glass"


def build_gl01_frosted_glass() -> str:
    """Sandblasted frosted glass, decomposed from a real macro photo (see the
    recipe card for the reference and the observation-by-observation
    reasoning). Reads as the same CONNECTED CRACK NETWORK topology as
    `dry_earth` (dense light facets separated by dark micro-crack
    boundaries), just at a far finer, denser scale than any existing
    dry_earth-derived material, so it clones `dry_earth` rather than
    inventing a new base. Cranks voronoi cell density way up for fine
    facets, tightens warp_0 for clean (not smeared) micro-joints, recolors
    to a narrow cool blue-gray range (uniform matte, not per-plate color
    variation), forces non-metal, pushes roughness high and fairly uniform
    (frosted glass is diffuse, not glossy), and keeps normal relief subtle
    (param4=0 at low param1) since real frosted glass has almost no macro
    bump -- the visible diffusion is a MICRO-surface effect this graph can
    only approximate, not simulate, logged as an honest limitation in the
    card rather than overclaimed."""
    g = load_example("dry_earth")
    set_param(g, "voronoi_0", "scale_x", 60)
    set_param(g, "voronoi_0", "scale_y", 60)
    set_param(g, "voronoi_0", "randomness", 1)
    set_gradient(g, "colorize_0", [    # narrow, uniform cool blue-gray
        (0.0, 0.60, 0.65, 0.71),
        (1.0, 0.76, 0.80, 0.86),
    ])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (0.08, 1, 1, 1)])  # tight crack ramp
    set_param(g, "warp_0", "amount", 0.05)   # clean fine joints, not smeared plates
    set_param(g, "blend_0", "amount", 0.5)
    drop_conn(g, "Material", 1)
    set_param(g, "Material", "metallic", 0)
    set_param(g, "Material", "roughness", 0.88)   # matte, diffuse, fairly uniform
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.15)  # subtle: real frosted glass has near-zero macro bump
    # dry_earth leaves the roughness INPUT unconnected, so a scalar-only
    # roughness exports no ORM map (same gap _dry_earth_plates works around
    # in cookbook_terrain.py). Feed a flat roughness texture (constant
    # colorize, input value ignored) so an ORM map exports for the preview.
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.88, 0.88, 0.88), (1.0, 0.88, 0.88, 0.88)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})
    return save_variant(g, _LABEL, "gl01_frosted_glass", 1)


BUILDERS = {
    "gl01_frosted_glass": build_gl01_frosted_glass,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
