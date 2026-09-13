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
                     save_variant, add_node, _grad, group_into_subgraph, rename_nodes, retype)

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


# `dry_earth` donor mapping for gl02, cloned from the SAME donor as gl01 but
# with `voronoi_0` retyped from square `voronoi` to `voronoi_triangle` (zero
# prior cookbook use). Port semantics verified via describe_node + the MM
# source (.mmg): both node types share port 0 (Nodes, f, distance to cell
# centers), port 1 (Border/Borders, f, distance to cell borders) and port 2
# (Random color, rgb, flat per-cell random) -- voronoi_triangle just adds two
# extra ports (3: UV Map, 4: a precomputed analytic Normal Map) that this
# recipe doesn't use. The existing voronoi_0(port1)->CrackRamp connection
# keeps its role (border distance -> edge mask) unchanged by the retype.
# colorize_0 is REWIRED here (gl01 fed it from the shared perlin_0 for a
# uniform frosted tone; gl02 feeds it from voronoi_0's port 2 instead, so
# each triangular facet gets its own flat jewel-tone shade -- the whole point
# of this material). colorize_3/metallic-drop follow the same dead-node
# precedent as gl01.
_GL02_NAMES = {
    "voronoi_0": "FacetCells",
    "colorize_1": "EdgeRamp",
    "warp_0": "EdgeWarp",
    "colorize_0": "FacetTint",
    "blend_0": "FacetComposite",
    "colorize_3": "ColorizeUnused",     # dead: its Material connection is dropped, forced metallic=0
    "perlin_0": "AmbientNoise",         # shared: feeds relief composite
    "perlin_1": "EdgeWarpNoise",        # shared: feeds EdgeWarp's amount and the dead ColorizeUnused
    "colorize_4": "ReliefContrast",
    "blend_1": "ReliefComposite",
    "colorize": "ReliefRamp",
    "normal_map_0": "FacetNormal",
    "rough_const": "RoughnessConst",
}


def build_gl02_cut_gem(catalog: dict) -> str:
    """Faceted cut gem: proves the `voronoi_triangle` base (triangular cells
    square voronoi cannot produce) for a hard-edged crystal / cut-gem look.
    Clones the same `dry_earth` donor gl01 uses (topology match: a
    voronoi-cell network with an edge/crack ramp, warp, and blend into an
    albedo, plus a parallel relief chain into a normal map), then RETYPES
    `voronoi_0` from square `voronoi` to `voronoi_triangle` at the exact
    starting params from the noise gallery (`scale_x`/`scale_y`=4,
    `stretch_x`/`stretch_y`=1, `randomness`=0.85) -- connection-safe because
    both node types expose the same port 0 (Nodes)/port 1 (Border)/port 2
    (Random color) signature (verified via describe_node + the node's own
    .mmg shader_model), so the existing port1->EdgeRamp wire keeps its role.

    Distinct from `gl01_frosted_glass` in every lever that matters: warp is
    pushed to near zero (0.02, vs gl01's already-low 0.05) so the naturally
    hard triangular edges stay crisp facets rather than smearing into round
    blobs or a connected-crack plate look; roughness is pushed LOW (0.1, vs
    gl01's matte 0.88) for a glassy/gem surface; and -- the key move -- the
    per-facet flat random color (`voronoi_triangle` port 2, the same idiom
    already proven in `cookbook_stone.py`'s `s04`/`s09` and
    `cookbook_scifi.py`'s chip mask) drives `FacetTint`'s gradient instead of
    gl01's uniform ambient-perlin tone, so each triangular facet gets its own
    shade from a single coherent emerald-green family (deep shadowed facets
    to a bright emerald highlight) rather than one flat color. `FacetNormal`
    keeps gl01's `param4=0` flat-normal fix but with much more relief
    strength (`param1`=0.65 vs gl01's subtle 0.15) for pronounced hard
    crystalline facet relief. Same ORM gap as gl01/dry_earth (the donor's
    roughness input is unconnected), fixed the same way with a flat
    `RoughnessConst` texture wired into Material's roughness port."""
    g = load_example("dry_earth")
    retype(g, "voronoi_0", "voronoi_triangle",
           {"scale_x": 4, "scale_y": 4, "stretch_x": 1, "stretch_y": 1, "randomness": 0.85})
    # Facet tint: replace the ambient-perlin feed with the per-facet random
    # color (port 2) so each triangular cell gets its own flat jewel shade.
    drop_conn(g, "colorize_0", 0)
    g["connections"].append(
        {"from": "voronoi_0", "from_port": 2, "to": "colorize_0", "to_port": 0})
    set_gradient(g, "colorize_0", [    # one coherent emerald family, dark->bright per facet
        (0.0, 0.02, 0.18, 0.09),
        (0.35, 0.04, 0.35, 0.16),
        (0.7, 0.06, 0.55, 0.27),
        (1.0, 0.12, 0.75, 0.40),
    ])
    # colorize_1 (EdgeRamp) gradient is left at the dry_earth DONOR's own
    # untouched default (thin dark line at pos 0-0.0636, white beyond) --
    # that default was already tuned for scale_x=scale_y=4, the exact scale
    # this recipe uses (gl01 had to retune it because it cranked scale to
    # 60; gl02 doesn't change scale at all, so the untouched threshold
    # already reads as a thin edge line at this facet density).
    set_param(g, "warp_0", "amount", 0.02)     # near zero: keep facets crisp, no organic smear
    set_param(g, "blend_0", "amount", 0.6)     # crisper facet-edge contrast than gl01's 0.5
    drop_conn(g, "Material", 1)
    set_param(g, "Material", "metallic", 0)
    set_param(g, "Material", "roughness", 0.1)   # low: glassy/gem surface, not matte
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.65)  # pronounced hard-crystalline relief
    # Same ORM gap as gl01: dry_earth leaves the roughness INPUT unconnected,
    # so a scalar-only roughness exports no ORM map. Flat low-roughness texture.
    add_node(g, "rough_const", "colorize",
             {"gradient": _grad([(0.0, 0.1, 0.1, 0.1), (1.0, 0.1, 0.1, 0.1)])})
    g["connections"].append(
        {"from": "perlin_0", "from_port": 0, "to": "rough_const", "to_port": 0})
    g["connections"].append(
        {"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})

    # Grouping mirrors gl01 exactly: same member sets, same shared top-level
    # noise sources (perlin_0/perlin_1 each feed into both groups via
    # EdgeWarp's cross-group output), only the exposed-param labels change.
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "warp_0", "colorize_0", "blend_0", "colorize_3"],
        "base_color", "Base Color",
        [("voronoi_0", "scale_x", "param0", "Facet size"),
         ("colorize_0", "gradient", "param1", "Facet color"),
         ("blend_0", "amount", "param2", "Edge contrast")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_4", "blend_1", "colorize", "normal_map_0", "rough_const"],
        "surface_detail", "Surface Detail",
        [("rough_const", "gradient", "param0", "Roughness"),
         ("normal_map_0", "param1", "param1", "Surface relief")],
        catalog,
    )
    rename_nodes(g, _GL02_NAMES)
    return save_variant(g, _LABEL, "gl02_cut_gem", 1)


BUILDERS = {
    "gl01_frosted_glass": build_gl01_frosted_glass,
    "gl02_cut_gem": build_gl02_cut_gem,
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
