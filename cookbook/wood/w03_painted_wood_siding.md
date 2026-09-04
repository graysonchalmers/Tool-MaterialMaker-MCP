# w03_painted_wood_siding - Painted plank siding, worn

_Category: wood. Open the graph: `cookbook/wood/w03_painted_wood_siding.ptex`._

Worn painted plank siding: mostly painted with sparse worn patches showing
the wood grain underneath, built from a masked paint-over-wood composite.

## Recipe

The masked paint-over-wood composite is the same lever used for
rusted-painted-steel, but the DONOR choice is what actually made or broke
this material. Three passes cloning plain `wood` (pure vertical grain, no
board structure) read as abstract paint-splatter blobs no matter how the mask
was tuned, because nothing in `wood` says "boards," so nothing said "siding."
The fix was the donor: clone `wooden_floor` instead (its `bricks_0` at 10 rows
by 1 column gives horizontal planks with seam lines, and its `blend_0`
already carries plank albedo plus relief), then composite the paint over
`blend_0`. On a planked base it reads as painted siding immediately.

Lesson specific to this material: match the donor's underlying structure
(planks, in this case) to what the material fundamentally is before tuning
color or mask, no amount of surface tuning adds structure a donor doesn't
have.

Two more rounds of tuning followed direct review: (1) the paint gradient
topped out at only 0.88 brightness with a warm yellow-brown cast, which read
as a dirty stain rather than paint; brightened to 0.84 to 0.94 and neutralized
the cast. (2) the wide 0.20 to 0.50 mask band (needed to kill an earlier
`blend`-edge speckle artifact) also made wood the majority and paint the
minority, backwards for siding that should read as mostly painted with worn
patches; fixed by moving the band to 0.55 to 0.72 (same width, shifted
position) so wood is the sparse minority showing through. Band position
controls majority/minority balance independently of the width that controls
edge softness, so this didn't reintroduce the speckle.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
