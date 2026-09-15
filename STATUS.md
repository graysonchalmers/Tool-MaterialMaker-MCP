# STATUS - Tool-MaterialMaker-MCP

> ⚠️ **Super-alpha.** Built by an artist/animator (not a software engineer) with
> heavy AI help. "Verified" below means "worked on the one machine it was built
> on," not "battle-tested." Expect breakage. See the README warning.

Gate ledger. Three states only: ✅ verified · 🔌 wired · ⬜ not started.

_Last updated: 2026-09-15 (reflections cycle MERGED to `main` `007d493`, pushed — see callout).
Prior: 2026-09-14 normal/albedo audit + 5 fixes and `task_73027cd8` fix, both on `main`._

> 🪞 **Reflections cycle — MERGED to `main` (`007d493`, pushed), fast suite 1217 green:**
> Rig gained ambient/reflection decouple, a `SKY_ONLY` sun-disc reflection, SSR
> (`ssr_enabled`), and an opt-in preview-only clearcoat param (`render_preview(clearcoat=)`,
> default 0.0 no-op). New objective gate `quality/preview_regress.py` diffs the 3D preview
> COMPOSITE. Three reflective materials added (cookbook 71→74): `m05_polished_chrome`,
> `s14_wet_river_stone` (dielectric, roughness-masked), `m06_car_paint`. A global normal
> green-flip attempt was REVERTED (`4e239da`) after it inverted the approved materials — the
> triplanar rig is fine, m04's raised scratches are an isolated pre-existing m04 quirk.
> **Not final:** Grayson wants s14 pebbles to reflect on faces + vary size + less-flat tops, and
> the car-paint clearcoat to gain surface detail (next session). Ledger:
> `.superpowers/sdd/2026-09-14-reflections/progress.md`. Spec/plan under `docs/superpowers/`.

> 🔧 **Normal/albedo registration audit + 5 fixes (MERGED):** two new `quality/` tools +
> 5 material normal-registration fixes. An audit found 8/71 materials whose normal relief
> was built from a different noise source than their albedo (relief did not register with
> color). Fixed: `s02_gray_granite`, `s06_river_pebbles`, `s04_scattered_river_stones`,
> `t03_gravel`, `pm04_hammertone` (all audit-clean, full suite green). Left as fine-by-design:
> `t02_fresh_snow`, `pm01_powder_coat`, `pm02_automotive_enamel`. Still pending: soften
> s06/t03 relief to domes (Grayson request), cube triplanar+bevel, and the original
> front-page showcase regen (hero+gallery stills on the new rig + a top-5 GIF strip). See
> `HANDOFF.md` + `.superpowers/sdd/2026-09-14-showcase-lighting-refresh/progress.md`.

