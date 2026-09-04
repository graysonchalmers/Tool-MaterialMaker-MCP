# s04_scattered_river_stones - Scattered river stones in sand

_Category: stone. Open the graph: `cookbook/stone/s04_scattered_river_stones.ptex`._

Rounded river stones sitting loose in a sand bed, with visible sand gaps between them. Deliberately softer and more scattered than s06's edge-to-edge pebble packing.

## Recipe

Clones `rock`, then thresholds `voronoi_0`'s own distance field (port 0) directly into a stone-vs-sand mask, so stones sit in a connected sand matrix with visible gaps rather than filling the whole frame with cells. The stone zone is widened so each masked region reads as a real rounded pebble, not a pinprick.

Pitfall specific to this material: the first attempt had the mask backwards. It assumed port 0 (F1, distance to the nearest voronoi seed) was high at cell centers, when it is actually low at centers and rises toward the inter-cell network. Thresholding on that wrong assumption painted tiny sand-colored dots at the cell centers with stone filling everywhere else, the exact inverse of the intended look. The fix was flipping the gradient direction (low F1 maps to stone, high F1 maps to sand). Because this is relief-driven, confirm the result with `render_preview` rather than judging the flat albedo swatch.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
