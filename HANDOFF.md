# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-27 (early AM) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**Phase 5 build step 1 (`overlay.py`) shipped: built, reviewed, fixed, merged,
pushed.** Continuing straight from this session's own de-risking spike (below),
Grayson said "continue" and the session ran the full `superpowers` pipeline
end to end: `writing-plans` → an isolated git worktree →
`subagent-driven-development` (5 tasks, fresh implementer + fresh reviewer per
task, haiku for mechanical tasks, sonnet for integration/review) →
`requesting-code-review`-style final whole-branch review on opus →
`finishing-a-development-branch` (merged locally, pushed).

`ensure_overlay(mm_project_path, addon_path, overlay_dir) -> overlay_path` now
exists in `src/mm_mcp/overlay.py`, 134 tests (up from 109), all green. It's
pure filesystem work (no Godot import, no Config dependency): builds/refreshes
a disposable copy of a Material Maker checkout with the future live-control
addon layered in and registered as a Godot `[autoload]` entry, using a
content-hash-of-addon + checkout-path marker to decide no-op vs. rebuild.

**Five real bugs found and fixed by the review loop, none of them
implementer error** — all were defects in this session's own plan-authored
reference code, each ruled on and fixed the same task, then re-reviewed clean
before moving on:
1. `_append_autoload` blindly appended to end-of-file instead of into the
   `[autoload]` section — verified against the real
   `z-Git\material-maker\project.godot` (10 sections follow `[autoload]`
   there); an end-of-file append would have attached the line to `[steam]`,
   silently defeating the whole addon-loading mechanism. **Critical.**
2. `_read_marker` didn't guard against valid-but-non-dict JSON (a garbled
   marker), crashing instead of degrading to "stale."
3. Task 4's integration test proved the autoload line's *presence*, not its
   *position* — a regression of bug #1 wouldn't have been caught end-to-end.
4. (final review) `ensure_overlay` ran destructive `rmtree`/`copytree`
   *before* validating any input — reviewer reproduced `overlay_dir ==
   mm_project_path` actually deleting a real test checkout. Fixed with an
   input-validation guard at the top of the function (addon_path must be a
   dir, mm_project_path must contain `project.godot`, overlay_dir can't
   equal or contain either input, case-insensitive).
5. (final review) `STATUS.md`'s gate ledger was never updated for this work,
   violating this project's own CLAUDE.md rule. Fixed.

Full detail — every ruling, every finding, every fix-round diff — lived in
the SDD ledger inside the (now-deleted) worktree; the git history on `main`
is the durable record now (9 commits, `53527bf`..`67a028a`, landed via a
clean fast-forward merge, individually visible in `git log`).

**Phase 5 both feasibility risks retired via spike, earlier this session.**
After the seam fix (below), Grayson picked "start Phase 5" (the live-control
addon). Started it the spike-first way the spec mandates and closed BOTH
"known risks" the spec flagged:
- **Risk #1 (autoload TCP socket in a running, non-editor Godot project):
  PROVEN.** Throwaway standalone project, one `[autoload]` line opened a
  `TCPServer`, Python connected and exchanged JSON. Confirmed again inside the
  real MM overlay.
- **Risk #2 (in-process graph-mutation surface): RETIRED.** MM exposes a
  GUI-grade API mirroring the batch `.ptex` shape
  (`get_current_graph_edit()` → `create_nodes`/`do_connect_node`/
  `set_node_parameters`/`generator.serialize()`). The read path
  (`get_graph` via `serialize()`) was proven end-to-end: a real MM overlay
  launched, addon reached the active tab, returned the default new-material
  graph, clean socket quit, exit 0.

