"""Phase 3C authoring helpers: transform bundled example graphs toward a prompt.

These codify the kind of remixing a live authoring session does (recolor a ramp,
swap a generator, blend two layers) so each variant is reproducible and auditable.
Everything here is pure graph-JSON surgery against the catalog vocabulary; no
Godot. Author variants land under quality/authored/<iter>/<case>/vN.ptex.
"""
import copy
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
from mm_mcp.config import load_config

_CFG = load_config()
_EX = Path(_CFG.examples_dir)


def load_example(name: str) -> dict:
    with open(_EX / f"{name}.ptex", encoding="utf-8") as fh:
        return json.load(fh)


def node(graph: dict, name: str) -> dict:
    for n in graph["nodes"]:
        if n["name"] == name:
            return n
    raise KeyError(f"node {name!r} not in graph")


def set_gradient(graph: dict, node_name: str, colors: list) -> None:
    """Replace a colorize node's gradient points.

    colors: list of (pos, r, g, b) with 0..1 floats. Alpha forced to 1.
    """
    pts = [{"a": 1, "r": r, "g": g, "b": b, "pos": pos}
           for (pos, r, g, b) in colors]
    node(graph, node_name)["parameters"]["gradient"] = {
        "interpolation": 1, "points": pts, "type": "Gradient",
    }


def set_param(graph: dict, node_name: str, key: str, value) -> None:
    node(graph, node_name).setdefault("parameters", {})[key] = value


def save_variant(graph: dict, iter_label: str, case_id: str, n: int) -> str:
    out = _ROOT / "quality" / "authored" / iter_label / case_id
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"v{n}.ptex"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=1)
    return str(path)


# ---- iteration 1 builders -------------------------------------------------

def build_f02_brown_leather(iter_label: str) -> list[str]:
    """crocodile_skin cellular grain, recolored green -> brown."""
    paths = []
    # v1: warm mid-brown
    g = load_example("crocodile_skin")
    set_gradient(g, "colorize_1", [
        (0.0, 0.20, 0.11, 0.05),   # dark seam brown
        (1.0, 0.52, 0.34, 0.18),   # raised grain tan-brown
    ])
    paths.append(save_variant(g, iter_label, "f02_brown_leather", 1))
    # v2: deeper reddish leather
    g = load_example("crocodile_skin")
    set_gradient(g, "colorize_1", [
        (0.0, 0.15, 0.07, 0.04),
        (1.0, 0.44, 0.24, 0.13),
    ])
    paths.append(save_variant(g, iter_label, "f02_brown_leather", 2))
    return paths


def build_w02_barn_wood(iter_label: str) -> list[str]:
    """wood grain recolored to faded gray-brown + rougher."""
    paths = []
    # v1: weathered gray-brown
    g = load_example("wood")
    set_gradient(g, "colorize_2", [
        (0.0, 0.44, 0.42, 0.39),   # faded gray plank
        (0.25, 0.30, 0.28, 0.25),  # dark grain
        (0.5, 0.44, 0.42, 0.39),
        (0.75, 0.44, 0.42, 0.39),
        (1.0, 0.28, 0.26, 0.23),
    ])
    # raise roughness (colorize_0 feeds roughness); push both stops high
    set_gradient(g, "colorize_0", [(0.0, 0.72, 0.72, 0.72), (1.0, 0.9, 0.9, 0.9)])
    paths.append(save_variant(g, iter_label, "w02_weathered_barn_wood", 1))
    # v2: greyer, more silvered
    g = load_example("wood")
    set_gradient(g, "colorize_2", [
        (0.0, 0.50, 0.49, 0.47),
        (0.25, 0.33, 0.32, 0.30),
        (0.5, 0.50, 0.49, 0.47),
        (0.75, 0.46, 0.45, 0.43),
        (1.0, 0.30, 0.29, 0.28),
    ])
    set_gradient(g, "colorize_0", [(0.0, 0.78, 0.78, 0.78), (1.0, 0.95, 0.95, 0.95)])
    paths.append(save_variant(g, iter_label, "w02_weathered_barn_wood", 2))
    return paths


