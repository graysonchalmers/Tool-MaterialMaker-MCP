# l03_suede - Suede or nubuck

_Category: leather. Open the graph: `cookbook/leather/l03_suede.ptex`._

Soft napped leather with no cellular grain at all: a continuous fibrous surface rather than the pebbled scale look of the other leathers in this set.

## Recipe

Clones `crocodile_skin` but swaps its donor generator: soft napped leather has no cellular grain, so `voronoi_0` is retyped to `perlin` (continuous, no hard cell edges), with `iterations` adding fine fiber grain on top. Warm fawn albedo, very high matte roughness, and a very low `normal_map` `param1` (around 0.10, still with `param4=0`) so the surface reads as soft nap rather than hard relief.

Note: suede is the one leather in this set exempt from the crocodile-donor voronoi port-0 polarity trap the other cell-based cards deal with, since there is no voronoi cell grain here to invert in the first place. This recipe read correctly on the first render, no rework needed.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