> ✅ **`task_73027cd8` fixed:** the round-3 catalog fix's resolved `default`
> field was taken from the wrong (linked inner leaf) node for compound-node
> params (e.g. `crystal.param0` reported 4, real default 16, from its own
> `remote`/`gen_parameters` block). `_parse_generic_node` now prefers the
> remote node's own declared default. Commit `948a8e7`, open as
> [PR #11](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/pull/11)
> with CI green, ready to merge. Fast suite 1165 passed. See `HANDOFF.md`'s
> session log for detail.
>
> ✅ **Round 3 MERGED to `main`:** six more proof materials on
> previously-unused catalog nodes, all Grayson-approved: `m04_scratched_steel`
> (scratches), `f11_corduroy` (directional_noise), `t10_packed_dirt` (dirt),
> `gl04_raw_crystal_cluster` (crystal), `pm06_splatter_finish` (splatter),
> `man03_mosaic_tile` (skewed_bricks -- swapped in for `custom_tiles`, which
> needs an out-of-scope `sdf2d` input). Cookbook is now 71 materials, 12
> categories; live noise coverage 20/53. Also fixed a real pre-existing
> `catalog_builder.py` bug this round surfaced (compound-node param range
> resolution for `named_parameter` widgets and type-referenced `linked_control`
> links, plus a fixpoint-loop fix for compound-to-compound reference chains
> after the first pass proved order-dependent). Full task-by-task ledger at
> `.superpowers/sdd/2026-09-14-noise-vocabulary-round-3/progress.md`; see
> `HANDOFF.md`'s session log for the summary. Plan:
> `docs/superpowers/plans/2026-09-14-noise-vocabulary-round-3.md`. Prior
> rounds' callouts retired to `HANDOFF.md`'s session log per this file's own
> "state + one line + evidence pointer" rule.

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
| `src/mm_mcp/catalog_builder.py` | ✅ | `.mmg` -> `catalog.json`, incl. compound-node param ranges (a bounded fixpoint pass over compound-to-compound reference chains, 2026-09-14, order-independence regression-tested) and defaults sourced from the remote node's own block, not the linked inner node (`task_73027cd8`, 2026-09-14, PR #11 open). `tests/test_catalog_*.py` |
| `src/mm_mcp/validator.py`, `graph.py` | ✅ | Graph validation (errors as data), recurses into subgraphs (2026-09-06, `577592f`), + pure helpers. `tests/test_validator.py`, `tests/test_graph.py` |
| `src/mm_mcp/render.py` | ✅ | Headless Godot runner, `--target` profiles (Godot, Unity/URP verified; Unreal UE5 file-level only), process-tree kill, temp-file IO. `tests/test_render.py` |
| `src/mm_mcp/server.py` (+ `idle.py`) | ✅ | 11 batch tools + 7 live tools + `catalog://nodes` + `guide://authoring`; opt-in idle exit (`MM_IDLE_EXIT_MINUTES`, 2026-09-06). `tests/test_server_tools.py`, `tests/test_server_live.py`, `tests/test_server_idle.py`, `tests/test_idle.py`; counts enforced by `tests/test_readme_counts.py` |
| `src/mm_mcp/doctor.py`, `paths.py`, `inspect.py`, `config.py` | ✅ | Setup preflight, opt-in path bounding (`MM_ALLOWED_ROOTS`), `.ptex` metrics, env config. Matching `tests/test_*.py` |
| `src/mm_mcp/preview.py` + `preview_project/` | ✅ | `render_preview` 3D composite. Rig reworked 2026-09-14 (`24ff854`): sphere + `_rounded_box` bevel cube + lathed chess rook (`_lathe`/`_catmull_profile` molding), ALL on one triplanar material at a unified world-space density (default tile 0.45, per-material `_make_showcase._TILE_OVERRIDES`). Lighting rig (`6ce84c6`): soft key shadow, boosted shadow-casting rim, sky bounce+reflections, SSAO. Front-page gallery/hero regenerated on this rig; all Grayson visual-approved. `tests/test_preview.py` |
| `render_preview_sweep` (`preview.py` + `preview_project/`) | ✅ | 2026-09-14: default sweep changed from the azimuth 360 orbit to a PRECESSION (`6ce84c6`) -- key aim wobbles in a cone (default 18 deg, rim/fill held still) so highlights circle relief without going backlit; `sweep_kind="azimuth"`/`cone` still reachable. Motion integration test now exercises precession, clears its floor empirically. One Godot process, looping GIF, `Pillow` runtime dep. `tests/test_preview.py` |
| `src/mm_mcp/overlay.py` + `addons/mm_live/` + `src/mm_mcp/live.py` | ✅ | Disposable MM overlay with a GDScript socket addon (port 8765); client with `connect_or_launch`, 8 commands incl. `load_graph`. `tests/test_overlay.py`, `tests/test_live.py` |
| `src/mm_mcp/play/` (`mm-play`, `play.bat`) | ✅ | Slider web page over cookbook subgraph params with a WebGL sphere; Grayson ran `play.bat` hands-on 2026-09-05. Refuses to start beside a stale listener and names the PID (2026-09-05). `tests/test_play_*.py`; `docs/superpowers/specs/2026-09-04-play-surface-design.md` |
| `cookbook/` + `quality/cookbook_*.py` + `promote_cookbook.py` | ✅ | 71 tracked materials on `main`, 12 categories (all six round-3 materials merged), subgraph-grouped, every node role-named (2026-09-06, render-identical), each card carrying a generated node table; builders are the source, `--check` is the regression baseline for graphs and card tables. `tests/test_cookbook*.py` incl. `test_cookbook_naming_gate.py`, `test_cookbook_card_table_gate.py`; `cookbook/README.md` |
| `docs/AUTHORING.md` + `guide://authoring` | ✅ | Invariant authoring guide served as an MCP resource; per-material recipes are cards beside each `.ptex`. `tests/test_guide_resource.py` |
| `quality/debug_swatches.py` | ✅ | 19 single-node diagnostic swatches with pixel assertions (merged to `main` with round 1; slope_blur structural-only, buffer node cannot render headless). Surfaced in README's "Core toolbox" section as a swatch contact sheet. `tests/test_debug_swatches.py`; `docs/DEBUG_SWATCHES.md` |
| `quality/` package (builders, helpers, naming checker, render_tracked, promote/check, swatches) | ✅ | Importable package, `python -m quality.<module>`; `author.py` is the shared builder base, guarded by `--check`. `tests/test_quality_package.py`, `tests/test_cookbook_builders_signature.py`; `quality/README.md` |
| `quality/node_usage_audit.py` | ✅ | Recurses cookbook subgraphs, reports live noise/pattern node coverage against a curated 53-node list (`_NOISE_PATTERN_NODES`); replaces the old one-time manual histogram. AUTHORING.md's coverage line is test-enforced against its live output. `tests/test_node_usage_audit.py`, `tests/test_authoring_counts.py` |
| `quality/normal_albedo_audit.py` | ✅ (branch) | Static audit: traces albedo(port 0)/normal(port 4) source generators across subgraph proxies, flags materials where the sets are disjoint (relief does not register with color). Reviewer hand-verified traversal. `tests/test_normal_albedo_audit.py` (branch `showcase-lighting-refresh`, commit `9678006`) |
| `quality/_make_showcase.py` | ✅ (branch) | Reproducible front-page render pipeline (still 1024x576 / hero 3-panel montage / gif modes); import-safe (Godot lazy). `tests/test_make_showcase.py` (branch `showcase-lighting-refresh`, commit `7d9f2a2`). Not yet used to regen the tracked gallery. |
| `docs/evidence/phase3/` | ✅ | Frozen Phase-3 test set, rubric, and both scorecards, archived 2026-09-05; runner retired. `tests/test_phase3_evidence.py` |
| Packaging (wheel/sdist, CI, release-please) | 🔌 | `twine`-clean, clean-venv verified, windows-latest CI green, release PRs auto-opened. PyPI on hold; macOS/Linux untested |
| Backup (nightly `backup-ops` mirror to V:) | ✅ | Regenerable render output and the overlay excluded 2026-09-05 (`C:\Projects-local\backup-ops\projects.psd1`, `Tool-MaterialMaker-MCP` override) |
