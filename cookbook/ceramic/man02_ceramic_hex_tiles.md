# man02_ceramic_hex_tiles - White ceramic hexagon tiles

_Category: ceramic. Open the graph: `cookbook/ceramic/man02_ceramic_hex_tiles.ptex`._

Prompt: "white ceramic hexagon tiles". A Phase-3 hero material (frozen
15-case test set), folded into the cookbook 2026-09-05 as the founding member
of the ceramic category.

## Recipe

Clone `beehive`, Material Maker's bundled hex field. `beehive_2`'s port 0
peaks at each cell center and falls to a narrow low band at the edges, so
one ramp does both jobs: `TileColor` maps the low band to a thin dark grout
line and everything above 0.20 to white tile, and `GlazeRoughness` inverts
that for roughness (grout rough, glazed faces near-mirror). The metallic
constant (`NonMetallic`) is set to 0. The hex relief from the donor's blend ->
normal_map chain is kept so the grout reads recessed; height (port 6) comes
from the same blend.

The lesson: when a bundled example already has the exact pattern topology
(regular hex cells), the whole material is two gradient ramps and one
constant. Tile density is `sx`/`sy` on the beehive (20 x 12 here).

## Subgraph structure

The tile host (2026-09-27). It absorbs `s05_hex_stone_tile` and
`man03_mosaic_tile` (both still shipped, pending retirement). s05 is this
same `beehive` graph with colour and roughness read off the per-cell blend
instead of the clean hex field, plus a perlin grain multiplied over both.
man03 is a different generator (`skewed_bricks`) feeding the same colour,
roughness and normal shape. So the host carries `skewed_bricks` in as a
layout, and two selectors pick the signals. Six groups, left to right into
Material:

