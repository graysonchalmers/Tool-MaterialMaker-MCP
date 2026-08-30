# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-30 (Phase 4 hardening) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**This session closed out Phase 4 hardening (path bounding + `inspect_project` +
CI + release-please), prompted by a compare against
`dcc-mcp/dcc-mcp-material-maker`.** That other project is a locked-down headless
export/inspection adapter, a different product from ours (it never authors
graphs); we borrowed its packaging/sandboxing rigor without changing our
round-trip North Star. Three items landed via 10 TDD tasks (subagent-driven,
whole-branch review clean, merged `d23b235`): (1) **opt-in `MM_ALLOWED_ROOTS`
path bounding** (`src/mm_mcp/paths.py`) wired into `save_graph` (now returns a
`{"ok","path"}` dict, not a bare str), `load_example`, and the 3 render tools,
plus an always-on `../` traversal guard; unset = unrestricted, so daily use is
unchanged, and `--check` reports the state. (2) **`inspect_project`** batch tool
#10 (`src/mm_mcp/inspect.py`). (3) **CI** `.github/workflows/test.yml` and
**release-please**, with `__version__` single-sourced via `importlib.metadata`.
`main` is **pushed and in sync** (`origin/main` = `d23b235`); the **tests CI
passed on its first real Windows run**. Older write-ups/log beyond the cap live
in [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).

## 📌 Where we stopped

Everything is landed and pushed. The one open thread: **release-please's first
run failed at the final step only** ("GitHub Actions is not permitted to create
or approve pull requests"). It got all the way to creating the release branch and
committing the CHANGELOG + version bump to **0.4.0**; it just could not open the
PR because the repo setting is still off. Grayson is handling that later.

## ▶️ Next concrete step

**Enable the one GitHub setting, then re-run release-please.** Repo → Settings →
Actions → General → Workflow permissions → check "Allow GitHub Actions to create
and approve pull requests" → Save. Then `gh run rerun <release-please run id>`
(or push any commit) opens the 0.4.0 release PR. The push credential also needed
a one-time `gh auth refresh -s workflow` (workflow files are separately
permissioned); that scope is now granted. Other follow-ups still open:
- **More debug swatches** if wanted: blend-mask polarity, height-to-normal
  convention, colorize/ramp direction — same pattern, each tied to a real trap.
- **More cookbook categories**: glass, plastics, painted metal still uncovered.

The older open backlog, unchanged:
- **2 findings ruled out, not fixed** (deliberate): #8 (`_cmd_clear_graph`'s
  guard is correct — `new_material()` creates the generator, doesn't read
  one) and #10 (`generic_size or 1` coercion is safer than passing an
  explicit 0). Both annotated in-code. Findings 3-7 and 9 are fixed.
- **`list_node_types` tool decision** — the teardown flagged it as redundant
  with the `catalog://nodes` resource + `describe_node`. It's a live, tested
  MCP tool, so removing it is a product call, not dead code. Undecided.
- **N. "Material Maker for dummies" — a simplified interface, unscoped.**
  New backlog idea from Grayson this session (captured in full in
  `_agent-commons/ideas/Tool-MaterialMaker-MCP.md`): the real node graph can
  be intimidating to a non-technical viewer; is there a simpler on-ramp?
  Explicitly deferred pending its own `brainstorming` session — worth
  checking against `docs/NORTH_STAR.md`'s round-trip-learning-tool framing
  first, since hiding the graph outright vs. exposing a simplified parameter
  panel on top of a graph mm-mcp already authored are very different scope
  bets.

**Older backlog, unchanged, still open:**
- **A. Unreal UE5 export verification** — the natural continuation of a
  prior session's work. Unity is proven end to end; Unreal's export
  mechanism is confirmed real at the file-generation level (same CLI, just
  `--target "Unreal/Unreal Engine 5"`) but running the generated script
  needs a live Unreal Editor with the `mcp__unreal-engine__*` MCP bridge
  connected and Material Maker's `export/mm.py` added to Unreal's Python
  paths (one-time setup, documented upstream). Grayson said Unreal "is not
  working right now" as of that session; check whether that's fixed before
  trying again.
- **B. More cookbook categories** — wood and stone are both represented (5
  categories total: fabrics, organics, sci-fi, terrain, wood, stone).
  Leather beyond `f02`, glass, plastics, painted metal beyond `combo01` are
  uncovered.
- **C. True cobblestone** — `s05_hex_stone_tile` is an honest partial
  (regular hex grid, not irregular). A voronoi-plate approach (like
  `dry_earth`'s cracked-plate network, recolored to stone tones with
  per-plate variation) is untried and would likely get real irregularity.
- **D. The two remaining honest partials** (wool loop-knit, sf03's
  circuit-board trace-bleed-through; a prior session ruled OUT one
  hypothesis for the circuit-board bug, see Open questions, but didn't find
  the real cause).
- **E. Image-to-material decomposition** — Grayson's own backlog idea,
  captured in `_agent-commons/ideas/Tool-MaterialMaker-MCP.md`. Explicitly
  deferred; likely wants its own `brainstorming` session before any design
  work, not a cold start here.
