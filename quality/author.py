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


def build_s02_gray_granite(iter_label: str) -> list[str]:
    """From scratch: fine multi-octave perlin speckle -> multi-tone gray ramp,
    low roughness (polished), non-metallic, subtle normal."""
    paths = []
    # v1: neutral gray granite, fine speckle
    g = _from_scratch_noise_material(
        {"iterations": 10, "persistence": 0.6, "scale_x": 32, "scale_y": 32},
        [(0.0, 0.28, 0.28, 0.30), (0.4, 0.46, 0.46, 0.48),
         (0.7, 0.60, 0.60, 0.62), (1.0, 0.74, 0.74, 0.75)],
        metallic=0.0, roughness=0.28, normal_amount=0.6)
    paths.append(save_variant(g, iter_label, "s02_gray_granite", 1))
    # v2: warmer speckle (feldspar tint), slightly coarser
    g = _from_scratch_noise_material(
        {"iterations": 9, "persistence": 0.62, "scale_x": 24, "scale_y": 24},
        [(0.0, 0.26, 0.25, 0.26), (0.35, 0.45, 0.43, 0.42),
         (0.7, 0.62, 0.59, 0.57), (1.0, 0.76, 0.74, 0.72)],
        metallic=0.0, roughness=0.32, normal_amount=0.7)
    paths.append(save_variant(g, iter_label, "s02_gray_granite", 2))
    return paths


def build_o01_mossy_forest_floor(iter_label: str) -> list[str]:
    """From scratch: clumpy perlin -> ramp from dark soil (low) to moss green
    (high), strong normal for bumpy relief, high roughness (matte)."""
    paths = []
    g = _from_scratch_noise_material(
        {"iterations": 8, "persistence": 0.72, "scale_x": 8, "scale_y": 8},
        [(0.0, 0.13, 0.09, 0.05),   # dark soil
         (0.4, 0.22, 0.20, 0.10),   # earthy
         (0.65, 0.20, 0.36, 0.12),  # moss
         (1.0, 0.36, 0.55, 0.20)],  # bright moss
        metallic=0.0, roughness=0.9, normal_amount=2.5)
    paths.append(save_variant(g, iter_label, "o01_mossy_forest_floor", 1))
    g = _from_scratch_noise_material(
        {"iterations": 9, "persistence": 0.75, "scale_x": 6, "scale_y": 6},
        [(0.0, 0.15, 0.11, 0.06), (0.45, 0.18, 0.26, 0.10),
         (0.7, 0.24, 0.42, 0.15), (1.0, 0.42, 0.60, 0.24)],
        metallic=0.0, roughness=0.92, normal_amount=3.0)
    paths.append(save_variant(g, iter_label, "o01_mossy_forest_floor", 2))
    return paths


def build_m02_brushed_aluminum(iter_label: str) -> list[str]:
    """From scratch: perlin stretched hard along one axis (scale_y>>scale_x) for
    directional brush streaks -> narrow neutral-gray ramp, metallic, med-low
    roughness, faint normal."""
    paths = []
    # NOTE: an extreme stretch (scale_y ~96) degenerates the noise to near-
    # constant, so its normal_map renders FLAT (broken map). Keep a moderate
    # stretch so streaks stay directional but the normal retains relief.
    g = _from_scratch_noise_material(
        {"iterations": 8, "persistence": 0.55, "scale_x": 3, "scale_y": 20},
        [(0.0, 0.60, 0.60, 0.61), (1.0, 0.82, 0.82, 0.83)],
        metallic=1.0, roughness=0.35, normal_amount=1.1)
    paths.append(save_variant(g, iter_label, "m02_brushed_aluminum", 1))
    g = _from_scratch_noise_material(
        {"iterations": 8, "persistence": 0.5, "scale_x": 4, "scale_y": 28},
        [(0.0, 0.64, 0.64, 0.66), (1.0, 0.86, 0.86, 0.87)],
        metallic=1.0, roughness=0.3, normal_amount=1.0)
    paths.append(save_variant(g, iter_label, "m02_brushed_aluminum", 2))
    return paths


BUILDERS = {
    "f02_brown_leather": build_f02_brown_leather,
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