def build_m01_weathered_copper(iter_label: str) -> list[str]:
    """rusted_metal 2-layer blend recolored: base gray->copper, patches
    orange-rust->green verdigris. blend_0 albedo = colorize_2 (base metal) over
    which colorize_1 (patch) is masked by colorize_3."""
    paths = []
    # v1: bright copper with teal verdigris
    g = load_example("rusted_metal")
    set_gradient(g, "colorize_2", [   # base metal -> copper
        (0.0, 0.45, 0.22, 0.10),
        (1.0, 0.72, 0.40, 0.19),
    ])
    set_gradient(g, "colorize_1", [   # patches -> verdigris green/teal
        (0.0, 0.05, 0.20, 0.15),
        (1.0, 0.33, 0.60, 0.47),
    ])
    paths.append(save_variant(g, iter_label, "m01_weathered_copper", 1))
    # v2: darker aged copper, more coverage of patina
    g = load_example("rusted_metal")
    set_gradient(g, "colorize_2", [
        (0.0, 0.38, 0.18, 0.08),
        (1.0, 0.63, 0.34, 0.16),
    ])
    set_gradient(g, "colorize_1", [
        (0.0, 0.08, 0.24, 0.19),
        (1.0, 0.28, 0.55, 0.44),
    ])
    # widen the patina mask a touch (colorize_3 threshold 0.45 -> 0.35)
    set_gradient(g, "colorize_3", [(0.35, 0, 0, 0), (0.35, 1, 1, 1)])
    paths.append(save_variant(g, iter_label, "m01_weathered_copper", 2))
    return paths


def build_s03_cracked_concrete(iter_label: str) -> list[str]:
    """dry_earth cracked-plate pattern recolored earth->gray concrete. The crack
    network (voronoi) is organic, not a grid, so it stays clear of must_not."""
    paths = []
    # v1: light gray concrete
    g = load_example("dry_earth")
    set_gradient(g, "colorize_0", [
        (0.25, 0.63, 0.63, 0.63),   # light concrete
        (0.65, 0.34, 0.34, 0.34),   # dark stain/crack floor
    ])
    paths.append(save_variant(g, iter_label, "s03_cracked_concrete", 1))
    # v2: cooler, slightly bluish gray + subtle stain
    g = load_example("dry_earth")
    set_gradient(g, "colorize_0", [
        (0.25, 0.58, 0.59, 0.60),
        (0.65, 0.30, 0.31, 0.33),
    ])
    paths.append(save_variant(g, iter_label, "s03_cracked_concrete", 2))
    return paths


def build_w01_oak_planks(iter_label: str) -> list[str]:
    """wooden_floor already has plank divisions (bricks node) + directional
    grain (perlin scale_y>>scale_x); its albedo ramp (colorize_0) clips
    everything >0.15 to flat brown, killing the grain. Spread the ramp into an
    oak gradient and raise perlin persistence so the grain reads."""
    paths = []
    # v1: warm oak, spread grain ramp
    g = load_example("wooden_floor")
    set_gradient(g, "colorize_0", [
        (0.0, 0.30, 0.17, 0.07),   # dark grain line
        (0.4, 0.55, 0.36, 0.19),
        (0.7, 0.68, 0.47, 0.27),
        (1.0, 0.80, 0.58, 0.35),   # light oak
    ])
    set_param(g, "perlin_0", "persistence", 0.85)
    paths.append(save_variant(g, iter_label, "w01_oak_planks", 1))
    # v2: paler oak, even more grain contrast
    g = load_example("wooden_floor")
    set_gradient(g, "colorize_0", [
        (0.0, 0.34, 0.21, 0.10),
        (0.35, 0.60, 0.42, 0.24),
        (0.7, 0.74, 0.55, 0.34),
        (1.0, 0.85, 0.66, 0.44),
    ])
    set_param(g, "perlin_0", "persistence", 0.9)
    set_param(g, "perlin_0", "scale_y", 24)
    paths.append(save_variant(g, iter_label, "w01_oak_planks", 2))
    return paths


def _grad(points):
    return {"interpolation": 1, "type": "Gradient",
            "points": [{"a": 1, "r": r, "g": g, "b": b, "pos": p}
                       for (p, r, g, b) in points]}


