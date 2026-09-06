# Role-named nodes across the cookbook - design

_2026-09-06. Executes teardown #5's finding 3 (Grayson's pick, "do 2 + 3 in the same session")._

## Why

The North Star's learning claim rests on the human opening the authored `.ptex` and
reading the graph. The one real human edit on record (`saved_graphs/bricks_grayson_edit.ptex`
vs upstream `bricks.ptex`) renamed 21 of 22 nodes to role names (`BrickPattern`,
`MossMask`, `RoughnessMap`, `NonMetallic`) before changing anything else. The cookbook today
ships 452 of its 681 working nodes (66%) with donor auto-names (`colorize_0`, `blend_1`,
`perlin_pm`), mostly inside the subgraphs the 2026-09-04 retrofit created. The subgraph
wrappers are named well; their contents are not. All 53 recipe cards reference those
auto-names in prose.

The 2026-09-06 crate material (`saved_graphs/crate_pine_mcp_authored.ptex`) is the
first fully role-named graph and is the reference for the convention below.

## What changes

1. **A `rename_nodes(graph, mapping)` helper** in `quality/author_helpers.py`. Walks the
   top level and every `type == "graph"` subgraph, renaming nodes, both ends of every
   connection, and every `linked_widgets[].node` reference on `gen_parameters` remotes.
   Errors (raise) on a source name that does not exist at that level, on a target name
   already in use at that level, and on any attempt to rename `Material`, `gen_inputs`,
   `gen_outputs`, or `gen_parameters`. Renaming never touches `node_position`, so
   Material Maker's position-derived seeds (`get_seed_from_position` in
   `addons/material_maker/engine/nodes/gen_base.gd`) and therefore the renders are
   unchanged.
2. **Every cookbook builder ends with a rename pass**, after all surgery and after
   `group_into_subgraph`, before `save_variant`. Builders that use `take_variant`
   rename the returned graph. `author.py` (the Phase-3 builders) is not edited.
3. **Naming convention** (documented as a lever in `docs/AUTHORING.md`, matching Grayson's
   own edit):
   - PascalCase, role first, node type implied by a suffix where it helps:
     `*Noise` (perlin/fbm/voronoi generators), `*Layout` (bricks/pattern structure),
     `*Mask` (a 0/1 or ramp used as a blend port-2 mask), `*Color` (albedo colorize),
     `*Roughness`, `*Height`, `*Normal`, `*Composite` (a blend that produces a final
     channel), `*Warp`, `*Offset`, `*Flecks`, `NonMetallic`/`Metallic` (uniforms feeding
     the metallic port).
   - Names describe what the node contributes to the material, not what the node is
     (`MortarLines` beats `Bricks2`).
   - Unique within their level (top level, or inside one subgraph).
   - Reserved: `Material`, `gen_inputs`, `gen_outputs`, `gen_parameters`.
4. **A gate test** `tests/test_cookbook_naming_gate.py`, parametrized over every cookbook
   entry like `test_cookbook_subgraph_gate.py`: no node at any level (excluding the
   reserved four and `type` in `ios`/`remote`/`material`) may match
   `^[a-z][a-z0-9]*(_[a-z0-9]+)*_\d+$` (donor auto-name), be a bare node-type name
   (`colorize`, `blend`, `perlin`, `Perlin`, `Warp`), or collide with a sibling.
5. **Cards stay truthful by mechanism, not by hand.** `quality/promote_cookbook.py`
   writes (and `--check` verifies) a generated block into each `cookbook/<cat>/<id>.md`
   between `<!-- nodes:begin -->` and `<!-- nodes:end -->` markers: a table of
   `subgraph / node / type` for every non-reserved node in the promoted graph. Prose
   that names donor nodes (`wood`'s `colorize_2`) is left alone where it describes the
   donor as a starting point; where a card's prose names a node as something the reader
   should find in the shipped graph, the task that renames that category updates the
   sentence. The generated table is the authoritative map.
6. **Render-equality proof per category.** Before any builder changes, render every
   tracked cookbook graph once into a baseline directory (one Godot at a time, via a
   script file, never `python -c`). After each category's rename, regenerate it,
   promote, render the promoted graphs, and assert `render_compare.renders_match`
   against the baseline for all four maps. Thumbnails and the contact sheet are not
   regenerated (renders are unchanged; regenerating would churn unrelated PNGs, see the
   HANDOFF heads-up).

## What does not change

- `src/mm_mcp/*`: nothing. The MCP tools already accept any node name.
- `mm-play`: slider ids are `f"{subgraph_node}/{slot_id}"`; subgraph node names are
  already role names and are not renamed. Slot ids are untouched.
- `author.py` and `docs/evidence/phase3/`: untouched.
- Live-control: unchanged (live rename remains a non-goal; this is batch authoring).
- Upstream donor graphs in `quality/donors/`: untouched; the rename is applied to the
  builder's output, so the recipe text about donors stays accurate.

## Sizing (from the 2026-09-06 count)

| Category | Files | Auto-named / working nodes | Builder lines |
|---|---|---|---|
| stone | 9 | 98 / 155 | 724 |
| terrain | 8 | 83 / 111 | 504 |
| painted-metal | 6 | 61 / 88 | 427 |
| organics | 5 | 45 / 57 | 280 |
| fabrics | 7 | 42 / 62 | 378 |
| leather | 6 | 36 / 69 | 533 |
| wood | 3 | 31 / 43 | 209 |
| metal | 2 | 21 / 26 | 98 |
| scifi | 4 | 14 / 38 | 357 |
| glass | 1 | 12 / 15 | 106 |
| ceramic | 1 | 6 / 11 | 63 |
| plastics | 1 | 3 / 6 | 96 |

## Acceptance

- `pytest -q -m "not integration"` green including the new gate over all 53.
- `python -m quality.promote_cookbook --check` in sync.
- Every promoted graph's four maps match the pre-change baseline within
  `render_compare.TOLERANCE`.
- `git status` shows only builder `.py`, `cookbook/**/*.ptex`, `cookbook/**/*.md`,
  `quality/author_helpers.py`, `quality/promote_cookbook.py`, tests, and docs changed;
  no thumbnail or contact-sheet churn.
