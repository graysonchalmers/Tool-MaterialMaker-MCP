# w05_dark_walnut - Dark walnut, semi-gloss

_Category: wood. Open the graph: `cookbook/wood/w05_dark_walnut.ptex`._

Deep saturated brown walnut with a sealed, finished look, lower roughness
than a raw weathered wood surface.

## Recipe

Pure recolor of `wood`'s existing `colorize_2` (albedo) and `colorize_0`
(roughness) ramps, the same lever the frozen barn-wood reference case already
uses. Deep saturated brown, with roughness lowered relative to barn wood's
raw weathered surface for a sealed, finished walnut look. `wood`'s own
generator chain already renders real grain relief out of the box, so this
doesn't touch the `normal_map` `param4` switch. First-pass hit.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`
(same grouping as `w04_driftwood_gray`, since both clone `wood`'s identical
11-node graph and differ only in the two gradients below). Opening the graph
shows 3 top-level nodes (these two groups plus `Material`) instead of the raw
11-node `wood` tangle:

- **Wood Grain** — the whole noise/pattern generator (the two grain
  perlins, the warp pair, the voronoi ring pattern and its colorize) plus the
  albedo colorize that paints its output. Exposed: `Wood color` (the deep
  walnut-brown albedo gradient). The generator's output (`blend_0`) also
  feeds the roughness ramp, the normal map, and the material's AO port
  directly, all in **Surface Finish** or top-level `Material` — it rides
  along with the albedo colorize here so this group carries a real knob,
  rather than exposing nothing from a group of untouched donor defaults.
- **Surface Finish** — the roughness ramp and the normal map. Exposed:
  `Finish sheen` (the semi-gloss roughness gradient).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
