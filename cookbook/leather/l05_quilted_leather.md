# l05_quilted_leather - Quilted or tufted leather

_Category: leather. Open the graph: `cookbook/leather/l05_quilted_leather.ptex`._

A saddle-tan grain base raised into a grid of puffy pads with recessed stitch-channel seams, the car-seat or chesterfield look.

## Recipe

Clones `crocodile_skin` for its base grain, but the quilt pads themselves come from the `pattern` node rather than the voronoi cells: two Sine waves multiplied (`x_wave`/`y_wave` = Sine, `mix` = Multiply, scale around 5) give a smooth grid of rounded pads that peak at the pad centers and fall to the seams, the quilt shape. Drive the normal from the pattern pads (`param1` around 0.9 for pronounced padding) with the crocodile grain blended on top at around 0.35 for fine detail, and darken the seams in albedo with a seam mask off the same pattern so the channels read as recessed.

Pitfall specific to this material: the natural way to lay down stitch dashes is a small `shape` repeated by `tiler`, but that approach fought back badly. In the full graph it produced no visible dashes, and isolating the tiler output to the albedo timed out the renderer at 180 seconds (a single centered shape through `tiler` builds a degenerate or expensive shader in this setup). The reliable path was the parameter-only `pattern` node instead, with no shape or tiler shader surprises. Honest gap: this delivers the quilt shape and channel seams but not individual per-stitch dash marks running along the seams. l06 in this cookbook solves the dash generator that l05 lacks.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. This
is one of the three materials in this category the blend-tracing caution is
about: it carries two `blend` nodes (`blend_h_q` for height, `blend_alb_q`
for albedo). Their port sources were traced from the serialized
`connections` list assembled in the builder, against `blend.mmg`'s own
shader model (ground truth): input `s1` is port0 (foreground), `s2` is port1
(background), `a` is port2 (mask), output = `mask*port0 + (1-mask)*port1`.
Traced wiring:

- `blend_h_q`: port0 ← `pattern_q` (the quilt pads), port1 ← `colorize_0`
  (grain height). Port2 (mask) has no connection at all, so it uses the
  node's own default of a constant `1.0` — this blend is a flat, unmasked
  `0.35*pads + 0.65*grain` mix, not a spatial composite.
- `blend_alb_q`: port0 (shown where mask=1) ← `colorize_1` (base grain);
  port1 (shown where mask=0) ← `seam_shade` (the dark constant); port2
  (mask) ← `seam_mask`.

Note for anyone tuning this graph: `seam_mask`'s gradient is 1 for low
`pattern_q` values and 0 for high ones, and the pattern's two-multiplied-sine
shape puts its high values in small, roughly circular regions at the pad
centers (visually confirmed against the render — regularly spaced dark
roundels, matching `x_scale=5`/`y_scale=5`) with lower values across the
broader area between them. So in the actual render, `colorize_1` (the base
grain, port0) covers the broader field and `seam_shade` (the near-black
constant, port1) appears in the smaller pad-center roundels — read as dark
button-tuft points on a grained field, not literally "dark seams / grain-
colored pad faces" as the recipe prose above describes. This is the
material's existing, already-shipped behavior (confirmed against the
pre-retrofit baseline render, not something this retrofit changed),
documented here factually since re-deriving the mask polarity is outside
this task's scope.

Opening the graph shows 4 top-level groups (plus `Material` and the
untouched metallic `uniform_0`) instead of the raw 11-node graph:

- **Leather Grain** — `voronoi_0`, `colorize_1`, `colorize_3`, and
  `colorize_0`. Unlike `l01`/`l03`/`l04`'s `_group_leather_grain` shape,
  `colorize_0` sits here rather than in a separate finish group: this
  builder rewires `normal_map_0`'s input away from `colorize_0` and onto
  `blend_h_q`'s output, so `colorize_0` no longer feeds `normal_map_0`
  directly and instead only feeds the quilt composite below. Exposed:
  `Leather color` (`colorize_1.gradient`), `Roughness`
  (`colorize_3.gradient`).
- **Quilt Pattern** — `pattern_q` alone. Exposed: `Quilt pad size`
  (`pattern_q.x_scale`).
- **Seam Shading** — `seam_mask`, `seam_shade`. Exposed: `Seam color`
  (`seam_shade.gradient`). The mask's own threshold gradient is not
  exposed, matching this project's standing convention for threshold masks.
- **Quilt Composite** — `blend_h_q`, `blend_alb_q`, and `normal_map_0`
  together, since `normal_map_0`'s only input is now `blend_h_q`'s output
  rather than a raw donor colorize. All of this group's external inputs come
  from **Leather Grain** (base albedo/height), **Quilt Pattern** (pad
  shape), and **Seam Shading** (mask/color) — the same all-external-inputs
  shape `f08_donegal_tweed`'s `fleck_composite` used. Exposed: `Quilt
  puffiness` (`blend_h_q.amount`), `Relief strength`
  (`normal_map_0.param1`).

`group_into_subgraph` preserves each incoming connection's own target port
independently when rehoming it through `gen_inputs`, so grouping cannot swap
which source lands on port0 vs port1 vs port2. Verified after building:
`renders_match` against this material's own pre-retrofit baseline came back
at an exact `grid_mean_abs_diff` of `0.0` on all three exported maps.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
