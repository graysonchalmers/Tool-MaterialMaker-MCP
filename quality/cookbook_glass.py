"""Cookbook growth: glass authoring recipes -- the first entry authored from a
reference PHOTO rather than a text prompt, proving out the "Authoring from a
reference photo" workflow in docs/AUTHORING.md. Same informal convention as
the other cookbook_*.py files -- 1 variant per material, no scorecard gate.
Outputs land under quality/authored/cookbook-glass/<case>/v1.ptex.

Run: python -m quality.cookbook_glass
Then: python -m quality.render_cookbook cookbook-glass
"""
import sys

from quality.author_helpers import (load_example, set_gradient, set_param, drop_conn,
                     save_variant, add_node, _grad, group_into_subgraph, rename_nodes, retype,
                     _from_scratch_noise_material)

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-glass"

# `dry_earth` donor mapping for gl01. voronoi_0 (facet cells) -> colorize_1
# (tight crack ramp) -> warp_0 (jointing), then blended with colorize_0
# (base tone from the shared perlin_0) into blend_0, which feeds
# Material's albedo. colorize_3 fed Material's metallic port in the donor;
# gl01 drops that connection and forces metallic=0, so colorize_3 is dead
# here (same precedent as `wooden_floor`'s combine_0). The relief pathway
# (warp_0 -> colorize_4 -> blend_1, mixed with the same shared perlin_0)
# feeds colorize -> normal_map (and Material's height port), plus the flat
# rough_const this builder adds.
_GL01_NAMES = {
    "voronoi_0": "FacetCells",
    "colorize_1": "CrackRamp",
    "warp_0": "JointWarp",
    "colorize_0": "BaseTone",
    "blend_0": "CrackComposite",
    "colorize_3": "ColorizeUnused",     # dead: its Material connection is dropped, forced metallic=0
    "perlin_0": "AmbientNoise",         # shared: feeds BaseTone and the relief composite
    "perlin_1": "CrackWarpNoise",       # shared: feeds JointWarp's amount and the dead ColorizeUnused
    "colorize_4": "ReliefContrast",
    "blend_1": "ReliefComposite",
    "colorize": "ReliefRamp",
    "normal_map_0": "GlassNormal",
    "rough_const": "RoughnessConst",
}


def build_gl01_frosted_glass(catalog: dict) -> str:
    """Sandblasted frosted glass, decomposed from a real macro photo (see the
    recipe card for the reference and the observation-by-observation
    reasoning). Reads as the same CONNECTED CRACK NETWORK topology as
    `dry_earth` (dense light facets separated by dark micro-crack
    boundaries), just at a far finer, denser scale than any existing
    dry_earth-derived material, so it clones `dry_earth` rather than
    inventing a new base. Cranks voronoi cell density way up for fine
    facets, tightens warp_0 for clean (not smeared) micro-joints, recolors
    to a narrow cool blue-gray range (uniform matte, not per-plate color
    variation), forces non-metal, pushes roughness high and fairly uniform
    (frosted glass is diffuse, not glossy), and keeps normal relief subtle
    (param4=0 at low param1) since real frosted glass has almost no macro
    bump -- the visible diffusion is a MICRO-surface effect this graph can
    only approximate, not simulate, logged as an honest limitation in the
    card rather than overclaimed."""
    g = load_example("dry_earth")
    set_param(g, "voronoi_0", "scale_x", 60)
    set_param(g, "voronoi_0", "scale_y", 60)
    set_param(g, "voronoi_0", "randomness", 1)
    set_gradient(g, "colorize_0", [    # narrow, uniform cool blue-gray
        (0.0, 0.60, 0.65, 0.71),
        (1.0, 0.76, 0.80, 0.86),
    ])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (0.08, 1, 1, 1)])  # tight crack ramp
    set_param(g, "warp_0", "amount", 0.05)   # clean fine joints, not smeared plates
    set_param(g, "blend_0", "amount", 0.5)
    drop_conn(g, "Material", 1)
    set_param(g, "Material", "metallic", 0)
    set_param(g, "Material", "roughness", 0.88)   # matte, diffuse, fairly uniform
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.15)  # subtle: real frosted glass has near-zero macro bump
    # dry_earth leaves the roughness INPUT unconnected, so a scalar-only
    # roughness exports no ORM map (same gap _dry_earth_plates works around
    # in cookbook_terrain.py). Feed a flat roughness texture (constant
    # colorize, input value ignored) so an ORM map exports for the preview.
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.88, 0.88, 0.88), (1.0, 0.88, 0.88, 0.88)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})

    # Group the raw dry_earth-derived tangle (14 top-level nodes) into two
    # named subgraphs so opening the graph in Material Maker shows a small,
    # legible handful of nodes instead of every wire. Two independent noise
    # sources (perlin_0, perlin_1) stay top-level since each feeds both
    # groups; grouping them in with either would just relabel the sharing
    # as an extra boundary port. colorize_3 is dead (its connection to
    # Material was dropped above, per dry_earth's own metallic-variance
    # wiring) and gets tucked inside base_color with its source, perlin_1,
    # rather than left as an orphaned top-level node.
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "warp_0", "colorize_0", "blend_0", "colorize_3"],
        "base_color", "Base Color",
        [("voronoi_0", "scale_x", "param0", "Facet size"),
         ("colorize_0", "gradient", "param1", "Base color"),
         ("blend_0", "amount", "param2", "Crack contrast")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_4", "blend_1", "colorize", "normal_map_0", "rough_const"],
        "surface_detail", "Surface Detail",
        [("rough_const", "gradient", "param0", "Roughness"),
         ("normal_map_0", "param1", "param1", "Surface relief")],
        catalog,
    )
    rename_nodes(g, _GL01_NAMES)
    return save_variant(g, _LABEL, "gl01_frosted_glass", 1)


