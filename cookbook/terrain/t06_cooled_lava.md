# t06_cooled_lava - Cooled lava

_Category: terrain. Open the graph: `cookbook/terrain/t06_cooled_lava.ptex`._

Near-black basalt plates with glowing ember-orange cracks between them.

## Recipe

Built with the shared `_dry_earth_plates()` helper in `cookbook_terrain.py` at scale 5, near-black basalt per-plate color, and `warp_0` at 0.2. The helper gives this material a flat roughness texture (rather than `dry_earth`'s normally unconnected scalar roughness) so an ORM map exports correctly.

The glow taps `warp_0` directly, the crack signal, which is low at the cracks: a `colorize_glow` node maps the crack lows to bright ember-orange and the plate interiors to black, and that output feeds the Material node's emission input (port 3) with `emission_energy` set to 1.0.

Pitfall specific to this material: the glow polarity was correct on the first try here, but if the glow ever lands on the plate faces instead of the cracks in a similar build, flip the `colorize_glow` gradient. Also, the bundled `render_preview` scene has no emission slot, so judge the glow on the exported emission map, not the preview sphere.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
**Caution specific to this material**: `warp_0` (`dry_earth`'s crack
signal) has THREE consumers here -- `blend_0` (crack darkening in
albedo), `colorize_4` (feeds the normal-relief chain via `blend_1`), and
`colorize_glow` (the emission glow). The whole `warp_0` -> `colorize_glow`
-> emission chain is kept inside ONE subgraph rather than split across
groups, since it is a single conceptual "glow" effect a viewer should be
able to reason about as one unit -- and per the stone category's own
`warp_0`-sensitivity precedent, `warp_0.amount` is never exposed as a
friendly parameter anywhere in this material.

- **Basalt Crust** -- `voronoi_0`, `colorize_1`, `colorize_0`,
  `colorize_plate`, `blend_0`. Exposed: `Plate size` (`voronoi_0.scale_x`),
  `Crust color` (`colorize_plate.gradient`), `Crack depth`
  (`blend_0.amount`).
- **Ember Glow** -- `warp_0`, `colorize_glow`. This is the whole glow
  chain from the crack signal through to the emission colorize, kept
  together per the caution above. `warp_0`'s other two outgoing
  connections (to `blend_0` and `colorize_4` in the other two groups)
  become separate boundary output ports from this group -- a single
  upstream node feeding multiple downstream groups is expected and
  mechanically safe, not a sign of a wrong split. Exposed: `Glow color`
  (`colorize_glow.gradient`) -- a downstream parameter, per the caution
  that only something downstream of `warp_0` should be exposed, never
  `warp_0.amount` itself.
- **Surface Relief** -- `perlin_1`, `colorize_3`, `perlin_0`, `blend_1`,
  `colorize_4`, `colorize`, `normal_map_0`, `rough_const`. Exposed:
  `Roughness` (`rough_const.gradient`). `normal_map_0.param1` stays at
  `dry_earth`'s untouched 0.99 default in this recipe, so it is not
  exposed (matching the stone category's `s07`/`s08` precedent of only
  exposing a relief parameter when the builder actually tunes it).

Verified after building, with extra scrutiny given the glow-chain caution:
`renders_match` against this material's own pre-retrofit baseline came
back at an exact `grid_mean_abs_diff` of `0.0` on all five exported maps,
checking the **emission map specifically** (not just albedo) to confirm
the three-way `warp_0` fan-out across group boundaries wired correctly:
albedo, emission, heightmap, normal, orm.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
