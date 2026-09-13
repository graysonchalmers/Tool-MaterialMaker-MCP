# sf07_conduit_panel - Conduit panel

_Category: scifi. Open the graph: `cookbook/scifi/sf07_conduit_panel.ptex`._

An interlocking pipe/conduit panel: curved copper pipes weaving across a dark gunmetal panel, standing proud of the surface as raised tubes. This is the first cookbook material to use the `truchet` node, a topology voronoi and perlin cannot make.

## Recipe

`truchet` with `shape=1` (Circle) tiles quarter-circle arcs that always meet edge to edge, so the field it outputs reads as one continuous network of curving pipe paths rather than a scattered or gridded pattern. `size=4` sets the tile density; kept modest so the pipe runs are chunky enough to be legible as tubes rather than a fine weave. The Line alternative (`shape=0`) was considered for a maze/circuit look but rejected: sf03 already owns that flat etched-trace territory, and the brief calls for pipes with real 3D relief, which the Circle shape's continuous curves suit better than Line's right-angle segments.

**Fixed 2026-09-13**: a controller render of the first version of this recipe showed a flat tan surface with a few specks -- the truchet pattern was invisible. Root cause, measured by rendering the truchet node in isolation and sampling the output: `truchet` (shape=1, Circle) outputs a SMOOTH distance field ranging approximately 0.50-0.95 (mean ~0.82), not a 0/1 binary and not centered at 0.5. It reads like interlocking curved tubes: dark (~0.5) along the tube seams/centers, bright (~0.95) on the tube bodies, with smooth gradients between. The original recipe thresholded albedo at 0.46-0.52 and relief at 0.48-0.52 -- both bands sit entirely below the field's real 0.5-0.95 floor, so they caught almost nothing.

The corrected recipe uses the measured range directly. A single truchet field drives both albedo and relief, so this recipe needs no `blend` at all: `colorize_albedo` thresholds it into dark recessed panel color (below 0.68-0.72, the seam side of the field) and bright metal pipe color (above, the tube-body side), with the transition band moved to 0.68-0.72 -- the midpoint of the real 0.5-0.95 range, not the midpoint of 0-1.

Relief is the bigger change: `normal_map` now reads the RAW, unthresholded truchet field directly (`param4=0`, the flat-normal fix, since the field is directly-fed and analytic) with `param1=0.9` for pronounced relief. There is no separate mask node feeding `normal_map` any more -- the smooth 0.5-0.95 distance field already has the shape of rounded interlocking tubes, so feeding it raw gives naturally rounded raised pipes for free, rather than a hard-edged bump from a binary mask. Roughness comes straight off the truchet field too (a continuous ramp is fine for a roughness gradient): panel matte, pipe polished. Metallic is a single flat scalar (0.6) on the Material node rather than a routed texture, since both panel and pipe are metal here (no paint-vs-metal split to make, unlike the painted-metal cookbook set).

## Difference from sf03_circuit_board

sf03 is flat etched PCB traces: a `pattern` Square wave gives right-angle stripes with no tile-based curve topology, and its relief is limited to the shared flat-normal fix (no raised geometry, traces read as printed, not extruded). sf07 is the opposite silhouette: `truchet`'s Circle tiles give continuously curving pipe paths, and the relief is deliberately pronounced (`param1=0.9` vs sf03's `0.15`) so the pipes read as physically raised tubes above the panel, not a flat printed pattern.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`:

- **Conduit Pattern** - `ConduitLayout` (truchet), `ConduitColor`. Exposed: `Conduit density` (`ConduitLayout`'s `size`), `Conduit color` (`ConduitColor`'s gradient).
- **Surface Finish** - `PanelRoughness`, `ConduitNormal`. Exposed: `Surface sheen`, `Relief strength`.

`ConduitLayout` feeds `ConduitColor`, `PanelRoughness`, and `ConduitNormal` directly (the single-upstream-node-feeds-multiple-groups case already used in sf01/sf03/sf04), which produces extra boundary output ports on it once Conduit Pattern and Surface Finish are split into separate groups; that is expected, not a wiring bug. There is no longer a dedicated relief-mask node: `ConduitNormal` takes `ConduitLayout`'s raw field the same way `PanelRoughness` does.

## Concerns / not rendered

This fix was authored and validated (0 validator errors, Material albedo/roughness/normal ports all wired) but NOT re-rendered -- this task's flow is author + validate + promote only, the render happens in a later controller pass. The 0.68-0.72 albedo threshold and `param1=0.9` relief strength are reasoned from the measured 0.5-0.95 truchet range (this time render-informed, unlike the original guess), but the exact pipe-vs-panel area ratio and relief intensity are still not eyeballed against a real render. If a render shows the panel reading as too thin a sliver (truchet's mean ~0.82 means most of the field sits above 0.72, so pipe dominates by design) or the relief too soft/too extreme, retune the 0.68-0.72 band or `param1` first.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for the rubric, the authoring workflow, the noise vocabulary, and the `param4=0` flat-normal fix.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | conduit_pattern | graph |
| (top level) | surface_finish | graph |
| conduit_pattern | ConduitLayout | truchet |
| conduit_pattern | ConduitColor | colorize |
| surface_finish | PanelRoughness | colorize |
| surface_finish | ConduitNormal | normal_map |
<!-- nodes:end -->