Full evidence + the implementation constraints discovered (await-based
`create_nodes`, lazy `main_window` resolution, overlay must carry
`steam_appid.txt`, don't PIPE Godot stdout) are recorded in the spec's new
"Feasibility verified" section:
`docs/superpowers/specs/2026-08-26-live-control-addon-design.md`. Spike code
was throwaway in scratchpad, not committed.

**Horizon seam in `render_preview` fixed and pushed** (earlier in this
session). Picked up option B from the prior handoff (the ground-plane horizon
seam) and closed it. The finite 60×60 plane's far edge sat ~30 units out, where fog only
reaches ~88%, leaving the ground's hard edge faintly visible against `BG_COLOR`
as a seam. Fixed by extending the plane to 400×400 so its edge sits ~200 units
out where fog is effectively 100% (ground fully dissolves into the background
before its edge), while scaling the ground UV repeat with plane size so the
near-camera tile density is unchanged from the tuned look. Verified with real
before/after renders. Committed as `9e52340` and **pushed**; `main` and
`origin/main` are in sync.

Also corrected a stale note: the prior handoff claimed 3 unpushed commits, but
`origin/main` was already at `0675ca1` before this session — that work
(`render_preview`, North Star, scene overhaul) was already on GitHub. Nothing
is unpushed now.

Prior context (still true):
**`render_preview` MCP tool built, tuned, and landed.** Grayson asked (via
`pickup`) whether anywhere in the pipeline could show a material applied to
a 3D object under real lighting, not just flat map swatches. Answer was no,
so this session built it: a new eighth MCP tool that takes `render_graph`'s
albedo/normal/orm output paths and composites them onto a sphere, a cube
(turned 45°), and a cutaway ball (a CSG sphere with a wedge cut out,
revealing an inner core), all resting on a tiled ground plane, under raking
key + rim lighting with shadows, a touch of depth of field, exponential fog,
and 8x MSAA + FXAA. Rendered via a small bundled Godot project
(`src/mm_mcp/preview_project/`), fully separate from the `z-Git\material-maker`
checkout, no fork.

Built via `superpowers:brainstorming` (spike to prove feasibility, then a
bounded design once Grayson confirmed he wanted it as a real MCP tool) and
`superpowers:test-driven-development` for the implementation. Then a long
visual-iteration round with Grayson, rendering, showing him the actual PNG,
adjusting, repeat, rather than guessing blind: ground plane + tiling knob,
the cutaway ball (two full rotation-angle sweeps to find 240° on the Y-axis
as the one orientation that keeps the cut face-on to the camera), fixing a
white untextured cut face (missing material on the CSG cutter) and a
noise-like inner core (wrong UV tile scale for its radius), DOF via
`CameraAttributesPractical` (not direct `Camera3D` properties, first attempt
errored), camera reframing, and finally dialing fog/DOF strength down.

Also added `docs/NORTH_STAR.md`: Grayson's framing that this project's real
point is lowering the barrier to learning Material Maker (he's learning it
himself by watching/editing what gets authored for him), not one-shot
texture generation. Linked from README and CLAUDE.md.

## 📌 Where we stopped

Clean stop. `main` and `origin/main` both at `67a028a`, in sync (`0 0`).
Working tree clean, 134/134 fast tests pass on the pushed tip. No worktree,
no branch, no lingering Godot processes.

## ▶️ Next concrete step

**Phase 5 build step 2: the real addon skeleton.** Step 1 (overlay builder)
is done. Step 2 per the spec's sub-plan: socket server + `ping`/`get_graph`
only, committed for real as `addons/mm_live/live_server.gd` inside this repo
(not scratchpad this time — `overlay.py`'s `ensure_overlay` now exists to
copy it into a real overlay on demand). Gate: Python connects, launches
Material Maker via the overlay, gets a real graph back for a bundled example.
The GDScript from tonight's earlier 1b spike (scratchpad, deleted) is a
working reference — same shape, same constraints (await-based `create_nodes`
comes in step 3, not step 2; lazy `main_window` resolution already proven).
Use `writing-plans` again for this step, same pattern as step 1.

Alternatives, all carried over unchanged:
- **A. More cookbook categories** (extend the authoring recipe library).
- **B. The two honest partials** (wool loop-knit, circuit-board mask-bleed).
- **D. PyPI publish** (on hold; GitHub-clone is the current route).
- **E. Document `render_preview`** in `docs/AUTHORING.md` / README, or leave it
  as just an MCP tool.
- **F. Two parked polish items from the final overlay-builder review** (both
  cosmetic, see Heads-up): `STATUS.md` prose wording, and a pre-existing
  "seven tools" vs. "eight tools" count mismatch between `__init__.py` and
  `STATUS.md` unrelated to this branch.

## ❓ Open questions

- Should `render_preview` get documented in `docs/AUTHORING.md` / README, or
  is it enough that it exists as an MCP tool? Not yet decided, not done.
- Two parked-not-fixed findings from the overlay-builder's final review
  (deliberately deferred, not forgotten): the staleness marker doesn't detect
  an already-built overlay being damaged from outside (e.g. hand-editing
  `project.godot` in the Godot editor while debugging steps 2-3) — whoever
  builds step 2/3 should reconsider this; `_append_autoload`'s
  `content.find("[autoload]")` matches the first occurrence anywhere in the
  file including inside a comment (verified inert against the real file, so
  low priority).
- Carried over, unchanged: Phase 5 implementation timing (no target date by
  design); circuit-board mask-bleed bug (no lead after 3 tries); wool's
  loop-knit approximation; PyPI vs. GitHub-clone-only (leaning GitHub-only);
  cross-platform (macOS/Linux) verification, still untested, no machine
  available.

## 🗂️ Changed this session (Phase 5 overlay builder + seam fix)

- Branch: `main`. Overlay builder landed as 9 commits (`53527bf`..`67a028a`,
  via a feature branch merged locally then pushed):
  `53527bf` plan doc, `ecabb38`/`82644fa`/`040c5bd` Task 1-2 (+ fix),
  `a7a3b15`/`7e88a10` Task 3 (+ fix), `93858ba`/`ef8f51d` Task 4 (+ fix),
  `e5ebac9` Task 5, `67a028a` final-review fix wave (input validation,
  STATUS.md, UnicodeDecodeError guard, case-insensitive path compare,
  docstrings, marker-contents test).
- Decisions (+ why): every plan-mandated bug got fixed in the same task's
  fix round rather than deferred, since each was load-bearing for later
  tasks (Task 3/4/5 all call `_is_stale`; Task 4/5 all call
  `_append_autoload`) — see "Current state" above for the bug list.
  `overlay_dir` stayed a caller-supplied parameter rather than derived from
  `Config`, keeping the module's only dependencies stdlib (`hashlib`, `json`,
  `os`, `shutil`) — a future `live.py` (step 3) will own choosing where the
  overlay actually lives.

