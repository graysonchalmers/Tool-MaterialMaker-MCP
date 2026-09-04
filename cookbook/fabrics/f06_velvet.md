# f06_velvet - Velvet

_Category: fabrics. Open the graph: `cookbook/fabrics/f06_velvet.ptex`._

A soft fibrous pile fabric with no grid pattern at all, deep saturated color,
and a subtle nap relief instead of hard thread crossings.

## Recipe

Velvet has no grid pattern, so this is not a weave graft like the other
fabrics. Retype the generator to `perlin` instead of `voronoi`. Perlin is
continuous (no cell edges) and its `iterations` parameter (octaves, up to 10)
layers in fine high-frequency detail on top of the base noise, which genuinely
reads as soft fiber grain. Deep saturated wine albedo, high roughness, and a
very low `normal_map` `param1` (around 0.12, still with `param4=0` since
perlin is a directly-fed analytic generator) for soft nap relief instead of
hard relief.

Pitfall: the first attempt reused the granite speckle lever (voronoi port 2
`rand3`, flat per-cell random) at voronoi's max scale, which looked mottled
and faceted like crystal or stone rather than soft fabric, because voronoi's
per-cell random value spans the full color-gradient range regardless of how
narrow the gradient is, producing hard high-contrast patch edges. Grafting a
`fast_blur_shader` between the voronoi and the colorize feeds to soften those
edges hit a Godot "invalid shader" render failure (its input port is `rgba`;
voronoi port 2 is `rgb`), not worth chasing further. For a soft, continuous
material like velvet, reach for `perlin`/`fbm` before `voronoi`.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Same `crocodile_skin` donor shape as `f03_canvas_burlap` (no `blend` node,
no mask wiring to trace) even though the generator is retyped to `perlin`
rather than a weave family. Opening the graph shows 2 top-level groups
(plus `Material` and the untouched metallic `uniform_0`) instead of the
raw 6-node graph:

- **Fiber Pattern** — `voronoi_0` (retyped to `perlin`) and `colorize_1`
  (albedo). `voronoi_0` also feeds **Surface Finish**'s normal and
  roughness colorizes directly, the expected shared-upstream-node shape.
  Exposed: `Fiber grain` (the `iterations` octave count), `Velvet color`.
- **Surface Finish** — `colorize_0` (normal source), `colorize_3`
  (roughness), `normal_map_0`. Exposed: `Roughness`, `Relief strength`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
