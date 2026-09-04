# o06_lichen_crusted_rock - Lichen-crusted rock

_Category: organics. Open the graph: cookbook/organics/o06_lichen_crusted_rock.ptex._

Gray stone with a patchy green-gray lichen crust, using a two-layer masked
blend to composite the crust over the base stone.

## Recipe

Clone `rusted_metal`'s two-layer masked-blend structure (the same lever the
weathered-copper reference material already proved) but recolor to
stone-plus-lichen instead of metal-plus-patina: base (`colorize_2`) to gray
stone, patch (`colorize_1`) to lichen green-gray, widen the mask
(`colorize_3` threshold) for more coverage.

Pitfall specific to this material: `rusted_metal` wires the Material node's
metallic input straight off the mask (`colorize_3`), which is correct for a
metal donor but wrong once recolored to stone. `drop_conn` that connection
and force the Material's own `metallic` scalar to 0. Also graft a light
`normal_map` fed from the mask (`rusted_metal` ships with no normal chain at
all) so lichen patches read as faintly raised rather than a pure flat-color
swap, a nice-to-have the donor's own verified reference cases don't bother
with.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
