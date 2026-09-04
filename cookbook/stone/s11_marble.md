# s11_marble - Polished marble

_Category: stone. Open the graph: `cookbook/stone/s11_marble.ptex`._

Polished Carrara-style marble with soft cloudy veins, the one non-paving recipe in the stone set.

## Recipe

Uses the same `dry_earth` donor as the paving materials, but for its vein structure rather than its plates, and inverts nearly every lever from the paving recipes. `voronoi_0` scale is set to 3 (few large sweeping veins). `warp_0.amount` is raised from the paving materials' 0.12 up to 0.5, since on marble the warp smear is not haze to remove, it is the whole look: soft cloudy veins wandering across the slab. There is no per-cell tone, since marble reads as one uniform stone rather than a mosaic: the base is a near-white cream on `colorize_0`, and the veins come from the crack Multiply eased to 0.5.

Polish is set up on the Material node directly: metallic is zeroed by setting `colorize_3` (feeding Material metallic) to all black, and roughness is dropped to 0.15 on the Material node's own `roughness` parameter, since its port 2 is left unconnected so the scalar param applies. `normal_map` `param1` is dropped to 0.1 so the veins carry only a whisper of relief.

Pitfall specific to this material: the material is genuinely glossy, but `render_preview`'s dark backdrop gives a low-roughness dielectric nothing to reflect, so it reads honed or matte in the preview, the same reason pure metals render dark there. Scope note: this recipe gives soft Carrara veining, not the angular fragments of breccia marble, which the un-warped voronoi cells would actually suit better.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
