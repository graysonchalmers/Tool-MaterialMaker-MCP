"""Debug diagnostic swatches: minimal single-node graphs that isolate ONE node
behavior so a wrong wiring is obvious on sight. A visual smoke test AND a
learning aid, separate from the frozen Phase 3 test set (test_set.json) and the
cookbook recipes (cookbook_*.py). Nothing here clones a full material; each
swatch wires one generator straight into a Material so what you see IS that
node's raw behavior.

Phase 1 (this file): the visual gallery. Each builder writes one v1.ptex to
quality/authored/debug-swatches/<swatch>/, rendered for eyeballing by
  python quality/render_cookbook.py debug-swatches
Each swatch's known-correct appearance is documented in docs/DEBUG_SWATCHES.md.
If a render doesn't match its legend, a node is miswired -- that's the whole
point (the inverted voronoi-port-0 grain that bit the leather cookbook would
have been obvious here on sight).

Phase 2 (deferred, Grayson's "both, phased" call): turn each legend line into a
headless pixel assertion (sample a cell center vs a border, assert the channel
ordering) so these run as a real automated regression smoke test. Not built yet
-- see docs/DEBUG_SWATCHES.md for the intended shape.

Run: python quality/debug_swatches.py
Then: python quality/render_cookbook.py debug-swatches
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author import _grad, save_variant

_LABEL = "debug-swatches"


def _material(albedo=(0.8, 0.8, 0.8), metallic=0.0, roughness=0.6):
    """The Material node skeleton Godot's loader expects (verified against
    author.py's _from_scratch_noise_material and the bundled examples). Input
    ports: albedo=0, metallic=1, roughness=2, normal=4. albedo_color is used
    only when the albedo input port is left unconnected."""
    r, g, b = albedo
    return {
        "name": "Material", "type": "material",
        "node_position": {"x": 640, "y": 40},
        "export_paths": {},
        "parameters": {
            "albedo_color": {"a": 1, "r": r, "g": g, "b": b, "type": "Color"},
            "ao": 1, "depth_scale": 1, "emission_energy": 1,
            "metallic": metallic, "normal": 1, "roughness": roughness,
            "size": 11, "sss": 0},
    }


def _graph(nodes, connections, **mat):
    return {"connections": connections, "nodes": nodes + [_material(**mat)]}


def _voronoi(scale=6):
    return {"name": "voronoi_0", "type": "voronoi",
            "node_position": {"x": 0, "y": 0},
            "parameters": {"scale_x": scale, "scale_y": scale, "randomness": 1}}


# ---- 1. voronoi port-0 polarity -------------------------------------------

def build_voronoi_port0_polarity() -> str:
    """Color-codes voronoi output port 0 so its polarity is unmistakable: cell
    CENTERS (low port-0 value) map to RED, cell BORDERS (high value) map to
    BLUE. This is the exact behavior that produced the inside-out leather grain
    (_dome_the_cells fixes it by reversing a height ramp fed from this port). If
    the swatch shows blue interiors / red seams, port-0 polarity is flipped."""
    nodes = [
        _voronoi(),
        {"name": "colorize_0", "type": "colorize",
         "node_position": {"x": 320, "y": 0},
         "parameters": {"gradient": _grad([
             (0.0, 1.0, 0.12, 0.12),    # low  = cell CENTERS -> RED
             (1.0, 0.12, 0.28, 1.0)])}},  # high = cell BORDERS -> BLUE
    ]
    conns = [
        {"from": "voronoi_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
    ]
    return save_variant(_graph(nodes, conns), _LABEL, "voronoi_port0_polarity", 1)


# ---- 2. voronoi port identity (0 / 1 / 2 side by side) --------------------

def _voronoi_port_field(case: str, port: int) -> str:
    nodes = [
        _voronoi(),
        {"name": "colorize_0", "type": "colorize",
         "node_position": {"x": 320, "y": 0},
         "parameters": {"gradient": _grad([(0.0, 0, 0, 0), (1.0, 1, 1, 1)])}},
    ]
    conns = [
        {"from": "voronoi_0", "from_port": port, "to": "colorize_0", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
    ]
    return save_variant(_graph(nodes, conns), _LABEL, case, 1)


def build_voronoi_port0_field() -> str:
    """Port 0 as a raw grayscale field: a smooth distance metric, dark at cell
    centers and bright toward borders. Pair with _polarity above and the port1
    / port2 swatches to see, at a glance, which output does what."""
    return _voronoi_port_field("voronoi_port0_field", 0)


def build_voronoi_port1_field() -> str:
    """Port 1 as a raw grayscale field: a second (different) distance metric.
    Distinct from port 0 -- confusing the two is a documented trap."""
    return _voronoi_port_field("voronoi_port1_field", 1)


def build_voronoi_port2_random() -> str:
    """Port 2 (rgb) fed straight to albedo: a FLAT random color per cell (rand3
    -- the fleck/speckle source). No gradient within a cell. If this swatch
    looks like a smooth field instead of flat-colored cells, something is
    feeding the wrong port."""
    nodes = [_voronoi()]
    conns = [{"from": "voronoi_0", "from_port": 2, "to": "Material", "to_port": 0}]
    return save_variant(_graph(nodes, conns), _LABEL, "voronoi_port2_random", 1)


# ---- 3. normal-map relief check (judge in 3D) -----------------------------

def build_normal_relief_check() -> str:
    """A known raised dome (a `shape` circle used as a heightmap) fed through
    normal_map with the param4=0 fix, on a flat gray material so all shading
    comes from the normal. JUDGE THIS IN 3D (render_preview): the circle should
    dome OUT and catch light. Flat = the param4 trap (buffered edge_detect
    returns flat for a directly-fed analytic generator). Dented IN = a
    green-channel / engine normal-convention flip.

    Albedo and roughness are wired to flat colorizes (both stops equal) fed off
    the same shape, purely so the renderer emits albedo + orm maps too -- without
    them render only produces normal.png and render_preview has nothing to
    composite. The flat gradients keep albedo/roughness uniform, so the 3D read
    is pure relief."""
    flat_grey = _grad([(0.0, 0.55, 0.55, 0.55), (1.0, 0.55, 0.55, 0.55)])
    flat_rough = _grad([(0.0, 0.5, 0.5, 0.5), (1.0, 0.5, 0.5, 0.5)])
    nodes = [
        {"name": "shape_0", "type": "shape",
         "node_position": {"x": 0, "y": 0},
         "parameters": {"shape": 0, "sides": 6, "radius": 0.5, "edge": 0.65}},
        {"name": "normal_map_0", "type": "normal_map",
         "node_position": {"x": 320, "y": 200},
         "parameters": {"param0": 11, "param1": 0.9, "param2": 0, "param4": 0}},
        {"name": "colorize_alb", "type": "colorize",
         "node_position": {"x": 320, "y": -80},
         "parameters": {"gradient": flat_grey}},
        {"name": "colorize_rgh", "type": "colorize",
         "node_position": {"x": 320, "y": 60},
         "parameters": {"gradient": flat_rough}},
    ]
    conns = [
        {"from": "shape_0", "from_port": 0, "to": "normal_map_0", "to_port": 0},
        {"from": "shape_0", "from_port": 0, "to": "colorize_alb", "to_port": 0},
        {"from": "shape_0", "from_port": 0, "to": "colorize_rgh", "to_port": 0},
        {"from": "colorize_alb", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "colorize_rgh", "from_port": 0, "to": "Material", "to_port": 2},
        {"from": "normal_map_0", "from_port": 0, "to": "Material", "to_port": 4},
    ]
    return save_variant(_graph(nodes, conns), _LABEL, "normal_relief_check", 1)


# ---- 4. UV direction / tiling ---------------------------------------------

def build_uv_direction() -> str:
    """A two-axis UV checker: R = the U axis, G = the V axis, combined into
    albedo. This swatch reveals Material Maker's actual UV convention (verified
    by rendering it): R rises left->right, so +U points RIGHT; G rises
    top->bottom, so +V points DOWN (standard texture-space, row 0 at top).
    Known corners therefore: top-left BLACK, top-right RED, bottom-left GREEN,
    bottom-right YELLOW. repeat=2 makes the tiling seams visible as the hard
    color cross down the middle. If U/V read swapped or a direction reverses,
    a transform/rotate upstream is wrong."""
    grad_bw = _grad([(0.0, 0, 0, 0), (1.0, 1, 1, 1)])
    nodes = [
        {"name": "grad_u", "type": "gradient",
         "node_position": {"x": 0, "y": -80},
         "parameters": {"repeat": 2, "rotate": 0, "mirror": False,
                        "gradient": grad_bw}},
        {"name": "grad_v", "type": "gradient",
         "node_position": {"x": 0, "y": 120},
         "parameters": {"repeat": 2, "rotate": 90, "mirror": False,
                        "gradient": grad_bw}},
        {"name": "combine_0", "type": "combine",
         "node_position": {"x": 340, "y": 0}, "parameters": {}},
    ]
    conns = [
        {"from": "grad_u", "from_port": 0, "to": "combine_0", "to_port": 0},  # R <- U
        {"from": "grad_v", "from_port": 0, "to": "combine_0", "to_port": 1},  # G <- V
        {"from": "combine_0", "from_port": 0, "to": "Material", "to_port": 0},
    ]
    return save_variant(_graph(nodes, conns), _LABEL, "uv_direction", 1)


BUILDERS = {
    "voronoi_port0_polarity": build_voronoi_port0_polarity,
    "voronoi_port0_field": build_voronoi_port0_field,
    "voronoi_port1_field": build_voronoi_port1_field,
    "voronoi_port2_random": build_voronoi_port2_random,
    "normal_relief_check": build_normal_relief_check,
    "uv_direction": build_uv_direction,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    for case in targets:
        path = BUILDERS[case]()
        print(f"{case}: {os.path.relpath(path, os.path.dirname(os.path.dirname(__file__)))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
