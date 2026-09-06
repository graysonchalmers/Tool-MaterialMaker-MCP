# m01_weathered_copper - Weathered copper

_Category: metal. Open the graph: `cookbook/metal/m01_weathered_copper.ptex`._

Prompt: "weathered copper". A Phase-3 hero material (frozen 15-case test
set), folded into the cookbook 2026-09-05 as one of the two founding members
of the bare-metal category.

## Recipe

Clone `rusted_metal`, which is already a two-layer metal: a base metal
(`colorize_2`) with weathered patches (`colorize_1`) masked in by a perlin
threshold (`colorize_3`), plus a roughness blend that follows the same mask.
Recolor only: base gray -> warm copper, patches orange rust -> green
verdigris. The patch mask still drives metallic, so the verdigris reads as a
dull crust and the exposed copper stays metallic. The lesson this hero
taught: a donor that already has the right LAYER STRUCTURE only needs its
ramps changed; look for two-layer donors before building composites.

## Subgraph structure

Opening the graph shows 4 top-level nodes instead of 11:

- **Patina Pattern** (`perlin_2`, `colorize_3`, `colorize_4`). Exposed:
  `Patch size`, `Patina coverage`. Its output also drives Material's metallic.
- **Copper Color** (`perlin_1`, `colorize_2`, `colorize_1`, `blend_0`).
  Exposed: `Copper color`, `Verdigris color`.
- **Surface Finish** (`perlin_0`, `colorize_0`, `blend_1`). Exposed:
  `Roughness`.

## See also

`guide://authoring` (or `docs/AUTHORING.md`), the recolor lever and the
masked two-layer blend; `docs/evidence/phase3/2026-08-26-iter1.md`.