def _drop_nodes(graph: dict, names: list) -> None:
    """Remove named top-level nodes and every connection touching them.
    Local to this module -- the first cookbook builder that needs to
    actually excise donor nodes rather than just rewire or leave them dead,
    since gl02's v1 kept gl01's whole frost/relief chain around it (art
    direction fix, see build_gl02_cut_gem's docstring)."""
    drop = set(names)
    graph["nodes"] = [n for n in graph["nodes"] if n["name"] not in drop]
    graph["connections"] = [c for c in graph["connections"]
                            if c["from"] not in drop and c["to"] not in drop]


# gl02 clones the SAME dry_earth donor as gl01 (voronoi_0 retyped to
# voronoi_triangle, zero prior cookbook use; port semantics verified via
# describe_node + the node's own .mmg: both share port 0 Nodes/f, port 1
# Border/f, port 2 Random color/rgb), but keeps only the four nodes that
# still serve a cut-gem look. Everything else in the donor -- warp_0's
# organic jointing, the perlin_0/perlin_1 noise feeding the blend/relief
# chain, the crack-composite blend, colorize_3/4, the second relief blend
# and its ramp -- was gl01's SANDBLASTED-FROST machinery (fine speckle +
# soft, wide, noise-blurred bevels) and got dropped wholesale: a v1
# self-screen came back reading as a matte grainy hex-tile floor, not a
# glossy gem, traced to exactly that inherited chain. What's left is
# voronoi_triangle facets -> per-facet tint (albedo) straight to Material,
# and the border-distance signal straight into normal_map for sharp,
# UN-warped facet-edge relief, plus a flat low-roughness texture.
_GL02_NAMES = {
    "voronoi_0": "FacetCells",
    "colorize_1": "EdgeRamp",
    "colorize_0": "FacetTint",
    "normal_map_0": "FacetNormal",
    "rough_const": "RoughnessConst",
}


