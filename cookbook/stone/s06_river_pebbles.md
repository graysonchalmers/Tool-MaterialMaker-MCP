# s06_river_pebbles - Natural river pebbles

_Category: stone. Open the graph: `cookbook/stone/s06_river_pebbles.ptex`._

Tightly packed rounded river pebbles, the organic counterpart to s05's regular hex tile. Reads closer to a packed gravel or fieldstone bed than perfectly smooth individual stones, but still clearly natural stone.

## Recipe

Clones `rock` (the same donor as `s02` granite) and tunes it for big rounded cells instead of granite's fine flecks: both voronoi scales dropped to about 7 (pebble-sized cells), albedo fed from `voronoi_0` port 2 (per-cell random) through a multi-tone natural-stone gradient so each pebble is a different tone, and normal strength raised (`param1` about 0.6, `param4=0`) so each cell bulges into a rounded stone. The same fine-perlin-grain multiply used in s05 adds per-stone surface texture.

Pitfall specific to this material: the albedo map alone looks like flat angular polygons; the rounding lives entirely in the normal map, so the flat swatch badly undersells it. This is a relief-driven material, so it can only be confirmed correct by running `render_preview` (the sphere/cube/ground 3D composite); under real lighting the cells read as tightly packed rounded natural stones, even though the underlying cells are still voronoi-angular.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
