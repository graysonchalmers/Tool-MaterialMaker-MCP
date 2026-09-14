"""Cookbook growth: fabric-category authoring recipes beyond the frozen 15-case
Phase 3 test set (see docs/evidence/phase3/test_set.json's freeze note -- this is additive,
not an edit to those cases). Informal: 1 variant per material, no scorecard
gate. Reuses author_helpers.py's graph-surgery helpers; outputs land under
quality/authored/cookbook-fabrics/<case>/v1.ptex, same layout convention as
the Phase 3 iterations.

Run: python -m quality.cookbook_fabrics
Then `python -m quality.render_cookbook` renders each variant for inspection.
"""
import sys

from quality.author_helpers import (load_example, node, set_gradient, set_param, retype,
                    rewire, add_node, save_variant, group_into_subgraph,
                    take_variant, rename_nodes, _from_scratch_noise_material, _grad)
from quality import author  # shared builder base; regression guard is promote_cookbook --check

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-fabrics"

# Every crocodile_skin-derived material shares the same donor shape:
# voronoi_0 (generator, retyped per material) -> colorize_1 (albedo),
# colorize_3 (roughness), colorize_0 (0/1 ramp feeding normal_map_0), plus
# uniform_0 (flat black constant into Material's metallic port). Per-material
# dicts below give each donor clone its own role names since the generator's
# type and the material's identity differ (weave vs diagonal_weave vs perlin,
# denim vs burlap vs velvet), matching cookbook_scifi.py's per-material
# _SFxx_NAMES precedent rather than one shared dict. `uniform_0` gets the
# same "NonMetallic" name every category in this retrofit uses for a flat
# black constant into the metallic port.
_F01_WOVEN_DENIM_NAMES = {
    "voronoi_0": "TwillLayout",       # diagonal_weave twill generator
    "colorize_1": "DenimColor",
    "colorize_3": "DenimRoughness",
    "colorize_0": "TwillHeight",      # 0/1 ramp feeding the normal map
    "normal_map_0": "TwillNormal",
    "uniform_0": "NonMetallic",
}

# The weave/weave2 family convention (see the task brief): the pattern node
# is WeaveLayout, its stitch colorize ThreadColor.
_F03_CANVAS_BURLAP_NAMES = {
    "voronoi_0": "WeaveLayout",       # weave (over/under plain weave)
    "colorize_1": "ThreadColor",
    "colorize_3": "BurlapRoughness",
    "colorize_0": "WeaveHeight",
    "normal_map_0": "WeaveNormal",
    "uniform_0": "NonMetallic",
}

_F04_WOOL_KNIT_NAMES = {
    "voronoi_0": "WeaveLayout",       # weave, coarse+wide-width stand-in for knit
    "colorize_1": "ThreadColor",
    "colorize_3": "KnitRoughness",
    "colorize_0": "WeaveHeight",
    "normal_map_0": "WeaveNormal",
    "uniform_0": "NonMetallic",
}

# diagonal_weave, not the weave/weave2 family, so its own layout name;
# satin uses *Sheen* for the anisotropic roughness chain per the brief.
_F05_SILK_SATIN_NAMES = {
    "voronoi_0": "SatinWeaveLayout",  # diagonal_weave at a near-invisible scale
    "colorize_1": "SatinColor",
    "colorize_3": "SatinSheen",
    "colorize_0": "SatinHeight",
    "normal_map_0": "SatinNormal",
    "uniform_0": "NonMetallic",
}

# perlin retype: "the fibre perlin FiberNoise" per the brief. Velvet also
# uses *Sheen* for its roughness chain.
_F06_VELVET_NAMES = {
    "voronoi_0": "FiberNoise",        # perlin, continuous fiber-like grain
    "colorize_1": "VelvetColor",
    "colorize_3": "VelvetSheen",
    "colorize_0": "FiberHeight",
    "normal_map_0": "FiberNormal",
    "uniform_0": "NonMetallic",
}

# weave2 stitch=3: the chevron reads as herringbone, so the pattern node
# gets its own name per the brief rather than the generic WeaveLayout.
_F07_HERRINGBONE_TWEED_NAMES = {
    "voronoi_0": "HerringboneLayout",
    "colorize_1": "TweedColor",
    "colorize_3": "TweedRoughness",
    "colorize_0": "HerringboneHeight",
    "normal_map_0": "HerringboneNormal",
    "uniform_0": "NonMetallic",
}