- **F. PyPI publish** (on hold; GitHub-clone is the current route).
- **G. Document `render_preview`** in `docs/AUTHORING.md` / README, or leave
  it as just an MCP tool.
- **H and I are done** (`render_node_output`/`live_render_node_output` and
  `reposition_node`, respectively) — see the Session log's 2026-08-28 and
  2026-08-29 (later) entries. Renaming an existing node live is a ruled-out
  non-goal, not an open gap: see `live.reposition_node`'s docstring for why.
- **J. Load an existing `.ptex` into a live session.** No `live_load`
  equivalent exists; `live_start`/`connect_or_launch` only ever begin from
  a default graph or whatever's already open in the attached window. Lowest
  priority of the remaining live-mode gaps.

## ❓ Open questions

- **Resolved this session:** whether to keep expanding live-control's
  mutation surface. Grayson said keep building it (see item I above) —
  no longer open.
- **Resolved this session:** the long-flagged untracked
  `docs/images/contact-sheet-wood-stone.png` is gone — superseded by the new
  tracked `docs/images/cookbook-contact-sheet.png` (4×7, all categories) and
  removed. No longer an open item.
- **New this session:** the cross-engine North Star wording treats UE4's
  export path (PNGs + manual in-editor assembly) as a lesser tier, not a
  real target — Grayson said "sounds good" generally but never explicitly
  confirmed that specific framing. Worth a quick check before it drives
  real scope decisions.
