# STATUS — Tool-MaterialMaker-MCP

Gate ledger. Three states only: ✅ verified · 🔌 wired · ⬜ not started.

_Last updated: 2026-08-25_

## Phases

| Phase | Description | Gate | State | Evidence |
|---|---|---|---|---|
| 0 | Harness: scaffold + smoke render of a known example | Smoke renders a PNG, exits 0 | ✅ | `smoke.ps1` exit 0, 4 PNGs from bricks.ptex (albedo 2.2MB, normal 5MB, heightmap, orm) |
| 1 | Catalog: build `catalog.json` from `.mmg` files | Every bundled example validates | ✅ | all 43 bundled examples validate with zero type/connection errors (`tests/test_examples_gate.py`, `pytest -q` → 43 passed); catalog grew 342 → 392 node types after adding the 50 compound "graph"-family nodes (e.g. `normal_map`, `occlusion`) and the `ios` built-in to `SPECIAL_TYPES` |
| 2 | Render MCP: wire the four units end to end | "render this example" works over MCP | ✅ | `smoke/smoke_mcp.py` loads `bricks` via `server.load_example`, validates, and renders via `server.render_graph` — `SMOKE PASS: rendered 4 image(s)`, exit 0; full suite `pytest -v` → 76 passed (includes the Godot-launching integration test) |
| 3 | Authoring quality: prompt-to-graph, tune | ≥70% usable-hit-rate (≥11/15, any-variant) on frozen test set | ⬜ | plan: `docs/superpowers/plans/2026-08-26-material-maker-mcp-phase3.md` |
| 4 | Public packaging (later) | Config-driven, cross-platform, docs | ⬜ | — |
| 5 | Live-control (later) | In-app socket drive, watchable build | ⬜ | — |

## Components

| Component | State | Notes |
|---|---|---|
| Project scaffold | ✅ | README, CLAUDE.md, HANDOFF.md, STATUS.md, PLAN.md, .gitignore, .env.example |
| Design spec | ✅ | Approved in brainstorming, pending Grayson's spec review |
| Upstream render path | ✅ | Verified: `--export-material` renders 4 PBR PNGs headlessly on this machine |
| smoke harness | ✅ | `smoke/smoke.ps1` runs and passes |
| catalog_builder.py | ✅ | Builds `catalog.json` from `.mmg` files; all 43 bundled examples validate against it |
| graph.py (build + validate) | ✅ | `Graph.to_ptex`/`from_ptex` + `validate_graph`; covered by `tests/test_graph.py`, `tests/test_validator.py` |
| render.py (runner) | ✅ | Headless Godot render runner; `tests/test_render.py` incl. the integration test that renders `bricks.ptex` for real |
| server.py (MCP) | ✅ | All seven tools + `catalog://nodes` resource; exercised end to end by `smoke/smoke_mcp.py` |
