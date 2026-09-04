# l03_suede - Suede or nubuck

_Category: leather. Open the graph: `cookbook/leather/l03_suede.ptex`._

Soft napped leather with no cellular grain at all: a continuous fibrous surface rather than the pebbled scale look of the other leathers in this set.

## Recipe

Clones `crocodile_skin` but swaps its donor generator: soft napped leather has no cellular grain, so `voronoi_0` is retyped to `perlin` (continuous, no hard cell edges), with `iterations` adding fine fiber grain on top. Warm fawn albedo, very high matte roughness, and a very low `normal_map` `param1` (around 0.10, still with `param4=0`) so the surface reads as soft nap rather than hard relief.

Note: suede is the one leather in this set exempt from the crocodile-donor voronoi port-0 polarity trap the other cell-based cards deal with, since there is no voronoi cell grain here to invert in the first place. This recipe read correctly on the first render, no rework needed.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via
the same shared `_group_leather_grain` helper as `l01`/`l04` (this donor
carries no `blend` node, so no port-source tracing applies). Opening the
graph shows 2 top-level groups (plus `Material` and the untouched metallic
`uniform_0`) instead of the raw 7-node graph:

- **Grain Pattern** — `voronoi_0` (retyped to `perlin`, `iterations=8`) and
  `colorize_1` (the fawn suede albedo). Exposed: `Fiber grain`
  (`voronoi_0.iterations`, matching `f06_velvet`'s convention of exposing the
  octave count for a perlin-donor material), `Suede color`.
- **Surface Finish** — `colorize_0` (linear height ramp), `colorize_3`
  (very matte roughness), `normal_map_0` (`param1=0.10`, `param4=0`).
  Exposed: `Nap roughness`, `Nap relief`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0` on
all three exported maps.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
