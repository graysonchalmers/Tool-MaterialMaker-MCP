# PLAN — Tool-MaterialMaker-MCP

Phase plan with binary exit gates. Never start Phase N+1 until Phase N's gate is
green and recorded in [STATUS.md](../STATUS.md). Full rationale in the
[design spec](superpowers/specs/2026-08-25-material-maker-mcp-design.md).

## Phase 0 — Harness
Scaffold (done) plus a headless smoke test.
- Smoke renders a known bundled `.ptex` via Godot `--export` and asserts a
  non-empty PNG appears.
- **Gate:** `smoke/smoke.ps1` exits 0 and a PNG is produced.

## Phase 1 — Node catalog
Build `catalog.json` from `<MM_PROJECT>/addons/material_maker/nodes/*.mmg`.
- Per node: inputs, outputs, parameters (type, min, max, step, default, enum,
  desc).
- **Gate:** every bundled example in `material_maker/examples/*.ptex` validates
  cleanly against the catalog.

## Phase 2 — Render MCP
Wire catalog + validator + render runner behind the MCP server.
- Tools: `list_node_types`, `describe_node`, `validate_graph`, `render_graph`,
  `save_graph`, `list_examples`, `load_example`.
- **Gate:** an MCP `render_graph` call on a loaded example returns image paths.

## Phase 3 — Authoring quality
Prompt-to-graph on a small material test set; tune catalog descriptions and
authoring guidance. This is the hard phase. Detailed plan:
[2026-08-26-material-maker-mcp-phase3.md](superpowers/plans/2026-08-26-material-maker-mcp-phase3.md).
Multi-variant (2-3 versions per prompt) ships in this phase; a case hits if any
variant is usable.
- **Gate:** ≥ 70% usable-hit-rate (≥ 11/15) on the frozen 15-case test set,
  Grayson-audited scorecard recorded in STATUS.md. (Decided 2026-08-26.)
- Sub-gates: 3A harness + frozen test set → 3B baseline scorecard → 3C tuning
  loop to ≥ 70%.

## Phase 4 — Public packaging (later, sketched)
Config-driven paths, cross-platform, binary auto-detect, install docs.

## Phase 5 — Live-control (later, sketched)
GDScript plugin inside a forked Material Maker exposing add-node/connect/
set-param/render over a socket for interactive, watchable building.
