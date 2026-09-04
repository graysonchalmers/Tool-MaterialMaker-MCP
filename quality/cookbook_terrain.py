"""Cookbook growth: terrain authoring recipes -- ground/landscape materials
beyond o01 moss / o02 mud (which are already terrain-adjacent but organic-
growth focused). Same informal convention as the other cookbook_*.py files
-- 1 variant per material, no scorecard gate. Outputs land under
quality/authored/cookbook-terrain/<case>/v1.ptex.

Run: python quality/cookbook_terrain.py
Then: python quality/render_cookbook.py cookbook-terrain
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import (load_example, node, set_gradient, set_param, retype,
                     rewire, drop_conn, add_node, save_variant, _grad,
                     group_into_subgraph)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-terrain"


def build_t01_sand_dunes(catalog: dict) -> str:
    """Sand dunes: clone `wood` UNMODIFIED structurally (like o03 bark) --
    dune ripples are organic and wavy, so KEEP the knot-warp chain rather
    than straightening it like m02 aluminum. Widen perlin_2's scale for
    broad, slow-rolling ripples instead of tight wood grain. Warm sand tan,
    high roughness. wood's own normal chain already works unmodified."""
    g = load_example("wood")
    set_param(g, "perlin_2", "scale_x", 7)
    set_param(g, "perlin_2", "scale_y", 3)
    set_param(g, "perlin_2", "iterations", 5)
    set_gradient(g, "colorize_2", [    # warm sand tan
        (0.0, 0.52, 0.40, 0.23),
        (0.5, 0.68, 0.55, 0.34),
        (1.0, 0.78, 0.65, 0.42),
    ])
    set_gradient(g, "colorize_0", [    # matte sand
        (0.0, 0.78, 0.78, 0.78),
        (1.0, 0.92, 0.92, 0.92),
    ])

    # Subgraph grouping. `perlin_2` -> `blend_0` (Multiply, port0) is the
    # dune-ripple base; `blend_0`'s port1 keeps wood's own unmodified
    # grain-warp chain (perlin_0/perlin_1/warp_0/voronoi_0/colorize_1/
    # warp_1), per the docstring's explicit choice to clone wood's structure
    # UNMODIFIED -- none of that chain's own params are builder-set, so it
    # rides along with the pattern group it feeds rather than standing alone
    # with zero exposed parameters. `blend_0` itself (amount/blend_type) is
    # an untouched donor default. NOTE (pre-existing, not this task's to
    # fix): `blend_0` feeds `Material` port 1 (metallic) DIRECTLY in the
    # `wood` donor -- unusual for a non-metal material, but this builder
    # never rewires it, so the wire is preserved as-is; it becomes a
    # boundary port from Dune Ripples straight to Material.
    group_into_subgraph(g, ["perlin_2", "perlin_1", "perlin_0", "warp_0",
                             "voronoi_0", "colorize_1", "warp_1", "blend_0"],
                         "dune_ripples", "Dune Ripples",
                         [("perlin_2", "scale_x", "param0", "Ripple scale"),
                          ("perlin_2", "iterations", "param1", "Ripple detail")],
                         catalog)
    group_into_subgraph(g, ["colorize_0", "colorize_2", "normal_map_0"],
                         "sand_finish", "Sand Finish",
                         [("colorize_2", "gradient", "param0", "Sand color"),
                          ("colorize_0", "gradient", "param1", "Surface sheen")],
                         catalog)
    return save_variant(g, _LABEL, "t01_sand_dunes", 1)


