# f04_wool_knit - Wool / chunky knit

_Category: fabrics. Open the graph: `cookbook/fabrics/f04_wool_knit.ptex`._

An honest coarse-weave stand-in for chunky knitwear, not a true knit. This
graph does not produce real stockinette knit loops: the catalog has no
generator capable of that, and the search was formally closed. Read the
structural read as a blocky chunky-weave textile, and describe it that way
in any user-facing copy, not as "knit."

## Recipe

`weave2`'s own `stitch` parameter looked promising for loop softness but only
renders a crisp herringbone/basket diagonal: structurally the same hard-
crossing weave as plain `weave`. The workable stand-in that shipped here:
`weave` at a COARSE scale with a near-max `width` (few, wide, almost-touching
ribs), which reads as chunky blocky yarn rows rather than fine thread,
closer to a basket or chunky-weave textile than true knit loops.

Closed for good on 2026-09-03: an isolation-render probe tested the four most
plausible knit leads and confirmed none produce stockinette (upright V's in
aligned wales is the real knit tell, not merely offset rows). `pattern`
Bounce and `bricks` Running Bond both make a staggered pillow honeycomb;
`weave2` stitch=1 is a basket weave; `weave2` stitch=3 is the only one with
chevrons, but they reverse band-to-band, i.e. herringbone tweed (shipped
separately as `f07_herringbone_tweed`), not knit. Do not re-open this search
without a new generator in the catalog.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Same `crocodile_skin` donor shape as `f03_canvas_burlap` (no `blend` node,
no mask wiring to trace). Opening the graph shows 2 top-level groups
(plus `Material` and the untouched metallic `uniform_0`) instead of the
raw 6-node graph:

- **Knit Pattern** — `voronoi_0` (retyped to `weave`) and `colorize_1`
  (albedo). `voronoi_0` also feeds **Surface Finish**'s normal and
  roughness colorizes directly, the expected shared-upstream-node shape.
  Exposed: `Rib count`, `Wool color`.
- **Surface Finish** — `colorize_0` (normal source), `colorize_3`
  (roughness), `normal_map_0`. Exposed: `Roughness`, `Relief strength`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
