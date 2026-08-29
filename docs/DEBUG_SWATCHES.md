# Debug diagnostic swatches

A small gallery of **minimal single-node graphs** that isolate ONE node
behavior so a wrong wiring is obvious on sight. Two jobs at once:

- **Visual smoke test** — render the gallery and eyeball it. If any swatch
  doesn't match its known-answer below, a node is miswired.
- **Learning aid** — each swatch is a worked "this is exactly what this node
  does" example, in the spirit of [NORTH_STAR.md](NORTH_STAR.md)'s
  round-trip learning loop.

Unlike the cookbook recipes (`quality/cookbook_*.py`), nothing here clones a
full material. Each swatch wires one generator straight into a Material, so
what you see IS that node's raw output.

## Run

```
python quality/debug_swatches.py                 # write all swatch .ptex files
python quality/render_cookbook.py debug-swatches # validate + render them
```

Outputs land in `quality/cookbook/debug-swatches/<swatch>/` (gitignored,
regenerable). For the relief swatch, also render a 3D preview to judge it (see
below) — a flat normal map alone can't tell dome-out from dented-in.

## The swatches and their known-answers

If a render disagrees with the "should look like" column, that's a caught bug.

| Swatch | Isolates | Should look like |
|---|---|---|
| `voronoi_port0_polarity` | voronoi output port 0, color-coded | Cell **centers RED**, seams **BLUE**. Port 0 is *low at centers, high at borders*. Blue centers / red seams = polarity flipped. This is the exact behavior that made the leather grain inside-out (`_dome_the_cells` fixes it by reversing the height ramp fed from this port). |
| `voronoi_port0_field` | voronoi port 0, raw grayscale | **Black centers**, bright seams — a smooth distance field, low at centers. Confirms the polarity above. |
| `voronoi_port1_field` | voronoi port 1, raw grayscale | A **different** distance metric: dark cells with **dark seams** (not bright like port 0). Distinct from port 0 — confusing the two is a documented trap. |
| `voronoi_port2_random` | voronoi port 2 (rgb) → albedo | **Flat, solid random color per cell**, no gradient inside a cell. This is `rand3`, the fleck/speckle source. If it looks like a smooth field, something is feeding the wrong port. |
| `uv_direction` | UV axes as R (U) and G (V) | A 2×2 grid (repeat=2). **+U points RIGHT** (R rises left→right), **+V points DOWN** (G rises top→bottom — Godot/MM texture convention, row 0 at top). Corners: top-left BLACK, top-right RED, bottom-left GREEN, bottom-right YELLOW. The hard color cross down the middle is the tiling seam. |
| `normal_relief_check` | `shape` dome → `normal_map` (param4=0) | **Judge in 3D.** The circle should **dome OUT** and catch light on the side facing the light. **Flat** = the `param4` trap (a buffered `edge_detect` returns flat for a directly-fed analytic generator; `param4=0` fixes it). **Dented IN** = a green-channel / engine normal-convention flip. |

### 3D preview for the relief swatch

```
# after rendering (albedo + normal + orm all land in the swatch's outdir):
render_preview(
  albedo_path=".../normal_relief_check_albedo.png",
  normal_path=".../normal_relief_check_normal.png",
  orm_path=".../normal_relief_check_orm.png",
  basename="normal_relief_check_preview")
```

## Phase 2 (planned, not built): automated regression assertions

Today these are a **visual** smoke test — a human reads the gallery. The
intended next step turns each known-answer row above into a **headless pixel
assertion** so a broken node change fails in CI without anyone looking:

- Sample known pixels and assert the relationship, e.g. for
  `voronoi_port0_polarity`, a cell-center pixel has `R > B` and a seam pixel has
  `B > R`; for `uv_direction`, the top-left pixel is near-black and the
  bottom-right is yellow (`R` high, `G` high, `B` low).
- Open design question for that phase: assert against a **live render** (truly
  exercises the Godot pipeline, but slow and Godot-dependent, so an
  `integration`-marked test) versus a **committed reference render** (fast, but
  only a snapshot test). Also: what reads the PNG pixels, since Pillow is in the
  venv but deliberately not a project dependency.

That phase is scoped separately; this file documents the visual gallery it will
build on.
