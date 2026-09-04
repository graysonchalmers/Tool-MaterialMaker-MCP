# s10_flagstone - Flagstone / slate paving

_Category: stone. Open the graph: `cookbook/stone/s10_flagstone.ptex`._

Large flat sawn slate slabs with recessed joints, tuned as the opposite of `s07_cobblestone` on nearly every axis.

## Recipe

A `dry_earth` clone with `voronoi_0` scale set to 4 (few big slabs). `normal_map` `param1` is dropped from 0.99 to 0.5 for flat slab tops, since cobbles bulge but sawn flagstones are flat and relief should live only in the recessed joints. `warp_0` is held at the haze-free 0.12 used across the paving materials, with a cool blue-gray / green-gray slate palette and low per-slab tonal variation, since slate slabs are fairly uniform compared to cobblestone's strong hue spread.

No separate pitfall pass was needed for this one; the recipe is a direct inversion of s07's cobblestone levers (flat instead of bulging, few large slabs instead of many small plates, low variation instead of high).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
