# t07_forest_floor - Forest floor

_Category: terrain. Open the graph: `cookbook/terrain/t07_forest_floor.ptex`._

Scattered brown leaf litter with a muted olive accent, structurally distinct from the connected-crack terrain materials in this set.

## Recipe

Re-based entirely off the `_dry_earth_plates()` family used by t05/t06/t08. Uses the `crocodile_skin` donor, retyping `voronoi_0` to `fbm` with noise=5 (Cellular 4), scale 6, iterations 5, since scattered overlapping leaf pieces have no connected crack network to speak of. Palette is brown-dominant leaf color with a muted olive accent, high matte roughness, and `param4=0` medium relief.

Pitfall specific to this material: on `dry_earth` this material read as cracked-mud camo no matter what palette was tried, because the underlying structure is a connected plate network and leaf litter is not. Leaving the plate donor entirely and re-basing onto `fbm` Cellular 4 was the fix, not a palette change.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, the
exact `o05_coral` template (organics category), same `crocodile_skin`
donor:

- **Litter Pattern** -- `colorize_1`, `voronoi_0` (retyped to `fbm`).
  Exposed: `Clump scale` (`voronoi_0.scale_x`), `Leaf color`
  (`colorize_1.gradient`).
- **Surface Finish** -- `colorize_3`, `colorize_0`, `normal_map_0`.
  Exposed: `Roughness` (`colorize_3.gradient`), `Debris relief`
  (`normal_map_0.param1`).

`uniform_0` (the untouched metallic-0 scalar, feeding Material port 1
directly) stays top-level, matching the same precedent used elsewhere in
this retrofit for untouched single-purpose scalar nodes.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
