# t06_cooled_lava - Cooled lava

_Category: terrain. Open the graph: `cookbook/terrain/t06_cooled_lava.ptex`._

Near-black basalt plates with glowing ember-orange cracks between them.

## Recipe

Built with the shared `_dry_earth_plates()` helper in `cookbook_terrain.py` at scale 5, near-black basalt per-plate color, and `warp_0` at 0.2. The helper gives this material a flat roughness texture (rather than `dry_earth`'s normally unconnected scalar roughness) so an ORM map exports correctly.

The glow taps `warp_0` directly, the crack signal, which is low at the cracks: a `colorize_glow` node maps the crack lows to bright ember-orange and the plate interiors to black, and that output feeds the Material node's emission input (port 3) with `emission_energy` set to 1.0.

Pitfall specific to this material: the glow polarity was correct on the first try here, but if the glow ever lands on the plate faces instead of the cracks in a similar build, flip the `colorize_glow` gradient. Also, the bundled `render_preview` scene has no emission slot, so judge the glow on the exported emission map, not the preview sphere.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
