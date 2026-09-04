# s07_cobblestone - True irregular cobblestone

_Category: stone. Open the graph: `cookbook/stone/s07_cobblestone.ptex`._

True irregular cobblestone with genuinely varied plate sizes and recessed mortar. Closes the gap `s05_hex_stone_tile` left open: this is the voronoi-plate approach that card's own notes flagged as untried.

## Recipe

Clones `dry_earth`, scales `voronoi_0` from 4 to 6 (cobble-sized plates), and feeds `voronoi_0` port 2 (per-cell random) through a multi-tone stone gradient rewired into `blend_0` port 1 in place of the flat perlin earth base, so each plate reads as a distinct stone while the existing warped-crack Multiply overlay reads as recessed mortar. `warp_0.amount` is dropped to 0.12 for clean thin mortar with a slight organic wobble.

Pitfall specific to this material: two traps cost a pass each. First, the initial tone gradient was too narrow (0.30 to 0.55, muted) so plates all looked uniform; it needed widening hard across both value and hue. Second, a broad gray haze inside the plates was mistaken for a gradient problem, but it was actually `dry_earth`'s stock `warp_0.amount` of 0.4 smearing the crack shadows into washes across the plates, fixed by dropping that value to 0.12. Judge the result in 3D with `render_preview`: the cobbles should bulge and the mortar should recess.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
