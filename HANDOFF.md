# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-26 (evening, cont. 3) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**v0.2.0 PyPI packaging + v0.3.0 setup doctor landed and pushed. Distribution is
GitHub-clone for now (PyPI on hold).** Public repo, MIT, Phase 3 still 15/15.
This session made the package genuinely installable and added a first-run setup
preflight:
- **v0.2.0** (`3ab2859`+`23bef31`): fixed `config.py` so a `pip`-installed copy
  works (was `_PROJECT_ROOT` resolving into site-packages); `.env` now cwd-based
  (or `MM_DOTENV`), `MM_OUTPUT_DIR` defaults to `./output`, personal path
  defaults removed; lowered `requires-python` to **3.10** (no 3.13-only syntax);
  added classifiers/keywords + a Windows-only OS classifier (honest alpha);
  `MANIFEST.in` prunes `tests/` from the sdist.
- **v0.3.0** (`3abc4d2`): **`mm-mcp --check`** setup doctor — one green/red
  checklist (project path, node defs, examples, `steam_appid.txt` contents,
  Godot binary + console-variant detection, output-dir writability, catalog
  build), exits 1 on any failure. Plus `--version`, `--help`, unknown-flag
  handling, and **lazy server startup** (importing `server` no longer validates;
  `_ensure_ready()` materializes config+catalog on first use, never caching a
  failed init).

`main` is level with `origin/main` at **`3abc4d2`**; tags **`v0.2.0`** and
**`v0.3.0`** pushed. Fast suite **103 passed**, integration render green.
`dist/` built for 0.3.0 and `twine`-clean (gitignored).

## 📌 Where we stopped

Finished, committed, pushed, and tagged v0.3.0 (setup doctor). Ran the full
suite (103 fast + 1 integration) and eyeballed the live CLI (green checklist,
red checklist, `--version`, `--help`, unknown-flag). No work in flight. The only
deferred thing is the actual **PyPI upload**, which Grayson put on hold in favor
of GitHub-clone distribution (the built `dist/` is ready if that reverses).

## ⭐ The flat-normal fix (the session's key discovery)

`normal_map` is a compound node: `input → buffer(2^param0) → switch(param4) →
edge_detect(param1)`. Default **`param4=1`** edge-detects a pre-rendered BUFFER of
the input, which comes back FLAT for a directly-fed analytic generator (voronoi,
weave, perlin-through-colorize) — the cause of every flat normal. Set **`param4=0`**
to edge-detect the raw input → real relief; `param1` tunes strength (0.2-0.4
subtle). Cloned working chains (dry_earth/bricks/beehive) already worked because
their input reaches normal_map via a buffered blend. Full notes in
`docs/AUTHORING.md`; it's a general lever (granite/aluminum can get real normals too).

## ▶️ Next concrete step

Nothing is required — Phase 3 is 15/15, packaging + setup doctor are done and
pushed. Pick from the menu below, or start a new thread of work entirely.

## 🧭 Next-up options (pick any; none are blocking)

**A. Extend authoring cases.** Grow the proven recipe library beyond the frozen
15 (new material categories: fabrics, organics, sci-fi panels, terrain).
Meatiest option, plays directly to the tool's core strength, produces visible
textures.

**B. Front-door polish.** A prompt-to-render quickstart and a short demo GIF
(assistant authoring a material end to end) for the README top. Lands the repo
well for GitHub visitors now that GitHub-clone is the distribution route.

**C. Phase 5 — live control.** Drive Material Maker over its in-app socket for a
watchable, interactive build instead of batch render. Biggest swing, most
uncertain.

**D. PyPI publish (ON HOLD).** The v0.3.0 `dist/` is built and `twine`-clean;
Grayson chose GitHub-clone distribution instead. Revive only if that reverses:
needs a PyPI account + token, then
`python -m twine upload dist\mm_mcp-0.3.0*` (username `__token__`).

**E. Cross-platform test (still open).** The package declares 3.10+ but is only
Windows-verified; `_console.exe` fallback on macOS/Linux is untested. No
Mac/Linux machine available. Marked honestly (Windows OS classifier + README
note) rather than claimed.

