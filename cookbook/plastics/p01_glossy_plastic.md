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

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 3 top-level nodes (two groups plus `Material`)
instead of the raw 5-node perlin/colorize/normal_map/rough_const tangle:

- **Surface Color** — the sole noise generator (`perlin_0`) plus the albedo
  colorize (`colorize_0`). Exposed: `Color` (the albedo gradient), `Pattern
  scale` (the perlin's `scale_x`).
- **Surface Finish** — the normal-map chain plus the flat-roughness constant
  (`normal_map_0`, `rough_const`). Exposed: `Roughness`, `Surface relief`
  (the normal map's strength).

Unlike `gl01_frosted_glass` (which left its two shared noise generators
top-level since each fed both groups), `perlin_0` here is folded into
`Surface Color` rather than kept top-level: it is the single noise source
feeding all three downstream nodes (`colorize_0`, `normal_map_0`,
`rough_const`), so the only way to leave it top-level would still need
boundary ports into both groups, and the alternative -- a `Surface Color`
group containing only `colorize_0` -- would be a degenerate single-node
"group" that doesn't actually simplify anything. `Surface Finish`'s noise
input arrives as a plain boundary port from `Surface Color`; that's an
artifact of one generator feeding two visually distinct concerns (color and
relief/roughness), not a modeling error.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
