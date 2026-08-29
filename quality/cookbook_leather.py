"""Cookbook growth: leather-category authoring recipes beyond the frozen 15-case
Phase 3 test set (`f02_brown_leather` is frozen there already -- see
quality/test_set.json's freeze note; this is additive, not an edit to that
case). Informal: 1 variant per material, no scorecard gate. Reuses author.py's
graph-surgery helpers; outputs land under
quality/authored/cookbook-leather/<case>/v1.ptex, same layout convention as the
Phase 3 iterations.

All four clone `crocodile_skin` -- the proven leather donor whose cellular
voronoi grain drives albedo (colorize_1 -> Material.albedo), roughness
(colorize_3 -> Material.roughness) and a height chain (colorize_0 ->
normal_map_0 -> Material.normal). f02 established the recolor lever on it; these
push into distinct territory: a glossy dark finish, a masked two-tone worn
composite, a soft napped suede (perlin donor, no cell grid), and a bold exotic
reptile scale. Where a variant wants real grain relief, it applies the
`param4=0` normal_map fix (see AUTHORING.md) -- f02 predates that fix and
renders a flat normal.

Run: python quality/cookbook_leather.py
Then quality/render_cookbook.py cookbook-leather renders each for inspection.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author import (load_example, node, set_gradient, set_param, retype,
                    rewire, add_node, save_variant, _grad)

_LABEL = "cookbook-leather"


def _dome_the_cells(g) -> None:
    """Flip crocodile_skin's height ramp so the voronoi CELL BODIES dome up and
    the seams between them recess -- the physically correct read for pebbled /
    scaled leather. crocodile_skin's stock colorize_0 (height, fed by voronoi
    port 0) maps low->dark, high->bright; voronoi port 0 is low at cell centers
    and high at the borders, so the stock ramp raises the SEAMS and sinks the
    scales (Grayson caught this in the 3D preview -- edges looked higher than
    the middle). Reversing the ramp inverts the relief: centers -> high, borders
    -> low."""
    set_gradient(g, "colorize_0", [
        (0.0, 1.0, 1.0, 1.0),        # cell centers (low voronoi) -> high ground
        (0.345, 0.5, 0.5, 0.5),
        (0.618, 0.0, 0.0, 0.0),      # borders (high voronoi) -> recessed seams
    ])


def build_l01_black_oiled_leather() -> str:
    """Glossy black oiled/waxed leather: near-black warm base with a faint brown
    sheen in the raised grain, LOW roughness (a polished, conditioned finish --
    the opposite of f02's matte tan). Pure recolor of the crocodile grain plus a
    low-roughness ramp, and the `param4=0` normal fix so the pebble grain shows
    real relief catching the gloss rather than reading as a flat black sheet."""
    g = load_example("crocodile_skin")
    set_gradient(g, "colorize_1", [           # near-black, warm brown highlight
        (0.0, 0.05, 0.035, 0.03),  # deep seam black
        (1.0, 0.22, 0.16, 0.11),   # raised grain, warm sheen (lifted so grain reads)
    ])
    set_gradient(g, "colorize_3", [           # low roughness: polished/oiled
        (0.0, 0.18, 0.18, 0.18),
        (1.0, 0.32, 0.32, 0.32),
    ])
    _dome_the_cells(g)                         # scales raised, seams recessed
    set_param(g, "normal_map_0", "param4", 0)  # raw grain -> real relief
    set_param(g, "normal_map_0", "param1", 0.45)
    return save_variant(g, _LABEL, "l01_black_oiled_leather", 1)


def build_l02_distressed_two_tone() -> str:
    """Distressed two-tone leather, worn lighter where it's rubbed: a dark
    saddle base with a lighter tan showing through on irregular high patches.
    Same masked-composite lever as combo01_rusted_painted_steel /
    w03_painted_wood_siding, but here BOTH layers are leather (rubbed-through
    finish, not paint-over-substrate): composite a lighter worn tan over the
    base grain albedo through an irregular perlin-threshold mask, and lift the
    roughness a touch in the worn patches so the rubbed areas read slightly
    drier/duller than the conditioned base. The pebble grain relief (normal) is
    left continuous under both tones so the worn areas are the SAME leather, just
    a different finish."""
    g = load_example("crocodile_skin")
    set_gradient(g, "colorize_1", [           # dark saddle base
        (0.0, 0.11, 0.06, 0.035),
        (1.0, 0.24, 0.14, 0.08),
    ])
    set_gradient(g, "colorize_3", [           # base: conditioned, mid roughness
        (0.0, 0.42, 0.42, 0.42),
        (1.0, 0.54, 0.54, 0.54),
    ])
    # Worn-patch mask: MANY small, soft, low-contrast rubs (a few giant
    # high-contrast blobs read as cow-hide, not wear -- same trap the
    # w03 siding recipe hit). Fine perlin + a WIDE feathered threshold band
    # scatters gentle rubs across the surface, and the worn tone sits only
    # a little lighter/warmer than the base so it reads as a rubbed finish,
    # not a second colour.
    add_node(g, "perlin_wm", "perlin", {"scale_x": 16, "scale_y": 16, "iterations": 6})
    add_node(g, "colorize_wm", "colorize",
             {"gradient": _grad([(0.40, 0, 0, 0), (0.72, 1, 1, 1)])})
    add_node(g, "worn_alb", "colorize",
             {"gradient": _grad([(0.0, 0.30, 0.20, 0.12), (1.0, 0.44, 0.32, 0.20)])})
    add_node(g, "worn_rgh", "colorize",
             {"gradient": _grad([(0.0, 0.56, 0.56, 0.56), (1.0, 0.66, 0.66, 0.66)])})
    add_node(g, "blend_alb", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "blend_rgh", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "perlin_wm", "from_port": 0, "to": "colorize_wm", "to_port": 0},
        {"from": "perlin_wm", "from_port": 0, "to": "worn_alb", "to_port": 0},
        {"from": "perlin_wm", "from_port": 0, "to": "worn_rgh", "to_port": 0},
        {"from": "colorize_1", "from_port": 0, "to": "blend_alb", "to_port": 0},  # base grain
        {"from": "worn_alb", "from_port": 0, "to": "blend_alb", "to_port": 1},
        {"from": "colorize_wm", "from_port": 0, "to": "blend_alb", "to_port": 2},
        {"from": "colorize_3", "from_port": 0, "to": "blend_rgh", "to_port": 0},
        {"from": "worn_rgh", "from_port": 0, "to": "blend_rgh", "to_port": 1},
        {"from": "colorize_wm", "from_port": 0, "to": "blend_rgh", "to_port": 2},
    ]
    rewire(g, "Material", 0, "blend_alb", 0)   # albedo <- worn-over-base
    rewire(g, "Material", 2, "blend_rgh", 0)   # roughness <- worn-over-base
    _dome_the_cells(g)                         # grain bodies raised, seams recessed
    set_param(g, "normal_map_0", "param4", 0)  # continuous grain relief under both
    set_param(g, "normal_map_0", "param1", 0.40)
    return save_variant(g, _LABEL, "l02_distressed_two_tone", 1)


def build_l03_suede() -> str:
    """Suede/nubuck: soft napped leather with NO cellular grain -- a fine fibrous
    surface, matte, with the faint tonal drift of brushed nap. Same donor-swap
    lever as f06_velvet: retype the voronoi generator to `perlin` (continuous,
    no hard cell edges; iterations add fine high-frequency fiber grain), warm
    fawn/tan albedo, very high matte roughness, and a very subtle normal so it
    reads as soft nap rather than hard relief."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "perlin",
           {"scale_x": 40, "scale_y": 40, "iterations": 8, "persistence": 0.55})
    set_gradient(g, "colorize_1", [           # warm fawn suede, gentle nap drift
        (0.0, 0.40, 0.30, 0.20),
        (0.5, 0.52, 0.40, 0.28),
        (1.0, 0.44, 0.33, 0.23),
    ])
    set_gradient(g, "colorize_3", [           # very matte, dry nap
        (0.0, 0.86, 0.86, 0.86),
        (1.0, 0.96, 0.96, 0.96),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])  # linear height
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.10, "param2": 0, "param4": 0}  # soft nap, raw
    return save_variant(g, _LABEL, "l03_suede", 1)


