# sf01_hull_plating - Diamond-plate hull panel

_Category: scifi. Open the graph: `cookbook/scifi/sf01_hull_plating.ptex`._

A diamond-plate metal hull panel with visibly darker, duller seams between the panel plates, built on top of a bundled example that otherwise has no albedo texture at all.

## Recipe

Clones `metal_pattern_2`, a bundled example with a working grid-line normal chain but no albedo texture: it relies entirely on the Material node's flat scalar `albedo_color`. This recipe grafts the same grid pattern (`blend_0`'s output) into new `colorize` nodes feeding both albedo and roughness, so the panel seams read as visibly darker and duller rather than only normal-lit. Uses a proactive `param4=0`, since `blend_0`'s inputs are pattern generators (analytic, directly fed), the same class of flat-normal blocker every other node in this project hits.

Pitfall: none required rework here, this recipe was a straightforward graft onto the donor's existing grid structure.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
