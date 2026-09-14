# sf05_circuit_maze_panel - Circuit maze panel

_Category: scifi. Open the graph: `cookbook/scifi/sf05_circuit_maze_panel.ptex`._

A steel panel with bold diagonal maze/chevron lines milled into it: a bright, moderately metallic trace network cut across a darker, less metallic panel, with real beveled relief rather than a flat printed pattern. This is the first cookbook material to use `truchet`'s Line mode (`shape=0`); the only other cookbook `truchet` recipe, sf07_conduit_panel, uses Circle mode (`shape=1`).

## Recipe

`truchet` with `shape=0` (Line) draws pairs of diagonal lines per tile that always connect edge to edge, producing one continuous maze network across the panel, the same tile-based topology voronoi and perlin cannot make that sf07's Circle mode already exploits, but with straight chevron segments instead of rounded arcs. `size=4` matches sf07's tile density.

**Measured before choosing any threshold**, per this project's standing rule that an unknown node's real output range must be diagnosed before tuning against it: an isolated render of the noise-gallery `truchet_line` case (`quality/noise_gallery.py`'s `build_crossfamily_row`, the same `{"shape":0,"size":4}` starting node), sampled pixel-by-pixel with `quality/pngread.py` over the full 512x512 albedo (4,194,304 pixels), gave a range of **0.498-1.000** (not 0/1 binary, and not the same range as Circle mode's measured 0.50-0.95). The key difference from Circle mode is shape, not just endpoints: a 25-bucket histogram put every bucket at 4.49-5.47% of pixels, i.e. the field is close to **uniformly distributed** across its whole span, mean and median both landing near 0.75. Circle mode's field, by contrast, is concentrated near its top (mean ~0.82, per sf07's fix). Line mode behaves like a smooth, roughly linear per-tile ramp, not a rounded distance field with a flat interior.

Because the field is close to uniform, its own mean/median and the midpoint of its range are all close together, so `colorize_albedo` thresholds at **0.73-0.77** (centered on 0.75) with no ambiguity about which "midpoint" to use. That threshold gives a roughly 50/50 area split between panel and line, which reads as bold thick maze walls rather than thin circuit traces; a future thinner-trace variant would push the band down toward the field's low end instead.

`normal_map` takes the RAW, unthresholded truchet field directly (`param4=0`, the flat-normal fix, field is directly-fed and analytic), the same choice sf07 made for the same reason: a hard 0/1 mask on a smooth field throws away real shape information. The visible effect differs from sf07's rounded tube bumps, though, because Line mode's field is a linear per-tile ramp rather than a distance field with a flat interior: feeding it raw produces beveled, faceted diagonal ridges, each maze tile reading as a sloped raised facet meeting its neighbors at ridge lines where the per-tile ramp resets. `param1=0.55` gives moderate-bold relief (between sf03's 0.15 flat-fix-only and sf07's 0.9 pronounced tube). The bright line channel sits at the field's high end, the same "dark below the band / bright above it" polarity as albedo, so raised and bright stay together rather than inverting one but not the other.

Roughness (`colorize_rgh`) is a continuous ramp with no threshold, 0.55 (panel, matte) down to 0.25 (line, glossier), the same convention sf07 uses since roughness has no visible edge to protect. Because the gradient's control points sit at field positions 0.0 and 1.0 but the field itself never goes below 0.498, the roughness actually achieved at the panel end is closer to 0.40 than 0.55, a side effect of the same continuous-ramp-over-full-domain approach sf07 already uses, not a bug: the ramp is still monotonic and visually distinct.

New for this material: a per-pixel **metallic** texture, which no prior scifi recipe routes (sf01-sf04 and sf07 all use a single flat `Material.metallic` scalar). Checked `material.mmg`'s input port order against the pinned Material Maker checkout (`z-Git/material-maker/addons/material_maker/nodes/material.mmg`): port0 `albedo_tex`, port1 `metallic_tex`, port2 `roughness_tex`, port3 `emission_tex`, port4 `normal_tex`. `colorize_metallic` reads the same truchet field, hard-thresholded at the SAME 0.73-0.77 band as albedo (so the metal-look edge lines up exactly with the color edge), into `Material` port 1: panel 0.10 (a painted or anodized steel panel, mostly non-metallic), line 0.50 (a moderate, not fully metallic, exposed trace). Verified via the exported ORM's blue channel rather than by eye, per the project's standing rule: sampled 25-127, matching the intended 0.10-0.50 split almost exactly (0.10 x 255 = 25.5, 0.50 x 255 = 127.5).

## Difference from sf03_circuit_board and sf07_conduit_panel

sf03 is flat etched PCB traces: a `pattern` Square wave gives right-angle stripes with no tile-based curve topology, and its relief is limited to the shared flat-normal fix (no raised geometry, traces read as printed, not extruded). sf07 is `truchet` Circle mode: continuously curving pipe paths with pronounced (`param1=0.9`) rounded relief, reading as physically raised tubes. sf05 sits between the two: it shares sf07's `truchet` node and real relief, but Line mode's straight chevron segments and near-uniform linear field give beveled, faceted ridges rather than rounded tubes, at a more moderate relief strength (`param1=0.55`). sf05 is also the only one of the three with a routed per-pixel metallic texture; sf03 and sf07 both use a flat `Material.metallic` scalar.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`:

- **Maze Pattern** - `MazeLayout` (truchet), `MazeColor`. Exposed: `Maze density` (`MazeLayout`'s `size`), `Line color` (`MazeColor`'s gradient).
- **Surface Finish** - `PanelRoughness`, `LineMetallic`, `MazeNormal`. Exposed: `Surface sheen` (`PanelRoughness`'s gradient), `Relief strength` (`MazeNormal`'s `param1`). `LineMetallic`'s gradient is intentionally not exposed, kept internal the same way sf03's mask colorizes are never exposed.

`MazeLayout` feeds four downstream nodes directly (`MazeColor`, `PanelRoughness`, `LineMetallic`, `MazeNormal`), one more than sf07's three because of the new metallic routing: the single-upstream-node-feeds-multiple-groups case already used in sf01/sf03/sf04/sf07, producing extra boundary output ports on `MazeLayout` once Maze Pattern and Surface Finish are split into separate groups. That is expected, not a wiring bug.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for the rubric, the authoring workflow, the noise vocabulary, and the `param4=0` flat-normal fix.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | maze_pattern | graph |
| (top level) | surface_finish | graph |
| maze_pattern | MazeLayout | truchet |
| maze_pattern | MazeColor | colorize |
| surface_finish | PanelRoughness | colorize |
| surface_finish | LineMetallic | colorize |
| surface_finish | MazeNormal | normal_map |
<!-- nodes:end -->
