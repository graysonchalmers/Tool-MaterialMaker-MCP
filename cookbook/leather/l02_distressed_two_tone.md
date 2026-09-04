# l02_distressed_two_tone - Distressed two-tone worn leather

_Category: leather. Open the graph: `cookbook/leather/l02_distressed_two_tone.ptex`._

A dark saddle base leather with a lighter rubbed tan showing through irregular worn patches, for both albedo and a small roughness lift.

## Recipe

Clones `crocodile_skin` and uses the masked-composite lever (the same shape as other two-layer weathering recipes in this cookbook), but here both layers are leather rather than two different materials. The wear mask is the entire recipe: it decides whether the result reads as genuine wear or as animal-print spots.

Pitfall: the first pass used a coarse perlin (scale 7) with a narrow threshold band and a big base-versus-worn tonal gap, which produced a few giant high-contrast blotches that read as cow-hide spots, not wear. Fixed with a finer perlin (scale 16, iterations 6), a wide feathered threshold band (0.40 to 0.72), and a small tonal gap between base and worn, so the rubs read as a distributed change of finish rather than a second color. When a wear or distress mask is producing blotches instead of gradual wear, widen the band and shrink both the noise scale and the tonal gap together, not just one of the three.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. This
is one of the three materials in this category the blend-tracing caution is
about: it carries two `blend` nodes (`blend_alb`, `blend_rgh`), both sharing
the same mask. Their port sources were traced from the serialized
`connections` list assembled in the builder, against `blend.mmg`'s own
shader model (ground truth, read directly from
`z-Git/material-maker/addons/material_maker/nodes/blend.mmg`): input `s1` is
port0 (foreground), `s2` is port1 (background), `a` is port2 (mask), and the
output is `mask*port0 + (1-mask)*port1`. Traced wiring:

- `blend_alb`: port0 (shown where mask=1) ← `colorize_1` (base grain
  albedo); port1 (shown where mask=0) ← `worn_alb`; port2 (mask) ←
  `colorize_wm`.
- `blend_rgh`: port0 (shown where mask=1) ← `colorize_3` (base roughness);
  port1 (shown where mask=0) ← `worn_rgh`; port2 (mask) ← `colorize_wm`
  (the same mask feeds both blends).

Note for anyone tuning this graph: given `colorize_wm`'s threshold shape
(ramping 0→1 between perlin values 0.40 and 0.72), the mask value is 1 only
in the smaller high-perlin region and 0 across the broader remainder — so in
the actual render, `worn_alb`/`worn_rgh` (port1) covers most of the visible
surface and `colorize_1`/`colorize_3` (port0, the "base" tone) shows through
in the smaller high-perlin patches, the reverse of which layer the recipe
prose above calls "base" versus "showing through." This is the material's
existing, already-shipped behavior (confirmed against the pre-retrofit
baseline render, not something this retrofit changed), documented here
factually rather than re-litigated, since fixing the mask polarity is
outside this task's scope.

Opening the graph shows 4 top-level groups (plus `Material` and the
untouched metallic `uniform_0`) instead of the raw 13-node graph:

- **Grain Pattern** / **Surface Finish** — the same 2-group split as
  `l01_black_oiled_leather` (via the shared `_group_leather_grain` helper):
  `voronoi_0`+`colorize_1` (Exposed: `Base leather color`), and
  `colorize_0`+`colorize_3`+`normal_map_0` (Exposed: `Base roughness`,
  `Relief strength`). `colorize_1`/`colorize_3`'s outputs now feed
  `blend_alb`/`blend_rgh` instead of `Material` directly, but the grouping
  mechanism handles that the same way regardless of the outgoing
  connection's destination.
- **Wear Pattern** — `perlin_wm`, `colorize_wm` (the mask), `worn_alb`,
  `worn_rgh`. Exposed: `Wear pattern scale` (`perlin_wm.scale_x`), `Worn
  color` (`worn_alb.gradient`).
- **Wear Composite** — `blend_alb`, `blend_rgh` together, since both inputs
  to each are external (majority/base from **Grain Pattern**/**Surface
  Finish**, worn tone and mask from **Wear Pattern**) — the same
  all-external-inputs shape `f08_donegal_tweed`'s `fleck_composite` used.
  Exposed: `Wear blend strength` (`blend_alb.amount`).

`group_into_subgraph` preserves each incoming connection's own target port
independently when rehoming it through `gen_inputs`, so grouping cannot swap
which source lands on port0 vs port1 vs port2. Verified after building:
`renders_match` against this material's own pre-retrofit baseline came back
at an exact `grid_mean_abs_diff` of `0.0` on all three exported maps.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
