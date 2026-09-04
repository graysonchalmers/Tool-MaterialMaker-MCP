# sf01_hull_plating - Diamond-plate hull panel

_Category: scifi. Open the graph: `cookbook/scifi/sf01_hull_plating.ptex`._

A diamond-plate metal hull panel with visibly darker, duller seams between the panel plates, built on top of a bundled example that otherwise has no albedo texture at all.

## Recipe

Clones `metal_pattern_2`, a bundled example with a working grid-line normal chain but no albedo texture: it relies entirely on the Material node's flat scalar `albedo_color`. This recipe grafts the same grid pattern (`blend_0`'s output) into new `colorize` nodes feeding both albedo and roughness, so the panel seams read as visibly darker and duller rather than only normal-lit. Uses a proactive `param4=0`, since `blend_0`'s inputs are pattern generators (analytic, directly fed), the same class of flat-normal blocker every other node in this project hits.

Pitfall: none required rework here, this recipe was a straightforward graft onto the donor's existing grid structure.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 3 top-level nodes (two groups plus `Material`)
instead of the raw 9-node graph:

- **Panel Pattern** — the donor's own unmodified pattern chain
  (`pattern_0`, `pattern_1`, `colorize_0`, `transform_2`, `blend_0`) plus
  `colorize_alb` (the grafted albedo recolor). None of the donor's own
  pattern nodes carry an explicit builder value of their own, so they ride
  along inside this group anchored by `colorize_alb`'s explicit gradient,
  rather than standing alone with only untouched defaults. Exposed: `Seam
  color`.
- **Surface Finish** — `colorize_rgh` and `normal_map_0`. `blend_0` (inside
  Panel Pattern) feeds both this group's `normal_map_0` and its own
  `colorize_rgh`, in addition to `colorize_alb` inside Panel Pattern -- one
  upstream node feeding multiple downstream groups, which produces the
  expected extra boundary output ports on `blend_0`. Exposed: `Seam
  roughness contrast`, `Relief strength`.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
