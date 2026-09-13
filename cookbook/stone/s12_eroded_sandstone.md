# s12_eroded_sandstone - Water-eroded sandstone

_Category: stone. Open the graph: `cookbook/stone/s12_eroded_sandstone.ptex`._

Sandstone with horizontal sediment strata smeared into diagonal erosion runs, as if water had run down the face and dragged the layers with it. Built from scratch, no donor, since nothing else in the cookbook has this topology.

## Recipe

**Why `directional_warp`, not `slope_blur`.** The phase plan originally named `slope_blur` for this recipe. `slope_blur.mmg` is a compound graph built entirely from two `buffer` nodes sandwiching an `edge_detect` shader (`buffer -> edge_detect_3_3_2 -> buffer_2`, no unbuffered bypass), and `buffer` nodes compile a compute shader at load time, which this project's headless `--export-material` pipeline cannot drive (proven in `quality/debug_swatches.py`'s `build_swatch_slope_blur`: a valid graph that renders all black). `directional_warp` has no such trap: it is a plain per-pixel UV offset by a constant `angle`/`strength`, verified with `describe_node` and pixel-checked in `build_swatch_directional_warp`. Its displacement is exactly the "smear a layered field along a constant direction" effect real water erosion needs, so it is a better fit here, not just a workaround.

**Banded sediment base.** `SedimentNoise` is a `perlin` with `scale_x=3` (low, few large features) and `scale_y=16` (high, many stacked features), so the raw field reads as horizontal sediment strata rather than a blobby cloud. `SedimentBands` colorizes it through a 6-stop warm sandstone gradient (tan, pale ochre, rust-brown, alternating) so each stratum carries a distinct tonal band instead of one dyed noise field.

**Directional erosion.** `ErosionWarp` (`directional_warp`) reads `SedimentBands`' RGBA output directly on its `in#` port, the same "RGBA colorize feeds a warp node's input port directly" pattern `dry_earth`'s own `warp_0` uses. `anglemap`/`strengthmap` are left unconnected so the node falls back to its own constant defaults, giving a clean, repeatable displacement from `angle`/`strength` alone. `angle=-58` (a steep diagonal) and `strength=0.62` (upper-middle of the -1..1 range) smear the horizontal bands into diagonal streaks: the strata read as eroded, not erased.

**Relief and roughness both read the eroded field, not the pre-warp one.** `ErosionWarp`'s output feeds both `ReliefHeight` (a plain 0->1 ramp) and `SandstoneRoughness` (a narrow matte-to-slightly-rough band, 0.52-0.70), the same "warp's RGBA output straight into an f-typed `colorize` input" pattern `dry_earth` uses for `warp_0 -> colorize_4`. So the bump map and the roughness variation both carry the erosion streaks, not only the albedo. `SandstoneNormal` keeps `param4=0` (the project's standing flat-normal fix) with a moderate `param1=0.3`: gentle relief, this is a worn stone face, not chunky cobbles. Non-metal: `Material.metallic` is set to 0 as a plain scalar, since port 1 is left unconnected, the same convention `_from_scratch_noise_material` and `s11_marble`'s roughness use when no texture is wired to a port.

## How this differs from the rest of the stone category

Every other stone recipe differentiates through a spatial cell pattern (voronoi plates/cracks for s07/s08/s10/s11, a hex grid for s05, Bricks courses for s09) or per-cell/per-fleck random color (s02, s04, s06). This one has no cells at all: its structure is a directional smear of horizontal layers, the one distortion technique (`directional_warp`) nothing else in the cookbook uses, so it does not collapse into another rocky-blob variant.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`. Built from scratch (no donor), so both groups are new, not carried over from a cloned graph:

- **Sediment Layers** -- `SedimentNoise`, `SedimentBands`. Exposed: `Layer frequency` (`SedimentNoise.scale_y`), `Sediment color` (`SedimentBands.gradient`).
- **Erosion & Relief** -- `ErosionWarp`, `ReliefHeight`, `SandstoneNormal`, `SandstoneRoughness`. Exposed: `Erosion angle` (`ErosionWarp.angle`), `Erosion strength` (`ErosionWarp.strength`), `Relief strength` (`SandstoneNormal.param1`), `Roughness` (`SandstoneRoughness.gradient`).

Both groups needed at least one member beyond a single node to avoid a degenerate one-node subgraph, so `ErosionWarp` (the warp itself) was folded into the same group as the relief and roughness chains it feeds, rather than standing alone.

## Concerns / not rendered

This recipe was authored and validated (0 validator errors, Material albedo/normal/roughness all wired) but not rendered as part of this task; the controller renders it for the visual verdict. The erosion angle/strength and the layer frequency were picked as defensible starting values based on the swatch proofs and the `dry_earth` precedent for RGBA-into-f connections, not verified against a real render in this pass.

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
| sediment_layers | SedimentNoise | perlin |
| sediment_layers | SedimentBands | colorize |
| erosion_relief | ErosionWarp | directional_warp |
| erosion_relief | ReliefHeight | colorize |
| erosion_relief | SandstoneNormal | normal_map |
| erosion_relief | SandstoneRoughness | colorize |
<!-- nodes:end -->
