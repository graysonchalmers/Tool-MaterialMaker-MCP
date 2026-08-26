# STATUS — Tool-MaterialMaker-MCP

Gate ledger. Three states only: ✅ verified · 🔌 wired · ⬜ not started.

_Last updated: 2026-08-25_

## Phases

| Phase | Description | Gate | State | Evidence |
|---|---|---|---|---|
| 0 | Harness: scaffold + smoke render of a known example | Smoke renders a PNG, exits 0 | ✅ | `smoke.ps1` exit 0, 4 PNGs from bricks.ptex (albedo 2.2MB, normal 5MB, heightmap, orm) |
| 1 | Catalog: build `catalog.json` from `.mmg` files | Every bundled example validates | ⬜ | — |
| 2 | Render MCP: wire the four units end to end | "render this example" works over MCP | ⬜ | — |
| 3 | Authoring quality: prompt-to-graph, tune | Agreed usable-hit-rate on test set | ⬜ | — |
| 4 | Public packaging (later) | Config-driven, cross-platform, docs | ⬜ | — |
| 5 | Live-control (later) | In-app socket drive, watchable build | ⬜ | — |

## Components

| Component | State | Notes |
|---|---|---|
| Project scaffold | ✅ | README, CLAUDE.md, HANDOFF.md, STATUS.md, PLAN.md, .gitignore, .env.example |
| Design spec | ✅ | Approved in brainstorming, pending Grayson's spec review |
| Upstream render path | ✅ | Verified: `--export-material` renders 4 PBR PNGs headlessly on this machine |
| smoke harness | ✅ | `smoke/smoke.ps1` runs and passes |
| catalog_builder.py | ⬜ | |
| graph.py (build + validate) | ⬜ | |
| render.py (runner) | ⬜ | |
| server.py (MCP) | ⬜ | |
