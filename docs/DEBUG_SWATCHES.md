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

## Phase 2 (built): automated regression assertions

The visual gallery above is also a **headless regression smoke test**. Each
known-answer row is encoded as a pixel check in `debug_swatches.py`'s
`PIXEL_CHECKS`, and `tests/test_debug_swatches.py` renders each swatch LIVE (at
size 128, `@pytest.mark.integration`) and asserts on the fresh pixels — so a
wiring or render regression fails without anyone eyeballing the gallery.

Design decisions that shaped it:

- **Live render, not a committed reference.** A snapshot of a stored PNG can't
  catch a wiring or render regression; only re-rendering can. So the checks are
  integration tests that launch Godot, like the rest of the suite.
- **Two assertion styles**, because voronoi cell positions are random (no fixed
  "cell center" pixel):
  - *Deterministic point-samples* where geometry is fixed — `uv_direction`'s
    four corners, `normal_relief_check`'s apex + the left→right R rise across the
    dome (which even distinguishes dome-out from flat or dented).
  - *Statistical invariants* where it's procedural — the polarity swatch has more
    red (centers) than blue (seams), so a flipped port-0 reverses it;
    `port2_random` is colorful with many distinct cell colors; port-0 and port-1
    fields are greyscale and measurably different from each other.
- **PNG reading is vendored** (`quality/pngread.py`, ~60 lines of stdlib `zlib`)
  rather than adding Pillow, keeping the project's dependency list clean.
- **Thresholds are calibrated against real size-128 renders**, with wide margins;
  the voronoi layout is deterministic (MM voronoi uses a fixed hash), so the
  statistical checks are stable run to run.

Run the automated layer:

```
python -m pytest tests/test_debug_swatches.py -q                 # reader + checks
python -m pytest tests/test_debug_swatches.py -q -m integration  # just the live checks
```

Dome-out vs dented-in on the relief swatch is asserted from the normal map's R
gradient, but the 3D `render_preview` above remains the clearest human read.
