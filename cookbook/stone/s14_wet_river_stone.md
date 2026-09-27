# s14_wet_river_stone - Wet river stone (river-pebble host)

_Category: stone. Open the graph: `cookbook/stone/s14_wet_river_stone.ptex`._

Dark, glossy river pebbles that look like they just came out of the water.
This is the dielectric reflection proof from the reflections cycle
(metallic 0, so every reflection comes from Godot's default specular
term). Since 2026-09-27 it is also the river-pebble host: one graph whose
feature layers reach the looks of `s06_river_pebbles`, `s04_scattered_river_stones`
and `t08_riverbed_pebbles` (all three retired into this host, 2026-09-27).

## Recipe

Clones `rock`, then:

- big voronoi cells (`PebbleCells`, scale 7) become rounded pebbles through
  s06's analytic coin-profile dome (cos, then clamp, then smoothstep). These
  are math nodes with no gradient stops, so the `param4=0` normal shows no
  ring banding;
- s06's two-scale mix: a finer voronoi (`SmallStoneCells`, 18) gets its own
  dome, nestled at 0.65 and max-composited, so small stones fill the big
  ones' seams. `StoneRandomMix` picks each pixel's stone (big or small) so
  one palette colours both sizes;
- `Top flatness` 1.0 (s06 uses 1.5) keeps some curvature on the tops;
- wet finish: a near-black palette, and roughness driven by the same height
  as the relief (glossy 0.08 in the crevices where water pools, 0.20 to
  0.38 on the tops), split into wet and damp patches by a large perlin
  (`PatchNoise`).

## Feature layers

Every layer defaults to 0, so the default graph renders exactly the wet
stone it did before the host work (a 2048 full-image diff of albedo,
normal and ORM against the pre-host graph: 0 pixels differ).

| Layer | Exposed params | What it does |
|---|---|---|
| Stone Profile: `Packing` (from `t08_riverbed_pebbles`) | `Packing` 0-1 | 0 = round pebbles (the dome reads the distance to each cell's seed). 1 = packed polygon plates (the dome reads the distance to the cell's straight border, so each stone fills its cell). `Top flatness` then sets how flat the plate tops are. |
| Dry Layer (from `s06_river_pebbles`) | `Dryness` 0-1, `Dry stone roughness`, `Dry seam roughness` | The wet/dry control. It blends the albedo from `Wet color` to `Dry color` (both in Stone Color), and the roughness from the wet finish to s06's dry finish: 0.42-0.60 on the tops, 0.86-0.93 grit in the seams, split by the relief height. 0.5 reads as damp stone. |
| Surface Grain (from `s06_river_pebbles`) | `Grain amount` 0-1, `Grain scale` | s06's fine perlin grain. One amount drives both the albedo speckle (multiplied, 0.82-1.0) and the relief grit (height + 0.15 x grain), so the colour grain and the bump grain are the same pixels. |
| Contact Gaps (from `t08_riverbed_pebbles`) | `Gap depth` 0-1 | t08's joint band (0.064 wide on the voronoi's border distance). One mask darkens the albedo toward black and cuts the relief, so a joint is dark exactly where it is recessed. |
| Sediment Bed (from `s04_scattered_river_stones`) | `Bed level` 0-1, `Bed color`, `Bed roughness` | Sand fills everything lower than `Bed level`, with a soft fillet (the mask ramps over the quarter of the height range below the level). One mask drives the albedo to s04's sand colour, the roughness to s04's sand roughness, and the relief up to a flat bed. Stones poke out of the sand, and the sand's colour edge is its relief edge. Higher level = fewer, smaller visible stones. |

Layer order is dry, grain, gaps, bed. Sand is last, so it fills the joints
and covers the grain.

`Wet color` and `Dry color` are the two palettes `Dryness` blends between.
Recolour a look by editing the palette that is active: `Wet color` at
Dryness 0, `Dry color` at Dryness 1.

### Presets

Set these on the collapsed nodes in Material Maker. Colors are gradient
stops (position: R, G, B in 0-1, then hex). Anything not listed stays at its
default. `Top flatness` (0-5) and `Grain scale` (1-160) have their own
slider ranges, wider than the math and perlin nodes they drive, so every
preset value below (Top flatness 1.5 and 4, Grain scale 128) is on the
slider.

**River pebbles, dry (s06):**
- `Dryness` = 1, `Grain amount` = 1, `Top flatness` = 1.5.
- That is all. The default `Dry color` is s06's palette, and this preset
  renders s06's maps exactly (0 pixels differ on albedo, normal and ORM).

