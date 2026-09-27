# m02_brushed_metal - Brushed metal

_Category: metal. Open the graph: `cookbook/metal/m02_brushed_metal.ptex`._

Prompt: "brushed aluminum". A Phase-3 hero material (frozen 15-case test
set), folded into the cookbook 2026-09-05 as one of the two founding members
of the bare-metal category.

## Recipe

The first attempt cloned `rock` and stretched its perlin; the streaks were
soft and the normal rendered flat. The structural insight that fixed it:
brushed metal is directional streaks WITH relief, which is exactly what wood
grain is. So clone `wood`, whose `perlin_2` (scale 32 x 4) is a directional
generator already feeding a working normal chain, and:

- straighten the grain: feed `blend_0`'s second input from the straight
  `perlin_2` instead of the knot warp, so streaks run parallel;
- finer, longer streaks (raise `scale_x`, drop `scale_y`, 8 iterations);
- neutralize albedo to aluminum gray (`colorize_2`), no wood tint;
- force uniform full metallic by dropping the grain-driven metallic wire so
  Material's scalar metallic=1 applies;
- low brushed roughness with streak-driven anisotropy (`colorize_0`);
- shallow brush relief: `normal_map_0` with the `param4=0` fix at low
  strength.

## Feature layers

Since 2026-09-27 this is the brushed-metal host: one graph that carries
three optional layers, each taken from a one-trick material and kept as real
nodes. Every layer defaults to 0, so the default graph renders the same
brushed aluminum as before.

| Layer | Exposed param | What it does |
|---|---|---|
| Hairline Layer (from the retired `m03_brushed_titanium`) | `Hairline fineness` 0-1 | m03's `noise_anisotropic` hairline (same params, rotated 90 degrees so it runs along the streak) blended over the streak. 0 = the coarse, grainy aluminum streak, 1 = m03's smooth fine hairline. Color, roughness and relief all read the blended signal, so they stay lined up. |
| Polish Layer (from the retired `m05_polished_chrome`) | `Polish` 0-1 | Pulls roughness toward m05's mirror band (0.06-0.14) and polishes the brush relief flat; at 1 the brush relief is gone completely. |
| Scratch Wear (from the retired `m04_scratched_steel`) | `Scratch amount` 0-1, `Scratch randomness`, `Scratch length` | m04's `scratches` node. One mask drives three things at the same pixels: a slight brightening (a fresh cut), roughness raised toward m04's 0.6, and a groove cut into the relief. |

The scratch layer sits after the polish layer, so scratches also cut
through a polished surface. Two things differ from the originals on
purpose. The hairline runs vertically with the streak, where m03's runs
horizontally (`noise_anisotropic` only streaks along x). Scratches are cut
in (grooves), where m04's read as raised lines.

### Presets

Set these on the collapsed nodes in Material Maker. Colors are given as
gradient stops (position: R, G, B in 0-1, then hex).

**Brushed titanium (m03):**
- `Hairline fineness` = 1.
- `Metal color`: 0.0: 0.58, 0.56, 0.62 (`#948F9E`); 1.0: 0.66, 0.64, 0.70
  (`#A8A3B2`).
- `Roughness`: 0.0: 0.22 gray; 1.0: 0.38 gray.

**Scratched steel (m04):**
- `Scratch amount` = 0.7.
- `Metal color`: 0.0: 0.30, 0.31, 0.33 (`#4C4F54`); 0.5: 0.40, 0.41, 0.44
  (`#666970`); 1.0: 0.50, 0.52, 0.55 (`#80858C`).
- `Roughness`: flat 0.6 gray at both stops.
- Optional: add `Hairline fineness` = 1 for a smoother base. The scratches
  then read bolder, but you get visible vertical banding.

**Polished chrome (m05):**
- `Polish` = 1.
- `Metal color`: 0.0: 0.82, 0.84, 0.88 (`#D1D6E0`); 1.0: 0.90, 0.92, 0.96
  (`#E6EBF5`).
- Leave `Roughness` alone, because Polish replaces it.

To get back to the default aluminum, set every layer to 0 and set
`Metal color` back to 0.0: 0.56 (`#8F8F8F`), 0.5: 0.67 (`#ABABAB`),
1.0: 0.78 (`#C7C7C7`), with `Roughness` 0.0: 0.20, 1.0: 0.40.