# weave2 stitch=1 (plain weave, no herringbone chevron), so the base weave
# uses the generic WeaveLayout/ThreadColor names; the independent fleck
# voronoi is FleckSource and its hard threshold FleckMask per the brief
# (see the memory note on f08's blend/opacity-mask caution).
_F08_DONEGAL_TWEED_NAMES = {
    "voronoi_0": "WeaveLayout",
    "colorize_1": "ThreadColor",
    "colorize_3": "TweedRoughness",
    "colorize_0": "WeaveHeight",
    "normal_map_0": "WeaveNormal",
    "uniform_0": "NonMetallic",
    "voronoi_fleck": "FleckSource",
    "colorize_fleck_mask": "FleckMask",
    "colorize_fleck_color": "FleckColor",
    "blend_fleck": "FleckComposite",
}


def _group_weave_family(g, catalog, *, pattern_name, pattern_label, color_label,
                         density_param, density_label, finish_label):
    """Shared grouping for f03/f04/f05/f06/f07: all five clone `crocodile_skin`
    and keep its identical voronoi(retyped)->{colorize_0, colorize_1,
    colorize_3} fan-out untouched structurally (only the generator's type/
    params and the three colorize gradients differ per material). Same donor
    and same shape already grouped this way for o04_snake_scales/o05_coral in
    cookbook_organics.py's `_group_crocodile_skin_pattern` -- reused here with
    per-material pattern names/labels instead of a single generic "Surface
    Pattern" label, since each fabric's generator type (weave/weave2/
    diagonal_weave/perlin) is different enough to deserve its own name.

    Per the task's blend caution: this donor carries NO `blend` node at all
    (see quality/donors/crocodile_skin.ptex's own `connections` list), so
    there is no port-source tracing to do here. The only structural subtlety
    is that `voronoi_0` (the retyped generator) is a single upstream node
    feeding THREE downstream consumers (colorize_0 for normal, colorize_1
    for albedo, colorize_3 for roughness), so it cannot sit inside both a
    "pattern" and a "surface finish" group at once -- it is folded into the
    pattern group (paired with colorize_1, the albedo it drives most
    directly), matching the organics precedent, so colorize_0/normal_map_0/
    colorize_3 read its output across the group boundary. `uniform_0`
    (Material's untouched metallic scalar, always 0 and never touched by any
    of these builders) is left top-level, also matching the organics
    precedent -- a single donor-default node feeding one port directly, not
    a generative/compositing chain worth collapsing."""
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1"], pattern_name, pattern_label,
        [("voronoi_0", density_param, "param0", density_label),
         ("colorize_1", "gradient", "param1", color_label)],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_0", "colorize_3", "normal_map_0"], "surface_finish",
        "Surface Finish",
        [("colorize_3", "gradient", "param0", finish_label),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )


def build_f03_canvas_burlap(catalog: dict) -> str:
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

    _group_weave_family(
        g, catalog, pattern_name="weave_pattern", pattern_label="Weave Pattern",
        color_label="Burlap color", density_param="width",
        density_label="Thread gap", finish_label="Roughness",
    )
    rename_nodes(g, _F03_CANVAS_BURLAP_NAMES)
    return save_variant(g, _LABEL, "f03_canvas_burlap", 1)


def build_f04_wool_knit(catalog: dict) -> str:
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

    _group_weave_family(
        g, catalog, pattern_name="knit_pattern", pattern_label="Knit Pattern",
        color_label="Wool color", density_param="columns",
        density_label="Rib count", finish_label="Roughness",
    )
    rename_nodes(g, _F04_WOOL_KNIT_NAMES)
    return save_variant(g, _LABEL, "f04_wool_knit", 1)


def build_f05_silk_satin(catalog: dict) -> str:
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

    _group_weave_family(
        g, catalog, pattern_name="weave_pattern", pattern_label="Weave Pattern",
        color_label="Satin color", density_param="size",
        density_label="Weave scale", finish_label="Sheen",
    )
    rename_nodes(g, _F05_SILK_SATIN_NAMES)
    return save_variant(g, _LABEL, "f05_silk_satin", 1)


def build_f06_velvet(catalog: dict) -> str:
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

    _group_weave_family(
        g, catalog, pattern_name="fiber_pattern", pattern_label="Fiber Pattern",
        color_label="Velvet color", density_param="iterations",
        density_label="Fiber grain", finish_label="Roughness",
    )
    rename_nodes(g, _F06_VELVET_NAMES)
    return save_variant(g, _LABEL, "f06_velvet", 1)


