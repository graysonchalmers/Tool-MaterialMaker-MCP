# gl02_cut_gem - Faceted cut gem

_Category: glass. Open the graph: `cookbook/glass/gl02_cut_gem.ptex`._

A hard-edged faceted crystal / cut-gem surface: sharp triangular facets, each
a slightly different shade of one coherent emerald-green family, separated by
crisp dark facet-boundary lines, low roughness for a glassy/gem finish. The
first cookbook use of `voronoi_triangle` (triangular cells square `voronoi`
cannot produce) -- proves the base for a faceted/gem look the noise gallery
calls out specifically for this node.

## Recipe

Clones the same `dry_earth` donor `gl01_frosted_glass` uses (topology match:
a voronoi-cell network with an edge/crack ramp, warp, and blend into an
albedo, plus a parallel relief chain into a normal map) rather than building
from scratch, since the donor's plate/crack topology already matches
"cells separated by boundary lines" -- only the cell SHAPE needed to change.

**Retype, not rebuild.** `voronoi_0` is retyped in place from square `voronoi`
to `voronoi_triangle` at the exact starting params from the noise gallery
(`quality/noise_gallery.py`): `scale_x`/`scale_y`=4, `stretch_x`/`stretch_y`=1,
`randomness`=0.85. This is connection-safe: `describe_node` (cross-checked
against the node's own `.mmg` `shader_model.outputs`) shows both node types
share the same first three output ports --

| Port | voronoi | voronoi_triangle |
|---|---|---|
| 0 | Nodes (f, distance to cell centers) | Nodes (f, distance to cell centers) |
| 1 | Borders (f, distance to borders) | Border (f, distance to borders) |
| 2 | Random color (rgb, flat per-cell random) | Random color (rgb, flat per-cell random) |

`voronoi_triangle` adds two extra ports this recipe doesn't use (3: a UV
map meant for a Custom UV companion node, 4: a precomputed analytic normal
map baked from the same SDF). The donor's only existing connection off
`voronoi_0` (port 1 -> the crack/edge ramp) keeps its exact role after the
retype, since port 1 means the same thing on both node types.

**Per-facet tint (the actual point of this material).** `gl01` fed its
`BaseTone` colorize from the shared ambient perlin noise for a uniform
frosted tone. `gl02` rewires that colorize (`FacetTint`) to take
`FacetCells`' port 2 (Random color) instead -- the same "per-cell random ->
colorize gradient" idiom already proven in `cookbook_stone.py` (`s04`, `s09`)
and `cookbook_scifi.py`'s circuit-chip mask. `FacetTint`'s gradient is one
coherent emerald family (deep shadowed green at the low end, a bright emerald
highlight at the high end), so every triangular facet gets its own flat
shade of the SAME gem color rather than a uniform tone -- this is what makes
individual facets read as distinct planes.

**Crisp edges, not smeared ones.** `EdgeWarp` (the donor's `warp_0`) is
pushed to near zero (`amount`=0.02, vs `gl01`'s already-low 0.05) so the
naturally hard triangular boundaries stay sharp geometric facets instead of
being organically warped into round blobs or a connected-crack plate look --
the exact failure mode the variety lens for this task calls out.
`EdgeRamp` (the donor's `colorize_1`, the crack/edge mask) is left at the
untouched `dry_earth` DEFAULT gradient (thin dark line 0-0.0636, white
beyond): that default was tuned for `scale_x=scale_y=4`, which is exactly
the scale this recipe uses (unlike `gl01`, which had to retune the threshold
because it cranked scale to 60 for fine sandblasted facets). `FacetComposite`
(the donor's `blend_0`, Multiply) sits at `amount`=0.6, a bit stronger than
`gl01`'s 0.5, for crisper facet-edge contrast.

**Glassy, not matte.** `Material.roughness`=0.1 (vs `gl01`'s matte 0.88).
Same ORM gap as `gl01`/`dry_earth` (the donor leaves the roughness input
unconnected, so a scalar-only roughness exports no ORM map): fixed the same
way, a flat `RoughnessConst` texture (0.1 uniform) wired into `Material`'s
roughness port.

**Hard crystalline relief.** `FacetNormal` (the donor's `normal_map_0`) keeps
the `param4=0` flat-normal fix (see `docs/AUTHORING.md`) but pushes
`param1` (relief strength) to 0.65, far above `gl01`'s subtle 0.15 -- the
facet-edge signal driving the normal should read as pronounced, hard-angled
relief, not a near-flat surface.

Forced non-metal (`Material.metallic=0`, `colorize_3`'s connection to
Material dropped) -- same precedent as `gl01` and `dry_earth`'s own
metallic-variance wiring.

## Subgraph structure

Grouped with the exact same member sets as `gl01` (only the exposed-param
labels differ, since the roles changed):

- **Base Color** -- the (retyped) facet-cell generator, its edge ramp, warp,
  and the per-facet-tint/edge composite. Exposed: `Facet size` (voronoi
  scale), `Facet color` (the per-facet tint gradient), `Edge contrast` (the
  composite blend amount).
- **Surface Detail** -- the height/normal chain plus the flat-roughness
  constant. Exposed: `Roughness`, `Surface relief` (the normal map's
  strength).

The two `perlin` noise sources stay outside both groups (same reasoning as
`gl01`): each is shared across boundaries, so folding either in would just
relabel the sharing as an extra boundary port.

## Honest limitation

Material Maker's `material` node has no true refraction, dispersion, or
internal light-transport model, so this recipe cannot simulate how light
actually bends and splits inside a cut gem. It approximates the LOOK (hard
faceted planes, per-facet color/brightness variation, glassy low-roughness
finish) as an opaque, physically-shaded surface -- the right call for how a
tileable texture like this gets used (a gem-cut panel, a crystal prop
surface), not a claim that it renders real gem optics.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`)
for the rubric, the noise vocabulary (including the `voronoi_triangle`
entry), the "Grouping into subgraphs" lever, and the `param4=0` flat-normal
fix. `gl01_frosted_glass` for the sibling recipe this one deliberately reads
differently from (frosted/matte/crack-network vs faceted/glossy/triangular).

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | EdgeWarpNoise | perlin |
| (top level) | AmbientNoise | perlin |
| (top level) | base_color | graph |
| (top level) | surface_detail | graph |
| base_color | FacetCells | voronoi_triangle |
| base_color | EdgeRamp | colorize |
| base_color | FacetTint | colorize |
| base_color | ColorizeUnused | colorize |
| base_color | FacetComposite | blend |
| base_color | EdgeWarp | warp |
| surface_detail | ReliefComposite | blend |
| surface_detail | FacetNormal | normal_map |
| surface_detail | ReliefContrast | colorize |
| surface_detail | ReliefRamp | colorize |
| surface_detail | RoughnessConst | colorize |
<!-- nodes:end -->
