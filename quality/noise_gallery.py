"""Noise vocabulary gallery: single-node graphs that show the raw CHARACTER of
each base-noise generator, side by side, so an author can pick a structure
instead of defaulting to the same two.

Why this exists: a histogram of the cookbook builders (2026-09-01) found the
"everything looks similar" problem is real and measurable -- 38 materials, but
69% clone just three donors (crocodile_skin x12, rock x7, wood x5, all
voronoi-cellular or wood-grain), and the only base noise ever ADDED by hand is
perlin (x9) and voronoi (x1). Zero use of fbm, anisotropic, shard, wavelet, or
truchet, though the catalog carries 47 noise/pattern nodes. This gallery is the
reference that widens that vocabulary.

Shape (per the advisor steer): this is a reference GALLERY, not a debug swatch.
Noise has no assertable known-answer beyond "renders non-empty," so it does NOT
go in debug_swatches.py's pixel-checked registry -- that would be a fake test.
It reuses the same single-node-into-a-grayscale-ramp plumbing, produces tracked
thumbnails, and is documented in AUTHORING.md's "Noise vocabulary" section. No
test surface.

The figure that answers the question is the fbm row: ONE node, all 8 `noise`
bases, scale and iterations pinned, only the basis varying. It is
self-validating -- if some Cellular bases read as near-duplicates, that is an
honest finding to report, not a failure.

Run:   python quality/noise_gallery.py
Then:  python quality/render_cookbook.py noise-gallery
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import _grad, save_variant

_LABEL = "noise-gallery"


def _material(albedo=(0.8, 0.8, 0.8), roughness=0.6):
    """Minimal Material node skeleton (same one debug_swatches.py uses)."""
    r, g, b = albedo
    return {
        "name": "Material", "type": "material",
        "node_position": {"x": 640, "y": 40},
        "export_paths": {},
        "parameters": {
            "albedo_color": {"a": 1, "r": r, "g": g, "b": b, "type": "Color"},
            "ao": 1, "depth_scale": 1, "emission_energy": 1,
            "metallic": 0.0, "normal": 1, "roughness": roughness,
            "size": 11, "sss": 0},
    }


# black->white ramp so the raw scalar field reads as grayscale
_GREY = {"name": "grey", "type": "colorize",
         "node_position": {"x": 320, "y": 0},
         "parameters": {"gradient": _grad([(0.0, 0, 0, 0), (1.0, 1, 1, 1)])}}


def _field(gen: dict, case: str) -> str:
    """Wire ONE generator's scalar output (port 0) through the grey ramp into
    the Material albedo, and save it. Apples-to-apples: every generator here
    exposes its primary field on output port 0."""
    nodes = [gen, dict(_GREY)]
    conns = [
        {"from": gen["name"], "from_port": 0, "to": "grey", "to_port": 0},
        {"from": "grey", "from_port": 0, "to": "Material", "to_port": 0},
    ]
    graph = {"connections": conns, "nodes": nodes + [_material()]}
    return save_variant(graph, _LABEL, case, 1)


# ---- Row 1: fbm, all 8 noise bases, everything else pinned -----------------
# The controlled sweep. noise enum: 0 Value, 1 Perlin, 2..7 Cellular 1..6.
# scale 4/4, iterations 3, persistence 0.5 held constant so ONLY the basis
# changes.
_FBM_BASES = [
    (0, "value"), (1, "perlin"),
    (2, "cellular1"), (3, "cellular2"), (4, "cellular3"),
    (5, "cellular4"), (6, "cellular5"), (7, "cellular6"),
]


def build_fbm_row() -> list:
    out = []
    for idx, tag in _FBM_BASES:
        gen = {"name": "fbm_0", "type": "fbm",
               "node_position": {"x": 0, "y": 0},
               "parameters": {"noise": idx, "scale_x": 4, "scale_y": 4,
                              "folds": 0, "iterations": 3, "persistence": 0.5}}
        out.append(_field(gen, f"fbm_{idx}_{tag}"))
    return out


# ---- Row 2: cross-family characters fbm cannot produce ---------------------

def build_crossfamily_row() -> list:
    cases = [
        # directional stretch -> brushed / fibrous grain
        ({"name": "aniso_0", "type": "noise_anisotropic",
          "node_position": {"x": 0, "y": 0},
          "parameters": {"scale_x": 4, "scale_y": 48, "smoothness": 1,
                         "interpolation": 1}}, "anisotropic_directional"),
        # angular shards -> cracked / crystalline
        ({"name": "shard_0", "type": "shard_fbm",
          "node_position": {"x": 0, "y": 0},
          "parameters": {"sharp": 0.7, "sx": 7, "sy": 7, "folds": 0,
                         "iter": 4, "per": 0.5, "off": 0}}, "shard_angular"),
        # structured tile randomness, Line -> woven / circuit / maze
        ({"name": "truchet_l", "type": "truchet",
          "node_position": {"x": 0, "y": 0},
          "parameters": {"shape": 0, "size": 4}}, "truchet_line"),
        # structured tile randomness, Circle -> pipes / interlock
        ({"name": "truchet_c", "type": "truchet",
          "node_position": {"x": 0, "y": 0},
          "parameters": {"shape": 1, "size": 4}}, "truchet_circle"),
        # triangular cells -> faceted / gem
        ({"name": "vtri_0", "type": "voronoi_triangle",
          "node_position": {"x": 0, "y": 0},
          "parameters": {"scale_x": 4, "scale_y": 4, "stretch_x": 1,
                         "stretch_y": 1, "randomness": 0.85}}, "voronoi_triangle"),
        # banded wavelet -> ripple / interference
        ({"name": "wav_0", "type": "wavelet_noise",
          "node_position": {"x": 0, "y": 0},
          "parameters": {"type": 4, "scale_x": 4, "scale_y": 4, "iterations": 3,
                         "persistence": 0.5, "frequency": 1, "offset": 0}},
         "wavelet_banded"),
    ]
    return [_field(gen, case) for gen, case in cases]


if __name__ == "__main__":
    paths = build_fbm_row() + build_crossfamily_row()
    for p in paths:
        print("wrote", p)
    print(f"\n{len(paths)} noise-gallery graphs authored.")
    print("Render: python quality/render_cookbook.py noise-gallery")
