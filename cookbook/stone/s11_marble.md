# s11_marble - Polished marble

_Category: stone. Open the graph: `cookbook/stone/s11_marble.ptex`._

Polished Carrara-style marble with soft cloudy veins, the one non-paving recipe in the stone set.

## Recipe

Uses the same `dry_earth` donor as the paving materials, but for its vein structure rather than its plates, and inverts nearly every lever from the paving recipes. `voronoi_0` scale is set to 3 (few large sweeping veins). `warp_0.amount` is raised from the paving materials' 0.12 up to 0.5, since on marble the warp smear is not haze to remove, it is the whole look: soft cloudy veins wandering across the slab. There is no per-cell tone, since marble reads as one uniform stone rather than a mosaic: the base is a near-white cream on `colorize_0`, and the veins come from the crack Multiply eased to 0.5.

Polish is set up on the Material node directly: metallic is zeroed by setting `colorize_3` (feeding Material metallic) to all black, and roughness is dropped to 0.15 on the Material node's own `roughness` parameter, since its port 2 is left unconnected so the scalar param applies. `normal_map` `param1` is dropped to 0.1 so the veins carry only a whisper of relief.

Pitfall specific to this material: the material is genuinely glossy, but `render_preview`'s dark backdrop gives a low-roughness dielectric nothing to reflect, so it reads honed or matte in the preview, the same reason pure metals render dark there. Scope note: this recipe gives soft Carrara veining, not the angular fragments of breccia marble, which the un-warped voronoi cells would actually suit better.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
**`warp_0` caution (highest scrutiny in this category)**: unlike every
other `dry_earth` clone in this set, this builder never rewires the donor
at all -- `colorize_0` (not a `colorize_cobble` replacement) is still
`blend_0`'s port1 background exactly as `dry_earth` ships it, so `warp_0`
stays paired with `blend_0`, its most direct and most visible consumer
here (the flowing crack/vein network). `warp_0.amount` is raised to 0.5 --
the one place in this whole category where the warp smear **is** the
intended look (soft cloudy marble veining) rather than haze to kill, and
the brief's own worked example for why this parameter is never exposed as
a friendly tunable. It is not exposed here either. `blend_0`'s own
`amount` (0.5, softening the veins) carries no port2 mask (unconnected ->
uniform 1.0) and is a genuine scalar knob, so it is exposed as `Vein
softness`. `colorize_3` (metallic, zeroed) stays an unexposed member of
the relief group -- "make this non-metal marble metallic" isn't a friendly
knob worth surfacing. Opening the graph shows 2 top-level groups instead
of the raw 12-node graph:

- **Marble Base & Veins** -- `voronoi_0`, `colorize_1`, `warp_0`,
  `perlin_0`, `colorize_0`, `blend_0`. Exposed: `Vein scale`
  (`voronoi_0.scale_x`), `Base color` (`colorize_0.gradient`), `Vein
  softness` (`blend_0.amount`).
- **Relief & Metallic** -- `perlin_1`, `colorize_3`, `colorize_4`,
  `blend_1`, `colorize`, `normal_map_0`. Exposed: `Vein relief`
  (`normal_map_0.param1`).

Verified after building, with the extra scrutiny the category caution
calls for on this material specifically: `renders_match` against this
material's own pre-retrofit baseline came back at an exact
`grid_mean_abs_diff` of `0.0` on all four exported maps (albedo, heightmap,
normal, orm) -- the high `warp_0.amount` value was preserved bit-for-bit,
not just structurally guaranteed by `group_into_subgraph`'s port-preserving
mechanics.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