def build_t02_fresh_snow(catalog: dict) -> str:
    """Fresh snow: clone `rock` and KEEP its smooth blobby structure (per
    AUTHORING.md's own rule: a smooth source is fine when the target is
    genuinely near-flat -- snow drifts are exactly that case, like s02
    granite reused rock for the same reason). Recolor albedo near-white
    with a faint cold blue-gray in the low points, force near-zero
    metallic (perlin_0 feeds it directly by default, wrong for snow), keep
    roughness fairly high but not maximal (snow has a little sheen).
    Proactive param4=0 on the normal chain (rock's own warp_0->normal_map_0
    is a directly-fed analytic chain, the same shape s02 granite had to fix)
    but at LOW strength -- soft drifts, not stone-scale relief."""
    g = load_example("rock")
    set_gradient(g, "colorize_0", [    # near-white, cold shadow in the low points
        (0.0, 0.72, 0.76, 0.82),
        (0.5, 0.88, 0.90, 0.94),
        (1.0, 0.97, 0.97, 0.99),
    ])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])  # non-metal
    set_gradient(g, "colorize_2", [    # slight sheen, not max-matte
        (0.0, 0.35, 0.35, 0.35),
        (1.0, 0.55, 0.55, 0.55),
    ])
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.18)

    # Subgraph grouping, same rock-donor template as s04/s06 (stone
    # category, Task 10): voronoi_0 -> blend_0 -> colorize_0 is the
    # untouched-topology pattern/color chain (only colorize_0's gradient is
    # builder-set here, so it carries the group's exposed parameter).
    # colorize_1 (metallic, forced to 0) stays an unexposed member of
    # Material Finish, same precedent as s11's zeroed colorize_3.
    group_into_subgraph(g, ["voronoi_0", "blend_0", "colorize_0"],
                         "snow_color", "Snow Color",
                         [("colorize_0", "gradient", "param0", "Snow color")],
                         catalog)
    group_into_subgraph(g, ["perlin_0", "colorize_1", "colorize_2"],
                         "material_finish", "Material Finish",
                         [("colorize_2", "gradient", "param0", "Surface sheen")],
                         catalog)
    group_into_subgraph(g, ["perlin_1", "voronoi_1", "warp_0", "normal_map_0"],
                         "relief", "Relief",
                         [("normal_map_0", "param1", "param0", "Relief strength")],
                         catalog)
    return save_variant(g, _LABEL, "t02_fresh_snow", 1)


def build_t03_gravel(catalog: dict) -> str:
    """Gravel: clone `rock`, reuse s02 granite's v2 lever (voronoi port 2 =
    rand3, flat per-cell random -> albedo, bypassing the smooth blend) but
    at PEBBLE scale (14, vs granite's fine-fleck 44) and a wider earthy
    gray/tan/brown palette instead of granite's grayscale. Stronger
    param4=0 relief than granite -- loose gravel is bumpier than a
    polished slab."""
    g = load_example("rock")
    set_param(g, "voronoi_0", "scale_x", 14)
    set_param(g, "voronoi_0", "scale_y", 14)
    set_param(g, "voronoi_0", "randomness", 1)
    rewire(g, "colorize_0", 0, "voronoi_0", 2)
    set_gradient(g, "colorize_0", [    # varied gray/tan/brown pebbles
        (0.0, 0.22, 0.20, 0.17),
        (0.30, 0.42, 0.38, 0.32),
        (0.55, 0.55, 0.50, 0.42),
        (0.80, 0.35, 0.28, 0.20),
        (1.0, 0.48, 0.46, 0.44),
    ])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])
    set_gradient(g, "colorize_2", [
        (0.0, 0.55, 0.55, 0.55),
        (1.0, 0.82, 0.82, 0.82),
    ])
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.55)

    # Subgraph grouping, the exact s06_river_pebbles template (Task 10):
    # colorize_0 was rewired to read voronoi_0 PORT 2 (rand3) directly,
    # orphaning blend_0 -- still present with no consumer, folded into
    # Pebble Pattern since it shares voronoi_0 as a source.
    group_into_subgraph(g, ["voronoi_0", "colorize_0", "blend_0"],
                         "pebble_pattern", "Pebble Pattern",
                         [("voronoi_0", "scale_x", "param0", "Pebble size"),
                          ("colorize_0", "gradient", "param1", "Pebble color")],
                         catalog)
    group_into_subgraph(g, ["perlin_0", "colorize_1", "colorize_2"],
                         "material_finish", "Material Finish",
                         [("colorize_2", "gradient", "param0", "Roughness")],
                         catalog)
    group_into_subgraph(g, ["perlin_1", "voronoi_1", "warp_0", "normal_map_0"],
                         "relief", "Relief",
                         [("normal_map_0", "param1", "param0", "Relief strength")],
                         catalog)
    return save_variant(g, _LABEL, "t03_gravel", 1)


