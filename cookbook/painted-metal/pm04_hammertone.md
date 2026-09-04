# pm04_hammertone - Hammertone, bronze-gray

_Category: painted-metal. Open the graph: `cookbook/painted-metal/pm04_hammertone.ptex`._

Bronze-gray hammertone paint with a dimple field, the strongest structural read of the whole painted-metal set.

## Recipe

Clones `rock`, using the same normal chain as pm01's powder coat but at a medium cell size (`voronoi_1` scale 14) so the rounded cells read as hammer-blow dimples: bigger than pm01's fine orange peel and smaller than `rock`'s native lumps, with the deepest relief in the family (`param1` 0.42, `param4=0`) because the dimples are the whole point of this material. Bronze-gray albedo carries per-cell tonal variation so the dimples catch the light, semi-gloss roughness gives the metallic-looking sheen, and metallic stays 0 since it is paint, not exposed metal.

Pitfall: this material runs a little dark in the preview scene; lift the bronze albedo stops if a brighter finish is wanted.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 3 top-level nodes (two groups plus `Material`)
instead of the raw 11-node graph:

- **Hammer Dimple Pattern** — `voronoi_0`, `voronoi_1`, `warp_0`,
  `perlin_0`, `perlin_1`, `blend_0`, `colorize_0` (albedo). Same `rock`
  donor blend as pm01/pm02: `blend_0`'s port0/port1 sources are
  `voronoi_0`'s two output ports and its port2 mask is `perlin_0`, all
  three inside this group, so it is fully self-contained. Exposed:
  `Paint color`, `Dimple size`.
- **Surface Finish** — `colorize_1` (metallic, flat 0), `colorize_2`
  (roughness), `normal_map_0`. `perlin_0` (inside Hammer Dimple Pattern)
  also feeds this group's `colorize_1`/`colorize_2` directly — the
  expected shared-upstream-node case. Exposed: `Sheen`, `Dimple depth`.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