def _from_scratch_noise_material(perlin_params, albedo_points, *,
                                 metallic=0.0, roughness=0.5, normal_amount=0.3):
    """A minimal, valid noise->colorize->material graph:
    perlin -> colorize(albedo) -> Material.albedo, perlin -> normal_map ->
    Material.normal (so the normal isn't flat), with scalar metallic/roughness.
    Node skeletons match the shapes Godot's loader expects (verified vs
    rusted_metal / wooden_floor)."""
    nodes = [
        {"name": "perlin_0", "type": "perlin",
         "node_position": {"x": 0, "y": 0}, "parameters": dict(perlin_params)},
        {"name": "colorize_0", "type": "colorize",
         "node_position": {"x": 300, "y": -60},
         "parameters": {"gradient": _grad(albedo_points)}},
        # normal_map is a COMPOUND node: its real params are param0 (buffer
        # size 2^n), param1 (STRENGTH, default 1 — this is what drives relief),
        # param2, param4. Earlier stray keys (amount/size/param3) were ignored,
        # and param1=0.2 rendered a near-flat normal. Map relief -> param1.
        {"name": "normal_map_0", "type": "normal_map",
         "node_position": {"x": 300, "y": 160},
         "parameters": {"param0": 10, "param1": normal_amount,
                        "param2": 0, "param4": 1}},
        {"name": "Material", "type": "material",
         "node_position": {"x": 620, "y": 40},
         "export_paths": {},
         "parameters": {
             "albedo_color": {"a": 1, "r": 1, "g": 1, "b": 1, "type": "Color"},
             "ao": 1, "depth_scale": 1, "emission_energy": 1,
             "metallic": metallic, "normal": 1, "roughness": roughness,
             "size": 11, "sss": 0}},
    ]
    connections = [
        {"from": "perlin_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "normal_map_0", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "normal_map_0", "from_port": 0, "to": "Material", "to_port": 4},
    ]
    return {"connections": connections, "nodes": nodes}


def rewire(graph: dict, to_node: str, to_port: int, from_node: str,
           from_port: int) -> None:
    """Repoint the connection feeding (to_node, to_port) to a new source."""
    for c in graph["connections"]:
        if c["to"] == to_node and c["to_port"] == to_port:
            c["from"] = from_node
            c["from_port"] = from_port
            return
    graph["connections"].append(
        {"from": from_node, "from_port": from_port,
         "to": to_node, "to_port": to_port})


def build_s02_gray_granite(iter_label: str) -> list[str]:
    """Polished gray granite = FINE multi-tone mineral flecks, low roughness,
    non-metallic, subtle relief.

    Root-cause fix (iter1 was foggy): iter1 cloned rock but only shrank the
    perlin, leaving rock's albedo voronoi at scale 4 (four giant blobs) blended
    with smooth fbm = low-frequency gray fog, no flecks. rock's albedo path is
    voronoi_0 -> blend_0 -> colorize_0. Granite's signature is a peppery spread
    of light/dark mineral flecks, so the cell density has to be high.

    v1: keep rock's chain, raise the ALBEDO voronoi (voronoi_0) to a fine fleck
        scale and add fine perlin grain; multi-tone gray ramp; low roughness.
        Leave the NORMAL voronoi (voronoi_1) coarse so relief stays subtle.
    v2: crisper flecks -- feed the albedo colorize directly from voronoi_0's
        per-cell random output (port 2 = rand3 per cell), bypassing the smooth
        blend, so each fine cell is a flat random gray.
    """
    paths = []

    # v1: fine-voronoi rock clone (safe: only param + gradient edits)
    g = load_example("rock")
    set_param(g, "voronoi_0", "scale_x", 40)   # albedo cell density: fine flecks
    set_param(g, "voronoi_0", "scale_y", 40)
    set_param(g, "voronoi_0", "randomness", 1)
    set_param(g, "perlin_0", "scale_x", 48)     # fine grain in the blend/rough
    set_param(g, "perlin_0", "scale_y", 48)
    set_param(g, "perlin_0", "iterations", 6)
    set_gradient(g, "colorize_0", [             # multi-tone gray fleck spread
        (0.0, 0.22, 0.22, 0.24),   # dark biotite/mica flecks
        (0.35, 0.46, 0.46, 0.48),  # mid feldspar gray
        (0.60, 0.66, 0.65, 0.66),  # light quartz
        (0.80, 0.52, 0.51, 0.50),  # warm feldspar
        (1.0, 0.34, 0.34, 0.36)])  # back to dark
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])   # non-metal
    set_gradient(g, "colorize_2",                                     # polished
                 [(0.0, 0.14, 0.14, 0.14), (1.0, 0.30, 0.30, 0.30)])
    # normal chain: rock's voronoi_1 -> warp_0 -> normal_map_0 is a directly-fed
    # analytic generator, so default param4=1 (buffered edge_detect) renders
    # flat. param4=0 edge-detects the raw warped voronoi -> real polished-stone
    # micro-relief. Strength kept low (subtle, not craggy) for a polished slab.
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.3)
    paths.append(save_variant(g, iter_label, "s02_gray_granite", 1))

    # v2: crisp per-cell random flecks -- albedo colorize fed from voronoi port 2
    g = load_example("rock")
    set_param(g, "voronoi_0", "scale_x", 44)
    set_param(g, "voronoi_0", "scale_y", 44)
    set_param(g, "voronoi_0", "randomness", 1)
    rewire(g, "colorize_0", 0, "voronoi_0", 2)  # random per-cell rgb -> albedo
    set_gradient(g, "colorize_0", [
        (0.0, 0.20, 0.20, 0.22),
        (0.40, 0.44, 0.44, 0.45),
        (0.70, 0.64, 0.63, 0.63),
        (1.0, 0.30, 0.30, 0.31)])
    set_gradient(g, "colorize_1", [(0.0, 0, 0, 0), (1.0, 0, 0, 0)])
    set_gradient(g, "colorize_2",
                 [(0.0, 0.14, 0.14, 0.14), (1.0, 0.28, 0.28, 0.28)])
    set_param(g, "normal_map_0", "param4", 0)
    set_param(g, "normal_map_0", "param1", 0.35)
    paths.append(save_variant(g, iter_label, "s02_gray_granite", 2))
    return paths


