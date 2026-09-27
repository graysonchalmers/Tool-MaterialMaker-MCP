"""Cookbook: ceramic category. Phase-3 hero folded in from the retired
examples/ folder (2026-09-05): the graph comes unchanged from
quality/author.py's shared builder via take_variant; this builder only groups
it. Outputs land under quality/authored/cookbook-ceramic/<case>/v1.ptex.

Run: python -m quality.cookbook_ceramic
Then: python -m quality.promote_cookbook cookbook-ceramic
"""
import copy
import sys

from quality import author  # shared builder base; regression guard is promote_cookbook --check
from quality.author_helpers import (widen_widget, save_variant, take_variant, group_into_subgraph, rename_nodes,
                     set_gradient, set_param, retype, add_node, _grad,
                     _from_scratch_noise_material, rewire, node, place,
                     tidy_ports, link_also)

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-ceramic"

# `beehive` donor mapping for man02. beehive_2 produces the clean hex value
# (port 0, rewired to drive albedo/roughness directly) and a per-cell random
# tone (port 1); colorize_2/colorize convert those two into the inputs mixed
# by blend for the relief pathway (normal + height), which man02's albedo
# and roughness no longer read from since they were rewired straight off
# beehive_2. Material port 6 is depth_tex (height), fed by colorize_3.
_MAN02_NAMES = {
    "beehive_2": "HexLayout",
    "colorize_5": "TileColor",       # albedo: tile + thin grout line
    "colorize_4": "GlazeRoughness",  # roughness: inverted (glazed face, rough grout)
    "colorize_2": "StructureTone",   # hex-value tone feeding the relief blend
    "colorize": "CellRandomTone",    # per-cell random tone feeding the relief blend
    "blend": "ReliefBlend",          # mixes the two tones for normal + height
    "normal_map": "GroutNormal",
    "colorize_3": "GroutDepth",      # feeds Material's depth_tex port
    "uniform_greyscale": "NonMetallic",
}


# Per-tile terrace depth for man02's hex relief, as a fraction of the grout
# depth: faces sit between 1 - k and 1 above the grout (0).
_MAN02_TERRACE = 0.15


def _position_seed(x: float, y: float) -> int:
    """Material Maker's seed for a node saved without one
    (gen_base.gd get_seed_from_position): ((int(x) * 0x1f1f1f1f) ^ int(y))
    % 65536, GDScript ints (truncating int(), C-style % keeps the sign)."""
    v = (int(x) * 0x1F1F1F1F) ^ int(y)
    return -(-v % 65536) if v < 0 else v % 65536


