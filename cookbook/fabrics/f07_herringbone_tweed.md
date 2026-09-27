# f07_herringbone_tweed - Herringbone tweed

_Category: fabrics. Open the graph: `cookbook/fabrics/f07_herringbone_tweed.ptex`._

A warm woven wool fabric with the classic herringbone chevron pattern:
diagonal ribbons that reverse direction band to band. This is the material
the wool-knit search found along the way, not a knit.

## Recipe

Retype the generator to `weave2` with `stitch=3` for the classic herringbone
chevron. `columns`/`rows` around 8, `width_x`/`width_y` around 0.8. Warm
brown Harris-tweed three-stop albedo (espresso, tan, cream) for a woven
two-tone heather look, very matte wool roughness (around 0.86 to 0.96), and a
soft `normal_map` `param1` around 0.35 with `param4=0` (directly-fed analytic
generator) so the chevron reads as pressed-tweed relief rather than sharp
thread crossings.

Honest limit: `weave2` emits one grayscale, so the tone comes from shading a
single ribbon shape, not two real thread colors, and it reads as a warm
one-tone weave. A true two-color tweed would need two colorizes blended
through the weave's own over/under mask. The host's Plaid Overlay
now does exactly that with `weave2`'s warp and weft masks (off by default).

## Subgraph structure

The woven-pattern host (2026-09-27). It absorbs `f01_woven_denim`,
`f05_silk_satin`, `f08_donegal_tweed` and `f09_plaid_flannel`. All four
are this same `crocodile_skin` shape: one generator feeds the albedo,
roughness and height colorizes. Only the generator differs, so the host
carries the other generators in and a Pattern selector picks one. Seven
groups, left to right into Material:

- **Twill Layout**: `TwillLayout` (`diagonal_weave`, the f01/f05 twill).
  Exposed: `Twill size`.
- **Crosshatch Layout**: `CrosshatchGrid` (`fbm` Cellular 3, the f09 grid).
  Exposed: `Check size` (drives `scale_x` and `scale_y`).
- **Weave Pattern**: `WeaveLayout` (`weave2`) and the selector math.
  Exposed: `Weave scale` (columns and rows), `Pattern`, `Stitch`,
  `Thread width` (both axes). Outputs the selected pattern plus
  `weave2`'s weft and warp thread masks.
- **Tweed Color**: `TweedColor`. Exposed: `Tweed color`.
- **Surface Finish**: `TweedRoughness`, `WeaveHeight`, `WeaveNormal`.
  Exposed: `Roughness`, `Relief strength`.
- **Plaid Overlay** (new): exposed `Plaid strength`, `Plaid sett`, `Sett repeat`.
- **Fleck Layer** (from f08): exposed `Fleck strength`, `Fleck density`
  (both axes), `Fleck color`.

The selector is one-hot weights in product-sum form: weave x w0 + twill x
w1 + crosshatch x w2, with the weights from `A<B` thresholds on the one
`Pattern` value. It is exact in every mode, where a lerp or a blend would
drift. Colour, roughness and relief all read the same selected signal, so
they stay registered in every mode.

Seeds: `diagonal_weave`, `fbm` and `voronoi` are seeded from node
position, so `TwillLayout` and `CrosshatchGrid` sit at (71, 216) in their
subgraphs (where the generator sits in f01/f05/f09) and `FleckSource` at
(0, 0) (as in f08). Do not move them. `weave2` has no seed.

## Feature layers

Every new layer defaults to a no-op, so the default renders exactly the
herringbone it did before the host work. A 2048 full-image diff of albedo,
normal and ORM against `main`'s graph gives 0 differing pixels (this graph
exports no heightmap), and the lit `preview_regress` composite is also
0 px.

| Layer | Exposed params | What it does |
|---|---|---|
| Weave Pattern: `Pattern` | 0, 0.5 or 1, default 0 | Picks the generator: 0 = `weave2` (below 0.25), 0.5 = diagonal twill (0.25 to 0.75), 1 = crosshatch (above 0.75). It is a switch, not a mix. |
| Weave Pattern: `Stitch` | 1-10, default 3 | `weave2`'s stitch length: 1 = plain over/under weave, 3 = the herringbone chevron. It also scales the weave (uv x stitch), so change `Weave scale` with it. |
| Weave Pattern: `Thread width` | 0-1, default 0.8 | Thread width on both axes; lower opens gaps between threads. |
| Plaid Overlay | `Plaid strength` 0-1, default 0 | Paints vertical threads with the sett along x and horizontal threads with the same sett along y, using `weave2`'s own warp/weft masks. The check is woven thread by thread and its colour edges sit on thread edges. Needs `Pattern` 0 (the masks come from `weave2`). At 1 the sett colours replace the tweed colour on the threads (Normal blend), so the threads lose their ribbon shading; relief still comes from the weave. |
| Fleck Layer | `Fleck strength` 0-1, default 0 | f08's sparse voronoi flecks, colour only (as f08 shipped). |