def build_o01_mossy_forest_floor(iter_label: str) -> list[str]:
    """CLONE dry_earth (working normal = crack/ground relief); recolor its earth
    albedo ramp (colorize_0) to dark soil -> green moss so the cracked ground
    reads as a mossy forest floor."""
    paths = []
    g = load_example("dry_earth")
    set_gradient(g, "colorize_0", [
        (0.25, 0.34, 0.44, 0.16),   # moss green (plate tops)
        (0.65, 0.14, 0.10, 0.05)])  # dark soil (crack floors)
    paths.append(save_variant(g, iter_label, "o01_mossy_forest_floor", 1))
    g = load_example("dry_earth")
    set_gradient(g, "colorize_0", [
        (0.25, 0.28, 0.40, 0.14), (0.55, 0.22, 0.28, 0.11),
        (0.7, 0.13, 0.09, 0.05)])
    paths.append(save_variant(g, iter_label, "o01_mossy_forest_floor", 2))
    return paths


def drop_conn(graph: dict, to_node: str, to_port: int) -> None:
    """Remove the connection feeding (to_node, to_port), if any."""
    graph["connections"] = [
        c for c in graph["connections"]
        if not (c["to"] == to_node and c["to_port"] == to_port)]


def build_m02_brushed_aluminum(iter_label: str) -> list[str]:
    """Brushed aluminum = neutral light-gray metal + fine PARALLEL directional
    brush streaks with real (shallow) normal relief.

    iter1 miss cloned rock and stretched its perlin, but rock's normal chain is
    isotropic, so the streaks were soft and the normal rendered flat. Structural
    insight: brushed metal is directional-streak-with-relief, which is exactly
    what WOOD GRAIN is. wood's perlin_2 (scale_x 32, scale_y 4) is a directional
    generator already feeding a WORKING normal chain (blend_0 -> normal_map_0),
    plus roughness/metallic/albedo. So clone wood and:
      - straighten the grain: feed blend_0's second input from the straight
        perlin_2 instead of the warped warp_1, killing wood's knotty waviness so
        the streaks run parallel like a brushed finish;
      - finer/longer streaks (raise scale_x, drop scale_y);
      - neutralize albedo to aluminum gray (no wood tint);
      - force uniform full metallic (drop the grain-driven metallic map so the
        Material's metallic=1 scalar applies);
      - map roughness to a low brushed range with streak-driven anisotropy;
      - soften the normal to shallow brush scratches (param1 0.99 -> ~0.35).
    """
    paths = []

    def brushed(scale_x, scale_y, alb_lo, alb_hi, rough_lo, rough_hi, relief):
        g = load_example("wood")
        rewire(g, "blend_0", 1, "perlin_2", 0)   # straighten: no knot warp
        set_param(g, "perlin_2", "scale_x", scale_x)
        set_param(g, "perlin_2", "scale_y", scale_y)
        set_param(g, "perlin_2", "iterations", 8)
        set_gradient(g, "colorize_2", [          # albedo: neutral aluminum gray
            (0.0, *(alb_lo,) * 3), (0.5, *((alb_lo + alb_hi) / 2,) * 3),
            (1.0, *(alb_hi,) * 3)])
        set_gradient(g, "colorize_0", [          # roughness: low, brushed streaks
            (0.0, *(rough_lo,) * 3), (1.0, *(rough_hi,) * 3)])
        drop_conn(g, "Material", 1)              # uniform metallic=1 (scalar)
        # normal chain: blend_0 was straightened to take the raw perlin_2
        # generator directly (no warp), so it's a directly-fed analytic input
        # -> default param4=1 (buffered edge_detect) renders flat, same as the
        # denim/granite blocker. param4=0 edge-detects the raw streaks -> real
        # brush-scratch relief.
        set_param(g, "normal_map_0", "param4", 0)
        set_param(g, "normal_map_0", "param1", relief)  # shallow scratches
        return g

    # v1: fine parallel streaks, light aluminum, subtle relief
    g = brushed(32, 3, 0.60, 0.82, 0.24, 0.44, 0.35)
    paths.append(save_variant(g, iter_label, "m02_brushed_aluminum", 1))
    # v2: denser/finer streaks, slightly darker, a touch more relief
    g = brushed(32, 2, 0.56, 0.78, 0.20, 0.40, 0.45)
    set_param(g, "perlin_2", "scale_x", 40)      # finer lines (cosmetic warning)
    paths.append(save_variant(g, iter_label, "m02_brushed_aluminum", 2))
    return paths


