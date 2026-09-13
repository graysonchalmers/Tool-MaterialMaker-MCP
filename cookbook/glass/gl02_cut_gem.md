# gl02_cut_gem - Faceted cut gem

_Category: glass. Open the graph: `cookbook/glass/gl02_cut_gem.ptex`._

A hard-edged faceted crystal / cut-gem surface: many small, sharp triangular
facets, each a slightly different shade of one coherent emerald-green family,
with crisp facet-boundary relief and a glossy, low-roughness finish. The
first cookbook use of `voronoi_triangle` (triangular cells square `voronoi`
cannot produce) -- proves the base for a faceted/gem look the noise gallery
calls out specifically for this node.

## Recipe

Clones the same `dry_earth` donor `gl01_frosted_glass` uses (a voronoi-cell
network with a border/edge signal available off the generator) rather than
building from scratch, since the donor's cell topology already matches
"cells separated by boundary lines" -- only the cell SHAPE needed to change.
Unlike `gl01`, this recipe keeps almost none of the REST of that donor: see
"v1 -> v2" below.

**Retype, not rebuild.** `voronoi_0` is retyped in place from square
`voronoi` to `voronoi_triangle` at the noise gallery's starting params
(`quality/noise_gallery.py`) for `stretch_x`/`stretch_y` (1) and
`randomness` (0.85), but at `scale_x`/`scale_y`=10, well above the gallery's
starting 4, for many small, sharp facets rather than a few large ones (see
"v1 -> v2" below for why). This is connection-safe: `describe_node`
(cross-checked against the node's own `.mmg` `shader_model.outputs`) shows
both node types share the same first three output ports --

| Port | voronoi | voronoi_triangle |
|---|---|---|
| 0 | Nodes (f, distance to cell centers) | Nodes (f, distance to cell centers) |
| 1 | Borders (f, distance to borders) | Border (f, distance to borders) |
| 2 | Random color (rgb, flat per-cell random) | Random color (rgb, flat per-cell random) |

`voronoi_triangle` adds two extra ports this recipe doesn't use (3: a UV
map meant for a Custom UV companion node, 4: a precomputed analytic normal
map baked from the same SDF). The donor's only existing connection off
`voronoi_0` (port 1 -> the edge-distance colorize) keeps its exact role
after the retype, since port 1 means the same thing on both node types.

**The whole graph, top to bottom.** Four nodes plus `Material`:
`FacetCells` (the retyped voronoi) feeds `FacetTint` (per-facet color,
straight to albedo) off port 2, and feeds `EdgeRamp` (the edge/border
signal) off port 1, which feeds `FacetNormal` (`normal_map`) directly --
no intermediate warp, blend, or second colorize. `RoughnessConst` is a flat
low-roughness texture wired into `Material`'s roughness port so an ORM map
exports. That is genuinely the entire graph: facets -> per-facet tint
(albedo) -> sharp facet edges into the normal, plus a flat roughness
texture. `Material.metallic=0` (non-metal gem).

**Per-facet tint.** `FacetTint`'s gradient is one coherent emerald family
(deep shadowed green at the low end, a bright emerald highlight at the high
end) driven by `FacetCells` port 2 (Random color) -- the same "per-cell
random -> colorize gradient" idiom already proven in `cookbook_stone.py`
(`s04`, `s09`) and `cookbook_scifi.py`'s circuit-chip mask -- so every
triangular facet gets its own flat shade of the same gem color, feeding
`Material`'s albedo directly with nothing layered on top.

**Sharp edges into the normal, nothing else.** `EdgeRamp` (the donor's
`colorize_1`) is left at the untouched `dry_earth` DEFAULT gradient (thin
dark line at pos 0-0.0636, white beyond) -- a per-cell-normalized threshold,
so it stays a thin proportional edge line at any voronoi scale, this
recipe's scale=10 included. Its output feeds `FacetNormal` directly.
`FacetNormal` keeps the `param4=0` flat-normal fix (`docs/AUTHORING.md`)
with `param1` (relief strength) at 0.6 for pronounced, hard-angled facet
relief.

