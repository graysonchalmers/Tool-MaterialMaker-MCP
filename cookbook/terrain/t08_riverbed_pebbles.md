# t08_riverbed_pebbles - Riverbed pebbles

_Category: terrain. Open the graph: `cookbook/terrain/t08_riverbed_pebbles.ptex`._

Discrete tumbled river pebbles with a damp sheen, distinguished from `t05_cracked_ice`'s connected crack network by recessed contact joints instead of crack lines.

## Recipe

Built with the shared `_dry_earth_plates()` helper in `cookbook_terrain.py` at scale 8, a river-tumbled multicolor palette (gray/tan/slate/brown/cream), `warp_0` at 0.02, and roughness 0.2 for a damp sheen. The low warp value produces recessed contact-shadow joints between discrete packed pebbles rather than warped crack lines; that single change is what separates this material from t05's ice plates despite sharing the same underlying helper.

No separate pitfall pass was needed once the warp value was set low; the recessed-joint read came through on the first pass at 0.02.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