def build_t04_grass_field(catalog: dict) -> str:
    """Grass field: clone rusted_metal's two-layer masked-blend structure --
    the same template o06 lichen-on-rock already proved twice now -- and
    recolor to soil+grass. Unlike lichen (sparse patches on a dominant
    base), grass should be the DOMINANT layer with dirt only showing
    through in patches.

    First attempt moved the mask threshold DOWN (0.22, by analogy with how
    o06/m01 "widen" their patch layer by lowering the threshold) expecting
    more grass coverage. Rendered almost the opposite: near-total soil with
    only tiny green flecks (checked the normal map too -- nearly flat,
    confirming the mask was saturated one way across ~all of the image, not
    a gradual shift). Reasoning about blend_type's exact mix formula and
    colorize's duplicate-point step extrapolation didn't resolve which
    direction was right for THIS specific base/patch/threshold combination,
    so the fix was empirical: flip the threshold UP instead (0.65) and
    re-render. That flip alone produced the intended dominant-grass-with-
    dirt-patches look on the first try. Lesson: don't trust threshold
    direction by analogy across cases -- render and look.

    Same metallic gotcha as lichen: drop_conn + force scalar 0. Same
    normal_map graft off the mask for grass-clump relief."""
    g = load_example("rusted_metal")
    set_gradient(g, "colorize_2", [    # base -> bare soil
        (0.0, 0.18, 0.12, 0.07),
        (1.0, 0.32, 0.23, 0.14),
    ])
    set_gradient(g, "colorize_1", [    # patch -> grass green (the dominant layer)
        (0.0, 0.10, 0.22, 0.06),
        (1.0, 0.30, 0.48, 0.14),
    ])
    set_gradient(g, "colorize_3", [(0.65, 0, 0, 0), (0.65, 1, 1, 1)])  # grass dominant
    drop_conn(g, "Material", 1)
    set_param(g, "Material", "metallic", 0)
    add_node(g, "normal_map_grass", "normal_map",
             {"param0": 9, "param1": 0.3, "param2": 0, "param4": 0})
    g["connections"].append(
        {"from": "colorize_3", "from_port": 0, "to": "normal_map_grass", "to_port": 0})
    g["connections"].append(
        {"from": "normal_map_grass", "from_port": 0, "to": "Material", "to_port": 4})

    # Subgraph grouping -- the exact o06_lichen_crusted_rock template
    # (organics, Task 4), same rusted_metal donor, same three-way fan-out
    # shape: colorize_3 (mask, explicitly widened threshold) feeds
    # blend_0's mask port, colorize_4's roughness variant, AND
    # normal_map_grass's relief input -- one signal, three groups. Rather
    # than folding it into any one of its three consumers (which would just
    # relabel two of the three as boundary ports instead of one), it gets
    # its own small group since the threshold is a real, explicitly-tuned
    # value, not an untouched donor default.
    group_into_subgraph(g, ["perlin_1", "colorize_2", "colorize_1", "blend_0"],
                         "soil_grass_color", "Soil & Grass Color",
                         [("colorize_2", "gradient", "param0", "Soil color"),
                          ("colorize_1", "gradient", "param1", "Grass color")],
                         catalog)
    group_into_subgraph(g, ["perlin_2", "colorize_3"],
                         "grass_coverage", "Grass Coverage",
                         [("colorize_3", "gradient", "param0", "Coverage")],
                         catalog)
    group_into_subgraph(g, ["perlin_0", "colorize_0", "colorize_4", "blend_1",
                             "normal_map_grass"],
                         "surface_finish", "Surface Finish",
                         [("normal_map_grass", "param1", "param0", "Relief strength")],
                         catalog)
    return save_variant(g, _LABEL, "t04_grass_field", 1)


def _group_dry_earth_plate(g: dict, catalog: dict, *, plate_label: str,
                            color_label: str, gap_label: str) -> None:
    """Shared grouping for the plain `_dry_earth_plates` terrain materials
    (t05_cracked_ice, t08_riverbed_pebbles): same donor, same
    `colorize_plate`/`rough_const` additions, no emission chain (that is
    t06_cooled_lava's bespoke case, kept separate below per the task
    brief's warp_0/glow-chain caution).

    `warp_0` is kept in one group with BOTH of its direct consumers here --
    `blend_0` (the crack/gap darkening composite feeding albedo) and, via
    `colorize_4`, the crack-relief chain feeding `normal_map_0` -- per the
    standing rule that `warp_0` is never exposed as a friendly parameter
    and always stays grouped with what it feeds. `colorize_3` (fed by
    `perlin_1`, orphaned once dry_earth's own metallic wire is dropped by
    `_dry_earth_plates`) folds into Surface Finish since it shares
    `perlin_1` with nothing else -- there is no other consumer for it to
    ride along with, and Surface Finish already has an explicit exposed
    parameter (`rough_const`, the flat roughness texture this helper adds)
    so it is not left standing with zero."""
    group_into_subgraph(g, ["voronoi_0", "colorize_1", "colorize_0", "colorize_plate",
                             "warp_0", "blend_0", "colorize_4", "blend_1", "colorize",
                             "normal_map_0"],
                         "plate_pattern", plate_label,
                         [("voronoi_0", "scale_x", "param0", "Plate size"),
                          ("colorize_plate", "gradient", "param1", color_label),
                          ("blend_0", "amount", "param2", gap_label)],
                         catalog)
    group_into_subgraph(g, ["perlin_1", "colorize_3", "perlin_0", "rough_const"],
                         "surface_finish", "Surface Finish",
                         [("rough_const", "gradient", "param0", "Roughness")],
                         catalog)


