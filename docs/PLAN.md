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
- Tools: `list_node_types`, `describe_node`, `validate`, `render_graph`,
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

## Phase 4 — Public packaging
Config-driven paths, cross-platform, binary auto-detect, install docs.
- **Gate:** installable via `pip install -e .`/wheel, `mm-mcp --check` setup
  doctor, install docs written.
- **State:** done except cross-platform. Installable, config-driven, and
  doctored; PyPI publish is on hold (GitHub-clone distribution instead) and
  macOS/Linux remain unverified. See STATUS.md.

## Phase 5 — Live-control
A GDScript addon layered onto a disposable Material Maker overlay (no source
fork) exposing add-node/connect/disconnect/set-param/render/clear over a
socket for interactive, watchable building.
- **Gate:** a hands-on session with Grayson watching nodes appear and render
  live in the real GUI.
- **State:** done. Built via TDD, hands-on verified 2026-08-28. See STATUS.md
  and the design spec:
  [2026-08-26-live-control-addon-design.md](superpowers/specs/2026-08-26-live-control-addon-design.md).
