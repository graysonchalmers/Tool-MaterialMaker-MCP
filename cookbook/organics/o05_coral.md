# o05_coral - Coral

_Category: organics. Open the graph: cookbook/organics/o05_coral.ptex._

A pink/orange, matte, porous coral surface with pronounced pitted relief.

## Recipe

Retype the generator to `fbm` with `noise=2` (Cellular) instead of `voronoi`.
Same "distinct cells" family, but fbm's cellular noise gives a porous,
irregularly-pitted surface rather than voronoi's flat-faceted cells, a better
match for coral's texture. Coral pink/orange albedo, matte roughness, and a
pronounced `param4=0` relief for the pitted bumps. First-pass hit.

Worth remembering generally: `fbm`'s `noise` enum (Value / Perlin / Cellular
x6) is a whole family of generator shapes, an alternative to `voronoi` any
time a cell-like pattern is needed.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
