# t09_rippled_wet_sand - Rippled wet sand

_Category: terrain. Open the graph: `cookbook/terrain/t09_rippled_wet_sand.ptex`._

Tight, near-parallel wet-sand ripple bands with a damp khaki tone -- the first cookbook material built on `wavelet_noise` (zero prior use in the cookbook before this).

## Recipe

Built from scratch (no donor has this topology) via `_from_scratch_noise_material`, then the placeholder `perlin_0` is `retype()`d to `wavelet_noise` -- the same move `t07_forest_floor` uses to swap in `fbm`; output port 0 is a plain `f` scalar on both node types, so the swap is connection-safe.

**Round 2 retune** (controller self-screen at 512 caught two problems in round 1 -- no banding, too dark/muddy):

- **Banding needs STRONG anisotropy, not scale/frequency alone.** Round 1 kept `scale_x == scale_y` and rendered as an isotropic dappled mottle (mud/coffee grounds), never bands, at any scale. Reading `wavelet_noise.mmg`'s actual GLSL directly (`z-Git/material-maker/addons/material_maker/nodes/wavelet_noise.mmg`) shows `size = vec2(scale_x, scale_y)` tiles each axis independently -- equal scale can only ever tile equally in both directions, so it can never band. Fixed with strong anisotropy: `scale_x=2` (the field barely varies along x, so each feature stretches long across it), `scale_y=24` (tight repetition along y). The result is elongated, near-parallel streaks running along x, stacked along y -- a genuine ripple-band read, distinct from `t01_sand_dunes`' broad but still roughly isotropic perlin rolls (which never band either) and from every voronoi-plate sibling (cellular, not banded, at all).
- **`type` was numerically out of spec.** This project's catalog (`describe_node`/`catalog_builder.py`) reports `type` as an ordinal enum index 0-4 ("Add 1".."Mult 3"), but the catalog builder's enum handling only derives min/max from the ORDINAL POSITION of the option names -- it never reads each option's real underlying `value` string. The `.mmg` source's real literal values are non-contiguous: Add 1/2/3 = `1`/`2`/`3`, Mult 2/3 = `-2`/`-3` (the shader's `if (type > 0.0)` branch is additive domain-shift, `else` multiplies the domain by `-type` each octave -- that multiply is where Mult's sharper interference fringes come from). Round 1's literal `4` silently hit the Add branch as an out-of-spec "Add 4", not the "Mult 3" the brief's label implied. Fixed to the real Mult-3 literal, `-3`. This is outside the catalog's 0-4 ordinal range, so `validate_graph` now reports one WARNING ("outside enum index range") on this node -- expected and accepted, confirmed against the node's own shader source as a catalog-enum limitation, not a real problem. `iterations` also dropped 3 -> 2 for cleaner, less busy bands; `frequency` (1.6, pairs with Mult for tighter fringes), `persistence` (0.5), and `offset` (0) are unchanged from round 1.
- **Palette lightened and cooled.** Round 1 read too dark and too saturated warm-brown (mud/soil, not wet sand). New gradient averaged roughly 0.35-0.48 luminance with a narrow, mostly-grey R/G/B spread.

**Round 3 retune** (controller re-screen: ripple structure now correct -- anisotropy, `type`, `iterations`, and the ripple-into-normal relief are all LOCKED and untouched here -- but round 2's palette overcorrected all the way to a flat neutral grey, reading as brushed metal or stone rather than sand). Palette-only fix: `WetSandColor`'s gradient shifted warm again -- a muted warm khaki/tan (clearly more red+green than blue) -- while keeping round 2's mid-tone luminance (still averaging roughly 0.35-0.4, not round 1's dark ~0.2). New gradient: `(0.34,0.29,0.21) -> (0.44,0.38,0.28) -> (0.53,0.46,0.35)`, landing between the two prior attempts -- warmer/more saturated than round 2's grey, lighter and less saturated than round 1's dark chocolate-brown. Nothing else in the graph changed for round 3.

Roughness is fed as a flat texture (`WetSandRoughness`, a constant-gradient colorize) rather than left as a Material-node scalar only -- the same lesson `_dry_earth_plates` and `p01_glossy_plastic` (`cookbook_plastics.py`) already established -- so an ORM map exports for the wet-sheen preview instead of silently having none. `RippleNormal`'s `param4=0` is the project's standing flat-normal fix (the wavelet field feeds it directly, the same analytic-generator trap every from-scratch/donor recipe has to correct for). Roughness (0.15, low, for a wet sheen), the flat-texture ORM trick, and the ripple-into-normal wiring are all unchanged since round 1.

Not rendered by me as part of this build pass -- the controller renders for the visual verdict. If the round-3 render still reads too grey or too brown, `Sand color` (`WetSandColor.gradient`) is the exposed lever to retune further; the ripple structure itself (scale/type/iterations) is locked and should not move.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`, the exact `p01_glossy_plastic` (`cookbook_plastics.py`) template for a from-scratch, no-donor material: `RippleField` (the retyped `wavelet_noise`) feeds all three downstream nodes (`WetSandColor`, `RippleNormal`, `WetSandRoughness`), so it has to live in one of the two groups; folding it into the color group avoids a degenerate single-node "finish" group.

- **Ripple Color** -- `RippleField`, `WetSandColor`. Exposed: `Sand color` (`WetSandColor.gradient`), `Ripple scale` (`RippleField.scale_x` only -- nudging it up narrows the anisotropy since `scale_y` stays fixed at 24; nudging it toward 24 would erase the banding).
- **Wet Sand Finish** -- `RippleNormal`, `WetSandRoughness`. Exposed: `Roughness` (`WetSandRoughness.gradient`), `Ripple relief` (`RippleNormal.param1`).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | ripple_color | graph |
| (top level) | wet_sand_finish | graph |
| ripple_color | RippleField | wavelet_noise |
| ripple_color | WetSandColor | colorize |
| wet_sand_finish | RippleNormal | normal_map |
| wet_sand_finish | WetSandRoughness | colorize |
<!-- nodes:end -->
