# s04_scattered_river_stones - Scattered river stones in sand

_Category: stone. Open the graph: `cookbook/stone/s04_scattered_river_stones.ptex`._

Rounded river stones sitting loose in a sand bed, with visible sand gaps between them. Deliberately softer and more scattered than s06's edge-to-edge pebble packing.

## Recipe

Clones `rock`, then thresholds `voronoi_0`'s own distance field (port 0) directly into a stone-vs-sand mask, so stones sit in a connected sand matrix with visible gaps rather than filling the whole frame with cells. The stone zone is widened so each masked region reads as a real rounded pebble, not a pinprick.

Pitfall specific to this material: the first attempt had the mask backwards. It assumed port 0 (F1, distance to the nearest voronoi seed) was high at cell centers, when it is actually low at centers and rises toward the inter-cell network. Thresholding on that wrong assumption painted tiny sand-colored dots at the cell centers with stone filling everywhere else, the exact inverse of the intended look. The fix was flipping the gradient direction (low F1 maps to stone, high F1 maps to sand). Because this is relief-driven, confirm the result with `render_preview` rather than judging the flat albedo swatch.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. The
`rock` donor's own `blend_0` (masked by `perlin_0`, port2) and the
`colorize_0`/`colorize_2` it used to feed were left orphaned once this
builder rewired the Material albedo/roughness ports onto the new
`blend_stones`/`blend_rgh` composites -- those dead nodes are folded into
whichever new group shares their input, not deleted (organizational-only
retrofit). `blend_stones` and `blend_rgh` share one real spatial mask,
`colorize_gap` (fed by `voronoi_0` port 0, the F1 distance field this
material's own pitfall note is about); per the sf03/pm03 precedent, a mask
gradient stays internal and is never exposed as a friendly parameter, and
both blends' `amount` is pinned at 1 (a pure mask-driven split, not a
dimmer), so neither is exposed either. Opening the graph shows 4 top-level
groups instead of the raw 17-node graph:

- **Stone/Sand Mask** -- `voronoi_0`, `colorize_gap` (the mask). Exposed:
  `Stone size` (`voronoi_0.scale_x`).
- **Stone & Sand Color** -- `colorize_stone`, `colorize_sand`,
  `blend_stones`, plus the orphaned `colorize_0`/`colorize_2`/`blend_0`.
  Exposed: `Stone color`, `Sand color`.
- **Material Finish** -- `colorize_1` (metallic, zeroed), `colorize_rgh_stone`,
  `colorize_rgh_sand`, `blend_rgh`, `perlin_0`. Exposed: `Stone roughness`,
  `Sand roughness`.
- **Relief** -- `perlin_1`, `voronoi_1`, `warp_0`, `normal_map_0`. Exposed:
  `Relief strength` (`normal_map_0.param1`) only -- `warp_0.amount` stays
  internal.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0` on
all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
