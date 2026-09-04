# t04_grass_field - Grass field

_Category: terrain. Open the graph: `cookbook/terrain/t04_grass_field.ptex`._

A soil-and-grass field where grass is the dominant coverage and dirt shows through only in patches.

## Recipe

Clones `rusted_metal`'s two-layer masked-blend structure, the same template `o06_lichen_crusted_rock` uses, and recolors it to soil and grass. Unlike lichen, which is sparse patches on a dominant base, grass needs to be the dominant layer with dirt only showing through in patches, which this recipe achieves with the mask threshold set high, at 0.65.

Pitfall specific to this material: v1 moved the mask threshold down to 0.22, reasoning by analogy with how other recipes widen their patch layer by lowering the threshold. That rendered almost the opposite of the intended look: near-total soil with only tiny green flecks, confirmed by a nearly flat normal map showing the mask was saturated one way across almost the whole image rather than shifting gradually. Flipping the threshold up to 0.65 instead produced the intended dominant-grass-with-dirt-patches look on the first try.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
