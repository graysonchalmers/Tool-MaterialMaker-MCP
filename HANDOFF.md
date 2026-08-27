# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-27 (midday) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**Phase 5 build step 2 (`addons/mm_live/live_server.gd` + `src/mm_mcp/live.py`)
shipped: built, reviewed, fixed, merged, pushed.** Picked up via `pickup`,
Grayson chose "start on Phase 5 step 2 via writing-plans." Ran the full
`superpowers` pipeline again, same shape as step 1: `writing-plans` ->
consent for an isolated git worktree (native `EnterWorktree`) ->
`subagent-driven-development` (5 tasks, fresh implementer + fresh reviewer per
task, haiku for mechanical/transcription tasks, sonnet for integration-heavy
tasks and reviews) -> whole-branch review on opus -> `finishing-a-development-branch`
(merged locally, then pushed).

The real live-control addon exists now, not scratchpad code: `live_server.gd`
is a thin GDScript autoload registered via `overlay.py`'s `[autoload]`
injection, opens a `TCPServer` on a fixed port (8765), and answers `ping`/
`get_graph` over a line-delimited JSON protocol -- deliberately read-only,
no mutating commands, no validation logic (mutations arrive pre-validated
from Python in a later step). `src/mm_mcp/live.py` is the Python side: a
low-level one-shot protocol client (`LiveResult`, `_send_command`, `ping`,
`get_graph`), tested against a hand-rolled fake TCP server, plus a
`connect_or_launch()` orchestration layer (`LiveSession`) that probes the
fixed port, launches Material Maker via `overlay.py`'s `ensure_overlay` if
nothing's listening, polls `ping()` until the addon reports `main_window` is
actually wired (never just "socket is open"), and manages the launched
process's lifecycle so it's never leaked, including on an unexpected
exception mid-poll (a review-found gap, fixed in one round). `Config` gained
a `live_overlay_dir` field mirroring `output_dir`'s existing env-override
pattern.

**Real bugs found by the review loop, same disciplined pattern as step 1:**
1. (Task 4 review) `connect_or_launch` had no `try`/`finally` around the
   launch-and-poll span -- an unexpected exception mid-poll would leak the
   just-launched, real, visible Godot process. Currently inert only because
   `_send_command` happens to catch every exception type it can raise, which
   is an accident of its current implementation, not a structural guarantee.
   Fixed same round: `try`/`except BaseException` terminates and re-raises.
2. (final whole-branch review, opus) Three merge-blocking findings, all
   fixed in one consolidated wave:
   - `mm_live_overlay/` (the disposable overlay's default location, a ~266MB
     full copy of the Material Maker checkout) was missing from `.gitignore`
     -- would have entered the nightly `V:` backup sweep and confused
     `git add -A` on first real use. **Caught before it ever happened, not
     after.**
   - `connect_or_launch` never checked whether the launched process had
     already died -- a bad overlay or a GDScript parse error in a future
     addon edit would spin the *full* 60-90s timeout before returning a
     generic "timed out" message, with the real diagnosis sitting unread in
     `mm_live.log`. Fixed: `process.poll()` check inside the loop, returns
     immediately with the exit code and the log path.
   - The integration test isolated its overlay directory but not the fixed
     port -- it could have silently passed by attaching to a stray
     already-running Material Maker instance instead of proving the freshly
     built overlay + committed addon actually work. Fixed: an explicit
     assertion that the session owns a launched process, not an attached one.

Prior sessions' detail (overlay builder, feasibility spike, seam fix,
render_preview) is preserved in the Session log below rather than repeated
here.

## 📌 Where we stopped

Clean stop. Merged to `main` locally (`81b433c`), then pushed; `main` and
`origin/main` in sync. Working tree clean, 148/148 fast tests pass on the
pushed tip. No worktree, no branch, no lingering Godot processes.

## ▶️ Next concrete step

