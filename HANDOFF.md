# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-29 (cleanup session) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**This session cleared the rest of the pre-release code-review debt and
finished the teardown's cleanup theme.** Resolved 6 of the 8 remaining
code-review findings (3-10) and documented 2 as deliberate non-changes with
primary-source reasons, then ran 4 teardown-blessed cleanup passes: killed
the dead `Graph` class and deduped three repeated helper snippets into shared
helpers (`_snapshot_pngs`, `_run_godot`+`_log_tail`, `_first_albedo`). Every
change was test-first or behavior-preserving under existing tests. Fast suite
**226 passed** / 10 deselected (up from 214 at pickup). **All 5 code commits
plus the wrap-up doc commit are pushed** (`c65cc83`, `13c7490`, `9726a59`,
`19427a7`, `f436300`, `c5b0cfb`); `origin/main` confirmed in sync (`0 0`).
Older history beyond the 3 write-ups / 5 log entries kept here lives in
[docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).

## 📌 Where we stopped

Wrapped cleanly, nothing mid-task, everything pushed and in sync. The only
untracked file is the long-flagged
`docs/images/contact-sheet-wood-stone.png` (kept deliberately out of every
commit this session; see Open questions).

## ▶️ Next concrete step

Nothing pending on the code side. The open backlog, unchanged:
- **2 findings ruled out, not fixed** (deliberate): #8 (`_cmd_clear_graph`'s
  guard is correct — `new_material()` creates the generator, doesn't read
  one) and #10 (`generic_size or 1` coercion is safer than passing an
  explicit 0). Both annotated in-code. Findings 3-7 and 9 are fixed.
- **`list_node_types` tool decision** — the teardown flagged it as redundant
  with the `catalog://nodes` resource + `describe_node`. It's a live, tested
  MCP tool, so removing it is a product call, not dead code. Undecided.
- **The untracked contact-sheet PNG** — add it or gitignore it, still open.
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
- **Still open, flagged a fourth session running now:** `docs/images/contact-sheet-wood-stone.png`
  is still untracked. Just decide next time `docs/images` is touched instead
  of re-flagging it again.
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

## 🗂️ Changed this session (remaining code-review findings + teardown cleanup)

- Branch: `main`. Committed and **pushed**: `c65cc83` (6 fixes + 2 documented
  non-changes), `13c7490` (kill dead `Graph` class), `9726a59` (dedupe the
  PNG-snapshot loop), `19427a7` (share the Godot retry loop + log-tail across
  render/preview), `f436300` (extract `_first_albedo`). No plan doc, no
  worktree — scoped fixes plus behavior-preserving refactors, each test-first
  or covered by existing tests, matching this project's precedent for
  well-scoped work this size.