**Scattered stones in sand (s04):**
- `Pebble size` = 9, `Small stone height` = 0, `Dryness` = 1,
  `Bed level` = 0.78, `Relief strength` = 0.35.
- `Dry color`: 0.0: 0.42, 0.40, 0.37 (`#6B665E`); 0.35: 0.58, 0.55, 0.50
  (`#948C80`); 0.65: 0.50, 0.49, 0.50 (`#807D80`); 1.0: 0.60, 0.56, 0.49
  (`#998F7D`).
- `Dry stone roughness`: 0.0: 0.42 gray; 1.0: 0.55 gray.
- `Bed color` and `Bed roughness` already default to s04's sand.
- Same stones in the same places as s04; the albedo matches (mean
  difference 0.6 of 255). The relief differs on purpose. s04 bumps every
  voronoi cell into a faceted pyramid, sand included. Here the sand is flat
  and only the stones are domed, because relief and colour share one mask.

**Riverbed plates (t08):**
- `Pebble size` = 8, `Small stone height` = 0, `Top flatness` = 4,
  `Packing` = 1, `Gap depth` = 0.6, `Grain amount` = 1, `Grain scale` = 128.
- `Wet color`: 0.0: 0.30, 0.30, 0.31 (`#4C4C4F`); 0.25: 0.52, 0.47, 0.40
  (`#857866`); 0.5: 0.34, 0.38, 0.42 (`#57616B`); 0.72: 0.44, 0.34, 0.26
  (`#705742`); 1.0: 0.62, 0.58, 0.52 (`#9E9485`).
- `Wet crevice roughness` and `Damp patch roughness`: flat 0.2 gray at both
  stops.
