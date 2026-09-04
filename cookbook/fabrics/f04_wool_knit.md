# f04_wool_knit - Wool / chunky knit

_Category: fabrics. Open the graph: `cookbook/fabrics/f04_wool_knit.ptex`._

An honest coarse-weave stand-in for chunky knitwear, not a true knit. This
graph does not produce real stockinette knit loops: the catalog has no
generator capable of that, and the search was formally closed. Read the
structural read as a blocky chunky-weave textile, and describe it that way
in any user-facing copy, not as "knit."

## Recipe

`weave2`'s own `stitch` parameter looked promising for loop softness but only
renders a crisp herringbone/basket diagonal: structurally the same hard-
crossing weave as plain `weave`. The workable stand-in that shipped here:
`weave` at a COARSE scale with a near-max `width` (few, wide, almost-touching
ribs), which reads as chunky blocky yarn rows rather than fine thread,
closer to a basket or chunky-weave textile than true knit loops.

Closed for good on 2026-09-03: an isolation-render probe tested the four most
plausible knit leads and confirmed none produce stockinette (upright V's in
aligned wales is the real knit tell, not merely offset rows). `pattern`
Bounce and `bricks` Running Bond both make a staggered pillow honeycomb;
`weave2` stitch=1 is a basket weave; `weave2` stitch=3 is the only one with
chevrons, but they reverse band-to-band, i.e. herringbone tweed (shipped
separately as `f07_herringbone_tweed`), not knit. Do not re-open this search
without a new generator in the catalog.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Same `crocodile_skin` donor shape as `f03_canvas_burlap` (no `blend` node,
no mask wiring to trace). Opening the graph shows 2 top-level groups
(plus `Material` and the untouched metallic `uniform_0`) instead of the
raw 6-node graph:

- **Knit Pattern** — `voronoi_0` (retyped to `weave`) and `colorize_1`
  (albedo). `voronoi_0` also feeds **Surface Finish**'s normal and
  roughness colorizes directly, the expected shared-upstream-node shape.
  Exposed: `Rib count`, `Wool color`.
- **Surface Finish** — `colorize_0` (normal source), `colorize_3`
  (roughness), `normal_map_0`. Exposed: `Roughness`, `Relief strength`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm). That `0.0` proves this
retrofit's own subgraph-grouping step changed nothing further — the
builder's rendered output before grouping and after grouping is pixel-
identical. It does **not** prove the tracked `.ptex` on `main` was
unchanged by this branch: it was not.

Disclosure: unlike every other material in this retrofit, this one's
committed `.ptex` changed by more than reorganization. Before this
retrofit, the tracked graph's generator was still a `pattern` node, a
stale leftover from the "Bounce" approach that the "Closed for good on
2026-09-03" note above explicitly rejected as unworkable; the builder
and this card had already moved on to the `weave`-based recipe described
under "Recipe," but the tracked artifact and its thumbnail had never
been re-promoted to match. Building this material fresh from the current
(`weave`-based) builder as part of this task's render-and-repromote step
incidentally rebuilt the tracked `.ptex` from the correct source, which
changed the generator node type `pattern` → `weave`,
`normal_map_0.param1` 0.5 → 0.3, and a colorize gradient's endpoints, as
a side effect of retrofitting subgraph structure — not as an intentional
fix undertaken by this task. The corrected thumbnail was independently
verified to match the `weave` version (6-column/7-row periodicity via
autocorrelation). No further action is needed on the artifact itself.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