def _dry_earth_plates(scale: int, plate_grad, blend_amount: float,
                      warp: float, roughness: float):
    """Shared dry_earth voronoi-plate setup used by the natural-surface plate
    materials below (cracked ice, cooled lava, forest floor, riverbed pebbles),
    the same lever s07-s11 masonry proved: per-plate tone from voronoi_0 PORT 2
    (rand3) into a colorize, swapped in as blend_0's base (port 1) in place of
    the flat earth; the warped-crack Multiply overlay (blend_0 port 0) stays and
    darkens the inter-plate gaps; warp_0 controls how clean vs smeared the cracks
    are; roughness set via the Material's own scalar param (dry_earth leaves the
    roughness input unconnected). Non-metal forced (drop the colorize_3->metallic
    wire + scalar 0). Returns the graph for per-material extra tuning."""
    g = load_example("dry_earth")
    set_param(g, "voronoi_0", "scale_x", scale)
    set_param(g, "voronoi_0", "scale_y", scale)
    add_node(g, "colorize_plate", "colorize", {"gradient": _grad(plate_grad)})
    g["connections"].append(
        {"from": "voronoi_0", "from_port": 2, "to": "colorize_plate", "to_port": 0})
    rewire(g, "blend_0", 1, "colorize_plate", 0)
    set_param(g, "blend_0", "amount", blend_amount)
    set_param(g, "warp_0", "amount", warp)
    drop_conn(g, "Material", 1)          # dry_earth wires colorize_3 -> metallic
    set_param(g, "Material", "metallic", 0)
    set_param(g, "Material", "roughness", roughness)
    # dry_earth leaves the roughness INPUT unconnected, so a scalar roughness
    # exports no ORM map and the 3D preview can't show a wet/glossy sheen. Feed a
    # flat roughness texture (constant colorize, input value ignored) so an ORM
    # map exports and the preview is faithful -- matters for the low-roughness
    # ice / wet pebbles / lava reads.
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, roughness, roughness, roughness),
                                 (1.0, roughness, roughness, roughness)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})
    return g


def build_t05_cracked_ice(catalog: dict) -> str:
    """Cracked ice / frozen lake: dry_earth voronoi-plate donor recolored to
    glassy blue-white plates with a network of darker cracks. Distinct from t02
    fresh snow (matte, soft, smooth rock donor): ice is GLOSSY (low roughness)
    and CRACKED (the voronoi-plate network reads as pressure cracks). Large
    plates (scale 5), clean sharp cracks (warp 0.12, the haze-free masonry
    value), deep crack darkening (blend 0.7) for blue-shadowed fissures, low
    roughness 0.12 for a wet-ice sheen. Keeps dry_earth's crack->height->normal
    chain for the pressure-ridge relief."""
    g = _dry_earth_plates(
        scale=5,
        plate_grad=[            # glassy blue-white, faint per-plate tint
            (0.0,  0.76, 0.84, 0.92),
            (0.35, 0.85, 0.91, 0.97),
            (0.7,  0.90, 0.94, 0.99),
            (1.0,  0.80, 0.87, 0.95),
        ],
        blend_amount=0.7, warp=0.12, roughness=0.12)
    # smooth glassy plates: feed the crack-only signal (colorize_4, warp_0's
    # crack network) into the normal-prep colorize instead of dry_earth's
    # perlin-grain height (blend_1), so the plate FACES are smooth and only the
    # cracks carry relief. Without this the plates read as frosted/sandy concrete
    # (dry_earth's built-in micro-grain), wrong for glassy ice.
    rewire(g, "colorize", 0, "colorize_4", 0)
    _group_dry_earth_plate(g, catalog, plate_label="Ice Plate & Cracks",
                            color_label="Ice color", gap_label="Crack depth")
    return save_variant(g, _LABEL, "t05_cracked_ice", 1)


