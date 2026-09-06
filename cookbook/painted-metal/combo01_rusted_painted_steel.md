# combo01_rusted_painted_steel - Rusted painted steel

_Category: painted-metal. Open the graph: `cookbook/painted-metal/combo01_rusted_painted_steel.ptex`._

Prompt: "rusted painted steel, paint peeling to bare metal". A Phase-3 hero
material (frozen 15-case test set, the one "combo" case that required
compositing two materials), folded into the cookbook 2026-09-05 so it
carries the same gates, card, and subgraph grouping as every other material.

## Recipe

Clone `rusted_metal` (rust albedo comes out of `blend_0`, rust roughness out
of `blend_1`, patch-driven metallic out of `colorize_3`), then composite a
flat paint coat OVER it:

- peel mask: `perlin_pm` thresholded by `colorize_pm`, a hard-ish irregular
  edge;
- paint: `paint_alb` (flat color) and `paint_rgh` (flat low roughness), each a
  two-stop colorize with identical stops fed by the mask perlin so they are
  valid constant sources;
- `blend_alb` and `blend_rgh` put paint over rust with the mask as opacity.

Where the mask is high the paint shows (smooth, colored); where it is low the
rust and bare metal show through. This is the paint-over-rust peel composite
that the later painted-metal set (`pm03_chipped_paint`) generalized, and it
predates the pinned blend port convention, so read its port order from the
graph rather than assuming majority-on-port-1.

## Subgraph structure

Opening the graph shows 3 top-level nodes instead of 17, and the composite
reads as exactly what it is, two layers feeding Material:

- **Rust Layer** (all of the `rusted_metal` donor: `perlin_0/1/2`,
  `colorize_0..4`, `blend_0`, `blend_1`). Exposed: `Bare metal color`, `Rust
  color`, `Rust patch size`.
- **Paint Coat** (`perlin_pm`, `colorize_pm`, `paint_alb`, `paint_rgh`,
  `blend_alb`, `blend_rgh`). Exposed: `Paint color`, `Peel amount`, `Peel
  patch size`.

## See also

`guide://authoring` (or `docs/AUTHORING.md`) for the blend mask and opacity
notes in "Cross-material lessons"; `docs/evidence/phase3/2026-08-26-iter1.md`.
