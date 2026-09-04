# o05_coral - Coral

_Category: organics. Open the graph: `cookbook/organics/o05_coral.ptex`._

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

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`,
sharing a helper (`_group_crocodile_skin_pattern` in
`quality/cookbook_organics.py`) with `o04_snake_scales` since both clone
`crocodile_skin`'s identical 6-node graph (the `fbm` retype above changes
`voronoi_0`'s noise, not its name or wiring). Opening the graph shows 4
top-level nodes instead of the raw 6-node `crocodile_skin` tangle:

- **Surface Pattern** — `voronoi_0` (the retyped `fbm` cellular generator)
  plus `colorize_1` (its albedo colorize). Exposed: `Cell size` (the
  cellular pattern scale) and `Coral color` (the pink/orange gradient).
- **Surface Finish** — `colorize_0` (explicitly set to an identity ramp,
  feeds the normal chain), `colorize_3` (the matte roughness colorize), and
  `normal_map_0`. Exposed: `Surface tone` (the roughness gradient) and
  `Pore relief` (the pronounced `normal_map_0` strength for the pitted
  bumps).
- `uniform_0` (Material's metallic scalar, an untouched donor default
  feeding one port directly) is left top-level, ungrouped.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
