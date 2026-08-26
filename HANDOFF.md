# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-26 (evening) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**Public v0.1.0 release, perfect Phase 3 score, normal-map polish pass, social
preview live.** The repo is **public** on GitHub with an MIT license, a public
README (8-material gallery + super-alpha disclaimer), a pip-installable package
(`mm-mcp` entry point), an `examples/` showcase (8 materials), a live social
preview card (uploaded via repo Settings → Social preview, confirmed persisting
after reload), and a tagged **`v0.1.0`** release. Phases 0-3 all done and
verified; **Phase 3 authoring quality is 15/15 (100%)**. The flat-normal blocker
that dogged several cases is **SOLVED** (`normal_map` `param4=0`), applied to
every case that had it, including the two remaining flat-normal HITs (`s02`
granite, `m02` aluminum) this session. Working tree is clean, `main` is level
with `origin/main` at commit `e3461c2`.

## 📌 Where we stopped

Applied the `param4=0` normal-map upgrade to granite and aluminum (option B from
the previous handoff), re-rendered and eyeballed both, restored their HIT
verdicts in the scorecard (rendering resets `_result.json` verdicts, so these
were manually re-patched with the original judge notes plus an appended
normal-upgrade note), copied the fixed graphs into the public `examples/`
showcase, and updated `docs/AUTHORING.md` + `examples/README.md`. Fast test
suite 80/80. Committed and pushed as `e3461c2`. Then uploaded
`docs/social-preview.png` as the repo's social preview via the browser (GitHub
has no API for this) and confirmed it persists after a page reload. No
unfinished work in flight.

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

Nothing is required — v0.1.0 is public, Phase 3 is 15/15, and the social preview
is live. Pick from the menu below, or start a new thread of work entirely.

## 🧭 Next-up options (pick any; none are blocking)

**A. DONE this session.** Uploaded `docs/social-preview.png` as the repo social
preview (manual, GitHub has no API for it) and confirmed it persists. Still
open if wanted: eyeball the live README render at
https://github.com/graysonchalmers/Tool-MaterialMaker-MCP, or consider a short
GIF of an assistant authoring a material end to end (prompt → graph → render)
for the README top.

**B. DONE this session.** Applied the `param4=0` normal fix to the granite and
aluminum showcase pieces — both now have real micro-relief instead of flat
normals. Quality was already DONE at 15/15; the frozen test set is maxed, so any
further work would be new cases or higher fidelity, not the gate.

**C. Robustness / cross-platform — partially DONE this session.**
- ✅ Validator noise: numeric slider params outside their declared `[min, max]`
  (voronoi/perlin `scale_*` at fleck/streak scales) now read as an advisory
  ("not shader-clamped, often fine; verify visually") instead of an alarming
  "outside [1, 32]". Enum params out of range still read as a real problem
  (an out-of-range enum index is genuinely invalid, unlike a slider). See
  `src/mm_mcp/validator.py`.
- ✅ Added `tests/test_author_helpers.py`: unit tests for `author.py`'s
  `rewire`/`drop_conn`/`add_node`/`node` graph-surgery helpers (repoint, append,
  no-op-when-missing, only-touch-matching-port, composition). These back every
  Phase 3 recipe, so a regression here would silently corrupt authored
  materials without failing anything else.
- ⬜ Still open: test on macOS/Linux (path handling, `_console.exe` is
  Windows-only — the code already falls back to the plain binary, but it's
  untested off-Windows). No Mac/Linux machine available this session.

**D. Phase 4/5 from the original plan (bigger lifts)**
- **Phase 4 (public packaging, deeper):** publish to PyPI so `pip install mm-mcp`
  works without a clone; a real quickstart; maybe a Dockerfile.
- **Phase 5 (live control):** drive Material Maker over its in-app socket for a
  watchable, interactive build instead of batch render.

**E. The flat-normal question — RESOLVED and applied everywhere it mattered.**
Root cause (`normal_map` `param4=1` buffers a directly-fed analytic input) found
via denim, then applied to granite and aluminum this session. No known case in
the 15-case set still has an avoidable flat normal.

## ❓ Open questions

- Do you want a PyPI publish (Phase 4), or is clone-and-`pip install -e .` fine
  for the alpha audience?
- Keep authoring 2 variants/case, or drop to 1 for speed? (Scoring has only ever
  needed variant 1.)
- Is the flat-normal limitation acceptable long-term, or worth a dedicated dig
  (option E)?

## 🗂️ Changed this session

- Branch: `feat/phase3` → merged to `main` (`ed6986b`), pushed. Tag `v0.1.0` at
  `4eaaca9`. Repo flipped **public**.
- **Phase 3 gate closed 10/15 → 11/15**: rewrote two `author.py` builders.
  - `s02` granite: root-caused the fog (cloned `rock` but only shrank the perlin,
    leaving the albedo voronoi at scale 4). Fix feeds the albedo colorize from
    **voronoi output port 2** (`rand3` = flat random value per cell) at a fine
    scale → crisp multi-tone mineral flecks. Added a `rewire` helper.
  - `m02` brushed aluminum: cloned `wood` (directional-streak generator with a
    **working** normal chain), straightened the grain (fed `blend_0` from the
    un-warped `perlin_2`), neutralized to gray, forced metallic (`drop_conn`
    helper drops the grain-driven metallic map so the scalar `metallic=1`
    applies). Streaks read in albedo + roughness.
- **Packaging:** added MIT `LICENSE`; made `pyproject.toml` pip-installable
  (src layout, build-system) with an `mm-mcp` console entry point (`server.main`);
  rewrote `README.md` for a public audience (gallery, generic install/config, MCP
  client snippet, tool table, gotchas, attribution); fixed the stale `--export`
  ref; added `examples/` (6 `.ptex` + 512px previews + table); refreshed
  `__init__` (v0.1.0).
- **Disclaimer:** prominent super-alpha / artist-built warning added to README,
  STATUS.md, and examples/README ("verified" = "worked on the one machine").
- Recorded s02/m02 verdicts in the iter1 `_result.json`s and rebuilt the
  scorecard; STATUS.md Phase 3 rows → ✅ verified.

## ⚠️ Heads-up for the next agent

- **Run tests with `.venv\Scripts\python.exe`** (or activate the venv). The
  package is now `pip install -e .`, so `import mm_mcp` works from anywhere.
  Fast suite: `pytest -q -m "not integration"` (80 passed).
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
