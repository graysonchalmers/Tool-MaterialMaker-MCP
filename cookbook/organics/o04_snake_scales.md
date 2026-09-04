# o04_snake_scales - Snake scales

_Category: organics. Open the graph: `cookbook/organics/o04_snake_scales.ptex`._

An olive-to-khaki reptile scale surface with faceted per-cell relief that
reads as scales through the normal map rather than the albedo.

## Recipe

`crocodile_skin`'s own default voronoi cellular pattern IS already a
reptile-scale layout, that's what it was built to look like, so no retype is
needed: pure recolor lever (olive to khaki, lower roughness than leather for
a scale sheen). Proactively apply the `param4=0` fix even though it wasn't
strictly required for the reference leather HIT: `crocodile_skin`'s normal
chain (`voronoi_0` to `colorize_0` to `normal_map_0`) is directly-fed with no
buffer, the same shape as the classic denim blocker, so it renders flat by
default. The faceted per-cell relief this produces is a better tell for
"scales" than the albedo, which stays fairly soft and blurred by the donor's
own design, and for this material that's fine: the read comes through the
normal, not the color.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`,
sharing a helper (`_group_crocodile_skin_pattern` in
`quality/cookbook_organics.py`) with `o05_coral` since both clone
`crocodile_skin`'s identical 6-node graph unmodified structurally. Opening
the graph shows 4 top-level nodes instead of the raw 6-node `crocodile_skin`
tangle:

- **Surface Pattern** — `voronoi_0` (the scale-cell generator) plus
  `colorize_1` (its albedo colorize). Exposed: `Scale size` (the
  denser/smaller scale-cell scale) and `Scale color` (the olive-to-khaki
  gradient).
- **Surface Finish** — `colorize_0` (untouched donor default, feeds the
  normal chain), `colorize_3` (the roughness colorize), and `normal_map_0`.
  Exposed: `Sheen` (the roughness gradient) and `Scale relief` (the
  `normal_map_0` strength driving the proactive `param4=0` fix above).
- `uniform_0` (Material's metallic scalar, an untouched donor default
  feeding one port directly) is left top-level, ungrouped.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
