# o06_lichen_crusted_rock - Lichen-crusted rock

_Category: organics. Open the graph: `cookbook/organics/o06_lichen_crusted_rock.ptex`._

Gray stone with a patchy green-gray lichen crust, using a two-layer masked
blend to composite the crust over the base stone.

## Recipe

Clone `rusted_metal`'s two-layer masked-blend structure (the same lever the
weathered-copper reference material already proved) but recolor to
stone-plus-lichen instead of metal-plus-patina: base (`colorize_2`) to gray
stone, patch (`colorize_1`) to lichen green-gray, widen the mask
(`colorize_3` threshold) for more coverage.

Pitfall specific to this material: `rusted_metal` wires the Material node's
metallic input straight off the mask (`colorize_3`), which is correct for a
metal donor but wrong once recolored to stone. `drop_conn` that connection
and force the Material's own `metallic` scalar to 0. Also graft a light
`normal_map` fed from the mask (`rusted_metal` ships with no normal chain at
all) so lichen patches read as faintly raised rather than a pure flat-color
swap, a nice-to-have the donor's own verified reference cases don't bother
with.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 4 top-level nodes (three groups plus `Material`)
instead of the raw 11-node tangle (the 10-node `rusted_metal` donor plus the
grafted `normal_map_lichen`):

- **Surface Color** — `perlin_1` (the shared noise source for both layers),
  `colorize_2` (base), `colorize_1` (patch), and `blend_0` (the two-layer
  composite feeding albedo). Exposed: `Stone color` and `Lichen color`.
- **Lichen Coverage** — `perlin_2` and `colorize_3` (the widened mask
  threshold). `colorize_3`'s output is a true three-way shared signal — it
  feeds `Surface Color`'s `blend_0` mask port, `Surface Finish`'s roughness
  variant, AND `Surface Finish`'s `normal_map_lichen` relief input — so
  rather than folding it into any one of those three consumers (which would
  just relabel two of the three as boundary ports instead of one), it gets
  its own small group, since its gradient is a real, explicitly-widened
  knob rather than an untouched donor default. Exposed: `Coverage`.
- **Surface Finish** — `perlin_0`, `colorize_0` and `colorize_4` (both
  untouched `rusted_metal` defaults, riding along as internal-only members),
  `blend_1` (the roughness composite), and `normal_map_lichen` (the grafted
  relief chain from the pitfall above). Exposed: `Relief strength` (the
  `normal_map_lichen` strength).

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
