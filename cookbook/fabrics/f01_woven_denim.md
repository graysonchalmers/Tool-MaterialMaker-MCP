# f01_woven_denim - Woven denim

_Category: fabrics. Open the graph: `cookbook/fabrics/f01_woven_denim.ptex`._

Prompt: "blue denim fabric". A Phase-3 hero material (frozen 15-case test
set), folded into the cookbook 2026-09-05 so it carries the same gates, card,
and subgraph grouping as every other material.

## Recipe

No bundled example uses Material Maker's weave nodes, so this GRAFTS one in:
clone `crocodile_skin` and retype its `voronoi_0` generator to
`diagonal_weave` (size 22), so the same generator -> colorize -> normal_map
chain that made scales now makes twill. `colorize_1` recolors the threads to
a narrow indigo range, `colorize_3` sets a high matte roughness, `uniform_0`
stays black so the cloth is non-metallic.

This was the material that surfaced the project-wide flat-normal blocker:
`normal_map` is a compound (input -> buffer -> switch(param4) -> edge_detect)
and its default `param4=1` runs edge_detect on a pre-rendered buffer that
comes back flat for a directly-fed analytic generator. `param4=0` routes the
raw weave into edge_detect and the twill appears in the normal map. Every
later analytic-generator material reuses that fix.

## Subgraph structure

Opening the graph shows 4 top-level nodes instead of 7:

- **Twill Weave** (`voronoi_0` as `diagonal_weave`, `colorize_1`,
  `colorize_3`). Exposed: `Weave size`, `Thread color`, `Cloth roughness`.
- **Weave Relief** (`colorize_0`, `normal_map_0`). Exposed: `Relief strength`.

`uniform_0` (the metallic constant) stays top-level, the same convention the
other crocodile_skin-derived materials follow for a single donor-default
constant feeding one port.

## See also

`guide://authoring` (or `docs/AUTHORING.md`) for the `param4=0` fix and the
weave family notes; `docs/evidence/phase3/2026-08-26-iter1.md` for the frozen
verdict.
