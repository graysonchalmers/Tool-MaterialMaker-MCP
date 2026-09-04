# t03_gravel - Gravel

_Category: terrain. Open the graph: `cookbook/terrain/t03_gravel.ptex`._

Loose scattered gravel at pebble scale with a wide earthy palette.

## Recipe

Clones `rock` and reuses `s02` granite's flat-per-cell-random lever (`voronoi_0` port 2, bypassing the smooth blend), but at pebble scale (14, versus granite's fine-fleck 44) with a wider earthy gray/tan/brown palette instead of granite's grayscale. `param4=0` relief is set stronger than granite's, since loose gravel is bumpier than a polished slab.

No pitfall pass was needed; this is a direct scale-and-palette retune of a proven lever from `s02` granite.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, the
exact `s06_river_pebbles` template (stone category):

- **Pebble Pattern** -- `colorize_0`, `voronoi_0`, `blend_0` (orphaned once
  `colorize_0` was rewired to read `voronoi_0` port 2 directly; folded in
  here since it shares `voronoi_0` as a source). Exposed: `Pebble size`
  (`voronoi_0.scale_x`), `Pebble color` (`colorize_0.gradient`).
- **Material Finish** -- `colorize_1`, `colorize_2`, `perlin_0`. Exposed:
  `Roughness` (`colorize_2.gradient`).
- **Relief** -- `normal_map_0`, `perlin_1`, `voronoi_1`, `warp_0`. Exposed:
  `Relief strength` (`normal_map_0.param1`). `warp_0.amount` is not
  exposed.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
