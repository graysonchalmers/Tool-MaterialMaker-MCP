# w05_dark_walnut - Dark walnut, semi-gloss

_Category: wood. Open the graph: cookbook/wood/w05_dark_walnut.ptex._

Deep saturated brown walnut with a sealed, finished look, lower roughness
than a raw weathered wood surface.

## Recipe

Pure recolor of `wood`'s existing `colorize_2` (albedo) and `colorize_0`
(roughness) ramps, the same lever the frozen barn-wood reference case already
uses. Deep saturated brown, with roughness lowered relative to barn wood's
raw weathered surface for a sealed, finished walnut look. `wood`'s own
generator chain already renders real grain relief out of the box, so this
doesn't touch the `normal_map` `param4` switch. First-pass hit.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
