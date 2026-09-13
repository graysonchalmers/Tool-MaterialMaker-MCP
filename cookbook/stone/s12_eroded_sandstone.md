# s12_eroded_sandstone - Water-eroded sandstone

_Category: stone. Open the graph: `cookbook/stone/s12_eroded_sandstone.ptex`._

Sandstone with horizontal sediment strata smeared into diagonal erosion runs, as if water had run down the face and dragged the layers with it. Built from scratch, no donor, since nothing else in the cookbook has this topology.

**Round 1 fix: a controller render read this as polished wood grain, not sandstone.** The first pass's fine, continuous banding plus a saturated warm-brown palette plus a glossy-leaning roughness band, once smeared by `directional_warp`, looked exactly like wood grain. Fixed with four changes: a matte roughness band, a subtle gritty albedo multiply, a paler/cooler/desaturated palette, and chunkier, more irregular strata (`scale_y` dropped 16 -> 9). This must not be mistakable for wood; the cookbook already has a wood category (w01-w05).

**Round 2 fix: pulling the banding down washed the strata into a soft mottle, reading as travertine/limestone rather than layered eroded sandstone.** Restored visible layering while keeping everything from round 1 (pale/matte palette, grit, the `directional_warp` erosion smear): `SedimentNoise.scale_y` raised back up 9 -> 14 (more, thinner, clearly separated strata, `scale_x` kept low at 4 for stretched horizontal bands), `SedimentBands`' gradient rebuilt as five flat color plateaus joined by hard (~0.02-wide) transitions instead of a smooth ramp, and `ErosionWarp.strength` trimmed 0.62 -> 0.5 so the now-thinner, higher-contrast layers get smeared into legible erosion runs rather than dissolved back into a mottle.

## Recipe

**Why `directional_warp`, not `slope_blur`.** The phase plan originally named `slope_blur` for this recipe. `slope_blur.mmg` is a compound graph built entirely from two `buffer` nodes sandwiching an `edge_detect` shader (`buffer -> edge_detect_3_3_2 -> buffer_2`, no unbuffered bypass), and `buffer` nodes compile a compute shader at load time, which this project's headless `--export-material` pipeline cannot drive (proven in `quality/debug_swatches.py`'s `build_swatch_slope_blur`: a valid graph that renders all black). `directional_warp` has no such trap: it is a plain per-pixel UV offset by a constant `angle`/`strength`, verified with `describe_node` and pixel-checked in `build_swatch_directional_warp`. Its displacement is exactly the "smear a layered field along a constant direction" effect real water erosion needs, so it is a better fit here, not just a workaround. The technique is kept as-is through this fix; only what it smears and how the result is finished changed.