def build_man01_metal_grating(iter_label: str) -> list[str]:
    """Hexagonal metal grating = regular hex cells + metallic + raised-edge /
    recessed-hole relief. CLONE beehive (hex generator with a working normal
    chain): beehive_2:0 is a hex distance field (high = cell face, low = edge),
    colorize_5 = albedo, colorize_4 = roughness, uniform_greyscale.color feeds
    metallic, normal_map gives the hex relief. Recolor to gray metal, force
    metallic, keep the regular hex relief."""
    paths = []
    g = load_example("beehive")
    set_param(g, "uniform_greyscale", "color", 1.0)          # fully metallic
    set_gradient(g, "colorize_5", [                           # albedo: gray metal
        (0.0, 0.20, 0.20, 0.22),   # recessed edges/holes (dark)
        (0.88, 0.58, 0.58, 0.60)]) # raised cell faces (lighter metal)
    set_gradient(g, "colorize_4", [                           # roughness: metal
        (0.30, 0.30, 0.30, 0.30), (0.89, 0.48, 0.48, 0.48)])
    paths.append(save_variant(g, iter_label, "man01_metal_grating", 1))
    g = load_example("beehive")
    set_param(g, "beehive_2", "sx", 16); set_param(g, "beehive_2", "sy", 16)
    set_param(g, "uniform_greyscale", "color", 1.0)
    set_gradient(g, "colorize_5", [
        (0.0, 0.16, 0.16, 0.18), (0.88, 0.52, 0.52, 0.55)])
    set_gradient(g, "colorize_4", [
        (0.30, 0.26, 0.26, 0.26), (0.89, 0.44, 0.44, 0.44)])
    paths.append(save_variant(g, iter_label, "man01_metal_grating", 2))
    return paths


