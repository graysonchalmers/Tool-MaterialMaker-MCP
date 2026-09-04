# sf03_circuit_board - Circuit board

_Category: scifi. Open the graph: `cookbook/scifi/sf03_circuit_board.ptex`._

A dark PCB base with fine bright copper traces and scattered chip blocks. The visible bleed-through between layers that dogged this recipe for several sessions has since been root-caused and fixed.

## Recipe

Built in three passes. v1 tried a second `pattern` node with `mix=Xor` of two Square waves for the chip mask, but it rendered as pure stripes with the chip layer completely invisible at every threshold tried; `pattern`'s Xor mix mode is not documented beyond the enum name and was not worth reverse-engineering further. v2 swapped to the proven granite-speckle lever, voronoi port 2's flat per-cell random, which made chips appear but at scale 6 they were huge camo blobs. v3 raised the voronoi scale to 18 for small, sparse, chip-sized blocks.

Pitfall, now resolved: the trace stripes faintly bled through the chip shapes even with the blend set to full opacity. The root cause was a type confusion, not a mask-threshold problem: the recipe had fed the chips' albedo colorize (whose "on" value was gray 0.65, not fully opaque) as the layer's own opacity input, so the underlying trace layer showed through wherever that gray value fell short of solid. The fix was to split the mask off from the albedo: add a separate hard mask colorize on the same voronoi threshold to drive layer opacity, while the albedo colorize keeps driving only color. This is the same pattern the stone cookbook's s04 recipe already used with a dedicated 0/1 gap mask. The trace layer itself had the identical latent issue (its gold colorize, luminance around 0.57, was doubling as its own mask, letting the base color bleed through and reading as muted olive); the same split-mask fix made the traces render as solid bright gold.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. This
is the one material in the cookbook with documented history of a subtle
opacity-masking bug (above), so the grouping decision and its verification
get extra scrutiny here. Opening the graph shows 4 top-level nodes (three
groups plus `Material`) instead of the raw 13-node graph:

- **Circuit Traces** — `perlin_0`, `colorize_base`, `pattern_traces`,
  `colorize_traces`, `colorize_traces_mask`, `blend_traces`. Exposed:
  `Board color` (`colorize_base`'s gradient), `Trace density`
  (`pattern_traces`'s `x_scale`), `Trace color` (`colorize_traces`'s
  gradient).
- **Chip Blocks** — `voronoi_chips`, `colorize_chips`,
  `colorize_chips_mask`, `blend_chips`. Exposed: `Chip size`
  (`voronoi_chips`'s `scale_x`), `Chip color` (`colorize_chips`'s gradient).
- **Surface Finish** — `colorize_rgh`, `normal_map_0`. Exposed: `Surface
  sheen`, `Relief strength`.

Both `blend` nodes' port-2 mask inputs (`colorize_traces_mask` ->
`blend_traces` port 2, and `colorize_chips_mask` -> `blend_chips` port 2 --
the exact wiring the bug fix above depends on) are grouped together with
the blend node they feed, since each mask colorize has exactly one
consumer here (unlike a genuinely shared multi-consumer signal, which would
warrant its own separate group). `group_into_subgraph` copies internal
connections verbatim, so grouping cannot alter a from/to/port triple; this
was additionally confirmed after the fact by reading the collapsed
subgraphs' own serialized `connections` and checking both mask-to-blend
edges are present unchanged. Critically, neither mask colorize's gradient
is exposed as a friendly parameter — only the corresponding albedo
colorize's gradient is — so no end-user-facing knob can touch the hard 0/1
opacity threshold the fix depends on.

Verified with extra rigor beyond the rest of this category's retrofit: all
three exported maps (albedo, normal, orm), not just albedo, were compared
against this material's own pre-retrofit baseline render, each landing at
an exact `grid_mean_abs_diff` of `0.0` (not merely under the `3.0`
tolerance) — a genuinely tight match, not a pass near the tolerance edge.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
