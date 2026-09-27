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
                    rename_nodes, _from_scratch_noise_material, _grad,
                    place, tidy_ports, link_also, widen_widget)

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
    # Host (2026-09-27): the weave2 node now also draws plain weave and twill
    # (its Stitch is exposed), and height/normal follow whichever Pattern is
    # selected, so the Herringbone* names became WeaveLayout/Weave*.
    "voronoi_0": "WeaveLayout",
    "colorize_1": "TweedColor",
    "colorize_3": "TweedRoughness",
    "colorize_0": "WeaveHeight",
    "normal_map_0": "WeaveNormal",
    "uniform_0": "NonMetallic",
}


def _group_weave_family(g, catalog, *, pattern_name, pattern_label, color_label,
                         density_param, density_label, finish_label):
    """Shared grouping for f03/f04/f06/f07 (and f05_silk_satin, since retired
    into f07's presets): all of them clone `crocodile_skin`
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
    analytic generator -> normal_map param4=0 fix.

    WOVEN-PATTERN HOST (2026-09-27): absorbs f01_woven_denim, f05_silk_satin,
    f08_donegal_tweed and f09_plaid_flannel. All four are this same
    crocodile_skin shape (one generator feeding the albedo, roughness and
    height colorizes); only the generator differs. f08's is this graph's own
    weave2 (stitch 1, 10x10, width 0.85); f01 and f05 are one graph with
    different values (diagonal_weave, size 22 vs 48); f09 is fbm Cellular 3.
    So the host carries the two other generators in, and a Pattern selector
    picks which ONE signal feeds all three colorizes (colour, roughness and
    relief always read the same source, so they stay registered in every
    mode). The selector is one-hot weights in product-sum form
    (weave x w0 + twill x w1 + crosshatch x w2, the weights from A<B
    thresholds on one 0 / 0.5 / 1 value): exact in every mode, where a lerp
    or a blend (f -> rgba -> f) would drift. Each absorbed material is a
    preset that renders its original exactly. New layers default to a no-op,
    so the default renders today's f07 exactly:
    - Plaid Overlay (new): weave2's own warp and weft thread masks (ports 2
      and 1) paint vertical threads with a sett gradient along x and
      horizontal threads with the same sett along y, so the check is woven
      thread by thread and its colour edges sit on thread edges. Multiply
      blend, so the sett tints the tweed and the ribbon shading stays. Replaces
      f09's crosshatch-as-plaid, which never read as plaid (that crosshatch
      stays as a Pattern mode, for the exact f09 preset).
    - Fleck Layer (f08): f08's voronoi port-2 fleck nodes and values, colour
      only (as f08 shipped); Fleck strength 0 = off.
    Seeds: diagonal_weave and fbm are seeded from node position, so
    TwillLayout and CrosshatchGrid each sit at (71, 216) of their own
    subgraph, the spot the generator holds in f01/f05/f09, and FleckSource
    at (0, 0) as in f08. weave2 has no seed, so WeaveLayout is free to move.
    Presets are on the card (cookbook/fabrics/f07_herringbone_tweed.md)."""
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

    # --- Pattern selector: weave2 / diagonal twill (f01, f05) / crosshatch (f09) ---
    add_node(g, "TwillLayout", "diagonal_weave", {"size": 22})
    add_node(g, "CrosshatchGrid", "fbm",
             {"noise": 4, "scale_x": 10, "scale_y": 10, "folds": 0,
              "iterations": 3, "persistence": 0.5})
    add_node(g, "PatternSelect", "uniform_greyscale", {"color": 0})
    add_node(g, "IsWeave", "math", {"op": 15, "default_in2": 0.25})       # P < 0.25
    add_node(g, "IsCrosshatch", "math", {"op": 15, "default_in1": 0.75})  # 0.75 < P
    add_node(g, "WeaveOrCrosshatch", "math", {"op": 0})                  # A+B
    add_node(g, "IsTwill", "math", {"op": 1, "default_in1": 1})          # 1 - (A+B)
    add_node(g, "WeaveTerm", "math", {"op": 2})                          # A*B
    add_node(g, "TwillTerm", "math", {"op": 2})
    add_node(g, "CrosshatchTerm", "math", {"op": 2})
    add_node(g, "WeaveTwillSum", "math", {"op": 0})
    add_node(g, "PatternMix", "math", {"op": 0})
    g["connections"] += [
        {"from": "PatternSelect", "from_port": 0, "to": "IsWeave", "to_port": 0},
        {"from": "PatternSelect", "from_port": 0, "to": "IsCrosshatch", "to_port": 1},
        {"from": "IsWeave", "from_port": 0, "to": "WeaveOrCrosshatch", "to_port": 0},
        {"from": "IsCrosshatch", "from_port": 0, "to": "WeaveOrCrosshatch", "to_port": 1},
        {"from": "WeaveOrCrosshatch", "from_port": 0, "to": "IsTwill", "to_port": 1},
        {"from": "voronoi_0", "from_port": 0, "to": "WeaveTerm", "to_port": 0},
        {"from": "IsWeave", "from_port": 0, "to": "WeaveTerm", "to_port": 1},
        {"from": "TwillLayout", "from_port": 0, "to": "TwillTerm", "to_port": 0},
        {"from": "IsTwill", "from_port": 0, "to": "TwillTerm", "to_port": 1},
        {"from": "CrosshatchGrid", "from_port": 0, "to": "CrosshatchTerm", "to_port": 0},
        {"from": "IsCrosshatch", "from_port": 0, "to": "CrosshatchTerm", "to_port": 1},
        {"from": "WeaveTerm", "from_port": 0, "to": "WeaveTwillSum", "to_port": 0},
        {"from": "TwillTerm", "from_port": 0, "to": "WeaveTwillSum", "to_port": 1},
        {"from": "WeaveTwillSum", "from_port": 0, "to": "PatternMix", "to_port": 0},
        {"from": "CrosshatchTerm", "from_port": 0, "to": "PatternMix", "to_port": 1},
    ]
    for consumer in ("colorize_1", "colorize_3", "colorize_0"):
        rewire(g, consumer, 0, "PatternMix", 0)

    # --- Plaid overlay (new): sett stripes woven through weave2's thread masks ---
    for name, rotate in (("WarpStripes", 0), ("WeftStripes", 90)):
        add_node(g, name, "gradient", {"repeat": 1, "rotate": rotate, "mirror": False,
                                       "gradient": _sett(_PLAID_SETT)})
    # 2 = Multiply (blend_type is an index into blend.mmg's values list): the
    # sett tints the tweed colour, so the weave's ribbon shading shows
    # through. Normal (0) replaced it and read flat at strength 1.
    add_node(g, "WarpComposite", "blend", {"blend_type": 2, "amount": 0})
    add_node(g, "WeftComposite", "blend", {"blend_type": 2, "amount": 0})
    g["connections"] += [
        {"from": "WarpStripes", "from_port": 0, "to": "WarpComposite", "to_port": 0},
        {"from": "colorize_1", "from_port": 0, "to": "WarpComposite", "to_port": 1},
        {"from": "voronoi_0", "from_port": 2, "to": "WarpComposite", "to_port": 2},  # vertical
        {"from": "WeftStripes", "from_port": 0, "to": "WeftComposite", "to_port": 0},
        {"from": "WarpComposite", "from_port": 0, "to": "WeftComposite", "to_port": 1},
        {"from": "voronoi_0", "from_port": 1, "to": "WeftComposite", "to_port": 2},  # horizontal
    ]

    # --- Fleck layer (f08's nodes and values; strength 0 = off) ---
    add_node(g, "FleckSource", "voronoi", {"scale_x": 36, "scale_y": 36, "randomness": 1})
    add_node(g, "FleckMask", "colorize", {"gradient": {
        "interpolation": 1, "type": "Gradient", "points": [
            {"a": 1, "r": 0, "g": 0, "b": 0, "pos": 0.0},
            {"a": 1, "r": 0, "g": 0, "b": 0, "pos": 0.78},
            {"a": 1, "r": 1, "g": 1, "b": 1, "pos": 0.84},
            {"a": 1, "r": 1, "g": 1, "b": 1, "pos": 1.0}]}})
    add_node(g, "FleckColor", "colorize", {"gradient": {
        "interpolation": 1, "type": "Gradient", "points": [
            {"a": 1, "r": 0.85, "g": 0.78, "b": 0.62, "pos": 0.78},
            {"a": 1, "r": 0.62, "g": 0.28, "b": 0.16, "pos": 0.90},
            {"a": 1, "r": 0.90, "g": 0.83, "b": 0.66, "pos": 1.0}]}})
    add_node(g, "FleckComposite", "blend", {"blend_type": 0, "amount": 0})
    g["connections"] += [
        {"from": "FleckSource", "from_port": 2, "to": "FleckMask", "to_port": 0},
        {"from": "FleckSource", "from_port": 2, "to": "FleckColor", "to_port": 0},
        {"from": "FleckColor", "from_port": 0, "to": "FleckComposite", "to_port": 0},
        {"from": "WeftComposite", "from_port": 0, "to": "FleckComposite", "to_port": 1},
        {"from": "FleckMask", "from_port": 0, "to": "FleckComposite", "to_port": 2},
    ]
    rewire(g, "Material", 0, "FleckComposite", 0)

    # Seed-bearing nodes where their originals keep them (see docstring);
    # everything else spaced left to right by data flow.
    place(g, {
        "TwillLayout": (71, 216), "CrosshatchGrid": (71, 216), "FleckSource": (0, 0),
        "voronoi_0": (0, 0), "PatternSelect": (0, 250),
        "IsWeave": (250, 200), "IsCrosshatch": (250, 400),
        "WeaveOrCrosshatch": (500, 300), "IsTwill": (750, 300),
        "WeaveTerm": (500, 0), "TwillTerm": (1000, 150), "CrosshatchTerm": (1000, 400),
        "WeaveTwillSum": (1250, 100), "PatternMix": (1500, 200),
        "WarpStripes": (0, 0), "WeftStripes": (0, 300),
        "WarpComposite": (350, 100), "WeftComposite": (650, 250),
        "FleckMask": (300, 150), "FleckColor": (300, -100), "FleckComposite": (600, 50),
    })

    group_into_subgraph(g, ["TwillLayout"], "twill_layout", "Twill Layout",
                        [("TwillLayout", "size", "param0", "Twill size")], catalog)
    tidy_ports(g, "twill_layout", [], [("TwillLayout", 0, "twill")], catalog)
    group_into_subgraph(g, ["CrosshatchGrid"], "crosshatch_layout", "Crosshatch Layout",
                        [("CrosshatchGrid", "scale_x", "param0", "Check size")], catalog)
    link_also(g, "crosshatch_layout", "param0", "CrosshatchGrid", "scale_y")
    tidy_ports(g, "crosshatch_layout", [], [("CrosshatchGrid", 0, "crosshatch")], catalog)
    group_into_subgraph(
        g, ["voronoi_0", "PatternSelect", "IsWeave", "IsCrosshatch", "WeaveOrCrosshatch",
            "IsTwill", "WeaveTerm", "TwillTerm", "CrosshatchTerm", "WeaveTwillSum",
            "PatternMix"],
        "weave_pattern", "Weave Pattern",
        [("voronoi_0", "columns", "param0", "Weave scale"),
         ("PatternSelect", "color", "param1", "Pattern (0 weave, 0.5 twill, 1 crosshatch)"),
         ("voronoi_0", "stitch", "param2", "Stitch (1 plain, 2 twill, 3 herringbone)"),
         ("voronoi_0", "width_x", "param3", "Thread width")],
        catalog,
    )
    link_also(g, "weave_pattern", "param0", "voronoi_0", "rows")
    link_also(g, "weave_pattern", "param3", "voronoi_0", "width_y")
    tidy_ports(g, "weave_pattern",
                [("twill_layout", 0, "twill"), ("crosshatch_layout", 0, "crosshatch")],
                [("PatternMix", 0, "pattern"), ("voronoi_0", 1, "weft_mask"),
                 ("voronoi_0", 2, "warp_mask")],
                catalog)
    group_into_subgraph(g, ["colorize_1"], "tweed_color", "Tweed Color",
                        [("colorize_1", "gradient", "param0", "Tweed color")], catalog)
    tidy_ports(g, "tweed_color", [("weave_pattern", 0, "pattern")],
                [("colorize_1", 0, "albedo")], catalog)
    group_into_subgraph(
        g, ["colorize_0", "colorize_3", "normal_map_0"], "surface_finish", "Surface Finish",
        [("colorize_3", "gradient", "param0", "Roughness"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    tidy_ports(g, "surface_finish", [("weave_pattern", 0, "pattern")],
                [("normal_map_0", 0, "normal"), ("colorize_3", 0, "roughness")], catalog)
    group_into_subgraph(
        g, ["WarpStripes", "WeftStripes", "WarpComposite", "WeftComposite"],
        "plaid_overlay", "Plaid Overlay",
        [("WarpComposite", "amount", "param0", "Plaid strength"),
         ("WarpStripes", "gradient", "param1", "Plaid sett"),
         ("WarpStripes", "repeat", "param2", "Sett repeat")],
        catalog,
    )
    link_also(g, "plaid_overlay", "param0", "WeftComposite", "amount")
    link_also(g, "plaid_overlay", "param1", "WeftStripes", "gradient")
    link_also(g, "plaid_overlay", "param2", "WeftStripes", "repeat")
    tidy_ports(g, "plaid_overlay",
                [("tweed_color", 0, "albedo"), ("weave_pattern", 1, "weft_mask"),
                 ("weave_pattern", 2, "warp_mask")],
                [("WeftComposite", 0, "albedo")], catalog)
    group_into_subgraph(
        g, ["FleckSource", "FleckMask", "FleckColor", "FleckComposite"],
        "fleck_layer", "Fleck Layer",
        [("FleckComposite", "amount", "param0", "Fleck strength"),
         ("FleckSource", "scale_x", "param1", "Fleck density"),
         ("FleckColor", "gradient", "param2", "Fleck color")],
        catalog,
    )
    link_also(g, "fleck_layer", "param1", "FleckSource", "scale_y")
    tidy_ports(g, "fleck_layer", [("plaid_overlay", 0, "albedo")],
                [("FleckComposite", 0, "albedo")], catalog)

    # Inner canvases: park the proxies at the edges of the hand-placed nodes.
    place(node(g, "weave_pattern"), {
        "gen_inputs": (650, 550), "gen_parameters": (-350, 250), "gen_outputs": (1800, 200)})
    for sub in ("twill_layout", "crosshatch_layout"):
        place(node(g, sub), {"gen_parameters": (-250, 216), "gen_outputs": (400, 216)})
    place(node(g, "plaid_overlay"), {
        "gen_inputs": (-350, 150), "gen_parameters": (-350, 450), "gen_outputs": (950, 250)})
    place(node(g, "fleck_layer"), {
        "gen_inputs": (300, 350), "gen_parameters": (-350, 250), "gen_outputs": (900, 50)})
    # Top level reads as a layer stack, left to right into Material. The
    # collapsed nodes carry seed_int 0, so moving them moves no seeds.
    place(g, {
        "twill_layout": (-600, 100), "crosshatch_layout": (-600, 300),
        "weave_pattern": (-300, 150), "tweed_color": (0, 0), "surface_finish": (0, 300),
        "plaid_overlay": (300, 0), "fleck_layer": (600, 0),
        "uniform_0": (600, 200), "Material": (900, 150),
    })
    rename_nodes(g, _F07_HERRINGBONE_TWEED_NAMES)
    # f08's Fleck density 36 (the default) is past voronoi's 32-stop
    # slider: own range 1-48.
    widen_widget(g, "fleck_layer", "param1", 48, catalog)
    return save_variant(g, _LABEL, "f07_herringbone_tweed", 1)


# Plaid sett for the Plaid Overlay (a muted navy / green / red tartan, a
# starting point: the overlay ships at strength 0). Constant interpolation,
# stops on eighths so each stripe edge falls on a thread edge at the default
# 8-thread weave with Sett repeat 1.
_PLAID_SETT = [
    (0.0, 0.12, 0.15, 0.28),
    (0.375, 0.16, 0.28, 0.20),
    (0.625, 0.58, 0.16, 0.13),
    (0.75, 0.16, 0.28, 0.20),
    (0.875, 0.80, 0.74, 0.58),
]


def _sett(points):
    """A constant-interpolation gradient (hard stripes) from (pos, r, g, b)."""
    grad = _grad(points)
    grad["interpolation"] = 0
    return grad


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


BUILDERS = {
    "f03_canvas_burlap": build_f03_canvas_burlap,
    "f04_wool_knit": build_f04_wool_knit,
    "f06_velvet": build_f06_velvet,
    "f07_herringbone_tweed": build_f07_herringbone_tweed,
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
