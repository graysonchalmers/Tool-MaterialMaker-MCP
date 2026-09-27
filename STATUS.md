# STATUS - Tool-MaterialMaker-MCP

> ⚠️ **Super-alpha.** Built by an artist/animator (not a software engineer) with
> heavy AI help. "Verified" below means "worked on the one machine it was built
> on," not "battle-tested." Expect breakage. See the README warning.

Gate ledger. Three states only: ✅ verified · 🔌 wired · ⬜ not started.

_Last updated: 2026-09-27 (hosts m02/s14/s07 merged, cookbook 66; v0.8.1 released, 0.9.0 release PR #15 open). Narrative lives in `HANDOFF.md` and `docs/teardowns/TEARDOWN-2026-09-27.md`, not here._

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
| `src/mm_mcp/catalog_builder.py` | ✅ | `.mmg` -> `catalog.json`, incl. compound-node param ranges (a bounded fixpoint pass over compound-to-compound reference chains, 2026-09-14, order-independence regression-tested) and defaults sourced from the remote node's own block, not the linked inner node (`task_73027cd8`, merged PR #11). `tests/test_catalog_*.py` |
| `src/mm_mcp/validator.py`, `graph.py` | ✅ | Graph validation (errors as data), recurses into subgraphs (2026-09-06, `577592f`), + pure helpers. `tests/test_validator.py`, `tests/test_graph.py` |
| `src/mm_mcp/render.py` | ✅ | Headless Godot runner, `--target` profiles (Godot, Unity/URP verified; Unreal UE5 file-level only). `size` honoured by downsampling MM's fixed 2048 bake; ok only on exit 0 + decodable maps; flat-normal "invalid shader" race retried up to twice (`a70bc47`); outdir forced absolute. `tests/test_render.py` |
| `src/mm_mcp/server.py` (+ `idle.py`) | ✅ | 11 batch tools + 7 live tools + `catalog://nodes` + `guide://authoring`, every tool described (test-enforced since `d4601a0`); opt-in idle exit (`MM_IDLE_EXIT_MINUTES`). `tests/test_server_tools.py`, `tests/test_server_live.py`, `tests/test_server_idle.py`, `tests/test_idle.py`; counts enforced by `tests/test_readme_counts.py` |
| `src/mm_mcp/doctor.py`, `paths.py`, `inspect.py`, `config.py` | ✅ | Setup preflight, opt-in path bounding (`MM_ALLOWED_ROOTS`), `.ptex` metrics, env config. Matching `tests/test_*.py` |
| `src/mm_mcp/preview.py` + `preview_project/` | ✅ | `render_preview` 3D composite. Rig reworked 2026-09-14 (`24ff854`): sphere + `_rounded_box` bevel cube + lathed chess rook, ALL on one triplanar material at a unified world-space density (default tile 0.45). Lighting rig (`6ce84c6`): soft key shadow, rim, sky bounce+reflections, SSAO. Reflections (2026-09-15): sun-disc + SSR + opt-in clearcoat. Deep Parallax (2026-09-16): opt-in `heightmap_path`/`heightmap_scale`; the sphere swaps to its own non-triplanar material ONLY when a heightmap is given (Godot 4.7 cannot compose heightmap with triplanar UV — confirmed via engine warning), with its own tuned UV scale (`SPHERE_HEIGHTMAP_UV_SCALE`) and a matched shared-material tile density (`SPHERE_MATCHED_TRIPLANAR_TILE`) so cube/rook/ground read consistently in the same demo. Front-page gallery/hero unaffected (still the original rig for non-heightmap renders, no-op verified by `quality/preview_regress.py`). `tests/test_preview.py` |
| `render_preview_sweep` (`preview.py` + `preview_project/`) | ✅ | 2026-09-14: default sweep is a PRECESSION (`6ce84c6`) -- key aim wobbles in a cone so highlights circle relief without going backlit; `sweep_kind="azimuth"` still reachable. 2026-09-16: `sweep_kind="parallax_spin"` (opt-in, only meaningful with `heightmap_path`) rotates the demo sphere itself instead of the light, since parallax is camera-angle- not light-angle-dependent. One Godot process, looping GIF, `Pillow` runtime dep. Frames stage privately and the GIF publishes atomically (PR #13, `53585a4`). `tests/test_preview.py`, `tests/test_preview_sweep.py` |
| `src/mm_mcp/overlay.py` + `addons/mm_live/` + `src/mm_mcp/live.py` | ✅ | Disposable MM overlay with a GDScript socket addon (port 8765); client with `connect_or_launch`, 8 commands incl. `load_graph`. `tests/test_overlay.py`, `tests/test_live.py` |
| `src/mm_mcp/play/` (`mm-play`, `play.bat`) | ✅ | Slider web page over cookbook subgraph params with a WebGL sphere; Grayson ran `play.bat` hands-on 2026-09-05. Refuses to start beside a stale listener and names the PID. Renders at 2048 (`98fccdc`). Download is bound to the exact render snapshot, slider values included (PR #7 `f44a799`, pruned to 20 in `cad3838`). `tests/test_play_*.py`; `docs/superpowers/specs/2026-09-04-play-surface-design.md` |
| `cookbook/` + `quality/cookbook_*.py` + `promote_cookbook.py` | ✅ | 66 tracked materials on `main`, 12 categories, subgraph-grouped, every node role-named (render-identical), each card carrying a generated node table; builders are the source, `--check` is the regression baseline. `s09_ashlar_wall` is the first material with a deliberate `depth_tex` (Deep Parallax) connection (2026-09-16, real round-trip export, not preview-only). `s14`/`m06` retunes Grayson-approved 2026-09-27. Host materials (2026-09-27): m02 (absorbed m03-m05), s14 (s04/s06/t08), s07 (s08/s10); defaults pixel-identical, proof in commit messages. `tests/test_cookbook*.py` incl. `test_cookbook_naming_gate.py`, `test_cookbook_card_table_gate.py`; `cookbook/README.md` |
| `docs/AUTHORING.md` + `guide://authoring` | ✅ | Invariant authoring guide served as an MCP resource; per-material recipes are cards beside each `.ptex`. `tests/test_guide_resource.py` |
| `quality/debug_swatches.py` | ✅ | 19 single-node diagnostic swatches with pixel assertions (merged to `main` with round 1; slope_blur structural-only, buffer node cannot render headless). Surfaced in README's "Core toolbox" section as a swatch contact sheet. `tests/test_debug_swatches.py`; `docs/DEBUG_SWATCHES.md` |
| `quality/` package (builders, helpers, naming checker, render_tracked, promote/check, swatches) | ✅ | Importable package, `python -m quality.<module>`; `author.py` is the shared builder base, guarded by `--check`. `tests/test_quality_package.py`, `tests/test_cookbook_builders_signature.py`; `quality/README.md` |
| `quality/node_usage_audit.py` | ✅ | Recurses cookbook subgraphs, reports live noise/pattern node coverage against a curated 53-node list (`_NOISE_PATTERN_NODES`); replaces the old one-time manual histogram. AUTHORING.md's coverage line is test-enforced against its live output. `tests/test_node_usage_audit.py`, `tests/test_authoring_counts.py` |
| `quality/normal_albedo_audit.py` | ✅ | Static audit: traces albedo(port 0)/normal(port 4) source generators across subgraph proxies, flags materials where the sets are disjoint (relief does not register with color). Reviewer hand-verified traversal. `tests/test_normal_albedo_audit.py` |
| `quality/_make_showcase.py` | ✅ | Reproducible front-page render pipeline (still 1024x576 / hero 3-panel montage / gif modes); import-safe (Godot lazy). `tests/test_make_showcase.py`. The tracked contact sheet is stale (71 of 74) and no script writes its tracked path. |
| `docs/evidence/phase3/` | ✅ | Frozen Phase-3 test set, rubric, and both scorecards, archived 2026-09-05; runner retired. `tests/test_phase3_evidence.py` |
| Packaging (wheel/sdist, CI, release-please) | 🔌 | `twine`-clean, clean-venv verified, windows-latest CI green, release PRs auto-opened. PyPI on hold; macOS/Linux untested |
| Backup (nightly `backup-ops` mirror to V:) | ✅ | Regenerable render output and the overlay excluded 2026-09-05 (`C:\Projects-local\backup-ops\projects.psd1`, `Tool-MaterialMaker-MCP` override) |
