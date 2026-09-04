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

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
