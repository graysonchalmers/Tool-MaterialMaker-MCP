# f03_canvas_burlap - Canvas / burlap

_Category: fabrics. Open the graph: `cookbook/fabrics/f03_canvas_burlap.ptex`._

A coarse, natural-tan woven fabric with visible gaps between thick threads,
the kind of weave you'd expect from canvas or burlap sacking.

## Recipe

Retype the generator to `weave` (plain over/under, one output) at a coarse
scale (`columns`/`rows` around 10) with `width` around 0.6 so gaps show
between the thick threads. Natural tan albedo, high roughness. Apply the
`param4=0` normal fix at moderate strength for pronounced coarse-thread
relief. This was a first-pass hit: no retries needed.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
This donor (`crocodile_skin`) carries no `blend` node at all, so there is
no mask/port wiring to trace here. Opening the graph shows 2 top-level
groups (plus `Material` and the untouched metallic `uniform_0`) instead of
the raw 6-node graph:

- **Weave Pattern** — `voronoi_0` (retyped to `weave`) and `colorize_1`
  (albedo). `voronoi_0` also feeds **Surface Finish**'s normal and
  roughness colorizes directly, so its output crosses the group boundary a
  second time — the expected shape when one generator feeds three
  downstream consumers. Exposed: `Thread gap`, `Burlap color`.
- **Surface Finish** — `colorize_0` (normal source), `colorize_3`
  (roughness), `normal_map_0`. Exposed: `Roughness`, `Relief strength`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