def build_f07_herringbone_tweed(catalog: dict) -> str:
    """Herringbone tweed: retype the generator to `weave2` with stitch=3, which
    renders the classic herringbone chevron (diagonal ribbons that reverse
    direction band to band). This slot came out of a geometry probe for wool
    loop-knit: isolation renders proved the catalog has NO stockinette-knit
    generator (bricks running-bond -> staggered pillow honeycomb; weave2 stitch=1
    -> plain basket weave; only weave2 stitch=3 shows the chevron the knit look
    needs, but the chevrons reverse per band, which is herringbone tweed, not
    upright-V stockinette). So knit-loop stays the honest limit and this ships the
    genuinely good material the probe found instead. Warm brown Harris-tweed
    three-tone (espresso / tan / cream) for the woven two-color heather, very
    matte wool roughness, soft rounded-ribbon normal (param1 low so the chevron
    reads as pressed tweed relief, not sharp thread crossings). Directly-fed
    analytic generator -> normal_map param4=0 fix."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "weave2",
           {"columns": 8, "rows": 8, "width_x": 0.8, "width_y": 0.8, "stitch": 3})
    set_gradient(g, "colorize_1", [    # warm brown tweed, dark-to-cream heather
        (0.0, 0.18, 0.14, 0.10),
        (0.5, 0.42, 0.34, 0.24),
        (1.0, 0.72, 0.65, 0.52),
    ])
    set_gradient(g, "colorize_3", [    # very matte wool
        (0.0, 0.86, 0.86, 0.86),
        (1.0, 0.96, 0.96, 0.96),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.35, "param2": 0, "param4": 0}

    _group_weave_family(
        g, catalog, pattern_name="herringbone_pattern",
        pattern_label="Herringbone Pattern", color_label="Tweed color",
        density_param="columns", density_label="Weave scale",
        finish_label="Roughness",
    )
    rename_nodes(g, _F07_HERRINGBONE_TWEED_NAMES)
    return save_variant(g, _LABEL, "f07_herringbone_tweed", 1)


def build_f08_donegal_tweed(catalog: dict) -> str:
    """Donegal-style flecked tweed: unlike f07 (which differentiates through
    weave GEOMETRY), this differentiates through COLOR -- a plain weave2
    base (stitch=1, no herringbone chevron) with the voronoi-port-2
    per-cell-random fleck lever (already proven on granite/masonry) layered
    on top as small, sparse, contrasting-color nubs, the classic Donegal
    look. The fleck source is a SEPARATE voronoi node (`voronoi_fleck`),
    not the base generator -- retyping voronoi_0 to weave2 for the base
    loses its own rand3 output, and the flecks want a much finer, unrelated
    cell frequency than the coarse weave grid anyway. The fleck mask is a
    hard-threshold colorize of that voronoi's port 2 (rand3): only the top
    ~10% of cell values pass, so flecks read as sparse scattered nubs, not
    a wash. Composited with `blend` (`blend_type=0` explicit, base weave on
    the majority port 1, flecks on the minority port 0, the sparse mask on
    port 2 -- the blend shows port 1 where the mask is 0 and port 0 where
    it's 1, so the majority layer belongs on port 1). Warm heather
    gray-brown base, cream/tan flecks, very matte wool roughness. Relief
    stays the weave's own (fleck nubs are color-only, no extra bump), a
    deliberate simplification noted in the recipe card."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "weave2",
           {"columns": 10, "rows": 10, "width_x": 0.85, "width_y": 0.85, "stitch": 1})
    set_gradient(g, "colorize_1", [    # heather gray-brown base weave
        (0.0, 0.20, 0.18, 0.16),
        (0.5, 0.38, 0.34, 0.29),
        (1.0, 0.56, 0.51, 0.44),
    ])
    set_gradient(g, "colorize_3", [    # very matte wool
        (0.0, 0.86, 0.86, 0.86),
        (1.0, 0.96, 0.96, 0.96),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.3, "param2": 0, "param4": 0}

    add_node(g, "voronoi_fleck", "voronoi",
             {"scale_x": 36, "scale_y": 36, "randomness": 1})
    add_node(g, "colorize_fleck_mask", "colorize",
             {"gradient": {"interpolation": 1, "type": "Gradient", "points": [
                 {"a": 1, "r": 0, "g": 0, "b": 0, "pos": 0.0},
                 {"a": 1, "r": 0, "g": 0, "b": 0, "pos": 0.78},
                 {"a": 1, "r": 1, "g": 1, "b": 1, "pos": 0.84},
                 {"a": 1, "r": 1, "g": 1, "b": 1, "pos": 1.0}]}})
    add_node(g, "colorize_fleck_color", "colorize",     # cream/rust two-tone flecks
             {"gradient": {"interpolation": 1, "type": "Gradient", "points": [
                 {"a": 1, "r": 0.85, "g": 0.78, "b": 0.62, "pos": 0.78},
                 {"a": 1, "r": 0.62, "g": 0.28, "b": 0.16, "pos": 0.90},
                 {"a": 1, "r": 0.90, "g": 0.83, "b": 0.66, "pos": 1.0}]}})
    add_node(g, "blend_fleck", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "voronoi_fleck", "from_port": 2, "to": "colorize_fleck_mask", "to_port": 0},
        {"from": "voronoi_fleck", "from_port": 2, "to": "colorize_fleck_color", "to_port": 0},
        {"from": "colorize_fleck_color", "from_port": 0, "to": "blend_fleck", "to_port": 0},
        {"from": "colorize_1", "from_port": 0, "to": "blend_fleck", "to_port": 1},
        {"from": "colorize_fleck_mask", "from_port": 0, "to": "blend_fleck", "to_port": 2},
    ]
    rewire(g, "Material", 0, "blend_fleck", 0)

    # Extra scrutiny per the task brief: this is the material the fleck/blend
    # caution is specifically about. `blend_fleck`'s port sources were traced
    # from the connections list assembled above (not assumed from the
    # docstring, which predates this retrofit):
    #   port0 (minority, shows where mask=1) <- colorize_fleck_color
    #   port1 (majority, shows where mask=0) <- colorize_1 (the base weave)
    #   port2 (mask)                         <- colorize_fleck_mask
    # The fleck voronoi (`voronoi_fleck`) and its two colorize consumers are
    # kept in their OWN group ("fleck_pattern"), separate from the base
    # weave's group ("base_weave"), so the "Fleck density" knob
    # (voronoi_fleck.scale_x) stays a distinct, independently tunable thing
    # rather than disappearing into the same opaque group as the weave it's
    # blended over. `blend_fleck` itself gets a THIRD group
    # ("fleck_composite") rather than folding into either side: all three of
    # its inputs are external (majority from base_weave, minority+mask from
    # fleck_pattern), the same shape pm03's paint_metal_composite used in
    # cookbook_painted_metal.py for an analogous three-input composite blend.
    # group_into_subgraph preserves each incoming connection's own to_port
    # independently when rehoming it through gen_inputs, so grouping cannot
    # swap which source lands on port0 vs port1 vs port2.
    _group_weave_family(
        g, catalog, pattern_name="base_weave", pattern_label="Base Weave",
        color_label="Tweed color", density_param="columns",
        density_label="Weave scale", finish_label="Roughness",
    )
    group_into_subgraph(
        g, ["voronoi_fleck", "colorize_fleck_mask", "colorize_fleck_color"],
        "fleck_pattern", "Fleck Pattern",
        [("voronoi_fleck", "scale_x", "param0", "Fleck density"),
         ("colorize_fleck_color", "gradient", "param1", "Fleck color")],
        catalog,
    )
    group_into_subgraph(
        g, ["blend_fleck"], "fleck_composite", "Fleck Composite",
        [("blend_fleck", "amount", "param0", "Fleck strength")],
        catalog,
    )
    rename_nodes(g, _F08_DONEGAL_TWEED_NAMES)
    return save_variant(g, _LABEL, "f08_donegal_tweed", 1)


