# s07_cobblestone - True irregular cobblestone

_Category: stone. Open the graph: `cookbook/stone/s07_cobblestone.ptex`._

True irregular cobblestone with genuinely varied plate sizes and recessed mortar. Closes the gap `s05_hex_stone_tile` left open: this is the voronoi-plate approach that card's own notes flagged as untried.

## Recipe

Clones `dry_earth`, scales `voronoi_0` from 4 to 6 (cobble-sized plates), and feeds `voronoi_0` port 2 (per-cell random) through a multi-tone stone gradient rewired into `blend_0` port 1 in place of the flat perlin earth base, so each plate reads as a distinct stone while the existing warped-crack Multiply overlay reads as recessed mortar. `warp_0.amount` is dropped to 0.12 for clean thin mortar with a slight organic wobble.

Pitfall specific to this material: two traps cost a pass each. First, the initial tone gradient was too narrow (0.30 to 0.55, muted) so plates all looked uniform; it needed widening hard across both value and hue. Second, a broad gray haze inside the plates was mistaken for a gradient problem, but it was actually `dry_earth`'s stock `warp_0.amount` of 0.4 smearing the crack shadows into washes across the plates, fixed by dropping that value to 0.12. Judge the result in 3D with `render_preview`: the cobbles should bulge and the mortar should recess.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via
a shared `_group_paving_stone` helper reused across `s07`/`s08`/`s10` (the
three dry_earth-clone paving materials that add the same `colorize_cobble`
+ grain-overlay structure). **`warp_0` caution**: this donor's
`warp_0.amount` is the single most render-sensitive parameter in the whole
stone category -- at 0.4 (the donor default) it smears the crack shadows
into a broad haze across the plates (this material's own pitfall note is
about exactly that), and this recipe deliberately drops it to 0.12 to kill
that haze. `warp_0` is grouped with `blend_0`, the thing it most directly
and visibly feeds (the crack/joint pattern), and its `amount` is **not**
exposed as a friendly parameter, per the retrofit's category-wide rule.
`dry_earth`'s own `blend_0` carries no port2 mask (unconnected -> uniform
1.0) -- its `amount` (0.6 here) is a genuine scalar mix strength, not a
spatial mask, so it is safe to expose as `Joint depth`. `colorize_0`
(the original flat-earth base `blend_0` used before this recipe rewired
`blend_0`'s background onto `colorize_cobble`) is orphaned but still
present, folded into the relief group since it shares `perlin_0` there.
Opening the graph shows 2 top-level groups instead of the raw 16-node
graph:

- **Stone & Relief** -- `voronoi_0`, `colorize_1`, `colorize_cobble`,
  `warp_0`, `blend_0` (the color/crack composite) plus the never-separately-
  tuned relief/roughness chain (`perlin_1`, `colorize_3`, `perlin_0`,
  `colorize_0`, `colorize_4`, `blend_1`, `colorize`, `normal_map_0`) --
  folded in here since it has no builder-set parameter of its own for this
  material (unlike `s10`, which tunes `normal_map_0.param1` and so gets a
  separate Relief group). Exposed: `Stone size` (`voronoi_0.scale_x`),
  `Stone color` (`colorize_cobble.gradient`), `Joint depth`
  (`blend_0.amount`).
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
