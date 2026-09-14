"""Cookbook: bare-metal category. Both materials are Phase-3 heroes folded in
from the retired examples/ folder (2026-09-05): the graphs come unchanged
from quality/author.py's shared builders via take_variant; these builders
only group them into named subgraphs. Outputs land under
quality/authored/cookbook-metal/<case>/v1.ptex.

Run: python -m quality.cookbook_metal
Then: python -m quality.promote_cookbook cookbook-metal
"""
import sys

from quality import author  # shared builder base; regression guard is promote_cookbook --check
from quality.author_helpers import (
    save_variant, take_variant, group_into_subgraph, rename_nodes,
    _from_scratch_noise_material, retype, add_node, _grad, set_param,
)

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-metal"

# `rusted_metal` donor mapping for m01: the docstring's "three ideas" are
# where the patches are (patina_pattern), what the two metals look like
# (copper_color), and how rough each is (surface_finish). colorize_3's
# output is a hard threshold reused three ways: the blend-2 mask in
# copper_color, the metallic scalar wired straight to Material, and the
# input to colorize_4's roughness bump.
_M01_NAMES = {
    "perlin_2": "PatchNoise",          # patina patch shape/size generator
    "colorize_3": "PatinaMask",        # hard threshold: where patches sit
    "colorize_4": "PatinaRoughness",   # roughness bump for patina areas
    "perlin_1": "MetalNoise",          # shared noise base for both metal colors
    "colorize_2": "CopperColor",       # base metal albedo
    "colorize_1": "VerdigrisColor",    # patch albedo
    "blend_0": "ColorComposite",       # base + patch, masked by PatinaMask
    "perlin_0": "RoughnessNoise",
    "colorize_0": "RoughnessVariation",
    "blend_1": "RoughnessComposite",   # PatinaRoughness base + RoughnessVariation
}

# `wood` donor mapping for m02: brushed_finish is the working streak/normal
# chain (straightened per the docstring); wood_knot_leftover is the dead
# knot-warp chain the straightening disconnected, kept for the story but
# renamed with an Unused suffix, same precedent as wood's CombineUnused.
_M02_NAMES = {
    "perlin_2": "StreakNoise",             # directional brush-streak generator
    "blend_0": "StreakComposite",          # straightened: both inputs from StreakNoise
    "colorize_2": "AluminumColor",
    "normal_map_0": "BrushNormal",
    "colorize_0": "RoughnessRamp",
    "perlin_0": "KnotNoiseUnused",
    "perlin_1": "KnotWarpNoiseUnused",
    "warp_0": "KnotWarpUnused",
    "voronoi_0": "KnotCellsUnused",
    "colorize_1": "KnotColorUnused",
    "warp_1": "KnotWarpFinalUnused",
}


# `noise_anisotropic` from-scratch build for m03: no donor to clone (the
# aluminum donor's warp-stretched streak is exactly the technique this
# material is meant to avoid), so it starts from
# `_from_scratch_noise_material`'s minimal perlin skeleton and `retype`s the
# generator to `noise_anisotropic` in place (single "f" output port 0, same
# shape as perlin's, so every downstream connection stays valid). A second
# colorize (roughness texture) is grafted on so the brushed sheen varies
# along the hairline direction instead of staying a flat scalar.
_M03_NAMES = {
    "perlin_0": "HairlineNoise",       # retyped to noise_anisotropic
    "colorize_0": "TitaniumColor",
    "colorize_rough": "RoughnessRamp",
    "normal_map_0": "BrushNormal",
}