# fbm Cellular 3 crosshatch grid: the pattern node gets its own PlaidGrid
# name (the fbm generator IS the plaid layout, not a stand-in weave), and
# the roughness node is FlannelRoughness rather than the generic
# *Roughness naming other builders use, since the material identity is
# "flannel" specifically.
_F09_PLAID_FLANNEL_NAMES = {
    "voronoi_0": "PlaidGrid",
    "colorize_1": "PlaidColor",
    "colorize_3": "FlannelRoughness",
    "colorize_0": "PlaidHeight",
    "normal_map_0": "PlaidNormal",
    "uniform_0": "NonMetallic",
}


def build_f09_plaid_flannel(catalog: dict) -> str:
    """Plaid flannel: retype crocodile_skin's generator to `fbm` with
    `noise=4` (Cellular 3, "woven crosshatch grid" per AUTHORING.md's noise
    vocabulary table) instead of the raw voronoi cells every other
    crocodile_skin-derived fabric in this file uses. This is a genuinely
    different structural family from f07_herringbone_tweed/f08_donegal_tweed
    (both built on `weave2`, plus f08's independent overlay voronoi for its
    flecks): here the crosshatch grid the base generator itself produces IS
    the plaid pattern, not a woven simulation recolored to look plaid.

    Polarity and value distribution measured directly, not assumed: read
    the tracked quality/cookbook/noise-gallery/fbm_4_cellular3 swatch (fbm
    noise=4, scale 4, iterations=3, persistence=0.5, straight 0-black/1-
    white ramp) with quality/pngread.py and histogrammed it. Two findings
    drove the params below:
    (1) The value distribution is a narrow BELL CURVE centered on ~0.5
    (roughly 65% of pixels fall in 0.35-0.65, under 2% in either tail
    below 0.15 or above 0.9), not spread evenly across 0..1. A naive
    3-stop ramp at 0/0.5/1 therefore let the stripe color at pos 0.5 --
    sitting right on the histogram's peak -- swallow the whole tile (first
    pass measured red covering roughly 70% of the render, checked by eye).
    A tight plateau at the opposite extreme (flat color bands narrower
    than the bell curve's spread) was tried next and made the low-value
    crossing regions read as isolated blob-shaped patches rather than a
    connected grid (also checked by eye on a render, not assumed) --
    because at the brief's starting scale_x/scale_y=4 each crosshatch
    valley occupies a large fraction of its own coarse cell, so isolating
    just that valley by value reads as "a spot per cell", not "a line
    crossing the tile".
    (2) Fix: scale_x/scale_y raised from the brief's diagnostic 4 to 10 --
    more repeats means each crossing valley is a proportionally smaller
    fraction of its cell, so thresholding it now reads as thin bands
    connecting into a grid instead of a spot per cell (the same "raise the
    noise-gallery diagnostic scale for the actual material" move l07 made
    on its own fbm retype, for the same reason: a swatch tuned to keep one
    basis legible per tile is not tuned for how that basis should read at
    material scale).

    Palette: colorize_1 keeps a plain 3-stop ramp (0.0 navy, 0.5 red, 1.0
    cream) -- once the denser grid fixed the blobbing, the bell-curve
    weighting toward 0.5 became a feature, not a bug: it is exactly what
    keeps the crossing red stripe reading as a stripe rather than
    vanishing into a hairline. Colors kept muted (desaturated brick-red
    and deep navy, not saturated tartan colors) against a heather-cream
    base so it reads as flannel, not a printed tartan. Soft, low-contrast matte
    roughness throughout (no sheen split between grid and cell, unlike
    f05's satin weave). Reused the donor's plain 0-black/1-white colorize_0
    ramp for height (same convention as f03-f08) and normal_map_0
    param4=0 (the standing flat-normal fix). param1 (relief strength)
    started at the brief's suggested LOW value (0.15) for a soft brushed
    nap, but Grayson reviewed the first preview and flagged it as reading
    too flat -- the crosshatch grid barely showed under lighting. Raised
    to 0.42 (moderate: enough that the grid reads clearly on lit
    surfaces, comparable to f03_canvas_burlap's coarse-thread relief,
    while staying well under a hard-relief material like stone) -- see
    the task report's second iteration for the before/after render
    comparison."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "fbm",
           {"noise": 4, "scale_x": 10, "scale_y": 10, "folds": 0,
            "iterations": 3, "persistence": 0.5})
    set_gradient(g, "colorize_1", [    # base/stripe/overcheck plaid read
        (0.0, 0.14, 0.16, 0.28),   # crossing intersections: muted navy overcheck
        (0.5, 0.50, 0.22, 0.18),   # single grid lines: muted brick-red stripe
        (1.0, 0.80, 0.74, 0.62),   # cell interior: heather-cream base
    ])
    set_gradient(g, "colorize_3", [    # soft matte flannel, low contrast
        (0.0, 0.82, 0.82, 0.82),
        (1.0, 0.92, 0.92, 0.92),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.42, "param2": 0, "param4": 0}

    _group_weave_family(
        g, catalog, pattern_name="plaid_pattern", pattern_label="Plaid Pattern",
        color_label="Plaid color", density_param="scale_x",
        density_label="Check size", finish_label="Roughness",
    )
    rename_nodes(g, _F09_PLAID_FLANNEL_NAMES)
    return save_variant(g, _LABEL, "f09_plaid_flannel", 1)


# fbm Cellular 5 soft diagonal weave: like f09, the fbm generator IS the
# pattern here (a loop-blob basis, not a stand-in weave donor), so the
# generator node gets its own BoucleLoop name rather than the generic
# WeaveLayout other builders use.
_F10_BOUCLE_UPHOLSTERY_NAMES = {
    "voronoi_0": "BoucleLoop",
    "colorize_1": "BoucleColor",
    "colorize_3": "BoucleRoughness",
    "colorize_0": "BoucleHeight",
    "normal_map_0": "BoucleNormal",
    "uniform_0": "NonMetallic",
}


def build_f10_boucle_upholstery(catalog: dict) -> str:
    """Boucle upholstery: retype crocodile_skin's generator to `fbm` with
    `noise=6` (Cellular 5, "soft diagonal weave" per AUTHORING.md's noise
    vocabulary table -- "brushed cloth, quilted softness"). Same
    donor/retype shape as f09_plaid_flannel's Cellular 3 (and l07's
    Cellular 1 in cookbook_leather.py), a different Cellular index for a
    structurally different family: Cellular 3 gives a hard crosshatch grid
    (f09's plaid), Cellular 1 gives worley cells with dark centers (l07's
    pebbles), Cellular 5 gives soft rounded blobs with mild diagonal
    linking and no hard cell edges at all -- the closest basis in this
    catalog to bouclé's tight, irregular nubby loop texture.

    Viewed the tracked quality/cookbook/noise-gallery/fbm_6_cellular5
    swatch (fbm noise=6, scale 4, iterations=3, persistence=0.5, straight
    0-black/1-white ramp) directly before choosing params: at that
    diagnostic scale it reads as a handful of large soft dark blobs on a
    lighter mid-gray field, with faint diagonal connective haze between
    them -- confirming the "soft diagonal weave" character, and confirming
    (same polarity documented for Cellular 1 in l07's builder) that low
    values sit at the blob centers, high values in the surrounding field.
    scale_x/scale_y raised from the brief's diagnostic 4 to 28 -- higher
    than f09's plaid fix (10) or l07's pebble fix (20) -- because bouclé
    loops read as much tighter and more numerous than a plaid check or a
    pebbled-leather grain; at 28 the blobs shrink to a dense field of small
    nubs rather than a few large blotches, the same "raise the
    noise-gallery diagnostic scale for the actual material" move both
    those builders made.

    Palette: cream/heathered-gray (per the brief, distinct from
    f04_wool_knit's warmer oatmeal weave-donor ribs and from f09's navy/
    brick-red plaid). Low value (blob/loop centers) gets a cream highlight
    -- the loop tops catching light -- and high value (the field between
    loops) shades to a cooler heather gray, with a mid heather-beige stop
    for variation. High matte roughness throughout, no sheen (a nubby
    upholstery weave has no glossy component, unlike f05's satin).

    Relief: normal_map param1=0.25. The brief calls for LOW relief for a
    "soft nubby bump rather than hard relief," but f09_plaid_flannel's
    first pass at the brief's suggested-low 0.15 read as too flat on
    review and needed a second iteration (raised to 0.42) to visibly read.
    0.25 is chosen as a value that should read clearly on a first pass --
    well above f09's flat-reading 0.15, close to f04_wool_knit's approved
    0.3 for its rounded ribs -- while staying clearly softer than f09's
    final hard-crosshatch 0.42, appropriate for bouclé's rounded, irregular
    loops rather than f09's straight grid lines. param4=0 is the standing
    flat-normal fix.

    Distinct from f06_velvet (a continuous perlin fiber grain with no cell
    structure at all -- smooth pile, not loops) and from f09_plaid_flannel
    (a hard crosshatch GRID from the same fbm family, straight lines
    crossing at right angles, vs this soft, irregular, diagonal cell
    pattern with no straight edges)."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "fbm",
           {"noise": 6, "scale_x": 28, "scale_y": 28, "folds": 0,
            "iterations": 3, "persistence": 0.5})
    set_gradient(g, "colorize_1", [    # cream loop highlights, heather-gray field
        (0.0, 0.80, 0.76, 0.68),   # loop tops (low value): cream highlight
        (0.5, 0.64, 0.60, 0.55),   # mid heather-beige
        (1.0, 0.44, 0.42, 0.40),   # field between loops (high value): cool gray
    ])
    set_gradient(g, "colorize_3", [    # very matte, no sheen
        (0.0, 0.85, 0.85, 0.85),
        (1.0, 0.95, 0.95, 0.95),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.25, "param2": 0, "param4": 0}

    _group_weave_family(
        g, catalog, pattern_name="loop_pattern", pattern_label="Loop Pattern",
        color_label="Boucle color", density_param="scale_x",
        density_label="Loop density", finish_label="Roughness",
    )
    rename_nodes(g, _F10_BOUCLE_UPHOLSTERY_NAMES)
    return save_variant(g, _LABEL, "f10_boucle_upholstery", 1)


# Directional-noise-derived: the generator IS the rib pattern (an anisotropic
# composite noise, not a woven-donor stand-in), so it gets its own RibNoise
# name per the naming convention f09/f10 established for fbm-generator
# materials that use the generator's raw pattern directly.
_F11_CORDUROY_NAMES = {
    "perlin_0": "RibNoise",       # directional_noise, retyped from the placeholder perlin
    "colorize_0": "CorduroyColor",
    "normal_map_0": "RibNormal",
    "rough_const": "RoughnessConst",
}


def build_f11_corduroy(catalog: dict) -> str:
    """Corduroy: the first cookbook material to use `directional_noise`, a
    compound node with an internal `switch` selecting one of three composite
    sub-networks ("Noise 1"/"Noise 2"/"Noise 3" per `param0` 0/1/2). No
    crocodile_skin donor has this topology, so this is built from scratch via
    `_from_scratch_noise_material` (the same shape `t09_rippled_wet_sand`
    uses in cookbook_terrain.py, the exact template for this whole builder),
    then `retype()`d from the placeholder `perlin_0` to `directional_noise`
    at its own defaults (`param0=0` "Noise 1", `n_scale=1`, `param1=11`,
    read from `directional_noise.mmg`'s `gen_parameters` block). Output port
    0 is a plain `f` scalar on both node types, so the swap is
    connection-safe.

    Verification render (required before trusting any `param0` mode reads as
    ribbing, since the brief only describes the modes from their internal
    `fbm2` scale parameters, not a rendered look): used the MCP
    `render_node_output` tool directly on an isolated
    directional_noise->colorize->Material graph (n_scale=1, param1=11,
    straight 0-black/1-white ramp), size 512, rendered ALL THREE modes in
    turn (one Godot process at a time) rather than stopping at the first.

    Honest description of what each mode actually shows (this replaces an
    earlier, overstated first-pass description that called mode 0 "clean,
    regular ribbing" without having rendered the other two to compare --
    caught in review):
    - `param0=0` ("Noise 1", `f11_verify_mode0_albedo.png`): anisotropic
      horizontal streaking, but genuinely IRREGULAR -- variable band width,
      wandering/wobbling lines, uneven spacing. Not clean parallel ribbing.
    - `param0=1` ("Noise 2", `f11_verify_mode1_albedo.png`): also
      anisotropic horizontal streaking over a finer grain, but LESS regular
      than mode 0, not more.
    - `param0=2` ("Noise 3", `f11_verify_mode2_albedo.png`): smooth, blurry,
      widely-spaced soft waves with no fine grain at all -- essentially a
      single broad feature repeated across the tile, not a repeating rib
      pattern, and visually the worst match of the three.

    Measured, not just eyeballed, since "regular" is exactly the property
    in question: wrote a one-off script (not committed, scratch-only) that
    reads each PNG via `quality/pngread.py`, averages each row's brightness
    across the full width, smooths that profile (25px moving average, to
    separate macro-scale banding from per-pixel grain noise), thresholds
    against the median to find band runs, and reports the coefficient of
    variation (stdev/mean) of both the gap between band centers and the
    band widths -- lower CoV means more regular/evenly-spaced. Results:
    mode 0 gap CoV=0.436, width CoV=0.615 (15 bands); mode 1 gap CoV=0.542,
    width CoV=0.625 (11 bands, both worse than mode 0); mode 2 found only 2
    macro-bands across the whole 2048px tile (CoV near 0, but only because
    there is no repeating structure to be irregular about -- confirming the
    visual read that it isn't ribbing at all).

    Verdict: kept `param0=0` as the best of three real options, not because
    it matches an idealized "clean parallel ribbing" description. It is the
    most regular of the two modes that show genuine repeating anisotropic
    banding, and a structurally different family from the cellular/blotchy
    fbm looks used elsewhere in this category (the brief's actual concern),
    even though it does not read as tight, evenly-spaced corduroy wales the
    way a literal photo reference would. This is a real limitation of this
    material worth flagging in its eventual recipe card, not a claim that
    the technique nails corduroy's regularity.

    `n_scale` (range 1-8) is exposed as the rib density knob -- it scales
    every internal fbm2/perlin/tiler branch inside "Noise 1" together, so
    raising it tightens the ribs without needing to touch any internal
    sub-network directly.

    Warm tan corduroy palette: dark umber in the rib grooves, warm tan
    base, a lighter tan highlight on the rib crests -- a real 3-stop ramp
    (not just 2 stops) so the ribbing itself carries the color variation,
    matching the noise field's own light/dark banding rather than a flat
    tint. Soft matte roughness (fabric, not shiny) fed as a flat texture via
    `rough_const` so an ORM map exports, the same `t09`/`p01` lesson every
    from-scratch cookbook material follows. `normal_map` `param4=0` is the
    standing flat-normal fix for a directly-fed analytic generator.
    `param1` (relief strength) set to 0.55 -- stronger than
    `f09_plaid_flannel`'s final 0.42 (a woven-crosshatch nap) and well above
    `f04_wool_knit`'s 0.3 (soft rounded ribs), because corduroy wales are a
    real, pronounced physical ridge, not a soft brushed or knit surface."""
    g = _from_scratch_noise_material(
        {"scale_x": 4, "scale_y": 4},   # placeholder; retyped to directional_noise below
        [(0.0, 0.22, 0.14, 0.08),   # dark umber shadow in the rib grooves
         (0.5, 0.52, 0.36, 0.21),   # warm tan base
         (1.0, 0.70, 0.54, 0.35)],  # light tan highlight on rib crests
        metallic=0.0, roughness=0.85, normal_amount=0.55)
    retype(g, "perlin_0", "directional_noise", {"param0": 0, "n_scale": 1, "param1": 11})
    set_param(g, "normal_map_0", "param4", 0)
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.85, 0.85, 0.85), (1.0, 0.85, 0.85, 0.85)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})

    group_into_subgraph(
        g, ["perlin_0", "colorize_0"], "corduroy_rib", "Corduroy Rib",
        [("perlin_0", "n_scale", "param0", "Rib density"),
         ("colorize_0", "gradient", "param1", "Corduroy color")],
        catalog,
    )
    group_into_subgraph(
        g, ["normal_map_0", "rough_const"], "corduroy_finish", "Corduroy Finish",
        [("rough_const", "gradient", "param0", "Roughness"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    rename_nodes(g, _F11_CORDUROY_NAMES)
    return save_variant(g, _LABEL, "f11_corduroy", 1)


def build_f01_woven_denim(catalog: dict) -> str:
    """Blue denim, folded in from the Phase-3 hero set (was
    examples/f01_woven_denim, iter1 variant 1). Graph unchanged from
    author.build_f01_woven_denim v1: `crocodile_skin` with its voronoi
    generator retyped to `diagonal_weave` so the twill drives albedo,
    roughness, and the normal, recolored indigo and matte, with the
    normal_map param4=0 fix that first unblocked flat normals project-wide.
    This builder only GROUPS it. `uniform_0` (the black metallic constant)
    stays top-level, the same convention the other crocodile_skin-derived
    materials use."""
    g = take_variant(author.build_f01_woven_denim, _LABEL, 1)
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "colorize_3"],
        "twill_weave", "Twill Weave",
        [("voronoi_0", "size", "param0", "Weave size"),
         ("colorize_1", "gradient", "param1", "Thread color"),
         ("colorize_3", "gradient", "param2", "Cloth roughness")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_0", "normal_map_0"],
        "weave_relief", "Weave Relief",
        [("normal_map_0", "param1", "param0", "Relief strength")],
        catalog,
    )
    rename_nodes(g, _F01_WOVEN_DENIM_NAMES)
    return save_variant(g, _LABEL, "f01_woven_denim", 1)


BUILDERS = {
    "f01_woven_denim": build_f01_woven_denim,
    "f03_canvas_burlap": build_f03_canvas_burlap,
    "f04_wool_knit": build_f04_wool_knit,
    "f05_silk_satin": build_f05_silk_satin,
    "f06_velvet": build_f06_velvet,
    "f07_herringbone_tweed": build_f07_herringbone_tweed,
    "f08_donegal_tweed": build_f08_donegal_tweed,
    "f09_plaid_flannel": build_f09_plaid_flannel,
    "f10_boucle_upholstery": build_f10_boucle_upholstery,
    "f11_corduroy": build_f11_corduroy,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    # Loaded once per script run (not once per builder), same convention as
    # cookbook_painted_metal.py/cookbook_scifi.py/cookbook_organics.py -- all
    # 6 materials need it for group_into_subgraph.
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