## 🗂️ Changed the prior session (seam fix)

- Branch: `main`. One commit, pushed: `9e52340` — `fix(preview)`: ground plane
  60×60 → 400×400 with density-preserving UV scale, removing the horizon seam.
  Single file: `src/mm_mcp/preview_project/preview.gd`.
- Decision (+ why): "bigger plane" over "real procedural sky" because the sky
  would change the deliberately-dark studio background Grayson tuned; enlarging
  the plane removes the seam while keeping that look exactly.

## 🗂️ Changed the prior session (render_preview)

- Branch: `main`. Three commits (already pushed before this session):
  - `41bd60b` — `render_preview` MCP tool (TDD: `src/mm_mcp/preview.py`,
    bundled `src/mm_mcp/preview_project/` Godot scene, 5 new tests,
    `pyproject.toml` package-data fix verified by an actual wheel build).
  - `8fc8e33` — `docs/NORTH_STAR.md`, linked from README + CLAUDE.md.
  - `aefd7af` — scene overhaul: ground plane, cutaway ball, DOF/fog/AA,
    camera reframing, `tile` UV-scale knob wired through the real Python API
    and MCP tool signature (previously only reachable via a raw Godot
    cmdline arg during manual testing).
- Decisions (+ why): `render_preview` takes already-rendered map paths, not
  a `.ptex` graph, so `render_graph` stays the only place graph-rendering
  logic lives (Grayson's call, to keep the two tools single-purpose). The
  cutaway ball's rotation is locked at 240° on the Y-axis, the only
  orientation across two full angle sweeps that kept the cut face
  camera-facing rather than hidden against the ground or the far side.

## ⚠️ Heads-up for the next agent

- **New module: `src/mm_mcp/overlay.py`.** Public entry point
  `ensure_overlay(mm_project_path, addon_path, overlay_dir) -> overlay_path`
  — builds/refreshes a disposable Material Maker overlay with an addon
  layered in. Pure filesystem, zero Godot/Config dependency, so it's
  unit-testable without launching anything (`tests/test_overlay.py`, 25
  tests). Nothing calls this yet — `live.py` (step 3 of the spec's sub-plan)
  is the next thing that will. Read the module docstring first; it explains
  why `overlay_dir` is caller-supplied and the "a rebuild wipes it wholesale"
  gotcha (don't put a log file inside `overlay_dir` expecting it to survive).
- **`_append_autoload` inserts at the end of the `[autoload]` section
  specifically, not blindly at end-of-file** — this was a real bug found and
  fixed this session (see Current state). If you're ever tempted to
  "simplify" this function back to a plain append, don't; the real Material
  Maker `project.godot` has ~10 sections after `[autoload]`, verified.
- **`ensure_overlay` validates before mutating anything.** It raises
  `ValueError` if `addon_path` isn't a directory, `mm_project_path` has no
  `project.godot`, or `overlay_dir` equals/contains either input path
  (case-insensitive) — this guards against actually deleting the real
  `z-Git\material-maker` checkout if `live.py` ever misconfigures
  `overlay_dir`. Also a bug found and fixed this session, reproduced by the
  reviewer before the fix landed.
- **New MCP tool:** `render_preview(albedo_path, normal_path, orm_path,
  basename="preview", tile=1.0) -> dict`. Call `render_graph` first and feed
  its output paths in. Renders through `src/mm_mcp/preview_project/`, a
  small standalone Godot project bundled in this repo, not the
  `z-Git\material-maker` checkout.
- **Run tests with `.venv\Scripts\python.exe`** (or activate the venv).
  Fast suite: `pytest -q -m "not integration"` (134 passed); `pytest -q`
  adds the Godot-launching integration renders (137 total).
- **Godot property-name traps hit this session** (both caused a script
  error + hung process, had to `taskkill`): depth of field lives on a
  `CameraAttributesPractical` resource assigned to `Camera3D.attributes`,
  not direct `Camera3D` properties; `smooth_faces` exists on `CSGSphere3D`
  but not `CSGBox3D`. If a Godot script error leaves the console binary
  hanging, `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` clears
  it (Bash tool, not PowerShell).
- **Known, honestly-flagged limitations, not bugs:** CSG boolean subtraction
  cuts sharp edges, no true bevel without a modeled mesh asset. The ground
  plane's horizon seam (see Open questions) is a similar "real fix needs
  more than a parameter tweak" case.
- **Testable command-building pattern:** `preview.py`'s `_build_command()`
  is a pure function returning the Godot argv list, tested directly without
  launching Godot, mirroring `render.py`'s `_collect_fresh_images()`.
- **Server startup is lazy.** Importing `mm_mcp.server` does NOT validate
  config or build the catalog; `_ensure_ready()` does that on first tool use
  (or at `mcp.run()`). A test calling a tool under bad config needs
  `server._reset()` in setup AND teardown.
- **`mm-mcp --check`** is the setup doctor (green/red preflight); `--version`,
  `--help` also work. Build/release tooling lives in the `release` extra
  (`pip install -e .[release]` → build, twine). `dist/` and `build/` are
  build-artifact scratch, safe to `rm -rf`, not tracked.
- **Pillow is installed in `.venv` but deliberately NOT in `pyproject.toml`**,
  a one-time tool for downscaling `examples/images/` previews. Don't add it
  as a dependency.
- All Phase 1-2 render gotchas still hold (see CLAUDE.md): `--export-material`,
  `_console.exe`, no `--headless`, `steam_appid.txt`.
- **Minor, non-blocking, carried over:** `.gitignore` has no `dist` entry
  even though CLAUDE.md and this doc call `dist/` gitignored, worth a
  one-line fix next time packaging is touched.
- `normal_map` is a compound node; real params `param0` (size), `param1`
  (strength), `param2`, `param4` (0 = real relief for analytic generators,
  1 = flat) — NOT `amount`/`size`. Voronoi **output port 2** = `rand3`
  random-per-cell (the fleck/speckle source); ports 0/1 are distance fields.
- **Cookbook growth pattern** (`quality/cookbook_<category>.py` +
  `render_cookbook.py` + `_make_previews.py`) is separate from the frozen
  Phase 3 test set on purpose, copy it for the next category rather than
  touching `test_set.json`/`run_case.py`/`author.py`'s `BUILDERS` dict. See
  `quality/README.md` for the short version and `docs/AUTHORING.md` for every
  recipe + the levers that didn't pan out.

---

## 🕓 Session log

### 2026-08-27 (early AM) — Phase 5 build step 1: overlay.py, full SDD pipeline
- Continued straight from this session's own Phase 5 de-risking spike.
  Grayson said "let's keep going" / "continue" through each stage rather than
  stopping between skills.
- **`writing-plans`:** designed `ensure_overlay` as a 5-task TDD plan (hash
  helper → autoload injection → staleness marker → first-build → no-op/rebuild
  tests), following the established codebase patterns (dataclass-free
  functional style matching `preview.py`, pytest + `tmp_path`). Saved to
  `docs/superpowers/plans/2026-08-26-phase5-overlay-builder.md`.
- **`using-git-worktrees`:** asked Grayson for consent (was on `main`
  directly), created an isolated worktree via the native `EnterWorktree` tool
  rather than a manual `git worktree add`. Fresh `.venv`, copied the
  gitignored `.env` over (not git-tracked, worktrees don't inherit it),
  baseline 109 tests green before starting.
- **`subagent-driven-development`:** pre-flight conflict scan across all 5
  tasks (found one real gap: Task 4/5's briefs didn't declare their
  dependency on Task 1/2's test helpers, carried forward via dispatch
  messages rather than editing the plan). Then 5 tasks, each a fresh haiku
  or sonnet implementer + a fresh sonnet reviewer, with model tier chosen by
  task complexity (haiku for mechanical/transcription tasks, sonnet for
  Task 4's multi-file integration). **3 real bugs found across the loop, all
  in this session's own plan-authored reference code** (see Current state for
  detail) — each ruled plan-mandated-not-implementer-error, fixed in the same
  task's fix round, verified by a scoped re-review before moving on. Every
  ruling recorded in the SDD ledger with a cost-if-wrong assessment.
- **Final whole-branch review** (opus, per Model Selection's "architecture
  and design tasks use the most capable model"): found 2 more real,
  empirically-reproduced findings — `ensure_overlay` ran destructive
  filesystem ops before validating input (reviewer actually deleted a test
  checkout by passing `overlay_dir == mm_project_path` to prove it), and
  `STATUS.md`'s gate ledger was never updated (a real CLAUDE.md rule this
  branch violated). One consolidated fix subagent (not one-fixer-per-finding,
  per the skill's guidance) closed both plus 4 folded-in Minor findings
  (UnicodeDecodeError guard, case-insensitive path comparison on Windows,
  missing docstrings, no test of the marker file's own JSON contents). Scoped
  re-review confirmed all 7 addressed, 134/134 tests green. Two cosmetic
  findings parked with rulings (STATUS.md prose wording; a pre-existing,
  unrelated "seven tools"/"eight tools" count mismatch).
- **`finishing-a-development-branch`:** presented the 3-option menu, Grayson
  chose merge-locally. Fast-forward merge (`128fa31`..`67a028a`, 9 commits),
  verified 134/134 on the merged result, worktree removed, branch deleted.
  Grayson then asked to push + wrap; pushed (`origin/main` synced, `0 0`).
- No target date was set for step 2 (the real addon script) — this session
  only committed to de-risking + building step 1, matching Phase 5's
  standing "deferred, no target date" status.

### 2026-08-26 (late night, cont. 3) — Phase 5 feasibility spike (both risks retired)
- After the seam fix, Grayson picked "start Phase 5" (live-control addon).
  Started it spike-first per the spec's own instruction to check its two risks
  before building.
- Read MM source to retire **risk #2** before touching Godot: found the
  GUI-grade mutation API (`get_current_graph_edit()` →
  `create_nodes`/`do_connect_node`/`set_node_parameters`/`generator.serialize()`),
  reachable via the `mm_globals` autoload at `/root/mm_globals`. Confirmed the
  `[autoload]` line format and that `mm_globals` is a `*`-singleton.
- Consulted the advisor, which split the spike into 1a (pure-Godot autoload
  socket, no MM copy) and 1b (real MM overlay), and flagged four constraints
  (await-based `create_nodes`, null `main_window` at `_ready()`, overlay needs
  `steam_appid.txt`, don't PIPE Godot stdout). All folded into the plan.
- **1a PASS:** throwaway `scratchpad/autoload_spike/` project, one autoload
  opened a `TCPServer`, Python did `ping`/`quit` over it. One GDScript
  type-inference fix (`get_string` needs an explicit `String` type). The
  drained-pipe gotcha showed up here (PIPE-without-drain faked a connect
  failure; file redirect fixed it).
- **1b PASS:** robocopied the 266M MM checkout into
  `scratchpad/mm_overlay/` (kept `.godot` cache for fast launch), dropped the
  addon at `addons/mm_live/live_server.gd`, appended the autoload line. Launched
  real MM, polled `ping` until `main_window` wired, then `get_graph` returned a
  genuine `generator.serialize()` (default new-material graph, 1 node type
  `material`, 0 connections). Clean socket `quit`, exit 0.
- Recorded the verdict + constraints in the spec's new "Feasibility verified"
  section and marked its Status ready-for-implementation. Spike code left in
  scratchpad (throwaway), not committed.

### 2026-08-26 (late night, cont. 2) — horizon seam fix
- Picked up via `pickup` with the seam fix as the appended task. Clean pickup,
  no drift (repo matched the baton).
- Diagnosed the seam as fog math, not geometry: the 60×60 plane's far edge sat
  ~30 units out, where exponential fog (density 0.07) only reaches ~88%, so the
  ground's hard edge stayed ~12% visible against `BG_COLOR`.
- Fixed by extending the plane to 400×400 (edge ~200 units out, fog effectively
  100%) with a density-preserving UV scale (`GROUND_SIZE / GROUND_SIZE_REFERENCE`)
  so near-camera tiling is unchanged. Chose bigger-plane over procedural-sky to
  preserve the tuned dark background.
- Verified with real before/after renders (seam gone, gradient horizon), 109
  fast tests, and a live `render_preview()` call. Committed `9e52340`, pushed.
- Found and corrected a stale baton claim: the "3 unpushed commits" note was
  wrong; `origin/main` was already at `0675ca1`, so that work was already on
  GitHub. Only the seam fix needed pushing.

### 2026-08-26 (late night, cont.) — render_preview MCP tool + North Star doc
- Picked up via `pickup`, Grayson asked whether the pipeline could show a
  material on a 3D object (spheres/cubes, nice side lighting for the normal
  map) rather than flat map swatches. Checked `src/mm_mcp/render.py` and the
  design docs: no, only `--export-material` flat PNGs existed anywhere.
- **Spike first** (`superpowers:brainstorming`, spike path): a throwaway
  standalone Godot project proved a headless lit sphere+cube render was
  feasible in about 20 minutes, one bug (`look_at()` before `add_child()`),
  no `steam_appid.txt` needed since it's not the Material Maker checkout.
- **Bounded design, then TDD implementation** (`41bd60b`): a new
  `render_preview` MCP tool, takes `render_graph`'s
  albedo/normal/orm paths (not a `.ptex` graph, keeps `render_graph`
  single-purpose), returns the same error-as-data shape as the other tools.
  Bundled the promoted spike assets as `src/mm_mcp/preview_project/`. Caught
  and fixed a real gap: the bundled Godot project wasn't in
  `pyproject.toml`'s package data, so a pip install would've silently
  shipped without it, verified the fix by actually building a wheel and
  checking its file list. 5 new tests, 110 passed at that point.
- **North Star doc** (`8fc8e33`): Grayson's framing, mid-session, that this
  project's real point is lowering the barrier to learning Material Maker
  (he's learning it himself by watching/editing what gets authored for him),
  not one-shot texture generation, wasn't written down anywhere. Added
  `docs/NORTH_STAR.md`, linked from README and CLAUDE.md so future sessions
  read it before proposing new scope.
- **Visual iteration round** (`aefd7af`), rendering and showing Grayson the
  actual PNG at every step rather than guessing blind:
  - Ground plane the objects rest on, tiling 8x finer than them, `--tile`
    knob to scale UV repeat (this had only ever been a manual Godot cmdline
    arg during testing; wired it through `render_preview`'s real Python API
    and the MCP tool signature as part of locking the scene in).
  - Third object: a cutaway ball (CSG sphere minus a wedge box, revealing an
    inner core), an honest approximation of a studio material-test ball,
    not a true beveled asset (Godot's CSG booleans cut sharp edges, a real
    bevel needs a modeled mesh, told Grayson this plainly rather than
    pretending otherwise).
  - Two full rotation-angle sweeps (6 renders each, composited into labeled
    contact sheets) to find where the cutaway ball's cut stayed visible.
    Z-axis rotation only ever swung it between "barely visible" and "hidden
    against the ground/shadow." Y-axis (Grayson's correction: "look down on
    top of it and turn it") is what worked, 240° locked in.
  - Fixed the cut face rendering plain white (the CSG wedge cutter had no
    material, gave it the shell's own) and the inner core reading as noise
    (it was using the ground's much-finer tile scale on a far smaller
    sphere, scaled its tile count to its own radius fraction instead).
  - Shadow-casting light, depth of field (`CameraAttributesPractical`
    assigned to `Camera3D.attributes`, not direct properties, first attempt
    errored and hung the Godot process, `taskkill` cleared it), exponential
    fog, MSAA 4x → 8x + FXAA (project setting and explicit viewport
    override), camera pushed closer + narrower FOV, cube turned 45°,
    look-at target raised to center it, then fog/DOF strength tuned down
    once the base look was approved.
  - Cleaned up the now-locked `cutaway_rot` debug arg into a named constant.
- Ran the full suite (112 passed, 109 fast + 3 integration) and one live
  call through the real `render_preview()` API as a final check before
  committing. Three commits on `main`, not pushed.

### 2026-08-26 (late night) — Phase 5 design spec + batch MVP verification
- Picked up option D from the prior handoff's menu (Phase 5 live control).
  Classified it architectural per `superpowers:brainstorming` and ran the
  full process: questions, approaches, sectioned design, written spec.
- **Key pivot during questioning:** Grayson pushed back on the original
  "forked Material Maker" framing, he doesn't want to maintain a diverging
  copy of someone else's codebase, just "control it from the outside."
  Resolved by distinguishing a Godot **addon** (additive, the same mechanism
  Material Maker's own `addons/material_maker` uses) from a true source fork,
  and by having the addon live in *this* repo, layered onto a disposable,
  auto-rebuilt overlay of the pristine checkout rather than baked into it.
- **Also clarified:** the live-GUI collaborative mode and the headless
  "agent makes me a texture" mode are two separate use cases. Grayson is
  fine deferring real-time back-and-forth for now (turn-based is enough),
  and confirmed the headless case is what the existing batch pipeline
  (Phases 0-3) already does.
- Picked transport (a TCP/WebSocket server run by the addon, Python connects
  as a client) over two alternatives, ruled out for not fitting
  "attach to an already-open instance" (subprocess-owned pipes) or not
  feeling real-time (file-based polling).
- Wrote and committed
  `docs/superpowers/specs/2026-08-26-live-control-addon-design.md` (`311e502`).
  Flagged two unverified feasibility risks inline rather than glossing over
  them: Godot autoload wiring for a *running* (non-editor) project, and
  whether Material Maker exposes a sane in-process graph-mutation surface.
  No implementation started; deliberately no target date.
- **Batch MVP verification:** ran a fresh, live round trip through
  `mm_mcp.server`'s real public tool functions (`list_examples` →
  `load_example` → edit → `validate` → `render_graph` → `save_graph`) on a
  novel request ("brick, warmer/redder"), not a replay of an existing test
  case. All 4 PBR maps rendered non-empty, albedo visually confirmed the
  request landed. Delivered the result to Grayson directly, closing the
  request-to-delivery loop for real rather than asserting it via test count.

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
