# HANDOFF Archive — Tool-MaterialMaker-MCP

Older `HANDOFF.md` content, moved out to keep the live pickup doc scannable
-- flagged as a real, growing pickup cost by the 2026-08-29 teardown
(Maintainer lens). Not a separate baton; `HANDOFF.md` is still the one file
`pickup`/`wrap-up` read and write. This file is pure overflow, append-only.

**Convention (adopted 2026-08-29):** `HANDOFF.md` keeps at most the 3 most
recent "Changed this session" write-ups and the 5 most recent session-log
entries. At wrap-up, if writing a new entry would push either section past
that cap, move the oldest entry (or entries) out of `HANDOFF.md` verbatim
(no summarizing -- this is overflow storage, not a condensed history) and
append it here, newest-archived-first within each section, matching
`HANDOFF.md`'s own ordering. This file is never read at pickup by default;
dig into it only when you need detail on something older than the live
doc's window.

---

## Archived "Changed this session" write-ups

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
  Actions to create and approve pull requests" setting is still off. Wrote two
  `_agent-commons\log\` entries (spec + implementation).

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

## 🗂️ Changed this session (debug diagnostic swatch gallery, both phases)

- Branch: `main`. Committed (local, then pushed at wrap): `a0d7674` (phase-1
  visual gallery + `docs/DEBUG_SWATCHES.md`), `ba3d968` (phase-2 automated
  checks + vendored `quality/pngread.py` + `tests/test_debug_swatches.py`),
  `ab688e6` (relief `relief_*` family: circle/polygon/star/rays + "UP" glyph).
  New files: `quality/debug_swatches.py`, `quality/pngread.py`,
  `tests/test_debug_swatches.py`, `docs/DEBUG_SWATCHES.md`. No plan doc, no
  worktree; informal harness growth, no gate. Outputs (`quality/authored`,
  `quality/cookbook`) gitignored.
- Decisions (+ why): ran `brainstorming` → classified bounded, then Grayson's
  "both, phased" call (build the visual gallery now, add the automated
  assertion layer). Chose a vendored ~60-line stdlib PNG reader over adding
  Pillow (his call, keeps deps clean). Calibrated every check threshold against
  real renders rather than guessing — which corrected two of my assumptions on
  sight: MM's +V points DOWN (not up), and the polarity swatch's red centers
  OUT-area the blue seams (so `red > blue` is the flip detector, not the
  reverse). Two assertion styles because voronoi layout is random: deterministic
  point-samples where geometry is fixed (UV corners, relief dome-out), full-
  buffer statistical scans where it isn't (the glyph's thin strokes need the
  full scan, a sparse grid walks past them). For "text", MM has no text node, so
  `relief_glyph` spells "UP" from two `sixteen_segment` glyphs scaled/translated
  via `transform` and unioned with `blend` Lighten. Left `render.py` untouched
  despite finding its orphan bug, since a separate session is fixing it.
- Process note: mid-session hit a render death-spiral from OVERLAPPING render
  jobs (a timed-out foreground render kept running in the background while I
  started another), which root-caused the `render.py` orphan-on-timeout bug.
  Recovered by killing all Godot and rendering strictly sequentially. Captured
  in the `render-orphan-contention` project memory.

## 🗂️ Changed this session (new leather cookbook category, 6 materials)

- Branch: `main`. Committed and **pushed**: `5f1a27b` (l01-l04 + AUTHORING
  section), `6915fc8` (l04 albedo-polarity fix + l05 quilted), `f55359a` (l06
  topstitched). New file `quality/cookbook_leather.py`; new AUTHORING Leather
  section; 6 tracked albedo thumbnails under `docs/images/cookbook-leather/`.
  Also appended the debug-materials idea to
  `_agent-commons/ideas/Tool-MaterialMaker-MCP.md`. No plan doc, no worktree,
  no gate: informal cookbook growth per `quality/README.md`, same pattern as
  the fabrics/wood/stone cookbooks.
- Decisions (+ why): followed the visual-iteration workflow (render + 3D
  preview + send to Grayson each pass; judge relief in 3D, not the flat
  swatch). Reworked three materials from honest misses rather than shipping
  them: l02's first wear mask made cow-hide blobs (finer/softer/lower-contrast
  fixed it), l04's bronze was on the wrong voronoi region (albedo-polarity
  flip), l05's intended stitch dashes via `shape`+`tiler` failed so it became
  a `pattern`-based quilt. Two general levers came out of it and are the real
  keep-value, both written into AUTHORING: **`_dome_the_cells`** (reverse
  `colorize_0` so voronoi cell BODIES dome up and seams recess; the stock
  crocodile ramp is inside-out because voronoi port 0 is low at centers, high
  at borders) and the **stitch-generator hunt** (`shape`+`tiler` degenerate
  shader → 180s timeout when isolated; `pattern` Square×Square grid works but
  its "on" region is the connected field, so the dash rectangles are its LOW
  cells → one reversed sharpen colorize fixes colour + flattened field at
  once). Also learned: isolating a node's output to albedo for a quick
  diagnostic reliably timed the renderer out here twice; prefer reading the
  full render over an isolate-to-albedo pass.

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

## 🗂️ Changed this session (pre-release audit, teardown, doc-accuracy fixes)

- Branch: `main`. Committed and pushed: `1fb0d45`. Changed:
  `README.md`, `docs/NORTH_STAR.md`, `docs/PLAN.md`, `docs/AUTHORING.md`,
  `.env.example`, `STATUS.md`. No `src/` code touched this session. No plan
  doc, no worktree — a mechanical accuracy pass following the teardown's own
  "one change worth making first" recommendation, not a design change.
- Also wrote and pushed `_agent-commons\log\2026-08-28-claude-code-materialmaker-mcp-teardown-and-doc-fixes.md`
  (scoped commit, not `Push-Repo`, since the commons repo had 34 other
  agents' pending log entries and an unrelated modified `dashboard/index.html`
  sitting uncommitted — staged and pushed only this session's own file).
- Decisions (+ why): fixed the README self-contradiction ("11 of 15" in the
  alpha warning vs. the real 15/15 two hundred lines later) by keeping both
  numbers but labeling which is the live score and which is the ship gate,
  rather than deleting one — both facts are true and useful, they were just
  unlabeled. Promoted `overlay.py` from 🔌 to ✅ in STATUS.md's Components
  table (reconciling its disagreement with the Phases table's Phase-5 ✅)
  because it's a proven hard dependency already exercised in the verified
  hands-on session, matching this project's own convention of using ✅ with
  caveats noted inline (like `render.py`'s Unreal-unverified note) rather
  than reserving ✅ for zero-known-issues — the two new gaps the teardown
  found in it (no rollback on a failed rebuild, staleness check ignores the
  checkout's own content) are recorded inline as known, low-priority instead
  of blocking the checkmark. Did not fold today's 10 code-review findings
  into HANDOFF.md's Heads-up as full detail during the pass itself — that's
  done now at wrap-up instead (see below), since the fix pass was scoped to
  docs only and the findings needed the wrap-up's fuller space anyway.

## 🗂️ Changed this session (render_node_output + live_render_node_output, backlog item H)

- Branch: `main`. Committed and pushed: `b85a55f` (housekeeping: revert
  upstream `bricks.ptex`, move `examples/g01-natural-stone/` into
  `saved_graphs/`), `f891fbb` (the feature). `origin/main` in sync.
  New/changed: `src/mm_mcp/graph.py` (`find_material_node`/
  `isolate_node_output`), `src/mm_mcp/server.py` (`render_node_output`,
  `live_render_node_output`, `disconnect_nodes` as a 4th `live_apply` op),
  `src/mm_mcp/live.py` (`disconnect_nodes`), `addons/mm_live/live_server.gd`
  (`_cmd_disconnect_nodes`), `tests/test_graph.py`, `tests/test_server_tools.py`,
  `tests/test_live.py`, `tests/test_server_live.py`, `README.md`, `STATUS.md`.
  No plan doc, no worktree — classified `bounded` via `brainstorming`, built
  directly via `test-driven-development` on `main`.
- Decisions (+ why): `render_node_output` returns just the single `_albedo.png`
  path, not all four exported maps, since only albedo actually reflects the
  isolated node after the rewire — the others reflect whatever else was
  already wired and would be misleading if returned alongside it. The live
  path's `disconnect_nodes` was added specifically because Material Maker's
  own `connect_children` (verified in the real upstream source) already
  disconnects whatever previously fed a port before wiring a new one, so a
  reconnect-based restore works whenever the target port started out
  connected to something — but there was no way to restore "unconnected" if
  it didn't, which item I's rename/reposition backlog entry had already
  flagged as a gap, just not yet needed until this feature. `disconnect_nodes`
  checks the connection actually exists (fetches the current graph first)
  rather than blindly forwarding to the socket, matching `connect_nodes`'
  existing "validate before touching the socket" convention, even though
  there's no catalog rule to check here (only existence). `live_render_node_output`
  restores unconditionally after render, even on a render failure, so the
  live window is never left stuck mid-preview if the render itself errors.
  The new GDScript handler was deliberately proven by a dedicated integration
  test that forces the disconnect-restore branch (no original connection to
  reconnect to) rather than folding it into an existing test, since the
  already-existing tests only exercise the reconnect branch (which reuses
  the already-proven `connect_nodes`/`do_connect_node`) — this project has no
  automated GDScript test harness, so the real integration test is the only
  proof any new GDScript code actually works.

## 🗂️ Changed this session (Grayson's saved_graphs/ round-trip: rename + moss)

- Branch: `main`. New: `saved_graphs/bricks_grayson_edit.ptex` (Grayson's
  hand-edited bricks variant, renamed/reorganized, with a moss-in-crevices
  layer added). Not committed yet, part of this wrap-up's commit. No plan
  doc, no worktree; direct authoring work following this project's
  established cookbook workflow, plus a throwaway one-off script (moved to
  the session scratchpad afterward, not part of the repo) that did the
  rename/reposition/moss-node insertion programmatically rather than by
  hand-editing 500+ lines of JSON.
- Decisions (+ why): established `saved_graphs/` as the new home for
  Grayson's own tweaked graphs, distinct from `quality/`'s Claude-authored
  cookbook recipes, because his first save landed inside the pristine
  `z-Git\material-maker` checkout (which this project's own conventions say
  not to modify) rather than anywhere version-controlled. Did the rename +
  reposition + moss edit file-side in one pass rather than splitting moss
  into a live-mode session, because renaming/repositioning are impossible
  in live mode as it exists today (see the new H/I/J backlog items) and
  doing the moss addition in a separate tool from the rename would have
  meant two disjointed passes instead of one coherent one. Verified the
  moss threshold empirically rather than trusting the first guess: the
  first pass produced zero visible moss, diagnosed by temporarily rerouting
  the graph to render `MossMask` in isolation (came back solid black),
  measuring the real value range of the underlying `SurfaceDetailMask` via
  a pixel histogram, and retuning the gradient thresholds to match reality
  instead of the assumed range.

## 🗂️ Changed this session (Unity export proven, render.py --target fix)

- Branch: `main`. Committed and pushed (`82a57f0`, `origin/main` in sync):
  `src/mm_mcp/render.py` (extracted `_build_command()`, `-t` → `--target`,
  new `target` param on `render()`), `src/mm_mcp/server.py` (`target` param
  on `render_graph`, forwarded through), `tests/test_render.py` +
  `tests/test_server_tools.py` (4 new tests). No plan doc, no worktree;
  small, TDD, matching this project's precedent for well-scoped fixes.
- Decisions (+ why): the spike (Unity/Unreal export feasibility) surfaced a
  real bug rather than staying a pure investigation, so it graduated from
  spike to a bounded implementation task with Grayson's explicit "go" before
  any code was touched, per `brainstorming`'s path discipline. Extracted a
  pure `_build_command()` rather than patching the inline `cmd` list, to
  match the existing testable-command-builder convention in `preview.py`/
  `live.py` (noted as a project pattern in earlier handoffs) rather than
  introducing a one-off. `target` defaults to `"Godot/Godot 4 Standard"` on
  both `render()` and `render_graph()` so no existing caller's behavior
  changes; this was a deliberate minimal-scope choice, Grayson asked to
  prove cross-engine export works, not to change what the default render
  does. Verified through the real MCP tool path (`server.render_graph`)
  against the bundled `bricks` example, not just the raw CLI probe used
  during the spike, since the point was proving *this project's* pipeline
  works, not just Material Maker's own CLI in isolation.

## 🗂️ Changed a prior session (wood/stone cookbooks, editability + cross-engine docs)

- Branch: `main`. New files: `quality/cookbook_wood.py`,
  `quality/cookbook_stone.py`, `quality/contact_sheet.py`, plus tracked
  preview PNGs under `docs/images/cookbook-wood/` and
  `docs/images/cookbook-stone/`. Modified: `docs/AUTHORING.md` (human-
  editability constraint + wood/stone cookbook writeups),
  `docs/NORTH_STAR.md` (cross-engine portability section). No plan doc, no
  worktree -- pure content/docs work plus two new small standalone
  utility scripts, no existing code touched.
- Decisions (+ why): `w03_painted_wood_siding` needed a donor swap
  (`wood` → `wooden_floor`) because siding fundamentally needs board
  structure that no amount of mask/color tuning can add -- written up as a
  general lesson, not just a one-off fix. `s04`'s original concrete recipe
  was replaced (not deleted-and-forgotten; preserved in AUTHORING.md's
  history text) with `s04_scattered_river_stones` at Grayson's explicit
  request. The GDScript parse-only smoke check from the backlog was tested
  empirically and found non-viable rather than assumed working from a
  prior review's claim -- the `--check-only` flag never boots the project's
  autoloads/global classes. The cross-engine North Star addition was
  researched (both Material Maker's own export docs and a portfolio-wide
  survey via a dispatched Explore agent) before writing anything, per this
  project's own "check before proposing new scope" rule.
  **Process change, not just content:** Grayson had to explicitly say "I
  haven't seen it" before this session started sending `SendUserFile`
  previews every pass instead of only looking at them via `Read` --
  saved as a standing feedback memory so it doesn't regress. Also learned
  (the hard way, twice) that the 512px tracked preview thumbnail can hide
  real detail, and that relief-driven materials (rounded pebbles) are
  invisible in a flat albedo swatch -- both `render_preview` (3D) and the
  full-res render under `quality/cookbook/` are now the standard judgment
  tools, not just the docs thumbnail.

## 🗂️ Changed a prior session (overlay read-only rmtree fix)

- Branch: `main`. Committed and pushed (`09455c8`) since this handoff was
  last written -- confirmed via `git log`/`origin/main` sync at this
  session's pickup, resolving that prior "not yet committed" note as stale.
  `src/mm_mcp/overlay.py` (new `_clear_readonly()` helper, called before
  `shutil.rmtree` in `ensure_overlay`), `tests/test_overlay.py` (new
  regression test). No plan doc, no worktree -- small, well-scoped, same
  precedent as the GUI-child-process-leak and `live_clear` fixes.
- Decisions (+ why): fixed by clearing the read-only attribute on every
  file under the overlay directory before `rmtree`, rather than passing an
  `onerror`/`onexc` handler to `shutil.rmtree` itself -- the `onexc`
  parameter's signature changed between Python versions (added 3.12), and
  this project's `pyproject.toml` declares `requires-python>=3.10`, so a
  version-independent pre-clear pass was preferred over a version-gated
  handler. Root-caused via `systematic-debugging` by reproducing directly
  against the real `.venv` Python (`live.connect_or_launch()`) rather than
  trusting the MCP tool's bare "Error executing tool live_start" -- the MCP
  wrapper swallows exception detail on a raise, so the real traceback only
  showed up outside it.

## 🗂️ Changed a prior session (Phase 5 hands-on verification + live_clear)

- Branch: `main`. Committed directly (`b414763`, pushed): `STATUS.md`
  (Phase 5 phase row + live-control component row, both 🔌 → ✅),
  `addons/mm_live/live_server.gd` (`_cmd_clear_graph` handler +
  `_show_transient_notice` helper + dispatch wiring), `src/mm_mcp/live.py`
  (`clear_graph()` client function), `src/mm_mcp/server.py` (`live_clear`
  MCP tool, registered), `tests/test_live.py` (1 fake-server unit test + 1
  real integration test), `tests/test_server_live.py` (2 unit tests). No
  plan doc, no worktree -- classified `bounded` via `brainstorming`, built
  directly via `test-driven-development` on `main`, same track as the
  GUI-child-process-leak fix from an earlier session.
- Decisions (+ why): the hands-on verification itself was not a special
  demo mode -- confirmed with Grayson that `live_apply`/`live_render`
  working end to end against a real launched Material Maker, with the
  window staying open afterward for edits, IS the product loop described in
  `docs/NORTH_STAR.md`, not a one-off proof. No permanent demo graph was
  kept. `clear_graph` resets to a single default Material node (not a fully
  empty graph) via Material Maker's own `graph_edit.gd:714` `new_material()`
  -- Grayson's explicit choice, and it happens to be exactly what the GUI's
  own "New" menu item already does, so no new reset logic had to be
  invented. The "warning" Grayson asked for became a non-blocking on-screen
  notice rather than a blocking confirmation dialog -- also his explicit
  choice, since a remote/automatic clear call must never hang the socket
  response on a human clicking something, and Material Maker has no
  existing toast/notification system to reuse (only blocking
  `AcceptDialog`s), so a minimal custom `CanvasLayer`+`Label` overlay was
  built instead.

## 🗂️ Changed a prior session (connect_or_launch readiness race)

- Branch: `main`. Landed via a feature branch
  (`worktree-connect-or-launch-readiness-race`) built end to end with
  `subagent-driven-development` in an isolated worktree, merged fast-forward
  then pushed: `1d3908f` plan doc, `0df1992` Task 1 (Python readiness gate +
  new fake-server test, 4 existing fixtures updated), `ba9f620` Task 2
  (GDScript `has_graph` signal via a new `_has_active_graph()` helper),
  `e3a9dd9` Task 3 (real integration verification: a new `ping`-shape
  assertion in the existing integration test, plus a 4x back-to-back
  manual relaunch check), `84948ae` Task 4 (spec doc amendment), `4f4240a`
  final-review fix wave (fail-fast on a responsive-but-graph-less attach,
  a second spec amendment, a stale docstring fix, one new regression test).
- Decisions (+ why): `has_graph` is reported as a field alongside `ready`
  rather than folded into it, so an already-running, fully-healthy instance
  keeps attaching near-instantly -- folding it into `ready` directly would
  have meant every already-attached live tool call re-derives readiness
  from scratch on every single call (per `_ensure_live_session`'s "cheap
  when already up" design), and any transient "no tab focused" moment would
  have looked identical to "still booting." The five existing mutating
  command handlers in `live_server.gd` were deliberately left untouched
  (their own `graph_edit == null` guards stay as defense-in-depth, now
  normally unreachable) rather than refactored into the new
  `_has_active_graph()` helper, since they need the live `MMGraphEdit`
  reference afterward for their own work, not just a boolean -- collapsing
  them would have added indirection without removing real duplication.
  The final review's two Important findings (the 60s misdiagnosed hang on
  attach, and the spec doc not documenting it) were ruled real and
  load-bearing rather than deferred, since merging this branch while a
  Material Maker window is already open from before the merge is exactly
  the trigger -- fixed in the same wave rather than left for a future
  session to rediscover. Implementing that fix made Task 1's own
  already-approved test (`test_connect_or_launch_waits_for_a_graph_tab_
  after_main_window_is_ready`) logically unsatisfiable, since its exact
  attach-path scenario became the new required-fail-fast case; retargeted
  to the fresh-launch path instead of inverting or deleting it, preserving
  the original protection on the one path where it still applies -- this
  call was checked with the advisor before implementing, then independently
  re-derived (not just trusted) by the scoped re-reviewer, who confirmed no
  better alternative existed given the brief's own definition of the bug.

## 🗂️ Changed the prior session (Phase 5 MCP tool surface)

- Branch: `main`. Landed as 9 commits via a feature branch (`worktree-phase5-mcp-tool-surface`)
  merged locally (fast-forward) then pushed: `e48b40d` plan doc, `6a0ee8b`
  Task 1 (`connect_or_launch` port-race hardening), `235b6b8` Task 2
  (`live_start`), `a82e764` Task 3 (`live_get_graph`), `0862265` Task 4
  (`live_apply`), `8ed1c9b` Task 5 (`live_render`), `52d5a6e` Task 6 (README
  Live mode section), `9fcf6a7` Task 7 (real integration test), `502eb4d`
  final-review fix wave (process-handle bug, grace-period discriminator,
  `live_apply` error-as-data, README wording). Plus one same-session
  follow-up directly on `main` (small, well-scoped, no worktree needed):
  `f97a2ac` fixes the GUI-child-process leak in `live.py`'s `_terminate`.
- Decisions (+ why): every `live_*` MCP tool calls `_ensure_live_session`
  first rather than requiring an explicit `live_start` call beforehand,
  matching the spec's "a live tool call launches it rather than erroring
  out" scope decision -- re-probing on every call is cheap (one ping
  round-trip) once a session is up. `live_apply`'s op schema
  (`{"op": "add_node"/"connect_nodes"/"set_param", ...}`) mirrors the
  underlying `live.py` function names/kwargs directly rather than inventing
  a new shape, and stops at the first failing op since a later op may
  assume an earlier one already applied. The final review's two Important
  findings were both ruled real and load-bearing (not pre-existing, not
  out-of-scope) since both were introduced by this plan's own tasks:
  fixing the `_ensure_live_session` clobbering bug required a small,
  targeted preservation fix rather than a bigger redesign (no `live_stop`
  tool exists or was needed -- Grayson closes the GUI himself in real use;
  the bug only mattered because a test's cleanup relied on it); fixing the
  grace-period discriminator required rewriting the plan's own given test
  for the occupied-port case, ruled correct against the spec's own "lazy
  main_window resolution" constraint rather than treating the plan's
  original code as authoritative. The GUI-child-process-leak finding
  (`LiveSession.close()`/`_terminate` not reaping the spawned GUI process)
  was ruled genuinely pre-existing and out of this plan's scope -- `live.py`
  was frozen after earlier tasks' clean reviews, and the leak reproduces
  identically in a pre-existing integration test from a prior session, not
  something this session's tasks caused.

---

## Archived session log

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

### 2026-08-28 (late night) — Unity export proven, render.py --target CLI bug found and fixed
- Picked up via `pickup`; no drift, `main` matched the wood/stone session's
  `7f8f9f2`, in sync with `origin/main`.
- Grayson wanted to prove cross-engine export could produce a real
  shader/material asset, "not just exporting images and then loading those
  into Unreal Engine." **`brainstorming`:** classified as a spike (a
  feasibility question, not a scoped change). Read Material Maker's own
  export templates directly (`material.mmg`) rather than assuming from
  docs: confirmed Unity's export writes a ready `.mat` + `.meta` files with
  no live Editor needed, and Unreal UE5's export writes a python script
  that builds a real native Unreal Material graph via `MaterialEditingLibrary`
  when run inside a live Editor.
- Tried to verify the Unreal half against this session's connected
  `mcp__unreal-engine__*` tools; no live Editor was reachable (`inspect`/
  `system_control` both errored "Unreal Engine is not connected"),
  confirmed across multiple retries and after Grayson said Unreal should be
  open. He asked to try Unity instead, no live bridge exists for Unity in
  this session, but Unity's export doesn't need one.
- Answered Grayson's follow-up question (pros/cons of Unity's Built-in vs
  URP vs HDRP pipelines, which for games) directly from general knowledge
  plus a quick read of Material Maker's per-pipeline export blocks; he
  picked URP.
- Probed the export CLI directly against a real Godot binary
  (`--export-material -t/--target <profile> -o <dir> <ptex>`) to prove
  Unity/URP produces a real `.mat`. Found the actual bug along the way:
  `-t` (the flag `render.py` has always used) is a silent no-op in Material
  Maker's `parse_args.gd`; only `--target` works. Confirmed with four
  direct CLI runs (valid Unity target, alternate Godot target, garbage
  string all via `-t`, all producing identical default-Godot output; the
  same values via `--target` worked immediately).
- Presented the fix as a bounded design in chat per `brainstorming`'s
  discipline (spike output graduating to real code needs its own
  approval); Grayson said "go." **`test-driven-development`:** extracted
  `_build_command()` in `render.py`, fixed the flag, added a `target`
  parameter to `render()` and `server.py`'s `render_graph`, 4 new tests
  written and watched fail first. Full fast suite: 187 passed (up from
  174). Verified for real through `server.render_graph(target="Unity/URP")`
  against the bundled `bricks` example: a genuine `.mat` wired to Unity's
  URP Lit shader with `_NORMALMAP`/`_PARALLAXMAP`/`_METALLICSPECGLOSSMAP`
  all correctly enabled, plus the confirmed-unchanged Godot default path.
  Cleaned up scratch spike output afterward.
- Grayson also asked for a way to open an example in the real GUI to
  tweak/save himself, part of the round-trip loop `docs/NORTH_STAR.md` is
  built around. Launched the real (non-overlay) Godot GUI directly with
  `bricks.ptex` loaded, running in the background as this session ends;
  confirmed the launch didn't crash (only cosmetic HDR-loader and
  window-transient-parent warnings, both known-benign), not confirmed
  Grayson actually used it.
- Committed and pushed on Grayson's explicit "let's push" (`82a57f0`,
  confirmed `origin/main` in sync via `git rev-list --left-right --count`).
- Wrote the required `_agent-commons\log\` entry
  (`2026-08-28-claude-code-unity-export-target-fix.md`) before this
  wrap-up, per `C:\Projects-local\CLAUDE.md`'s standing rule.

### 2026-08-28 (evening) — wood/stone cookbook categories, editability + cross-engine docs
- Picked up via `pickup`. Drift found and reported: the handoff said the
  overlay read-only-rmtree fix was uncommitted; git showed `main` and
  `origin/main` both at `09455c8` -- already landed. No other drift.
- Grayson asked for four things at once: (1) human-editability as a written
  constraint, (2) some cookbook categories, (3) short answer on the
  GDScript smoke-check backlog item, (4) checking Material Maker's export
  options and other local projects for Unreal texture QA prior art, then
  updating NORTH_STAR.md if it made sense.
- **(1)** Added a "Human-editability constraint" section to
  `docs/AUTHORING.md` (simple chains, descriptive names, sane layout,
  prefer the simpler equivalent).
- **(3)** Built and ran the GDScript parse-only smoke check for real before
  trusting the prior review's claim it was viable. It isn't:
  `--headless --check-only --script` never boots the project's autoloads
  or global `class_name`s, so it can't resolve `mm_globals`/`MMGraphEdit`.
  Confirmed with a dependency-free scratch script (passes) vs. the real
  addon (fails identically with/without `--path`). Reverted the test.
- **(4)** Dispatched an Explore agent across Grayson's other local projects
  for Unreal asset-QA prior art before writing anything. Found
  `Tool-UnityQA` had already scoped and deferred the identical problem
  (texture channel-packing/color-space checks across engines) -- confirmed
  this is new ground, not a reuse. Read Material Maker's own export docs
  (Unity `.mat`, Unreal UE4 manual/UE5 python-script). Added a "Cross-engine
  portability" section to `docs/NORTH_STAR.md`.
- **(2)** Built `quality/cookbook_wood.py` (3 recipes) and
  `quality/cookbook_stone.py` (3 recipes), following the established
  cookbook-growth pattern. Visually verified every render before writing
  anything up -- caught and fixed a real miss along the way (`w03`'s first
  paint-mask attempt read as cow-hide blotches, fixed by tuning the mask).
- Grayson then pointed out he'd never actually been SHOWN any of this --
  every review to that point was me looking at renders via `Read`, not
  sending them. Started `SendUserFile`-ing every pass; saved as a standing
  feedback memory (`feedback-send-render-previews.md`). He also asked for
  a tiled contact sheet -- built `quality/contact_sheet.py`.
- Grayson's review of the sent images found three real problems, fixed all
  three: `w03`'s speckle (root-caused to the `blend` node's opacity math at
  a razor-thin mask threshold -- widening the band fixed it; tested and
  confirmed this does NOT generalize to `sf03`'s similar-looking unresolved
  bug), `s04` concrete too light (darkened), `s05` hex tile too flat (added
  a fine-grain multiply layer -- then discovered the 512px tracked preview
  was hiding that detail entirely, a real caveat now in memory).
- Grayson asked for a sixth stone (natural river stones/pebbles) and
  flagged `w03` as still "not quite right" and asked for a softer
  pebble-style replacement for `s04`. Built `s06_river_pebbles` (rounded
  voronoi cells, per-cell random tone, `param4=0` relief) -- the flat
  albedo looked like angular polygons; confirmed correct via
  `render_preview` (3D), establishing "judge relief materials in 3D" as a
  standing rule. Root-caused `w03` for real this time: the donor (`wood`)
  had no board structure at all, so no mask tuning could ever make it read
  as siding -- swapped to `wooden_floor` and it worked immediately.
- Grayson's next review: "the white feels weird" on `w03` (two more real
  fixes -- the paint color was capped at 88% brightness with a muddy cast,
  and the mask balance had wood as the majority, backwards for siding) and
  wanted `s04` replaced entirely with something softer/pebble-like.
  Built `s04_scattered_river_stones` (stones in a sand matrix, distinct
  from `s06`'s packed mosaic) -- hit and fixed a real bug: assumed
  `voronoi` port 0's distance field was high at cell centers, it's actually
  the opposite, which had to be found by rendering and looking, not derived
  from the shader source alone.
- Captured Grayson's backlog idea (image-to-material decomposition from
  reference photos) verbatim in a new
  `_agent-commons/ideas/Tool-MaterialMaker-MCP.md` -- this project had none.
- Wrote six `_agent-commons/log/` entries across the session (one per major
  thread) plus the ideas file, all in a single scoped commit to the Skills
  repo (staged only this session's own files, left other agents' pending
  work untouched).
- Fast suite not re-run this session -- no Python/GDScript code changed,
  only new standalone `quality/` scripts and docs.

### 2026-08-28 (yet later still) — overlay read-only rmtree bug, found and fixed
- Picked up via `pickup`; no drift between the handoff and the repo. Grayson
  chose to try `live_clear` live in chat (build something, render, clear,
  watch the notice) instead of just trusting last session's integration
  test.
- `live_start` failed immediately with a bare "Error executing tool
  live_start". **`systematic-debugging`:** read the error carefully (no
  detail), checked `output/mm_live.log`'s timestamp (34 minutes stale --
  the failure happened before Godot was even launched), then reproduced
  directly against the real `.venv` Python (`live.connect_or_launch()`) to
  get an actual traceback rather than guessing from the MCP wrapper's
  swallowed exception. Root cause: `ensure_overlay`'s rebuild path
  (`shutil.rmtree` then `shutil.copytree`) can't delete the read-only
  `.git/objects/pack/*.idx` files that a real git checkout (the overlay's
  source, `z-Git\material-maker`) has, on Windows. This was the *first*
  overlay rebuild since it was created (rebuilds only trigger on an
  `addons/mm_live` content change, which last session's `live_clear`
  addition caused) -- confirmed via a minimal standalone repro
  (`shutil.rmtree` on a directory with one chmod'd-read-only file) before
  touching any project code.
- **`test-driven-development`:** wrote
  `test_ensure_overlay_rebuilds_when_overlay_contains_read_only_files`
  first, watched it fail with the exact `PermissionError`, then added
  `_clear_readonly()` (walks the tree, clears the read-only bit on every
  file) called right before `rmtree` in `ensure_overlay`. `tests/test_overlay.py`:
  26 passed (up from 25). Full fast suite: 183 passed (up from 182).
- Verified against the real overlay on this machine, not just the test: a
  direct Python call rebuilt it and launched a real Material Maker
  instance successfully. Then ran the originally-intended demo over the
  real MCP tools: `live_start` attached to that instance, `live_get_graph`
  showed the graph restored from last session's verification (voronoi →
  Material -- Material Maker apparently reopens its last-edited graph on
  launch), `live_render` rendered it (`before_clear_albedo.png`),
  `live_clear` reset it, and a final `live_get_graph` confirmed exactly one
  default `Material` node with zero connections.
- Asked Grayson in-chat whether he saw the on-screen notice and whether to
  commit/push; he invoked `/wrap-up` before answering either. This wrap-up
  commits locally per the skill's guardrail (no push approval standing this
  session) and leaves both open (see Open questions).
- Wrote the required `_agent-commons\log\` entry
  (`2026-08-28-claude-code-overlay-readonly-rmtree-fix.md`) before this
  wrap-up, per `C:\Projects-local\CLAUDE.md`'s standing rule.

### 2026-08-28 (later still) — Phase 5 hands-on verification, then a live_clear tool
- Picked up via `pickup`. The prior session's blocker (no MCP wiring to
  `mm-mcp` in this Claude Code session) was already fixed by that session's
  `.mcp.json`; this session's tool list confirmed `mcp__material-maker__*`
  connected, proving the restart-and-reload fix worked.
- Ran the actual manual live-GUI verification with Grayson: no stale
  Material Maker process was running, `live_start` launched a fresh
  instance and reported `has_graph` correctly on the first try,
  `live_get_graph` confirmed a clean default graph, `live_apply` added a
  `voronoi` node wired into the Material's albedo, Grayson watched it
  appear and connect live (screenshot-confirmed: Voronoi -> Static PBR
  Material -> Albedo, 3D preview sphere showing the live pattern), then
  `live_render` produced a real PNG matching the live preview exactly.
  Updated `STATUS.md`: Phase 5 itself (not just its build sub-plan) is now
  ✅ verified -- the spec's own literal "Done" criterion, met.
- Grayson confirmed no permanent demo graph was needed (the just-proven
  loop IS the product, per `docs/NORTH_STAR.md`), then asked whether a live
  graph could be cleared remotely, with a warning so he's not confused
  watching. It couldn't -- checked `live_server.gd`/`live.py` directly,
  confirmed no clear/reset/delete command existed anywhere in the protocol.
- **`brainstorming`:** classified bounded (a new command on an existing
  protocol, not a new subsystem). Grounded the design in Material Maker's
  real source before proposing anything: `graph_edit.gd:714`'s
  `new_material()` is the exact reset the GUI's own "New" menu item uses.
  Asked two clarifying questions via `AskUserQuestion` (reset to default
  Material node vs. fully empty; non-blocking notification vs. blocking
  confirmation) rather than assuming either. Presented the short design in
  chat, got explicit approval.
- **`test-driven-development`:** built directly on `main`, no plan doc, no
  worktree (small enough, matching the GUI-child-process-leak fix's
  precedent). RED/GREEN for `live.clear_graph()` (fake-server test) and
  `server.live_clear()` (2 unit tests against a fake session), then the
  GDScript handler + a small non-blocking notice overlay (no unit harness
  possible for GDScript in this repo -- proven instead by a new real
  integration test: build a 2-node graph, clear it, confirm it's back to
  exactly one default Material node with zero connections). Passed on the
  first real launch; confirmed zero leftover Godot processes after via
  `tasklist`. Full fast suite: 182 passed (up from 177 at session start).
- Committed (`b414763`) and pushed on Grayson's explicit go-ahead; confirmed
  `origin/main` in sync (`git log origin/main..HEAD` empty both ways).
- Wrote two `_agent-commons\log\` entries this session (the verification,
  then the `live_clear` feature separately, since they were distinct pieces
  of work even within one continuous session).

### 2026-08-28 (later same day) — MCP wiring blocker found and fixed
- Picked up via `pickup`. Handoff and git agreed exactly (main, `0c105c2`,
  clean) -- no drift. Grayson said "go" on the recommended next step (manual
  live-GUI verification).
- Hit a blocker immediately: this Claude Code session had no `mm-mcp` server
  wired in at all, confirmed via `find`/`cat` for `.mcp.json` and
  `claude_desktop_config*` (none existed) and by checking the session's own
  loaded tool list (no `mm_mcp`-prefixed tools present). The README's
  "Connect it to an MCP client" section (`README.md:154`) documents the
  recipe but nothing in the repo actually did it.
- Asked Grayson which client to wire it into (this Claude Code session via a
  project-local `.mcp.json`, or Claude Desktop instead); he said "go for it."
  Verified `.venv\Scripts\mm-mcp.exe` exists before pointing at it (rather
  than assuming global PATH). Created `.mcp.json` with `MM_GODOT_BINARY`/
  `MM_PROJECT_PATH`/`MM_OUTPUT_DIR` copied from the existing `.env` (no
  secrets in any of the three, confirmed by reading `.env` first and
  grepping out anything key/secret/token-shaped).
- Added `.mcp.json` to `.gitignore` next to `.env` -- same reasoning: local
  absolute machine paths, not a repo concern, and no deliberate decision was
  made to track it.
- Wrote the required `_agent-commons\log\` entry
  (`2026-08-28-claude-code-mm-mcp-mcp-json.md`) before this wrap-up, per
  `C:\Projects-local\CLAUDE.md`'s standing rule.
- No code changed. The actual live-GUI verification is still pending --
  requires a fresh Claude Code session (or restart) to pick up the new MCP
  server, which this session's own tool set can't do mid-conversation.

### 2026-08-28 — connect_or_launch readiness race, full SDD pipeline + final-review fix wave
- Picked up via `pickup`, argument named the top backlog item from last
  session (`connect_or_launch`'s readiness race). Started `writing-plans`
  directly given the item was already fully scoped and repro'd in the prior
  handoff -- read the real source (`live_server.gd`, `live.py`, the existing
  `_FakeLiveServer` test fixtures, the design spec) before writing the plan,
  not just the handoff's summary. Saved to
  `docs/superpowers/plans/2026-08-27-connect-or-launch-readiness-race.md`.
- **Standing-preference friction, fixed at the source:** when the plan
  finished, Claude presented the Subagent-Driven-vs-Inline menu as usual.
  Grayson pushed back hard: this preference has been confirmed twice
  before and he doesn't know how to make it stick harder, and asked what
  was actually blocking it. The real answer: `C:\Users\Grayson\.claude\
  CLAUDE.md`'s own "Plan execution" section explicitly said to keep
  presenting the menu (just framed as confirmation), which is what
  produced the recurring stop-and-wait. Rewrote that file to state the
  execution plainly and proceed in the same turn, asking only for a
  genuine blocker; rewrote the matching memory note
  ([[phase5-live-control-design]]-adjacent `feedback-execution-mode.md`)
  the same way. This is a cross-project fix, not specific to this repo.
- **`using-git-worktrees`:** consent given (was on `main` directly),
  isolated worktree via native `EnterWorktree`. The plan doc was
  uncommitted on `main` at pickup time -- the same recurring gap flagged in
  every prior Phase 5 session -- copied into the worktree and committed
  there first. Fresh `.venv`, `.env` copied over, baseline 177 fast tests
  green.
- **`subagent-driven-development`:** pre-flight conflict scan across all 4
  tasks, clean (documented as a table in the ledger per the skill's
  updated requirement, not just a verdict). All 4 tasks passed their first
  task-level review clean -- haiku for the two mechanical/transcription
  tasks (Python fake-server fix, GDScript signal, spec doc edit), sonnet
  for Task 3's real-launch judgment work (which included the 4x manual
  relaunch verification, the actual empirical proof the bug is gone).
- **Final whole-branch review** (opus): "Ready to merge, with fixes."
  Confirmed the `has_graph` contract agrees exactly across the Python task
  (written first, before the GDScript field existed) and the GDScript task,
  confirmed no stale `ping` consumer was left anywhere in the codebase, and
  confirmed all four live MCP tools genuinely funnel through the new gate.
  Found 2 Important findings, both real: attaching to an already-running,
  pre-upgrade-addon Material Maker now hung the full `launch_timeout` (60s)
  per tool call with a misdiagnosed timeout error instead of the actual
  cause (a responsive instance with no graph tab) -- and the spec doc's own
  amendment (from Task 4) didn't document this new failure mode. Ruled both
  real, load-bearing, and in-scope for this same fix wave (merging this
  branch while a Material Maker window is already open is exactly the
  trigger), with the fix's shape decided by the controller: distinguish
  "never became ready" from "became ready but no graph tab," fail fast on
  the latter within the existing grace period (no new timing constant).
- **One consolidated fix wave** (sonnet): implemented the 3-way readiness
  split in `connect_or_launch` (a new `main_window_ever_ready` return value
  from `_wait_for_ready_or_give_up`), a diagnostic error message, the spec
  amendment, a stale-docstring fix, and one new regression test. Surfaced a
  real judgment call along the way: implementing the fix made Task 1's own
  already-approved test logically unsatisfiable (its exact scenario --
  attach path, `ready` immediately true, `has_graph` arriving only after
  the grace period -- became the new required-fail-fast case). Confirmed
  with the advisor, then retargeted that test to the fresh-launch path
  instead of inverting or deleting it, preserving its original protection
  on the one path where it still legitimately applies. Scoped re-review
  (sonnet) verdicted all 3 findings ADDRESSED, and independently
  re-derived the test-retargeting call from the raw diff rather than
  trusting the report -- confirmed sound, confirmed no better alternative
  existed given the brief's own definition of the bug. No new breakage.
  Full fast suite: 179 passed (up from 177).
- **`finishing-a-development-branch`:** fast-forward merge to `main`
  (`4f4240a`), 179/179 fast tests green on the merged tip (an untracked
  duplicate of the plan doc, left over on `main` from before the worktree
  existed, had to be removed first so the merge could bring in the
  tracked copy cleanly -- same recurring gap as every prior Phase 5
  session). Worktree and branch cleaned up. Grayson asked to push and
  wrap up in one message; pushed, confirmed `origin/main` synced.

### 2026-08-27 (night) — Phase 5 build step 4: MCP tool surface, full SDD pipeline + final-review fix wave
- Picked up via `pickup`, Grayson chose "start on Phase 5 step 4 via
  writing-plans" and asked to fold the `connect_or_launch` port-race
  hardening backlog item into the same plan. Also asked whether the
  subagent-driven-execution preference could be made a durable default;
  confirmed it was already saved from the step-3 session, strengthened the
  memory note to reflect a second explicit confirmation, and added a short
  standing line to Grayson's global `C:\Users\Grayson\.claude\CLAUDE.md` so
  the default applies across every project, not just this one.
- **`writing-plans`:** designed a 7-task plan -- Task 1 hardens
  `connect_or_launch`'s port-race handling first (since the new MCP tools
  would call it repeatedly), Tasks 2-5 wire the four `live_*` MCP tools one
  at a time, Task 6 documents them in README, Task 7 is a real integration
  test proving the plan's own gate. Saved to
  `docs/superpowers/plans/2026-08-27-phase5-mcp-tool-surface.md`.
- **`using-git-worktrees`:** consent given, isolated worktree via native
  `EnterWorktree`. Fresh `.venv`, `.env` copied over, baseline 158 fast
  tests green. The plan doc was uncommitted on `main` at pickup time (same
  recurring gap as every prior Phase 5 session) -- copied into the worktree
  by hand and committed there first.
- **`subagent-driven-development`:** pre-flight conflict scan across all 7
  tasks, clean (no rulings needed before Task 1). All 7 tasks passed their
  first task-level review clean -- haiku for the mechanical/transcription
  tasks (1-6), sonnet for Task 7's real-launch judgment work. Task 7's own
  integration test passed on the first attempt (42.79s), and flagged
  (DONE_WITH_CONCERNS, not a blocker) that the run left 2 orphaned Godot
  processes -- correctly attributed at the time to a pre-existing
  GUI-child-reaping gap in `live.py`, later found by the final review to
  also implicate a new bug in this session's own Task 2 (see below).
- **Final whole-branch review** (opus): "Ready to merge, with fixes." Found
  2 Important, both real and verified against actual source rather than
  trusting reports: (1) `_ensure_live_session` clobbered a launched
  process's handle on every subsequent call, since `connect_or_launch`'s
  attach path always returns `process=None` -- this was very likely the
  *actual* cause of Task 7's orphaned processes, not solely the GUI-child
  gap. (2) The grace-period hardening from Task 1 would misclassify a
  normally-booting Material Maker as squatted, verified by reading the
  addon's real GDScript (`ping` legitimately returns `ready: false` for far
  longer than the grace period during a real boot) -- a plan-mandated
  defect requiring a ruling, since fixing it meant rewriting Task 1's own
  given test. Also found 1 more Important (`live_apply` raised instead of
  returning errors as data on a malformed op) and 1 free-riding Minor
  (README's tool-count sentence needed updating again). Triaged 5 deferred
  Minors from task-level reviews: 2 resolved for free as part of the two
  Important fixes, 2 parked as genuinely low-priority, and the
  GUI-child-process leak confirmed as a real, separate, out-of-scope gap
  worth its own future backlog item (not conflatable with the
  `_ensure_live_session` fix -- fixing one alone doesn't fix the other).
- **One consolidated fix wave** (sonnet, per the skill's "one fix dispatch,
  not one fixer per finding"): fixed all 3 Important findings plus the
  Minor. One accepted deviation from the literal fix instructions: applying
  the process-handle fix exposed a genuine pre-existing cross-test-pollution
  bug in `tests/test_server_live.py` (tests never reset the `_live_session`
  module global between each other; the old unconditional-overwrite
  behavior had been masking it) -- fixed with an `autouse` pytest fixture
  confined to that one file. Scoped re-review (sonnet) verdicted all 4
  findings ADDRESSED with file:line evidence, including manually tracing the
  exact cross-test-pollution scenario the autouse fixture fixes, confirming
  it a genuine test-isolation fix rather than a production-bug workaround.
  No new breakage. Full fast suite: 174 passed (up from 158).
- **`finishing-a-development-branch`:** fast-forward merge to `main`
  (`502eb4d`), 174/174 fast tests green on the merged tip, worktree and
  branch cleaned up (via `ExitWorktree` + `git worktree remove`/
  `git branch -d`, since this worktree lived under the native
  `.claude/worktrees/` location, not a superpowers-managed one). Grayson
  asked to merge, push, and wrap up in one go -- pushed, confirmed
  `origin/main` synced (`502eb4d` on both sides).
- **Same-session follow-up via `/wrap-up`'s own `+` argument:** Grayson
  asked to also fix the GUI-child-process leak flagged in the wrap-up
  report. Small enough to fix directly on `main` (no plan, no worktree):
  wrote 3 failing unit tests mocking `subprocess.run` first, then added a
  `taskkill /F /T /PID` call to `_terminate` ahead of its existing
  terminate()/kill() fallback (`f97a2ac`). Manually verified against 4 real
  Material Maker launches in a row via `tasklist` -- zero leftover
  processes every time (previously: 2 every time). While doing that manual
  verification, hit a different, unrelated failure 3 times in a row
  (`"no active graph"` right after a successful `connect_or_launch`) --
  suspected the repeated back-to-back launches might be an artifact of the
  fix itself, so proved otherwise with `git stash`: reproduced identically
  on the untouched pre-fix code, confirming it's a separate, pre-existing
  race in the readiness check, not a regression. Documented as a new
  backlog item rather than chased further (out of scope for a leak fix,
  and it touches the addon's startup sequence, not just `live.py`). Fast
  suite 177/177, committed and pushed directly to `main` (small, low-risk,
  already-standing push approval this session).

### 2026-08-27 (evening) — Phase 5 build step 3: mutating commands, full SDD pipeline
- Picked up via `pickup`, Grayson chose "start on Phase 5 step 3 via
  writing-plans." Confirmed a new standing preference mid-session: Grayson
  always wants subagent-driven execution over inline `executing-plans` when
  offered the choice -- saved to memory (`feedback-execution-mode.md`).
- **`writing-plans`:** read the design spec plus the real Material Maker
  source (`graph_edit.gd`, `loader.gd`, `gen_graph.gd`, `gen_base.gd`,
  `main_window.gd`, `gen_material.gd`, `material.mmg`, `warp.mmg`) to ground
  every GDScript API call in verified reality. Found and documented, before
  any code was written: `create_nodes` can silently rename a node on a
  collision (`add_generator`'s uniquify loop); `do_connect_node` and
  `set_node_parameters` address two different node trees with two different
  naming conventions; `main_window.export_material` *looked* like the right
  render entry point from source alone (this turned out to be wrong -- see
  below). Designed a 6-task plan (3 GDScript handlers, 2 Python client
  functions, 1 real integration test). Saved to
  `docs/superpowers/plans/2026-08-27-phase5-mutating-commands.md`.
- **`using-git-worktrees`:** consent given, isolated worktree via native
  `EnterWorktree`. The plan doc was uncommitted on `main` at pickup time
  (same gap flagged in step 2's own handoff) -- copied into the worktree by
  hand and committed there first.
- **`subagent-driven-development`:** pre-flight conflict scan across all 6
  tasks, clean. Tasks 1-3 (GDScript, haiku, pure transcription) and Tasks
  4-6 (Python + integration test, sonnet, judgment-heavy) all passed their
  first task-level review clean. **Real bugs surfaced only once Task 6's
  real integration test ran** -- two genuine, load-bearing bugs in
  already-approved prior tasks that no per-task review could have caught
  (no automated GDScript harness exists in this repo):
  1. Task 2's `_cmd_connect_nodes` declared `from_name`/`to_name` with `=`
     instead of `:=` -- a genuine parse-time type-inference failure that
     broke the *entire* addon script, confirmed via the real Godot launch
     log. Ruled plan-mandated (the plan's own given code had this bug), not
     an implementer error. Fixed by resuming Task 2's original implementer;
     independently re-reviewed clean.
  2. Task 6's own test then hit a genuine topology gap (its own scripted
     graph was never wired into the live graph's default `"Material"`
     node, so no render condition could ever be true) -- fixed by the
     controller, ruled a plan defect. That fix exposed a second symptom
     (more connections producing *fewer* files, not more), which two
     node-type-mismatch hypotheses (checked and ruled out via source and
     via a repeat with type-corrected nodes) failed to explain. Consulted
     the advisor, which correctly diagnosed Task 3's `_cmd_render`:
     `main_window.export_material` fire-and-forgets the real file-writing
     coroutine instead of awaiting it. Confirmed with a direct discriminator
     probe (render, sleep 10s, re-list output dir -- the PNG appeared ~10s
     after the reported failure) before committing to the fix. Fixed by
     resuming Task 3's original implementer with the corrected API
     (`graph_edit.get_material_node()` -> `material_node.export_material(
     prefix, profile, 0, true)`); independently re-reviewed clean.
  Both fix rounds were dispatched to their *original* task's implementer
  (not Task 6's), keeping fix ownership aligned with the code that was
  actually wrong, and both got their own scoped re-review before Task 6
  was retried.
- **Final whole-branch review** (opus): "ready to merge, with fixes." 3
  Important findings (all fixed in one consolidated wave): `set_param` let
  an unrecognized parameter name through Python validation since
  `validate_graph` treats that as a warning, not an error, now blocked; the
  plan doc's mid-execution correction was uncommitted plus two more stale
  spots taught the same wrong claim, fixed; `STATUS.md`'s gate ledger still
  said this step hadn't started, updated. Reviewer explicitly recommended
  fixing only 1 of 6 Minor findings (a `set_param`-effect assertion added
  to the integration test) and leaving the rest as documented risk --
  followed that triage rather than gold-plating. Independently verified the
  Godot binary's `--headless --check-only --script` flags exist and would
  catch the parse-error class of bug (not the await-bug class) for a future
  hardening pass. Flagged the port-race finding as no longer theoretical.
- **`finishing-a-development-branch`:** fast-forward merge to `main`
  (`071dbb6`), 158/158 fast tests + both integration tests individually
  verified green on the merged tip, worktree and branch cleaned up. Grayson
  asked to add the port-race issue to a backlog (this project has no
  dedicated backlog file -- landed it prominently in this doc's Open
  questions instead, plus a wrap-up memory update), then wrap up and push.

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
