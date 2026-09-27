# s07_cobblestone - True irregular cobblestone

_Category: stone. Open the graph: `cookbook/stone/s07_cobblestone.ptex`._

True irregular cobblestone with genuinely varied plate sizes and recessed mortar. Closes the gap `s05_hex_stone_tile` left open: this is the voronoi-plate approach that card's own notes flagged as untried.

## Recipe

Clones `dry_earth`, scales `voronoi_0` from 4 to 6 (cobble-sized plates), and feeds `voronoi_0` port 2 (per-cell random) through a multi-tone stone gradient rewired into `blend_0` port 1 in place of the flat perlin earth base, so each plate reads as a distinct stone while the existing warped-crack Multiply overlay reads as recessed mortar. `warp_0.amount` is dropped to 0.12 for clean thin mortar with a slight organic wobble.

Pitfall specific to this material: two traps cost a pass each. First, the initial tone gradient was too narrow (0.30 to 0.55, muted) so plates all looked uniform; it needed widening hard across both value and hue. Second, a broad gray haze inside the plates was mistaken for a gradient problem, but it was actually `dry_earth`'s stock `warp_0.amount` of 0.4 smearing the crack shadows into washes across the plates, fixed by dropping that value to 0.12. Judge the result in 3D with `render_preview`: the cobbles should bulge and the mortar should recess.

## Subgraph structure

The paved-stone host (2026-09-27). It absorbs `s08_dry_stone_wall` and
`s10_flagstone` (both retired into it 2026-09-27), which are this same `dry_earth` graph with different
parameters and no node of their own. Six groups, left to right into
Material:

- **Stone Layout**: `PlateCells`, the joint band (`JointScale`,
  `PlateEdges`, `JointWarp`, `JointWarpNoise`) and the per-stone tone
  (`ToneWarp`, `StoneTone`). Exposed: `Stone size` (drives `scale_x` and
  `scale_y`), `Joint width`, `Tones follow joints`.
