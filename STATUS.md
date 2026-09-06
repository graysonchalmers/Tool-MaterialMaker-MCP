# STATUS - Tool-MaterialMaker-MCP

> ⚠️ **Super-alpha.** Built by an artist/animator (not a software engineer) with
> heavy AI help. "Verified" below means "worked on the one machine it was built
> on," not "battle-tested." Expect breakage. See the README warning.

Gate ledger. Three states only: ✅ verified · 🔌 wired · ⬜ not started.

_Last updated: 2026-09-05._

**How to read this file (rule adopted 2026-09-05, teardown #3):** each cell holds
the state, one line of what it is, and a pointer to where the evidence lives
(a test file, a doc, a commit). Corrections, reversals, and session narrative
go in `HANDOFF.md`'s session log or `git log`, never into a cell. If a row
needs more than three lines to explain, the explanation belongs in a doc the
row points at.

## Phases

| Phase | Description | Gate | State | Evidence |
|---|---|---|---|---|
| 0 | Harness: scaffold + smoke render | `smoke.ps1` exits 0 with PNGs | ✅ | `smoke/smoke.ps1` |
| 1 | Node catalog from `.mmg` files | Every bundled example validates | ✅ | `tests/test_examples_gate.py` (43 bundled examples, 392 node types) |
| 2 | Render MCP end to end | `render_graph` over MCP returns images | ✅ | `smoke/smoke_mcp.py`; `tests/test_render.py` integration test |
| 3 | Authoring quality | >= 70% usable on the frozen 15-case set | ✅ | 15/15. `quality/scorecards/2026-08-26-iter1.md`; plan `docs/superpowers/plans/2026-08-26-material-maker-mcp-phase3.md` |
| 4 | Public packaging | Installable, config-driven, doctored, cross-platform | 🔌 | Installable + `mm-mcp --check` + CI + release-please done (`docs/superpowers/specs/2026-08-30-phase4-hardening-design.md`). macOS/Linux unverified, no machine. PyPI on hold (GitHub-clone route). |
| 5 | Live-control | Hands-on session watching nodes appear live | ✅ | 2026-08-28 hands-on. `docs/superpowers/specs/2026-08-26-live-control-addon-design.md`; `tests/test_live.py`, `tests/test_server_live.py` |

## Components

| Component | State | What it is / evidence |
|---|---|---|
| `src/mm_mcp/catalog_builder.py` | ✅ | `.mmg` -> `catalog.json`, incl. compound-node param ranges. `tests/test_catalog_*.py` |
| `src/mm_mcp/validator.py`, `graph.py` | ✅ | Graph validation (errors as data) + pure helpers. `tests/test_validator.py`, `tests/test_graph.py` |
| `src/mm_mcp/render.py` | ✅ | Headless Godot runner, `--target` profiles (Godot, Unity/URP verified; Unreal UE5 file-level only), process-tree kill, temp-file IO. `tests/test_render.py` |
| `src/mm_mcp/server.py` | ✅ | 10 batch tools + 7 live tools + `catalog://nodes` + `guide://authoring`. `tests/test_server_tools.py`, `tests/test_server_live.py`; counts enforced by `tests/test_readme_counts.py` |
| `src/mm_mcp/doctor.py`, `paths.py`, `inspect.py`, `config.py` | ✅ | Setup preflight, opt-in path bounding (`MM_ALLOWED_ROOTS`), `.ptex` metrics, env config. Matching `tests/test_*.py` |
| `src/mm_mcp/preview.py` + `preview_project/` | ✅ | `render_preview` 3D composite (sphere/cube/cutaway). `tests/test_preview.py` |
| `src/mm_mcp/overlay.py` + `addons/mm_live/` + `src/mm_mcp/live.py` | ✅ | Disposable MM overlay with a GDScript socket addon (port 8765); client with `connect_or_launch`, 8 commands incl. `load_graph`. `tests/test_overlay.py`, `tests/test_live.py` |
| `src/mm_mcp/play/` (`mm-play`, `play.bat`) | ✅ | Slider web page over cookbook subgraph params with a WebGL sphere; Grayson ran `play.bat` hands-on 2026-09-05. Refuses to start beside a stale listener and names the PID (2026-09-05). `tests/test_play_*.py`; `docs/superpowers/specs/2026-09-04-play-surface-design.md` |
| `cookbook/` + `quality/cookbook_*.py` + `promote_cookbook.py` | ✅ | 53 tracked materials, 12 categories, each subgraph-grouped with a card and thumbnail; builders are the source, `--check` is the regression baseline. `tests/test_cookbook*.py`; `cookbook/README.md` |
| `docs/AUTHORING.md` + `guide://authoring` | ✅ | Invariant authoring guide served as an MCP resource; per-material recipes are cards beside each `.ptex`. `tests/test_guide_resource.py` |
| `quality/debug_swatches.py` | ✅ | 13 single-node diagnostic swatches with pixel assertions. `tests/test_debug_swatches.py`; `docs/DEBUG_SWATCHES.md` |
| `quality/` Phase-3 harness (`author.py`, `run_case.py`, `test_set.json`, `scorecards/`) | ✅ | Frozen evidence for the Phase 3 gate. Do not edit. `quality/README.md` |
| Packaging (wheel/sdist, CI, release-please) | 🔌 | `twine`-clean, clean-venv verified, windows-latest CI green, release PRs auto-opened. PyPI on hold; macOS/Linux untested |
| Backup (nightly `backup-ops` mirror to V:) | ✅ | Regenerable render output and the overlay excluded 2026-09-05 (`C:\Projects-local\backup-ops\projects.psd1`, `Tool-MaterialMaker-MCP` override) |
