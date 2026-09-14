# STATUS - Tool-MaterialMaker-MCP

> ⚠️ **Super-alpha.** Built by an artist/animator (not a software engineer) with
> heavy AI help. "Verified" below means "worked on the one machine it was built
> on," not "battle-tested." Expect breakage. See the README warning.

Gate ledger. Three states only: ✅ verified · 🔌 wired · ⬜ not started.

_Last updated: 2026-09-14 (round 1's noise/distortion vocabulary + core-toolbox plan MERGED to `main` and pushed 2026-09-13 (`0169446`); round 2 FINISHED on branch `noise-vocabulary-round-2`, all 11 tasks landed and reviewed clean, not yet merged)._

> 🔌 **Finished on branch `noise-vocabulary-round-2`, ready to merge:** a
> reusable `quality/node_usage_audit.py` script (live noise/pattern coverage
> reporting, replaces the old one-time manual histogram) plus six more proof
> materials on previously-unused catalog nodes, all landed and approved:
> `l07_pebbled_leather` (fbm Cellular 1), `f09_plaid_flannel` (fbm Cellular 3),
> `f10_boucle_upholstery` (fbm Cellular 5), `sf05_circuit_maze_panel` (truchet
> Line), `gl03_shattered_crystal` (shard_fbm), `w06_burled_wood` (warp2).
> README/AUTHORING count integration done (65 materials, 14/53 live noise
> nodes). Full task-by-task ledger for this round lived at
> `.superpowers/sdd/2026-09-13-noise-vocabulary-round-2/progress.md`,
> deleted per this skill's own convention once the final review closed
> clean; see `HANDOFF.md`'s session log for the summary. Plan:
> `docs/superpowers/plans/2026-09-13-noise-vocabulary-round-2.md`. One
> finding parked at Task 8's review (the shared `wood` donor bleeds
> GrainMask into Material's metallic port, w04/w05/w06 alike) was fully
> closed before merge: `main`'s `a984312` fixed w04/w05, this branch's
> `0997d6d` fixed w06 the same way. Merge to `main` is Grayson's call, same
> as round 1; given, in progress.

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
| 3 | Authoring quality | >= 70% usable on the frozen 15-case set | ✅ | 15/15. `docs/evidence/phase3/2026-08-26-iter1.md`; plan `docs/superpowers/plans/2026-08-26-material-maker-mcp-phase3.md` |
| 4 | Public packaging | Installable, config-driven, doctored, cross-platform | 🔌 | Installable + `mm-mcp --check` + CI + release-please done (`docs/superpowers/specs/2026-08-30-phase4-hardening-design.md`). macOS/Linux unverified, no machine. PyPI on hold (GitHub-clone route). |
| 5 | Live-control | Hands-on session watching nodes appear live | ✅ | 2026-08-28 hands-on. `docs/superpowers/specs/2026-08-26-live-control-addon-design.md`; `tests/test_live.py`, `tests/test_server_live.py` |

## Components

| Component | State | What it is / evidence |
|---|---|---|
| `src/mm_mcp/catalog_builder.py` | ✅ | `.mmg` -> `catalog.json`, incl. compound-node param ranges. `tests/test_catalog_*.py` |
| `src/mm_mcp/validator.py`, `graph.py` | ✅ | Graph validation (errors as data), recurses into subgraphs (2026-09-06, `577592f`), + pure helpers. `tests/test_validator.py`, `tests/test_graph.py` |
| `src/mm_mcp/render.py` | ✅ | Headless Godot runner, `--target` profiles (Godot, Unity/URP verified; Unreal UE5 file-level only), process-tree kill, temp-file IO. `tests/test_render.py` |
| `src/mm_mcp/server.py` (+ `idle.py`) | ✅ | 10 batch tools + 7 live tools + `catalog://nodes` + `guide://authoring`; opt-in idle exit (`MM_IDLE_EXIT_MINUTES`, 2026-09-06). `tests/test_server_tools.py`, `tests/test_server_live.py`, `tests/test_server_idle.py`, `tests/test_idle.py`; counts enforced by `tests/test_readme_counts.py` |
| `src/mm_mcp/doctor.py`, `paths.py`, `inspect.py`, `config.py` | ✅ | Setup preflight, opt-in path bounding (`MM_ALLOWED_ROOTS`), `.ptex` metrics, env config. Matching `tests/test_*.py` |
| `src/mm_mcp/preview.py` + `preview_project/` | ✅ | `render_preview` 3D composite (sphere/cube/cutaway). `tests/test_preview.py` |
| `src/mm_mcp/overlay.py` + `addons/mm_live/` + `src/mm_mcp/live.py` | ✅ | Disposable MM overlay with a GDScript socket addon (port 8765); client with `connect_or_launch`, 8 commands incl. `load_graph`. `tests/test_overlay.py`, `tests/test_live.py` |
| `src/mm_mcp/play/` (`mm-play`, `play.bat`) | ✅ | Slider web page over cookbook subgraph params with a WebGL sphere; Grayson ran `play.bat` hands-on 2026-09-05. Refuses to start beside a stale listener and names the PID (2026-09-05). `tests/test_play_*.py`; `docs/superpowers/specs/2026-09-04-play-surface-design.md` |
| `cookbook/` + `quality/cookbook_*.py` + `promote_cookbook.py` | ✅ | 59 tracked materials on `main`, 12 categories; 65 on branch `noise-vocabulary-round-2` (all six round-2 materials landed and reviewed clean; branch not yet merged), subgraph-grouped, every node role-named (2026-09-06, render-identical), each card carrying a generated node table; builders are the source, `--check` is the regression baseline for graphs and card tables. `tests/test_cookbook*.py` incl. `test_cookbook_naming_gate.py`, `test_cookbook_card_table_gate.py`; `cookbook/README.md` |
| `docs/AUTHORING.md` + `guide://authoring` | ✅ | Invariant authoring guide served as an MCP resource; per-material recipes are cards beside each `.ptex`. `tests/test_guide_resource.py` |
| `quality/debug_swatches.py` | ✅ | 19 single-node diagnostic swatches with pixel assertions (merged to `main` with round 1; slope_blur structural-only, buffer node cannot render headless). Surfaced in README's "Core toolbox" section as a swatch contact sheet. `tests/test_debug_swatches.py`; `docs/DEBUG_SWATCHES.md` |
| `quality/` package (builders, helpers, naming checker, render_tracked, promote/check, swatches) | ✅ | Importable package, `python -m quality.<module>`; `author.py` is the shared builder base, guarded by `--check`. `tests/test_quality_package.py`, `tests/test_cookbook_builders_signature.py`; `quality/README.md` |
| `quality/node_usage_audit.py` | ✅ (on branch `noise-vocabulary-round-2`) | Recurses cookbook subgraphs, reports live noise/pattern node coverage against a curated 52-node list (`_NOISE_PATTERN_NODES`); replaces the old one-time manual histogram. AUTHORING.md's coverage line is test-enforced against its live output. `tests/test_node_usage_audit.py`, `tests/test_authoring_counts.py` |
| `docs/evidence/phase3/` | ✅ | Frozen Phase-3 test set, rubric, and both scorecards, archived 2026-09-05; runner retired. `tests/test_phase3_evidence.py` |
| Packaging (wheel/sdist, CI, release-please) | 🔌 | `twine`-clean, clean-venv verified, windows-latest CI green, release PRs auto-opened. PyPI on hold; macOS/Linux untested |
| Backup (nightly `backup-ops` mirror to V:) | ✅ | Regenerable render output and the overlay excluded 2026-09-05 (`C:\Projects-local\backup-ops\projects.psd1`, `Tool-MaterialMaker-MCP` override) |
