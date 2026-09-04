# l01_black_oiled_leather - Black oiled or waxed leather

_Category: leather. Open the graph: `cookbook/leather/l01_black_oiled_leather.ptex`._

A near-black, conditioned leather with a warm brown highlight lifted in the raised grain and a low-roughness polished sheen. The albedo thumbnail is nearly black and shows almost nothing; judge this one under real lighting, not the flat swatch.

## Recipe

Clones `crocodile_skin`, the proven leather donor whose cellular voronoi grain drives albedo (`colorize_1` to Material.albedo), roughness (`colorize_3` to Material.roughness), and a height chain (`voronoi_0` to `colorize_0` to `normal_map_0` to Material.normal). Recolor to a near-black warm base, lift a brown highlight into the raised grain, drop roughness low for a conditioned or polished finish, and keep the `param4=0` grain-relief fix. As with the other cell-based leathers in this set, the height ramp is domed (centers high, borders low) rather than left at the donor's stock inside-out mapping, so the scale bodies read raised and the seams read recessed.

Pitfall: the first render was too dark even in 3D. Lifting the highlight stop (grain around 0.22, 0.16, 0.11) made the grain actually read. Always confirm a dark leather like this under `render_preview` lighting before judging it flat.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
