# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-26 (night) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**Authoring cookbook grown across all 4 planned categories: fabrics, organics,
sci-fi panels, terrain.** 16 new materials, 20/24 clean HIT + 4 documented
partials/fixed-after-one-try, all informal (no scorecard gate, separate from
the frozen 15-case Phase 3 set). 4 commits, `main` pushed through `afb3290`.
Packaging (v0.2.0) and the setup doctor (v0.3.0) from the prior session are
untouched and still current — see the session log below for that history.

Per-category results:
- **Fabrics** (`a714faf`): canvas/burlap HIT, silk/satin HIT, velvet HIT
  (2 tries — voronoi speckle read as faceted crystal, `perlin` fixed it),
  wool/chunky-knit PARTIAL (no true loop-knit generator in this catalog).
- **Organics** (`bec23b5`): bark, snake scales, coral, lichen-crusted rock —
  4/4 HIT on the first pass, each reused an already-proven lever.
- **Sci-fi panels** (`61c83bd`): hull plating, hazard stripe panel, vent
  grille — 3/4 HIT. Circuit board is a documented PARTIAL: chip blocks bleed
  trace-stripe color through them for an unresolved reason after 3 tries.
- **Terrain** (`afb3290`): sand dunes, fresh snow, gravel HIT immediately;
  grass field HIT after one empirical fix (mask threshold direction was
  backwards from what analogy with `o06`/`m01` predicted).

