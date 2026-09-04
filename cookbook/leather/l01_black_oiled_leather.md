# l01_black_oiled_leather - Black oiled or waxed leather

_Category: leather. Open the graph: `cookbook/leather/l01_black_oiled_leather.ptex`._

A near-black, conditioned leather with a warm brown highlight lifted in the raised grain and a low-roughness polished sheen. The albedo thumbnail is nearly black and shows almost nothing; judge this one under real lighting, not the flat swatch.

## Recipe

Clones `crocodile_skin`, the proven leather donor whose cellular voronoi grain drives albedo (`colorize_1` to Material.albedo), roughness (`colorize_3` to Material.roughness), and a height chain (`voronoi_0` to `colorize_0` to `normal_map_0` to Material.normal). Recolor to a near-black warm base, lift a brown highlight into the raised grain, drop roughness low for a conditioned or polished finish, and keep the `param4=0` grain-relief fix. As with the other cell-based leathers in this set, the height ramp is domed (centers high, borders low) rather than left at the donor's stock inside-out mapping, so the scale bodies read raised and the seams read recessed.

Pitfall: the first render was too dark even in 3D. Lifting the highlight stop (grain around 0.22, 0.16, 0.11) made the grain actually read. Always confirm a dark leather like this under `render_preview` lighting before judging it flat.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, via a
shared `_group_leather_grain` helper reused across `l01`/`l03`/`l04` (the
three leathers in this set that keep `crocodile_skin`'s structure
unmodified). This donor carries no `blend` node (confirmed by reading
`quality/donors/crocodile_skin.ptex`'s own `connections` list), so there is
no port-source tracing to do here. Opening the graph shows 2 top-level
groups (plus `Material` and the untouched metallic `uniform_0`) instead of
the raw 7-node graph:

- **Grain Pattern** — `voronoi_0` (left at its donor default scale — this
  builder only recolors, it never tunes `voronoi_0`'s own parameters) and
  `colorize_1` (the recolored grain albedo). `voronoi_0` also feeds
  **Surface Finish**'s height and roughness colorizes directly (a single
  upstream node feeding three downstream consumers, folded into the group
  paired with the albedo it drives most directly). Exposed: `Oiled leather
  color`. Since `voronoi_0` itself is never touched, this group's only
  exposed parameter is the color — no bare untouched `.mmg` default is
  exposed.
- **Surface Finish** — `colorize_0` (height, domed by `_dome_the_cells`),
  `colorize_3` (roughness, tuned low for the polished finish),
  `normal_map_0` (`param4=0`, `param1=0.45`). Exposed: `Polish level`,
  `Grain relief`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0` on
all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
