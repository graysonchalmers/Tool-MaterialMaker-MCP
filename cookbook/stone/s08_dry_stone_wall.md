# s08_dry_stone_wall - Dry-stone / fieldstone wall

_Category: stone. Open the graph: `cookbook/stone/s08_dry_stone_wall.ptex`._

Randomly packed fieldstone wall with no coursing, distinct from the neatly quarried `s09_ashlar_wall` in the same set.

## Recipe

Uses the same `dry_earth` clone as `s07_cobblestone`, retuned to read as a different material rather than a recolor: `voronoi_0` scale moved from 6 to 8 (smaller, denser stones), a cool weathered-gray palette in place of cobblestone's warm tan, and thin dark dry-stack gaps. `warp_0.amount` is held at the same haze-free 0.12 used in s07.

Pitfall specific to this material: a pass at `warp_0.amount` 0.20, chasing more angular edges, brought the haze back without sharpening any corners, because warp displaces rather than bevels; the angular fieldstone read actually comes from the voronoi cell shape itself, which is already polygonal. The mossy-green stop needs to stay restrained too; pushed further it tips into a camo grid, the same trap s05's hex tile hit. Honest limit: pure voronoi has no horizontal coursing, so this reads as random rubble or fieldstone, not neatly coursed drystone.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
