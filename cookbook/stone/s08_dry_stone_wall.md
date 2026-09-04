# s08_dry_stone_wall - Dry-stone / fieldstone wall

_Category: stone. Open the graph: `cookbook/stone/s08_dry_stone_wall.ptex`._

Randomly packed fieldstone wall with no coursing, distinct from the neatly quarried `s09_ashlar_wall` in the same set.

## Recipe

Uses the same `dry_earth` clone as `s07_cobblestone`, retuned to read as a different material rather than a recolor: `voronoi_0` scale moved from 6 to 8 (smaller, denser stones), a cool weathered-gray palette in place of cobblestone's warm tan, and thin dark dry-stack gaps. `warp_0.amount` is held at the same haze-free 0.12 used in s07.

Pitfall specific to this material: a pass at `warp_0.amount` 0.20, chasing more angular edges, brought the haze back without sharpening any corners, because warp displaces rather than bevels; the angular fieldstone read actually comes from the voronoi cell shape itself, which is already polygonal. The mossy-green stop needs to stay restrained too; pushed further it tips into a camo grid, the same trap s05's hex tile hit. Honest limit: pure voronoi has no horizontal coursing, so this reads as random rubble or fieldstone, not neatly coursed drystone.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via
the same shared `_group_paving_stone` helper as `s07`/`s10` (all three clone
`dry_earth` and add the same `colorize_cobble` + grain-overlay structure).
**`warp_0` caution**: held at the same haze-free 0.12 used in `s07` --
this material's own pitfall note is specifically about a pass at 0.20 that
brought the smear-haze back without any angularity gain, confirming
`warp_0.amount` is the single most render-sensitive parameter in this
category. `warp_0` stays grouped with `blend_0` (the thing it directly
feeds) and its `amount` is **not** exposed as a friendly parameter, per the
retrofit's category-wide rule. `blend_0`'s own `amount` (0.6, a plain
scalar mix, no port2 mask) is a genuine tunable and is exposed. The
structure is identical to `s07`'s (same helper, same donor, same added
nodes -- only parameter values differ). Opening the graph shows 2
top-level groups instead of the raw 16-node graph:

- **Stone & Relief** -- `voronoi_0`, `colorize_1`, `colorize_cobble`,
  `warp_0`, `blend_0`, plus the never-separately-tuned relief/roughness
  chain (`perlin_1`, `colorize_3`, `perlin_0`, `colorize_0`, `colorize_4`,
  `blend_1`, `colorize`, `normal_map_0`; `colorize_0` is orphaned once
  `blend_0`'s background is rewired onto `colorize_cobble`, still present,
  folded in since it shares `perlin_0`). Exposed: `Stone size`
  (`voronoi_0.scale_x`), `Stone color` (`colorize_cobble.gradient`),
  `Joint depth` (`blend_0.amount`).
- **Surface Grain** -- `perlin_grain`, `colorize_grain`, `blend_grain`.
  Exposed: `Grain scale` (`perlin_grain.scale_x`), `Grain contrast`
  (`colorize_grain.gradient`).

Verified after building, with extra scrutiny given the `warp_0` caution:
`renders_match` against this material's own pre-retrofit baseline came back
at an exact `grid_mean_abs_diff` of `0.0` on all four exported maps (albedo,
heightmap, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