- **Hex Layout**: `HexLayout` (`beehive`), `StructureTone`,
  `CellRandomTone`, `StoneToneBlend`. Exposed: `Tiles across`, `Tiles
  down`, `Edge softness`. Outputs the clean hex value and the per-cell
  blend (the relief field, and s05's stone tone).
- **Brick Layout** (from man03): `BrickLayout` (`skewed_bricks`, man03's
  values). Exposed: `Brick rows`, `Brick columns`, `Jitter`, `Mortar width`.
- **Tile Pattern**: the selector math. Exposed: `Layout`, `Tone source`.
  Outputs the tone (feeds colour and roughness) and the relief (feeds
  normal and height).
- **Tile Color**: `TileColor`, `GlazeRoughness`. Exposed: `Tile and grout
  color`, `Glaze roughness`.
- **Tile Relief**: `GroutNormal`, `GroutDepth`. Exposed: `Grout depth`.
  `GroutNormal`'s Resolution (`param0`) is not exposed: the catalog has no
  range for it, so the web play surface would show it as a 0-1 slider.
- **Surface Grain** (from s05): `GrainNoise`, `GrainContrastAlbedo`,
  `GrainContrastRoughness`, `AlbedoGrain`, `RoughnessGrain`. Exposed:
  `Grain strength` (both composites), `Grain scale` (both axes), `Grain
  detail`.

`NonMetallic` (metallic 0) stays top-level as a single donor-default
constant feeding one port.

Both selectors are one-hot weights in product-sum form (a x w0 + b x w1,
the weights from an `A<B` threshold at 0.5 and 1 minus that), as in f07's
Pattern selector. Colour, roughness, normal and height always read the
same layout, so they stay registered in every mode. The grain sits on the
blend's port 0 with the base on port 1, so `Grain strength` 0 passes the
base through untouched.

Seeds: `beehive`, `perlin` and `skewed_bricks` are seeded from node
position. `HexLayout` keeps its donor position (the same spot it holds in
s05), and `BrickLayout` and `GrainNoise` sit at (0, 0) in their subgraphs,
as in man03 and s05. Do not move them.

## Feature layers

Every new layer defaults off, so the default is the white hex tile it was
before the host work. A 2048 full-image diff of albedo, normal, ORM and
heightmap against `main`'s graph: heightmap 0 px; albedo 320 px (0.008%),
normal 79 px (0.002%) and ORM 1584 px (0.038%) differ, all by exactly 1/255.
The selectors are exact arithmetic (x 1 + y x 0), and the bypass test pins
the flips on them: with both selectors bypassed the diff is 0 px, and the
grain layer alone is 0 px. So this is GPU-compiler rounding of the `beehive`
expression in a new context, amplified by the steep 0.10-0.20 ramp. Lit
preview: 79 of 590k px differ.

| Layer | Exposed params | What it does |
|---|---|---|
| Tile Pattern: `Layout` | 0 or 1, default 0 | 0 = hex (`beehive`), 1 = bricks (`skewed_bricks`). It is a switch at 0.5, not a mix. |
| Tile Pattern: `Tone source` | 0 or 1, default 0 | Hex only. 0 = colour and roughness read the clean hex value (every tile one colour). 1 = they read the per-cell blend, so each tile takes its own tone from the colour ramp (s05's stones). |
| Brick Layout | `Brick rows` 6, `Brick columns` 3, `Jitter` 1, `Mortar width` 0.1 | man03's `skewed_bricks`. Only used at `Layout` 1. |
| Surface Grain | `Grain strength` 0-1, default 0 | s05's perlin grain multiplied over albedo (0.80-1.0) and roughness (0.85-1.05). |

### Presets

Set these on the collapsed nodes. Colors are gradient stops (position: R,
G, B in 0-1). Anything not listed stays at its default. Each preset was
rendered at 2048 and diffed against the current original.

**Hex stone tile (s05)**: albedo, ORM and heightmap 0 px; normal differs
(see below).
- `Tiles across` = 7, `Tiles down` = 5, `Tone source` = 1, `Grain strength` = 1.
- `Tile and grout color`: 0.0: 0.15, 0.14, 0.13; 0.08: 0.16, 0.15, 0.14;
  0.14: 0.45, 0.42, 0.38; 0.40: 0.56, 0.50, 0.42; 0.65: 0.43, 0.43, 0.45;
  0.88: 0.50, 0.46, 0.39.
- `Glaze roughness`: 0.08: 0.85 gray; 0.14: 0.58 gray; 0.88: 0.64 gray.

s05 still runs its normal through the buffered path (`param4` = 1). The
host is on the direct path (`param4` = 0), so the s05 normal differs by at
most 3/255 on 7.1% of pixels (mean 0.07/255).

**Mosaic tile (man03)**: albedo, normal and ORM 0 px; the lit preview is
also 0 px.
- `Layout` = 1 (`Brick rows` 6, `Brick columns` 3, `Jitter` 1 are the defaults).
- `Tile and grout color`: 0.0: 0.10, 0.09, 0.08; 0.12: 0.10, 0.09, 0.08;
  0.30: 0.85, 0.79, 0.66; 1.0: 0.92, 0.87, 0.74.
- `Glaze roughness`: 0.0: 0.78 gray; 0.12: 0.78 gray; 0.30: 0.14 gray;
  1.0: 0.08 gray.
- `Grout depth` = 0.4.
- Inside Tile Relief, set `GroutNormal`'s Resolution to 1024 (`param0` =
  10, man03's value). It is the one preset value that is not on the
  collapsed node. Left at 2048, the normal is off by up to 50/255 on 6.5%
  of pixels (mean 0.86/255); albedo and ORM stay 0 px.

man03 exported no heightmap. The host does export one in brick mode: faces
high, mortar low, from the same field as the normal. man03's Material node
also had `roughness` 0.5 and `depth_scale` 1, where the host has 1 and
0.2. Those only reach the `.tres`, not the PNG maps. For man03's in-engine
look, set them on the Material node too.

`Grain scale` 48 is past the perlin slider's range (it stops at 32), so type
it into the field. It is already the default.

**Beyond the originals (not rendered yet):** the layers combine, e.g.
`Grain strength` 1 on the white ceramic, or `Layout` 1 with the s05 ramps.

**Back to the default:** `Layout` 0, `Tone source` 0, `Tiles across` 20,
`Tiles down` 12, `Grain strength` 0, `Grout depth` 1.02, `GroutNormal`
Resolution 2048 (`param0` 11), and the default ramps (0.10: 0.26, 0.25, 0.23; 0.20: 0.92, 0.92,
0.90; 1.0: 0.97, 0.97, 0.95 / 0.10: 0.80, 0.20: 0.14, 1.0: 0.10 gray).

## See also

`guide://authoring` (or `docs/AUTHORING.md`), the `pattern`/`beehive` notes;
`docs/evidence/phase3/2026-08-26-iter1.md`.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | NonMetallic | uniform_greyscale |
| (top level) | hex_layout | graph |
| (top level) | brick_layout | graph |
| (top level) | tile_pattern | graph |
| (top level) | tile_color | graph |
| (top level) | tile_relief | graph |
| (top level) | surface_grain | graph |
| hex_layout | CellRandomTone | colorize |
| hex_layout | StructureTone | colorize |
| hex_layout | StoneToneBlend | blend |
| hex_layout | HexLayout | beehive |
| brick_layout | BrickLayout | skewed_bricks |
| tile_pattern | LayoutSelect | uniform_greyscale |
| tile_pattern | ToneSelect | uniform_greyscale |
| tile_pattern | IsBricks | math |
| tile_pattern | IsHex | math |
| tile_pattern | IsCellTone | math |
| tile_pattern | IsCleanTone | math |
| tile_pattern | CleanToneTerm | math |
| tile_pattern | CellToneTerm | math |
| tile_pattern | HexToneTerm | math |
| tile_pattern | BrickToneTerm | math |
| tile_pattern | HexReliefTerm | math |
| tile_pattern | BrickReliefTerm | math |
| tile_pattern | HexTone | math |
| tile_pattern | ToneMix | math |
| tile_pattern | ReliefMix | math |
| tile_color | GlazeRoughness | colorize |
| tile_color | TileColor | colorize |
| tile_relief | GroutNormal | normal_map |
| tile_relief | GroutDepth | colorize |
| surface_grain | GrainNoise | perlin |
| surface_grain | GrainContrastAlbedo | colorize |
| surface_grain | GrainContrastRoughness | colorize |
| surface_grain | AlbedoGrain | blend |
| surface_grain | RoughnessGrain | blend |
<!-- nodes:end -->
