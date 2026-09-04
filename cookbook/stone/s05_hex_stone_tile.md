# s05_hex_stone_tile - Hex stone tile / mosaic

_Category: stone. Open the graph: `cookbook/stone/s05_hex_stone_tile.ptex`._

A natural-toned stone mosaic laid out on beehive's regular hex grid. Honest partial: this is a good-looking stone mosaic, not true cobblestone. `s07_cobblestone` supersedes this one for anyone who actually needs irregular cobblestone.

## Recipe

Reuses beehive's hex relief chain (the same lever as `man01`/`man02`), keeping the default per-cell-random blend so each tile reads as a genuinely different natural stone tone rather than a flat repeat. Scale tuned to `sx`7/`sy`5 (big cobbles, not a fine grid) with a narrow dark mortar band (0.0 to 0.08). A detail pass multiplies a fine perlin (`scale` 48, `iterations` 5) over both albedo and roughness through a `blend_type=2` (Multiply) node with no mask connected, since an unconnected opacity port defaults to a uniform 1.0 and so introduces no mask-edge speckle.

Pitfall specific to this material: beehive's hex grid is perfectly regular, and real cobblestone or crazy paving has irregular, variously sized stones, which this recipe does not have, so do not oversell it as cobblestone in user-facing copy. Separately, the tracked 512px preview thumbnail hid the fine detail-pass grain almost completely; it only became visible cropping the real 2048px render, so any "is this detailed enough" judgment on a fine high-frequency effect should check the full-resolution render, not just the docs preview.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
