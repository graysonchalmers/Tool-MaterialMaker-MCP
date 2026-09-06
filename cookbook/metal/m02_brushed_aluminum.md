# m02_brushed_aluminum - Brushed aluminum

_Category: metal. Open the graph: `cookbook/metal/m02_brushed_aluminum.ptex`._

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
- shallow scratch relief: `normal_map_0` with the `param4=0` fix at low
  strength.

## Subgraph structure

Opening the graph shows 3 top-level nodes instead of 12:

- **Brushed Finish** (`perlin_2`, `blend_0`, `colorize_2`, `colorize_0`,
  `normal_map_0`). Exposed: `Streak length`, `Streak density`, `Aluminum
  color`, `Roughness`, `Scratch depth`.
- **Wood Donor Leftover (unused)** (`perlin_0`, `perlin_1`, `warp_0`,
  `voronoi_0`, `colorize_1`, `warp_1`). Wood's knot-warp chain, disconnected
  by the straightening rewire; it feeds nothing. Kept and labeled rather than
  deleted so the graph still shows how a wood grain became a brushed finish.
  Delete it freely if you are editing this material for real.

## See also

`guide://authoring` (or `docs/AUTHORING.md`) for the `param4=0` fix and the
"pick the base by topology" lesson; `docs/evidence/phase3/2026-08-26-iter1.md`.
