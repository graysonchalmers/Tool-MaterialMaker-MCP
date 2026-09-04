# t02_fresh_snow - Fresh snow

_Category: terrain. Open the graph: `cookbook/terrain/t02_fresh_snow.ptex`._

Near-white smooth snow drifts with a faint cold tint in the low points.

## Recipe

Clones `rock` and keeps its smooth blobby structure, since a smooth source is fine when the target is genuinely near-flat, and snow drifts are exactly that case, the same reasoning `s02` granite used for reusing `rock`. Albedo is near-white with a faint cold blue-gray in the low points. Metallic is forced near-zero, since this donor's `perlin_0` feeds metallic directly by default, which is wrong for snow. A proactive `param4=0` is applied at low strength (about 0.18) for soft drifts rather than stone-scale relief.

No pitfall pass was needed beyond the metallic override; the low-strength relief was set proactively rather than discovered by a failed first attempt.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