### Presets

Set these on the collapsed nodes. Colors are gradient stops (position: R, G,
B in 0-1). Anything not listed stays at its default. Each preset was
rendered at 2048 and diffed against the original material: 0 px differ on
albedo, normal and ORM for all four.

**Woven denim (f01), exact:**
- `Pattern` = 0.5, `Twill size` = 22 (default).
- `Tweed color`: 0.0: 0.10, 0.13, 0.30; 1.0: 0.26, 0.34, 0.55.
- `Roughness`: 0.0: 0.80 gray; 1.0: 0.93 gray. `Relief strength` = 0.25.

**Silk satin (f05), exact:**
- `Pattern` = 0.5, `Twill size` = 48.
- `Tweed color`: 0.0: 0.02, 0.25, 0.15; 1.0: 0.10, 0.42, 0.28.
- `Roughness`: 0.0: 0.12 gray; 1.0: 0.22 gray. `Relief strength` = 0.08.

**Donegal tweed (f08), exact:**
- `Weave scale` = 10, `Stitch` = 1, `Thread width` = 0.85.
- `Tweed color`: 0.0: 0.20, 0.18, 0.16; 0.5: 0.38, 0.34, 0.29; 1.0: 0.56,
  0.51, 0.44.
- `Relief strength` = 0.3. `Fleck strength` = 1 (`Fleck density` 36 and
  `Fleck color` are the defaults).

**Plaid flannel (f09), exact:**
- `Pattern` = 1, `Check size` = 10 (default).
- `Tweed color`: 0.0: 0.14, 0.16, 0.28; 0.5: 0.50, 0.22, 0.18; 1.0: 0.80,
  0.74, 0.62.
- `Roughness`: 0.0: 0.82 gray; 1.0: 0.92 gray. `Relief strength` = 0.42.

`Fleck density` 36 is past the voronoi slider's range (it stops at 32), so
type it into the field; it is already the default.

**Beyond the originals (these use the new layers):**
- *Woven tartan*: `Plaid strength` = 1 on the default herringbone, or with
  `Stitch` = 2 and `Weave scale` = 16 for a finer twill.
- *Flecked herringbone*: `Fleck strength` = 1 on the default.

**Back to the default:** `Pattern` 0, `Stitch` 3, `Weave scale` 8, `Thread
width` 0.8, `Plaid strength` and `Fleck strength` 0, and the default colour
and roughness ramps (0.0: 0.18, 0.14, 0.10; 0.5: 0.42, 0.34, 0.24; 1.0:
0.72, 0.65, 0.52 / 0.86 to 0.96 gray, `Relief strength` 0.35).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | NonMetallic | uniform |
| (top level) | twill_layout | graph |
| (top level) | crosshatch_layout | graph |
| (top level) | weave_pattern | graph |
| (top level) | tweed_color | graph |
| (top level) | surface_finish | graph |
| (top level) | plaid_overlay | graph |
| (top level) | fleck_layer | graph |
| twill_layout | TwillLayout | diagonal_weave |
| crosshatch_layout | CrosshatchGrid | fbm |
| weave_pattern | WeaveLayout | weave2 |
| weave_pattern | PatternSelect | uniform_greyscale |
| weave_pattern | IsWeave | math |
| weave_pattern | IsCrosshatch | math |
| weave_pattern | WeaveOrCrosshatch | math |
| weave_pattern | IsTwill | math |
| weave_pattern | WeaveTerm | math |
| weave_pattern | TwillTerm | math |
| weave_pattern | CrosshatchTerm | math |
| weave_pattern | WeaveTwillSum | math |
| weave_pattern | PatternMix | math |
| tweed_color | TweedColor | colorize |
| surface_finish | TweedRoughness | colorize |
| surface_finish | WeaveHeight | colorize |
| surface_finish | WeaveNormal | normal_map |
| plaid_overlay | WarpStripes | gradient |
| plaid_overlay | WeftStripes | gradient |
| plaid_overlay | WarpComposite | blend |
| plaid_overlay | WeftComposite | blend |
| fleck_layer | FleckSource | voronoi |
| fleck_layer | FleckMask | colorize |
| fleck_layer | FleckColor | colorize |
| fleck_layer | FleckComposite | blend |
<!-- nodes:end -->