def build_l04_reptile_exotic() -> str:
    """Bold exotic reptile leather (snake/lizard): the crocodile donor's own
    cellular scales, enlarged to a few big bold scales and recolored to an exotic
    bronze-green with strong scale relief. Same recolor+param lever as f02, but
    leaning INTO the voronoi cell scale (f02 kept the default fine grain) so the
    scales read as a deliberate exotic pattern, plus the param4=0 fix so the
    scale edges cast real relief."""
    g = load_example("crocodile_skin")
    set_param(g, "voronoi_0", "scale_x", 7)    # fewer, bigger scales
    set_param(g, "voronoi_0", "scale_y", 9)    # slightly elongated (reptilian)
    set_param(g, "voronoi_0", "intensity", 0.6)
    set_gradient(g, "colorize_1", [            # exotic bronze-green scales
        (0.0, 0.06, 0.09, 0.04),   # dark scale seams
        (0.6, 0.24, 0.30, 0.12),   # olive-green scale body
        (1.0, 0.46, 0.42, 0.18),   # bronze scale crest
    ])
    set_gradient(g, "colorize_3", [            # semi-gloss scales
        (0.0, 0.28, 0.28, 0.28),
        (1.0, 0.44, 0.44, 0.44),
    ])
    _dome_the_cells(g)                         # scales domed up, seams recessed
    set_param(g, "normal_map_0", "param4", 0)  # strong scale-edge relief
    set_param(g, "normal_map_0", "param1", 0.7)
    return save_variant(g, _LABEL, "l04_reptile_exotic", 1)


BUILDERS = {
    "l01_black_oiled_leather": build_l01_black_oiled_leather,
    "l02_distressed_two_tone": build_l02_distressed_two_tone,
    "l03_suede": build_l03_suede,
    "l04_reptile_exotic": build_l04_reptile_exotic,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