- Decisions (+ why): took the advisor's split-by-verifiability framing. Did
  the mechanical fixes (#4 negative port, #9 fd leak, #3 atexit) and the
  judgment calls (#7 30s mutation timeout, #5 overlay cleanup, #6 log_tail
  docstring), but ruled out #8 and #10 as non-bugs with primary-source
  reasons rather than forcing 8 changes for an 8-item list. #8:
  `new_material()` creates the generator (confirmed in `graph_edit.gd:690-724`),
  so the guard is correct as-is. #10: an explicit `generic_size: 0` would
  build a broken input-less node, so the `or 1` coercion is the safer
  behavior. On cleanup, killed the dead `Graph` class (only self-tested,
  teardown Kill verdict) and deduped the three repeated helper snippets the
  teardown flagged into `_snapshot_pngs` / `_run_godot`+`_log_tail` /
  `_first_albedo`. The retry/timeout behavior had NO coverage before, so that
  dedup added 4 characterization tests that also fill the gap. Process note: a
  `git add -A` slip swept the untracked contact-sheet PNG into `c65cc83`;
  caught and removed via `git rm --cached` + amend (both amends local,
  pre-push). Fast suite: 226 passed (up from 214), 10 deselected.

## 🗂️ Changed this session (backlog item I: reposition_node, rename ruled out)

- Branch: `main`. Committed and pushed: `352317a`. Changed:
  `src/mm_mcp/live.py` (`reposition_node`), `src/mm_mcp/server.py`
  (`reposition_node` as a 5th `live_apply` op), `addons/mm_live/live_server.gd`
  (`_cmd_reposition_node`), `tests/test_live.py`, `tests/test_server_live.py`
  (2 unit tests + 1 real integration test), `HANDOFF.md`, `STATUS.md`,
  `docs/HANDOFF_ARCHIVE.md`. No plan doc, no worktree; direct TDD on `main`,
  matching this project's precedent for well-scoped additions this size.
- Decisions (+ why): built the reposition half of item I but deliberately
  ruled OUT the rename half as unsupported, not just undone. Checked
  Material Maker's own `graph_edit.gd:undoredo_command` -- the exhaustive
  dispatcher for every graph mutation the GUI itself can perform
  (add/remove/update/setparams/setgenericsize/setseed/setminimized/
  move_generators/resize_comment/node_color_change) -- and found no rename
  case at all, and no "Rename" context-menu action anywhere in the codebase
  for an ordinary graph node (only portal links and library items get one).
  Renaming a generator's `Node.name` directly would work in isolation, but
  the corresponding `GraphNode` (addressed as `"node_"+name"` by
  `connect_nodes`/`disconnect_nodes`/`set_param`) would desync, and Godot's
  own built-in `GraphEdit` keeps its connection list keyed by node name
  too -- reimplementing a rename by hand risks corrupting either, with no
  upstream precedent for doing it safely. Reposition is safe by contrast:
  it reuses `do_set_position` (`minimal.gd`), the exact call
  `move_generators`'s own undo/redo handler makes, whose `_on_offset_changed`
  callback already writes the new position back onto the generator (not
  just the on-screen `GraphNode`), so `get_graph`/serialize reflects the
  move. Proven with a real integration test (`test_live_apply_reposition_node_moves_a_real_node`)
  that adds a node, repositions it, and reads the graph back to confirm the
  new `node_position` -- not just that the handler was written correctly on
  paper, matching this project's "no automated GDScript test harness, only
  a real launch proves it" precedent. Zero leftover Godot processes after
  the integration run. Fast suite: 214 passed (up from 211), 10 deselected.

## 🗂️ Changed this session (backlog item K: the two worst live-control bugs)

- Branch: `main`. Committed and pushed: `12a4be3`. Changed: `src/mm_mcp/server.py`
  (`live_render_node_output` now checks the restore call's own success;
  `live_apply`'s op-handler exception tuple grew `AttributeError`),
  `tests/test_server_live.py` (4 new tests), `STATUS.md`, `HANDOFF.md`. No
  plan doc, no worktree — both bugs were already diagnosed with exact line
  numbers and root causes from the prior session's code review, so this was
  direct TDD on `main`, matching this project's own precedent for
  well-scoped fixes this size.
- Decisions (+ why): a failed restore now reports `ok=False` rather than
  being silently swallowed, since the live graph staying wired to a
  temporary preview connection is exactly the kind of state a human
  watching the live window needs to know about — but the render's own
  image is still attached when the render itself succeeded, since losing
  that real result to a separate, unrelated restore failure would throw
  away useful output. `live_apply`'s fix was the narrowest correct change
  (add `AttributeError` to the existing tuple) rather than broadening to a
  bare `except Exception`, matching this project's existing precise/narrow
  exception-handling style rather than papering over unknown failure modes.
  Wrote all 4 new tests first and confirmed each failed against the
  pre-fix code (red) before implementing, per `test-driven-development`.
  Fast suite: 211 passed (up from 207), 9 deselected.

> 📦 **9 older "Changed this session" write-ups archived** (through
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
> cost by the 2026-08-29 teardown (Maintainer lens). **23 older entries are
> now archived there**, from the 2026-08-28 Unity-export session back through
> the project's Phase 1-2 kickoff on 2026-08-25.


### 2026-08-29 (cleanup) — resolved the remaining code-review findings, then 4 teardown cleanup passes
- Picked up via `pickup`; no drift, `main` at the prior session's `1368115`,
  `origin/main` in sync, 214 passing (only untracked file the long-flagged
  contact-sheet PNG).
- Grayson picked next-move #1: fix the 8 remaining code-review findings
  (3-10). Ran an advisor consult first; it recommended splitting by
  verifiability and flagged #7/#5/#6 as judgment calls and #8/#10 as likely
  non-bugs. Followed that.
- Answered the two blocking file questions before touching code: `live_apply`
  passes no timeout (so mutations inherit the 5s default — #7 is real), and
  `new_material()` CREATES the generator via `clear_material()`→`create_gen`
  (so #8's suggested guard is wrong — read `graph_edit.gd:690-724`).
- Fixed 6 findings test-first (red confirmed): #4 negative port index, #9
  `_launch_overlay` fd leak, #3 atexit handler (verified it fires at real
  interpreter shutdown), #7 30s mutation timeout, #5 overlay cleanup-on-fail,
  #6 log_tail docstring accuracy. Documented #8 and #10 as deliberate
  non-changes with in-code reasons. Committed `c65cc83` — and caught a
  `git add -A` slip that swept the untracked PNG in, removed it via
  `git rm --cached` + amend (both amends local, pre-push).
- Then, on Grayson's "keep going", ran the teardown's cleanup theme across 3
  more rounds: killed the dead `Graph` class (`13c7490`, only self-tested,
  rebuilt its test fixture as a plain dict), deduped the PNG-snapshot loop
  (`9726a59`, dup pair 1), and shared the Godot retry loop + log-tail across
  render/preview (`19427a7`, dup pair 2 — added 4 characterization tests for
  the previously-untested retry/timeout behavior). On "one more cycle then
  wrap up", extracted `_first_albedo` (`f436300`, dup pair 3).
- All 5 commits (plus the wrap-up doc commit) were pushed at end of session
  once Grayson said "push + /wrap". Fast suite ended at 226 passed (up from
  214), 10 deselected. No integration runs this session (all changes
  unit-level or behavior-preserving refactors), so zero Godot processes
  spawned.
- Wrote/updated the `_agent-commons\log\` entry
  (`2026-08-29-claude-code-materialmaker-mcp-remaining-review-findings.md`).

### 2026-08-29 (later) — fixed the top 2 code-review bugs, trimmed HANDOFF.md, closed backlog item I
- Picked up via `pickup`. No drift: `main` matched the prior session's
  `d0df55b`, `origin/main` in sync, working tree clean except the
  long-flagged untracked `docs/images/contact-sheet-wood-stone.png`.
- Grayson said he liked all three of the prior session's proposed next
  moves (K, L, M) and was fine with any order, so this session did all
  three. Also raised a new, unscoped idea: a simplified "Material Maker for
  dummies" interface, since the real node graph can be intimidating to a
  non-technical viewer. Logged it as backlog item N in
  `_agent-commons/ideas/Tool-MaterialMaker-MCP.md` verbatim rather than
  designing anything, since it's explicit backlog wanting its own
  `brainstorming` session, and flagged a possible tension with
  `docs/NORTH_STAR.md`'s round-trip-learning-tool framing worth checking
  first.
- **K:** fixed the two worst live-control correctness bugs via direct TDD
  on `main` (both already diagnosed with line numbers from the prior
  session's code review). `live_render_node_output` now checks whether
  restoring the original wiring after a preview actually succeeded, instead
  of silently reporting success while the live graph stayed wired to the
  temporary connection. `live_apply` now also catches `AttributeError` from
  a malformed op (alongside the existing `KeyError`/`TypeError`), since a
  list where a parameters dict was expected could raise uncaught deep
  inside `validate_graph`. 4 new tests, all written and confirmed red
  before the fix. Committed `12a4be3`.
- **L:** adopted a HANDOFF.md trim/archive convention. The doc had grown to
  1840 lines with no cap, flagged by the prior session's teardown. Moved 8
  older "Changed this session" write-ups and 22 older session-log entries
  verbatim into a new `docs/HANDOFF_ARCHIVE.md`; this doc now keeps only
  the 3 most recent write-ups and 5 most recent log entries, documented as
  a standing convention in both this doc and `CLAUDE.md`. Also fixed a
  stale `-t`-vs-`--target` flag in `CLAUDE.md`'s manual render example
  while in there. Committed `cb47010`.
- **M:** asked Grayson directly (via a structured question, not a coin
  flip) whether to keep growing live-control's mutation surface given the
  teardown's sunk-cost flag. He said keep building it, so picked up backlog
  item I. Investigated Material Maker's own source before writing any
  GDScript: its undo/redo command dispatcher
  (`graph_edit.gd:undoredo_command`) has a `move_generators` case (reuses
  `do_set_position`, which also writes the new position back onto the
  generator, not just the on-screen node) but genuinely no rename case
  anywhere for an ordinary node -- confirmed this isn't a gap in the addon,
  it's unsupported by Material Maker itself, since faking a rename by hand
  would risk desyncing the addon's `"node_"+name` addressing and Godot's
  own built-in connection bookkeeping. Built `reposition_node` as a new
  `live_apply` op reusing the same verified-safe call, proven with a real
  integration test that adds a node, moves it, and confirms the new
  position via `get_graph`. Ruled the rename half out explicitly rather
  than leaving it as a silent gap. Committed `352317a`.
- Pushed all three commits after confirming `origin/main` sync
  (`git rev-list --left-right --count` → `0  0`).
- Wrote and pushed the required `_agent-commons\log\` entry
  (`2026-08-29-claude-code-materialmaker-mcp-bugfix-trim-reposition.md`),
  scoped to just this session's own new files since the commons repo had
  other agents' pending work sitting uncommitted.
- Fast suite: 214 passed (up from 207 at pickup), 10 deselected. Zero
  leftover Godot processes after the two real integration runs (item K's
  restore-failure tests were unit-level; item I's reposition test launched
  a real overlay).

### 2026-08-29 — pre-release audit, code review, adversarial teardown, doc-accuracy fixes
- Grayson asked whether the project was ready to post for external alpha
  testers. Ran a live test-suite check (207 passed / 9 deselected, matched
  the existing 216 figure, no drift), then an 8-angle code review across
  `src/mm_mcp/*.py` + `addons/mm_live/live_server.gd` (finder agents +
  1-vote verification per candidate) via `code-review` at high effort, then
  a docs-vs-code coherence audit (README, NORTH_STAR.md, PLAN.md, STATUS.md,
  AUTHORING.md, CLAUDE.md against the real code). Reported 10 verified
  correctness findings — see Heads-up above for the full list, none fixed
  yet.
- Answer to the readiness question: ready for a small, hand-picked Windows
  alpha test, not a public/broad post — cross-platform is completely
  unverified, setup is nontrivial, no PyPI, zero external users so far. Full
  reasoning given in chat.
- Grayson then ran `/teardown`: a 6-lens adversarial review (Architect,
  Maintainer+6mo, Red team, Newcomer, Economist, Simplifier), each an
  independent agent with a steelman-then-attack structure, informed by
  fresh evidence gathered directly (git log, directory sizes, tracked vs.
  gitignored footprint, commit-date histogram). Headline: the core (Phases
  0-3, the `quality/` harness) is close to what a from-scratch rebuild would
  produce; live-control absorbed 39% of commits and 49% of test lines for a
  workflow used once for real and bypassed that once; the project's own
  vision docs (NORTH_STAR.md, PLAN.md) misdescribed the shipped live-control
  feature as unbuilt; STATUS.md's own two tables disagreed with each other
  about it. Full report (Rebuild Question, all 6 lenses, verdict table, v2
  sketch, one-change recommendation) delivered to Grayson as a file via
  `SendUserFile` — not committed to this repo, since it's a point-in-time
  review artifact, not project documentation.
- Grayson said to trust my judgment and start whichever fix made sense.
  Picked the documentation-accuracy pass over the two alternatives (fixing
  the two worst live-control bugs, or a HANDOFF.md baton cleanup) as the
  highest clarity-per-hour move and the one most directly tied to the
  original readiness question — a false doc claim misleads every reader
  today, the code bugs need specific conditions to surface. Fixed every
  concrete false/stale claim the teardown found (see the Changed-this-session
  block above for the full list and reasoning). Verified: fast suite still
  207 passed after the edits (docs/config only). Committed `1fb0d45`.
- Wrote and pushed `_agent-commons\log\2026-08-28-claude-code-materialmaker-mcp-teardown-and-doc-fixes.md`,
  scoped to just that file (see commit note above).
- Grayson then ran `/wrap-up + push`. Pushed `1fb0d45` directly (`git push`,
  local session with the real working tree — the `github-push` clone-and-
  reapply flow doesn't apply here). Confirmed `origin/main` in sync. Updated
  project memory (`phase5-live-control-design.md`, `public-alpha-status.md`,
  a new `teardown-2026-08-29-audit-findings.md`, `MEMORY.md` index) and this
  handoff doc's top sections + Heads-up + a new "Changed this session" block,
  per this skill's own convention.

### 2026-08-28 (later still) — render_node_output + live_render_node_output, backlog item H
- Picked up via `pickup`; no drift, `main` matched the prior session's
  `f6e3edb`, in sync with `origin/main`.
- Grayson asked for two quick housekeeping fixes first: revert the upstream
  `z-Git\material-maker` checkout's `bricks.ptex` back to pristine (his real
  edit was already safely copied into `saved_graphs/`), and move his own
  `examples/g01-natural-stone/` GUI save into `saved_graphs/` since he
  confirmed that's the natural-stone variant he actually wants kept.
  Renamed it to `natural_stone_grayson_edit.ptex` to match the bricks
  convention. Committed separately (`b85a55f`) before the main feature.
- Then built backlog item H (`render_node_output`) via `brainstorming`
  (classified bounded — the render/validate/catalog flow it composes
  already exists) → `test-driven-development`. Read `graph.py`/`render.py`/
  `server.py`/`catalog_builder.py`/`validator.py` first, then confirmed the
  real `material` node's input order (`albedo_tex` is port 0) via
  `describe_node` and the real `bricks` example graph, rather than assuming.
- Grayson asked for both batch and live-mode in the same pass. Checking the
  live protocol for feasibility surfaced real hidden complexity before any
  code was written: Material Maker's own `connect_children` (verified
  directly in the `z-Git\material-maker` source) already disconnects
  whatever fed a port before wiring a new one, so restoring by reconnecting
  the original source works — but only if the port started out connected to
  something. There was no `disconnect_nodes` primitive to restore
  "unconnected" when it didn't. Surfaced this to Grayson as a real scope
  question (three options: add the primitive now, refuse that one case,
  drop live-mode from this pass) rather than silently deciding, per
  `brainstorming`'s "hidden complexity upgrades the path" rule — he chose to
  add it now.
- Confirmed `do_disconnect_node` already exists in Material Maker's own
  `graph_edit.gd`, mirroring `do_connect_node` exactly (found by reading the
  real source, not assumed), which meant the new op was a straightforward
  addition rather than inventing a new mechanism.
- Presented the full design (batch path, live path, testing plan) in chat
  per `brainstorming`'s bounded-path requirement; Grayson approved with "go
  for it."
- Built via strict TDD, one unit at a time, watching each fail for the
  right reason before implementing: `graph.py`'s `find_material_node`/
  `isolate_node_output` (pure, 8 new tests), `server.py`'s
  `render_node_output` (5 new tests + 1 real integration test against the
  bundled `bricks` example), `live.py`'s `disconnect_nodes` (2 new tests),
  the GDScript `_cmd_disconnect_nodes` handler (no unit harness exists for
  GDScript in this repo — only provable via integration test), `server.py`'s
  `live_render_node_output` and the `disconnect_nodes` `live_apply` op (7
  new tests) — then one dedicated real integration test, deliberately
  designed so the preview node starts with no existing `albedo_tex`
  connection, forcing the disconnect-restore branch specifically (the
  actual new GDScript code), not the already-proven reconnect branch.
- Full suite: 216 passed (up from 187), confirmed zero leftover Godot
  processes afterward via `tasklist`.
- Updated `README.md`'s tool tables (9 batch + 6 live tools now, was
  stale by one entry already — `live_clear` was missing from the Live mode
  table before this session, fixed in the same edit) and `STATUS.md`'s
  Components rows for `server.py` and the live-control stack.
- Committed as `f891fbb`. Wrote a `_agent-commons/log/` entry, committed and
  pushed it directly (not via `Push-Repo`, since that helper's `git add -A`
  would have swept in an unrelated modified `dashboard/index.html` and
  dozens of other agents' pending log entries sitting uncommitted in that
  repo — staged and pushed only this session's own file instead).
- Grayson asked to push and wrap up. Pushed both commits (`git push`,
  direct — this is a local session with the real working tree, not a
  Cowork/cloud session, so the `github-push` skill's clone-and-reapply flow
  doesn't apply here). Confirmed `origin/main` in sync.

### 2026-08-28 (even later) — saved_graphs/ round-trip: version control, rename, moss
- Continuation of the same session, after the Unity/--target work below was
  pushed. Grayson had tweaked `bricks.ptex` live in the GUI window launched
  at the end of the previous thread and asked, in one rambling but clear
  message, for four things: version control the change, a screenshot,
  organized/labeled controls, and moss in the crevices.
- Checked the upstream `z-Git\material-maker` checkout: Grayson's Ctrl+S
  had saved directly into it (`git status` showed a real diff), exactly
  the "pristine, don't modify" file this project's CLAUDE.md warns about.
  Copied the edit out to a new `saved_graphs/` folder rather than editing
  in place, establishing it as the convention for Grayson's own saved work
  going forward.
- Screenshot: tried computer-use directly. `request_access(["Material
  Maker"])` granted at full tier (per `computer-use-tiers`, a native app's
  own window, not the taskbar surface, so full tier was expected), but the
  window itself never appeared in a screenshot. Diagnosed properly rather
  than guessing: `open_application` failed (the running process was
  launched directly by path, not through the Steam-registered app entry
  the grant matched), then found via a PowerShell `Get-Process`/Win32 check
  that the window was minimized (`IsIconic: True`) at an off-screen
  position. Restored and foregrounded it via `ShowWindow`/
  `SetForegroundWindow`, but a `computer_batch` key press then errored
  "Godot_v4.7.1-stable_win64 is not in the allowed applications", proving
  the raw process is a different identity than the granted Steam-app entry
  no matter what state it's in. Tried `request_access` again with three
  plausible raw-process names; all came back "not installed" (the request
  wasn't even shown to Grayson). Recognized this as the tiers skill's
  genuinely-blocked case, not a "try harder" one, and handed the actual
  screenshot to Grayson to take himself.
- Read the saved graph directly (17 nodes) rather than guessing at what to
  rename: traced every connection back through `describe_node('material')`
  and `describe_node('blend')` to get the real input port names/order
  (`albedo_tex`/`metallic_tex`/`roughness_tex`/`normal_tex`/`ao_tex`/
  `depth_tex`, `blend`'s `s1`/`s2`/`a` mask ports), and checked
  `blend_type`'s enum values directly rather than assuming what mode 7
  meant (it's "Burn"). Built a full role map for all 16 top-level nodes
  from that (e.g. `colorize_2` → `BrickMortarMask`, `blend_1` →
  `BrickColorVariationMask`) before touching anything.
- Grayson clarified he wanted the offline/file-side path, not live
  injection, after asking a genuine "how does this actually work"
  question. Answered honestly rather than picking one silently: explained
  both mechanisms, and surfaced that live mode currently can't rename or
  reposition existing nodes at all (only add/wire/set-params), which ruled
  it out for the rename half regardless of preference.
- Wrote a one-off Python script (not part of the repo, moved to the
  session scratchpad after use) to apply the rename map, add the moss
  nodes/connections, and recompute node positions by topological depth,
  rather than hand-editing ~500 lines of JSON where a missed connection
  reference would silently break the graph.
- First moss render came back with zero visible moss. Didn't assume the
  wiring was wrong; diagnosed it properly (`systematic-debugging` in
  spirit): rerouted the graph to output `MossMask` directly as albedo,
  confirmed it was solid black, then rendered `SurfaceDetailMask` (the
  mask's own input) the same way and histogrammed the PNG by hand (no
  numpy in the venv, used PIL's histogram directly) to find its real value
  range (40-231 of 255, not the 0-40 range the first threshold assumed).
  Retuned the gradient thresholds to match, re-rendered, moss appeared
  correctly in the crevices on the second attempt.
- Verified in both the flat albedo and a real `render_preview` 3D pass
  (sphere/cube/cutaway under lighting), per this project's own standing
  rule to judge relief/detail in 3D, not the flat swatch. Sent both to
  Grayson via `SendUserFile`, not just described.
- Grayson confirmed it looked good, then asked directly what should improve
  about the MCP based on everything this session surfaced. Answered with
  three concrete, session-evidenced gaps (not a speculative wishlist): no
  single-node-output rendering tool, `live_apply` can't rename/reposition,
  no way to load an existing `.ptex` into a live session. Recommended the
  first as smallest/highest-value. Grayson asked to log all three as
  backlog rather than build any of them now; added as items H/I/J in Next
  concrete step.