def build_gl02_cut_gem(catalog: dict) -> str:
    """Faceted cut gem: proves the `voronoi_triangle` base (triangular cells
    square voronoi cannot produce) for a hard-edged, GLOSSY crystal / cut-gem
    look. Clones the `dry_earth` donor gl01 uses and RETYPES `voronoi_0` from
    square `voronoi` to `voronoi_triangle` at the noise gallery's starting
    params (`stretch_x`/`stretch_y`=1, `randomness`=0.85), but at a higher
    `scale_x`/`scale_y`=10 (vs the gallery's 4) for MORE, smaller, sharper
    facets -- v1 at scale 4 read as a few large, round-ish hex-like cells,
    too close to `s05_hex_stone_tile`'s tiled-mosaic look. Connection-safe
    because both node types expose the same port 0 (Nodes)/port 1
    (Border)/port 2 (Random color) signature (verified via describe_node +
    the node's own .mmg shader_model), so the existing port1->EdgeRamp wire
    keeps its role.

    v1 cloned gl01's whole donor tangle (warp, blend, dual noise sources,
    a second relief-composite blend) and just retuned it. A self-screen
    render came back as a matte, grainy, greenish HEX TILE floor, not a
    glossy gem -- that texture-grain and the soft, wide bevels both traced
    to gl01's frost/relief chain: mixing a high-iteration ambient perlin
    into the height signal (via blend_1/colorize_4/colorize in the old v1)
    is exactly gl01's sandblasted-frost effect, wrong for a gem's CLEAN FLAT
    facet faces. v2 drops that whole chain (`_drop_nodes`) down to four
    nodes plus Material: `FacetCells` -> `FacetTint` (the per-facet random
    color, port 2, straight to albedo -- no darkening blend on top, so each
    facet is a flat, clean color, exactly the "clean flat facet faces" a cut
    gem needs) and `FacetCells` -> `EdgeRamp` (the border-distance edge
    signal, port 1, UN-warped -- v1's `warp_0` is gone entirely, so the
    facet seams stay geometrically sharp) -> `FacetNormal` directly (no
    intermediate contrast/blend/ramp -- the fewer processing steps between
    the edge signal and the normal map, the crisper the seam reads instead
    of a soft wide bevel).

    Kept from v1: the single coherent emerald-green `FacetTint` gradient
    (deep shadowed facets to a bright highlight, the same "per-cell random
    -> colorize gradient" idiom already proven in `cookbook_stone.py`'s
    `s04`/`s09` and `cookbook_scifi.py`'s chip mask), and the flat
    `RoughnessConst` texture that makes an ORM map export (same gap
    gl01/dry_earth has: the donor's roughness input is unconnected).
    Roughness itself is now pushed LOW (0.08, down from v1's already-lower-
    than-gl01 0.1) for an actually glossy gem surface -- v1's grain read as
    matte regardless of the roughness number because the height-channel
    noise was doing the visual work, not the roughness value; with that
    noise gone, a low roughness should finally read as shiny.
    `FacetNormal`'s `param4=0` flat-normal fix stays; `param1` (relief
    strength) is 0.6, still pronounced but slightly down from v1's 0.65
    now that the whole signal feeding it is a clean, sharp edge (no
    softening blend behind it, so less strength is needed for the same
    visual punch)."""
    g = load_example("dry_earth")
    retype(g, "voronoi_0", "voronoi_triangle",
           {"scale_x": 10, "scale_y": 10, "stretch_x": 1, "stretch_y": 1, "randomness": 0.85})
    _drop_nodes(g, ["warp_0", "perlin_0", "perlin_1", "colorize_3", "blend_0",
                    "colorize_4", "blend_1", "colorize"])

    # Facet tint (albedo): straight from the per-facet random color (port 2),
    # no darkening blend on top -- a clean flat color per facet.
    g["connections"].append(
        {"from": "voronoi_0", "from_port": 2, "to": "colorize_0", "to_port": 0})
    set_gradient(g, "colorize_0", [    # one coherent emerald family, dark->bright per facet
        (0.0, 0.02, 0.18, 0.09),
        (0.35, 0.04, 0.35, 0.16),
        (0.7, 0.06, 0.55, 0.27),
        (1.0, 0.12, 0.75, 0.40),
    ])
    g["connections"].append(
        {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0})

    # Facet edges (normal): the border-distance signal (port 1, already
    # wired to colorize_1/EdgeRamp by the donor) straight into normal_map,
    # no warp/blend/second-ramp detour -- a sharp, un-softened edge signal.
    # EdgeRamp's gradient is left at the dry_earth DONOR's own untouched
    # default (thin dark line at pos 0-0.0636, white beyond); that default
    # is a per-cell-normalized threshold so it stays a thin proportional
    # edge line at any voronoi scale, this recipe's scale=10 included.
    g["connections"].append(
        {"from": "colorize_1", "from_port": 0, "to": "normal_map_0", "to_port": 0})
    set_param(g, "normal_map_0", "param4", 0)     # flat-normal fix (docs/AUTHORING.md)
    set_param(g, "normal_map_0", "param1", 0.6)   # sharp facet-edge relief

    drop_conn(g, "Material", 1)
    set_param(g, "Material", "metallic", 0)
    set_param(g, "Material", "roughness", 0.08)   # low: actually glossy, not matte

    # Same ORM gap as gl01: dry_earth leaves the roughness INPUT
    # unconnected, so a scalar-only roughness exports no ORM map. Flat
    # low-roughness texture; its own input source doesn't matter (the
    # gradient is a flat constant either way) so it reuses FacetCells' port
    # 0 rather than keeping a noise node alive just to feed it.
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.08, 0.08, 0.08), (1.0, 0.08, 0.08, 0.08)])})
    g["connections"].append(
        {"from": "voronoi_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})

    # Group the now-minimal graph into two named subgraphs, same convention
    # every other cookbook recipe follows (docs/AUTHORING.md, "Grouping into
    # subgraphs") even at this small a node count (see p01_glossy_plastic in
    # cookbook_plastics.py for the same call at a similar size). FacetCells
    # is the sole generator feeding both groups (color via port 2, and both
    # the edge signal and the roughness carrier via ports 1/0), so -- same
    # reasoning as p01 -- it's folded into facet_color rather than left
    # top-level as a single-purpose shared node would be; facet_finish
    # receives its two inputs as plain boundary ports.
    group_into_subgraph(
        g, ["voronoi_0", "colorize_0"], "facet_color", "Facet Color",
        [("voronoi_0", "scale_x", "param0", "Facet size"),
         ("colorize_0", "gradient", "param1", "Facet color")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_1", "normal_map_0", "rough_const"], "facet_finish", "Facet Finish",
        [("rough_const", "gradient", "param0", "Roughness"),
         ("normal_map_0", "param1", "param1", "Surface relief")],
        catalog,
    )
    rename_nodes(g, _GL02_NAMES)
    return save_variant(g, _LABEL, "gl02_cut_gem", 1)


# gl03 clones the SAME dry_earth donor as gl01/gl02, but retypes voronoi_0 to
# `shard_fbm` -- a node with only ONE output port (type f), unlike voronoi's
# four-port signature (f, f, rgb, rgba) that gl02's voronoi_triangle swap
# relied on for connection safety. The donor's only outgoing wire off
# voronoi_0 uses from_port 1 (the "Border" output feeding CrackRamp), not
# port 0, so retype() alone leaves that connection pointing at a port that
# no longer exists; the builder repoints it to shard_fbm's sole port 0
# right after the retype (inline, since this connection-repair need is
# unique to this one donor swap).
#
# docs/AUTHORING.md's pinned finding: shard_fbm at its own defaults
# (sharp=0.7, folds=0) reads as a soft turbulent CLOUD, not a crystalline
# shatter. Isolated-node renders during authoring (render_node_output on
# just this node, three params sweeps) confirmed that in person:
#   - sharp=0.7 folds=0 (the raw default): soft cloud, no hard edges.
#   - sharp=1.0 folds=4 iter=5 sx=10 sy=10: fine moire/ripple interference,
#     too busy -- reads as scanline static, not clean fracture lines.
#   - sharp=0.95 folds=3: sharp straight crack lines but with busy
#     concentric ripple contours crowding the space between them.
#   - sharp=0.9 folds=2 sx=7 sy=7 iter=4 per=0.5 off=0 (CHOSEN): clean
#     angular straight fracture lines cutting across smoother panels --
#     the clearest "shattered crystal" read of the four, so this is what
#     ships. Well above the pinned defaults on both sharp and folds, per
#     AUTHORING.md's own instruction.
_GL03_NAMES = {
    "voronoi_0": "ShardField",
    "colorize_1": "CrackRamp",
    "warp_0": "FractureWarp",
    "colorize_0": "BaseTone",
    "blend_0": "CrackComposite",
    "colorize_3": "ColorizeUnused",     # dead: its Material connection is dropped, forced metallic=0
    "perlin_0": "AmbientNoise",         # shared: feeds BaseTone and the relief composite
    "perlin_1": "CrackWarpNoise",       # shared: feeds FractureWarp's amount and the dead ColorizeUnused
    "colorize_4": "ReliefContrast",
    "blend_1": "ReliefComposite",
    "colorize": "ReliefRamp",
    "normal_map_0": "CrystalNormal",
    "rough_const": "RoughnessConst",
}


def build_gl03_shattered_crystal(catalog: dict) -> str:
    """Shattered/cracked crystal glass: proves the `shard_fbm` base (zero
    prior cookbook use) for a hard-edged fracture-network look, distinct
    from both existing glass siblings. `gl01_frosted_glass` is a CONNECTED
    SANDBLAST crack network off `voronoi` -- soft, diffuse, matte, cool
    blue-gray. `gl02_cut_gem` is FACETED `voronoi_triangle` cells -- uniform
    hex-ish cut facets, glossy emerald. `gl03` instead reads as a jewel-tone
    slab of glass that has been SHATTERED: sharp straight crack lines
    cutting across smoother panels (the `shard_fbm` field itself, pushed
    well past its soft-cloud defaults -- see the module comment above for
    the isolated-node sweep that picked sharp=0.9/folds=2), glossy and
    saturated violet-blue rather than gl01's matte neutral or gl02's flat
    emerald-per-facet.

    `FractureWarp`'s amount is cut from the donor's 0.4 to 0.08 -- gl01
    leans INTO that same warp to soften/organic-ify its crack joints (the
    "connected sandblast" look); here the goal is the opposite, so the
    warp is kept just large enough to avoid a perfectly computed/sterile
    line (donor precedent: a warp node feeding a crack composite) without
    smearing the shard field's hard angles into gl01's soft look.
    `CrackComposite`'s amount is raised to 0.5 (up from the donor's 0.4)
    for higher-contrast, more visible fracture lines against the jewel
    base tone -- a first pass at 0.6 combined with a darker base gradient
    read as an almost-black smudge in render_preview (shard_fbm's crack
    signal covers the WHOLE surface, unlike voronoi's flat-cell-interior-
    plus-thin-border signal gl01/gl02 multiply against, so the same
    multiply-composite idiom darkens much more broadly here); the fix was
    both this small amount trim AND brightening `BaseTone` below.
    `ReliefComposite`'s amount is cut to 0.25 (down from the
    donor's 0.5) so the ambient `AmbientNoise` mixed into the height
    signal doesn't wash out the crack sharpness the way it subtly does in
    gl01's frost -- this is a hard-edged crystal, not a soft-diffused
    surface, so the height signal should stay dominated by the shard
    field's own crack contrast."""
    g = load_example("dry_earth")
    retype(g, "voronoi_0", "shard_fbm",
           {"sharp": 0.9, "sx": 7, "sy": 7, "folds": 2, "iter": 4, "per": 0.5, "off": 0})
    # shard_fbm exposes only one output (port 0); the donor's wire off
    # voronoi_0 used port 1 (voronoi's "Border" output). Repoint it.
    for c in g["connections"]:
        if c["from"] == "voronoi_0" and c["from_port"] == 1:
            c["from_port"] = 0

    # NOT a narrow near-zero threshold (gl01/gl02's convention for voronoi's
    # "Border" output, which is near-zero only at cell edges and high
    # everywhere else): shard_fbm has no such output, it's a continuous
    # turbulent field whose crack-like structure IS its dark/light
    # transitions across the WHOLE 0..1 range. A narrow (0, 0.1) threshold
    # (v1's first attempt) crushed almost the entire field to flat white --
    # confirmed by rendering CrackRamp in isolation, which came back as a
    # blank page with a few stray specks. This mild S-curve instead keeps
    # the field's own structure (verified by the same isolated-node render:
    # a crisp b&w shattered-crystal pattern nearly identical to the raw
    # field, just with slightly more contrast at the extremes).
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (0.3, 0.15, 0.15, 0.15),
                                    (0.7, 0.85, 0.85, 0.85), (1.0, 1, 1, 1)])
    set_param(g, "warp_0", "amount", 0.08)     # keep the shard field's hard angles, minimal softening
    set_param(g, "blend_0", "amount", 0.5)     # visible fracture lines without swallowing the base tone

    # Jewel-tone violet-blue "crystal" base. Brighter than a first pass that
    # matched gl01's darker earthy value range: since shard_fbm's crack
    # signal covers the WHOLE surface (a dense turbulent field, not
    # voronoi's flat cell interiors with occasional thin borders), the
    # multiply composite below darkens broadly rather than at isolated
    # seams -- confirmed by a first render_preview coming back nearly black
    # and unreadable. This gradient is pushed brighter/more saturated so the
    # final composited surface still reads as a lit gem, not a dark smudge.
    set_gradient(g, "colorize_0", [
        (0.0, 0.20, 0.12, 0.45),
        (0.5, 0.38, 0.24, 0.72),
        (1.0, 0.62, 0.48, 0.92),
    ])

    drop_conn(g, "Material", 1)
    set_param(g, "Material", "metallic", 0)
    set_param(g, "Material", "roughness", 0.07)   # glossy: clear/cut-crystal glass, not diffuse frost

    set_param(g, "blend_1", "amount", 0.25)   # keep the height signal crack-dominated, not ambient-washed
    set_param(g, "normal_map_0", "param4", 0)     # flat-normal fix (docs/AUTHORING.md)
    set_param(g, "normal_map_0", "param1", 0.8)   # hard crystalline relief -- push past gl02's 0.6

    # Same ORM gap as gl01/gl02: dry_earth's roughness input is unconnected,
    # so a scalar-only roughness exports no ORM map. Flat low-roughness
    # texture; input source doesn't matter (constant gradient either way).
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.07, 0.07, 0.07), (1.0, 0.07, 0.07, 0.07)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})

    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "warp_0", "colorize_0", "blend_0", "colorize_3"],
        "base_color", "Base Color",
        [("voronoi_0", "sharp", "param0", "Shard sharpness"),
         ("colorize_0", "gradient", "param1", "Base color"),
         ("blend_0", "amount", "param2", "Crack contrast")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_4", "blend_1", "colorize", "normal_map_0", "rough_const"],
        "surface_detail", "Surface Detail",
        [("rough_const", "gradient", "param0", "Roughness"),
         ("normal_map_0", "param1", "param1", "Surface relief")],
        catalog,
    )
    rename_nodes(g, _GL03_NAMES)
    return save_variant(g, _LABEL, "gl03_shattered_crystal", 1)


