# man02_ceramic_hex_tiles - White ceramic hexagon tiles

_Category: ceramic. Open the graph: `cookbook/ceramic/man02_ceramic_hex_tiles.ptex`._

Prompt: "white ceramic hexagon tiles". A Phase-3 hero material (frozen
15-case test set), folded into the cookbook 2026-09-05 as the founding member
of the ceramic category.

## Recipe

Clone `beehive`, Material Maker's bundled hex field. `beehive_2`'s port 0
peaks at each cell center and falls to a narrow low band at the edges, so
one ramp does both jobs: `colorize_5` maps the low band to a thin dark grout
line and everything above 0.20 to white tile, and `colorize_4` inverts that
for roughness (grout rough, glazed faces near-mirror). The metallic constant
(`uniform_greyscale`) is set to 0. The hex relief from the donor's blend ->
normal_map chain is kept so the grout reads recessed; height (port 6) comes
from the same blend.

The lesson: when a bundled example already has the exact pattern topology
(regular hex cells), the whole material is two gradient ramps and one
constant. Tile density is `sx`/`sy` on the beehive (20 x 12 here).

## Subgraph structure

Opening the graph shows 4 top-level nodes instead of 10:

- **Tile Pattern** (`beehive_2`, `colorize_5`, `colorize_4`). Exposed:
  `Tiles across`, `Tiles down`, `Tile and grout color`, `Glaze roughness`.
- **Tile Relief** (`colorize_2`, `colorize`, `blend`, `normal_map`,
  `colorize_3`). Exposed: `Grout depth`, `Edge softness`.

`uniform_greyscale` (metallic 0) stays top-level as a single donor-default
constant feeding one port.

## See also

`guide://authoring` (or `docs/AUTHORING.md`), the `pattern`/`beehive` notes;
`docs/evidence/phase3/2026-08-26-iter1.md`.