- **New this session:** `sf03_circuit_board`'s trace-bleed-through bug is
  STILL unresolved, but one hypothesis is ruled OUT (from a prior session):
  widening a razor-thin mask threshold band (w03's fix) does not fix
  `sf03`'s bleed-through. Whoever picks this up next should look elsewhere,
  possibly the specific interaction between `voronoi` port 2 (per-cell
  random) and `blend`, since `sf03`'s chips use voronoi where w03's fixed
  case used a plain perlin mask.
- Still open, unchanged: is `.mcp.json` the right long-term wiring, or
  should it fold into `project-setup`'s standard kit? Not decided.
- Still open, unchanged: should `render_preview` get documented in
  `docs/AUTHORING.md` / README, or is it enough as just an MCP tool?
- Still open, unchanged: true cobblestone (a voronoi-plate approach,
  untried, vs. `s05`'s honest hex-grid partial); wool's loop-knit
  approximation; PyPI vs. GitHub-clone-only (leaning GitHub-only);
  cross-platform (macOS/Linux) verification, still untested, no machine
  available; two parked-not-fixed overlay-builder findings from a much
  earlier session (staleness marker, `_append_autoload`'s first-occurrence
  match, both verified low-priority).

## 🗂️ Changed this session (Phase 4 hardening: path bounding, inspect_project, CI + release-please)

- Branch: `phase4-hardening` (off `main`), 10 TDD tasks subagent-driven, merged
  `--no-ff` as `d23b235`, **pushed to `origin/main`**. New: `src/mm_mcp/paths.py`,
  `src/mm_mcp/inspect.py`, `.github/workflows/test.yml`,
  `.github/workflows/release-please.yml`, `release-please-config.json`,
  `.release-please-manifest.json`, `tests/test_paths.py`, `tests/test_inspect.py`,
  and the spec + plan under `docs/superpowers/`. Edited: `config.py`
  (`allowed_roots`), `server.py` (guards on 5 tools + `inspect_project`),
  `__init__.py` (version via `importlib.metadata`), `doctor.py`, `README.md`,
  `STATUS.md`. Fast suite 260 passed; first real Windows CI run green.
- Decisions (+ why): prompted by a compare against
  `dcc-mcp/dcc-mcp-material-maker` (a headless export/inspection adapter, a
  different product). Borrowed its packaging/sandboxing rigor only where it
  serves our North Star. **Path bounding is opt-in** (`MM_ALLOWED_ROOTS` unset =
  unrestricted) so daily use is frictionless; the `../` traversal guard on
  name/basename fragments is always on. `save_graph` now returns a
  `{"ok","path"}` dict (was a bare str) to match every other tool's shape; no
  internal consumer depended on the old return. **CI provisioning was corrected
  mid-flight:** a bare runner needs the MM checkout + a stub Godot binary (the
  fast suite calls `require_valid`), not "no clone" as first specced; verified
  locally (260 passed) before writing the workflow. Version single-sourced to
  `pyproject.toml` only (release-please owns it), `__init__.py` derives it with a
  `0.0.0+unknown` fallback that is load-bearing for `pythonpath=src` test runs.
- Push friction worth remembering: the commit adds workflow files, which need a
  **`workflow`-scoped** credential. The default git/OAuth and gh tokens lacked
  it; fixed with a one-time `gh auth refresh -h github.com -s workflow`, then
  pushed via `git -c credential.helper='!gh auth git-credential'`. release-please
  then ran but failed only at "open the PR" because the repo's "Allow GitHub
  Actions to create and approve pull requests" setting is still off (see Next
  concrete step). Wrote two `_agent-commons\log\` entries (spec + implementation).

## 🗂️ Changed this session (README front-page 3D previews + social-preview fix)

- Branch: `main`. Committed and **pushed**: `d7f2659` (hero + 3D gallery +
  cookbook section), `738e10b` (social-preview title-crop fix + brick swap).
  New tracked assets: `docs/images/hero.png`, `docs/images/gallery/*.png` (8),
  `docs/images/cookbook-contact-sheet.png`; edited `README.md` and
  `docs/social-preview.png`. Removed the superseded/long-untracked
  `docs/images/contact-sheet-wood-stone.png`. Also fast-forwarded local `main`
  past the render-timeout fix that had merged upstream after the prior wrap.
- Decisions (+ why): ran `brainstorming` → bounded (README already had a
  gallery). Grayson chose "hero + 3D gallery" and "keep 4 columns." Reworked
  the gallery from flat swatches to **3D previews** (the `render_preview`
  sphere+cube+cutaway scene) rendered strictly sequentially, one Godot at a
  time, per the render-orphan rule. **Pure metals (copper, steel) render dark**
  in that scene (dark backdrop + metals reflect environment; they also emit no
  normal map), so Grayson had them swapped out for tree bark + dark walnut.
  Grayson's own hand-finished `saved_graphs/bricks_grayson_edit.ptex` replaced
  the stock red brick in both the hero triptych and the gallery, as a
  round-trip showcase. New collapsible "Material cookbook" section holds a 4×7
  contact sheet of all 28 cookbook materials. The GitHub topic/search **social
  card** crops the 1280×640 image to ~2.74:1, which was chopping off the title;
  lifted the title+subtitle into the crop-safe zone and swapped the brick tile,
  then **uploaded the new `docs/social-preview.png` via repo Settings → Social
  preview** through Grayson's Chrome (that card is NOT read from the repo file,
  it must be uploaded in the web UI). Verified the README images serve HTTP 200.

## 🗂️ Changed this session (render-timeout process-tree kill fix)

- Branch: **`claude/confident-tesla-ee9400`** (git worktree), committed
  `cd1fcb9`, **merged to `main` this session**. Changed: `src/mm_mcp/render.py`
  (new `_kill_tree` helper; `_run_godot` rebuilt on `subprocess.Popen` +
  `communicate()`), `src/mm_mcp/live.py` (`_terminate` delegates to the shared
  `_kill_tree`), `tests/test_render.py` (timeout test asserts the
  `taskkill /F /T /PID` argv fires; `_kill_tree` no-pid + swallow-failure cases;
  a hardening test that the bounded post-kill reap can't hang; retry tests
  re-patched onto `Popen`), `tests/test_live.py` (`_terminate` tests re-patched
  onto `render.subprocess.run`). Also updated the `render-orphan-contention`
  project memory + `MEMORY.md` index (they said the bug was still live).
- Decisions (+ why): the fix requires killing the tree **while the launcher is
  still alive** — `subprocess.run` kills its direct child before re-raising, and
  Windows `taskkill /T` walks live parent-PID links, so a dead/recycled PID
  kills nothing. That forced the move from `subprocess.run` to `Popen` +
  `communicate()` (which also keeps the concurrent pipe-drain that stops a
  chatty render log from deadlocking the child). `_kill_tree` lives in
  `render.py` and `live.py` imports it (live already depends on render, never
  the reverse — avoids a circular import), keeping the memory's
  "all helper pairs deduped" invariant true rather than adding a 4th copy of
  the taskkill block. Hardened the post-kill reap with `communicate(timeout=10)`
  + swallow, so if taskkill fails AND a grandchild keeps the pipe open, the reap
  can't block forever. Verified against real Godot (timeout → `_GodotTimeout`,
  zero leftover Godot, subsequent render OK) and directly observed the
  grandchild + ~6MB single-instance-stuck process live via `tasklist`. A
  `/code-review` pass found 2 PLAUSIBLE findings, both ruled `no_change_needed`
  with primary-source reasons. Fast suite: 232 passed, 21 deselected. Wrote
  `_agent-commons\log\2026-08-29-claude-code-render-timeout-killtree-fix.md`.
  Landed via a real merge with the concurrent debug-swatch wrap-up (`e6eb4c0`),
  which had independently trimmed the same two baton entries.

> 📦 **14 older "Changed this session" write-ups archived** (through
> 2026-08-29) -- the pre-release audit/teardown/doc-fix pass,
> render_node_output/live_render_node_output (item H), saved_graphs/
> round-trip, Unity export proof, wood/stone cookbooks, the overlay
> read-only `rmtree` fix, Phase 5 hands-on verification + `live_clear`, the
> `connect_or_launch` readiness race, and the Phase 5 MCP tool surface --
> moved to [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md) per the trim
> convention (see the note above the Session log below).

## ⚠️ Heads-up for the next agent

- **The 2026-08-29 8-angle code review found 10 verified correctness bugs.
  As of this cleanup session: 7 are fixed (findings 1-7 and 9), and 2 are
  ruled out as deliberate non-changes (#8, #10) with in-code reasons. That
  leaves none outstanding.** Recorded here so they aren't tribal knowledge
  living only in a conversation transcript. Ranked most severe first:
  1. **✅ FIXED.** `server.py` (`live_render_node_output`): the restore-original-wiring
     call after a preview wasn't checked for success — a failed restore used
     to report overall success while the live graph stayed wired to the
     temporary preview connection. Now checked; a failed restore reports
     `ok=False` with a message naming the live graph's actual state (still
     wired to the preview), while still attaching the render's own image if
     the render itself succeeded. New tests:
     `test_live_render_node_output_reports_a_failed_reconnect_restore`,
     `..._reports_a_failed_disconnect_restore`,
     `..._combines_render_and_restore_failures`.
  2. **✅ FIXED.** `server.py` (`live_apply`): only caught `(KeyError, TypeError)`
     from op handlers; a malformed op (e.g. a list where a parameters dict
     is expected) could raise an uncaught `AttributeError` from deep inside
     `validate_graph`'s `.items()` call, discarding the batch's
     already-succeeded results. `AttributeError` added to the caught tuple.
     New test: `test_live_apply_reports_a_malformed_op_field_as_data_not_a_raised_exception`.
  3. **✅ FIXED.** `server.py`: no atexit handler called `_live_session.close()`,
     orphaning a launched Godot process on unclean exit. Added
     `_close_live_session_atexit` + `atexit.register`; verified it fires at
     real interpreter shutdown (the `close()`→`_terminate` it calls was
     already integration-proven).
  4. **✅ FIXED.** `validator.py`: port-range validation only checked the
     upper bound. Now rejects a negative `from_port`/`to_port` too; message
     names the valid range (`0..N-1`).
  5. **✅ FIXED.** `overlay.py` (`ensure_overlay`): a rebuild that failed
     partway left an ambiguous marker-less partial. Now removes the
     half-built overlay and re-raises (unambiguous: complete overlay or
     none). Cleanup is best-effort, can't mask the original error.
  6. **✅ FIXED (docstring).** `live.py` (`render`) always returns an empty
     `log_tail` on the live path (live Godot output goes to `mm_live.log`,
     whole-process). Docstrings in `live.render`/`live_render_node_output`
     corrected to say so and point at `mm_live.log`, rather than populating
     `log_tail` from a possibly-stale, misleading whole-process tail.
  7. **✅ FIXED.** `live.py`: the five mutation ops now default to a 30s
     socket timeout (was 5s), so a cold-launch shader compile doesn't
     spuriously time out. 30s is a ceiling, half `render()`'s proven 60s;
     read-only one-shots (`ping`/`get_graph`/`clear_graph`) stay 5s.
     PLAUSIBLE, not reproduced.
  8. **⛔ RULED OUT (non-bug).** `_cmd_clear_graph`'s `graph_edit==null`-only
     guard is CORRECT, not a missing `generator==null` check. `new_material()`
     CREATES a fresh generator (`clear_material()`→`create_gen`); it doesn't
     read one like the mutating siblings. Adding the guard would refuse to
     clear exactly the graph-less state a clear recovers. Confirmed against
     Material Maker's `graph_edit.gd:690-724`. Annotated in-code.
  9. **✅ FIXED.** `live.py` (`_launch_overlay`): the parent's `mm_live.log`
     handle is now closed (try/finally) after Popen dups the fd, was leaking
     one fd per launch.
  10. **⛔ RULED OUT (deliberate).** `catalog_builder.py`'s `generic_size or 1`
      coercion is intentional: an explicit `0` would build an input-less
      (broken) node, so treating a falsy value as the default 1 is safer than
      passing 0 through. No bundled `.mmg` triggers it. Annotated in-code.
      PLAUSIBLE.
  The full teardown also found real cleanup/duplication issues (a dead
  `Graph` class in `graph.py`, three byte-for-byte-duplicated helper pairs,
  an unused `list_node_types` tool) — see the delivered teardown file for
  those; they were ranked below correctness bugs and not re-verified
  individually here.
- **`ensure_overlay`'s rebuild path now clears read-only file attributes
  before `rmtree` -- fixed this session, real and load-bearing, not
  theoretical.** The overlay is a full copy of the real git checkout at
  `z-Git\material-maker`; git marks `.git/objects/pack/*.idx` read-only,
  and `shutil.rmtree` can't delete a read-only file on Windows without
  help. Every rebuild (any `addons/mm_live` change) would have hit this.
  Fixed via a new `_clear_readonly()` helper in `overlay.py`, called right
  before `rmtree`. If you're ever tempted to remove it thinking it's
  unnecessary, don't -- it only reproduces against a *real* git checkout,
  not the synthetic fixtures most tests use, so its absence is easy to miss
  until the next real rebuild. If `live_start`/`connect_or_launch` ever
  fails again with a bare, detail-free MCP error, reproduce directly via
  `.venv\Scripts\python.exe -c "from mm_mcp import live; live.connect_or_launch()"`
  rather than trusting the MCP tool's error message -- it swallows
  exception detail on a raise; the real traceback only shows up outside it.
- **`ping`'s response now has a `has_graph` field alongside `ready`, and
  they mean different things -- don't conflate them.** `ready` is still
  purely "main_window resolved." `has_graph` (new this session) is "a graph
  tab actually exists" (`get_current_graph_edit()`/`.generator` non-null,
  same check the five mutating handlers already did). `connect_or_launch`
  requires both before declaring a session usable. Computed by a new
  `_has_active_graph()` helper in `live_server.gd`, placed right after
  `_cmd_ping`. The five mutating command handlers were deliberately left
  unchanged -- their own `graph_edit == null` guards are now normally
  unreachable defense-in-depth, not dead code to clean up.
- **`connect_or_launch` now has THREE ways to give up, not two -- know
  which one you're touching.** (1) Genuinely still booting: `ping` never
  reports `ready: true` during the initial grace period -- falls through to
  the full `launch_timeout` main poll loop, unchanged from before this
  session. (2) Squatted port: `ping` never answers at all during the grace
  period -- fails fast with the pre-existing "occupied by an unresponsive
  process" message, unchanged. (3) **New this session:** responsive but
  graph-less -- `ping` reports `ready: true` at least once during the grace
  period but `has_graph` never follows -- fails fast within that same grace
  period (reusing `_SQUATTED_PORT_GRACE`, no new constant) with a message
  naming the instance as responsive and pointing at a stale/pre-upgrade
  addon or a genuinely tab-less instance. `_wait_for_ready_or_give_up`'s
  return contract grew a fourth value, `main_window_ever_ready`, to let
  `connect_or_launch` tell (1) apart from (3) -- read its docstring before
  changing the discriminator again. The "we launched this process
  ourselves" (fresh-launch) path is completely untouched by (3): it still
  waits the full `launch_timeout` for both `ready` and `has_graph`, no
  grace-period ambiguity, since there's no "maybe it's a stale addon"
  question for a process this session just spawned.
- **✅ Resolved this session: the readiness-race backlog item from last
  session is fixed and verified.** A real 4x back-to-back relaunch check
  (the same technique that originally found the bug) showed zero
  `"no active graph"` failures, versus 3-of-4 before the fix. See Current
  state and the two items above for the mechanism.
- **`server.py` now has four live MCP tools consuming `live.py`:**
  `live_start`/`live_get_graph`/`live_apply`/`live_render`, all going through
  a shared `_ensure_live_session(cfg, launch_timeout=60.0)` helper that
  calls `live.connect_or_launch` fresh every time. **Do not read
  `server._live_session` directly** to check on a launched process --
  always call `_ensure_live_session(cfg)` yourself, since the module global
  is meant as internal bookkeeping, not a public handle. It DOES correctly
  preserve a previously-launched process's handle across later attach-only
  calls now (fixed this session), but that's an implementation detail, not
  a contract to depend on from outside `server.py`.
- **`live_apply(ops)` dispatches via `_LIVE_OP_HANDLERS`, a dict keyed by
  `op["op"]`** (`"add_node"`/`"connect_nodes"`/`"set_param"`), stops at the
  first failing op, and reports a malformed op (not a dict, or missing a
  required key) as a data-shaped error rather than raising -- consistent
  with this project's "validation errors are data" convention. If you add a
  fourth op kind, add its handler to that dict and nowhere else.
- **`connect_or_launch`'s squatted-port grace period discriminates on
  whether `ping` ever answered at all during the grace window, not whether
  it reached `ready`.** This was a real bug this session: `ping` legitimately
  returns `ready: false` for far longer than the 5s grace period during a
  normal Material Maker boot (the addon's socket binds at project startup,
  well before `main_window` resolves), so gating on "ready in time" wrongly
  told Grayson to taskkill a healthy, booting instance. If you touch this
  logic again, re-read `_wait_for_ready_or_give_up`'s docstring in
  `live.py` before changing the discriminator back -- `ever_answered=True`
  (even with `ready=False`) must fall through to the patient main poll loop,
  not fail fast. Only a port that *never* answers a single valid ping during
  the whole grace window is treated as squatted.
- **✅ Fixed this session: `_terminate` now kills the GUI child process
  too.** It used to only call `process.terminate()` on the launcher's
  `Popen` handle, which left the spawned GUI child running (confirmed via
  `tasklist`/`wmic`: two orphaned `Godot_v4.7.1-stable_win64*.exe` processes
  after a real integration test passed and `close()` ran). Now runs
  `taskkill /F /T /PID <pid>` (kills the whole process tree) before the
  original terminate()/kill() sequence, which still runs after as a
  fallback. A test double with no real `.pid` attribute skips the taskkill
  call and falls straight to the fallback, so the existing fake-process
  tests needed zero changes. Verified manually against 4 real launches in a
  row (2 successes, 2 mid-test failures from the unrelated race below) --
  zero leftover Godot processes every time, versus 2 leftover every time
  before this fix.
- **✅ Fixed a later session: the gap below (readiness races ahead of graph
  tab creation) is resolved.** See the top of this section (`has_graph`,
  the three-way give-up split) for the actual mechanism now in place. Kept
  the original finding text below for the historical record of how it was
  found.
- `connect_or_launch`'s readiness check races ahead of the default graph
  tab's creation. `ping`'s `ready` field only checks `mm_globals.main_window
  != null`; it doesn't check whether `get_current_graph_edit()` (and its
  `generator`) actually exist yet. `add_node`/`get_graph`/etc. all
  independently check `graph_edit == null or graph_edit.generator == null`
  and return `{"ok": false, "error": "no active graph"}` when that race
  loses. Reproduced 3 times in a row this session (after 1 clean pass
  earlier the same day), confirmed pre-existing and unrelated to the
  `_terminate` fix via `git stash` against the untouched code.
- **`addons/mm_live/live_server.gd` now answers all five commands:**
  `ping`/`get_graph` (read-only, from step 2) plus `add_node`/`connect_nodes`/
  `set_param`/`render` (mutating, from this session). Still deliberately
  thin -- no validation logic anywhere in this file; everything mutating
  arrives pre-validated from the Python side by design. Lazy `main_window`
  resolution -- never cache it, resolve fresh inside every command handler.
  **Two node-addressing conventions coexist and must not be confused:**
  `do_connect_node` (used by `connect_nodes`) addresses the GraphEdit's own
  scene tree, where node names are `"node_" + generator_name` -- the handler
  prefixes this internally. `set_node_parameters` (used by `set_param`)
  takes a **generator**, not a GraphNode, resolved via
  `graph_edit.generator.get_node(NodePath(name))` with the **plain** name,
  no prefix. The wire protocol only ever exposes plain names either way.
- **`render`'s handler calls `graph_edit.get_material_node()` then
  `material_node.export_material(prefix, profile, 0, true)` directly --
  NOT `main_window.export_material(...)`.** That was the original approach
  and it shipped, passed review, and was wrong: `main_window.export_material`
  has no `await` in its own body, so awaiting it resolves same-frame while
  the real file-writing coroutine keeps running in the background,
  unobserved. If you're ever touching this handler again, don't revert to
  the `main_window` wrapper without re-reading the plan's "Verified against
  Material Maker source" section (the corrected entry, not the original).
- **No automated GDScript test harness exists in this repo.** Both real
  bugs this session (the `:=`/`=` parse error, the un-awaited render call)
  passed clean task-level reviews because no reviewer could actually execute
  the script -- only the real integration test caught them. Godot 4.7.1 does
  support `--headless --check-only --script <path>` against the built
  overlay as a cheap parse-only smoke check (confirmed by the final review);
  it would catch a parse error like the first bug but not runtime-semantics
  bugs like the second. Worth adding as cheap insurance, not a substitute
  for the integration test.
- **New module: `src/mm_mcp/live.py`.** `ping()`/`get_graph()` are one-shot
  connect/send/recv/close calls (`_send_command`), no persistent session
  state on either side. `add_node`/`connect_nodes`/`set_param` each validate
  the proposed mutation against `_ensure_catalog(cfg)` (a module-level cache
  keyed by `cfg.nodes_dir`) via `validate_graph` before calling
  `_send_command` -- on any `"error"`-severity problem (or, for `set_param`
  specifically, an unrecognized-parameter warning scoped to that node), the
  socket is never touched. `render(basename, profile, cfg, ...) -> RenderResult`
  reuses `render.py`'s own `RenderResult`/`_collect_fresh_images` rather than
  reimplementing freshness detection. `connect_or_launch(cfg=None, host=LIVE_HOST,
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
  Fast suite: `pytest -q -m "not integration"` (174 passed, 6 deselected).
  `pytest -q` adds the Godot-launching integration tests; the squatted-port
  hardening fixed this session should make running multiple integration
  tests in one process more reliable than before, but this hasn't been
  stress-tested specifically -- if you hit a port-race-shaped flake again,
  check the GUI-child-process-leak item above first (a leaked prior-test
  process squatting the port is a plausible new cause), then fall back to
  running integration tests individually (`-k build_and_render`,
  `-k default_new_material`, `-k live_tools_hold_a_real_session`) for a
  clean signal.
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

> 📦 **Trim convention (adopted 2026-08-29):** this doc keeps at most the 3
> most recent "Changed this session" write-ups and the 5 most recent
> session-log entries below. When a new wrap-up entry would push either
> section past that cap, the oldest entry moves out verbatim (no
> summarizing) into [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md)
> instead of letting this doc grow unbounded -- flagged as a real pickup
> cost by the 2026-08-29 teardown (Maintainer lens). **26 older entries are
> now archived there**, from the 2026-08-29 pre-release-audit session back
> through the project's Phase 1-2 kickoff on 2026-08-25.


### 2026-08-30 (Phase 4 hardening) — path bounding + inspect_project + CI/release-please, from a project compare
- Grayson asked to compare us against `github.com/dcc-mcp/dcc-mcp-material-maker`.
  Verdict: same name, different product (theirs is a locked-down headless
  export/inspection adapter; ours authors graphs). Borrowed three of its rigors.
- Ran `brainstorming` → architectural. Grayson chose opt-in path bounding, full
  release-please, `inspect_project` as path-in/metrics-out. Wrote spec + plan,
  then executed 10 tasks via `subagent-driven-development` (per-task spec+quality
  review, whole-branch final review on Opus = APPROVE FOR MERGE).
- Probed two blowup risks before writing YAML: fast suite needs the MM checkout +
  a stub Godot binary on a bare runner (first "no clone" read was wrong, the repo
  `.env` masked it); `main` was already clean with the render-timeout fix merged.
- Items: opt-in `MM_ALLOWED_ROOTS` bounding + always-on traversal guard;
  `inspect_project` tool #10; `test.yml` CI (green first run); release-please
  (seeded to cut 0.4.0); `__version__` via `importlib.metadata`. Fast suite 260.
- Merged `phase4-hardening` → `main` (`d23b235`), verified merged tree, pushed.
  Push needed a one-time `gh auth refresh -s workflow` (workflow files are
  separately permissioned). CI passed; release-please got to the 0.4.0 release
  branch + version-bump commit but failed to open the PR (repo "Actions may
  create PRs" setting still off — Grayson handling later).
- Wrote `_agent-commons\log\2026-08-30-claude-code-mm-mcp-phase4-hardening-spec.md`
  and `...-phase4-hardening-implemented.md`.

### 2026-08-29 (README images) — 3D-preview hero + gallery + cookbook sheet, social-preview fix
- Picked up via `pickup` with Grayson's ask: nicer front-page images. Found
  drift: `origin/main` was 2 commits ahead (the render-timeout fix had merged
  after the prior wrap); fast-forwarded local cleanly first.
- Ran `brainstorming` → bounded. Grayson chose "hero + 3D gallery," "keep 4
  columns," "render hero finalists I choose," and "swap the dark metals for
  other mats." Rendered 8 gallery previews + 2 replacements sequentially via a
  scratch script against `mm_mcp.render`/`preview`; sent contact sheets each
  pass and iterated. Learned pure metals render near-black in the preview scene.
- Grayson asked to feature his own brick: rendered
  `saved_graphs/bricks_grayson_edit.ptex` (an irregular mossy cobblestone) and
  swapped it into both the hero triptych and the gallery as a round-trip example.
- Wired README: hero at top, 4-col 3D gallery, collapsible "Material cookbook"
  section with a 4×7 sheet of all 28 cookbook materials. Committed `d7f2659`,
  pushed, verified images serve HTTP 200.
- Grayson flagged the GitHub topic-card social preview showed cropped title.
  Root cause: topic cards crop the 1280×640 to ~2.74:1. Lifted the text into
  the safe zone and swapped his brick into the tile grid (`738e10b`), then
  uploaded the new `docs/social-preview.png` via repo Settings → Social preview
  through his Chrome (the card is set in the web UI, not from the repo file).
- Wrote `_agent-commons\log\2026-08-29-claude-code-materialmaker-mcp-readme-front-page-images.md`.

### 2026-08-29 (render timeout fix) — killed the process-tree leak behind the render-orphan cascade
- Worktree session on branch `claude/confident-tesla-ee9400`. Task: fix the
  latent process-leak in `render.py`'s `_run_godot` timeout path, the root cause
  of the `render-orphan-contention` cascade the debug-swatch session had flagged
  and spawned `task_93dccd69` for (this is that task).
- Ran `systematic-debugging`/advisor first. Confirmed the crux: `subprocess.run`'s
  timeout kills only the direct child before re-raising, so a later `taskkill /T`
  on the (now dead, possibly recycled) launcher PID can't tree-walk to the
  orphaned grandchild — the kill MUST happen while the launcher is alive, which
  forces `Popen` + `communicate()` over `subprocess.run`.
- Implemented a shared `render._kill_tree(process)` (`taskkill /F /T /PID`, pid
  guard, swallowed failure) and rebuilt `_run_godot` on `Popen`; routed
  `live.py`'s `_terminate` through the same helper (dedup, live→render import
  only). Hardened the post-kill reap with a 10s timeout so a surviving
  grandchild holding the pipe can't hang the loop.
- Verified empirically against real Godot: forced a timeout → `_GodotTimeout`,
  zero leftover Godot, next `render()` succeeded. Directly reproduced the
  mechanism — `tasklist` mid-render showed two real GUI processes outside the
  launcher, one frozen at ~6,376 K (the memory's ~6MB single-instance signature)
  followed by a hang; recovered via TaskStop + taskkill all Godot.
- Ran `/code-review` (medium): 2 PLAUSIBLE findings, both `no_change_needed`
  after analysis. Added a hardening round earlier (bounded reap) with its own
  test. Fast suite: 232 passed, 21 deselected.
- Updated the `render-orphan-contention` memory + `MEMORY.md` index (was marked
  still buggy). Wrote `_agent-commons\log\2026-08-29-claude-code-render-timeout-killtree-fix.md`.
- Committed `cd1fcb9`, then merged to `main` alongside the concurrent
  debug-swatch wrap-up `e6eb4c0` (which had independently trimmed the same two
  baton entries — reconciled by hand so both sessions survive). Pushed to
  `origin/main`.

### 2026-08-29 (debug swatch gallery) — built both phases + a relief shapes/text family
- Picked up via `pickup` (clean, `main` at `c9934a7`, in sync). Grayson chose
  next-move #1: his own backlog "debug materials / visual smoke-test swatches"
  idea.
- Ran `brainstorming` → bounded. Grayson's "both, phased" call: build the
  visual gallery now, add the automated-assertion layer as phase 2. Picked all
  four candidate diagnostics for the first cut.
- **Phase 1** (`a0d7674`): `quality/debug_swatches.py` — 6 single-node swatches
  (voronoi port0 polarity, port0/1/2 fields+random, UV direction, relief dome)
  + `docs/DEBUG_SWATCHES.md`. Followed visual-iteration: render, `SendUserFile`,
  judge relief in 3D. The UV swatch corrected my guess — MM's +V points DOWN.
- **Phase 2** (`ba3d968`): `PIXEL_CHECKS` + `tests/test_debug_swatches.py`
  render each swatch live and assert calibrated pixel invariants. Grayson chose
  a vendored ~60-line stdlib PNG reader (`quality/pngread.py`) over Pillow.
  Calibration corrected a second assumption: red centers out-area blue seams, so
  `red > blue` is the polarity-flip detector.
- Grayson then asked for more relief shapes AND text. **Relief family**
  (`ab688e6`): `relief_circle` (strict dome-out check kept), polygon, star,
  rays, and `relief_glyph` spelling "UP" from two `sixteen_segment` glyphs
  (MM has no text node) scaled/translated/unioned. The glyph's thin strokes
  needed a full-buffer scan (a sparse grid walked past them). All 14
  debug-swatch tests pass (93s), fast suite 229.
- **Detour:** hit a render death-spiral from overlapping render jobs; root-
  caused a real latent `render.py` bug — it leaks a Material Maker self-relaunch
  child on a 180s timeout, cascading into hangs (same class `live.py` already
  fixed). Recovered by killing all Godot and rendering sequentially; captured
  in the `render-orphan-contention` memory; spawned `task_93dccd69` to fix it
  (running in its own session). Left `render.py` untouched here to avoid a
  conflict.
- Wrote `_agent-commons/log/2026-08-29-claude-code-materialmaker-mcp-debug-swatches.md`.
  3 commits pushed at wrap.

### 2026-08-29 (leather cookbook) — new leather category, 6 materials, 2 reusable levers
- Picked up via `pickup` (clean, `main` at `969d420`, in sync). Grayson chose
  next-move #1: author a new cookbook category. Picked leather (backlog B).
- Built 6 leather recipes in `quality/cookbook_leather.py`, each a distinct
  lever on the `crocodile_skin` donor. Followed the visual-iteration workflow
  throughout: render flat + 3D `render_preview`, `SendUserFile` the previews
  every pass, judge relief in 3D, ask before continuing.
- Reworked three from honest misses rather than shipping them: l02's first
  wear mask made cow-hide blobs (fixed with finer/softer/lower-contrast perlin
  + threshold); l04's bronze was landing on the thin voronoi borders not the
  scale bodies (albedo-polarity flip); l05's intended `shape`+`tiler` stitch
  dashes failed (no visible dashes; isolating the tiler output timed the
  renderer out at 180s) so it became a `pattern`-sine quilt.
- Grayson then queued: push, tweak l04, add a 5th "stitched". Did all three,
  plus chased real stitches into l06. l06's `pattern` Square×Square grid works
  but its polarity is inside-out (dash rectangles are the pattern's LOW cells);
  one reversed sharpen colorize fixed colour + flattened field at once. l06
  dashes render raised and cream in 3D (bold, full-grid, not fine seam-lines).
- Two general levers written into `docs/AUTHORING.md` as the real keep-value:
  `_dome_the_cells` (voronoi-port-0 height-ramp flip; Grayson caught the
  inside-out grain in 3D) and the stitch-generator hunt (shape+tiler trap vs.
  pattern polarity). Captured Grayson's new "debug materials / visual
  smoke-test swatches" idea to `_agent-commons/ideas/`.
- 3 commits pushed (`5f1a27b`, `6915fc8`, `f55359a`); `origin/main` in sync.
  Wrote `_agent-commons\log\2026-08-29-claude-code-materialmaker-mcp-leather-cookbook.md`.
  No integration/gate changes (informal cookbook growth).

_(Older entries continue in [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).)_

