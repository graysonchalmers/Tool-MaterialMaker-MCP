# s02_gray_granite - Polished gray granite

_Category: stone. Open the graph: `cookbook/stone/s02_gray_granite.ptex`._

Prompt: "polished gray granite". One of the Phase-3 hero materials (the frozen
15-case test set that took authoring quality from 3/15 to 15/15); folded into
the cookbook 2026-09-05 so it carries the same gates, card, and subgraph
grouping as every other material instead of living in a separate `examples/`
folder.

## Recipe

Clone `rock`. Granite's signature is a peppery spread of light and dark
mineral flecks, so the albedo voronoi (`voronoi_0`) is pushed to a fine cell
scale (44) with `randomness=1`, and the albedo colorize (`colorize_0`) is fed
straight from voronoi port 2, the per-cell random output, so each fine cell
becomes one flat random gray fleck (the earlier attempt blended a coarse
voronoi with smooth fbm and read as low-frequency fog). The ramp runs dark
biotite through mid feldspar to light quartz. Metallic is forced to zero
(`colorize_1`), roughness is low and narrow (`colorize_2`) for a polished slab.

Relief: `rock`'s normal chain (`voronoi_1` -> `warp_0` -> `normal_map_0`) is a
directly-fed analytic generator, so the default `param4=1` (buffered
edge_detect) renders flat. `param4=0` edge-detects the raw warped voronoi and
gives real polished-stone micro-relief; strength (`param1`) is kept at 0.35 so
it reads as a subtle speckle, not craggy rock. See the `param4=0` fix in the
guide (`guide://authoring`).

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 5 top-level nodes (one shared noise source, three
groups, `Material`) instead of the raw 11:

- **Fleck Color** (`voronoi_0`, `blend_0`, `colorize_0`). Exposed: `Fleck
  density` (voronoi scale), `Fleck colors` (the gray ramp). `blend_0` is the
  donor's original albedo blend, left in place but unconnected downstream in
  this variant.
- **Surface Finish** (`colorize_1`, `colorize_2`). Exposed: `Polish
  (roughness)`.
- **Stone Relief** (`voronoi_1`, `perlin_1`, `warp_0`, `normal_map_0`).
  Exposed: `Relief cell size`, `Relief strength`.

`perlin_0` stays top-level: it feeds both the color group and the finish
group, so folding it into either would just add a boundary port.

## See also

The invariant guide (`guide://authoring` or `docs/AUTHORING.md`) for the
rubric, the noise vocabulary, and the `param4=0` flat-normal fix. The frozen
scorecard this material was judged on is `docs/evidence/phase3/2026-08-26-iter1.md`.
