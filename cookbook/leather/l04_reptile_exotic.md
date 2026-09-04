# l04_reptile_exotic - Exotic reptile scale

_Category: leather. Open the graph: `cookbook/leather/l04_reptile_exotic.ptex`._

An exotic bronze-olive reptile scale leather with fewer, bigger, slightly elongated scales and strong relief, so the scale edges cast real depth rather than reading as a fine uniform grain.

## Recipe

Clones `crocodile_skin` and leans into the voronoi cell scale rather than keeping the donor's default fine grain: drop `voronoi_0` scale to around 7x9 for fewer, bigger, slightly elongated scales, recolor to an exotic bronze-olive, and use strong relief (`param1` around 0.7, still `param4=0`).

Pitfall, and the one specific to this card: the albedo ramp hit the same voronoi port-0 polarity trap the height ramp needs fixing on every cell-based leather here, but it matters more for this material because the color contrast is high (unlike the near-monochrome l01). `colorize_1` is fed by `voronoi_0` port 0, which is low at the cell centers (the scale bodies) and high at the borders. The first pass mapped low to dark and high to bronze, so the scale bodies came out dark and only the thin border seams got color, reading olive with no bronze at all. Fix: reverse the ramp too, centers to bronze-olive body, borders to dark seam, so the scales carry the color and the seams read as dark grooves. Also dropped the roughness from semi-gloss to a drier matte, since the semi-gloss pass read wet or plastic. Remaining open knob: the bronze still skews olive because the voronoi field rarely reaches the ramp's top stop.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via
the same shared `_group_leather_grain` helper as `l01`/`l03`. Per the task's
blend caution, this builder was specifically checked for a `blend` node
despite echoing the `o04_snake_scales`/`o05_coral` naming family from
`cookbook_organics.py` (both of which also clone `crocodile_skin`) — it has
none, confirmed by reading through the builder's own connections (it only
recolors and retunes `voronoi_0`'s scale, the same shape as `l01`). Opening
the graph shows 2 top-level groups (plus `Material` and the untouched
metallic `uniform_0`) instead of the raw 7-node graph:

- **Grain Pattern** — `voronoi_0` (`scale_x=7`, `scale_y=9`, `intensity=0.6`
  — fewer, bigger, elongated scales) and `colorize_1` (the bronze-olive
  scale albedo, with the reversed polarity described above). Exposed:
  `Scale size` (`voronoi_0.scale_x`, explicitly tuned here unlike `l01`,
  which never touches it), `Scale color`.
- **Surface Finish** — `colorize_0` (height, domed), `colorize_3` (matte
  finish), `normal_map_0` (`param1=0.7`, `param4=0`, for strong scale-edge
  relief). Exposed: `Finish`, `Scale relief`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0` on
all three exported maps.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
