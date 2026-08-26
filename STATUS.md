# STATUS — Tool-MaterialMaker-MCP

> ⚠️ **Super-alpha.** Built by an artist/animator (not a software engineer) with
> heavy AI help. "Verified" below means "worked on the one machine it was built
> on," not "battle-tested." Expect breakage. See the README warning.

Gate ledger. Three states only: ✅ verified · 🔌 wired · ⬜ not started.

_Last updated: 2026-08-26_

## Phases

| Phase | Description | Gate | State | Evidence |
|---|---|---|---|---|
| 0 | Harness: scaffold + smoke render of a known example | Smoke renders a PNG, exits 0 | ✅ | `smoke.ps1` exit 0, 4 PNGs from bricks.ptex (albedo 2.2MB, normal 5MB, heightmap, orm) |
| 1 | Catalog: build `catalog.json` from `.mmg` files | Every bundled example validates | ✅ | all 43 bundled examples validate with zero type/connection errors (`tests/test_examples_gate.py`, `pytest -q` → 43 passed); catalog grew 342 → 392 node types after adding the 50 compound "graph"-family nodes (e.g. `normal_map`, `occlusion`) and the `ios` built-in to `SPECIAL_TYPES` |
| 2 | Render MCP: wire the four units end to end | "render this example" works over MCP | ✅ | `smoke/smoke_mcp.py` loads `bricks` via `server.load_example`, validates, and renders via `server.render_graph` — `SMOKE PASS: rendered 4 image(s)`, exit 0; full suite `pytest -v` → 76 passed (includes the Godot-launching integration test) |
| 3 | Authoring quality: prompt-to-graph, tune | ≥70% usable-hit-rate (≥11/15, any-variant) on frozen test set | ✅ | **15/15 (100%).** plan: `docs/superpowers/plans/2026-08-26-material-maker-mcp-phase3.md`; 3A+3B+3C all ✅ verified |
| 3A | Test set + scoring harness | Harness renders a known case → contact sheet + scorecard, exit 0; 15-case set frozen after Grayson review | ✅ | harness ✅: `run_case.py` on bricks-as-`s01_red_brick_wall` → 4 maps + `source.ptex` + scorecard, exit 0. Test set ✅: 15 cases across 7 categories, Grayson-reviewed (m02 anisotropy softened), `_meta.frozen=true` 2026-08-26 |
| 3B | Baseline measurement | Baseline scorecard, all 15 scored + miss taxonomy, recorded | ✅ | **baseline = 3/15 (20%)** with nearest-example-as-is, 1 variant/case, size 512. HITs: `s01` bricks, `o02` dry_earth, `m03` rusted_metal. Scorecard: `quality/scorecards/2026-08-26-baseline.md`. Miss taxonomy (3C worklist): wrong-example ×5 (m02,s02,s03,o01,man02), missing-composite ×3 (m01,man01,combo01), recolor-only ×2 (w02,f02), weak-attribute ×1 (w01), render-broken ×1 (f01) |
| 3C | Tuning loop | ≥70% hit-rate scorecard, Grayson-audited | ✅ | **iter1 = 15/15 (100%)**, up from 3/15 baseline. Levers: recolor (f02, w02, m01, s03) + grain-ramp (w01) + clone-a-sharp-edged-example (o01 moss) + voronoi per-cell-random flecks (s02) + wood-grain-as-brush (m02) + beehive hex clone (man01, man02) + paint-over-rust peel composite (combo01) + **weave-graft + normal_map fix (f01 denim)**. **FLAT-NORMAL BLOCKER RESOLVED:** `normal_map` is a compound (input → buffer → switch(**param4**) → edge_detect(param1)); default `param4=1` runs edge_detect on a pre-rendered buffer that comes back FLAT for a directly-fed analytic generator. Setting **`param4=0`** feeds the raw analytic input into edge_detect → real relief. This unblocked denim's twill normal and is a general fix for any analytic-generator graph. Scorecard: `quality/scorecards/2026-08-26-iter1.md`; recipes in `docs/AUTHORING.md`. |
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
