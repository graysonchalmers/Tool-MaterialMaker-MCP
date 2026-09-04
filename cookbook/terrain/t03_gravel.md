# t03_gravel - Gravel

_Category: terrain. Open the graph: `cookbook/terrain/t03_gravel.ptex`._

Loose scattered gravel at pebble scale with a wide earthy palette.

## Recipe

Clones `rock` and reuses `s02` granite's flat-per-cell-random lever (`voronoi_0` port 2, bypassing the smooth blend), but at pebble scale (14, versus granite's fine-fleck 44) with a wider earthy gray/tan/brown palette instead of granite's grayscale. `param4=0` relief is set stronger than granite's, since loose gravel is bumpier than a polished slab.

No pitfall pass was needed; this is a direct scale-and-palette retune of a proven lever from `s02` granite.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