## ❓ Open questions

- PyPI publish, or stay GitHub-clone only? (Currently leaning GitHub-only;
  packaging is done either way.)
- Keep authoring 2 variants/case, or drop to 1 for speed? (Scoring has only ever
  needed variant 1.)
- Worth building a Dockerfile / cross-platform CI, or is Windows-only fine for
  the alpha audience?

## 🗂️ Changed this session (v0.2.0 packaging + v0.3.0 doctor)

- Branch: `main` throughout. Commits `3ab2859`, `23bef31`, `3abc4d2`, all pushed.
  Tags `v0.2.0` and `v0.3.0` pushed.
- **`config.py` installed-case fix (why):** `_PROJECT_ROOT` resolved from
  `__file__` up 3 levels, which points into site-packages once `pip install`ed —
  so the `.env` lookup and `MM_OUTPUT_DIR` default were both wrong for a real
  install. Now `.env` is read from cwd (or `MM_DOTENV`), `MM_OUTPUT_DIR` defaults
  to `./output`, and the personal path defaults are emptied so a stranger gets
  the actionable "set MM_PROJECT_PATH" message. Verified via a clean-venv install
  from outside the repo.
- **`pyproject.toml`:** `requires-python` → `>=3.10` (grep found no 3.13-only
  syntax, only `X | None` unions); classifiers + keywords; Windows-only OS
  classifier (only platform verified); Repository/Issues URLs; a `release` extra
  (build, twine). `MANIFEST.in` prunes `tests/` from the sdist (tests import
  `quality/author.py`, which isn't shipped).
- **Setup doctor (`doctor.py`, new):** `check_setup(cfg)` runs every check and
  returns them as data (never raising, unlike `require_valid` which stops at the
  first). `mm-mcp --check` prints the checklist and exits 1 on any failure.
- **`server.py` lazy startup:** import no longer validates/builds; `_ensure_ready()`
  memoizes only on success; `_reset()` clears it. `main(argv)` returns an int exit
  code and handles `--version`/`--help`/unknown-flag before touching config.
- **README:** clone-first install (PyPI noted as packaged-but-unpublished), a
  "Check your setup" section, Python-3.10/Windows-verified notes.
- **Tests:** `tests/test_doctor.py` (11 tests). Fast suite 92 → 103.
- **Version:** 0.1.0 → 0.2.0 (packaging) → 0.3.0 (doctor).

## ⚠️ Heads-up for the next agent

- **Run tests with `.venv\Scripts\python.exe`** (or activate the venv). The
  package is `pip install -e .`, so `import mm_mcp` works from anywhere.
  Fast suite: `pytest -q -m "not integration"` (103 passed); `pytest -q` adds the
  Godot-launching integration render.
- **Server startup is lazy now.** Importing `mm_mcp.server` does NOT validate
  config or build the catalog; `_ensure_ready()` does that on first tool use (or
  at `mcp.run()`). If you write a test that calls a tool under bad config, call
  `server._reset()` in setup AND teardown so you don't cache state across tests.
- **`mm-mcp --check`** is the setup doctor (green/red preflight); `--version`,
  `--help` also work. Build/release tooling lives in the `release` extra
  (`pip install -e .[release]` → build, twine). `dist/` is gitignored.
- **Pillow is installed in `.venv` but deliberately NOT in `pyproject.toml`** — it
  was a one-time tool to downscale the `examples/images/` previews. Don't add it
  as a dependency.
- `quality/runs/` and `quality/authored/` are gitignored (heavy PNGs / regen'd);
  scorecards + test_set are the committed evidence, `author.py` reproduces renders.
- All Phase 1-2 render gotchas still hold (see CLAUDE.md): `--export-material`,
  `_console.exe`, no `--headless`, `steam_appid.txt`.
- `normal_map` is a compound node; real params `param0` (size), `param1`
  (strength), `param2`, `param4` — NOT `amount`/`size`.
- Voronoi **output port 2** = `rand3` random-per-cell (the fleck/speckle source);
  ports 0/1 are distance fields. Reusable for any granular material.

---

## 🕓 Session log

### 2026-08-26 (evening, cont. 3) — v0.2.0 PyPI packaging + v0.3.0 setup doctor
- **Phase 4 packaging (v0.2.0).** Made the package actually installable: fixed
  `config.py` (`_PROJECT_ROOT` resolved into site-packages once pip-installed —
  the `.env` lookup and `MM_OUTPUT_DIR` default were both wrong for a real
  install). `.env` now cwd/`MM_DOTENV`-based, output defaults to `./output`,
  personal defaults emptied. Lowered `requires-python` to 3.10, added
  classifiers/keywords + Windows-only OS classifier, `MANIFEST.in` prunes tests
  from the sdist. Built wheel + sdist, `twine check` clean, and **verified by
  installing the wheel into a clean venv outside the repo** (imports as the
  version, `mm-mcp` on PATH, actionable error with no config, 392-node catalog
  with real config). Commits `3ab2859` + `23bef31`, tag `v0.2.0`.
- **Setup doctor (v0.3.0).** Built `mm-mcp --check`: `doctor.py` runs every
  prerequisite check and returns results as data (never raising), so a cloner
  gets one green/red checklist instead of a startup exception. Added `--version`,
  `--help`, unknown-flag handling, and refactored `server.py` to lazy startup so
  those work when config is broken. Addressed an advisor review (failed init not
  cached, `steam_appid.txt` contents checked, output-dir check has no side
  effect, unknown flags fail legibly). 11 new tests, fast suite 92 → 103,
  integration green. Commit `3abc4d2`, tag `v0.3.0`.
- **Distribution decision:** Grayson put PyPI on hold; **GitHub-clone is the
  route.** The v0.3.0 `dist/` is built and ready if that reverses. README
  reworked clone-first.

### 2026-08-26 (evening, cont. 2) — Robustness: validator noise + author-helper tests
- Softened the validator's numeric-out-of-range warning wording: it now says
  a slider's `min`/`max` isn't shader-enforced and often still renders fine,
  instead of reading like a real problem. Kept enum out-of-range wording as a
  genuine warning (an invalid index actually is a problem, unlike a slider).
  Verified against the real granite graph's `scale_x=44`/`scale_y=44`.
- Added `tests/test_author_helpers.py` covering `author.py`'s `rewire`,
  `drop_conn`, `add_node`, and `node` helpers (10 tests) plus 2 new
  `test_validator.py` cases for the two new message flavors. Fast suite
  80 → 92 passed.

### 2026-08-26 (evening, cont.) — Social preview uploaded live
- Uploaded `docs/social-preview.png` as the repo's social preview via the
  browser (repo Settings → General → Social preview; GitHub has no API for
  this field). Confirmed it persists after a page reload — the last open item
  from the previous handoff's option A is closed.

### 2026-08-26 (evening) — Normal-map polish: granite + aluminum get real relief
- Applied the `param4=0` normal fix (option B from the last handoff) to `s02`
  gray granite and `m02` brushed aluminum, both already HITs but flat-normal.
  Granite: `voronoi_1 -> warp_0 -> normal_map_0` was a directly-fed analytic
  chain (same shape as the denim blocker). Aluminum: `blend_0 -> normal_map_0`
  *looked* buffered but wasn't, once `blend_0` had been straightened to take
  `perlin_2` directly (that straightening was iter1's own fix for the streaks,
  and it happened to also make the chain analytic-direct) — a new nuance beyond
  the original denim writeup, now documented in `docs/AUTHORING.md`.
- Re-rendered both, confirmed via the actual normal PNGs: granite shows subtle
  mottled micro-relief, aluminum shows clean parallel vertical brush streaks
  (previously flat/uniform blue for both). Albedo unchanged, so `examples/images/`
  preview thumbnails didn't need regenerating.
- Rendering a case resets its `_result.json` verdict to unscored — recovered the
  original HIT verdicts + judge notes from the last committed scorecard and
  re-applied them (with an appended note on the normal upgrade) before
  rebuilding the scorecard, so Phase 3 stays 15/15 with the original audit trail
  intact rather than silently wiped.
- Copied the fixed `.ptex` graphs into the public `examples/` showcase (the v2
  variant of each was already the one on display). Fast suite still 80/80.

### 2026-08-26 (late pm) — 15/15 via the flat-normal fix + gallery refresh
- Went for 15/15. Landed `combo01` (paint-over-rust peel composite: flat paint
  coat blended over rusted_metal through an irregular perlin peel mask) → 14/15.
- Cracked the flat-normal blocker: `normal_map` is a compound
  `input→buffer→switch(param4)→edge_detect`; default `param4=1` buffers the input
  and returns flat for analytic generators. **`param4=0`** fixes it. That gave
  `f01` denim a real diagonal-twill normal (diagonal_weave grafted into
  crocodile_skin) → **15/15 (100%)**. Documented in `docs/AUTHORING.md`.
- Refreshed the `examples/` gallery to 8 materials (added denim, ceramic hex,
  rusted painted steel) and re-cut `docs/social-preview.png` as a 4x2 grid.
  Updated README gallery + status to 15/15. Commits through `9273ec5`.

### 2026-08-26 (pm) — Close Phase 3 gate + ship v0.1.0 public release
- Audited the flagged `s02` granite: called it a real MISS (foggy albedo, not the
  flat normal). Fixed it with a fine voronoi **port-2 per-cell-random** fleck
  source → genuine HIT. Then fixed `m02` brushed aluminum by cloning `wood`'s
  directional-streak-with-working-normal chain and straightening it. Scorecard
  went 10/15 → **11/15 (73%)**, gate met and recorded in STATUS.md.
- Packaging pass: MIT LICENSE, pip-installable `pyproject` with `mm-mcp` entry
  point, public README rewrite (gallery + tool table + gotchas), `examples/`
  showcase (6 materials), fixed the `--export` typo.
- Added a prominent **super-alpha / artist-built** disclaimer across README,
  STATUS, examples README (Grayson's explicit ask: make clear it's very early and
  he's an artist/animator, not a software engineer).
- Merged `feat/phase3` → `main`, pushed, **flipped the repo public** (with
  description + topics), cut **`v0.1.0`** release.
- Verified: editable install works, `mm_mcp` imports anywhere, `mm-mcp` on PATH,
  80 fast tests pass. Recorded a Next-up options menu (A-E) above.

### 2026-08-26 — Scope + execute Phase 3 (authoring quality) to 10/15
- Planned Phase 3 as three gated sub-phases (3A test set + harness, 3B baseline,
  3C tuning); locked the gate at ≥70% any-variant with multi-variant included.
- 3A: authored + froze the 15-case test set (after review), built `run_case.py`
  harness + scorecard machinery. 3B: baseline = 3/15 (nearest-example-as-is) with
  a miss taxonomy. 3C iter1: 3→10/15 via the recolor lever (leather, barn wood,
  copper, concrete), a grain-ramp fix (oak planks), and the clone-a-sharp-edged-
  example insight (moss). Solved the flat-normal blocker; added a render retry.
- Ruled out: hand-assembling `normal_map` (renders flat) and cloning smooth
  examples like `rock` for relief (also flat) — sharp-edged sources are required.

### 2026-08-25 — Set up Material Maker + build the MCP (Phases 1-2)
- Cloned RodZill4/material-maker into `z-Git\` as a reference, got it running (found the
  Steam `steam_appid.txt` self-relaunch gotcha), and confirmed headless `--export-material`
  renders PBR maps.
- Brainstormed and approved the MCP design (thin batch-render first, me-first audience),
  scaffolded `Tool-MaterialMaker-MCP` as a new project, pushed a private GitHub repo.
- Wrote the Phase 1-2 implementation plan, then executed it subagent-driven: 9 TDD tasks,
  each reviewed for spec + quality; fix loops on Tasks 3/5/7/9; whole-branch review (Opus)
  + one fix wave. All reviews clean. Merged to `main`, pushed, branch deleted.