## Subgraph structure

Opening the graph shows a left-to-right layer stack. There are 8 top-level
nodes instead of 28.

- **Brushed Finish** (`StreakNoise`, `StreakComposite`). Exposed: `Streak
  length`, `Streak density`. Output: the streak signal.
- **Hairline Layer** (`HairlineNoise`, `HairlineAlign`, `BrushComposite`).
  Exposed: `Hairline fineness`. Streak in, brush signal out.
- **Metal Color** (`MetalColor`, `RoughnessRamp`). Exposed: `Metal color`,
  `Roughness`. Brush signal in, albedo and roughness out.
- **Polish Layer** (`PolishRoughness`, `PolishMask`, `FlatHeight`,
  `PolishRoughnessComposite`, `PolishHeightComposite`). Exposed: `Polish`.
  `PolishMask` is the opacity of both composites. Out: roughness and height.
- **Scratch Wear** (`ScratchNoise`, `ScratchMask`, `ScratchTint`,
  `ScratchColorComposite`, `ScratchRoughness`, `ScratchRoughnessComposite`,
  `GrooveHeight`, `ScratchHeightComposite`). Exposed: `Scratch amount`,
  `Scratch randomness`, `Scratch length`. `ScratchMask` (the scratches times
  `Scratch amount`) is the opacity of all three composites. Out: albedo,
  roughness and height.
- **SurfaceNormal** is a plain top-level `normal_map`, not a subgraph. Its
  strength (0.45) scales the brush relief and the scratch grooves together.
- **Wood Donor Leftover (unused)** (`KnotNoiseUnused`, `KnotWarpNoiseUnused`, `KnotWarpUnused`,
  `KnotCellsUnused`, `KnotColorUnused`, `KnotWarpFinalUnused`). Wood's knot-warp chain, disconnected
  by the straightening rewire; it feeds nothing. Kept and labeled rather than
  deleted so the graph still shows how a wood grain became a brushed finish.
  Delete it freely if you are editing this material for real.
- **Material**, the output.

## See also

`guide://authoring` (or `docs/AUTHORING.md`) for the `param4=0` fix and the
"pick the base by topology" lesson; `docs/evidence/phase3/2026-08-26-iter1.md`.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | SurfaceNormal | normal_map |
| (top level) | brushed_finish | graph |
| (top level) | hairline_layer | graph |
| (top level) | metal_color | graph |
| (top level) | polish_layer | graph |
| (top level) | scratch_wear | graph |
| (top level) | wood_knot_leftover | graph |
| brushed_finish | StreakNoise | perlin |
| brushed_finish | StreakComposite | blend |
| hairline_layer | HairlineNoise | noise_anisotropic |
| hairline_layer | HairlineAlign | rotate |
| hairline_layer | BrushComposite | blend |
| metal_color | MetalColor | colorize |
| metal_color | RoughnessRamp | colorize |
| polish_layer | PolishMask | uniform_greyscale |
| polish_layer | PolishRoughness | colorize |
| polish_layer | PolishRoughnessComposite | blend |
| polish_layer | FlatHeight | uniform_greyscale |
| polish_layer | PolishHeightComposite | blend |
| scratch_wear | ScratchNoise | scratches |
| scratch_wear | ScratchMask | math |
| scratch_wear | ScratchTint | uniform |
| scratch_wear | ScratchColorComposite | blend |
| scratch_wear | ScratchRoughness | uniform_greyscale |
| scratch_wear | ScratchRoughnessComposite | blend |
| scratch_wear | GrooveHeight | uniform_greyscale |
| scratch_wear | ScratchHeightComposite | blend |
| wood_knot_leftover | KnotWarpNoiseUnused | perlin |
| wood_knot_leftover | KnotNoiseUnused | perlin |
| wood_knot_leftover | KnotWarpUnused | warp |
| wood_knot_leftover | KnotColorUnused | colorize |
| wood_knot_leftover | KnotWarpFinalUnused | warp |
| wood_knot_leftover | KnotCellsUnused | voronoi |
<!-- nodes:end -->
