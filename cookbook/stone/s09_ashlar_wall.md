# s09_ashlar_wall - Ashlar / castle block wall

_Category: stone. Open the graph: `cookbook/stone/s09_ashlar_wall.ptex`._

Regular, quarried cut-block wall, the coursed counterpart to `s08_dry_stone_wall`'s random rubble.

## Recipe

The one stone material in this set that leaves the voronoi cluster entirely, because a `Bricks` node gives true coursed rectangular blocks that voronoi cannot produce. Clones `stone_wall`, which is already a Bricks-driven stone wall and already routes `Bricks` port 1 (its per-brick random) into the per-block tone colorize (`colorize_1`). Retuned by moving `Bricks` columns/rows from 3x6 to 4x4 for squarer, larger ashlar blocks, keeping `row_offset` 0.5 (coursed, broken joints) and the 0.15 bevel (chamfered cut-stone edge), with fine 0.06 mortar. The per-block ramp is recolored to dressed limestone/sandstone, tempering `stone_wall`'s rustic orange block tone.

Pitfall specific to this material: getting a genuinely quarried, cut-stone read needs the Bricks donor specifically, not the voronoi family the rest of the stone set uses, since coursed rectangles are a Bricks-only structure. The pale lime joints in this recipe deliberately contrast s08's dark dry-stack gaps within the set.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
