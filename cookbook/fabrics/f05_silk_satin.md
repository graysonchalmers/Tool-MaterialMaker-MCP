# f05_silk_satin - Silk / satin

_Category: fabrics. Open the graph: `cookbook/fabrics/f05_silk_satin.ptex`._

A glossy, smooth woven fabric where the differentiator from a coarser fabric
like denim or canvas is not visible thread texture but low roughness and
saturated, low-contrast jewel-tone color.

## Recipe

Retype the generator to `diagonal_weave` at a FINE scale (around 48, versus
denim's around 20) so the weave is nearly invisible. The read comes from LOW
roughness (glossy) plus a saturated, low-contrast jewel-tone albedo, not from
visible thread structure. Keep normal strength very low (around 0.08), just
enough faint sheen-line variation to read as woven rather than flat plastic.
First-pass hit.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Same `crocodile_skin` donor shape as `f03_canvas_burlap` (no `blend` node,
no mask wiring to trace). Opening the graph shows 2 top-level groups
(plus `Material` and the untouched metallic `uniform_0`) instead of the
raw 6-node graph:

- **Weave Pattern** — `voronoi_0` (retyped to `diagonal_weave`) and
  `colorize_1` (albedo). `voronoi_0` also feeds **Surface Finish**'s
  normal and roughness colorizes directly, the expected shared-upstream-
  node shape. Exposed: `Weave scale`, `Satin color`.
- **Surface Finish** — `colorize_0` (normal source), `colorize_3`
  (roughness/gloss), `normal_map_0`. Exposed: `Sheen`, `Relief strength`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
