# l02_distressed_two_tone - Distressed two-tone worn leather

_Category: leather. Open the graph: `cookbook/leather/l02_distressed_two_tone.ptex`._

A dark saddle base leather with a lighter rubbed tan showing through irregular worn patches, for both albedo and a small roughness lift.

## Recipe

Clones `crocodile_skin` and uses the masked-composite lever (the same shape as other two-layer weathering recipes in this cookbook), but here both layers are leather rather than two different materials. The wear mask is the entire recipe: it decides whether the result reads as genuine wear or as animal-print spots.

Pitfall: the first pass used a coarse perlin (scale 7) with a narrow threshold band and a big base-versus-worn tonal gap, which produced a few giant high-contrast blotches that read as cow-hide spots, not wear. Fixed with a finer perlin (scale 16, iterations 6), a wide feathered threshold band (0.40 to 0.72), and a small tonal gap between base and worn, so the rubs read as a distributed change of finish rather than a second color. When a wear or distress mask is producing blotches instead of gradual wear, widen the band and shrink both the noise scale and the tonal gap together, not just one of the three.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. This
is one of the three materials in this category the blend-tracing caution is
about: it carries two `blend` nodes (`AlbedoComposite`, `RoughnessComposite`),
both sharing the same mask. Their port sources were traced from the serialized
`connections` list assembled in the builder, against `blend.mmg`'s own
shader model (ground truth, read directly from
`z-Git/material-maker/addons/material_maker/nodes/blend.mmg`): input `s1` is
port0 (foreground), `s2` is port1 (background), `a` is port2 (mask), and the
output is `mask*port0 + (1-mask)*port1`. Traced wiring:

- `AlbedoComposite`: port0 (shown where mask=1) ← `WornColor` (the scattered
  rubs); port1 (shown where mask=0) ← `LeatherColor` (base grain albedo, the
  majority); port2 (mask) ← `RubMask`.
- `RoughnessComposite`: port0 (shown where mask=1) ← `WornRoughness` (rubbed
  roughness); port1 (shown where mask=0) ← `LeatherRoughness` (base
  roughness, the majority); port2 (mask) ← `RubMask` (the same mask feeds
  both blends).

Polarity fix (2026-09-04): `RubMask`'s threshold ramps 0→1 between perlin
values 0.40 and 0.72, so the mask is 1 only in the smaller high-perlin region
and 0 across the broader remainder. The worn tone is therefore the MINORITY
(scattered rubs) and belongs on port0 (shown where mask=1), while the dark
saddle base is the MAJORITY and belongs on port1 (shown where mask=0). The
original wiring had these reversed, so the lighter worn tan covered most of
the hide and the dark base showed through only in small patches — backwards
from this recipe's own description. Both blends were swapped; a before/after
render confirmed the field flipped from mostly-light to mostly-dark-saddle
with lighter worn rubs scattered through it. As a bonus, the exposed `Wear
blend strength` (`AlbedoComposite.amount`) now controls what its label
claims, since port0 is finally the wear layer.

Opening the graph shows 4 top-level groups (plus `Material` and the
untouched metallic `NonMetallic`) instead of the raw 13-node graph:

- **Grain Pattern** / **Surface Finish** — the same 2-group split as
  `l01_black_oiled_leather` (via the shared `_group_leather_grain` helper):
  `PoreCells`+`LeatherColor` (Exposed: `Base leather color`), and
  `GrainHeight`+`LeatherRoughness`+`LeatherNormal` (Exposed: `Base
  roughness`, `Relief strength`). `LeatherColor`/`LeatherRoughness`'s
  outputs now feed `AlbedoComposite`/`RoughnessComposite` instead of
  `Material` directly, but the grouping mechanism handles that the same way
  regardless of the outgoing connection's destination.
- **Wear Pattern** — `RubNoise`, `RubMask` (the mask), `WornColor`,
  `WornRoughness`. Exposed: `Wear pattern scale` (`RubNoise.scale_x`), `Worn
  color` (`WornColor.gradient`).
- **Wear Composite** — `AlbedoComposite`, `RoughnessComposite` together,
  since both inputs to each are external (majority/base from **Grain
  Pattern**/**Surface Finish**, worn tone and mask from **Wear Pattern**) —
  the same all-external-inputs shape `f08_donegal_tweed`'s
  `fleck_composite` used. Exposed: `Wear blend strength`
  (`AlbedoComposite.amount`).

`group_into_subgraph` preserves each incoming connection's own target port
independently when rehoming it through `gen_inputs`, so grouping cannot swap
which source lands on port0 vs port1 vs port2. Verified after building:
`renders_match` against this material's own pre-retrofit baseline came back
at an exact `grid_mean_abs_diff` of `0.0` on all three exported maps.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | NonMetallic | uniform |
| (top level) | grain_pattern | graph |
| (top level) | surface_finish | graph |
| (top level) | wear_pattern | graph |
| (top level) | wear_composite | graph |
| grain_pattern | LeatherColor | colorize |
| grain_pattern | PoreCells | voronoi |
| surface_finish | LeatherRoughness | colorize |
| surface_finish | GrainHeight | colorize |
| surface_finish | LeatherNormal | normal_map |
| wear_pattern | RubNoise | perlin |
| wear_pattern | RubMask | colorize |
| wear_pattern | WornColor | colorize |
| wear_pattern | WornRoughness | colorize |
| wear_composite | AlbedoComposite | blend |
| wear_composite | RoughnessComposite | blend |
<!-- nodes:end -->
