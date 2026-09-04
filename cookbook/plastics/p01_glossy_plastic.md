# p01_glossy_plastic - Glossy injection-molded plastic

_Category: plastics. Open the graph: `cookbook/plastics/p01_glossy_plastic.ptex`._

A smooth, glossy, saturated red plastic surface, the first entry in the
plastics category and the first cookbook material built from scratch rather
than cloned from a donor.

## Recipe

Every other cookbook category so far differentiates through visible
micro-pattern (weave, crack network, cell facets). Plastic differentiates
the opposite way, as a smooth, patternless surface, so there is no donor
whose topology fits: this graph is built from scratch via
`_from_scratch_noise_material` (perlin -> colorize -> Material, perlin ->
normal_map -> Material). The albedo gradient is a narrow, near-single-color
band (saturated red, minimal spread) so any residual perlin variation stays
invisible in color. Non-metallic, low roughness (`0.18`) for the glossy
specular kick. Normal relief is kept just above zero (`param1=0.04`) rather
than exactly flat, a truly dead-flat normal is physically wrong for a real
molded surface, this keeps only the faintest micro-variation. The
`param4=0` fix (see the guide) still applies since perlin feeds `normal_map`
directly, the default `param4=1` would read even flatter still.

Same ORM gap as every scalar-roughness recipe: `_from_scratch_noise_material`
leaves roughness as a Material parameter with no texture input, which exports
no ORM map. Fixed the same way `gl01_frosted_glass` and the `dry_earth`-derived
terrain materials are, a flat constant-gray roughness texture (`rough_const`)
wired into `Material` port 2, so an ORM map exports for the preview.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
