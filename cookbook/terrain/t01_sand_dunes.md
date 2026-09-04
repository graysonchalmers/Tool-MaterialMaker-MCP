# t01_sand_dunes - Sand dunes

_Category: terrain. Open the graph: `cookbook/terrain/t01_sand_dunes.ptex`._

Broad, slow-rolling sand dunes with warm tan tone and organic, wavy ripples.

## Recipe

Clones `wood` structurally unmodified, the same move `o03_tree_bark` uses, since dune ripples are organic and wavy, so the knot-warp chain is kept rather than straightened out the way `m02` aluminum straightens it. `perlin_2`'s scale is widened for broad, slow-rolling ripples instead of tight wood grain. Palette is a warm sand tan with high roughness.

No pitfall pass was needed for this material; `wood`'s own chain already produced correct relief unmodified, so no `param4=0` normal fix was required.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`:

- **Dune Ripples** -- `perlin_2`, `perlin_1`, `perlin_0`, `warp_0`,
  `voronoi_0`, `colorize_1`, `warp_1`, `blend_0`. This is the whole
  ripple-generating chain: `perlin_2` (the dune-ripple base) Multiplied
  against `wood`'s own unmodified grain-warp chain, kept unmodified per
  this recipe's own choice to clone `wood`'s structure as-is. None of that
  grain-warp chain's own parameters are builder-set, so it rides along
  with the pattern group instead of standing alone with zero exposed
  parameters. Exposed: `Ripple scale` (`perlin_2.scale_x`), `Ripple
  detail` (`perlin_2.iterations`).
- **Sand Finish** -- `colorize_2`, `colorize_0`, `normal_map_0`. Exposed:
  `Sand color` (`colorize_2.gradient`), `Surface sheen`
  (`colorize_0.gradient`).

Pre-existing wiring note, not touched by this retrofit: in the `wood`
donor, `blend_0` feeds the Material node's metallic port (port 1) DIRECTLY
-- unusual for a non-metal material, but this recipe never rewires it, so
the connection is preserved as-is (now a boundary port from Dune Ripples
straight to Material).

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
