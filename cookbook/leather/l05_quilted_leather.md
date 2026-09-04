# l05_quilted_leather - Quilted or tufted leather

_Category: leather. Open the graph: `cookbook/leather/l05_quilted_leather.ptex`._

A saddle-tan grain base raised into a grid of puffy pads with recessed stitch-channel seams, the car-seat or chesterfield look.

## Recipe

Clones `crocodile_skin` for its base grain, but the quilt pads themselves come from the `pattern` node rather than the voronoi cells: two Sine waves multiplied (`x_wave`/`y_wave` = Sine, `mix` = Multiply, scale around 5) give a smooth grid of rounded pads that peak at the pad centers and fall to the seams, the quilt shape. Drive the normal from the pattern pads (`param1` around 0.9 for pronounced padding) with the crocodile grain blended on top at around 0.35 for fine detail, and darken the seams in albedo with a seam mask off the same pattern so the channels read as recessed.

Pitfall specific to this material: the natural way to lay down stitch dashes is a small `shape` repeated by `tiler`, but that approach fought back badly. In the full graph it produced no visible dashes, and isolating the tiler output to the albedo timed out the renderer at 180 seconds (a single centered shape through `tiler` builds a degenerate or expensive shader in this setup). The reliable path was the parameter-only `pattern` node instead, with no shape or tiler shader surprises. Honest gap: this delivers the quilt shape and channel seams but not individual per-stitch dash marks running along the seams. l06 in this cookbook solves the dash generator that l05 lacks.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
