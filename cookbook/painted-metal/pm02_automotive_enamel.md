# pm02_automotive_enamel - Automotive enamel, deep red

_Category: painted-metal. Open the graph: `cookbook/painted-metal/pm02_automotive_enamel.ptex`._

A near-mirror deep red clearcoat with a faint metallic-flake sparkle, distinct from pm01's matte pebbling and pm04's dimpled hammertone.

## Recipe

Clones `rock`. Albedo is driven off `voronoi_0`'s per-cell random (port 2, rand3) at a very fine scale (60) so each tiny cell is a slightly different red, giving the faint metallic-flake sparkle. Very low roughness (0.07 to 0.11) produces the near-mirror clearcoat with a sharp specular highlight on the preview sphere, near-flat normal (`param1` 0.04) for the glassy coat, and metallic stays 0 since the dielectric clearcoat, not a metal surface, dominates the visible response.

Pitfall: the flake speckle reads a touch sandy on the matte faces of the preview geometry. If a cleaner enamel is wanted, drop the albedo spread or the fleck scale.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 3 top-level nodes (two groups plus `Material`)
instead of the raw 11-node graph:

- **Flake Pattern** — `voronoi_0`, `voronoi_1`, `warp_0`, `perlin_0`,
  `perlin_1`, `blend_0`, `colorize_0` (albedo). `blend_0` is `rock`'s own
  noise-mix step: port0/port1 come from `voronoi_0`'s two output ports and
  the port2 mask from `perlin_0`, all three inside this group, so it is
  fully self-contained. Its output goes nowhere in this recipe — this
  builder rewires `colorize_0` to read `voronoi_0`'s port 2 (per-cell
  random) directly instead, for the flake speckle, leaving `blend_0` a
  harmless dead end. It still rides into this group rather than standing
  alone as a bare unused node. Exposed: `Paint color`, `Fleck density`.
- **Surface Finish** — `colorize_1` (metallic, flat 0), `colorize_2`
  (roughness), `normal_map_0`. `perlin_0` (inside Flake Pattern) also
  feeds this group's `colorize_1`/`colorize_2` directly — the expected
  shared-upstream-node case. Exposed: `Clearcoat gloss`, `Coat
  smoothness`.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
