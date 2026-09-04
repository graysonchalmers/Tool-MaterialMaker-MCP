# sf03_circuit_board - Circuit board

_Category: scifi. Open the graph: `cookbook/scifi/sf03_circuit_board.ptex`._

A dark PCB base with fine bright copper traces and scattered chip blocks. The visible bleed-through between layers that dogged this recipe for several sessions has since been root-caused and fixed.

## Recipe

Built in three passes. v1 tried a second `pattern` node with `mix=Xor` of two Square waves for the chip mask, but it rendered as pure stripes with the chip layer completely invisible at every threshold tried; `pattern`'s Xor mix mode is not documented beyond the enum name and was not worth reverse-engineering further. v2 swapped to the proven granite-speckle lever, voronoi port 2's flat per-cell random, which made chips appear but at scale 6 they were huge camo blobs. v3 raised the voronoi scale to 18 for small, sparse, chip-sized blocks.

Pitfall, now resolved: the trace stripes faintly bled through the chip shapes even with the blend set to full opacity. The root cause was a type confusion, not a mask-threshold problem: the recipe had fed the chips' albedo colorize (whose "on" value was gray 0.65, not fully opaque) as the layer's own opacity input, so the underlying trace layer showed through wherever that gray value fell short of solid. The fix was to split the mask off from the albedo: add a separate hard mask colorize on the same voronoi threshold to drive layer opacity, while the albedo colorize keeps driving only color. This is the same pattern the stone cookbook's s04 recipe already used with a dedicated 0/1 gap mask. The trace layer itself had the identical latent issue (its gold colorize, luminance around 0.57, was doubling as its own mask, letting the base color bleed through and reading as muted olive); the same split-mask fix made the traces render as solid bright gold.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