**Glossy.** `Material.roughness`=0.08 and `RoughnessConst`'s flat texture
are both low, for an actually shiny gem surface. Same ORM gap as
`gl01`/`dry_earth` (the donor leaves the roughness input unconnected, so a
scalar-only roughness exports no ORM map): fixed the same way. Roughness's
carrier input comes off `FacetCells` port 0 (an arbitrary choice -- the
gradient is a flat constant either way, so the input value never actually
matters) rather than keeping a noise node alive just to feed it.

## v1 -> v2: what got cut and why

v1 cloned gl01's ENTIRE donor tangle unchanged and just retuned parameters
on top of it: `warp_0`'s organic jointing, two `perlin` noise sources
feeding a crack-composite blend and a second relief-composite blend, plus
an extra contrast colorize and ramp colorize in the normal chain. A
self-screen render of that v1 came back reading as a matte, grainy,
greenish HEX-TILE floor -- not a glossy cut gem, and uncomfortably close to
`s05_hex_stone_tile`. Root cause: that whole donor chain IS gl01's
sandblasted-frost machinery (a high-iteration ambient perlin mixed into the
height signal, on top of an organically-warped edge mask) -- exactly the
wrong shape for a gem, whose facet faces need to be CLEAN and FLAT, not
speckled with fine noise, and whose edges need to be crisp, not
warp-softened into wide bevels. v2 drops that entire chain (`warp_0`,
both `perlin` nodes, the crack-composite blend, the extra contrast/ramp
colorizes, the second relief blend) down to the four-node graph described
above, and raises the voronoi scale from 4 to 10 so more, smaller facets
are visible (the v1 hex-tile read was partly just too few, too-large
cells at scale 4).

## Subgraph structure

Two named subgraphs, the same convention every cookbook recipe follows
(`docs/AUTHORING.md`, "Grouping into subgraphs") even at this small a node
count (see `p01_glossy_plastic` in `cookbook_plastics.py` for the same call
at a similar size):

- **Facet Color** -- the (retyped) facet-cell generator and its per-facet
  tint. Exposed: `Facet size` (voronoi scale), `Facet color` (the tint
  gradient).
- **Facet Finish** -- the edge-ramp/normal-map chain plus the flat-roughness
  constant. Exposed: `Roughness`, `Surface relief` (the normal map's
  strength).

`FacetCells` is the sole generator feeding both groups (color via port 2,
and both the edge signal and the roughness carrier via ports 1/0), so --
same reasoning as `p01_glossy_plastic` -- it's folded into `Facet Color`
rather than left top-level as a single-purpose shared node would be;
`Facet Finish` receives its two inputs as plain boundary ports.

## Honest limitation

Material Maker's `material` node has no true refraction, dispersion, or
internal light-transport model, so this recipe cannot simulate how light
actually bends and splits inside a cut gem. It approximates the LOOK (hard
faceted planes, per-facet color variation, a glossy low-roughness finish)
as an opaque, physically-shaded surface -- the right call for how a
tileable texture like this gets used (a gem-cut panel, a crystal prop
surface), not a claim that it renders real gem optics.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`)
for the rubric, the noise vocabulary (including the `voronoi_triangle`
entry), the "Grouping into subgraphs" lever, and the `param4=0` flat-normal
fix. `gl01_frosted_glass` for the sibling recipe this one deliberately reads
differently from (frosted/matte/crack-network vs faceted/glossy/triangular).
`s05_hex_stone_tile` for the look this recipe's v1 accidentally drifted
toward and v2 corrects away from.

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | facet_color | graph |
| (top level) | facet_finish | graph |
| facet_color | FacetCells | voronoi_triangle |
| facet_color | FacetTint | colorize |
| facet_finish | EdgeRamp | colorize |
| facet_finish | FacetNormal | normal_map |
| facet_finish | RoughnessConst | colorize |
<!-- nodes:end -->
