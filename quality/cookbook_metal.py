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
    _from_scratch_noise_material, retype, add_node, _grad, set_param, rewire,
    node, place, tidy_ports,
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
    "colorize_2": "MetalColor",            # was AluminumColor; the host recolors to any metal
    "normal_map_0": "SurfaceNormal",       # was BrushNormal; now carries scratch grooves too
    "colorize_0": "RoughnessRamp",
    "perlin_0": "KnotNoiseUnused",
    "perlin_1": "KnotWarpNoiseUnused",
    "warp_0": "KnotWarpUnused",
    "voronoi_0": "KnotCellsUnused",
    "colorize_1": "KnotColorUnused",
    "warp_1": "KnotWarpFinalUnused",
}


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


# m04's scratch colorway sets the SCRATCH color; the host's scratch layer
# shows a fresh cut as a pull toward this bright neutral instead, so the
# scratch reads on any metal color the host is set to.
_SCRATCH_TINT = {"a": 1, "r": 0.9, "g": 0.9, "b": 0.9, "type": "Color"}
# How far one full-strength scratch cuts into the height that feeds the
# normal map (AddSub blend toward GrooveHeight=0: height - depth * mask).
_GROOVE_DEPTH = 0.8


def build_m02_brushed_metal(catalog: dict) -> str:
    """Brushed aluminum, and the brushed-metal HOST: one material carrying
    exposed feature layers instead of several one-trick materials. Every
    layer defaults OFF (amount 0), so the default graph renders the same as
    the pre-host m02.

    Base (was examples/m02_brushed_aluminum, iter1 variant 2): `wood` clone
    with the grain straightened (blend_0's second input fed from the straight
    perlin_2 instead of the knot warp), finer longer streaks, neutral gray
    albedo, uniform metallic (the grain-driven metallic wire is dropped so
    the scalar 1 applies), low anisotropic roughness, and shallow brush
    relief via normal_map param4=0. The straightening leaves wood's knot-warp
    chain (perlin_0, perlin_1, warp_0, voronoi_0, colorize_1, warp_1)
    connected to nothing downstream; it is grouped separately and labeled as
    the unused donor leftover rather than deleted, so the graph still tells
    the "wood grain became brushed metal" story.

    Layers, left to right (each its own subgraph):
    - Hairline Layer (from m03_brushed_titanium): m03's noise_anisotropic
      with m03's params, rotated 90 degrees because noise_anisotropic only
      streaks along x and m02's streak runs along y (unrotated, the slider
      would cross-hatch the two instead of trading one brushing for a finer
      one). BrushComposite (Normal blend, amount = "Hairline fineness")
      mixes it over the streak; color, roughness and relief all read
      BrushComposite, so they stay registered.
    - Metal Color: the base colorize ramps (albedo, roughness) on that
      brush signal.
    - Polish Layer (from m05_polished_chrome): one PolishMask value is the
      opacity of two blends, roughness toward m05's 0.06-0.14 mirror band
      and the brush relief toward a flat height (fully flat at Polish 1: a
      10% residual was tried and m02's fine 8-octave streak still read as
      sparkle on a mirror).
    - Scratch Wear (from m04_scratched_steel): m04's scratches node with
      m04's params, times "Scratch amount", is ONE ScratchMask; it is the
      opacity of all three scratch blends (albedo pull to a bright cut
      tint, roughness up to m04's 0.6, and a groove cut into the height), so
      the scratch reads in color, sheen and relief at the same pixels.
      Grooves (cut in), not m04's raised lines: that was m04's per-material
      quirk, not a look to copy.
    Noise seeds come from node position, so HairlineNoise and ScratchNoise
    sit at (0, 0) of their own subgraphs: seed 0, the same field m03 and m04
    ship, which makes the original-vs-host comparison like for like."""
    g = take_variant(author.build_m02_brushed_metal, _LABEL, 2)

    # --- Hairline layer (m03) ---
    add_node(g, "HairlineNoise", "noise_anisotropic",
             {"scale_x": 4, "scale_y": 48, "smoothness": 1, "interpolation": 1})
    add_node(g, "HairlineAlign", "rotate", {"cx": 0, "cy": 0, "rotate": 90})
    add_node(g, "BrushComposite", "blend", {"blend_type": 0, "amount": 0})  # 0 = Normal
    g["connections"] += [
        {"from": "HairlineNoise", "from_port": 0, "to": "HairlineAlign", "to_port": 0},
        {"from": "HairlineAlign", "from_port": 0, "to": "BrushComposite", "to_port": 0},
        {"from": "blend_0", "from_port": 0, "to": "BrushComposite", "to_port": 1},
    ]
    rewire(g, "colorize_2", 0, "BrushComposite", 0)
    rewire(g, "colorize_0", 0, "BrushComposite", 0)

    # --- Polish layer (m05) ---
    add_node(g, "PolishMask", "uniform_greyscale", {"color": 0})
    add_node(g, "PolishRoughness", "colorize",
             {"gradient": _grad([(0.0, 0.06, 0.06, 0.06), (1.0, 0.14, 0.14, 0.14)])})
    add_node(g, "PolishRoughnessComposite", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "FlatHeight", "uniform_greyscale", {"color": 0.5})
    add_node(g, "PolishHeightComposite", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "BrushComposite", "from_port": 0, "to": "PolishRoughness", "to_port": 0},
        {"from": "PolishRoughness", "from_port": 0, "to": "PolishRoughnessComposite", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "PolishRoughnessComposite", "to_port": 1},
        {"from": "PolishMask", "from_port": 0, "to": "PolishRoughnessComposite", "to_port": 2},
        {"from": "FlatHeight", "from_port": 0, "to": "PolishHeightComposite", "to_port": 0},
        {"from": "BrushComposite", "from_port": 0, "to": "PolishHeightComposite", "to_port": 1},
        {"from": "PolishMask", "from_port": 0, "to": "PolishHeightComposite", "to_port": 2},
    ]

    # --- Scratch wear (m04) ---
    add_node(g, "ScratchNoise", "scratches", {
        "length": 0.25, "width": 0.5, "layers": 4, "waviness": 0.5,
        "angle": 0, "randomness": 0.5})
    add_node(g, "ScratchMask", "math", {"op": 2, "default_in2": 0})  # 2 = A*B
    add_node(g, "ScratchTint", "uniform", {"color": dict(_SCRATCH_TINT)})
    add_node(g, "ScratchColorComposite", "blend", {"blend_type": 0, "amount": 0.3})
    add_node(g, "ScratchRoughness", "uniform_greyscale", {"color": 0.6})
    add_node(g, "ScratchRoughnessComposite", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "GrooveHeight", "uniform_greyscale", {"color": 0})
    add_node(g, "ScratchHeightComposite", "blend",
             {"blend_type": 13, "amount": _GROOVE_DEPTH})  # 13 = AddSub
    g["connections"] += [
        {"from": "ScratchNoise", "from_port": 0, "to": "ScratchMask", "to_port": 0},
        {"from": "ScratchTint", "from_port": 0, "to": "ScratchColorComposite", "to_port": 0},
        {"from": "colorize_2", "from_port": 0, "to": "ScratchColorComposite", "to_port": 1},
        {"from": "ScratchMask", "from_port": 0, "to": "ScratchColorComposite", "to_port": 2},
        {"from": "ScratchRoughness", "from_port": 0, "to": "ScratchRoughnessComposite", "to_port": 0},
        {"from": "PolishRoughnessComposite", "from_port": 0, "to": "ScratchRoughnessComposite", "to_port": 1},
        {"from": "ScratchMask", "from_port": 0, "to": "ScratchRoughnessComposite", "to_port": 2},
        {"from": "GrooveHeight", "from_port": 0, "to": "ScratchHeightComposite", "to_port": 0},
        {"from": "PolishHeightComposite", "from_port": 0, "to": "ScratchHeightComposite", "to_port": 1},
        {"from": "ScratchMask", "from_port": 0, "to": "ScratchHeightComposite", "to_port": 2},
    ]
    g["connections"] = [c for c in g["connections"]
                        if not (c["to"] == "Material" and c["to_port"] in (0, 2))
                        and c["to"] != "normal_map_0"]
    g["connections"] += [
        {"from": "ScratchColorComposite", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "ScratchRoughnessComposite", "from_port": 0, "to": "Material", "to_port": 2},
        {"from": "ScratchHeightComposite", "from_port": 0, "to": "normal_map_0", "to_port": 0},
    ]

    # Seed-bearing noises at (0, 0) of their own subgraph (seed 0 = m03's
    # and m04's field); everything else spaced left to right by data flow.
    place(g, {
        "HairlineNoise": (0, 0), "HairlineAlign": (300, 0), "BrushComposite": (600, 200),
        "PolishRoughness": (-50, -50), "FlatHeight": (-50, 250), "PolishMask": (-50, 450),
        "PolishRoughnessComposite": (300, 50), "PolishHeightComposite": (300, 330),
        "ScratchNoise": (0, 0), "ScratchMask": (300, 0), "ScratchTint": (300, 220),
        "ScratchRoughness": (300, 400), "GrooveHeight": (300, 580),
        "ScratchColorComposite": (600, 150), "ScratchRoughnessComposite": (600, 380),
        "ScratchHeightComposite": (600, 610),
    })

    group_into_subgraph(
        g, ["perlin_2", "blend_0"], "brushed_finish", "Brushed Finish",
        [("perlin_2", "scale_x", "param0", "Streak length"),
         ("perlin_2", "scale_y", "param1", "Streak density")],
        catalog,
    )
    tidy_ports(g, "brushed_finish", [], [("blend_0", 0, "streak")], catalog)
    group_into_subgraph(
        g, ["HairlineNoise", "HairlineAlign", "BrushComposite"],
        "hairline_layer", "Hairline Layer",
        [("BrushComposite", "amount", "param0", "Hairline fineness")],
        catalog,
    )
    tidy_ports(g, "hairline_layer", [("brushed_finish", 0, "streak")],
                [("BrushComposite", 0, "brush")],
                catalog)
    group_into_subgraph(
        g, ["colorize_2", "colorize_0"], "metal_color", "Metal Color",
        [("colorize_2", "gradient", "param0", "Metal color"),
         ("colorize_0", "gradient", "param1", "Roughness")],
        catalog,
    )
    tidy_ports(g, "metal_color", [("hairline_layer", 0, "brush")],
                [("colorize_2", 0, "albedo"), ("colorize_0", 0, "roughness")],
                catalog)
    group_into_subgraph(
        g, ["PolishRoughness", "FlatHeight", "PolishMask",
            "PolishRoughnessComposite", "PolishHeightComposite"],
        "polish_layer", "Polish Layer",
        [("PolishMask", "color", "param0", "Polish")],
        catalog,
    )
    tidy_ports(g, "polish_layer",
                [("hairline_layer", 0, "brush"), ("metal_color", 1, "roughness")],
                [("PolishRoughnessComposite", 0, "roughness"),
                 ("PolishHeightComposite", 0, "height")],
                catalog)
    group_into_subgraph(
        g, ["ScratchNoise", "ScratchMask", "ScratchTint", "ScratchColorComposite",
            "ScratchRoughness", "ScratchRoughnessComposite", "GrooveHeight",
            "ScratchHeightComposite"],
        "scratch_wear", "Scratch Wear",
        [("ScratchMask", "default_in2", "param0", "Scratch amount"),
         ("ScratchNoise", "randomness", "param1", "Scratch randomness"),
         ("ScratchNoise", "length", "param2", "Scratch length")],
        catalog,
    )
    tidy_ports(g, "scratch_wear",
                [("metal_color", 0, "albedo"), ("polish_layer", 0, "roughness"),
                 ("polish_layer", 1, "height")],
                [("ScratchColorComposite", 0, "albedo"),
                 ("ScratchRoughnessComposite", 0, "roughness"),
                 ("ScratchHeightComposite", 0, "height")],
                catalog)
    group_into_subgraph(
        g, ["perlin_0", "perlin_1", "warp_0", "voronoi_0", "colorize_1", "warp_1"],
        "wood_knot_leftover", "Wood Donor Leftover (unused)",
        [],
        catalog,
    )

    # Inner canvases: the proxies group_into_subgraph centres on the members
    # would overlap the hand-placed nodes, so park them at the edges.
    place(node(g, "brushed_finish"), {"gen_outputs": (450, 250)})
    place(node(g, "hairline_layer"), {
        "gen_inputs": (-350, 250), "gen_parameters": (-350, 450), "gen_outputs": (900, 200)})
    place(node(g, "polish_layer"), {
        "gen_inputs": (-400, 200), "gen_parameters": (-400, 450), "gen_outputs": (650, 200)})
    place(node(g, "scratch_wear"), {
        "gen_inputs": (-450, 400), "gen_parameters": (-450, -150), "gen_outputs": (900, 380)})
    # Top level reads as a layer stack, left to right into Material. The
    # collapsed nodes carry seed_int 0, so moving them moves no seeds.
    place(g, {
        "brushed_finish": (-150, 0), "hairline_layer": (150, 0), "metal_color": (450, -120),
        "polish_layer": (750, 120), "scratch_wear": (1050, 0), "normal_map_0": (1350, 180),
        "Material": (1600, 0),
    })
    rename_nodes(g, _M02_NAMES)
    return save_variant(g, _LABEL, "m02_brushed_metal", 1)


