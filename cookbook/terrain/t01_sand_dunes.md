# t01_sand_dunes - Sand dunes

_Category: terrain. Open the graph: `cookbook/terrain/t01_sand_dunes.ptex`._

Broad, slow-rolling sand dunes with warm tan tone and organic, wavy ripples.

## Recipe

Clones `wood` structurally unmodified, the same move `o03_tree_bark` uses, since dune ripples are organic and wavy, so the knot-warp chain is kept rather than straightened out the way `m02` aluminum straightens it. `perlin_2`'s scale is widened for broad, slow-rolling ripples instead of tight wood grain. Palette is a warm sand tan with high roughness.

No pitfall pass was needed for this material; `wood`'s own chain already produced correct relief unmodified, so no `param4=0` normal fix was required.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
