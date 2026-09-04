# l06_topstitched_leather - Topstitched leather

_Category: leather. Open the graph: `cookbook/leather/l06_topstitched_leather.ptex`._

Saddle grain leather with a grid of raised cream thread dashes in rows, the real per-stitch marks that l05's quilted card lacks. The dashes render bold and blocky rather than fine topstitch, and cover the full grid rather than following seam lines; judge in 3D.

## Recipe

Clones `crocodile_skin` for the base grain and, like l05, reaches for the `pattern` node for the repeated marks rather than a `shape`+`tiler` chain: a single centered `shape` through `tiler` again produced no visible dashes in the full graph and again timed out the renderer at 180 seconds when its output was isolated to albedo, so it stays ruled out for any repeated-mark grid.

The mechanism that works: `pattern` with `x_wave`/`y_wave` = Square and `mix` = Multiply makes the dash grid reliably in one node, with `x_scale`/`y_scale` setting the dash pitch.

Pitfall specific to this material: the pattern's polarity is inside-out. Its high (on) region is the connected field, and the isolated rectangles wanted as dashes are its low cells. Rendered straight, that put dark recessed marks on a flat thread-colored field, the exact inverse of stitches. Fix: a single reversed sharpen colorize (1 at the pattern's low, 0 at its high) so the mask is 1 at the dash marks, which corrects the color and un-flattens the field (the leather grain shows again) in one edit. With the mask right, the dashes drive a cream thread in albedo and a raised bump in the normal, blended over the grain height before `normal_map`, `param4=0`.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
