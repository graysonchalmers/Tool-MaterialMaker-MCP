# pm03_chipped_paint - Paint chipped to bare metal

_Category: painted-metal. Open the graph: `cookbook/painted-metal/pm03_chipped_paint.ptex`._

Flat green paint over bare steel, chipped through to exposed metal in scattered worn spots. Distinct from the frozen `combo01_rusted_painted_steel` on purpose: that recipe chips paint to rust, this one chips to bare metal, so the two should never be read as duplicates.

## Recipe

Clones `rusted_metal` for its ready-made two-layer metal base, recolors that base to bare steel, then composites a flat green paint coat over it through one hard chip mask (perlin thresholded at roughly less than 0.30 for the minority worn spots). The green paint is wired as the majority coverage, with the chip mask driving bare metal only in the sparse worn spots. The same hard mask also drives metallic (Material port 1: metal chips = 1, paint = 0) and a chip-edge normal step so the paint sits physically proud of the chips.

Pitfall specific to this material: getting the mask wiring right took two passes. The first attempt was inverted, with metal as the majority and green paint only in the pits, which read as corroded metal rather than chipped paint. A second pass over-corrected to nearly all-metal before the wiring that puts paint as the dominant layer and metal only in the masked minority spots was pinned down. Metallic being masked per-pixel rather than a single global value is what makes the exposed chips read as real bright steel rather than dull painted metal.

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
This is the material the project's blend/mask caution is specifically
about: it carries **three** `blend` nodes, and each one's port0/port1/
port2 sources were traced from the serialized connections before any
grouping was decided. Opening the graph shows 5 top-level nodes (four
groups plus `Material`) instead of the raw 18-node graph:

- **Bare Metal Base** — `perlin_0`, `perlin_1`, `perlin_2`, `colorize_0`
  through `colorize_4`, and both of the donor `rusted_metal`'s own
  two-tone metal-layer blends, `blend_0` (port0 ← `colorize_2` steel
  base, port1 ← `colorize_1` darker steel, port2 mask ← `colorize_3`)
  and `blend_1` (port0 ← `colorize_4`, port1 ← `colorize_0`, constant
  amount, no mask connection). Every one of both blends' inputs is
  inside this one group, so only their single output edges (feeding
  `Paint/Metal Composite`'s `blend_alb`/`blend_rgh`) cross the boundary.
  Exposed: `Bare metal color`, `Metal shadow tone`.
- **Chip Mask** — `perlin_chip`, `mask_chip`, the hard 0/1 threshold that
  decides where paint chips away to bare metal. Exposed: `Chip pattern
  scale`.
- **Paint Layer** — `paint_alb`, `paint_rgh`, the flat green paint
  colors. Exposed: `Paint color`, `Paint sheen`.
- **Paint/Metal Composite** — `blend_alb`, `blend_rgh`, `normal_chip`,
  the actual paint-over-metal composite. Both `blend_alb` and
  `blend_rgh` take all three of their inputs from OUTSIDE this group
  (bare metal from `Bare Metal Base`, paint from `Paint Layer`, mask
  from `Chip Mask`) — `group_into_subgraph` preserves each incoming
  connection's own target port independently, so this cannot swap which
  external source lands on port0 vs port1 vs port2. Neither `mask_chip`'s
  gradient nor its threshold band is exposed anywhere as a friendly
  parameter, so no end-user knob can touch the hard mask the chip-vs-paint
  split depends on. Exposed: `Chip edge relief`.

Verified after building: `renders_match` against this material's own
pre-retrofit baseline came back at an exact `grid_mean_abs_diff` of `0.0`
on all three exported maps (albedo, normal, orm), not merely under the
`3.0` tolerance.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
