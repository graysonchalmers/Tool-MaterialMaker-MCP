# s10_flagstone - Flagstone / slate paving

_Category: stone. Open the graph: `cookbook/stone/s10_flagstone.ptex`._

Large flat sawn slate slabs with recessed joints, tuned as the opposite of `s07_cobblestone` on nearly every axis.

## Recipe

A `dry_earth` clone with `voronoi_0` scale set to 4 (few big slabs). `normal_map` `param1` is dropped from 0.99 to 0.5 for flat slab tops, since cobbles bulge but sawn flagstones are flat and relief should live only in the recessed joints. `warp_0` is held at the haze-free 0.12 used across the paving materials, with a cool blue-gray / green-gray slate palette and low per-slab tonal variation, since slate slabs are fairly uniform compared to cobblestone's strong hue spread.

No separate pitfall pass was needed for this one; the recipe is a direct inversion of s07's cobblestone levers (flat instead of bulging, few large slabs instead of many small plates, low variation instead of high).

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via
the same shared `_group_paving_stone` helper as `s07`/`s08`. **`warp_0`
caution**: held at the same haze-free 0.12 used across the paving
materials -- `warp_0.amount` is the single most render-sensitive parameter
in this category, and `warp_0` stays grouped with `blend_0`, the thing it
directly feeds; its `amount` is **not** exposed as a friendly parameter.
This is the one material in the shared-helper trio that earns a separate
Relief group: unlike `s07`/`s08`, it explicitly tunes `normal_map_0.param1`
(0.99 -> 0.5, flat slab tops), so that chain gets its own exposed parameter
instead of being folded into Stone Color. Opening the graph shows 3
top-level groups instead of the raw 16-node graph:

- **Stone Color** -- `voronoi_0`, `colorize_1`, `colorize_cobble`,
  `warp_0`, `blend_0`. Exposed: `Stone size` (`voronoi_0.scale_x`),
  `Stone color` (`colorize_cobble.gradient`), `Joint depth`
  (`blend_0.amount`).
- **Relief** -- `perlin_1`, `colorize_3`, `perlin_0`, `colorize_0`
  (orphaned once `blend_0`'s background is rewired onto `colorize_cobble`,
  folded in here since it shares `perlin_0`), `colorize_4`, `blend_1`,
  `colorize`, `normal_map_0`. Exposed: `Slab flatness`
  (`normal_map_0.param1`).
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