def build_man02_ceramic_hex_tiles(iter_label: str) -> list[str]:
    """White ceramic hexagon tiles = regular hex faces (white, glazed/low-rough)
    + recessed darker/rougher grout. CLONE beehive; non-metallic; recolor faces
    white with dark grout; roughness LOW on faces (high pattern value) and HIGH
    in grout (low value); keep the hex relief so grout reads recessed."""
    # The blend path mixes the hex structure (beehive:0) with a per-cell RANDOM
    # tone (beehive:1). That random is right for a metal panel (man01) but wrong
    # for uniform white ceramic tiles, and the default polarity put white in the
    # grout. Fix: drive albedo + roughness straight off the clean hex field
    # (beehive_2:0) so faces are uniform, and set faces white / grout dark. The
    # normal still reads from blend for relief (recessed grout).
    paths = []
    for n, (sx, sy) in enumerate([(20, 12), (14, 14)], start=1):
        g = load_example("beehive")
        set_param(g, "beehive_2", "sx", sx); set_param(g, "beehive_2", "sy", sy)
        set_param(g, "uniform_greyscale", "color", 0.0)      # non-metallic
        rewire(g, "colorize_5", 0, "beehive_2", 0)           # albedo <- clean hex
        rewire(g, "colorize_4", 0, "beehive_2", 0)           # roughness <- clean hex
        # Low white threshold so each hexagon is mostly white tile with only a
        # THIN dark grout line (beehive:0 peaks at cell center; grout is the
        # narrow low-value band at the edges).
        set_gradient(g, "colorize_5", [                      # face high, grout low
            (0.10, 0.26, 0.25, 0.23),   # grout (dark), thin
            (0.20, 0.92, 0.92, 0.90),   # tile -> white fast
            (1.0, 0.97, 0.97, 0.95)])   # tile face (white)
        set_gradient(g, "colorize_4", [                      # roughness inverted
            (0.10, 0.80, 0.80, 0.80),   # grout: rough
            (0.20, 0.14, 0.14, 0.14),   # face: glazed
            (1.0, 0.10, 0.10, 0.10)])
        paths.append(save_variant(g, iter_label, "man02_ceramic_hex_tiles", n))
    return paths


def retype(graph: dict, node_name: str, new_type: str, params: dict) -> None:
    """Swap a node's type and replace its parameters. Connections that
    reference it keep working as long as the new type's output port 0 is
    compatible with what the old one fed."""
    nd = node(graph, node_name)
    nd["type"] = new_type
    nd["parameters"] = dict(params)


def build_f01_woven_denim(iter_label: str) -> list[str]:
    """Blue denim = diagonal twill weave in the normal + indigo base + matte
    cloth. No bundled example uses the weave nodes, so GRAFT diagonal_weave into
    crocodile_skin's generator->colorize->normal_map chain: swap voronoi_0 for
    diagonal_weave so the woven diagonal pattern drives albedo, the normal, and
    roughness. Recolor to indigo, matte, non-metallic (uniform_0 = black metal).

    THE FIX (flat-normal blocker, resolved): normal_map is a compound node
    input -> [buffer] -> switch(param4) -> edge_detect(param1). With the default
    param4=1 the edge_detect runs on a pre-rendered BUFFER of the input, which
    comes back FLAT for a directly-fed analytic generator (this is why every
    crocodile/wood-donor normal rendered flat). Setting **param4=0** routes the
    raw analytic input straight into edge_detect, so the weave's real gradients
    produce the twill normal. param1 tunes strength. This same param4=0 switch
    can give real normals to any analytic-generator graph (granite, aluminum...)."""
    paths = []
    for n, (size, lo, hi, strength) in enumerate(
            [(22, (0.10, 0.13, 0.30), (0.26, 0.34, 0.55), 0.25),
             (18, (0.08, 0.11, 0.26), (0.30, 0.38, 0.60), 0.3)], start=1):
        g = load_example("crocodile_skin")
        retype(g, "voronoi_0", "diagonal_weave", {"size": size})
        set_gradient(g, "colorize_1", [(0.0, *lo), (1.0, *hi)])   # indigo threads
        set_gradient(g, "colorize_3",                             # matte, high
                     [(0.0, 0.80, 0.80, 0.80), (1.0, 0.93, 0.93, 0.93)])
        set_gradient(g, "colorize_0", [(0.0, 0, 0, 0), (1.0, 1, 1, 1)])  # linear height
        node(g, "normal_map_0")["parameters"] = {
            "param0": 11, "param1": strength, "param2": 0, "param4": 0}  # raw, not buffered
        paths.append(save_variant(g, iter_label, "f01_woven_denim", n))
    return paths


def add_node(graph: dict, name: str, ntype: str, params: dict) -> None:
    graph["nodes"].append({"name": name, "type": ntype,
                           "node_position": {"x": 0, "y": 0},
                           "parameters": dict(params)})


