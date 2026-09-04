# pm05_scuffed_panel - Scuffed panel, utility blue

_Category: painted-metal. Open the graph: `cookbook/painted-metal/pm05_scuffed_panel.ptex`._

Faded utility-blue paint with directional brushed scuff streaks, built from a straightened wood-grain donor rather than any of the cell-based donors the rest of the family uses.

## Recipe

Clones `wood` for its directional grain and working normal chain, the same donor used for brushed aluminum elsewhere in this project, but keeps it as paint rather than bare metal. The grain is straightened into parallel scuffs by rewiring `blend_0:1` from the straight `perlin_2`, killing `wood`'s knot warp, and stretching it long and fine (`scale_x` 48, `scale_y` 2). Faded utility-blue albedo carries brighter worn streaks. Metallic stays 0 throughout (drop the grain-driven metallic map and set the scalar to 0), with a `param4=0` normal at `param1` 0.30 for the directional scuff grooves.

Pitfall specific to this material, and the fix that mattered most: the key move over the first pass was octave count. 8 iterations rendered a grainy fbm noise with only a weak directional axis; dropping to 2 iterations made the streaks read as smooth brushed lines with a clear direction. Honest note: the streaks are quite regular, closer to a brushed finish than random scuffing; add a low-frequency perlin break-up if true random scuffs are wanted.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 3 top-level nodes (two groups plus `Material`)
instead of the raw 11-node graph:

- **Scuff Pattern** — `perlin_0`, `perlin_1`, `warp_0`, `voronoi_0`,
  `colorize_1`, `warp_1`, `perlin_2`, `blend_0`, `colorize_2` (albedo).
  `blend_0` is `wood`'s own node (Multiply, constant mask): both its
  port0 and port1 read from the same straightened `perlin_2` (the
  builder's `rewire` killed the donor's knot-warp branch by pointing
  both blend inputs at it), so there is no "which layer is on top"
  question — both content inputs are the same source. The old knot-warp
  chain (`perlin_0`, `perlin_1`, `warp_0`, `voronoi_0`, `colorize_1`,
  `warp_1`) is left with no path to `Material` at all, a pre-existing
  quirk of the rewire rather than something this retrofit introduced;
  it rides into this group rather than sitting as loose unconnected
  top-level nodes. Exposed: `Paint color`, `Scuff length`.
- **Surface Finish** — `colorize_0` (roughness), `normal_map_0`.
  Exposed: `Roughness contrast`, `Scuff depth`.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
