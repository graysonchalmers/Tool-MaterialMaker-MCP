# s12_eroded_sandstone - Water-eroded sandstone

_Category: stone. Open the graph: `cookbook/stone/s12_eroded_sandstone.ptex`._

Sandstone with horizontal sediment strata smeared into diagonal erosion runs, as if water had run down the face and dragged the layers with it. Built from scratch, no donor, since nothing else in the cookbook has this topology.

**Fixed after a controller render read this as polished wood grain, not sandstone.** The first pass's fine, continuous banding plus a saturated warm-brown palette plus a glossy-leaning roughness band, once smeared by `directional_warp`, looked exactly like wood grain. Fixed with four changes (below): a matte roughness band, a subtle gritty albedo multiply, a paler/cooler/desaturated palette, and chunkier, more irregular strata. This must not be mistakable for wood; the cookbook already has a wood category (w01-w05).

## Recipe

**Why `directional_warp`, not `slope_blur`.** The phase plan originally named `slope_blur` for this recipe. `slope_blur.mmg` is a compound graph built entirely from two `buffer` nodes sandwiching an `edge_detect` shader (`buffer -> edge_detect_3_3_2 -> buffer_2`, no unbuffered bypass), and `buffer` nodes compile a compute shader at load time, which this project's headless `--export-material` pipeline cannot drive (proven in `quality/debug_swatches.py`'s `build_swatch_slope_blur`: a valid graph that renders all black). `directional_warp` has no such trap: it is a plain per-pixel UV offset by a constant `angle`/`strength`, verified with `describe_node` and pixel-checked in `build_swatch_directional_warp`. Its displacement is exactly the "smear a layered field along a constant direction" effect real water erosion needs, so it is a better fit here, not just a workaround. The technique is kept as-is through this fix; only what it smears and how the result is finished changed.

**Banded sediment base, made chunkier and more irregular.** `SedimentNoise` is a `perlin` with `scale_x=4` (low, few large features) and `scale_y=9` (moderate -- lowered from the first pass's 16 so layers are broader and fewer), 3 iterations and `persistence=0.62` (up from 0.55) for more irregular, varied-thickness band steps with occasional sharp breaks, instead of the fine, even, nearly-continuous banding a higher-frequency/higher-iteration field gives. Fine continuous banding is what read as wood grain once smeared; chunkier, irregular banding does not. `SedimentBands` colorizes it through a 6-stop palette of pale buff, pale tan, and light warm grey, with two thin, desaturated rust-accent bands rather than a dominant saturated brown, and an overall lower saturation and higher value than the first pass's warm-brown palette (or a wood palette), so the base reads as dry pale rock before any warp is applied.

**Directional erosion.** `ErosionWarp` (`directional_warp`) reads `SedimentBands`' RGBA output directly on its `in#` port, the same "RGBA colorize feeds a warp node's input port directly" pattern `dry_earth`'s own `warp_0` uses. `anglemap`/`strengthmap` are left unconnected so the node falls back to its own constant defaults, giving a clean, repeatable displacement from `angle`/`strength` alone. `angle=-58` (a steep diagonal) and `strength=0.62` (upper-middle of the -1..1 range, unchanged from the first pass) smear the now-chunky bands into diagonal streaks: the strata read as eroded, not erased.

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
