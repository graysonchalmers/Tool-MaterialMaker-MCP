# s13_polished_marble - Polished marble

_Category: stone. Open the graph: `cookbook/stone/s13_polished_marble.ptex`._

Classic white/gray Carrara marble: a light polished field with darker cool-gray veins running through it. Moved in from the terrain category (was `t09_marbled_silt`) after Grayson's verdict on that render: the fbm-turbulence swirl reads as marble, so embrace it rather than keep it as a terrain "dried mineral wash" material.

## Recipe

Same donor and base technique as `t09_marbled_silt` (`crocodile_skin`, `voronoi_0` retyped to `fbm`, Perlin basis with `folds` for turbulence): this material exists specifically to prove the fbm-turbulence base is reusable for real stone, not just terrain, so the noise chain is kept intact and only retuned, not rebuilt.

Retuned from the terrain version: `folds` dropped 3 -> 2 and `scale_x`/`scale_y` dropped 4 -> 3, for fewer, larger, more meandering veins -- the terrain values leaned toward tight, closely-spaced folds that read as onion-ring banding rather than long sweeping marble veins.

**Vein-character fix (this pass)**: Grayson's verdict on that first Carrara render was TERRAZZO/speckled granite, not flowing veins. Two causes, both fixed without changing the donor or the fbm-turbulence approach:

1. `scale_x`/`scale_y` dropped again, 3 -> 1.8 (a smaller MM scale number makes larger features), so the folded field produces only a handful of large meandering ridges across the surface instead of many small ones. `folds` bumped 2 -> 3 so the ridge geometry itself meanders more. `iterations` dropped 5 -> 4 to hold fine-octave graininess down and keep the extra fold complexity from reintroducing speckle.
2. The albedo gradient's dark/transition region used to eat about 56% of the fbm value range (0.0-0.28 and 0.72-1.0), so a wide swath of the field rendered as some shade of gray -- reading as scattered dark flecks rather than a few thin lines. Narrowed the vein-plus-transition band to 12% at each extreme (0.0-0.12 and 0.88-1.0) and widened the near-white plateau to 76% of the range (0.12-0.88) so only the sparse fold extremes go dark.

Palette shifts from terrain's warm tan/rust to classic white/gray Carrara: a near-white base plateau (~0.86-0.90) now spans the wide 0.12-0.88 middle of the gradient, with a charcoal-grey vein core (~0.16-0.17, darker than the first pass's cool-gray 0.32-0.35 so the thin lines read as crisp dark strokes) confined to a narrow band at each extreme (0.0-0.05, 0.95-1.0) with a short transition (0.05-0.12, 0.88-0.95). The base is deliberately LIGHT and the veins DARKER, thin, and sparse, not a 50/50 split -- a 50/50 warm-toned version of this same shape read as burl wood, and the first Carrara pass's too-broad transition read as terrazzo.

Roughness (`MarbleRoughness`) reads the same raw `fbm` field the albedo does (this donor's shape feeds `colorize_0`/`colorize_1`/`colorize_3` all straight from `voronoi_0` port 0, so no extra rewiring was needed) with a genuine roughness TEXTURE, not a bare scalar: a polished-marble band around 0.20 across the base field, rising slightly to 0.30 at the vein bands, so an ORM map exports and the veins read a touch rougher than the polished field, matching how real ground-and-polished stone takes the polish slightly differently at the veins. Its gradient breakpoints (0.05/0.12/0.88/0.95) mirror the retuned albedo gradient's so the rougher band lines up with the vein band. Metallic stays 0 via the untouched `NonMetallic` uniform (marble is a dielectric). Relief (`MarbleNormal`) drops `param1` from terrain's 0.25 to 0.08 (`param4=0` unchanged, the standing flat-normal fix) -- polished marble is nearly flat, so the veins are the faintest whisper of relief, not a gentle terrain swell.

## Difference from s11_marble

`s11_marble` (the existing masonry-family marble) warps `dry_earth`'s voronoi crack network hard (`warp_0.amount=0.5`) to turn cell borders into flowing veins -- "the flow IS the look" per that builder's docstring. `s13_polished_marble` has no voronoi node anywhere: its veins come from a folded `fbm` turbulence field instead. Keeping both gives the stone category two structurally distinct routes to a marble look, which is the reason this material was moved into stone rather than discarded when the terrain slot moved on to a different material.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, the same `crocodile_skin`-donor template as `t07_forest_floor` and the former `t09_marbled_silt`:

- **Marble Veins** -- `VeinColor`, `MarbleVeins` (retyped to `fbm`, Perlin basis with `folds=3`, `scale_x`/`scale_y=1.8`, `iterations=4`). Exposed: `Vein scale` (`MarbleVeins.scale_x`), `Vein color` (`VeinColor.gradient`).
- **Polished Finish** -- `MarbleRoughness`, `MarbleHeight`, `MarbleNormal`. Exposed: `Roughness` (`MarbleRoughness.gradient`), `Vein relief` (`MarbleNormal.param1`).

`NonMetallic` (the untouched metallic-0 scalar, feeding Material port 1 directly) stays top-level, matching the same precedent used elsewhere for untouched single-purpose scalar nodes.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for the rubric, the authoring workflow, the noise vocabulary, and the `param4=0` flat-normal fix.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | NonMetallic | uniform |
| (top level) | marble_veins | graph |
| (top level) | polished_finish | graph |
| marble_veins | VeinColor | colorize |
| marble_veins | MarbleVeins | fbm |
| polished_finish | MarbleRoughness | colorize |
| polished_finish | MarbleHeight | colorize |
| polished_finish | MarbleNormal | normal_map |
<!-- nodes:end -->
