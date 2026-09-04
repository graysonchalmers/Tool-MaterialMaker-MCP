"""Cookbook growth: plastics authoring recipes -- the first entry in a new
`plastics` category. Same informal convention as the other cookbook_*.py
files -- 1 variant per material, no scorecard gate. Outputs land under
quality/authored/cookbook-plastics/<case>/v1.ptex.

Run: python quality/cookbook_plastics.py
Then: python quality/render_cookbook.py cookbook-plastics
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import _from_scratch_noise_material, set_param, save_variant, add_node, _grad

_LABEL = "cookbook-plastics"


def build_p01_glossy_plastic() -> str:
    """Glossy injection-molded plastic: every other cookbook category so far
    differentiates through visible micro-pattern (weave, crack network, cell
    facets); plastic differentiates the opposite way, as a smooth,
    patternless surface. Built from scratch (no donor topology to clone)
    via `_from_scratch_noise_material`: a narrow, near-single-color albedo
    band (saturated red, minimal gradient spread) so residual perlin
    variation stays invisible in color, non-metallic, low roughness for the
    glossy specular kick. Normal relief kept just above zero (param1=0.04)
    rather than exactly flat -- a truly dead-flat normal is physically wrong
    for a real molded surface, this keeps only the faintest micro-variation.
    The default param4=1 (buffered edge_detect) would read even flatter
    still since the perlin feeds it directly (same analytic-generator trap
    as every donor-based recipe), so param4 is forced to 0 for real, if
    subtle, relief.

    `_from_scratch_noise_material` leaves roughness as a scalar-only
    Material parameter (no texture input), which exports no ORM map (same
    gap `gl01_frosted_glass` hit and worked around) -- the 3D preview needs
    one. Feeds a flat roughness texture (constant colorize, input value
    ignored) into the Material's roughness port so ORM exports."""
    g = _from_scratch_noise_material(
        {"scale_x": 6, "scale_y": 6},
        [(0.0, 0.55, 0.05, 0.05), (1.0, 0.62, 0.08, 0.08)],
        metallic=0.0, roughness=0.18, normal_amount=0.04)
    set_param(g, "normal_map_0", "param4", 0)
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.18, 0.18, 0.18), (1.0, 0.18, 0.18, 0.18)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})
    return save_variant(g, _LABEL, "p01_glossy_plastic", 1)


BUILDERS = {
    "p01_glossy_plastic": build_p01_glossy_plastic,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
