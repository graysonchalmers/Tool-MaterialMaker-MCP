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
python -m quality.debug_swatches                 # write all swatch .ptex files
python -m quality.render_cookbook debug-swatches # validate + render them
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

### The blend family (`blend_*`)

The `blend` node is the workhorse of every masked two-layer material, and its
port/opacity semantics caused real, repeated debugging (the sf03 circuit-board
trace-bleed-through and the pm03 chipped-paint polarity flip). These two swatches
make the semantics unmistakable. From `blend.mmg`, the Normal-mode output is:

```
out = opacity * s1 + (1 - opacity) * s2      opacity = amount * mask * s1.alpha
```

where **port 0 = `s1` (Foreground)**, **port 1 = `s2` (Background)**, **port 2 =
`a` (Mask)**. Both swatches set `blend_type=0` (Normal) explicitly — the `.mmg`
default is `13` (AddSub), which would give a different formula and wrong colors.

| Swatch | Isolates | Should look like |
|---|---|---|
| `blend_mask_polarity` | which port shows where the mask is 0 vs 1 (`amount=1`, hard mask) | A hard vertical split: **LEFT half BLUE**, **RIGHT half RED**. Foreground RED is on port 0 and shows where the **mask is 1** (right); background BLUE is on port 1 and shows where the **mask is 0** (left). Red on the LEFT = the ports are swapped in your head. This is the pm03 lesson: put the **majority** layer on port 1 and mask in the minority. |
| `blend_opacity_ramp` | `opacity = amount × mask` (`amount=0.5`, ramp mask 0→1) | A smooth crossfade: **LEFT pure BLUE** (mask 0 → opacity 0), fading to a **PURPLE right edge that never reaches pure red** (mask 1 × amount 0.5 → opacity 0.5, so the foreground caps at half-strength). A *mid* mask gives a *partial* blend, not a switch — that partiality is exactly the sf03 bug (a 0.65-valued mask fed as opacity left the top layer 65% opaque and the layer below bled through the other 35%). |

Both are albedo-only (no relief), so no 3D preview is needed — eyeball the albedo.

### The relief family (`relief_*`)

All five feed a height source through the same `normal_map(param4=0)` chain onto
a flat gray material, so the relief is the whole story. **Judge in 3D** — each
shape should stand **OUT**. **Flat** = the `param4` trap (a buffered
`edge_detect` returns flat for a directly-fed analytic generator; `param4=0`
fixes it). **Inverted** = a green-channel / engine normal-convention flip. They
cover different stress cases:

| Swatch | Height source | Stresses |
|---|---|---|
| `relief_circle` | `shape` Circle | Smooth curves. The one swatch with a **strict dome-out** pixel check (apex neutral, R rises left→right across it — which distinguishes dome-out from flat and from dented-in). |
| `relief_polygon` | `shape` Polygon (triangle) | Straight edges and hard corners. |
| `relief_star` | `shape` Star | Concave inner corners the convex shapes lack. |
| `relief_rays` | `shape` Rays | Thin radial strokes — where a too-coarse normal buffer smears or drops detail. |
| `relief_glyph` | two `sixteen_segment` glyphs → transform → blend | **Text.** Spells `UP` (MM has no text node). The sharp-thin-stroke-with-gaps case; its automated check scans the full buffer because the strokes are too thin for a sparse grid. |

### The warp / distortion family (`warp`, `warp2`, `directional_warp`, `slope_blur`)

Distortion nodes are assertable because they DISPLACE a KNOWN reference field.
All four share one reference: `ref_grad`, a raw 0->1 horizontal ramp, hard-
thresholded by a `colorize` into `ref_mask` (a black-left / white-right split
at x=0.5). `ref_grad` doubles as the distortion node's displacement/control
input, so the shift direction and size are constant and predictable instead
of noise-driven.

| Swatch | Isolates | Should look like |
|---|---|---|
| `warp` | slope-driven displacement (mode=Slope) | The `ref_mask` split shifted RIGHT by `2*amount*eps` = 0.2. The vertical boundary sits at x=0.3 instead of x=0.5 — a pixel at x=0.45 (black in the undistorted reference) now reads WHITE. No shift = `d` (port 1) isn't wired to a real height map. |
| `warp2` | the simpler unit-slope warp | Same shift shape as `warp`, but by exactly `amount` = 0.3 (no `eps`). The boundary sits at x=0.2; x=0.35 flips from black to white. |
| `directional_warp` | a constant per-pixel shift along a fixed `angle` | With `anglemap`/`strengthmap` left unconnected (their MM defaults make the formula reduce to a constant `-0.5*strength` shift), `angle=0, strength=1.0` shifts the boundary LEFT by 0.5 (wrapping): x=0.45 flips from black to white. Proves you don't need to wire the optional map inputs to get a clean, deterministic displacement out of this node. |
| `slope_blur` | smearing along a height map's slope | **Not currently renderable here** — see the concern box below. If it ever renders: the hard x=0.5 boundary should read as an INTERMEDIATE grey ramp, not a hard step. |

**Concern: `slope_blur` does not render in this project's headless pipeline.**
Its compound graph is built entirely from `buffer`-type nodes (compute
shaders) sandwiching an edge-detect shader, with no unbuffered bypass. Those
`buffer` nodes fail to compile their compute shader under `--export-material`
("Cannot call method 'shader_compile_spirv_from_source' on a null value"),
producing an all-black image — confirmed even for a completely bare, unwired
`slope_blur` node, so it is not a wiring mistake in this swatch. The relief
family's `normal_map` also contains an internal `buffer` node and hits the
identical error every render, but survives because its `switch` node picks
the unbuffered branch at `param4=0`; `slope_blur` has no such escape hatch.
The builder still authors a valid `.ptex` (see
`tests/test_debug_swatches.py`'s `test_slope_blur_graph_validates_but_does_not_render_here`),
but it is intentionally left out of the live pixel-check table above until
this environment/engine limitation is resolved.

### 3D preview for a relief swatch

```
# after rendering (albedo + normal + orm all land in the swatch's outdir):
render_preview(
  albedo_path=".../relief_glyph_albedo.png",
  normal_path=".../relief_glyph_normal.png",
  orm_path=".../relief_glyph_orm.png",
  basename="relief_glyph_preview")
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
