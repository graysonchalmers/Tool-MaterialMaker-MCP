"""Cookbook growth: organic-category authoring recipes beyond the frozen
15-case Phase 3 test set (o01 moss, o02 dry mud already cover GROUND organics;
this widens into organism SURFACES: bark, scales, coral, lichen-on-stone).
Same informal convention as cookbook_fabrics.py -- 1 variant per material, no
scorecard gate. Outputs land under quality/authored/cookbook-organics/<case>/v1.ptex.

Run: python -m quality.cookbook_organics
Then: python -m quality.render_cookbook cookbook-organics
"""
import sys

from quality.author_helpers import (load_example, node, set_gradient, set_param, retype,
                     rewire, drop_conn, add_node, save_variant, group_into_subgraph,
                     take_variant, rename_nodes)
from quality import author  # shared builder base; regression guard is promote_cookbook --check

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-organics"

# Worked mapping for `wood` cloned unmodified structurally (o03; see
# cookbook_wood.py's _WOOD_NAMES for the identical donor graph -- same 11
# nodes, same wiring, just bark wording instead of wood wording since bark
# wants ridges/furrows, not annual rings).
_BARK_NAMES = {
    "perlin_0": "GrainNoiseFine",
    "perlin_1": "GrainNoiseCoarse",
    "perlin_2": "GrainWobble",
    "voronoi_0": "BarkRidges",       # furrow/ridge pattern (wood's ring pattern, recast)
    "colorize_1": "RidgeContrast",
    "warp_0": "GrainWarp",
    "warp_1": "RidgeWarp",           # the knot-overlay waviness this builder keeps
    "blend_0": "GrainMask",
    "colorize_2": "BarkColor",
    "colorize_0": "BarkRoughness",
    "normal_map_0": "BarkNormal",
}

# Worked mapping for `dry_earth` cloned unmodified structurally (o01): the
# shared perlin_0/perlin_1 sources feed both groups (see the docstring),
# voronoi_0 is the plate/crack cell pattern, colorize_3 is the mask that
# both composites the albedo AND drives Material's metallic port directly
# (same shared-mask-drives-metallic shape as o06's LichenMask below).
_MOSSY_FLOOR_NAMES = {
    "perlin_0": "LitterNoise",
    "perlin_1": "MossCoverageNoise",
    "voronoi_0": "PlateCells",
    "colorize_1": "PlateEdges",
    "warp_0": "PlateWarp",
    "colorize_0": "MossColor",
    "blend_0": "AlbedoComposite",
    "colorize_3": "MossMask",
    "colorize_4": "ReliefRamp",
    "blend_1": "ReliefComposite",
    "colorize": "ReliefHeight",
    "normal_map_0": "GroundNormal",
}


def _group_crocodile_skin_pattern(g, catalog, *, pattern_size_label,
                                   pattern_color_label, sheen_label,
                                   relief_label):
    """Shared grouping for o04_snake_scales/o05_coral: both clone
    `crocodile_skin`'s identical 6-node graph (voronoi_0 -> colorize_0/1/3,
    normal_map_0, uniform_0) unmodified structurally -- o04 keeps voronoi_0
    as a voronoi and o05 retypes it to fbm, but the node NAMES and wiring are
    the same either way, so the two `group_into_subgraph` calls are shared
    here instead of being duplicated verbatim in both builders (the friendly
    labels differ per material since "scale size" doesn't describe coral's
    cellular pattern). `uniform_0` (Material's untouched metallic scalar) is
    left top-level -- it is a single donor-default node feeding one port
    directly, not a generative/compositing chain worth collapsing."""
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1"], "surface_pattern", "Surface Pattern",
        [("voronoi_0", "scale_x", "param0", pattern_size_label),
         ("colorize_1", "gradient", "param1", pattern_color_label)],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_0", "colorize_3", "normal_map_0"],
        "surface_finish", "Surface Finish",
        [("colorize_3", "gradient", "param0", sheen_label),
         ("normal_map_0", "param1", "param1", relief_label)],
        catalog,
    )


def build_o03_tree_bark(catalog: dict) -> str:
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

    # Same donor (`wood`, unmodified structurally, per the docstring) and
    # same identical 11-node graph as cookbook_wood.py's w04/w05, which grouped
    # it into the noise/pattern generator + albedo colorize ("Wood Grain")
    # and the roughness ramp + normal map ("Surface Finish") -- see that
    # file's build_w04_driftwood_gray for the full reasoning on why
    # colorize_2 rides into the generator group rather than being left with
    # only untouched donor defaults. Bark reuses the identical grouping,
    # relabeled for the bark context.
    group_into_subgraph(
        g,
        ["perlin_0", "perlin_1", "perlin_2", "voronoi_0", "colorize_1",
         "warp_0", "warp_1", "blend_0", "colorize_2"],
        "bark_grain", "Bark Grain",
        [("colorize_2", "gradient", "param0", "Bark color")],
        catalog,
    )
    group_into_subgraph(
        g,
        ["colorize_0", "normal_map_0"],
        "surface_finish", "Surface Finish",
        [("colorize_0", "gradient", "param0", "Bark sheen")],
        catalog,
    )
    rename_nodes(g, _BARK_NAMES)
    return save_variant(g, _LABEL, "o03_tree_bark", 1)


def build_o04_snake_scales(catalog: dict) -> str:
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

    # See _group_crocodile_skin_pattern's docstring: shared with o05_coral,
    # both clone crocodile_skin's identical 6-node graph. `uniform_0`
    # (Material's metallic scalar, untouched donor default) is left
    # top-level.
    _group_crocodile_skin_pattern(
        g, catalog,
        pattern_size_label="Scale size", pattern_color_label="Scale color",
        sheen_label="Sheen", relief_label="Scale relief",
    )
    rename_nodes(g, {
        "voronoi_0": "ScaleLayout",     # finished discrete scale tiling
        "colorize_1": "ScaleColor",
        "colorize_3": "ScaleSheen",
        "colorize_0": "ScaleHeight",
        "normal_map_0": "ScaleNormal",
        "uniform_0": "NonMetallic",
    })
    return save_variant(g, _LABEL, "o04_snake_scales", 1)