# gl04 is the first cookbook material to use `crystal`, a compound
# (`graph`-type) node with NO internal mode switch -- unlike this round's
# other two compound-node siblings (`dirt`'s param0 mode picker,
# `directional_noise`'s implicit direction control), `crystal.mmg`'s
# `gen_parameters` block exposes only param0/param1 (Scale X/Scale Y, both
# defaulting to 16), which drive TWO independently-seeded internal `voronoi`
# fields (verified by reading `crystal.mmg`: `voronoi` seed_int 0, `voronoi_2`
# seed_int 1998774700, both scale_x=scale_y=16, stretch=0.85) combined
# through a chain of `math` nodes into one output. Built from scratch via
# `_from_scratch_noise_material` (no donor has this topology), then
# `retype()`d from the placeholder `perlin_0` to `crystal` -- the same
# connection-safe move `t09`/`t10` use, since a compound node's port 0 is a
# plain `f` output like `perlin`'s.
_GL04_NAMES = {
    "perlin_0": "CrystalCells",     # placeholder perlin, retyped to `crystal` below
    "colorize_0": "CrystalColor",
    "normal_map_0": "CrystalNormal",
    "rough_const": "RoughnessConst",
}


def build_gl04_raw_crystal_cluster(catalog: dict) -> str:
    """Raw crystal cluster: proves the `crystal` compound node (zero prior
    cookbook use) for an irregular, natural crystal-formation look -- a
    fourth glass topology distinct from all three existing siblings.
    `gl01_frosted_glass` is a CONNECTED SANDBLAST crack network off plain
    `voronoi` (soft, diffuse, matte). `gl02_cut_gem` is FACETED
    `voronoi_triangle` cells (uniform, flat, hard-edged, no cracks).
    `gl03_shattered_crystal` is a dense CONTINUOUS `shard_fbm` fracture field
    (turbulent, covers the whole surface). `crystal`'s two-voronoi composite
    is none of those: it reads as a cluster of irregular, variably-sized
    polygonal cells with bright pointed glints near cell centers and dark
    crack-like valleys at cell boundaries -- like a raw amethyst geode or
    quartz cluster, not a cut/faceted/fractured surface.

    VERIFICATION (isolated single-node render via the MCP
    `render_node_output` tool, `CrystalCells`/`perlin_0` at the
    `crystal.mmg`-default `param0=16, param1=16` before any grouping):
    the raw grayscale output is an irregular mosaic of polygonal cells,
    clearly varying in size and shape (not a uniform grid -- some cells
    span several times the area of their neighbors), separated by dark
    crack-like boundaries, with a sharp bright pointed highlight near the
    center of many (not all) cells. That confirms the two-voronoi-composite
    reads as an irregular natural crystal cluster rather than a regular
    tiled pattern, and is visibly distinct from `gl02_cut_gem`'s uniform
    `voronoi_triangle` mosaic.

    That same render's pixel histogram (4,194,304 samples, 8-bit) came back
    heavily skewed dark: min 0, p50 (median) 23, p90 67, p99 117, max 223
    (of 255) -- i.e. roughly half the field sits below ~0.09 normalized and
    the bright glints are a thin tail up to ~0.87, not a flat 0..1 spread.
    A naive 0.0/0.5/1.0 gradient would have wasted its top half on values
    the field barely reaches. `CrystalColor`'s gradient stops are placed
    against that measured distribution instead: 0.0 and 0.08 bracket the
    dense low end (median 0.09) with the deepest valley tones, 0.22 and
    0.45 cover the p75-p99 range (0.17-0.46) with the mid-facet tones, and
    0.80 catches the sparse bright tail (p99.5+ up to the observed max
    ~0.87) with a near-white glint color -- so the interesting structure
    (crack valleys vs. facet centers vs. glints) actually shows up in the
    final render instead of collapsing into one flat dark hue.

    Palette is jewel-tone amethyst purple (deep violet valleys through
    lavender mid-tones to near-white glints), distinct from `gl02`'s flat
    emerald and `gl03`'s blue-violet. Roughness is pushed low (0.06, at
    `gl02_cut_gem`'s glossy calibration point) for actually-glossy crystal
    faces, not matte. `CrystalNormal`'s `param1` (relief strength) is 0.7 --
    between `gl02`'s 0.6 and `gl03`'s 0.8 -- for sharp crystalline facet
    relief without over-exaggerating it into `gl03`'s territory.
    `param4=0` is the required flat-normal fix."""
    g = _from_scratch_noise_material(
        {"scale_x": 16, "scale_y": 16},  # placeholder; retyped to crystal below
        [(0.0, 0.10, 0.03, 0.16), (0.08, 0.22, 0.09, 0.32),
         (0.22, 0.42, 0.22, 0.55), (0.45, 0.62, 0.42, 0.75),
         (0.80, 0.92, 0.85, 0.95)],
        metallic=0.0, roughness=0.06, normal_amount=0.7)
    retype(g, "perlin_0", "crystal", {"param0": 16, "param1": 16})
    set_param(g, "normal_map_0", "param4", 0)   # flat-normal fix (docs/AUTHORING.md)

    # crystal (like dry_earth/wavelet_noise/dirt before it) leaves the
    # roughness INPUT unconnected on a from-scratch skeleton, so a
    # scalar-only roughness exports no ORM map. Flat low-roughness texture,
    # same fix as every prior glass sibling.
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.06, 0.06, 0.06), (1.0, 0.06, 0.06, 0.06)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})

    # Same two-group split as every other from-scratch cookbook material
    # (p01_glossy_plastic, t09_rippled_wet_sand, t10_packed_dirt): the
    # generator feeds both the color and normal/roughness paths, so it lives
    # in the pattern group rather than staying top-level as a single-purpose
    # shared node.
    group_into_subgraph(
        g, ["perlin_0", "colorize_0"], "crystal_pattern", "Crystal Pattern",
        [("perlin_0", "param0", "param0", "Cell scale"),
         ("colorize_0", "gradient", "param1", "Crystal color")],
        catalog,
    )
    group_into_subgraph(
        g, ["normal_map_0", "rough_const"], "crystal_finish", "Crystal Finish",
        [("rough_const", "gradient", "param0", "Roughness"),
         ("normal_map_0", "param1", "param1", "Surface relief")],
        catalog,
    )
    rename_nodes(g, _GL04_NAMES)
    return save_variant(g, _LABEL, "gl04_raw_crystal_cluster", 1)


BUILDERS = {
    "gl01_frosted_glass": build_gl01_frosted_glass,
    "gl02_cut_gem": build_gl02_cut_gem,
    "gl03_shattered_crystal": build_gl03_shattered_crystal,
    "gl04_raw_crystal_cluster": build_gl04_raw_crystal_cluster,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