def build_man02_ceramic_hex_tiles(catalog: dict) -> str:
    """White ceramic hexagon tiles (was examples/man02_ceramic_hex_tiles,
    iter1 variant 1): `beehive` clone, non-metallic, faces recolored white
    with a thin dark grout band, roughness inverted (glazed faces, rough
    grout), hex relief kept but inverted so the grout is a recessed groove
    (2026-09-27; the donor's relief made it a raised ridge, see below and
    the card). `uniform_greyscale`
    (metallic 0) stays top-level as a single donor-default constant.

    TILE HOST (2026-09-27): absorbs s05_hex_stone_tile and man03_mosaic_tile.
    s05 is this same beehive graph with the colour and roughness read off
    the per-cell blend instead of the clean hex field, plus a perlin grain
    multiplied over both; man03 is a different generator (`skewed_bricks`)
    feeding the same colour / roughness / normal shape. So the host carries
    `skewed_bricks` in as a Brick Layout, and two switches pick the result:
    - Layout (0 hex, 1 bricks): colour, roughness, normal and height.
    - Tone source (0 clean hex, 1 per-cell stone): in hex mode, whether
      colour and roughness read the clean hex value (man02) or the per-cell
      blend (s05). The per-cell blend for colour comes from a twin of the
      relief chain (StoneLayout ... StoneToneBlend, same params, linked to
      the same exposed controls, StoneLayout given HexLayout's position
      seed explicitly).
    The switches select AFTER the colorizes and normal maps, not before:
    each source keeps its own colorize (one exposed ramp linked to all
    three) and its own normal, and Normal blends whose mask is an `A<B`
    threshold (0 or 1) pick one. A first build selected the field before
    the colorizes (f07-style product-sum math); that is exact arithmetic,
    but the GPU compiler rounded `beehive` differently in the new context
    and 0.002-0.04% of default pixels moved by 1/255. The same happened
    when the colour path's per-cell tone read the relief chain's own
    beehive (a second use of it in the albedo shader), hence the twin.
    Height has no blend: GroutDepth reads a product-sum of the two relief
    fields, which measured 0 px.
    - Surface Grain (s05's nodes and values): perlin grain multiplied over
      albedo and roughness. Grain on blend port 0 and the base on port 1,
      so Grain strength 0 passes the base through bit-exact.
    BrickNormal keeps man03's resolution (param0 = 10) inside; Grout depth
    drives both normals. Each absorbed material is a preset on the card
    (cookbook/ceramic/man02_ceramic_hex_tiles.md). Seeds: beehive, perlin
    and skewed_bricks seed from node position, so HexLayout keeps its
    donor spot and BrickLayout / GrainNoise sit at (0, 0) as in man03/s05.
    Material-node params are unchanged (they only reach the .tres).
    Measured 2048 diffs (Pillow, full image) when the host landed: default
    vs pre-host man02 albedo, ORM, heightmap 0 px, normal 1 px at 1/255;
    s05 preset albedo, ORM, heightmap 0 px, normal <= 3/255; man03 preset
    albedo, normal, ORM 0 px.
    RECESSED GROUT (2026-09-27): the hex relief chain (colorize_2, colorize,
    blend; the colour twin is copied before this) is inverted, see the
    comment in the body: relief = 1 - max(S, k*C), k = _MAN02_TERRACE.
    Diffs vs the host before it, default and s05 preset: albedo, ORM 0 px,
    normal and heightmap changed by design; man03 preset 0 px on all four
    maps and lit. Polarity (2048, grout/face = darkest/brightest 10% of a
    clean-hex albedo mask): default height grout 56 vs faces 241 (was 208
    vs 88), faces' 5th percentile 217; corr(normal R, -d mask/dx) +0.58
    (was -0.23; s07 cobblestone +0.48). s05 preset 55 vs 242, +0.45."""
    g = take_variant(author.build_man02_ceramic_hex_tiles, _LABEL, 1)
    # Direct normal path (2026-09-27): the donor's buffered param4=1 races to a
    # flat normal headless; param4=0 at the same param1 matches within 0.37/255.
    set_param(g, "normal_map", "param4", 0)
    tile_ramp = node(g, "colorize_5")["parameters"]["gradient"]
    glaze_ramp = node(g, "colorize_4")["parameters"]["gradient"]

    # --- Stone tone: a twin of the hex relief chain for the colour path ---
    # s05 reads colour off the per-cell blend. Reading it off the relief
    # chain's own nodes puts a second use of beehive_2:0 into the albedo
    # shader, and the GPU compiler then rounds the clean-hex colour path
    # differently (1/255 flips on 0.008% of pixels). A twin chain has its own
    # uniforms, so nothing is shared. StoneLayout carries beehive_2's
    # position-derived seed explicitly, so its per-cell tones match s05's.
    hx, hy = (node(g, "beehive_2")["node_position"][k] for k in ("x", "y"))
    for twin, src in (("StoneLayout", "beehive_2"), ("StoneStructureTone", "colorize_2"),
                      ("StoneCellTone", "colorize"), ("StoneToneBlend", "blend")):
        add_node(g, twin, node(g, src)["type"], copy.deepcopy(node(g, src)["parameters"]))
    node(g, "StoneLayout")["seed"] = _position_seed(hx, hy)
    g["connections"] += [
        {"from": "StoneLayout", "from_port": 0, "to": "StoneStructureTone", "to_port": 0},
        {"from": "StoneLayout", "from_port": 1, "to": "StoneCellTone", "to_port": 0},
        {"from": "StoneStructureTone", "from_port": 0, "to": "StoneToneBlend", "to_port": 0},
        {"from": "StoneCellTone", "from_port": 0, "to": "StoneToneBlend", "to_port": 1},
    ]

    # --- Recessed grout: invert the hex relief (normal + height only) ---
    # The donor relief is Lighten(StructureTone, CellRandomTone) = max(S, C):
    # S is 1 on the grout band, C a per-cell tone (0-0.23, or 0.97 on about a
    # third of the cells), so the grout came out a RAISED ridge. Here S -> 1-S,
    # C -> 1 - k*C and Lighten -> Darken, so relief = min(1-S, 1-kC) =
    # 1 - max(S, kC): the old field turned upside down with the per-cell
    # tone squeezed to k, i.e. grout at 0 and every face between 1-k and 1.
    # Only the relief chain changes; the colour twin above was copied first.
    for name, scale in (("colorize_2", 1.0), ("colorize", _MAN02_TERRACE)):
        for pt in node(g, name)["parameters"]["gradient"]["points"]:
            for ch in ("r", "g", "b"):
                pt[ch] = round(1 - scale * pt[ch], 6)
    set_param(g, "blend", "blend_type", 10)                          # Darken

    # --- Brick Layout (man03's generator, man03's values) ---
    add_node(g, "BrickLayout", "skewed_bricks", {
        "rows": 6, "columns": 3, "offset": 0.5, "randomness": 1,
        "mortar": 0.1, "bevel": 0.1, "round": 0, "corner": 0.3})

    # --- Switches: Layout (hex / bricks) and Tone source (clean / per-cell) ---
    add_node(g, "LayoutSelect", "uniform_greyscale", {"color": 0})
    add_node(g, "ToneSelect", "uniform_greyscale", {"color": 0})
    add_node(g, "IsBricks", "math", {"op": 15, "default_in1": 0.5})    # 0.5 < L
    add_node(g, "IsHex", "math", {"op": 1, "default_in1": 1})          # 1 - IsBricks
    add_node(g, "IsCellTone", "math", {"op": 15, "default_in1": 0.5})  # 0.5 < T
    # height only: relief = hex blend x (1 - l) + bricks x l
    add_node(g, "HexReliefTerm", "math", {"op": 2})
    add_node(g, "BrickReliefTerm", "math", {"op": 2})
    add_node(g, "ReliefMix", "math", {"op": 0})
    g["connections"] += [
        {"from": "LayoutSelect", "from_port": 0, "to": "IsBricks", "to_port": 1},
        {"from": "IsBricks", "from_port": 0, "to": "IsHex", "to_port": 1},
        {"from": "ToneSelect", "from_port": 0, "to": "IsCellTone", "to_port": 1},
        {"from": "blend", "from_port": 0, "to": "HexReliefTerm", "to_port": 0},
        {"from": "IsHex", "from_port": 0, "to": "HexReliefTerm", "to_port": 1},
        {"from": "BrickLayout", "from_port": 0, "to": "BrickReliefTerm", "to_port": 0},
        {"from": "IsBricks", "from_port": 0, "to": "BrickReliefTerm", "to_port": 1},
        {"from": "HexReliefTerm", "from_port": 0, "to": "ReliefMix", "to_port": 0},
        {"from": "BrickReliefTerm", "from_port": 0, "to": "ReliefMix", "to_port": 1},
    ]
    rewire(g, "colorize_3", 0, "ReliefMix", 0)

    # --- Colour and roughness: one colorize per source, switched after ---
    # colorize_5 / colorize_4 keep reading beehive_2:0 exactly as before.
    for name, ramp, src, port in (
            ("CellTileColor", tile_ramp, "StoneToneBlend", 0),
            ("BrickTileColor", tile_ramp, "BrickLayout", 0),
            ("CellGlazeRoughness", glaze_ramp, "StoneToneBlend", 0),
            ("BrickGlazeRoughness", glaze_ramp, "BrickLayout", 0)):
        add_node(g, name, "colorize", {"gradient": copy.deepcopy(ramp)})
        g["connections"].append({"from": src, "from_port": port, "to": name, "to_port": 0})
    for mix in ("ToneColorMix", "LayoutColorMix", "ToneRoughnessMix", "LayoutRoughnessMix"):
        add_node(g, mix, "blend", {"blend_type": 0, "amount": 1})     # Normal, mask = switch
    g["connections"] += [
        {"from": "CellTileColor", "from_port": 0, "to": "ToneColorMix", "to_port": 0},
        {"from": "colorize_5", "from_port": 0, "to": "ToneColorMix", "to_port": 1},
        {"from": "IsCellTone", "from_port": 0, "to": "ToneColorMix", "to_port": 2},
        {"from": "BrickTileColor", "from_port": 0, "to": "LayoutColorMix", "to_port": 0},
        {"from": "ToneColorMix", "from_port": 0, "to": "LayoutColorMix", "to_port": 1},
        {"from": "IsBricks", "from_port": 0, "to": "LayoutColorMix", "to_port": 2},
        {"from": "CellGlazeRoughness", "from_port": 0, "to": "ToneRoughnessMix", "to_port": 0},
        {"from": "colorize_4", "from_port": 0, "to": "ToneRoughnessMix", "to_port": 1},
        {"from": "IsCellTone", "from_port": 0, "to": "ToneRoughnessMix", "to_port": 2},
        {"from": "BrickGlazeRoughness", "from_port": 0, "to": "LayoutRoughnessMix", "to_port": 0},
        {"from": "ToneRoughnessMix", "from_port": 0, "to": "LayoutRoughnessMix", "to_port": 1},
        {"from": "IsBricks", "from_port": 0, "to": "LayoutRoughnessMix", "to_port": 2},
    ]

    # --- Normal: the hex normal as before, man03's brick normal, switched after ---
    add_node(g, "BrickNormal", "normal_map",
             {"param0": 10, "param1": 1.02, "param2": 0, "param4": 0})
    add_node(g, "NormalMix", "blend", {"blend_type": 0, "amount": 1})
    g["connections"] += [
        {"from": "BrickLayout", "from_port": 0, "to": "BrickNormal", "to_port": 0},
        {"from": "BrickNormal", "from_port": 0, "to": "NormalMix", "to_port": 0},
        {"from": "normal_map", "from_port": 0, "to": "NormalMix", "to_port": 1},
        {"from": "IsBricks", "from_port": 0, "to": "NormalMix", "to_port": 2},
    ]
    rewire(g, "Material", 4, "NormalMix", 0)

    # --- Surface Grain (s05's nodes and values; strength 0 = off) ---
    add_node(g, "GrainNoise", "perlin", {"scale_x": 48, "scale_y": 48, "iterations": 5})
    add_node(g, "GrainContrastAlbedo", "colorize",
             {"gradient": _grad([(0.0, 0.80, 0.80, 0.80), (1.0, 1.0, 1.0, 1.0)])})
    add_node(g, "GrainContrastRoughness", "colorize",
             {"gradient": _grad([(0.0, 0.85, 0.85, 0.85), (1.0, 1.05, 1.05, 1.05)])})
    add_node(g, "AlbedoGrain", "blend", {"blend_type": 2, "amount": 0})     # Multiply
    add_node(g, "RoughnessGrain", "blend", {"blend_type": 2, "amount": 0})
    g["connections"] += [
        {"from": "GrainNoise", "from_port": 0, "to": "GrainContrastAlbedo", "to_port": 0},
        {"from": "GrainNoise", "from_port": 0, "to": "GrainContrastRoughness", "to_port": 0},
        {"from": "GrainContrastAlbedo", "from_port": 0, "to": "AlbedoGrain", "to_port": 0},
        {"from": "LayoutColorMix", "from_port": 0, "to": "AlbedoGrain", "to_port": 1},
        {"from": "GrainContrastRoughness", "from_port": 0, "to": "RoughnessGrain", "to_port": 0},
        {"from": "LayoutRoughnessMix", "from_port": 0, "to": "RoughnessGrain", "to_port": 1},
    ]
    rewire(g, "Material", 0, "AlbedoGrain", 0)
    rewire(g, "Material", 2, "RoughnessGrain", 0)

    # Seed-bearing nodes where their originals keep them (see docstring);
    # beehive_2 is never moved. Everything else spaced by data flow.
    place(g, {
        "BrickLayout": (0, 0), "GrainNoise": (0, 0),
        "StoneLayout": (-595, -450), "StoneStructureTone": (-590, -350),
        "StoneCellTone": (-590, -280), "StoneToneBlend": (-600, -210),
        "LayoutSelect": (0, 300), "ToneSelect": (0, 0),
        "IsBricks": (250, 300), "IsHex": (500, 400), "IsCellTone": (250, 0),
        "HexReliefTerm": (750, 350), "BrickReliefTerm": (750, 550), "ReliefMix": (1000, 450),
        "CellTileColor": (-275, -300), "BrickTileColor": (-275, -450),
        "CellGlazeRoughness": (-280, 150), "BrickGlazeRoughness": (-280, 300),
        "ToneColorMix": (50, -200), "LayoutColorMix": (300, -250),
        "ToneRoughnessMix": (50, 100), "LayoutRoughnessMix": (300, 150),
        "BrickNormal": (-270, 250), "NormalMix": (50, 150),
        "GrainContrastAlbedo": (300, -100), "GrainContrastRoughness": (300, 100),
        "AlbedoGrain": (600, -50), "RoughnessGrain": (600, 150),
    })

    group_into_subgraph(
        g, ["beehive_2", "colorize_2", "colorize", "blend",
            "StoneLayout", "StoneStructureTone", "StoneCellTone", "StoneToneBlend"],
        "hex_layout", "Hex Layout",
        [("beehive_2", "sx", "param0", "Tiles across"),
         ("beehive_2", "sy", "param1", "Tiles down"),
         ("blend", "amount", "param2", "Edge softness")],
        catalog,
    )
    link_also(g, "hex_layout", "param0", "StoneLayout", "sx")
    link_also(g, "hex_layout", "param1", "StoneLayout", "sy")
    link_also(g, "hex_layout", "param2", "StoneToneBlend", "amount")
    tidy_ports(g, "hex_layout", [],
               [("beehive_2", 0, "hex"), ("blend", 0, "relief"),
                ("StoneToneBlend", 0, "stone_tone")], catalog)
    group_into_subgraph(
        g, ["BrickLayout"], "brick_layout", "Brick Layout",
        [("BrickLayout", "rows", "param0", "Brick rows"),
         ("BrickLayout", "columns", "param1", "Brick columns"),
         ("BrickLayout", "randomness", "param2", "Jitter"),
         ("BrickLayout", "mortar", "param3", "Mortar width")],
        catalog,
    )
    tidy_ports(g, "brick_layout", [], [("BrickLayout", 0, "bricks")], catalog)
    group_into_subgraph(
        g, ["LayoutSelect", "ToneSelect", "IsBricks", "IsHex", "IsCellTone",
            "HexReliefTerm", "BrickReliefTerm", "ReliefMix"],
        "tile_pattern", "Tile Pattern",
        [("LayoutSelect", "color", "param0", "Layout (0 hex, 1 bricks)"),
         ("ToneSelect", "color", "param1", "Tone source (0 clean hex, 1 per-cell stone)")],
        catalog,
    )
    tidy_ports(g, "tile_pattern",
               [("hex_layout", 1, "relief"), ("brick_layout", 0, "bricks")],
               [("IsBricks", 0, "is_bricks"), ("IsCellTone", 0, "is_cell_tone"),
                ("ReliefMix", 0, "height_relief")], catalog)
    group_into_subgraph(
        g, ["colorize_5", "CellTileColor", "BrickTileColor", "ToneColorMix", "LayoutColorMix",
            "colorize_4", "CellGlazeRoughness", "BrickGlazeRoughness", "ToneRoughnessMix",
            "LayoutRoughnessMix"],
        "tile_color", "Tile Color",
        [("colorize_5", "gradient", "param0", "Tile and grout color"),
         ("colorize_4", "gradient", "param1", "Glaze roughness")],
        catalog,
    )
    for widget in ("CellTileColor", "BrickTileColor"):
        link_also(g, "tile_color", "param0", widget, "gradient")
    for widget in ("CellGlazeRoughness", "BrickGlazeRoughness"):
        link_also(g, "tile_color", "param1", widget, "gradient")
    tidy_ports(g, "tile_color",
               [("hex_layout", 0, "hex"), ("hex_layout", 2, "stone_tone"),
                ("brick_layout", 0, "bricks"), ("tile_pattern", 0, "is_bricks"),
                ("tile_pattern", 1, "is_cell_tone")],
               [("LayoutColorMix", 0, "albedo"), ("LayoutRoughnessMix", 0, "roughness")],
               catalog)
    group_into_subgraph(
        g, ["normal_map", "BrickNormal", "NormalMix", "colorize_3"], "tile_relief", "Tile Relief",
        [("normal_map", "param1", "param0", "Grout depth")],
        catalog,
    )
    link_also(g, "tile_relief", "param0", "BrickNormal", "param1")
    tidy_ports(g, "tile_relief",
               [("hex_layout", 1, "relief"), ("brick_layout", 0, "bricks"),
                ("tile_pattern", 0, "is_bricks"), ("tile_pattern", 2, "height_relief")],
               [("NormalMix", 0, "normal"), ("colorize_3", 0, "height")], catalog)
    group_into_subgraph(
        g, ["GrainNoise", "GrainContrastAlbedo", "GrainContrastRoughness",
            "AlbedoGrain", "RoughnessGrain"],
        "surface_grain", "Surface Grain",
        [("AlbedoGrain", "amount", "param0", "Grain strength"),
         ("GrainNoise", "scale_x", "param1", "Grain scale"),
         ("GrainNoise", "iterations", "param2", "Grain detail")],
        catalog,
    )
    link_also(g, "surface_grain", "param0", "RoughnessGrain", "amount")
    link_also(g, "surface_grain", "param1", "GrainNoise", "scale_y")
    tidy_ports(g, "surface_grain",
               [("tile_color", 0, "albedo"), ("tile_color", 1, "roughness")],
               [("AlbedoGrain", 0, "albedo"), ("RoughnessGrain", 0, "roughness")], catalog)

    # Inner canvases: park the proxies at the edges of the hand-placed nodes.
    place(node(g, "tile_pattern"), {
        "gen_inputs": (500, 700), "gen_parameters": (-350, 150), "gen_outputs": (1300, 250)})
    place(node(g, "tile_color"), {
        "gen_inputs": (-650, -100), "gen_parameters": (-650, 250), "gen_outputs": (600, 0)})
    place(node(g, "tile_relief"), {
        "gen_inputs": (-650, 150), "gen_parameters": (-650, 400), "gen_outputs": (350, 150)})
    place(node(g, "brick_layout"), {"gen_parameters": (-350, 0), "gen_outputs": (350, 0)})
    place(node(g, "surface_grain"), {
        "gen_inputs": (300, 350), "gen_parameters": (-350, 0), "gen_outputs": (900, 50)})
    # Top level reads as a layer stack, left to right into Material. The
    # collapsed nodes carry seed_int 0, so moving them moves no seeds.
    place(g, {
        "hex_layout": (-1200, -100), "brick_layout": (-1200, 150),
        "tile_pattern": (-900, 150), "tile_color": (-600, -100), "tile_relief": (-600, 150),
        "surface_grain": (-300, -100), "uniform_greyscale": (-300, 150),
        "Material": (0, 0),
    })
    rename_nodes(g, _MAN02_NAMES)
    # Exposed values past the inner node's slider get their own range
    # (named_parameter, author_helpers.widen_widget):
    # Grain scale: default and s05 preset 48, perlin stops at 32.
    widen_widget(g, "surface_grain", "param1", 64, catalog)
    return save_variant(g, _LABEL, "man02_ceramic_hex_tiles", 1)


BUILDERS = {
    "man02_ceramic_hex_tiles": build_man02_ceramic_hex_tiles,
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
