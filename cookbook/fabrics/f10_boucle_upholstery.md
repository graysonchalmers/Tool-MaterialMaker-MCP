# f10_boucle_upholstery - Boucle upholstery

_Category: fabrics. Open the graph: `cookbook/fabrics/f10_boucle_upholstery.ptex`._

A cream and heathered-gray bouclé upholstery weave: tight, irregular nubby
loops over a soft diagonal field, high matte roughness, and a rounded,
moderate relief that reads as soft loop texture rather than hard cell edges.

## Recipe

Clones `crocodile_skin` like the rest of this category, and like
`f09_plaid_flannel` and `l07_pebbled_leather` retypes the base generator to
`fbm` instead of keeping `voronoi_0` as a raw voronoi. Here it is `noise=6`
(Cellular 5, "soft diagonal weave" per `docs/AUTHORING.md`'s noise vocabulary
table -- "brushed cloth, quilted softness"). This is a different Cellular
index from both siblings, and each reads as a structurally different family:
Cellular 3 (f09) gives a hard crosshatch grid, Cellular 1 (l07) gives worley
cells with dark centers, Cellular 5 (this material) gives soft rounded blobs
with mild diagonal linking and no hard cell edges at all, the closest basis
in this catalog to bouclé's tight, irregular nubby loop texture.

Viewed the tracked `quality/cookbook/noise-gallery/fbm_6_cellular5` swatch
(fbm noise=6, scale 4, iterations=3, persistence=0.5, straight 0-black/
1-white ramp) directly before choosing params: at that diagnostic scale it
reads as a handful of large soft dark blobs on a lighter mid-gray field, with
faint diagonal connective haze between them, confirming the "soft diagonal
weave" character and confirming the same polarity documented for l07's
Cellular 1: low values sit at the blob centers, high values in the
surrounding field. `scale_x`/`scale_y` were raised from the brief's
diagnostic 4 to 28, higher than f09's plaid fix (10) or l07's pebble fix
(20), because bouclé loops read as much tighter and more numerous than a
plaid check or a pebbled-leather grain; at 28 the blobs shrink to a dense
field of small nubs rather than a few large blotches, the same "raise the
noise-gallery diagnostic scale for the actual material" move both those
builders made.

Palette is cream and heathered gray, distinct from `f04_wool_knit`'s warmer
oatmeal weave-donor ribs and from f09's navy/brick-red plaid: low value
(loop centers) gets a cream highlight for the loop tops catching light, high
value (the field between loops) shades to a cooler heather gray, with a mid
heather-beige stop for variation. Roughness is a high, low-contrast matte
ramp with no sheen split, a nubby upholstery weave has no glossy component,
unlike `f05_silk_satin`'s anisotropic sheen chain.

Relief is `normal_map` `param1=0.25`. The brief calls for LOW relief for a
"soft nubby bump rather than hard relief," but f09's first pass at the
brief's suggested-low 0.15 read as too flat on review and needed a second
iteration (raised to 0.42) to visibly read. 0.25 was chosen up front as a
value that should read clearly on a first pass: well above f09's
flat-reading 0.15, close to `f04_wool_knit`'s approved 0.3 for its rounded
ribs, while staying clearly softer than f09's final hard-crosshatch 0.42,
appropriate for bouclé's rounded, irregular loops rather than f09's straight
grid lines. This read correctly on the first render, no relief iteration was
needed. `param4=0` (the standing flat-normal fix for a directly-fed analytic
generator) stayed set throughout.

## Distinguishing it from f06/f09

`f06_velvet` is a continuous perlin fiber grain with no cell structure at
all, a smooth pile rather than loops. `f09_plaid_flannel` is a hard
crosshatch GRID from the same `fbm` family, straight lines crossing at right
angles. This material has neither: a soft, irregular, diagonal cell pattern
with no straight edges and no continuous fiber grain, the bouclé loop look.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via
the same shared `_group_weave_family` helper `f03`-`f09` use (this donor
carries no `blend` node, so no port-source tracing applies). Opening the
graph shows 2 top-level groups (plus `Material` and the untouched metallic
`NonMetallic`) instead of the raw 6-node graph:

- **Loop Pattern** - `BoucleLoop` (retyped to `fbm`, `noise=6`, `scale_x=28`,
  `scale_y=28`, `folds=0`, `iterations=3`, `persistence=0.5`) and
  `BoucleColor` (the cream/heather-gray loop albedo). `BoucleLoop` also feeds
  **Surface Finish**'s normal and roughness colorizes directly, the same
  shared-upstream-node shape the rest of this category's materials use.
  Exposed: `Loop density` (`BoucleLoop.scale_x`), `Boucle color`.
- **Surface Finish** - `BoucleHeight` (normal source, the donor's plain
  0-black/1-white ramp, unmodified), `BoucleRoughness` (high matte finish,
  no sheen), `BoucleNormal` (`param1=0.25`, `param4=0`, for a rounded,
  moderate loop relief). Exposed: `Roughness`, `Relief strength`.

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
| (top level) | loop_pattern | graph |
| (top level) | surface_finish | graph |
| loop_pattern | BoucleColor | colorize |
| loop_pattern | BoucleLoop | fbm |
| surface_finish | BoucleRoughness | colorize |
| surface_finish | BoucleHeight | colorize |
| surface_finish | BoucleNormal | normal_map |
<!-- nodes:end -->
