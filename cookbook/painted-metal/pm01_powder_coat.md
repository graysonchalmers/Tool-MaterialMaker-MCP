# pm01_powder_coat - Powder coat, safety yellow

_Category: painted-metal. Open the graph: `cookbook/painted-metal/pm01_powder_coat.ptex`._

Flat safety-yellow powder coat with fine, dense, even orange-peel pebbling: a distinct structural read rather than a plain gray panel with a roughness tweak.

## Recipe

Clones `rock` for its isotropic voronoi-warp-normal chain, but the donor's stock settings do not give orange peel out of the box. `rock`'s `warp_0` (amount 0.3, coarse scale-4 perlin) smears the voronoi cells into ridges, which the first render read as a wormy crackle or foil texture instead. Fix: flatten the warp hard (`amount` 0.03) and push the cells fine (`voronoi_1`/`voronoi_0` scale 44) so they stay round and dense. Low relief (`normal_map_0` `param1` 0.12, `param4=0`), matte roughness, flat safety-yellow albedo, metallic 0. Reads as tight even pebbling under real lighting.

Pitfall: this material is a dielectric paint coat over metal, so metallic stays 0 across the whole surface here; there is no bare-metal exposure in this recipe (that is pm03's job).

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 3 top-level nodes (two groups plus `Material`)
instead of the raw 11-node graph:

- **Orange Peel Pattern** — the donor's own voronoi/warp noise chain
  (`voronoi_0`, `voronoi_1`, `warp_0`, `perlin_0`, `perlin_1`) plus
  `blend_0` and the albedo `colorize_0`. `blend_0` is `rock`'s own
  noise-mix step (not a paint-over-metal composite): its port0/port1
  sources are `voronoi_0`'s own two output ports and its port2 mask is
  `perlin_0` — all three are inside this same group, so the blend is
  fully self-contained; only its single output edge into `colorize_0`
  needed to cross anything, and that stayed internal too. Exposed:
  `Paint color`, `Peel density`.
- **Surface Finish** — `colorize_1` (metallic, flat 0), `colorize_2`
  (roughness), `normal_map_0`. `perlin_0` (inside Orange Peel Pattern)
  also feeds this group's `colorize_1`/`colorize_2` directly — one
  upstream node feeding multiple downstream groups, producing the
  expected extra boundary output ports on `perlin_0`. Exposed:
  `Roughness`, `Relief strength`.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
