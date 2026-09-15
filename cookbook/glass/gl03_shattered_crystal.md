# gl03_shattered_crystal - Shattered crystal glass

_Category: glass. Open the graph: `cookbook/glass/gl03_shattered_crystal.ptex`._

A jewel-toned slab of glass that has been shattered: sharp, angular fracture
lines cut across smoother panels, glossy and saturated violet-blue, with
hard crystalline relief. The first cookbook use of `shard_fbm` (zero prior
cookbook use), proving the node out for a hard-edged fracture-network look
rather than the soft turbulent cloud it produces at its own defaults.

## Recipe

Clones the same `dry_earth` donor `gl01_frosted_glass`/`gl02_cut_gem` use,
and retypes the base generator (`voronoi_0`) to `shard_fbm`.

**Pushed well past the soft-cloud defaults.** `docs/AUTHORING.md`'s pinned
finding is that `shard_fbm` at its own defaults (`sharp=0.7, folds=0`) reads
as a soft turbulent cloud, not a crystalline shatter. Confirmed in person
with `render_node_output` sweeps that isolate just this node (rewiring its
output straight to `Material`'s albedo, bypassing the rest of the graph),
against three candidate parameter sets:

- `sharp=1.0, folds=4, sx=10, sy=10, iter=5` -- pushed too far: fine
  moire/interference ripples crowd out any clean lines, reads as scanline
  static, not fracture geometry.
- `sharp=0.95, folds=3, sx=7, sy=7, iter=4` -- has sharp crack lines, but
  busy concentric ripple contours crowd the space between them.
- `sharp=0.9, folds=2, sx=7, sy=7, iter=4, per=0.5, off=0` (**shipped**) --
  clean, angular, straight fracture lines cutting across smoother panels.
  The clearest "shattered crystal" read of the three.

Both `sharp` and `folds` land well above the pinned soft-cloud defaults
(`0.7` / `0`), per `docs/AUTHORING.md`'s own instruction not to settle for
the default read.

**Gotcha: the retype breaks a port reference.** `shard_fbm` exposes exactly
one output (port 0, type `f`). `voronoi` exposes four (Nodes, Border,
Random color, plus an rgba composite), and the donor's only outgoing wire
off `voronoi_0` uses **port 1** (voronoi's "Border" output) to feed the
crack-ramp colorize. `retype()` swaps the node's type and parameters but
does not repair connections that reference a port the new type does not
have, so after retyping, that wire pointed at a port that no longer
existed. Fixed with a small inline pass over the graph's connections,
repointing that one `from_port` from `1` to `0` right after the retype.
Confirmed clean with zero validation errors afterward.

**Gotcha: the gl01/gl02 crack-ramp convention doesn't transfer.**
`gl01`/`gl02` build their crack signal with a narrow near-zero threshold
colorize (dark only below roughly 0.06), which works because voronoi's
"Border" output is near-zero only at cell edges and high everywhere else.
`shard_fbm` has no such output -- it is a continuous turbulent field whose
crack-like structure IS its dark/light transitions across the whole 0..1
range (sampling the raw field: min 0.04, 10th percentile 0.27, median 0.50,
max 0.92 -- a broad, roughly bell-shaped distribution, nothing concentrated
near zero). Copying gl01's narrow threshold verbatim crushed almost the
entire field to flat white when rendered in isolation, destroying the
signal. Fixed with a mild S-curve instead of a threshold
(`(0,0)->(0.3,0.15)->(0.7,0.85)->(1,1)`), which keeps the field's own
structure -- an isolated render of the fixed ramp came back visually
near-identical to the raw field, just with slightly more contrast at the
extremes.

**Composite tuning.** `FractureWarp` (the donor's `warp_0`) amount is cut
from `0.4` to `0.08` -- `gl01` leans INTO that same warp to soften its crack
joints into an organic, connected network; here the goal is the opposite,
so the warp is kept just large enough to avoid a perfectly computed,
sterile line without smearing the shard field's hard angles into `gl01`'s
soft look. `CrackComposite` (Multiply blend) amount is `0.5` -- a first pass
at `0.6` combined with a darker base gradient rendered as an almost-black,
unreadable smudge in `render_preview`, because `shard_fbm`'s crack signal
covers the whole surface rather than isolated seams, so the same
multiply-composite idiom `gl01`/`gl02` use darkens far more broadly here.
The fix was both trimming this amount and brightening `BaseTone`'s
gradient (a jewel-tone violet-blue, `0.20/0.12/0.45` up to `0.62/0.48/0.92`)
until the composited surface read as a lit gem again. `ReliefComposite`
amount is cut to `0.25` (from the donor's `0.5`) so the ambient noise mixed
into the height signal doesn't wash out the crack sharpness -- this is a
hard-edged crystal, not a soft-diffused surface, so the height signal stays
dominated by the shard field's own crack contrast. `CrystalNormal` keeps
the `param4=0` flat-normal fix with `param1=0.8` (pushed past `gl02`'s
`0.6`) for hard crystalline relief. `Material.roughness=0.07`, glossy like
`gl02`, not matte like `gl01`. Same ORM gap as `gl01`/`gl02` (the donor
leaves the roughness input unconnected, so a scalar-only roughness exports
no ORM map): fixed the same way, a flat `RoughnessConst` texture wired into
`Material`'s roughness port.

**How this differs from its glass siblings.** `gl01_frosted_glass` is a
CONNECTED SANDBLAST crack network off plain `voronoi` -- fine, dense, soft
and diffuse, matte cool blue-gray. `gl02_cut_gem` is FACETED
`voronoi_triangle` cells -- uniform, flat, hex-ish facets with crisp facet
edges and no crack lines at all. `gl03` is neither: a dense, continuous
fracture field covering the whole surface (not flat panels with occasional
seams), glossy and saturated, reading as a slab of crystal that has
actually been shattered rather than sandblasted or faceted.

## Subgraph structure

Two named subgraphs, the same convention every cookbook recipe follows
(`docs/AUTHORING.md`, "Grouping into subgraphs"):

- **Base Color** -- the shard-field generator, its crack ramp and warp, and
  the crack/base-tone blend that produces the albedo. Exposed:
  `Shard sharpness` (the `shard_fbm` sharp param), `Base color` (the jewel
  gradient), `Crack contrast` (the blend amount between the crack mask and
  the base color).
- **Surface Detail** -- the height/normal chain plus the flat-roughness
  constant. Exposed: `Roughness`, `Surface relief` (the normal map's
  strength).

The two `perlin` noise sources stay outside both groups since each feeds
into more than one group, same reasoning as `gl01_frosted_glass`.

## Honest limitation

Material Maker's `material` node has no true refraction, dispersion, or
internal light-transport model, so this recipe cannot simulate how light
actually bends and splits inside shattered glass or a fractured crystal. It
approximates the LOOK (a dense angular fracture network, a glossy jewel-tone
finish, hard crystalline relief) as an opaque, physically-shaded surface --
the right call for how a tileable texture like this gets used (a broken
window panel, a crystal prop surface, a shattered gem texture), not a claim
that it renders real glass optics.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`)
for the rubric, the noise vocabulary (including the `shard_fbm` entry and
its soft-cloud-at-defaults trap), the "Grouping into subgraphs" lever, and
the `param4=0` flat-normal fix. `gl01_frosted_glass` and `gl02_cut_gem` for
the sibling recipes this one deliberately reads differently from
(soft/diffuse crack network vs faceted/flat cut cells vs dense/continuous
shattered fracture field).

<!-- nodes:begin -->
## Nodes

Generated by `python -m quality.promote_cookbook` from the shipped graph;
do not edit by hand. Open the `.ptex` and look for these names.

| Subgraph | Node | Type |
|---|---|---|
| (top level) | CrackWarpNoise | perlin |
| (top level) | AmbientNoise | perlin |
| (top level) | base_color | graph |
| (top level) | surface_detail | graph |
| base_color | ShardField | shard_fbm |
| base_color | CrackRamp | colorize |
| base_color | BaseTone | colorize |
| base_color | ColorizeUnused | colorize |
| base_color | CrackComposite | blend |
| base_color | FractureWarp | warp |
| surface_detail | ReliefComposite | blend |
| surface_detail | CrystalNormal | normal_map |
| surface_detail | ReliefContrast | colorize |
| surface_detail | ReliefRamp | colorize |
| surface_detail | RoughnessConst | colorize |
<!-- nodes:end -->