def build_o05_coral(catalog: dict) -> str:
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

    # See _group_crocodile_skin_pattern's docstring: shared with
    # o04_snake_scales, both clone crocodile_skin's identical 6-node graph
    # (the fbm retype of voronoi_0 changes its noise, not its name/wiring).
    # `uniform_0` (Material's metallic scalar, untouched donor default) is
    # left top-level.
    _group_crocodile_skin_pattern(
        g, catalog,
        pattern_size_label="Cell size", pattern_color_label="Coral color",
        sheen_label="Surface tone", relief_label="Pore relief",
    )
    rename_nodes(g, {
        "voronoi_0": "PolypCells",     # fbm Cellular: porous, still noise not a rigid layout
        "colorize_1": "CoralColor",
        "colorize_3": "CoralSheen",
        "colorize_0": "CoralHeight",
        "normal_map_0": "CoralNormal",
        "uniform_0": "NonMetallic",
    })
    return save_variant(g, _LABEL, "o05_coral", 1)


def build_o06_lichen_crusted_rock(catalog: dict) -> str:
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

    # rusted_metal's two-layer masked-blend structure (base colorize_2 +
    # patch colorize_1, composited by blend_0 through the colorize_3 mask)
    # plus this builder's own additions: the widened mask threshold and the
    # new normal_map_lichen relief chain. `colorize_3` (the mask) is a true
    # shared generator -- it feeds blend_0's mask port (surface_color),
    # colorize_4's roughness variant (surface_finish), AND
    # normal_map_lichen's relief input (also surface_finish) -- so rather
    # than folding it into one of those (which would just relabel two of the
    # three consumers as boundary ports instead of one), it gets its own
    # small group since its gradient is a real, explicitly-tuned knob (the
    # widened threshold), not an untouched donor default. `colorize_0` and
    # `colorize_4` are untouched rusted_metal defaults but stay inside
    # surface_finish as internal-only members (same pattern as w04's
    # untouched colorize_1/warp_0/warp_1 riding inside wood_grain).
    group_into_subgraph(
        g, ["perlin_1", "colorize_2", "colorize_1", "blend_0"],
        "surface_color", "Surface Color",
        [("colorize_2", "gradient", "param0", "Stone color"),
         ("colorize_1", "gradient", "param1", "Lichen color")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_2", "colorize_3"], "lichen_mask", "Lichen Coverage",
        [("colorize_3", "gradient", "param0", "Coverage")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_0", "colorize_0", "colorize_4", "blend_1", "normal_map_lichen"],
        "surface_finish", "Surface Finish",
        [("normal_map_lichen", "param1", "param0", "Relief strength")],
        catalog,
    )
    rename_nodes(g, {
        "perlin_1": "StoneNoise",             # drives both base-stone and lichen-tone ramps
        "colorize_2": "RockColor",
        "colorize_1": "LichenColor",
        "blend_0": "AlbedoComposite",
        "perlin_2": "LichenCoverageNoise",
        "colorize_3": "LichenMask",           # feeds blend_0's mask, colorize_4, AND the normal
        "perlin_0": "RockRoughnessNoise",
        "colorize_0": "RockRoughnessTone",
        "colorize_4": "LichenRoughnessTone",
        "blend_1": "RoughnessComposite",
        "normal_map_lichen": "LichenNormal",
    })
    return save_variant(g, _LABEL, "o06_lichen_crusted_rock", 1)


def build_o01_mossy_forest_floor(catalog: dict) -> str:
    """Mossy forest floor, folded in from the Phase-3 hero set (was
    examples/o01_mossy_forest_floor, iter1 variant 1). Graph unchanged from
    author.build_o01_mossy_forest_floor v1: `dry_earth`'s cracked-plate
    ground with its earth ramp recolored dark soil -> green moss so plate
    tops read as moss and crack floors as soil. This builder only GROUPS it,
    the same two-group split as the other dry_earth-derived materials
    (gl01_frosted_glass, the terrain plates): a Ground Color group and a
    Ground Relief group, with the two shared perlin sources left top-level
    because each feeds both groups."""
    g = take_variant(author.build_o01_mossy_forest_floor, _LABEL, 1)
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "warp_0", "colorize_0", "blend_0", "colorize_3"],
        "ground_color", "Ground Color",
        [("voronoi_0", "scale_x", "param0", "Plate size"),
         ("colorize_0", "gradient", "param1", "Moss and soil colors"),
         ("blend_0", "amount", "param2", "Crack contrast"),
         ("warp_0", "amount", "param3", "Plate warp")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_4", "blend_1", "colorize", "normal_map_0"],
        "ground_relief", "Ground Relief",
        [("normal_map_0", "param1", "param0", "Relief strength")],
        catalog,
    )
    rename_nodes(g, _MOSSY_FLOOR_NAMES)
    return save_variant(g, _LABEL, "o01_mossy_forest_floor", 1)


BUILDERS = {
    "o01_mossy_forest_floor": build_o01_mossy_forest_floor,
    "o03_tree_bark": build_o03_tree_bark,
    "o04_snake_scales": build_o04_snake_scales,
    "o05_coral": build_o05_coral,
    "o06_lichen_crusted_rock": build_o06_lichen_crusted_rock,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    # Loaded once per script run (not once per builder) since this category
    # now has 4 materials, all of which need it for group_into_subgraph.
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
