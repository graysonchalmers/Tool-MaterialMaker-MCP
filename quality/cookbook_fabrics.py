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
                    take_variant, rename_nodes)
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