**Banded sediment base -- restored to distinct, legible strata (round 2).** `SedimentNoise` is a `perlin` with `scale_x=4` (low, few large horizontal features, unchanged and kept low so bands stay stretched horizontally) and `scale_y=14` (high again -- more, thinner, clearly separated bands, raised back up from round 1's 9, which had softened the strata into a mottle), 3 iterations and `persistence=0.62`. `SedimentBands` now colorizes it through a 10-stop gradient built as five flat color plateaus (pale buff / pale tan / muted rust / light warm grey / pale sandy highlight) joined by hard (~0.02-wide) transitions, rather than a smoothly interpolated ramp -- so individual sediment layers show up as distinct banded color steps, not a soft blur between neighbors. Saturation/value stay in round 1's pale, cool, dry range (not the original saturated warm-brown palette, and not a wood palette).

**Directional erosion.** `ErosionWarp` (`directional_warp`) reads `SedimentBands`' RGBA output directly on its `in#` port, the same "RGBA colorize feeds a warp node's input port directly" pattern `dry_earth`'s own `warp_0` uses. `anglemap`/`strengthmap` are left unconnected so the node falls back to its own constant defaults, giving a clean, repeatable displacement from `angle`/`strength` alone. `angle=-58` (a steep diagonal, unchanged) and `strength=0.5` (trimmed down from round 1's 0.62, so the now-thinner, higher-contrast layers are smeared into legible erosion runs rather than dissolved back into a mottle) smear the bands into diagonal streaks: the strata read as eroded, not erased.

**Matte roughness -- the biggest single fix.** `SandstoneRoughness` is now a narrow MATTE band, 0.80-0.88, raised substantially from the first pass's 0.52-0.70 (which leaned glossy and varied enough to read as a wood-like sheen). Sandstone is dry and matte, not glossy; this alone kills much of the wood read. `ErosionWarp`'s output still feeds both `ReliefHeight` (a plain 0->1 ramp, unchanged) and `SandstoneRoughness`, the same "warp's RGBA output straight into an f-typed `colorize` input" pattern `dry_earth` uses for `warp_0 -> colorize_4`, so both the bump map and the roughness variation carry the erosion streaks. `SandstoneNormal` keeps `param4=0` (the project's standing flat-normal fix) with a moderate `param1=0.3`: gentle relief, this is a worn stone face, not chunky cobbles. Non-metal: `Material.metallic` is set to 0 as a plain scalar, since port 1 is left unconnected, the same convention `_from_scratch_noise_material` and `s11_marble`'s roughness use when no texture is wired to a port.

**Surface grit.** `GritNoise` is a new fine perlin (`scale_x=42`, `scale_y=42`, 5 iterations), the same fine-grain idiom `s05`/`s06`/`s07`/`s08`/`s10` already use elsewhere in this file for per-stone surface grain. `GritContrast` colorizes it to a narrow, subtle multiply band (0.88-1.0), and `AlbedoGrit` (`blend`, `blend_type=2` Multiply, `amount=1`, port 2 mask left unconnected so the opacity defaults to a uniform 1.0, no threshold/speckle risk) multiplies it over `ErosionWarp`'s eroded albedo before `Material` port 0. Continuous smooth grain reads as wood; a fine gritty micro-texture reads as stone -- this and the matte roughness are the two biggest levers against the wood misread.

## How this differs from the rest of the stone category

Every other stone recipe differentiates through a spatial cell pattern (voronoi plates/cracks for s07/s08/s10/s11, a hex grid for s05, Bricks courses for s09) or per-cell/per-fleck random color (s02, s04, s06). This one has no cells at all: its structure is a directional smear of horizontal layers, the one distortion technique (`directional_warp`) nothing else in the cookbook uses, so it does not collapse into another rocky-blob variant.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. Built from scratch (no donor), so all three groups are new, not carried over from a cloned graph:

- **Sediment Layers** -- `SedimentNoise`, `SedimentBands`. Exposed: `Layer frequency` (`SedimentNoise.scale_y`), `Sediment color` (`SedimentBands.gradient`).
- **Erosion & Relief** -- `ErosionWarp`, `ReliefHeight`, `SandstoneNormal`, `SandstoneRoughness`. Exposed: `Erosion angle` (`ErosionWarp.angle`), `Erosion strength` (`ErosionWarp.strength`), `Relief strength` (`SandstoneNormal.param1`), `Roughness` (`SandstoneRoughness.gradient`).
- **Surface Grit** (new in this fix) -- `GritNoise`, `GritContrast`, `AlbedoGrit`. Exposed: `Grit scale` (`GritNoise.scale_x`).

Every group needed at least one member beyond a single node to avoid a degenerate one-node subgraph, so `ErosionWarp` (the warp itself) was folded into the same group as the relief and roughness chains it feeds, and `AlbedoGrit` (the multiply blend) into the same group as the grit noise and its contrast ramp, rather than standing alone.

## Concerns / not rendered

This fix was authored and validated (0 validator errors, Material albedo/normal/roughness all wired) but not rendered as part of this task; the controller renders it for the next visual verdict. The new roughness band, palette, strata frequency/persistence, and grit contrast were picked as defensible values reasoned from the wood misread and the established grain idiom elsewhere in this file, not verified against a real render in this pass. `GritNoise`'s `scale_x`/`scale_y=42` trip the validator's cosmetic "outside default slider range [1, 32]" warning (2 warnings, 0 errors) -- the same warning `s05_hex_stone_tile`'s `GrainNoise` (scale 48) already carries in the promoted cookbook, so it is an accepted, not-shader-clamped pattern here, not a new risk.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for the rubric, the authoring workflow, the noise vocabulary, and the `param4=0` flat-normal fix.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | sediment_layers | graph |
| (top level) | erosion_relief | graph |
| (top level) | surface_grit | graph |
| sediment_layers | SedimentNoise | perlin |
| sediment_layers | SedimentBands | colorize |
| erosion_relief | ErosionWarp | directional_warp |
| erosion_relief | ReliefHeight | colorize |
| erosion_relief | SandstoneNormal | normal_map |
| erosion_relief | SandstoneRoughness | colorize |
| surface_grit | GritNoise | perlin |
| surface_grit | GritContrast | colorize |
| surface_grit | AlbedoGrit | blend |
<!-- nodes:end -->
