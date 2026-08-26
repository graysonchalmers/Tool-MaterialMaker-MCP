# HANDOFF — Tool-MaterialMaker-MCP

The session baton. Read at pickup, rewrite at wrap-up.

## Where things stand

- **Date:** 2026-08-25
- **Phase:** 1 and 2 complete. Catalog, graph builder/validator, render runner,
  and the MCP server (all seven tools + `catalog://nodes` resource) are built,
  tested, and wired end to end.
- Phase 2 gate is green: `smoke/smoke_mcp.py` loads the bundled `bricks` example
  through `mm_mcp.server`, validates it, and renders it via `render_graph` —
  `SMOKE PASS: rendered 4 image(s)`, exit 0. Full suite (`pytest -v`, 76 tests,
  including the Godot-launching integration test) passes.

## What just happened

- Implemented catalog_builder, graph/validator, render runner, and the MCP
  server across Tasks 1-8.
- Task 9: wrote `smoke/smoke_mcp.py` (the Phase 2 capstone smoke), ran it green,
  ran the full test suite green, and updated STATUS.md/HANDOFF.md/README.md.

## Next concrete step

- Start Phase 3 (authoring quality): build a material test set and iterate on
  prompt-to-graph authoring quality, tuning catalog descriptions and authoring
  guidance. This is an iterative tuning loop, not bite-sized TDD — it gets its
  own plan.
- Two open knobs to settle before/at Phase 3 kickoff:
  - The Phase 3 usable-hit-rate target (the quality bar for "good enough").
  - Whether to add multi-variant generation, or defer it further.

## Open questions

- Phase 3 usable-hit-rate target (the quality bar) not yet set.
- Whether to add multi-variant generation.

## Heads-up for the next agent

- Do not modify `C:\Projects-local\z-Git\material-maker` in Phase 1; it is the
  pristine upstream reference and the render target.
- Render runs need the MM project's `steam_appid.txt` present or Godot exits fast.
