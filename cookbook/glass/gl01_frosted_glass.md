# gl01_frosted_glass - Frosted glass

_Category: glass. Open the graph: `cookbook/glass/gl01_frosted_glass.ptex`._

Matte, sandblasted-glass surface: a dense field of fine, light crystalline facets separated by dark micro-crack boundaries, cool blue-gray, diffuse (no gloss). The first cookbook material authored from a reference PHOTO instead of a text prompt, proving out the "Authoring from a reference photo" section of `docs/AUTHORING.md`.

## Reference photo

["Frosted glass surface.jpg"](https://commons.wikimedia.org/wiki/File:Frosted_glass_surface.jpg), (c) J. Koopstra, CC BY-SA 4.0, via Wikimedia Commons.

## Decomposition

Reading the photo against the rubric in `docs/AUTHORING.md`:

- **Color/tone**: cool blue-gray, low saturation, a narrow value range, no per-region color variation, matte diffuse light response, not glossy or reflective.
- **Pattern topology**: a dense, uniformly distributed field of light angular facets separated by dark, thin boundary lines, the same CONNECTED CRACK NETWORK topology as `dry_earth`'s voronoi-plate cracks, just far finer and denser than any existing dry_earth-derived material.
- **Scale/frequency**: very fine and uniform, no large-scale clumping or directional flow beyond a faint diagonal wave, much finer than granite's fine-fleck voronoi (scale 44) or gravel's pebble scale (14).
- **Relief cues**: the photo shows crisp micro-facet edges, but physically, frosted glass is nearly flat at the macro scale, the visible light diffusion is a MICRO-surface scattering effect, not a bump. Relief was kept deliberately subtle rather than matched to the crisp look of the crack lines in the photo.

## Recipe

Clone `dry_earth` (topology match, not a from-scratch build). `voronoi_0` scale pushed to 60 (vs. dry_earth's default 4) for fine, dense facets, `randomness=1`. `colorize_0` (plate albedo) recolored to a narrow cool blue-gray range. `colorize_1` (crack ramp) tightened to an 0.08 threshold for thin, clean facet edges. `warp_0.amount` dropped to 0.05, well below even the masonry family's clean-joint value of ~0.12, since these facets need to read as fine and regular, not organically warped. `blend_0.amount` at 0.5 for visible but not overpowering crack darkening. Forced non-metal (`Material.metallic=0`). Roughness pushed high and left fairly uniform (`0.88`) since frosted glass is diffuse, not glossy. `normal_map_0` uses the `param4=0` fix (see the guide) but at a low `param1=0.15`, subtle relief, consistent with the "physically near-flat" reasoning above rather than chasing the photo's crisp micro-edges literally.

Same ORM gap as the `dry_earth`-derived terrain materials: the donor leaves the roughness input unconnected, so a scalar-only roughness exports no ORM map. Fixed the same way `_dry_earth_plates()` does in `cookbook_terrain.py`, a flat constant-gray roughness texture (`rough_const`) wired into `Material` port 2, so an ORM map actually exports for the preview.

## Honest limitation

Material Maker's `material` node has no true transparency or refraction model. This recipe approximates frosted glass as an opaque, matte, finely-faceted diffuse surface, which is the right call for how it will be *used* (a wall panel, a frosted door insert, a diffuser surface visible under normal lighting) but it is not simulating light transmission through the glass. If a use case specifically needs to see through the material, this recipe is not that.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow (including the "Authoring from a reference
photo" section this material exercises), the noise vocabulary, and the
`param4=0` flat-normal fix.
