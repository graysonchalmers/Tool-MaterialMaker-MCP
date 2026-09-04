# w04_driftwood_gray - Bleached driftwood

_Category: wood. Open the graph: `cookbook/wood/w04_driftwood_gray.ptex`._

Pale, low-saturation gray driftwood, sun-bleached and weathered.

## Recipe

Pure recolor of `wood`'s existing `colorize_2` (albedo) and `colorize_0`
(roughness) ramps, the same lever the frozen barn-wood reference case already
uses. Pale, low-saturation gray for the bleached driftwood look. `wood`'s own
generator chain already renders real grain relief out of the box, so this
doesn't touch the `normal_map` `param4` switch. First-pass hit.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
