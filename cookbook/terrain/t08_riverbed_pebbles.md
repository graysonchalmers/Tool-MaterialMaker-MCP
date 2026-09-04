# t08_riverbed_pebbles - Riverbed pebbles

_Category: terrain. Open the graph: `cookbook/terrain/t08_riverbed_pebbles.ptex`._

Discrete tumbled river pebbles with a damp sheen, distinguished from `t05_cracked_ice`'s connected crack network by recessed contact joints instead of crack lines.

## Recipe

Built with the shared `_dry_earth_plates()` helper in `cookbook_terrain.py` at scale 8, a river-tumbled multicolor palette (gray/tan/slate/brown/cream), `warp_0` at 0.02, and roughness 0.2 for a damp sheen. The low warp value produces recessed contact-shadow joints between discrete packed pebbles rather than warped crack lines; that single change is what separates this material from t05's ice plates despite sharing the same underlying helper.

No separate pitfall pass was needed once the warp value was set low; the recessed-joint read came through on the first pass at 0.02.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via
the same shared `_group_dry_earth_plate()` helper used by
`t05_cracked_ice` (the two plain plate materials with no emission chain).

- **Pebble Bed & Gaps** -- `voronoi_0`, `colorize_1`, `colorize_0`,
  `colorize_plate`, `warp_0`, `blend_0`, `colorize_4`, `blend_1`,
  `colorize`, `normal_map_0`. `warp_0` (at this material's own low 0.02,
  the value that produces recessed contact joints rather than crack lines)
  is kept with both of its direct consumers -- `blend_0` and, via
  `colorize_4`, the relief chain -- and is not exposed as a friendly
  parameter. Exposed: `Plate size` (`voronoi_0.scale_x`), `Pebble color`
  (`colorize_plate.gradient`), `Gap depth` (`blend_0.amount`).
- **Surface Finish** -- `perlin_1`, `colorize_3`, `perlin_0`,
  `rough_const`. Exposed: `Roughness` (`rough_const.gradient`).

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all four exported maps (albedo, heightmap, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
