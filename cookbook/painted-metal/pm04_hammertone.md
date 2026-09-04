# pm04_hammertone - Hammertone, bronze-gray

_Category: painted-metal. Open the graph: `cookbook/painted-metal/pm04_hammertone.ptex`._

Bronze-gray hammertone paint with a dimple field, the strongest structural read of the whole painted-metal set.

## Recipe

Clones `rock`, using the same normal chain as pm01's powder coat but at a medium cell size (`voronoi_1` scale 14) so the rounded cells read as hammer-blow dimples: bigger than pm01's fine orange peel and smaller than `rock`'s native lumps, with the deepest relief in the family (`param1` 0.42, `param4=0`) because the dimples are the whole point of this material. Bronze-gray albedo carries per-cell tonal variation so the dimples catch the light, semi-gloss roughness gives the metallic-looking sheen, and metallic stays 0 since it is paint, not exposed metal.

Pitfall: this material runs a little dark in the preview scene; lift the bronze albedo stops if a brighter finish is wanted.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