**Phase 5 build step 3: mutating commands.** Steps 1 (overlay builder) and 2
(addon skeleton: `ping`/`get_graph`) are done. Step 3 per the spec's
sub-plan: `add_node`/`connect_nodes`/`set_param`/`render` on both the
GDScript addon side and `live.py`'s client side. Gate: "a scripted sequence
of live ops visibly builds a simple graph in a real running window and
renders it." Known constraints from the earlier feasibility spike that step
3 must respect (see the spec's "Feasibility verified" section): `create_nodes`
is `await`-based in Godot -- the addon's command loop must be a coroutine
that awaits the result before writing the socket response, or it replies
with a coroutine-state object instead of real data (this wasn't exercised
by step 2's read-only `ping`/`get_graph`, which are synchronous). The
"render" handler is still unverified against source -- confirm it actually
invokes Material Maker's own existing preview/export code path before
building on that assumption. Use `writing-plans` again for this step, same
pattern as steps 1 and 2.

Alternatives, all carried over unchanged:
- **A. More cookbook categories** (extend the authoring recipe library).
- **B. The two honest partials** (wool loop-knit, circuit-board mask-bleed).
- **D. PyPI publish** (on hold; GitHub-clone is the current route).
- **E. Document `render_preview`** in `docs/AUTHORING.md` / README, or leave it
  as just an MCP tool.
- **F. Parked polish items from step 1's and step 2's final reviews** (see
  Heads-up): `STATUS.md` prose wording; a pre-existing "seven tools" vs.
  "eight tools" count mismatch; step 2's parked Minor findings (GDScript
  `peer.put_data()` discarded return, `log_file` fd leak in `_launch_overlay`,
  no fast-suite guard on `_ADDON_PATH` resolution).

## ❓ Open questions

- Should `render_preview` get documented in `docs/AUTHORING.md` / README, or
  is it enough that it exists as an MCP tool? Not yet decided, not done.
- Step 2's own open questions, carried forward for whoever builds step 3: a
  two-instance launch race in `connect_or_launch` (two concurrent calls could
  both see "not listening" and both launch, one wins the port); a foreign
  process squatting on port 8765 causes a full-timeout dead end with no way
  to detect "this isn't actually Material Maker"; the channel is
  unauthenticated to other local processes, fine for read-only `get_graph`
  but worth reconsidering once step 3 makes it a write channel. All three
  flagged by the final review as "worth a line in step 3/4's plan, not a fix
  in step 2."
- Two parked-not-fixed findings from the overlay-builder's (step 1) final
  review (deliberately deferred, not forgotten): the staleness marker
  doesn't detect an already-built overlay being damaged from outside (e.g.
  hand-editing `project.godot` in the Godot editor while debugging steps
  3-4) -- whoever builds step 3 should reconsider this; `_append_autoload`'s
  `content.find("[autoload]")` matches the first occurrence anywhere in the
  file including inside a comment (verified inert against the real file, so
  low priority).
- Carried over, unchanged: Phase 5 implementation timing (no target date by
  design); circuit-board mask-bleed bug (no lead after 3 tries); wool's
  loop-knit approximation; PyPI vs. GitHub-clone-only (leaning GitHub-only);
  cross-platform (macOS/Linux) verification, still untested, no machine
  available.

## 🗂️ Changed this session (Phase 5 addon skeleton)

- Branch: `main`. Landed as 6 commits via a feature branch merged locally
  then pushed: `33dad4e` Task 1 (addon skeleton, GDScript), `846f310` Task 2
  (`Config.live_overlay_dir`), `9ff21ec` Task 3 (`live.py` protocol client),
  `b1242b5`/`5614ea0` Task 4 (`connect_or_launch` + fix round), `23d5fe0`
  Task 5 (real integration test), `25675d3` final-review fix wave. Plus a
  separate `d8cda95` committing the plan doc itself (was never committed
  during planning) and the `81b433c` merge commit.
