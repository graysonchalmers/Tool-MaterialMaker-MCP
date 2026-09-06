# o01_mossy_forest_floor - Mossy forest floor

_Category: organics. Open the graph: `cookbook/organics/o01_mossy_forest_floor.ptex`._

Prompt: "mossy forest floor". A Phase-3 hero material (frozen 15-case test
set), folded into the cookbook 2026-09-05 so it carries the same gates, card,
and subgraph grouping as every other material.

## Recipe

Clone `dry_earth`, whose cracked-plate ground already has a working
crack-and-plate relief chain, and recolor only its earth albedo ramp
(`colorize_0`): plate tops become moss green, crack floors become dark soil,
so the same plate topology reads as a mossy floor instead of dried mud. The
lesson that later became the terrain set's rule ("pick the base by topology,
not by donor name"): a connected crack network is the right base for anything
that grows in patches between low seams.

## Subgraph structure

Same two-group split as the other dry_earth-derived materials
(`gl01_frosted_glass`, the terrain plates). Opening the graph shows 5
top-level nodes instead of 13:

- **Ground Color** (`voronoi_0`, `colorize_1`, `warp_0`, `colorize_0`,
  `blend_0`, `colorize_3`). Exposed: `Plate size`, `Moss and soil colors`,
  `Crack contrast`, `Plate warp`.
- **Ground Relief** (`colorize_4`, `blend_1`, `colorize`, `normal_map_0`).
  Exposed: `Relief strength`.

`perlin_0` and `perlin_1` stay top-level: each feeds both groups, so folding
either in would only relabel the sharing as an extra boundary port.

## See also

`guide://authoring` (or `docs/AUTHORING.md`), "Cross-material lessons" for
the topology-not-donor rule; `quality/scorecards/2026-08-26-iter1.md`.