- **Stone Color**: `StoneColor`, `JointComposite` (dark joint shade),
  `StoneMetallic` (dry_earth's 0-0.52 metallic variation, unchanged).
  Exposed: `Stone color`, `Joint depth`.
- **Stone Surface**: `ReliefNoiseFine` and the top-flatness math. Exposed:
  `Top flatness`.
- **Mortar**: exposed `Mortar fill`, `Mortar color`.
- **Surface Grain**: exposed `Grain scale` (both axes), `Grain contrast`.
- **Relief**: `ReliefRamp`, `ReliefComposite`, `ReliefHeight`,
  `StoneNormal`. Exposed: `Relief strength`.

**`JointWarp` caution** still holds: its `amount` (0.12) is not exposed. At
the donor's 0.4 it smears the joint shadows into a haze across the stones.

## Feature layers

Every layer defaults to a no-op, so the default renders exactly the
cobblestone it did before the host work. A 2048 full-image diff of albedo,
normal, ORM and heightmap against `main`'s graph gives 0 differing pixels.

| Layer | Exposed params | What it does |
|---|---|---|
| Stone Layout: `Joint width` | 0-1, default 0.5 | Scales the joint band on its own. The border distance is divided by max(2 x width, 0.1) before `PlateEdges`, so 0.5 is the shipped joint, 0.25 is half as wide, and 1 is twice as wide. It sits upstream of `JointWarp`, so the dark joint and the relief groove move together. |
| Stone Layout: `Tones follow joints` | 0 or 1, default 0 | Set it to 1. Every original ships 0, where the per-stone tone cells are not warped but the joints are, so some tone edges sit mid-stone. Thin joints make this obvious. At 1, `ToneWarp` (JointWarp's twin on the cell random) puts every tone edge on a joint. In-between values mix two tones; use 0 or 1. |
| Stone Surface: `Top flatness` | 0-1, default 0 | Pulls the fine relief noise toward its mid value, so the tops go flat while the joints keep full depth. This is the "relief lives in the joints" s10 wanted. s10's own lever, `Relief strength` 0.5, halves the joints too. |
| Mortar: `Mortar fill`, `Mortar color` | 0-1, default 0 | 0 = open dry-laid joints, the look of s07, s08 and s10 alike. Above 0, mortar fills the joint's V-groove up to that level, with a flat floor and a crease where it meets the stone. One mask, smoothstep(clamp((fill - band) x 8)), paints the mortar colour where the relief is mortar, and the colour varies with the same surface noise that textures it. 1 = flush with the tops. |

`Stone size`, `Stone color`, `Joint depth`, `Grain scale`, `Grain
contrast` and `Relief strength` are the originals' own levers, now exposed.
Two things are different in the host: `Stone size` and `Grain scale` now
drive both axes, and `Relief strength` is new as an exposed slider.

### Presets

Set these on the collapsed nodes. Colors are gradient stops (position: R, G,
B in 0-1). Anything not listed stays at its default. `Grain scale` has its
own slider range, 1-64 (a named parameter both perlin scales read), so the
default 40 and s08's 48 are on the slider.

**Dry stone wall (s08), exact:**
- `Stone size` = 8, `Grain scale` = 48.
- `Stone color`: 0.0: 0.22, 0.23, 0.22; 0.25: 0.40, 0.41, 0.40; 0.45: 0.58,
  0.58, 0.56; 0.62: 0.50, 0.47, 0.40; 0.80: 0.43, 0.45, 0.40; 1.0: 0.30,
  0.29, 0.26.
- Renders s08's maps exactly (0 px on albedo, normal, ORM and heightmap).

**Flagstone (s10), exact:**
- `Stone size` = 4, `Relief strength` = 0.5.
- `Stone color`: 0.0: 0.18, 0.20, 0.23; 0.30: 0.30, 0.34, 0.38; 0.55: 0.42,
  0.44, 0.46; 0.78: 0.34, 0.40, 0.38; 1.0: 0.48, 0.50, 0.54.
- `Grain contrast`: 0.0: 0.85 gray; 1.0: 1.0 gray.
- Renders s10's maps exactly (0 px).

**Beyond the originals (these use the new layers):**
- *Tight dry-stack*, s08's stated intent (s08 shipped s07's joint width):
  the s08 preset plus `Joint width` = 0.25 and `Tones follow joints` = 1.
- *Sawn flagstone, grouted*: the s10 preset, but keep `Relief strength` at
  0.99. Add `Top flatness` = 0.75, `Tones follow joints` = 1, `Mortar fill`
  = 0.6, and `Mortar color` 0.0: 0.26, 0.27, 0.28; 1.0: 0.38, 0.39, 0.40.
- *Cobbles set in mortar*: `Joint width` = 0.7, `Tones follow joints` = 1,
  `Mortar fill` = 0.55. The default `Mortar color` is 0.0: 0.30, 0.29,
  0.27; 1.0: 0.44, 0.42, 0.39.

**Back to the default:** set `Joint width` to 0.5, and set `Tones follow
joints`, `Top flatness` and `Mortar fill` to 0.

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
| (top level) | stone_layout | graph |
| (top level) | stone_color | graph |
| (top level) | stone_surface | graph |
| (top level) | mortar | graph |
| (top level) | relief | graph |
| (top level) | surface_grain | graph |
| stone_layout | PlateCells | voronoi |
| stone_layout | PlateEdges | colorize |
| stone_layout | JointWarpNoise | perlin |
| stone_layout | JointWarp | warp |
| stone_layout | JointWidth | math |
| stone_layout | JointWidthFloor | math |
| stone_layout | JointScale | math |
| stone_layout | ToneWarp | warp |
| stone_layout | ToneDelta | math |
| stone_layout | ToneShift | math |
| stone_layout | StoneTone | math |
| stone_color | StoneMetallic | colorize |
| stone_color | JointComposite | blend |
| stone_color | StoneColor | colorize |
| stone_surface | ReliefNoiseFine | perlin |
| stone_surface | TopNoiseDelta | math |
| stone_surface | TopFlatten | math |
| stone_surface | TopNoise | math |
| mortar | MortarLevel | uniform_greyscale |
| mortar | MortarRelief | math |
| mortar | MortarDepth | math |
| mortar | MortarRamp | math |
| mortar | MortarMask | math |
| mortar | MortarColor | colorize |
| mortar | MortarColorComposite | blend |
| relief | ReliefComposite | blend |
| relief | StoneNormal | normal_map |
| relief | ReliefRamp | colorize |
| relief | ReliefHeight | colorize |
| surface_grain | GrainNoise | perlin |
| surface_grain | GrainContrast | colorize |
| surface_grain | GrainOverStone | blend |
<!-- nodes:end -->
