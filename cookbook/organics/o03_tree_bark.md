# o03_tree_bark - Tree bark

_Category: organics. Open the graph: `cookbook/organics/o03_tree_bark.ptex`._

A weathered, knotty gray-brown bark surface with real grain relief carried
over unmodified from the wood donor.

## Recipe

Clone `wood` UNMODIFIED structurally. Unlike a material such as aluminum,
which straightens the grain to kill wood's knots, bark WANTS the knotty
waviness, so leave `wood`'s knot-overlay chain alone. Apply just the recolor
lever (weathered gray-brown, multi-stop for tonal variation) and push
roughness high. `wood`'s own normal chain already produces real grain relief
out of the box, so no `param4` fix is needed here. First-pass hit.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md` (the
identical grouping used by `cookbook/wood/w04_driftwood_gray.ptex` and
`w05_dark_walnut.ptex`, since this clones `wood`'s same 11-node graph
unmodified structurally, per the recipe above). Opening the graph shows 3
top-level nodes (these two groups plus `Material`) instead of the raw
11-node `wood` tangle:

- **Bark Grain** — the whole noise/pattern generator (the two grain
  perlins, the warp pair, the voronoi ring pattern and its colorize) plus the
  albedo colorize that paints its output. Exposed: `Bark color` (the
  weathered gray-brown albedo gradient). The generator's output (`blend_0`)
  also feeds the roughness ramp, the normal map, and the material's AO port
  directly — it rides along with the albedo colorize here so this group
  carries a real knob, rather than exposing nothing from a group of
  untouched donor defaults.
- **Surface Finish** — the roughness ramp and the normal map. Exposed:
  `Bark sheen` (the rough, matte roughness gradient).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