def build_m03_brushed_titanium(catalog: dict) -> str:
    """Brushed titanium: a finer, more uniform directional hairline than
    `m02_brushed_aluminum`'s warp-stretched streak, built from the
    `noise_anisotropic` node (scale_y:scale_x = 48:4, the anisotropic
    stretch ratio itself is the directional grain -- no warp node needed).
    Titanium reads as a mid-light cool gray, slightly cooler than aluminum
    and with a faint violet cast (m02's albedo is neutral bright silver;
    here the gradient leans violet-gray, R and B both above G), so the two
    brushed metals are never a recolor of each other. The whole surface is metal (metallic=1
    scalar, same reasoning as m02: no paint layer to mask off). Roughness
    is a texture (not m02's scalar) fed by the same anisotropic noise so
    the sheen varies faintly along the brush direction. The hairline noise
    also feeds normal_map for the fine directional groove relief;
    param4=0 keeps it a real (if subtle) buffered normal rather than the
    dead-flat default the analytic generator would otherwise produce."""
    g = _from_scratch_noise_material(
        {"scale_x": 4, "scale_y": 48},
        [(0.0, 0.58, 0.56, 0.62), (1.0, 0.66, 0.64, 0.70)],
        metallic=1.0, roughness=0.3, normal_amount=0.35)
    retype(g, "perlin_0", "noise_anisotropic",
           {"scale_x": 4, "scale_y": 48, "smoothness": 1, "interpolation": 1})
    set_param(g, "normal_map_0", "param4", 0)
    add_node(g, "colorize_rough", "colorize",
             {"gradient": _grad([(0.0, 0.22, 0.22, 0.22), (1.0, 0.38, 0.38, 0.38)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "colorize_rough", "to_port": 0})
    g["connections"].append(
        {"from": "colorize_rough", "from_port": 0, "to": "Material", "to_port": 2})

    group_into_subgraph(
        g, ["perlin_0", "colorize_0", "colorize_rough", "normal_map_0"],
        "brushed_finish", "Brushed Finish",
        [("perlin_0", "scale_y", "param0", "Hairline density"),
         ("colorize_0", "gradient", "param1", "Titanium color"),
         ("colorize_rough", "gradient", "param2", "Roughness"),
         ("normal_map_0", "param1", "param3", "Groove depth")],
        catalog,
    )
    rename_nodes(g, _M03_NAMES)
    return save_variant(g, _LABEL, "m03_brushed_titanium", 1)


def build_m01_weathered_copper(catalog: dict) -> str:
    """Weathered copper (was examples/m01_weathered_copper, iter1 variant 1):
    `rusted_metal`'s two-layer blend recolored, base gray -> copper, patches
    orange rust -> green verdigris, patch mask unchanged. Grouped into the
    three ideas the donor is built from: where the patches are, what the two
    metals look like, and how rough each is."""
    g = take_variant(author.build_m01_weathered_copper, _LABEL, 1)
    group_into_subgraph(
        g, ["perlin_2", "colorize_3", "colorize_4"],
        "patina_pattern", "Patina Pattern",
        [("perlin_2", "scale_x", "param0", "Patch size"),
         ("colorize_3", "gradient", "param1", "Patina coverage")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_1", "colorize_2", "colorize_1", "blend_0"],
        "copper_color", "Copper Color",
        [("colorize_2", "gradient", "param0", "Copper color"),
         ("colorize_1", "gradient", "param1", "Verdigris color")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_0", "colorize_0", "blend_1"],
        "surface_finish", "Surface Finish",
        [("colorize_0", "gradient", "param0", "Roughness")],
        catalog,
    )
    rename_nodes(g, _M01_NAMES)
    return save_variant(g, _LABEL, "m01_weathered_copper", 1)


def build_m02_brushed_aluminum(catalog: dict) -> str:
    """Brushed aluminum (was examples/m02_brushed_aluminum, iter1 variant 2):
    `wood` clone with the grain straightened (blend_0's second input fed from
    the straight perlin_2 instead of the knot warp), finer longer streaks,
    neutral gray albedo, uniform metallic (the grain-driven metallic wire is
    dropped so the scalar 1 applies), low anisotropic roughness, and shallow
    brush-scratch relief via normal_map param4=0. The straightening leaves
    wood's knot-warp chain (perlin_0, perlin_1, warp_0, voronoi_0, colorize_1,
    warp_1) connected to nothing downstream; it is grouped separately and
    labeled as the unused donor leftover rather than deleted, so the graph
    still tells the "wood grain became brushed metal" story."""
    g = take_variant(author.build_m02_brushed_aluminum, _LABEL, 2)
    group_into_subgraph(
        g, ["perlin_2", "blend_0", "colorize_2", "colorize_0", "normal_map_0"],
        "brushed_finish", "Brushed Finish",
        [("perlin_2", "scale_x", "param0", "Streak length"),
         ("perlin_2", "scale_y", "param1", "Streak density"),
         ("colorize_2", "gradient", "param2", "Aluminum color"),
         ("colorize_0", "gradient", "param3", "Roughness"),
         ("normal_map_0", "param1", "param4", "Scratch depth")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_0", "perlin_1", "warp_0", "voronoi_0", "colorize_1", "warp_1"],
        "wood_knot_leftover", "Wood Donor Leftover (unused)",
        [],
        catalog,
    )
    rename_nodes(g, _M02_NAMES)
    return save_variant(g, _LABEL, "m02_brushed_aluminum", 1)


_M04_NAMES = {
    "perlin_0": "ScratchNoise",     # retyped to scratches
    "colorize_0": "SteelColor",
    "normal_map_0": "ScratchNormal",
    "rough_const": "RoughnessConst",
}


def build_m04_scratched_steel(catalog: dict) -> str:
    """Scratched steel: the first cookbook material to use the `scratches`
    node (discrete, individually-angled, wavy scratch marks composed in
    layers), a genuinely different technique from `m02_brushed_aluminum`
    (continuous parallel streaks from a stretched `perlin`) and
    `m03_brushed_titanium` (continuous streaks from `noise_anisotropic`):
    those two read as a uniform brushed finish, this one reads as scuffed,
    scored metal. Built from scratch via `_from_scratch_noise_material` (no
    donor has this topology) then `retype()`d from its placeholder
    `perlin_0` to `scratches` using the node's own verified catalog
    defaults -- `length`/`width`/`layers`/`waviness`/`angle`/`randomness`
    are all real, independently tunable float params, so the starting point
    is trustworthy rather than a guess. Both nodes' output port 0 is a
    plain `f` scalar, so the swap is connection-safe (same move `t09`
    (`cookbook_terrain.py`) uses for `wavelet_noise`).

    Cool gray steel palette, slightly darker and less uniform than m02's
    neutral bright silver or m03's violet-tinted titanium, since scored
    steel reads rougher than a brushed finish. metallic=1.0 scalar (uniform
    metal, same reasoning as m02/m03: no paint layer to mask off), and
    moderate-to-high roughness (scored metal is not glossy) fed as a flat
    texture (`rough_const`) rather than left as a Material-node scalar
    only, the same `_dry_earth_plates`/`t09` lesson: a scalar-only
    roughness exports no ORM map for the preview. Roughness is intentionally
    NOT proportional to the scratch signal itself (unlike, say, a relief-
    driven roughness ramp) since scored steel's matte-vs-glossy read is
    fairly uniform across the surface; the variation is scratch angle and
    position, not roughness."""
    g = _from_scratch_noise_material(
        {"scale_x": 4, "scale_y": 4},   # placeholder; retyped to scratches below
        [(0.0, 0.30, 0.31, 0.33), (0.5, 0.40, 0.41, 0.44), (1.0, 0.50, 0.52, 0.55)],
        metallic=1.0, roughness=0.6, normal_amount=0.4)
    retype(g, "perlin_0", "scratches", {
        "length": 0.25, "width": 0.5, "layers": 4, "waviness": 0.5,
        "angle": 0, "randomness": 0.5})
    set_param(g, "normal_map_0", "param4", 0)
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.6, 0.6, 0.6), (1.0, 0.6, 0.6, 0.6)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})

    # Subgraph grouping -- the exact t09_rippled_wet_sand template (the other
    # from-scratch, no-donor cookbook material): perlin_0 (retyped to
    # scratches) feeds all three downstream nodes (colorize_0, normal_map_0,
    # rough_const), so it has to live in one of the two groups; folding it
    # into the color group (rather than leaving it top-level) avoids a
    # degenerate single-node "finish" group.
    group_into_subgraph(
        g, ["perlin_0", "colorize_0"], "scratch_finish", "Scratch Finish",
        [("colorize_0", "gradient", "param0", "Steel color"),
         ("perlin_0", "randomness", "param1", "Scratch randomness")],
        catalog,
    )
    group_into_subgraph(
        g, ["normal_map_0", "rough_const"], "surface_detail", "Surface Detail",
        [("rough_const", "gradient", "param0", "Roughness"),
         ("normal_map_0", "param1", "param1", "Scratch depth")],
        catalog,
    )
    rename_nodes(g, _M04_NAMES)
    return save_variant(g, _LABEL, "m04_scratched_steel", 1)


BUILDERS = {
    "m01_weathered_copper": build_m01_weathered_copper,
    "m02_brushed_aluminum": build_m02_brushed_aluminum,
    "m03_brushed_titanium": build_m03_brushed_titanium,
    "m04_scratched_steel": build_m04_scratched_steel,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    catalog = build_catalog(load_config().nodes_dir)  # once per run, threaded through
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
