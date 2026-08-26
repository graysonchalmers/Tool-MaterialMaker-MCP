"""Cookbook growth: organic-category authoring recipes beyond the frozen
15-case Phase 3 test set (o01 moss, o02 dry mud already cover GROUND organics;
this widens into organism SURFACES: bark, scales, coral, lichen-on-stone).
Same informal convention as cookbook_fabrics.py -- 1 variant per material, no
scorecard gate. Outputs land under quality/authored/cookbook-organics/<case>/v1.ptex.

Run: python quality/cookbook_organics.py
Then: python quality/render_cookbook.py cookbook-organics
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author import (load_example, node, set_gradient, set_param, retype,
                     rewire, drop_conn, add_node, save_variant)

_LABEL = "cookbook-organics"


def build_o03_tree_bark() -> str:
    """Tree bark: clone `wood` UNMODIFIED structurally (unlike m02 aluminum,
    which straightens out the knots) -- bark wants the grain AND the knotty
    waviness, so keep wood's blend_0<-warp_1 knot-overlay chain as-is. Just
    recolor to weathered gray-brown bark and push roughness high. wood's own
    normal chain (blend_0 -> normal_map_0) already works (w01/w02 are HITs
    with it unmodified), so no param4 fix needed here."""
    g = load_example("wood")
    set_gradient(g, "colorize_2", [    # weathered bark, not wood-finish brown
        (0.0, 0.16, 0.12, 0.09),
        (0.3, 0.30, 0.24, 0.18),
        (0.6, 0.22, 0.17, 0.12),
        (1.0, 0.12, 0.09, 0.07),
    ])
    set_gradient(g, "colorize_0", [    # rough, matte bark
        (0.0, 0.80, 0.80, 0.80),
        (1.0, 0.95, 0.95, 0.95),
    ])
    return save_variant(g, _LABEL, "o03_tree_bark", 1)


def build_o04_snake_scales() -> str:
    """Snake scales: crocodile_skin's OWN default voronoi cellular pattern is
    already a reptile-scale layout (it's what it was built for) -- no
    retype, just the recolor lever. Two-tone olive-to-khaki for a subtle
    iridescent read, roughness lower than leather (scales have more sheen).
    Applies the param4=0 fix proactively: crocodile_skin's normal chain
    (voronoi_0 -> colorize_0 -> normal_map_0) is directly-fed with no
    buffer, same shape as the denim blocker, so its default param4=1 would
    render flat even though f02 leather's HIT didn't depend on catching it."""
    g = load_example("crocodile_skin")
    set_param(g, "voronoi_0", "scale_x", 20)   # smaller, denser scales
    set_param(g, "voronoi_0", "scale_y", 20)
    set_gradient(g, "colorize_1", [    # olive -> pale khaki highlight
        (0.0, 0.14, 0.18, 0.08),
        (1.0, 0.46, 0.50, 0.28),
    ])
    set_gradient(g, "colorize_3", [    # some sheen, not matte leather
        (0.0, 0.35, 0.35, 0.35),
        (1.0, 0.55, 0.55, 0.55),
    ])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.3, "param2": 0, "param4": 0}
    return save_variant(g, _LABEL, "o04_snake_scales", 1)


def build_o05_coral() -> str:
    """Coral: retype the generator to `fbm` with Cellular noise (enum value
    2) -- a porous, bumpy, organic cell pattern distinct from voronoi's flat-
    faceted cells, closer to coral's irregular pitted surface. Coral
    pink/orange, matte-ish, pronounced normal relief (param4=0, higher
    strength) for the porous bumpy surface."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "fbm",
           {"noise": 2, "scale_x": 18, "scale_y": 18, "folds": 2,
            "iterations": 5, "persistence": 0.6})
    set_gradient(g, "colorize_1", [    # coral pink/orange
        (0.0, 0.55, 0.18, 0.14),
        (1.0, 0.92, 0.48, 0.34),
    ])
    set_gradient(g, "colorize_3", [    # matte, porous
        (0.0, 0.70, 0.70, 0.70),
        (1.0, 0.88, 0.88, 0.88),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.5, "param2": 0, "param4": 0}
    return save_variant(g, _LABEL, "o05_coral", 1)


def build_o06_lichen_crusted_rock() -> str:
    """Lichen-crusted rock: clone `rusted_metal`'s two-layer masked-blend
    structure (proven in m01 weathered copper) but recolor to stone+lichen
    instead of metal+patina: base (colorize_2) -> gray stone, patch
    (colorize_1) -> lichen green-gray, widen the mask (colorize_3 threshold)
    for more coverage. rusted_metal wires Material's metallic input straight
    off the mask (colorize_3) -- fine for a metal donor, wrong for stone, so
    drop that connection and force the Material's own metallic scalar to 0.
    Adds a light normal_map fed from the mask so lichen patches read as
    faintly raised, rather than a pure flat color swap."""
    g = load_example("rusted_metal")
    set_gradient(g, "colorize_2", [    # base -> gray stone
        (0.0, 0.30, 0.30, 0.30),
        (1.0, 0.55, 0.55, 0.55),
    ])
    set_gradient(g, "colorize_1", [    # patch -> lichen green-gray
        (0.0, 0.20, 0.26, 0.14),
        (1.0, 0.42, 0.50, 0.26),
    ])
    set_gradient(g, "colorize_3", [(0.35, 0, 0, 0), (0.35, 1, 1, 1)])  # widen mask
    drop_conn(g, "Material", 1)
    set_param(g, "Material", "metallic", 0)
    add_node(g, "normal_map_lichen", "normal_map",
             {"param0": 9, "param1": 0.3, "param2": 0, "param4": 0})
    g["connections"].append(
        {"from": "colorize_3", "from_port": 0, "to": "normal_map_lichen", "to_port": 0})
    g["connections"].append(
        {"from": "normal_map_lichen", "from_port": 0, "to": "Material", "to_port": 4})
    return save_variant(g, _LABEL, "o06_lichen_crusted_rock", 1)


BUILDERS = {
    "o03_tree_bark": build_o03_tree_bark,
    "o04_snake_scales": build_o04_snake_scales,
    "o05_coral": build_o05_coral,
    "o06_lichen_crusted_rock": build_o06_lichen_crusted_rock,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