- Decisions (+ why): the addon lives at top-level `addons/mm_live/`, a
  sibling of `src/`, not inside `src/mm_mcp/` -- unlike `preview_project/`
  (which ships in the wheel via package-data), this addon will NOT ship in a
  built wheel; accepted as a known gap under Phase 4's current GitHub-clone
  distribution decision (PyPI on hold), not silently "fixed" by moving it.
  `LIVE_PORT = 8765` is a hardcoded literal on both the GDScript and Python
  sides with a cross-reference comment, not a shared-constant mechanism --
  explicit YAGNI call for a single fixed local addon. `connect_or_launch`
  only owns the lifecycle of a process it actually launched itself
  (`LiveSession.close()` no-ops when attaching to an already-running
  instance), matching the spec's "attach to an already-open instance"
  scope decision.

## 🗂️ Changed the prior session (Phase 5 overlay builder + seam fix)

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
  `_append_autoload`) -- see the session log for the bug list. `overlay_dir`
  stayed a caller-supplied parameter rather than derived from `Config`,
  keeping the module's only dependencies stdlib (`hashlib`, `json`, `os`,
  `shutil`) -- `live.py` (step 2) ended up owning where the overlay actually
  lives, as anticipated.

## ⚠️ Heads-up for the next agent

- **New addon: `addons/mm_live/live_server.gd`.** Thin GDScript autoload,
  `TCPServer` on port 8765, `ping`/`get_graph` only. Lazy `main_window`
  resolution -- never cache it, resolve fresh inside every command handler
  (autoloads start before the main scene, so it's null at `_ready()`). If
  you're ever tempted to add validation logic here, don't -- everything
  mutating (step 3) arrives pre-validated from the Python side by design.
- **New module: `src/mm_mcp/live.py`.** `ping()`/`get_graph()` are one-shot
  connect/send/recv/close calls (`_send_command`), no persistent session
  state on either side. `connect_or_launch(cfg=None, host=LIVE_HOST,
  port=LIVE_PORT, launch_timeout=60.0) -> LiveSession` is the orchestration
  entry point: probes the port, launches via `overlay.py`'s `ensure_overlay`
  if nothing's listening, polls until ready, guards against leaking the
  process it launched on any exit path (success, timeout, or an unexpected
  exception). `LiveSession.close()` is a safe no-op when `process is None`
  (attached, didn't launch).
- **`overlay.py`'s `ensure_overlay` is now actually consumed** (by
  `live.py`'s `_launch_overlay`), no longer just unit-tested in isolation.
  `_ADDON_PATH` resolves to `<repo-root>/addons/mm_live` via 3 `os.path.dirname`
  calls from `src/mm_mcp/live.py` -- this assumes an editable/source-checkout
  install, verified correct for that case, not for a real wheel install (see
  the top-level-`addons/` decision above).
- **`mm_live_overlay/` (the disposable overlay's default build location) is
  gitignored.** It's a ~266MB full copy of the Material Maker checkout,
  rebuilt on every addon change -- don't be surprised it's large, and don't
  remove the gitignore entry.
- **`mm_live.log`** (in `cfg.output_dir`, default `./output/mm_live.log`) has
  the launched Godot process's captured stdout+stderr. Check it first if a
  live-mode launch fails -- `connect_or_launch` now names this path directly
  in its error message when the launched process dies before becoming ready.
- **`_append_autoload` inserts at the end of the `[autoload]` section
  specifically, not blindly at end-of-file** -- a real bug found and fixed in
  step 1. If you're ever tempted to "simplify" this function back to a plain
  append, don't; the real Material Maker `project.godot` has ~10 sections
  after `[autoload]`, verified.
- **`ensure_overlay` validates before mutating anything.** It raises
  `ValueError` if `addon_path` isn't a directory, `mm_project_path` has no
  `project.godot`, or `overlay_dir` equals/contains either input path
  (case-insensitive) -- guards against actually deleting the real
  `z-Git\material-maker` checkout if `live.py` ever misconfigures
  `overlay_dir`.
- **New MCP tool (from an earlier session):** `render_preview(albedo_path,
  normal_path, orm_path, basename="preview", tile=1.0) -> dict`. Call
  `render_graph` first and feed its output paths in. Renders through
  `src/mm_mcp/preview_project/`, a small standalone Godot project bundled in
  this repo, not the `z-Git\material-maker` checkout.
- **Run tests with `.venv\Scripts\python.exe`** (or activate the venv).
  Fast suite: `pytest -q -m "not integration"` (148 passed, 4 deselected);
  `pytest -q` adds the Godot-launching integration tests, including the new
  real-live-mode one from this session (which opens a visible GUI window
  briefly, unlike the other, headless integration tests).
- **Godot property-name traps hit in an earlier session** (both caused a
  script error + hung process, had to `taskkill`): depth of field lives on a
  `CameraAttributesPractical` resource assigned to `Camera3D.attributes`,
  not direct `Camera3D` properties; `smooth_faces` exists on `CSGSphere3D`
  but not `CSGBox3D`. If a Godot script error leaves the console binary
  hanging, `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` clears
  it (Bash tool, not PowerShell).
- **Known, honestly-flagged limitations, not bugs:** CSG boolean subtraction
  cuts sharp edges, no true bevel without a modeled mesh asset. The ground
  plane's horizon seam issue from an earlier session was a similar "real fix
  needs more than a parameter tweak" case (already fixed, see session log).
- **Testable command-building pattern:** `preview.py`'s `_build_command()`
  and `live.py`'s `_launch_command()` are both pure functions returning a
  Godot argv list, tested directly without launching Godot, mirroring
  `render.py`'s `_collect_fresh_images()`.
- **Server startup is lazy.** Importing `mm_mcp.server` does NOT validate
  config or build the catalog; `_ensure_ready()` does that on first tool use
  (or at `mcp.run()`). A test calling a tool under bad config needs
  `server._reset()` in setup AND teardown.
- **`mm-mcp --check`** is the setup doctor (green/red preflight); `--version`,
  `--help` also work. Build/release tooling lives in the `release` extra
  (`pip install -e .[release]` -> build, twine). `dist/` and `build/` are
  build-artifact scratch, safe to `rm -rf`, not tracked.
- **Pillow is installed in `.venv` but deliberately NOT in `pyproject.toml`**,
  a one-time tool for downscaling `examples/images/` previews. Don't add it
  as a dependency.
- All Phase 1-2 render gotchas still hold (see CLAUDE.md): `--export-material`,
  `_console.exe`, no `--headless`, `steam_appid.txt`.
- **Minor, non-blocking, carried over:** `.gitignore` had no `dist` entry
  even though CLAUDE.md and this doc call `dist/` gitignored, worth a
  one-line fix next time packaging is touched.
- `normal_map` is a compound node; real params `param0` (size), `param1`
  (strength), `param2`, `param4` (0 = real relief for analytic generators,
  1 = flat) -- NOT `amount`/`size`. Voronoi **output port 2** = `rand3`
  random-per-cell (the fleck/speckle source); ports 0/1 are distance fields.
- **Cookbook growth pattern** (`quality/cookbook_<category>.py` +
  `render_cookbook.py` + `_make_previews.py`) is separate from the frozen
  Phase 3 test set on purpose, copy it for the next category rather than
  touching `test_set.json`/`run_case.py`/`author.py`'s `BUILDERS` dict. See
  `quality/README.md` for the short version and `docs/AUTHORING.md` for every
  recipe + the levers that didn't pan out.

---

## 🕓 Session log

### 2026-08-27 (midday) — Phase 5 build step 2: addon skeleton, full SDD pipeline
- Picked up via `pickup`, Grayson chose "start on Phase 5 step 2 via
  writing-plans."
- **`writing-plans`:** read the design spec, `overlay.py`, `preview.py`,
  `render.py`, and the real Material Maker source (`console.gd`, `globals.gd`,
  `main_window.gd`, `graph_edit.gd`) to ground the GDScript API calls in
  verified reality rather than guessing. Designed a 5-task TDD plan (addon
  skeleton -> Config field -> low-level protocol client -> connect_or_launch
  orchestration -> real integration test), following established codebase
  patterns (dataclass-result style matching `preview.py`/`render.py`, pytest
  + `tmp_path`, a hand-rolled fake TCP server for protocol tests). Caught and
  fixed 3 count errors during self-review before dispatch. Saved to
  `docs/superpowers/plans/2026-08-27-phase5-addon-skeleton.md`.
- **`using-git-worktrees`:** asked Grayson for consent (was on `main`
  directly), created an isolated worktree via the native `EnterWorktree` tool.
  Fresh `.venv`, copied the gitignored `.env` over, baseline 134 tests green
  before starting. The plan doc itself was uncommitted on `main` at pickup
  time, so it had to be copied into the worktree by hand rather than
  inherited via branch history -- flagged by the final review as a
  housekeeping gap and fixed by committing it to `main` before merging.
- **`subagent-driven-development`:** pre-flight conflict scan across all 5
  tasks (clean -- no contradictions found; path arithmetic and port-literal
  consistency checked by hand and recorded in the ledger table). Then 5
  tasks, each a fresh haiku or sonnet implementer + a fresh sonnet reviewer
  (haiku for pure-transcription tasks, sonnet for tasks needing real
  judgment: process-lifecycle correctness, real Godot API verification).
  **1 real bug found in the loop** (Task 4's `connect_or_launch` had no
  exception-safety guard around the launch-and-poll span -- see Current
  state), ruled Important, fixed in one round, verified by a scoped
  re-review. The Task 1 reviewer went further than reading the diff: wrote a
  standalone headless Godot script to actually execute the GDScript
  buffering/slicing logic under scrutiny rather than reasoning about Godot 4
  API semantics from memory, confirming a suspected `PackedByteArray`
  value-type mutation risk was NOT a bug.
- **Final whole-branch review** (opus): found the protocol genuinely agrees
  across the GDScript/Python language boundary when read as one system (port,
  host, command names, framing, response shape all checked cross-file), and
  that the Task 4 exception-safety fix held up under whole-diff scrutiny, not
  just its own small patch. Also found 3 new, real, merge-blocking issues no
  task-scoped review could see (see Current state): the missing `.gitignore`
  entry for the 266MB overlay, the silent-timeout/no-log-pointer gap in
  `connect_or_launch`, and the integration test's stray-instance gap. One
  consolidated fix subagent closed all three plus added a regression test
  for the dead-process-detection path; a scoped re-review confirmed all
  addressed, no new breakage, 148/148 independently re-confirmed by the
  controller directly (not trusting subagent-reported counts, which had
  drifted inconsistently across a few tasks' own self-reports for reasons
  never root-caused -- ground truth taken from a direct `pytest` run
  instead). 6 further Minor findings parked with rulings (GDScript
  `put_data()` discarded return, `log_file` fd leak, `Popen.kill()` being a
  no-op alias of `terminate()` on Windows, a fast-suite gap on `_ADDON_PATH`
  resolution, a two-instance launch race, an unauthenticated local channel)
  -- all explicitly deferred to step 3/4's own plans per the reviewer's own
  triage, not silently dropped.
- **`finishing-a-development-branch`:** presented the 3-option menu, Grayson
  chose merge-locally. Committed the previously-uncommitted plan doc to
  `main` first (`d8cda95`), then merged (`81b433c`, real merge commit since
  `main` had moved), verified 148/148 on the merged result with the
  project's own venv (not the system Python used for the initial
  `pip install`, which surfaced an unrelated pre-existing `huggingface-hub`
  version conflict warning from global site-packages -- harmless, not this
  project's dependency tree), removed the worktree (needed `--force` after
  showing Grayson what was at stake: a single untracked file that was
  already a duplicate of what had just been committed to `main`), deleted
  the branch.
- Grayson then asked to update STATUS.md + HANDOFF.md, wrap up, and push --
  all three done this pass.

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
