# sf02_hazard_stripe_panel - Hazard stripe panel

_Category: scifi. Open the graph: `cookbook/scifi/sf02_hazard_stripe_panel.ptex`._

A diagonal yellow and black hazard stripe panel, built fresh rather than from a donor since none of the bundled examples have diagonal stripes.

## Recipe

Built from scratch using the `pattern` node (independent x/y wave generators, Sine/Triangle/Square/Sawtooth/Constant/Bounce, combined via a mix mode): `x_wave` set to Square gives alternating bars, `y_wave` set to Constant keeps the bars running along Y before rotation. The wiring order matters: `pattern` (its `f` output) feeds a `colorize` node that converts to rgba with a hard yellow/black threshold, and only then feeds a `transform` node that rotates 45 degrees. Feeding `transform` directly from `pattern`'s `f` output is a port-type mismatch, since `transform`'s input is `rgba`; this wiring order matches `metal_pattern_2`'s own order, which was the tell that led to the fix.

Pitfall: none beyond the port-type ordering above, this recipe hit target on the intended structure.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 3 top-level nodes (two groups plus `Material`)
instead of the raw 6-node graph:

- **Stripe Pattern** — `pattern_0`, `colorize_0`, `transform_0`. `pattern_0`
  also feeds `colorize_rgh` in Surface Finish directly (one upstream node
  feeding multiple downstream groups, producing an expected extra boundary
  output port). Exposed: `Stripe count` (`pattern_0`'s `x_scale`), `Stripe
  colors` (`colorize_0`'s gradient), `Stripe angle` (`transform_0`'s
  `rotate`).
- **Surface Finish** — `colorize_rgh`, `normal_map_0`. Exposed: `Surface
  sheen`, `Relief strength`.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
