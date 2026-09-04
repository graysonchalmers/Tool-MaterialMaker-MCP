# l02_distressed_two_tone - Distressed two-tone worn leather

_Category: leather. Open the graph: `cookbook/leather/l02_distressed_two_tone.ptex`._

A dark saddle base leather with a lighter rubbed tan showing through irregular worn patches, for both albedo and a small roughness lift.

## Recipe

Clones `crocodile_skin` and uses the masked-composite lever (the same shape as other two-layer weathering recipes in this cookbook), but here both layers are leather rather than two different materials. The wear mask is the entire recipe: it decides whether the result reads as genuine wear or as animal-print spots.

Pitfall: the first pass used a coarse perlin (scale 7) with a narrow threshold band and a big base-versus-worn tonal gap, which produced a few giant high-contrast blotches that read as cow-hide spots, not wear. Fixed with a finer perlin (scale 16, iterations 6), a wide feathered threshold band (0.40 to 0.72), and a small tonal gap between base and worn, so the rubs read as a distributed change of finish rather than a second color. When a wear or distress mask is producing blotches instead of gradual wear, widen the band and shrink both the noise scale and the tonal gap together, not just one of the three.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
