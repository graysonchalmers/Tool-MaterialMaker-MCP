# Normal/albedo source-mismatch audit

Static (no-render) check: does a material's normal-map relief come
from the same pattern-generator source(s) as its albedo, so the
bump lines up with the color grain? Flagged = both sides have a
pattern-generator source and the two sets are disjoint.

**8/71 flagged**

| Flagged | Material | Albedo sources | Normal sources |
|---|---|---|---|
| YES | painted-metal/pm01_powder_coat | orange_peel_pattern/MixNoise, orange_peel_pattern/OrangePeelCells | orange_peel_pattern/OrangePeelNoise, orange_peel_pattern/WarpNoise |
| YES | painted-metal/pm02_automotive_enamel | flake_pattern/FlakeCells | flake_pattern/FlakeNormalCells, flake_pattern/WarpNoise |
| YES | painted-metal/pm04_hammertone | hammer_dimple_pattern/HammerDimples, hammer_dimple_pattern/MixNoise | hammer_dimple_pattern/DimpleNormalCells, hammer_dimple_pattern/WarpNoise |
| YES | stone/s02_gray_granite | fleck_color/FleckCells | stone_relief/ReliefCells, stone_relief/ReliefWarpNoise |
| YES | stone/s04_scattered_river_stones | mask_pattern/PebbleCells, material_finish/SurfaceNoise | relief/ReliefCells, relief/ReliefWarpNoise |
| YES | stone/s06_river_pebbles | pebble_pattern/PebbleCells, surface_grain/GrainNoise | relief/ReliefCells, relief/ReliefWarpNoise |
| YES | terrain/t02_fresh_snow | material_finish/DriftNoise, snow_color/SnowSparkle | relief/DriftShape, relief/ReliefWarpNoise |
| YES | terrain/t03_gravel | pebble_pattern/GravelCells | relief/ReliefCells, relief/ReliefWarpNoise |
|  | painted-metal/combo01_rusted_painted_steel | paint_coat/PeelNoise, rust_layer/MetalToneNoise, rust_layer/RustPatchNoise | (none) |
|  | fabrics/f01_woven_denim | twill_weave/TwillLayout | twill_weave/TwillLayout |
|  | fabrics/f03_canvas_burlap | weave_pattern/WeaveLayout | weave_pattern/WeaveLayout |
|  | fabrics/f04_wool_knit | knit_pattern/WeaveLayout | knit_pattern/WeaveLayout |
|  | fabrics/f05_silk_satin | weave_pattern/SatinWeaveLayout | weave_pattern/SatinWeaveLayout |
|  | fabrics/f06_velvet | fiber_pattern/FiberNoise | fiber_pattern/FiberNoise |
|  | fabrics/f07_herringbone_tweed | herringbone_pattern/HerringboneLayout | herringbone_pattern/HerringboneLayout |
|  | fabrics/f08_donegal_tweed | base_weave/WeaveLayout, fleck_pattern/FleckSource | base_weave/WeaveLayout |
|  | fabrics/f09_plaid_flannel | plaid_pattern/PlaidGrid | plaid_pattern/PlaidGrid |
|  | fabrics/f10_boucle_upholstery | loop_pattern/BoucleLoop | loop_pattern/BoucleLoop |
|  | fabrics/f11_corduroy | corduroy_rib/RibNoise | corduroy_rib/RibNoise |
|  | glass/gl01_frosted_glass | AmbientNoise, CrackWarpNoise, base_color/FacetCells | AmbientNoise, CrackWarpNoise, base_color/FacetCells |
|  | glass/gl02_cut_gem | facet_color/FacetCells | facet_color/FacetCells |
|  | glass/gl03_shattered_crystal | AmbientNoise, CrackWarpNoise, base_color/ShardField | AmbientNoise, CrackWarpNoise, base_color/ShardField |
|  | glass/gl04_raw_crystal_cluster | crystal_pattern/CrystalCells | crystal_pattern/CrystalCells |
|  | leather/l01_black_oiled_leather | grain_pattern/PoreCells | grain_pattern/PoreCells |
|  | leather/l02_distressed_two_tone | grain_pattern/PoreCells, wear_pattern/RubNoise | grain_pattern/PoreCells |
|  | leather/l03_suede | grain_pattern/NapGrainNoise | grain_pattern/NapGrainNoise |
|  | leather/l04_reptile_exotic | grain_pattern/PoreCells | grain_pattern/PoreCells |
|  | leather/l05_quilted_leather | leather_grain/PoreCells, quilt_pattern/QuiltLayout | leather_grain/PoreCells, quilt_pattern/QuiltLayout |
|  | leather/l06_topstitched_leather | leather_grain/PoreCells, stitch_pattern/StitchDashes | leather_grain/PoreCells, stitch_pattern/StitchDashes |
|  | leather/l07_pebbled_leather | grain_pattern/PoreCells | grain_pattern/PoreCells |
|  | metal/m01_weathered_copper | copper_color/MetalNoise, patina_pattern/PatchNoise | (none) |
|  | metal/m02_brushed_aluminum | brushed_finish/StreakNoise | brushed_finish/StreakNoise |
|  | metal/m03_brushed_titanium | brushed_finish/HairlineNoise | brushed_finish/HairlineNoise |
|  | metal/m04_scratched_steel | scratch_finish/ScratchNoise | scratch_finish/ScratchNoise |
|  | ceramic/man02_ceramic_hex_tiles | tile_pattern/HexLayout | tile_pattern/HexLayout |
|  | ceramic/man03_mosaic_tile | mosaic_pattern/MosaicTiles | mosaic_pattern/MosaicTiles |
|  | organics/o01_mossy_forest_floor | LitterNoise, MossCoverageNoise, ground_color/PlateCells | LitterNoise, MossCoverageNoise, ground_color/PlateCells |
|  | organics/o03_tree_bark | bark_grain/BarkRidges, bark_grain/GrainNoiseCoarse, bark_grain/GrainNoiseFine, bark_grain/GrainWobble | bark_grain/BarkRidges, bark_grain/GrainNoiseCoarse, bark_grain/GrainNoiseFine, bark_grain/GrainWobble |
|  | organics/o04_snake_scales | surface_pattern/ScaleLayout | surface_pattern/ScaleLayout |
|  | organics/o05_coral | surface_pattern/PolypCells | surface_pattern/PolypCells |
|  | organics/o06_lichen_crusted_rock | lichen_mask/LichenCoverageNoise, surface_color/StoneNoise | lichen_mask/LichenCoverageNoise |
|  | plastics/p01_glossy_plastic | surface_color/SurfaceNoise | surface_color/SurfaceNoise |
|  | painted-metal/pm03_chipped_paint | bare_metal_base/SteelMaskNoise, bare_metal_base/SteelToneNoise, chip_mask/ChipNoise | chip_mask/ChipNoise |
|  | painted-metal/pm05_scuffed_panel | scuff_pattern/ScuffNoise | scuff_pattern/ScuffNoise |
|  | painted-metal/pm06_splatter_finish | splatter_pattern/SplatterPattern | splatter_pattern/SplatterPattern |
|  | stone/s05_hex_stone_tile | hex_pattern/HexLayout, surface_grain/GrainNoise | hex_pattern/HexLayout |
|  | stone/s07_cobblestone | stone_and_relief/PlateCells, stone_and_relief/ReliefNoiseCoarse, surface_grain/GrainNoise | stone_and_relief/PlateCells, stone_and_relief/ReliefNoiseCoarse, stone_and_relief/ReliefNoiseFine |
|  | stone/s08_dry_stone_wall | stone_and_relief/PlateCells, stone_and_relief/ReliefNoiseCoarse, surface_grain/GrainNoise | stone_and_relief/PlateCells, stone_and_relief/ReliefNoiseCoarse, stone_and_relief/ReliefNoiseFine |
|  | stone/s09_ashlar_wall | block_finish/SurfaceNoise, block_layout/BlockLayout, block_layout/BlockWarpNoise | block_finish/SurfaceNoise, block_layout/BlockLayout, block_layout/BlockWarpNoise |
|  | stone/s10_flagstone | relief/ReliefNoiseCoarse, stone_color/PlateCells, surface_grain/GrainNoise | relief/ReliefNoiseCoarse, relief/ReliefNoiseFine, stone_color/PlateCells |
|  | stone/s11_marble | marble_relief/ReliefNoiseCoarse, marble_veins/BaseNoise, marble_veins/PlateCells | marble_relief/ReliefNoiseCoarse, marble_veins/BaseNoise, marble_veins/PlateCells |
|  | stone/s12_eroded_sandstone | sediment_layers/SedimentNoise, surface_grit/GritNoise | sediment_layers/SedimentNoise |
|  | stone/s13_polished_marble | marble_veins/MarbleVeins | marble_veins/MarbleVeins |
|  | scifi/sf01_hull_plating | panel_pattern/PlateCrossMask, panel_pattern/PlateGridWave | panel_pattern/PlateCrossMask, panel_pattern/PlateGridWave |
|  | scifi/sf02_hazard_stripe_panel | stripe_pattern/StripeWave | stripe_pattern/StripeWave |
|  | scifi/sf03_circuit_board | chip_blocks/ChipLayout, circuit_traces/BoardNoise, circuit_traces/TraceWave | circuit_traces/BoardNoise, circuit_traces/TraceWave |
|  | scifi/sf04_vent_grille_panel | hole_pattern/HoleLayout | hole_pattern/HoleLayout |
|  | scifi/sf05_circuit_maze_panel | maze_pattern/MazeLayout | maze_pattern/MazeLayout |
|  | scifi/sf07_conduit_panel | conduit_pattern/ConduitLayout | conduit_pattern/ConduitLayout |
|  | terrain/t01_sand_dunes | dune_ripples/DuneRipples, dune_ripples/GrainNoiseCoarse, dune_ripples/GrainNoiseFine, dune_ripples/RingPattern | dune_ripples/DuneRipples, dune_ripples/GrainNoiseCoarse, dune_ripples/GrainNoiseFine, dune_ripples/RingPattern |
|  | terrain/t04_grass_field | grass_coverage/BladeNoise, soil_grass_color/SoilNoise | grass_coverage/BladeNoise |
|  | terrain/t05_cracked_ice | plate_pattern/IcePlates, surface_finish/ReliefNoiseCoarse | plate_pattern/IcePlates, surface_finish/ReliefNoiseCoarse |
|  | terrain/t06_cooled_lava | basalt_crust/CrustPlates, surface_relief/ReliefNoiseCoarse | basalt_crust/CrustPlates, surface_relief/ReliefNoiseCoarse, surface_relief/ReliefNoiseFine |
|  | terrain/t07_forest_floor | litter_pattern/LitterCells | litter_pattern/LitterCells |
|  | terrain/t08_riverbed_pebbles | plate_pattern/PebbleCells, surface_finish/ReliefNoiseCoarse | plate_pattern/PebbleCells, surface_finish/ReliefNoiseCoarse, surface_finish/ReliefNoiseFine |
|  | terrain/t09_rippled_wet_sand | ripple_color/RippleField | ripple_color/RippleField |
|  | terrain/t10_packed_dirt | dirt_pattern/DirtNoise | dirt_pattern/DirtNoise |
|  | wood/w03_painted_wood_siding | board_structure/GrainNoise, board_structure/PlankLayout, paint_overlay/WearNoise | board_structure/GrainNoise, board_structure/PlankLayout |
|  | wood/w04_driftwood_gray | wood_grain/GrainNoiseCoarse, wood_grain/GrainNoiseFine, wood_grain/GrainWobble, wood_grain/RingPattern | wood_grain/GrainNoiseCoarse, wood_grain/GrainNoiseFine, wood_grain/GrainWobble, wood_grain/RingPattern |
|  | wood/w05_dark_walnut | wood_grain/GrainNoiseCoarse, wood_grain/GrainNoiseFine, wood_grain/GrainWobble, wood_grain/RingPattern | wood_grain/GrainNoiseCoarse, wood_grain/GrainNoiseFine, wood_grain/GrainWobble, wood_grain/RingPattern |
|  | wood/w06_burled_wood | wood_grain/GrainNoiseCoarse, wood_grain/GrainNoiseFine, wood_grain/GrainWobble, wood_grain/SwirlField | wood_grain/GrainNoiseCoarse, wood_grain/GrainNoiseFine, wood_grain/GrainWobble, wood_grain/SwirlField |
