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


BUILDERS = {
    "f02_brown_leather": build_f02_brown_leather,
    "w02_weathered_barn_wood": build_w02_barn_wood,
    "m01_weathered_copper": build_m01_weathered_copper,
    "s03_cracked_concrete": build_s03_cracked_concrete,
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