_M06_NAMES = {
    "perlin_0": "MicroNoise",
    "colorize_0": "CarPaintColor",
    "colorize_rough": "RoughnessVariation",
    "voronoi_0": "FlakeCells",
    "colorize_flake": "FlakeMask",
    "blend_0": "RoughnessWithFlake",
    "normal_map_0": "MicroNormal",
    "orange_peel": "OrangePeelNoise",
    "peel_scaled": "OrangePeelWeighted",
    "normal_height": "NormalHeightMix",
}


def build_m06_car_paint(catalog: dict) -> str:
    """Candy-red car paint: `m05_polished_chrome`'s minimal metallic skeleton
    (from-scratch perlin -> colorize -> Material, metallic=1.0 scalar,
    roughness held low and fed as a texture not a bare scalar) recolored to a
    saturated, deeply-chromatic red instead of chrome's near-neutral gray --
    this is the whole point of the task: prove the grazing-angle Fresnel
    brightening is real PBR on a COLORED metal, not just chrome's white-on-
    white case. Albedo gradient stays in the red band throughout (R roughly
    3-4x G/B, both endpoints deep and saturated) so the base coat itself
    reads as candy paint even before any clearcoat garnish is added in the
    preview.

    roughness is slightly higher than chrome's (0.12-0.20 vs chrome's
    0.06-0.14) since automotive base-coat lacquer is glossy but not a bare
    mirror; the metallic-flake sparkle is a second signal layered on top of
    that roughness texture rather than replacing it: a small-scale `voronoi`
    (FlakeCells) thresholded hard via a second colorize (FlakeMask) into a
    sparse, tiny bright-spot mask, then `blend`ed additively onto
    RoughnessVariation so only the flake specks get punched toward glossier
    (lower) roughness -- the rest of the panel keeps its even base-coat
    sheen. normal_amount starts at chrome's 0.04 (not 0, which bakes Godot's
    dead-flat default per the m03/m04/m05 precedent) but is raised to 0.10
    below, after folding a second, coarser noise ("orange peel") into the
    normal input -- Grayson's 2026-09-15 iteration feedback on the clearcoat
    demo was that the surface "feels flat / missing surface detail"; the
    paint's own surface is still meant to read as glossy lacquer, not a bare
    bump map, so the added relief is a broad wave layered under the flake
    sparkle rather than replacing it."""
    g = _from_scratch_noise_material(
        {"scale_x": 8, "scale_y": 8},
        [(0.0, 0.45, 0.03, 0.05), (1.0, 0.62, 0.05, 0.08)],
        metallic=1.0, roughness=0.16, normal_amount=0.04)
    add_node(g, "colorize_rough", "colorize",
             {"gradient": _grad([(0.0, 0.12, 0.12, 0.12), (1.0, 0.20, 0.20, 0.20)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "colorize_rough", "to_port": 0})

    # Metallic-flake sparkle: voronoi port 0 ("Nodes") is a grayscale
    # distance-to-cell-center field, near 0 at each cell's center and
    # growing outward -- a hard low-end threshold on that field isolates a
    # small bright disc at each cell center (a sparse fleck pattern) rather
    # than the cell borders. FlakeMask inverts that (low value = 0.05 at the
    # flecks, 1.0 everywhere else) so it can be Darken-blended onto
    # RoughnessVariation: Darken picks min(c1, c2), so it punches roughness
    # down to ~0.05 (a glossy sparkle) only where the mask is low, and
    # passes RoughnessVariation through unchanged everywhere else.
    add_node(g, "voronoi_0", "voronoi", {"scale_x": 48, "scale_y": 48})
    add_node(g, "colorize_flake", "colorize",
             {"gradient": _grad([(0.0, 0.05, 0.05, 0.05), (0.15, 0.05, 0.05, 0.05),
                                  (0.16, 1, 1, 1), (1.0, 1, 1, 1)])})
    add_node(g, "blend_0", "blend", {"blend_type": 10, "amount": 1})
    g["connections"].append(
        {"from": "voronoi_0", "from_port": 0, "to": "colorize_flake", "to_port": 0})
    g["connections"].append(
        {"from": "colorize_flake", "from_port": 0, "to": "blend_0", "to_port": 0})
    g["connections"].append(
        {"from": "colorize_rough", "from_port": 0, "to": "blend_0", "to_port": 1})
    g["connections"].append(
        {"from": "blend_0", "from_port": 0, "to": "Material", "to_port": 2})

    # Orange-peel surface detail (2026-09-15, Grayson's iteration feedback:
    # the clearcoat demo "feels flat / missing surface detail"). MicroNoise
    # (perlin_0, 8x8) stays untouched -- it still drives albedo/roughness/
    # flake fan-out and its deep base colors are already approved. Add an
    # independent, coarser-frequency noise (real automotive orange-peel is a
    # broader wave than the micro-grain) and fold it into the normal input
    # via a math add, the same technique s06 (cookbook_stone.py) used to
    # combine grain_scaled + height_relief before normal_map_0.
    add_node(g, "orange_peel", "perlin", {"scale_x": 14, "scale_y": 14, "iterations": 2})
    add_node(g, "peel_scaled", "math", {"op": 2, "default_in2": 0.6})   # 2 = A*B: weight the wave
    add_node(g, "normal_height", "math", {"op": 0})                    # 0 = A+B: micro + orange peel
    g["connections"] += [
        {"from": "orange_peel", "from_port": 0, "to": "peel_scaled", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "normal_height", "to_port": 0},
        {"from": "peel_scaled", "from_port": 0, "to": "normal_height", "to_port": 1},
    ]
    rewire(g, "normal_map_0", 0, "normal_height", 0)
    # Raise relief strength enough for the combined wave to read without
    # going rough -- was 0.04 (chrome/other from-scratch materials' shared
    # precedent, set inside _from_scratch_noise_material above); override
    # here rather than editing that shared helper call. Starting point for
    # the render-and-look loop, not a locked value.
    set_param(g, "normal_map_0", "param1", 0.10)
    # Direct normal path (2026-09-27): the helper's buffered param4=1 races to a
    # flat normal headless; param4=0 at the same param1 matches within 0.37/255.
    set_param(g, "normal_map_0", "param4", 0)

    group_into_subgraph(
        g, ["perlin_0", "colorize_0", "colorize_rough", "voronoi_0",
            "colorize_flake", "blend_0", "normal_map_0",
            "orange_peel", "peel_scaled", "normal_height"],
        "car_paint_finish", "Car Paint Finish",
        [("perlin_0", "scale_x", "param0", "Micro-variation scale"),
         ("colorize_0", "gradient", "param1", "Paint color"),
         ("colorize_rough", "gradient", "param2", "Base roughness"),
         ("voronoi_0", "scale_x", "param3", "Flake size"),
         ("normal_map_0", "param1", "param4", "Micro relief")],
        catalog,
    )
    rename_nodes(g, _M06_NAMES)
    return save_variant(g, _LABEL, "m06_car_paint", 1)


BUILDERS = {
    "m01_weathered_copper": build_m01_weathered_copper,
    "m02_brushed_metal": build_m02_brushed_metal,
    "m06_car_paint": build_m06_car_paint,
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
