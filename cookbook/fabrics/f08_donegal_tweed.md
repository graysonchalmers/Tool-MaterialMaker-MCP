# f08_donegal_tweed - Donegal-style flecked tweed

_Category: fabrics. Open the graph: `cookbook/fabrics/f08_donegal_tweed.ptex`._

A heather gray-brown woven wool base with sparse cream and rust flecks
scattered across it, the classic Donegal tweed look. Where
`f07_herringbone_tweed` differentiates through weave geometry (the
chevron), this one differentiates through color instead.

## Recipe

A plain `weave2` base (`stitch=1`, no herringbone chevron) recolored to a
warm heather gray-brown. Layered on top: a second, independent `voronoi`
node (`voronoi_fleck`) purely for the fleck source, not the base
generator, since retyping the base to `weave2` loses its own per-cell
random output, and the flecks want a much finer, unrelated cell frequency
than the weave grid anyway. The fleck mask is a hard-threshold `colorize`
of that voronoi's port 2 (`rand3`, per-cell random): only the top ~20% of
cell values pass, so flecks read as scattered nubs rather than a wash.
Fleck color is a second `colorize` of the same port 2 output, spread
across cream and rust so different fleck cells land different hues, the
multi-color fleck mix real Donegal tweed is known for.

Composited with `blend` (`blend_type=0` set explicitly, matching the rest
of the cookbook's convention): base weave on the majority port 1, flecks
on the minority port 0, the sparse mask on port 2, since a `blend` shows
port 1 where its mask is 0 and port 0 where it's 1.

## Honest limitation

Relief comes entirely from the weave's own structure; the fleck layer is
color-only, with no extra bump where a fleck sits. Real tweed flecks are a
different fiber, so they'd carry a faint texture difference too. Not
attempted here, a deliberate scope cut for a color-differentiated variant
of an already-solved weave.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
This is the material the fleck/blend caution for this category is
specifically about: it carries one `blend` node, and its port0/port1/
port2 sources were traced from the serialized connections before any
grouping was decided. Opening the graph shows 4 top-level groups (plus
`Material` and the untouched metallic `uniform_0`) instead of the raw
11-node graph:

- **Base Weave** — `voronoi_0` (retyped to `weave2`, `stitch=1`) and
  `colorize_1` (the base weave's albedo). `voronoi_0` also feeds
  **Surface Finish**'s normal and roughness colorizes directly, the
  same shared-upstream-node shape as the rest of this category's
  materials. Exposed: `Weave scale`, `Tweed color`.
- **Fleck Pattern** — `voronoi_fleck` (the SEPARATE voronoi node used
  purely for the fleck source, deliberately kept out of `Base Weave` so
  the "how sparse are the flecks" knob stays independently tunable
  rather than disappearing into the same group as the weave it sits
  over), `colorize_fleck_mask` (the hard 0/1 threshold), and
  `colorize_fleck_color` (the cream/rust fleck color ramp). Exposed:
  `Fleck density` (`voronoi_fleck.scale_x`), `Fleck color`
  (`colorize_fleck_color.gradient`). The mask's own threshold band is
  NOT exposed, matching this project's standing rule for hard 0/1 masks.
- **Fleck Composite** — `blend_fleck` alone, in its own group rather than
  folded into either side, since all three of its inputs are external:
  port0 (minority, shows where the mask is 1) ← `colorize_fleck_color`
  from `Fleck Pattern`, port1 (majority, shows where the mask is 0) ←
  `colorize_1` from `Base Weave`, port2 (mask) ← `colorize_fleck_mask`
  from `Fleck Pattern`. `group_into_subgraph` preserves each incoming
  connection's own target port independently when rehoming it, so
  grouping cannot swap which source lands on which port — confirmed by
  reading back the collapsed subgraph's own internal connections after
  building, not assumed from this description alone. Exposed: `Fleck
  strength` (`blend_fleck.amount`).
- **Surface Finish** — `colorize_0` (normal source), `colorize_3`
  (roughness), `normal_map_0`. Exposed: `Roughness`, `Relief strength`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
