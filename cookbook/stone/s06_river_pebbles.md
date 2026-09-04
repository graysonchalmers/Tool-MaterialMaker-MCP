# s06_river_pebbles - Natural river pebbles

_Category: stone. Open the graph: `cookbook/stone/s06_river_pebbles.ptex`._

Tightly packed rounded river pebbles, the organic counterpart to s05's regular hex tile. Reads closer to a packed gravel or fieldstone bed than perfectly smooth individual stones, but still clearly natural stone.

## Recipe

Clones `rock` (the same donor as `s02` granite) and tunes it for big rounded cells instead of granite's fine flecks: both voronoi scales dropped to about 7 (pebble-sized cells), albedo fed from `voronoi_0` port 2 (per-cell random) through a multi-tone natural-stone gradient so each pebble is a different tone, and normal strength raised (`param1` about 0.6, `param4=0`) so each cell bulges into a rounded stone. The same fine-perlin-grain multiply used in s05 adds per-stone surface texture.

Pitfall specific to this material: the albedo map alone looks like flat angular polygons; the rounding lives entirely in the normal map, so the flat swatch badly undersells it. This is a relief-driven material, so it can only be confirmed correct by running `render_preview` (the sphere/cube/ground 3D composite); under real lighting the cells read as tightly packed rounded natural stones, even though the underlying cells are still voronoi-angular.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. The
`rock` donor's own `blend_0` (masked by `perlin_0`) was orphaned when this
builder rewired `colorize_0` to read `voronoi_0` port 2 directly instead of
`blend_0`'s output -- it still exists in the graph with no consumer, folded
into the pattern group since it shares `voronoi_0`/the same conceptual
"color source" step. `blend_grain` carries no port2 mask (unconnected -> a
uniform 1.0), a plain full-strength Multiply, no polarity to trace.
Opening the graph shows 4 top-level groups instead of the raw 13-node
graph:

- **Pebble Pattern** -- `voronoi_0`, `colorize_0`, and the orphaned
  `blend_0`. Exposed: `Pebble size` (`voronoi_0.scale_x`), `Pebble color`
  (`colorize_0.gradient`).
- **Surface Grain** -- `perlin_grain`, `colorize_grain`, `blend_grain`.
  Exposed: `Grain scale` (`perlin_grain.scale_x`), `Grain detail`
  (`perlin_grain.iterations`).
- **Material Finish** -- `colorize_1` (metallic, zeroed), `colorize_2`
  (roughness), `perlin_0`. Exposed: `Roughness` (`colorize_2.gradient`).
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
