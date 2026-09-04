# s09_ashlar_wall - Ashlar / castle block wall

_Category: stone. Open the graph: `cookbook/stone/s09_ashlar_wall.ptex`._

Regular, quarried cut-block wall, the coursed counterpart to `s08_dry_stone_wall`'s random rubble.

## Recipe

The one stone material in this set that leaves the voronoi cluster entirely, because a `Bricks` node gives true coursed rectangular blocks that voronoi cannot produce. Clones `stone_wall`, which is already a Bricks-driven stone wall and already routes `Bricks` port 1 (its per-brick random) into the per-block tone colorize (`colorize_1`). Retuned by moving `Bricks` columns/rows from 3x6 to 4x4 for squarer, larger ashlar blocks, keeping `row_offset` 0.5 (coursed, broken joints) and the 0.15 bevel (chamfered cut-stone edge), with fine 0.06 mortar. The per-block ramp is recolored to dressed limestone/sandstone, tempering `stone_wall`'s rustic orange block tone.

Pitfall specific to this material: getting a genuinely quarried, cut-stone read needs the Bricks donor specifically, not the voronoi family the rest of the stone set uses, since coursed rectangles are a Bricks-only structure. The pale lime joints in this recipe deliberately contrast s08's dark dry-stack gaps within the set.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
This is the only material in the category built on `stone_wall`'s `Bricks`
donor rather than a `voronoi`/`dry_earth` clone, and the only one where a
`blend` node's port sources needed tracing (this builder itself never
touches any `blend` node -- it only retunes `Bricks` and recolors
`colorize_1` -- but the donor's own wiring still needed reading before
deciding how to group it). Read `blend_0`'s raw connections directly:
port0(s1)=`colorize_1` (block tone, fed by `blend_1`'s Perlin + Bricks
per-brick-random mix), port1(s2)=`colorize_0` (mortar tone, fed by
`Perlin`), port2(mask)=`colorize_2` (the Warp'd `Bricks` shape, high inside
each brick face and low at the joints). That means mask-high shows the
block tone and mask-low shows the mortar tone -- the expected read for cut
stone with dark joints, not the port-reversal this retrofit's leather task
found elsewhere. `blend_1` (Perlin + Bricks port1 random -> `colorize_1`)
and `blend_2` (Warp + Perlin -> the height/AO/depth fan-out) both carry no
port2 mask (unconnected -> uniform 1.0), plain amount mixes. None of these
three blends' wiring is modified by this retrofit, only regrouped --
confirmed unchanged by the exact `renders_match` result below. `uniform_0`
(the metallic constant) and the donor's own unnamed shader-preview node
(literal name `"394"`) are left top-level, matching the convention for
untouched single-purpose nodes. Opening the graph shows 2 top-level groups
(plus `Material`, `uniform_0`, `394`) instead of the raw 16-node graph:

- **Block Layout** -- `Bricks`, `perlin_0` (Warp's distortion field),
  `Warp`, `colorize_2` (the brick/mortar mask), `colorize_7` (roughness,
  directly downstream of `colorize_2`). Exposed: `Block size`
  (`Bricks.columns`), `Joint width` (`Bricks.mortar`), `Edge chamfer`
  (`Bricks.bevel`).
- **Block & Mortar Finish** -- `Perlin`, `colorize_0`, `blend_1`,
  `colorize_1`, `blend_0`, plus the never-separately-tuned relief/AO/depth
  chain (`blend_2`, `colorize_6`, `colorize_4`, `normal_map_0`), folded in
  here since it has no builder-set parameter of its own. Exposed: `Block
  color` (`colorize_1.gradient`).

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all four exported maps (albedo, heightmap, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