- The ORM map is identical to t08's. The plates sit in a different layout
  (t08's voronoi has a different seed), and the grit is softer than t08's
  harsh 10-octave relief noise.

**Back to the default wet stone:** set `Dryness`, `Grain amount`, `Gap
depth`, `Bed level` and `Packing` to 0, `Pebble size` 7, `Small stone height` 0.65, `Top flatness` 1.0, `Grain
scale` 40, `Relief strength` 0.6, and:
- `Wet color`: 0.0: 0.05, 0.05, 0.05 (`#0D0D0D`); 0.28: 0.10, 0.08, 0.07
  (`#1A1412`); 0.52: 0.14, 0.13, 0.12 (`#24211F`); 0.74: 0.09, 0.10, 0.11
  (`#171A1C`); 1.0: 0.06, 0.05, 0.05 (`#0F0D0D`).
- `Dry color` (s06): 0.0: 0.18, 0.17, 0.16 (`#2E2B29`); 0.28: 0.34, 0.30,
  0.26 (`#574C42`); 0.52: 0.52, 0.48, 0.42 (`#857A6B`); 0.74: 0.44, 0.45,
  0.47 (`#707378`); 1.0: 0.30, 0.27, 0.24 (`#4C453D`).
- `Wet crevice roughness`: 0.0: 0.08; 0.35: 0.14; 1.0: 0.20.
  `Damp patch roughness`: 0.0: 0.20; 0.35: 0.30; 1.0: 0.38.
- `Dry stone roughness`: 0.0: 0.42; 1.0: 0.60. `Dry seam roughness`: 0.0:
  0.86; 1.0: 0.93.
- `Bed color`: 0.0: 0.62, 0.54, 0.40 (`#9E8A66`); 1.0: 0.70, 0.62, 0.47
  (`#B29E78`). `Bed roughness`: 0.0: 0.78; 1.0: 0.85.

`Pebble size`, `Small stone size`, `Grain scale` and `Wet patch scale` each
set both scale_x and scale_y. `Top flatness` sets both stone sizes' domes.
`Grain scale` and `Top flatness` are named parameters: the inner nodes read
`$param1` / `$param2`, so one value drives both.

## Subgraph structure

The top level reads left to right as a layer stack: 9 subgraphs, then Material.

- **Pebble Pattern** (`PebbleCells`, `SurfaceNoise`, and the donor's orphaned
  `PebbleBlendUnused`). Exposed: `Pebble size`. Out: noise, cell distance,
  border distance, cell random.
- **Stone Profile** (the two dome chains, `PlateDistance`/`ShapeDelta`/
  `PackingOffset`/`DomeInput` for Packing, `StoneHeightMix`, `SmallStoneMask`,
  `StoneRandomMix`). Exposed: `Small stone size`, `Small stone height`, `Top
  flatness`, `Packing`. Out: height, and the per-stone random value.
- **Stone Color** (`WetStoneColor`, `DryStoneColor`). Exposed: `Wet color`,
  `Dry color`. Out: wet and dry albedo.
- **Wet Finish** (`NonMetallic`, `WetRoughness`, `DampPatchRoughness`,
  `PatchNoise`, `PatchMask`, `RoughnessPatchComposite`). Exposed: `Wet
  crevice roughness`, `Damp patch roughness`, `Wet patch scale`. Out:
  metallic (0), wet roughness.
- **Dry Layer**, **Surface Grain**, **Contact Gaps**, **Sediment Bed**: the
  layers in the table above. Each has one mask node (`Dryness`,
  `GrainAmount`, `ContactMask`, `BedMask`) that every one of its composites
  reads.
- **Relief** (`PebbleNormal`, strength 0.6). Exposed: `Relief strength`.

Seed-bearing noises keep their pre-host positions (`PebbleCells` and
`SurfaceNoise` where the `rock` donor put them; `SmallStoneCells`,
`PatchNoise` and `GrainNoise` at (0, 0) of their subgraphs), so moving
anything else around never reshuffles the stones.

## See also

`guide://authoring` (or `docs/AUTHORING.md`) for the `param4=0` fix and the
blend-polarity notes; `cookbook/metal/m02_brushed_metal.md` for the first
host material.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | pebble_pattern | graph |
| (top level) | stone_profile | graph |
| (top level) | stone_color | graph |
| (top level) | material_finish | graph |
| (top level) | dry_layer | graph |
| (top level) | surface_grain | graph |
| (top level) | contact_gaps | graph |
| (top level) | sediment_bed | graph |
| (top level) | relief | graph |
| pebble_pattern | SurfaceNoise | perlin |
| pebble_pattern | PebbleCells | voronoi |
| pebble_pattern | PebbleBlendUnused | blend |
| stone_profile | DomeCurve | math |
| stone_profile | DomeFlatten | math |
| stone_profile | DomeSmooth | math |
| stone_profile | PlateDistance | math |
| stone_profile | ShapeDelta | math |
| stone_profile | PackingOffset | math |
| stone_profile | DomeInput | math |
| stone_profile | SmallStoneCells | voronoi |
| stone_profile | SmallDomeCurve | math |
| stone_profile | SmallDomeFlatten | math |
| stone_profile | SmallDomeSmooth | math |
| stone_profile | SmallStoneHeight | math |
| stone_profile | StoneHeightMix | math |
| stone_profile | SmallStoneMask | math |
| stone_profile | StoneRandomMix | blend |
| stone_color | WetStoneColor | colorize |
| stone_color | DryStoneColor | colorize |
| material_finish | NonMetallic | colorize |
| material_finish | WetRoughness | colorize |
| material_finish | DampPatchRoughness | colorize |
| material_finish | PatchNoise | perlin |
| material_finish | PatchMask | colorize |
| material_finish | RoughnessPatchComposite | blend |
| dry_layer | Dryness | uniform_greyscale |
| dry_layer | DryColorComposite | blend |
| dry_layer | DryStoneRoughness | colorize |
| dry_layer | DrySeamRoughness | colorize |
| dry_layer | DryRoughnessMix | blend |
| dry_layer | DryRoughnessComposite | blend |
| surface_grain | GrainNoise | perlin |
| surface_grain | GrainContrast | colorize |
| surface_grain | GrainAmount | uniform_greyscale |
| surface_grain | GrainColorComposite | blend |
| surface_grain | GrainWeight | math |
| surface_grain | GrainHeight | math |
| surface_grain | GrainReliefHeight | math |
| contact_gaps | ContactEdges | colorize |
| contact_gaps | GapDepth | uniform_greyscale |
| contact_gaps | ContactMask | math |
| contact_gaps | GapShade | uniform |
| contact_gaps | ContactColorComposite | blend |
| contact_gaps | ContactHeightKeep | math |
| contact_gaps | ContactHeight | math |
| sediment_bed | BedLevel | uniform_greyscale |
| sediment_bed | BedDepth | math |
| sediment_bed | BedRamp | math |
| sediment_bed | BedMask | math |
| sediment_bed | BedColor | colorize |
| sediment_bed | BedRoughness | colorize |
| sediment_bed | BedColorComposite | blend |
| sediment_bed | BedRoughnessComposite | blend |
| sediment_bed | BedFill | math |
| sediment_bed | BedHeight | math |
| relief | PebbleNormal | normal_map |
<!-- nodes:end -->