def build_t06_cooled_lava(catalog: dict) -> str:
    """Cooled lava / volcanic basalt: dry_earth voronoi-plate donor as a
    near-black cracked crust, with warm EMISSION glowing in the fissures. The
    glow taps warp_0 (dry_earth's crack signal, dark at the cracks where the
    Multiply overlay darkens the plates): a colorize maps the crack lows to
    bright ember-orange and the plate interiors to black, fed into the Material's
    emission input (port 3) with emission_energy maxed. Basalt plates near-black,
    a little ropey warp (0.2), matte-ish roughness 0.75. NOTE: if the glow lands
    on the plate faces instead of the cracks, flip the colorize_glow gradient
    (warp_0 polarity)."""
    g = _dry_earth_plates(
        scale=5,
        plate_grad=[            # near-black basalt crust
            (0.0, 0.04, 0.03, 0.03),
            (0.5, 0.08, 0.06, 0.05),
            (1.0, 0.12, 0.09, 0.07),
        ],
        blend_amount=0.6, warp=0.2, roughness=0.75)
    # ember glow in the cracks: warp_0 is LOW at cracks -> map low to orange.
    add_node(g, "colorize_glow", "colorize", {"gradient": _grad([
        (0.0,  1.0, 0.42, 0.05),   # deepest crack: bright ember
        (0.3,  0.7, 0.14, 0.0),    # cooling toward the crack shoulder
        (0.55, 0.0, 0.0, 0.0),     # plate interior: no glow
        (1.0,  0.0, 0.0, 0.0),
    ])})
    g["connections"].append(
        {"from": "warp_0", "from_port": 0, "to": "colorize_glow", "to_port": 0})
    g["connections"].append(
        {"from": "colorize_glow", "from_port": 0, "to": "Material", "to_port": 3})
    set_param(g, "Material", "emission_energy", 1.0)

    # Subgraph grouping -- CAUTION per the task brief: `warp_0` (dry_earth's
    # crack signal) has THREE consumers here -- `blend_0` (crack darkening
    # in albedo), `colorize_4` (feeds the normal-relief chain via blend_1),
    # and `colorize_glow` (the emission glow). The brief requires the whole
    # `warp_0` -> `colorize_glow` -> emission chain to stay inside ONE
    # subgraph, reasoned about as a single "glow" effect. So `warp_0` is
    # grouped here with `colorize_glow` ONLY, not with `blend_0`/
    # `colorize_4` (which land in the other two groups instead) -- its
    # other two outgoing connections become two separate boundary output
    # ports from Ember Glow, per the standing rule that a single upstream
    # node feeding multiple downstream groups is fine and expected
    # (`group_into_subgraph` creates one boundary port per outgoing
    # connection, so this doesn't collapse the fan-out). `warp_0.amount` is
    # NOT exposed anywhere -- per the brief, a downstream "glow color"
    # parameter is exposed on `colorize_glow` instead, never the raw crack
    # signal.
    group_into_subgraph(g, ["voronoi_0", "colorize_1", "colorize_0", "colorize_plate",
                             "blend_0"],
                         "basalt_crust", "Basalt Crust",
                         [("voronoi_0", "scale_x", "param0", "Plate size"),
                          ("colorize_plate", "gradient", "param1", "Crust color"),
                          ("blend_0", "amount", "param2", "Crack depth")],
                         catalog)
    group_into_subgraph(g, ["warp_0", "colorize_glow"],
                         "ember_glow", "Ember Glow",
                         [("colorize_glow", "gradient", "param0", "Glow color")],
                         catalog)
    group_into_subgraph(g, ["perlin_1", "colorize_3", "perlin_0", "blend_1",
                             "colorize_4", "colorize", "normal_map_0", "rough_const"],
                         "surface_relief", "Surface Relief",
                         [("rough_const", "gradient", "param0", "Roughness")],
                         catalog)
    return save_variant(g, _LABEL, "t06_cooled_lava", 1)


