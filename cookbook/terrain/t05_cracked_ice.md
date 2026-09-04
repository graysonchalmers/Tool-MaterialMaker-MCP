# t05_cracked_ice - Cracked ice

_Category: terrain. Open the graph: `cookbook/terrain/t05_cracked_ice.ptex`._

Glassy blue-white ice with a connected network of sharp surface cracks; smooth flat plate faces with relief only at the cracks.

## Recipe

Built with the shared `_dry_earth_plates()` helper in `cookbook_terrain.py` at scale 5, glassy blue-white per-plate tint, `warp_0` at 0.12 for clean sharp cracks, and roughness 0.12. The helper also gives this material a flat roughness texture rather than a scalar, so an ORM map actually exports (`dry_earth` normally leaves the roughness input unconnected, which renders no ORM and hides a wet or glossy sheen in the 3D preview).

The key move for the ice look specifically: the crack-only signal (`colorize_4`, sourced from `warp_0`) is fed into the normal-prep colorize instead of `dry_earth`'s perlin-grain height (`blend_1`), so plate faces stay smooth and only the cracks carry relief.

Pitfall specific to this material: without that swap, the plates read as frosted or sandy concrete rather than glassy ice. Judge smoothness on the normal map and plate faces directly; the low-roughness gloss is real but the preview's dark backdrop cannot show it, the same caveat that applies to `t06_cooled_lava`'s emission.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
