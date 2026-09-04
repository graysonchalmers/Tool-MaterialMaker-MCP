# t02_fresh_snow - Fresh snow

_Category: terrain. Open the graph: `cookbook/terrain/t02_fresh_snow.ptex`._

Near-white smooth snow drifts with a faint cold tint in the low points.

## Recipe

Clones `rock` and keeps its smooth blobby structure, since a smooth source is fine when the target is genuinely near-flat, and snow drifts are exactly that case, the same reasoning `s02` granite used for reusing `rock`. Albedo is near-white with a faint cold blue-gray in the low points. Metallic is forced near-zero, since this donor's `perlin_0` feeds metallic directly by default, which is wrong for snow. A proactive `param4=0` is applied at low strength (about 0.18) for soft drifts rather than stone-scale relief.

No pitfall pass was needed beyond the metallic override; the low-strength relief was set proactively rather than discovered by a failed first attempt.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, same
`rock`-donor template used for `s04`/`s06` (stone category):

- **Snow Color** -- `colorize_0`, `voronoi_0`, `blend_0` (the untouched
  voronoi/blend pattern chain feeding `colorize_0`). Exposed: `Snow color`
  (`colorize_0.gradient`).
- **Material Finish** -- `colorize_1`, `colorize_2`, `perlin_0`. Exposed:
  `Surface sheen` (`colorize_2.gradient`). `colorize_1` (metallic, forced
  to 0) stays an unexposed member.
- **Relief** -- `normal_map_0`, `perlin_1`, `voronoi_1`, `warp_0`. Exposed:
  `Relief strength` (`normal_map_0.param1`). `warp_0.amount` is not
  exposed, kept grouped with its direct consumer (`normal_map_0`).

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
