# sf04_vent_grille_panel - Vent grille panel

_Category: scifi. Open the graph: `cookbook/scifi/sf04_vent_grille_panel.ptex`._

A metal panel punched with a grid of small square vent holes, distinct from the hexagonal grating look used elsewhere in this project.

## Recipe

Built with a single `pattern` node, using both `x_wave` and `y_wave` set to Square with `mix=Min`: the minimum of two square waves is their intersection, which gives a grid of small square holes in one node with no separate mask or composite step needed. This is deliberately distinct from a beehive-based hexagonal grating, which uses hex cells instead of a square punch pattern.

Pitfall: none, this recipe hit target on the first structural idea. Note: an emission-only "glowing tech panel" variant of this category was considered and ruled out before building, since the render pipeline's export target only produces albedo, normal, heightmap, and orm maps, so an emission-only material would be invisible in the actual product output; this vent grille was built in its place.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 3 top-level nodes (two groups plus `Material`)
instead of the raw 5-node graph:

- **Hole Pattern** — `pattern_holes`, `colorize_0`. `pattern_holes` also
  feeds `colorize_rgh` and `normal_map_0` in Surface Finish directly (one
  upstream node feeding multiple downstream groups, producing expected
  extra boundary output ports). Exposed: `Hole density` (`pattern_holes`'s
  `x_scale`), `Hole vs plate color` (`colorize_0`'s gradient).
- **Surface Finish** — `colorize_rgh`, `normal_map_0`. Exposed: `Recess
  roughness`, `Relief strength`.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