def build_t07_forest_floor(catalog: dict) -> str:
    """Forest floor / leaf litter -- RE-BASED off the voronoi-plate donor the
    other terrain plate materials share. Leaf litter has NO connected crack
    network (that shared topology made every plate material read as a sibling and
    made this one read as cracked-mud camo). Uses `fbm` with noise=Cellular 4
    (enum index 5), the scattered clumpy-blob base from the noise gallery
    (docs/images/noise-gallery/fbm-bases.png): overlapping organic clumps, no
    crack lines. crocodile_skin donor for its clean single-colorize albedo;
    retype its voronoi_0 to fbm. Warm brown-dominant leaf palette with a muted
    olive accent, high matte roughness, medium param4=0 relief for a bumpy debris
    mat (crocodile_skin's roughness input IS a texture, so an ORM map exports for
    the preview)."""
    g = load_example("crocodile_skin")
    retype(g, "voronoi_0", "fbm",
           {"noise": 5, "scale_x": 6, "scale_y": 6, "folds": 0,
            "iterations": 5, "persistence": 0.5})
    set_gradient(g, "colorize_1", [    # brown-dominant leaf litter, muted olive
        (0.0,  0.14, 0.10, 0.05),   # dark mulch
        (0.35, 0.32, 0.23, 0.11),   # mid brown leaf
        (0.6,  0.30, 0.27, 0.13),   # muted olive-brown
        (0.82, 0.46, 0.34, 0.17),   # tan dry leaf
        (1.0,  0.24, 0.16, 0.08),   # dark brown
    ])
    set_gradient(g, "colorize_3", [    # matte forest floor
        (0.0, 0.86, 0.86, 0.86),
        (1.0, 0.97, 0.97, 0.97),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    node(g, "normal_map_0")["parameters"] = {
        "param0": 11, "param1": 0.4, "param2": 0, "param4": 0}

    # Subgraph grouping -- the exact o05_coral template (organics, Task 4),
    # same crocodile_skin donor: the retyped noise node + its albedo
    # colorize as "pattern", the roughness/relief consumers as "finish".
    # `uniform_0` (Material's untouched metallic-0 scalar, feeding port 1
    # directly) is left top-level, matching o05/s05/s09's precedent for
    # untouched single-purpose scalar nodes.
    group_into_subgraph(g, ["voronoi_0", "colorize_1"],
                         "litter_pattern", "Litter Pattern",
                         [("voronoi_0", "scale_x", "param0", "Clump scale"),
                          ("colorize_1", "gradient", "param1", "Leaf color")],
                         catalog)
    group_into_subgraph(g, ["colorize_0", "colorize_3", "normal_map_0"],
                         "surface_finish", "Surface Finish",
                         [("colorize_3", "gradient", "param0", "Roughness"),
                          ("normal_map_0", "param1", "param1", "Debris relief")],
                         catalog)
    return save_variant(g, _LABEL, "t07_forest_floor", 1)


def build_t08_riverbed_pebbles(catalog: dict) -> str:
    """Riverbed pebbles: dry_earth voronoi-plate donor as tight-packed, rounded,
    WET river stones. The wet-vs-dry contrast with t03 gravel (loose, angular,
    matte, rock donor) is the whole point: small rounded plates (scale 8), clean
    joints (warp 0.12), a multicolor river-tumbled palette (gray/tan/slate/brown/
    cream), and LOW roughness 0.2 for a damp sheen. Deep recessed wet gaps
    (blend 0.6). Keeps dry_earth's relief so each pebble bulges."""
    g = _dry_earth_plates(
        scale=8,
        plate_grad=[            # river-tumbled multicolor stones
            (0.0,  0.30, 0.30, 0.31),   # gray
            (0.25, 0.52, 0.47, 0.40),   # tan
            (0.5,  0.34, 0.38, 0.42),   # slate blue-gray
            (0.72, 0.44, 0.34, 0.26),   # warm brown
            (1.0,  0.62, 0.58, 0.52),   # pale cream stone
        ],
        blend_amount=0.6, warp=0.02, roughness=0.2)   # warp ~0: recessed contact
        # gaps between packed pebbles, not the warped crack lines that made this
        # a sibling of the ice plates
    _group_dry_earth_plate(g, catalog, plate_label="Pebble Bed & Gaps",
                            color_label="Pebble color", gap_label="Gap depth")
    return save_variant(g, _LABEL, "t08_riverbed_pebbles", 1)


BUILDERS = {
    "t01_sand_dunes": build_t01_sand_dunes,
    "t02_fresh_snow": build_t02_fresh_snow,
    "t03_gravel": build_t03_gravel,
    "t04_grass_field": build_t04_grass_field,
    "t05_cracked_ice": build_t05_cracked_ice,
    "t06_cooled_lava": build_t06_cooled_lava,
    "t07_forest_floor": build_t07_forest_floor,
    "t08_riverbed_pebbles": build_t08_riverbed_pebbles,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    # Loaded once per script run (not once per builder), same convention as
    # cookbook_stone.py/cookbook_leather.py -- all 8 materials need it for
    # group_into_subgraph.
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