def build_combo01_rusted_painted_steel(iter_label: str) -> list[str]:
    """Rusted painted steel, paint peeling to bare metal. CLONE rusted_metal
    (rust albedo = blend_0:0, rust roughness = blend_1:0) and composite a flat
    paint coat OVER the rust through an irregular peel mask:
      - peel mask: a perlin thresholded by a colorize (hard-ish irregular edge);
      - paint: a flat color + flat low roughness (a colorize with both stops the
        same, fed by the mask perlin so it's a valid constant source);
      - blend paint over rust for both albedo and roughness, opacity = mask.
    Where the mask is high, paint shows (smooth); where low, rust/bare metal
    shows (rough) -> roughness contrast + irregular peel edges."""
    paths = []
    palette = [((0.18, 0.42, 0.40), (0.20, 0.46, 0.44)),   # faded teal-green
               ((0.42, 0.16, 0.14), (0.46, 0.18, 0.16))]   # faded oxide red
    for n, (plo, phi) in enumerate(palette, start=1):
        g = load_example("rusted_metal")
        add_node(g, "perlin_pm", "perlin",
                 {"scale_x": 6, "scale_y": 6, "iterations": 5})
        add_node(g, "colorize_pm", "colorize",
                 {"gradient": _grad([(0.42, 0, 0, 0), (0.52, 1, 1, 1)])})
        add_node(g, "paint_alb", "colorize",
                 {"gradient": _grad([(0.0, *plo), (1.0, *phi)])})
        add_node(g, "paint_rgh", "colorize",
                 {"gradient": _grad([(0.0, 0.28, 0.28, 0.28),
                                     (1.0, 0.30, 0.30, 0.30)])})
        add_node(g, "blend_alb", "blend", {"blend_type": 0, "amount": 1})
        add_node(g, "blend_rgh", "blend", {"blend_type": 0, "amount": 1})
        g["connections"] += [
            {"from": "perlin_pm", "from_port": 0, "to": "colorize_pm", "to_port": 0},
            {"from": "perlin_pm", "from_port": 0, "to": "paint_alb", "to_port": 0},
            {"from": "perlin_pm", "from_port": 0, "to": "paint_rgh", "to_port": 0},
            {"from": "blend_0", "from_port": 0, "to": "blend_alb", "to_port": 0},
            {"from": "paint_alb", "from_port": 0, "to": "blend_alb", "to_port": 1},
            {"from": "colorize_pm", "from_port": 0, "to": "blend_alb", "to_port": 2},
            {"from": "blend_1", "from_port": 0, "to": "blend_rgh", "to_port": 0},
            {"from": "paint_rgh", "from_port": 0, "to": "blend_rgh", "to_port": 1},
            {"from": "colorize_pm", "from_port": 0, "to": "blend_rgh", "to_port": 2},
        ]
        rewire(g, "Material", 0, "blend_alb", 0)   # albedo <- paint-over-rust
        rewire(g, "Material", 2, "blend_rgh", 0)   # roughness <- paint-over-rust
        paths.append(save_variant(g, iter_label, "combo01_rusted_painted_steel", n))
    return paths


BUILDERS = {
    "f02_brown_leather": build_f02_brown_leather,
    "f01_woven_denim": build_f01_woven_denim,
    "combo01_rusted_painted_steel": build_combo01_rusted_painted_steel,
    "man01_metal_grating": build_man01_metal_grating,
    "man02_ceramic_hex_tiles": build_man02_ceramic_hex_tiles,
    "w02_weathered_barn_wood": build_w02_barn_wood,
    "m01_weathered_copper": build_m01_weathered_copper,
    "s03_cracked_concrete": build_s03_cracked_concrete,
    "w01_oak_planks": build_w01_oak_planks,
    "s02_gray_granite": build_s02_gray_granite,
    "o01_mossy_forest_floor": build_o01_mossy_forest_floor,
    "m02_brushed_aluminum": build_m02_brushed_aluminum,
}


def main() -> int:
    iter_label = sys.argv[1] if len(sys.argv) > 1 else "iter1"
    targets = sys.argv[2:] or list(BUILDERS.keys())
    for case in targets:
        paths = BUILDERS[case](iter_label)
        print(f"{case}: {len(paths)} variants")
        for p in paths:
            print("  ", os.path.relpath(p, _ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
