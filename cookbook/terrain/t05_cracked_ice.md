# t05_cracked_ice - Cracked ice

_Category: terrain. Open the graph: `cookbook/terrain/t05_cracked_ice.ptex`._

Glassy blue-white ice with a connected network of sharp surface cracks; smooth flat plate faces with relief only at the cracks.

## Recipe

Built with the shared `_dry_earth_plates()` helper in `cookbook_terrain.py` at scale 5, glassy blue-white per-plate tint, `warp_0` at 0.12 for clean sharp cracks, and roughness 0.12. The helper also gives this material a flat roughness texture rather than a scalar, so an ORM map actually exports (`dry_earth` normally leaves the roughness input unconnected, which renders no ORM and hides a wet or glossy sheen in the 3D preview).

The key move for the ice look specifically: the crack-only signal (`colorize_4`, sourced from `warp_0`) is fed into the normal-prep colorize instead of `dry_earth`'s perlin-grain height (`blend_1`), so plate faces stay smooth and only the cracks carry relief.

Pitfall specific to this material: without that swap, the plates read as frosted or sandy concrete rather than glassy ice. Judge smoothness on the normal map and plate faces directly; the low-roughness gloss is real but the preview's dark backdrop cannot show it, the same caveat that applies to `t06_cooled_lava`'s emission.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via
a shared `_group_dry_earth_plate()` helper reused across `t05` and
`t08_riverbed_pebbles` (the two plain plate materials with no emission
chain -- `t06_cooled_lava`'s glow chain needs bespoke handling, see its own
card).

- **Ice Plate & Cracks** -- `voronoi_0`, `colorize_1`, `colorize_0`,
  `colorize_plate`, `warp_0`, `blend_0`, `colorize_4`, `blend_1`,
  `colorize`, `normal_map_0`. `warp_0` has two direct consumers here --
  `blend_0` (the crack darkening in albedo) and, via `colorize_4`, the
  crack-relief chain feeding `normal_map_0` (further sharpened by this
  recipe's own `colorize` rewire onto `colorize_4` for smooth glassy
  faces) -- so both are kept in the same group as `warp_0`, per the
  standing rule that `warp_0` is never exposed as a friendly parameter and
  always stays with what it feeds. Exposed: `Plate size`
  (`voronoi_0.scale_x`), `Ice color` (`colorize_plate.gradient`), `Crack
  depth` (`blend_0.amount`).
- **Surface Finish** -- `perlin_1`, `colorize_3`, `perlin_0`,
  `rough_const`. Exposed: `Roughness` (`rough_const.gradient`, the flat
  roughness texture the helper adds). `colorize_3` (orphaned once
  `dry_earth`'s metallic wire is dropped) folds in since it shares
  `perlin_1` with nothing else.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all four exported maps (albedo, heightmap, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
