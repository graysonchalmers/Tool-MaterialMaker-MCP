# l06_topstitched_leather - Topstitched leather

_Category: leather. Open the graph: `cookbook/leather/l06_topstitched_leather.ptex`._

Saddle grain leather with a grid of raised cream thread dashes in rows, the real per-stitch marks that l05's quilted card lacks. The dashes render bold and blocky rather than fine topstitch, and cover the full grid rather than following seam lines; judge in 3D.

## Recipe

Clones `crocodile_skin` for the base grain and, like l05, reaches for the `pattern` node for the repeated marks rather than a `shape`+`tiler` chain: a single centered `shape` through `tiler` again produced no visible dashes in the full graph and again timed out the renderer at 180 seconds when its output was isolated to albedo, so it stays ruled out for any repeated-mark grid.

The mechanism that works: `pattern` with `x_wave`/`y_wave` = Square and `mix` = Multiply makes the dash grid reliably in one node, with `x_scale`/`y_scale` setting the dash pitch.

Pitfall specific to this material: the pattern's polarity is inside-out. Its high (on) region is the connected field, and the isolated rectangles wanted as dashes are its low cells. Rendered straight, that put dark recessed marks on a flat thread-colored field, the exact inverse of stitches. Fix: a single reversed sharpen colorize (1 at the pattern's low, 0 at its high) so the mask is 1 at the dash marks, which corrects the color and un-flattens the field (the leather grain shows again) in one edit. With the mask right, the dashes drive a cream thread in albedo and a raised bump in the normal, blended over the grain height before `normal_map`, `param4=0`.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. This
is one of the three materials in this category the blend-tracing caution is
about: it carries two `blend` nodes (`AlbedoComposite` for albedo,
`HeightComposite` for height). Their port sources were traced from the
serialized `connections` list assembled in the builder, against
`blend.mmg`'s own shader model (ground truth): input `s1` is port0
(foreground), `s2` is port1 (background), `a` is port2 (mask), output =
`mask*port0 + (1-mask)*port1`. Traced wiring:

- `AlbedoComposite`: port0 (shown where mask=1) ← `LeatherColor` (base
  grain); port1 (shown where mask=0) ← `ThreadColor` (cream thread color);
  port2 (mask) ← `StitchMask`. Since `StitchMask` is 1 at the dash marks
  (per the reversed-polarity fix described above), the render correctly
  shows the base grain covering most of the surface and the cream thread
  only at the dash marks — visually confirmed against the render, matching
  the recipe's stated intent for this material (unlike `l02`/`l05` in this
  same category, where the analogous trace comes out inverted from their
  prose).
- `HeightComposite`: port0 (mask=1) ← `GrainHeight` (grain height); port1
  (mask=0) ← `StitchMask` reused directly as the background VALUE, not
  routed through a separate height layer — the same node feeds both this
  port and its own mask port2. Net effect: grain height shows at the dash
  marks (mask=1) and the mask's own 0/1 value substitutes for height
  everywhere else (mask=0 region gets height ≈0, i.e. flat, since
  `1-mask=1` there and `StitchMask` itself is 0 there) — an economical way
  to both raise the dash marks and flatten the field between them without a
  third node.

Opening the graph shows 3 top-level groups (plus `Material` and the
untouched metallic `NonMetallic`) instead of the raw 11-node graph:

- **Leather Grain** — `PoreCells`, `LeatherColor`, `LeatherRoughness`, and
  `GrainHeight`. As with `l05`, `GrainHeight` sits here rather than in a
  separate finish group, since `LeatherNormal`'s input was rewired away
  from it and onto `HeightComposite`'s output. Exposed: `Leather color`
  (`LeatherColor.gradient`), `Roughness` (`LeatherRoughness.gradient`).
- **Stitch Pattern** — `StitchDashes`, `StitchMask`, and `ThreadColor`
  grouped together, since `ThreadColor`'s only input is `StitchMask`
  (internal) and its only output crosses the group boundary to
  `AlbedoComposite` — the same shape `f08_donegal_tweed` used to fold
  `colorize_fleck_color` in with its mask/generator rather than giving it a
  separate group. Exposed: `Stitch pitch` (`StitchDashes.x_scale`), `Thread
  color` (`ThreadColor.gradient`).
- **Stitch Composite** — `AlbedoComposite`, `HeightComposite`, and
  `LeatherNormal` together (mirroring `l05`'s `quilt_composite` shape),
  since `LeatherNormal`'s only input is now `HeightComposite`'s output.
  Exposed: `Stitch raise` (`HeightComposite.amount`), `Relief strength`
  (`LeatherNormal.param1`).

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
| (top level) | leather_grain | graph |
| (top level) | stitch_pattern | graph |
| (top level) | stitch_composite | graph |
| leather_grain | LeatherColor | colorize |
| leather_grain | LeatherRoughness | colorize |
| leather_grain | PoreCells | voronoi |
| leather_grain | GrainHeight | colorize |
| stitch_pattern | StitchDashes | pattern |
| stitch_pattern | StitchMask | colorize |
| stitch_pattern | ThreadColor | colorize |
| stitch_composite | LeatherNormal | normal_map |
| stitch_composite | AlbedoComposite | blend |
| stitch_composite | HeightComposite | blend |
<!-- nodes:end -->
