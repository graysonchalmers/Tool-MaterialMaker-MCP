"""Cookbook growth: leather-category authoring recipes beyond the frozen 15-case
Phase 3 test set (`f02_brown_leather` is frozen there already -- see
quality/test_set.json's freeze note; this is additive, not an edit to that
case). Informal: 1 variant per material, no scorecard gate. Reuses author_helpers.py's
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
from author_helpers import (load_example, node, set_gradient, set_param, retype,
                    rewire, add_node, save_variant, _grad, group_into_subgraph)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-leather"


def _group_leather_grain(g, catalog, *, color_label, sheen_label, relief_label,
                          pattern_size_param=None, pattern_size_label=None):
    """Shared grouping for the leathers that clone `crocodile_skin` and keep
    its identical voronoi_0 -> {colorize_0, colorize_1, colorize_3} fan-out
    unmodified structurally (l01/l04 keep voronoi_0 as a voronoi, l03 retypes
    it to perlin -- the node NAME and wiring are the same either way). Same
    donor shape already grouped this way for o04_snake_scales/o05_coral in
    cookbook_organics.py's `_group_crocodile_skin_pattern` and for
    f03-f07 in cookbook_fabrics.py's `_group_weave_family`; reused here with
    an optional pattern-size exposure since not every leather in this set
    tunes voronoi_0's own parameters (l01 only recolors, so its grain-pattern
    group's sole exposed param is the color).

    voronoi_0 is folded into the pattern group with colorize_1 (matching that
    precedent, since it feeds three consumers and cannot sit in more than one
    group). `uniform_0` (Material's untouched metallic scalar) is left
    top-level -- a single donor-default node feeding one port directly, not a
    generative/compositing chain worth collapsing. l02 reuses this same
    helper for its base-grain half (see build_l02) since its donor structure
    is identical here; only the two blend-composited wear-layer groups on top
    are bespoke to that material."""
    pattern_exposed = []
    if pattern_size_param:
        pattern_exposed.append(
            ("voronoi_0", pattern_size_param, "param0", pattern_size_label))
    pattern_exposed.append(
        ("colorize_1", "gradient", f"param{len(pattern_exposed)}", color_label))
    group_into_subgraph(g, ["voronoi_0", "colorize_1"], "grain_pattern",
                         "Grain Pattern", pattern_exposed, catalog)
    group_into_subgraph(
        g, ["colorize_0", "colorize_3", "normal_map_0"], "surface_finish",
        "Surface Finish",
        [("colorize_3", "gradient", "param0", sheen_label),
         ("normal_map_0", "param1", "param1", relief_label)],
        catalog,
    )


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


def build_l01_black_oiled_leather(catalog: dict) -> str:
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

    # voronoi_0 is left at its donor default scale here (no set_param call
    # touches it), so the Grain Pattern group's sole exposed param is the
    # color -- no bare untouched default is exposed.
    _group_leather_grain(
        g, catalog, color_label="Oiled leather color",
        sheen_label="Polish level", relief_label="Grain relief",
    )
    return save_variant(g, _LABEL, "l01_black_oiled_leather", 1)


def build_l02_distressed_two_tone(catalog: dict) -> str:
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
        # Polarity fix (2026-09-04): the worn tone is the MINORITY (scattered
        # rubs), the dark saddle base is the MAJORITY. blend output =
        # mask*port0 + (1-mask)*port1, and colorize_wm's mask is 1 only in the
        # small high-perlin patches, 0 across the broad remainder. So the worn
        # tone belongs on port0 (shown where mask=1 = the patches) and the base
        # on port1 (shown where mask=0 = most of the surface). The original
        # wiring had these reversed, so the worn tan covered most of the hide
        # and the base showed only in small patches -- backwards from the
        # recipe's own intent.
        {"from": "worn_alb", "from_port": 0, "to": "blend_alb", "to_port": 0},   # worn rubs (minority, mask=1)
        {"from": "colorize_1", "from_port": 0, "to": "blend_alb", "to_port": 1}, # dark saddle base (majority, mask=0)
        {"from": "colorize_wm", "from_port": 0, "to": "blend_alb", "to_port": 2},
        {"from": "worn_rgh", "from_port": 0, "to": "blend_rgh", "to_port": 0},   # worn roughness (minority)
        {"from": "colorize_3", "from_port": 0, "to": "blend_rgh", "to_port": 1}, # base roughness (majority)
        {"from": "colorize_wm", "from_port": 0, "to": "blend_rgh", "to_port": 2},
    ]
    rewire(g, "Material", 0, "blend_alb", 0)   # albedo <- worn-over-base
    rewire(g, "Material", 2, "blend_rgh", 0)   # roughness <- worn-over-base
    _dome_the_cells(g)                         # grain bodies raised, seams recessed
    set_param(g, "normal_map_0", "param4", 0)  # continuous grain relief under both
    set_param(g, "normal_map_0", "param1", 0.40)

    # Port-source trace for blend_alb/blend_rgh, read directly from the
    # `connections` list assembled above (ground truth: blend.mmg's shader
    # model is s1=port0/foreground, s2=port1/background, a=port2/mask, output
    # = mask*port0 + (1-mask)*port1). Post-polarity-fix wiring:
    #   blend_alb: port0 (shown where mask=1) <- worn_alb (scattered rubs)
    #              port1 (shown where mask=0) <- colorize_1 (base grain, majority)
    #              port2 (mask)               <- colorize_wm
    #   blend_rgh: port0 (shown where mask=1) <- worn_rgh (rubbed roughness)
    #              port1 (shown where mask=0) <- colorize_3 (base roughness, majority)
    #              port2 (mask)               <- colorize_wm (same mask)
    # Grouping below keeps both blends together in one composite group with
    # no change to any of these connections; group_into_subgraph rehomes each
    # incoming connection's own to_port independently, so it cannot swap
    # which source lands on port0 vs port1 vs port2 (same guarantee already
    # relied on for f08_donegal_tweed's fleck composite).
    _group_leather_grain(
        g, catalog, color_label="Base leather color",
        sheen_label="Base roughness", relief_label="Relief strength",
    )
    group_into_subgraph(
        g, ["perlin_wm", "colorize_wm", "worn_alb", "worn_rgh"],
        "wear_pattern", "Wear Pattern",
        [("perlin_wm", "scale_x", "param0", "Wear pattern scale"),
         ("worn_alb", "gradient", "param1", "Worn color")],
        catalog,
    )
    group_into_subgraph(
        g, ["blend_alb", "blend_rgh"], "wear_composite", "Wear Composite",
        [("blend_alb", "amount", "param0", "Wear blend strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "l02_distressed_two_tone", 1)


def build_l03_suede(catalog: dict) -> str:
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

    # voronoi_0 was retyped to perlin above with explicit iterations=8 (the
    # fiber-grain octave count), matching f06_velvet's convention of exposing
    # `iterations` as the fiber-grain density knob for a perlin-donor fabric.
    _group_leather_grain(
        g, catalog, color_label="Suede color",
        sheen_label="Nap roughness", relief_label="Nap relief",
        pattern_size_param="iterations", pattern_size_label="Fiber grain",
    )
    return save_variant(g, _LABEL, "l03_suede", 1)


def build_l04_reptile_exotic(catalog: dict) -> str:
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
    # Albedo polarity matters here (unlike the near-monochrome f02/l01): voronoi
    # port 0 is LOW at the cell CENTERS (the scale bodies) and high at the
    # borders. Map centers -> bronze-olive body, borders -> dark seam, so the
    # scales carry the colour and the seams read as dark grooves (the stock
    # low->dark ramp put the colour on the thin borders and left the bodies
    # dark). This is the same port-0 polarity lesson as _dome_the_cells, applied
    # to the albedo ramp instead of the height ramp.
    set_gradient(g, "colorize_1", [            # exotic bronze-green scales
        (0.0, 0.48, 0.41, 0.16),   # scale body (center): bronze-olive
        (0.5, 0.28, 0.31, 0.12),   # mid
        (1.0, 0.05, 0.08, 0.04),   # scale seam (border): dark
    ])
    set_gradient(g, "colorize_3", [            # drier reptile finish (was too wet)
        (0.0, 0.46, 0.46, 0.46),
        (1.0, 0.60, 0.60, 0.60),
    ])
    _dome_the_cells(g)                         # scales domed up, seams recessed
    set_param(g, "normal_map_0", "param4", 0)  # strong scale-edge relief
    set_param(g, "normal_map_0", "param1", 0.7)

    # Per the task's blend caution, this builder was checked for a `blend`
    # node regardless of the o04_snake_scales/o05_coral naming-family
    # precedent it echoes: it has none. It clones crocodile_skin unmodified
    # structurally (recolor + retuned voronoi_0 scale + the param4=0 fix),
    # the exact same shape as l01/l03, so it reuses `_group_leather_grain`.
    # voronoi_0's scale_x IS explicitly tuned here (unlike l01), so it is
    # exposed as the pattern-size knob.
    _group_leather_grain(
        g, catalog, color_label="Scale color",
        sheen_label="Finish", relief_label="Scale relief",
        pattern_size_param="scale_x", pattern_size_label="Scale size",
    )
    return save_variant(g, _LABEL, "l04_reptile_exotic", 1)


def build_l05_quilted_leather(catalog: dict) -> str:
    """Quilted / tufted leather (car-seat / chesterfield): a saddle-tan grain
    base raised into a regular grid of puffy pads separated by recessed
    stitch-channel seams -- the classic stitched-upholstery look.

    Stitch mechanism (practice notes -- this one took diagnosis): the obvious
    `shape` -> `tiler` dash-grid approach FOUGHT BACK. Rendered in the full
    graph it produced no visible dashes, and isolating the tiler output to the
    albedo TIMED OUT the renderer at 180s (a single centered shape tiled by
    `tiler` makes a degenerate/expensive shader here). The reliable path is the
    parameter-only `pattern` node (same node the sci-fi cookbook uses): two Sine
    waves multiplied give a smooth grid of rounded pads that peak at the pad
    centers and fall to the seams -- exactly the quilt shape, with no
    shape/tiler shader surprises. So:
      - normal: drive the relief from the pattern pads (strong puffy quilt),
        with the crocodile grain layered on top as fine detail;
      - albedo: darken the seams so the recessed channels read as stitched
        valleys, keeping the leather grain on the pad faces.
    (Individual stitch-dash marks running ALONG each seam are a further
    refinement; this delivers the quilt + channel seams reliably first.)"""
    g = load_example("crocodile_skin")
    set_gradient(g, "colorize_1", [           # saddle tan leather
        (0.0, 0.22, 0.13, 0.07),
        (1.0, 0.44, 0.28, 0.15),
    ])
    set_gradient(g, "colorize_3", [           # mid roughness leather
        (0.0, 0.40, 0.40, 0.40),
        (1.0, 0.52, 0.52, 0.52),
    ])
    _dome_the_cells(g)                        # fine grain: bodies up, seams down

    # Quilt grid: two multiplied sine waves -> rounded pads (high at pad
    # centers, low at the seams between them). Parameter-only, cheap, reliable.
    add_node(g, "pattern_q", "pattern",
             {"mix": 0, "x_wave": 0, "x_scale": 5, "y_wave": 0, "y_scale": 5})
    # Seam mask: high in the recessed seams (low pattern value), 0 on the pads.
    add_node(g, "seam_mask", "colorize",
             {"gradient": _grad([(0.10, 1, 1, 1), (0.45, 0, 0, 0)])})
    # Seam shade: a dark constant to sink the channels in albedo.
    add_node(g, "seam_shade", "colorize",
             {"gradient": _grad([(0.0, 0.09, 0.05, 0.03), (1.0, 0.09, 0.05, 0.03)])})
    # Combined height: pads (pattern) as the big shape, grain layered on top.
    # amount is the port0 (pads) weight since port2/mask is unconnected (opacity
    # = amount x mask, mask defaults to 1.0), so height = amount*pads +
    # (1-amount)*grain. 0.65 makes the pads dominant with the crocodile grain as
    # ~0.35 fine detail, matching this recipe's stated "drive the relief from
    # the pattern pads, grain on top at ~0.35" intent. It was 0.35 (pads
    # underweighted, grain dominant), the inverse; fixed 2026-09-04. The exposed
    # "Quilt puffiness" slider IS this amount, so higher now reads as puffier.
    add_node(g, "blend_h_q", "blend", {"blend_type": 0, "amount": 0.85})
    add_node(g, "blend_alb_q", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "pattern_q", "from_port": 0, "to": "seam_mask", "to_port": 0},
        {"from": "pattern_q", "from_port": 0, "to": "seam_shade", "to_port": 0},
        # height: pattern pads (base) + grain (colorize_0) overlaid at 0.35
        {"from": "pattern_q", "from_port": 0, "to": "blend_h_q", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "blend_h_q", "to_port": 1},
        # albedo: darken the seams over the saddle grain. Polarity fix
        # (2026-09-04): seam_mask is 1 in the recessed seams (low pattern) and
        # 0 on the pad faces (high pattern), and blend output =
        # mask*port0 + (1-mask)*port1, so the dark seam_shade must sit on port0
        # (shown where mask=1 = seams) and the grain on port1 (shown where
        # mask=0 = pads). The original wiring had these reversed, so the dark
        # landed on the pad CENTERS (button-tuft dots) instead of in the seams.
        {"from": "seam_shade", "from_port": 0, "to": "blend_alb_q", "to_port": 0},  # dark seams (mask=1)
        {"from": "colorize_1", "from_port": 0, "to": "blend_alb_q", "to_port": 1},  # grain pad faces (mask=0)
        {"from": "seam_mask", "from_port": 0, "to": "blend_alb_q", "to_port": 2},
    ]
    rewire(g, "Material", 0, "blend_alb_q", 0)     # albedo <- seam-shaded grain
    rewire(g, "normal_map_0", 0, "blend_h_q", 0)   # height <- pads + grain
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.9)    # pronounced puffy padding

    # Port-source trace for blend_h_q/blend_alb_q, from the `connections`
    # list assembled above (ground truth, per blend.mmg's shader model:
    # s1=port0/foreground, s2=port1/background, a=port2/mask, output =
    # mask*port0 + (1-mask)*port1; blend_h_q's port2 is left unconnected, so
    # its mask uses the node's own default of 1.0, i.e. a flat, unmasked
    # 0.35/0.65 mix rather than a spatial composite):
    #   blend_h_q:   port0 <- pattern_q (quilt pads), port1 <- colorize_0
    #                (grain height); no port2 connection (default mask 1.0,
    #                amount=0.35 -> flat 0.35*pads + 0.65*grain)
    #   blend_alb_q: port0 (shown where mask=1) <- colorize_1 (base grain)
    #                port1 (shown where mask=0) <- seam_shade
    #                port2 (mask)               <- seam_mask
    # colorize_0 no longer feeds normal_map_0 directly here (it was rewired
    # to blend_h_q instead), so it moves into the grain-generator group below
    # rather than a separate finish group -- normal_map_0 moves into the
    # composite group instead, since its only input is now blend_h_q's
    # output, not a raw donor colorize. This is a deliberate structural
    # difference from l01/l03/l04's `_group_leather_grain` shape, not reused
    # here for that reason.
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "colorize_3", "colorize_0"],
        "leather_grain", "Leather Grain",
        [("colorize_1", "gradient", "param0", "Leather color"),
         ("colorize_3", "gradient", "param1", "Roughness")],
        catalog,
    )
    group_into_subgraph(
        g, ["pattern_q"], "quilt_pattern", "Quilt Pattern",
        [("pattern_q", "x_scale", "param0", "Quilt pad size")],
        catalog,
    )
    group_into_subgraph(
        g, ["seam_mask", "seam_shade"], "seam_shading", "Seam Shading",
        [("seam_shade", "gradient", "param0", "Seam color")],
        catalog,
    )
    group_into_subgraph(
        g, ["blend_h_q", "blend_alb_q", "normal_map_0"],
        "quilt_composite", "Quilt Composite",
        [("blend_h_q", "amount", "param0", "Quilt puffiness"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "l05_quilted_leather", 1)


def build_l06_topstitched_leather(catalog: dict) -> str:
    """Topstitched leather panel: saddle-tan grain with a regular grid of RAISED
    cream stitch dashes -- the real per-stitch marks l05's quilt lacked.

    Stitch mechanism, take two (the reliable one): a SINGLE `pattern` node makes
    the whole dash grid -- Square in X (short on-segments = dashes) times Square
    in Y (rows), mixed Multiply -> an on/off grid of dash marks. This avoids
    both traps found earlier: the `shape`+`tiler` timeout, and the two-mask
    blend-AND whose polarity came out inverted (a channel version rendered as
    dark RECESSED perforations instead of raised light thread -- the `pattern`
    Square output and the `blend` Multiply's default opacity fought the intent).
    One pattern node, one sharpen colorize, unambiguous polarity:
      - albedo: cream thread at the dash marks over the saddle grain;
      - normal: the dashes raised proud of the grain (thread sits on top)."""
    g = load_example("crocodile_skin")
    set_gradient(g, "colorize_1", [           # saddle tan leather
        (0.0, 0.22, 0.13, 0.07),
        (1.0, 0.44, 0.28, 0.15),
    ])
    set_gradient(g, "colorize_3", [           # mid roughness leather
        (0.0, 0.40, 0.40, 0.40),
        (1.0, 0.52, 0.52, 0.52),
    ])
    _dome_the_cells(g)                        # fine grain: bodies up, seams down

    # Dash grid in ONE node: short on-segments in X (dashes) x rows in Y.
    add_node(g, "dash_grid", "pattern",
             {"mix": 0, "x_wave": 2, "x_scale": 32, "y_wave": 2, "y_scale": 12})
    # NOTE the polarity: pattern Square*Square's HIGH region is the connected
    # field; the isolated rectangles (the actual dash marks we want) are its LOW
    # cells. So the mask is 1 at LOW (marks) -> reversed gradient. (Rendered the
    # un-reversed version first: dark recessed marks on a flat thread-coloured
    # field -- the exact inverse.)
    add_node(g, "stitch_mask", "colorize",    # 1 AT the dash marks (pattern low)
             {"gradient": _grad([(0.40, 1, 1, 1), (0.58, 0, 0, 0)])})
    add_node(g, "thread_alb", "colorize",     # cream thread colour
             {"gradient": _grad([(0.0, 0.80, 0.74, 0.60), (1.0, 0.88, 0.82, 0.68)])})
    add_node(g, "blend_alb_st", "blend", {"blend_type": 0, "amount": 1})
    add_node(g, "blend_h_st", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "dash_grid", "from_port": 0, "to": "stitch_mask", "to_port": 0},
        {"from": "stitch_mask", "from_port": 0, "to": "thread_alb", "to_port": 0},
        # albedo: cream thread at the dashes over the saddle grain
        {"from": "colorize_1", "from_port": 0, "to": "blend_alb_st", "to_port": 0},
        {"from": "thread_alb", "from_port": 0, "to": "blend_alb_st", "to_port": 1},
        {"from": "stitch_mask", "from_port": 0, "to": "blend_alb_st", "to_port": 2},
        # normal: raise the stitches above the grain height before normal_map
        {"from": "colorize_0", "from_port": 0, "to": "blend_h_st", "to_port": 0},
        {"from": "stitch_mask", "from_port": 0, "to": "blend_h_st", "to_port": 1},
        {"from": "stitch_mask", "from_port": 0, "to": "blend_h_st", "to_port": 2},
    ]
    rewire(g, "Material", 0, "blend_alb_st", 0)     # albedo <- thread over grain
    rewire(g, "normal_map_0", 0, "blend_h_st", 0)   # height <- grain + raised stitches
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.6)

    # Port-source trace for blend_alb_st/blend_h_st, from the `connections`
    # list assembled above (ground truth, per blend.mmg's shader model:
    # s1=port0/foreground, s2=port1/background, a=port2/mask, output =
    # mask*port0 + (1-mask)*port1):
    #   blend_alb_st: port0 (mask=1) <- colorize_1 (base grain)
    #                 port1 (mask=0) <- thread_alb (cream thread)
    #                 port2 (mask)   <- stitch_mask
    #   blend_h_st:   port0 (mask=1) <- colorize_0 (grain height)
    #                 port1 (mask=0) <- stitch_mask (reused directly as the
    #                                   background value, not a separate
    #                                   height layer -- same mask feeds both
    #                                   its own port1 and port2 here)
    #                 port2 (mask)   <- stitch_mask
    # Same structural note as l05: colorize_0 no longer feeds normal_map_0
    # directly (rewired to blend_h_st instead), so it joins the
    # grain-generator group and normal_map_0 joins the composite group.
    # thread_alb is folded into the stitch-pattern group alongside dash_grid/
    # stitch_mask (its only input), the same shape f08_donegal_tweed used to
    # fold colorize_fleck_color in with its mask/generator rather than giving
    # it a separate group.
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "colorize_3", "colorize_0"],
        "leather_grain", "Leather Grain",
        [("colorize_1", "gradient", "param0", "Leather color"),
         ("colorize_3", "gradient", "param1", "Roughness")],
        catalog,
    )
    group_into_subgraph(
        g, ["dash_grid", "stitch_mask", "thread_alb"],
        "stitch_pattern", "Stitch Pattern",
        [("dash_grid", "x_scale", "param0", "Stitch pitch"),
         ("thread_alb", "gradient", "param1", "Thread color")],
        catalog,
    )
    group_into_subgraph(
        g, ["blend_alb_st", "blend_h_st", "normal_map_0"],
        "stitch_composite", "Stitch Composite",
        [("blend_h_st", "amount", "param0", "Stitch raise"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "l06_topstitched_leather", 1)


BUILDERS = {
    "l01_black_oiled_leather": build_l01_black_oiled_leather,
    "l02_distressed_two_tone": build_l02_distressed_two_tone,
    "l03_suede": build_l03_suede,
    "l04_reptile_exotic": build_l04_reptile_exotic,
    "l05_quilted_leather": build_l05_quilted_leather,
    "l06_topstitched_leather": build_l06_topstitched_leather,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    # Loaded once per script run (not once per builder), same convention as
    # cookbook_fabrics.py/cookbook_organics.py -- all 6 materials need it for
    # group_into_subgraph.
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
