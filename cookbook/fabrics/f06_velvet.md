# f06_velvet - Velvet

_Category: fabrics. Open the graph: cookbook/fabrics/f06_velvet.ptex._

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

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