New pattern for future categories: `quality/cookbook_<category>.py` (graph
builders, reusing `author.py`'s helpers) + `quality/render_cookbook.py
<label>` (validate+render, no `test_set.json` dependency) +
`quality/_make_previews.py <label>` (downscaled preview thumbnails into
`docs/images/cookbook-<label>/`). None of this touches the frozen 15 or its
scorecard machinery. `quality/README.md` documents the convention.

## 📌 Where we stopped

All 4 categories finished, documented in `docs/AUTHORING.md`, and committed.
Working tree is clean (only the pre-existing gitignored `dist/` untracked).
No work in flight — this is a clean stopping point, not a partial one.

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

Nothing is required — this was open-ended cookbook growth, not a gated phase.
Pick from the menu below, or start a new thread of work entirely.

## 🧭 Next-up options (pick any; none are blocking)

**A. More cookbook categories.** The 4 originally planned are done; could keep
going (e.g. liquids/glass, food, more sci-fi variety) using the same
`cookbook_<category>.py` pattern. Cheap to extend, same recipe-library payoff.

**B. Revisit the 2 partials.** Wool/chunky-knit (no loop-knit generator; could
try a hand-built bump approach instead of a weave-family node) and circuit
board (chip-bleed bug never root-caused). Neither is blocking, both are
loose threads if perfection matters more than coverage.

**C. Front-door polish.** A prompt-to-render quickstart and a short demo GIF
(assistant authoring a material end to end) for the README top. Now has 16
more example materials to potentially draw from for a refreshed gallery.

**D. Phase 5 — live control.** Drive Material Maker over its in-app socket for
a watchable, interactive build instead of batch render. Biggest swing, most
uncertain, unrelated to the cookbook work.

**E. PyPI publish (ON HOLD).** The v0.3.0 `dist/` is still built and
`twine`-clean from the prior session; GitHub-clone remains the chosen
distribution route. Revive only if that reverses.

**F. Cross-platform test (still open).** The package declares 3.10+ but is
only Windows-verified; `_console.exe` fallback on macOS/Linux is untested. No
Mac/Linux machine available.

## ❓ Open questions

- Worth root-causing the circuit-board mask-opacity bug, or is the documented
  partial good enough? (No lead on the cause after 3 iterations.)
- Is there a better loop-knit approximation for wool than coarse `weave`, or
  is "chunky basket-weave" an acceptable stand-in permanently?
- PyPI publish, or stay GitHub-clone only? (Carried over from the prior
  session, still unresolved — currently leaning GitHub-only.)
- Worth building a Dockerfile / cross-platform CI, or is Windows-only fine for
  the alpha audience? (Also carried over, still open.)

## 🗂️ Changed this session (cookbook growth: fabrics, organics, sci-fi, terrain)

- Branch: `main` throughout. Commits `a714faf`, `bec23b5`, `61c83bd`,
  `afb3290`, all local (not pushed — not asked to this session).
- **New pattern, not touching frozen infra:** `quality/cookbook_<category>.py`
  (graph-surgery builders importing `author.py`'s helpers), `quality/
  render_cookbook.py <label>` (validate+render without the `test_set.json`
  lookup `run_case.py` requires), `quality/_make_previews.py <label>`
  (Pillow downscale into `docs/images/cookbook-<label>/`, generalized this
  session from a fabrics-only hardcode). `quality/README.md` documents the
  convention for future categories.
- **New authoring levers found and written up in `docs/AUTHORING.md`:**
  `weave`/`weave2`/`diagonal_weave` for fabric grids (no true loop-knit
  generator exists in this catalog); `perlin`/`fbm` over `voronoi` for
  soft/continuous materials (voronoi's cell edges stay hard no matter how
  narrow the color gradient); the `pattern` node family (x/y wave generators
  + a mix mode) for sci-fi geometric panels, including the specific
  `pattern → colorize → transform` wiring order metal_pattern_2 requires;
  `rusted_metal`'s two-layer masked-blend structure reused 3 more times
  (lichen, grass) beyond its original copper/rust use.
- **Two things that didn't fully resolve, documented honestly rather than
  hidden:** `pattern`'s `mix=Xor` produced zero visible output at every
  threshold tried (silently dead, not just wrong); circuit board's chip
  shapes still bleed trace-stripe color through them for a reason not
  identified after 3 iterations. Mask-threshold DIRECTION (raise vs lower to
  favor a layer) turned out unpredictable by analogy across cases even on
  the same donor graph — grass field needed an empirical flip to fix.

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
- **Cookbook growth pattern** (`quality/cookbook_<category>.py` +
  `render_cookbook.py` + `_make_previews.py`) is separate from the frozen
  Phase 3 test set on purpose — copy it for the next category rather than
  touching `test_set.json`/`run_case.py`/`author.py`'s `BUILDERS` dict. See
  `quality/README.md` for the short version and `docs/AUTHORING.md` for every
  recipe + the levers that didn't pan out.
- `quality/cookbook/` and `docs/images/cookbook-*/` are the render output and
  the tracked preview thumbnails respectively (the former gitignored, the
  latter committed as documentation assets — see `.gitignore`'s comment).

---

## 🕓 Session log

### 2026-08-26 (night) — Cookbook growth: fabrics, organics, sci-fi, terrain
- Extended the proven authoring recipe library beyond the frozen 15-case
  Phase 3 test set into 4 new material categories, per Grayson's request
  after `pickup` surfaced it as the recommended next-up option. Informal:
  1 variant per material, self-judged by eye, no scorecard/gate.
- Built a new convention to do this without touching frozen infra:
  `quality/cookbook_<category>.py` (graph builders reusing `author.py`'s
  helpers) + `quality/render_cookbook.py <label>` (validate+render, skips
  `test_set.json`) + `quality/_make_previews.py <label>` (Pillow downscale
  into `docs/images/cookbook-<label>/`, generalized from a fabrics-only
  hardcode partway through). `quality/README.md` documents it.
- **Fabrics** (`a714faf`): canvas/burlap and silk/satin were straightforward
  weave-graft + `param4=0` hits. Velvet took 2 tries (voronoi speckle at max
  scale read as faceted crystal, not soft fiber; a `fast_blur_shader` graft
  hit a Godot "invalid shader" rgb/rgba port mismatch; `perlin` instead of
  `voronoi` solved it outright — a general lever for soft/continuous
  materials). Wool/chunky-knit is a documented PARTIAL: no true loop-knit
  generator exists in this catalog, `weave2`'s `stitch` param gives a crisp
  herringbone instead of loop softness; coarse `weave` is the closest
  stand-in.
- **Organics** (`bec23b5`): bark, snake scales, coral, lichen-crusted rock —
  4/4 HIT on the first pass. Each reused an already-proven lever (wood
  cloned unmodified for bark's knots, crocodile_skin's own default pattern
  for scales, `fbm`'s Cellular noise instead of voronoi for coral's porous
  cells, rusted_metal's masked two-layer blend for lichen-on-stone).
- **Sci-fi panels** (`61c83bd`): a category with zero frozen-set precedent.
  Introduced the `pattern` node family (x/y wave generators + a mix mode).
  Hull plating, hazard stripe panel, and a square-hole vent grille are
  clean HITs. Circuit board is a documented PARTIAL: `pattern`'s `mix=Xor`
  produced literally no visible output at any threshold (checked via the
  normal map), and after swapping to the proven voronoi-speckle lever for
  chip placement, the underlying trace stripes still faintly bleed through
  the chip shapes for a reason not identified after 3 iterations. Also
  ruled out an emission-based "glowing panel" idea before building
  anything — the render pipeline's export target doesn't produce an
  emission map at all, so it would've been invisible in the real output.
- **Terrain** (`afb3290`): sand dunes, fresh snow, and gravel were clean
  HITs reusing proven levers (wood kept unmodified for organic ripples,
  rock kept smooth for snow's near-flat target, the voronoi-speckle lever
  at pebble scale). Grass field needed one real fix: a masked-blend
  threshold moved by analogy with how `o06` lichen/`m01` copper "widen"
  their patch layer rendered almost the opposite of intended (near-total
  soil, tiny green flecks — confirmed via an almost-flat normal map).
  Flipping the threshold direction empirically (not by re-deriving the
  blend formula) fixed it on the first re-render. **General lesson
  recorded:** mask-threshold direction isn't reliably predictable by
  analogy across cases, even from the same donor graph — render and look.
- All 4 commits are on `main`, not pushed (push wasn't requested this
  session). 16 new materials total: 12 clean HITs on the first or second
  try, 2 that needed a documented empirical fix (velvet, grass field), 2
  honest partials (wool, circuit board).

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
