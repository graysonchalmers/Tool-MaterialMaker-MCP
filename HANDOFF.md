# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-09-01 (noise-vocab gallery + 2 backlog items + wool take-two) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**Closed two backlog items, shipped a noise-vocabulary reference gallery, took a
second crack at wool loop-knit.** Batch committed + pushed (`20e485d`).
- **#3 `list_node_types`: resolved KEEP.** ~5KB name list vs ~260KB full catalog,
  it's the cheap discovery lever, not redundant. Advisor caught a real doc bug:
  the `category` arg is a plain NAME substring, not a taxonomy (no category field
  anywhere), so `list_node_types("noise")` misses perlin/fbm*/truchet. Docstring
  (server.py) + README corrected to "name substring."
- **#4 `render_preview`: documented.** New "judge in 3D, not off the flat albedo"
  step in AUTHORING.md's workflow, with the dark-backdrop + `tile` caveats.
- **Noise vocabulary (the main event).** Diagnosed the "everything looks similar"
  complaint with a number: 38 cookbook builders, 69% clone 3 donors
  (crocodile_skin x12, rock x7, wood x5), and the only base noise added by hand
  is perlin (x9) + voronoi (x1). Zero fbm/anisotropic/shard/wavelet/truchet out
  of 47 noise nodes. Built `quality/noise_gallery.py` (fbm all-8-bases sweep +
  cross-family row), 2 tracked contact sheets under `docs/images/noise-gallery/`,
  a new AUTHORING.md "Noise vocabulary" section with reach-for-X tables. Kept as a
  REFERENCE, deliberately NOT a pixel-checked debug swatch (noise has no
  known-answer). Fast suite 262 green.
- **Wool loop-knit (take two, still open).** pattern-Bounce (Bounce x Bounce,
  Multiply) is a real discovery but reads as tufted/quilted upholstery, a square
  bump lattice, not interlocking knit loops (the square grid is inherent to
  `pattern` multiplying two axis-aligned waves). Reverted f04 to the committed
  weave partial to keep main clean and avoid mislabeling quilted-as-knit; the full
  recipe + finding + next-steps are below. `main` clean, in sync.

Older write-ups/log beyond the cap live in
[docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).

## 📌 Where we stopped

Wool take-two authored, rendered, and judged in 3D (quilted, not knit); f04
reverted to the committed weave partial; `main` clean and in sync at `20e485d`
plus this wrap-up baton commit. Natural stopping point.

## ▶️ Next concrete step

**Wool loop-knit is still the open item, now with two untried leads from this
session** (the pattern-Bounce recipe that got us to "pillowy but square" is in
the Changed-this-session block below):
1. **Offset alternate rows** of the pattern-Bounce lattice into true V-columns.
   Needs a per-row phase shift `pattern` alone can't do (a transform/tile/offset
   trick, or a second offset pattern blended in). This is the most likely path to
   real knit.
2. **`truchet` Circle** interlocking arcs (the gallery's loop-interlock geometry)
   as the fallback second attempt.
3. **Accept the quilted result as a NEW slot** (e.g. `f07_quilted`): it's a
   genuinely good tufted-upholstery material, just not knit. Deferred here because
   Grayson asked to take a break from making new materials.

Other backlog (nothing blocked):
- **Another cookbook category**: glass and plastics still uncovered (quick-win).

The older open backlog, unchanged:
- **2 findings ruled out, not fixed** (deliberate): #8 (`_cmd_clear_graph`'s
  guard is correct — `new_material()` creates the generator, doesn't read
  one) and #10 (`generic_size or 1` coercion is safer than passing an
  explicit 0). Both annotated in-code. Findings 3-7 and 9 are fixed.
- **`list_node_types` tool decision — RESOLVED this session: KEEP.** ~5KB name
  list vs the ~260KB full `catalog://nodes` resource, so it's the cheap discovery
  lever, not redundant with the resource + `describe_node`. Docstring + README
  corrected: the `category` arg is a name substring, not a taxonomy.
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
- **D. One remaining honest partial** (wool loop-knit). **sf03's
  circuit-board trace-bleed-through is FIXED (2026-09-01)** — root cause was
  the chips' albedo colorize being reused as the blend's opacity mask (65%
  opacity), fixed by a dedicated hard 0/1 mask; see the Changed-this-session
  block and AUTHORING.md.
- **E. Image-to-material decomposition** — Grayson's own backlog idea,
  captured in `_agent-commons/ideas/Tool-MaterialMaker-MCP.md`. Explicitly
  deferred; likely wants its own `brainstorming` session before any design
  work, not a cold start here.
- **F. PyPI publish** (on hold; GitHub-clone is the current route).
- **G. Document `render_preview` — DONE this session** (AUTHORING.md workflow
  step 5). It was already in the README tool table; the gap was the workflow doc.
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
- **Resolved 2026-09-01:** `sf03_circuit_board`'s trace-bleed-through bug is
  FIXED. It was never a mask-threshold problem (that hypothesis was correctly
  ruled out earlier). Real cause: the chips' albedo colorize (gray 0.65) was
  fed as the `blend`'s port-2 opacity, and a blend's opacity is `amount * a`
  (`blend.mmg`), so chips were 65% opaque and the traces bled through the other
  35%. Fixed by splitting a dedicated hard 0/1 opacity mask off the albedo
  (same on the traces). No longer open.
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

## 🗂️ Changed this session (noise-vocab gallery + 2 backlog items + wool take-two)

- Branch: `main`. Commit `20e485d`, **pushed** to `origin/main` (CI triggered).
  Files: `quality/noise_gallery.py` (new), `docs/AUTHORING.md` (new "Noise
  vocabulary" section + a render_preview workflow step), `src/mm_mcp/server.py`
  (list_node_types docstring), `README.md` (tool-table wording), 2 tracked
  contact sheets under `docs/images/noise-gallery/`. Rendered outputs under
  `quality/cookbook/noise-gallery/` + `quality/authored/noise-gallery/` are
  gitignored by the existing cookbook convention. No gate/phase state moved.
- **The noise diagnosis (why the materials look alike), quantified:** 38 cookbook
  builders, 69% clone 3 donors (crocodile_skin x12, rock x7, wood x5), only base
  noise added by hand is perlin x9 + voronoi x1, zero fbm/anisotropic/shard/
  wavelet/truchet out of 47 noise nodes. The fix is a wider base-noise vocabulary,
  not more recolors. Biggest lever: `fbm`'s `noise` enum (8 bases; Value/Perlin
  are close cousins, Cellular 2-7 are the untapped multi-octave range that plain
  voronoi can't do). Cross-family: anisotropic (directional), truchet Line/Circle
  (circuits/pipes), voronoi_triangle (scales/gems), wavelet (fine grain).
  Caveats: `shard_fbm` reads soft at defaults (push `sharp`/`folds`);
  `fbm_variations` has unresolved `$?1..$?4` enum labels, check its `.mmg` first.
- **Wool take-two recipe (kept for next session, NOT committed):** retype
  crocodile_skin's `voronoi_0` to `pattern` with `mix=0` (Multiply), `x_wave=5`
  (Bounce), `y_wave=5` (Bounce), `x_scale=8`, `y_scale=8`; normal_map `param1=0.5
  param4=0`; heathered-oatmeal albedo. Result: pillowy TUFTED/QUILTED upholstery
  (a square bump lattice), not interlocking knit loops. The square grid is
  inherent to `pattern` multiplying two axis-aligned waves. Reverted f04 to the
  committed weave partial. Next-steps: offset alternate rows into V-columns, or
  `truchet` Circle, or keep the quilted look as its own new slot. The
  pattern-Bounce lever DOES produce real pillow relief, worth reusing for any
  padded/tufted/cushioned material.
- Process: `advisor` before rendering shaped the noise work (diagnose with a
  histogram first, ship a reference gallery not a pixel-checked swatch, lead with
  the fbm sweep, watch the param4=0 flat-normal trap). `brainstorming` (bounded)
  locked the wool approach before authoring.

## 🗂️ Changed this session (blend-opacity debug swatches +2)

- Branch: `main`. Commit `80256d0`, **pushed** to `origin/main` (CI triggered),
  plus this wrap-up baton commit. Files: `quality/debug_swatches.py` (2 builders
  + 2 pixel checks + 2 registry entries), `docs/DEBUG_SWATCHES.md` (new blend
  family section), `docs/AUTHORING.md` (cross-ref from the pm03 writeup). Rendered
  outputs under `quality/cookbook/debug-swatches/blend_*/` stay gitignored/
  regenerable, matching the existing debug-swatch convention (no tracked
  thumbnails, the doc is the reference). No `src/` change, no gate/phase moved.
- Swatches: `blend_mask_polarity` (amount=1, hard left/right mask -> LEFT blue
  /port-1/background, RIGHT red/port-0/foreground; proves which port shows at
  mask 0 vs 1) and `blend_opacity_ramp` (amount=0.5, ramp mask -> pure blue at
  left, purple that never reaches full red at right; proves opacity = amount ×
  mask, the partial-opacity shape of the sf03 bug).
- Process (+ why): read `blend.mmg` before designing, so the known-answers are
  derived from source, not guessed. Called `advisor` before writing the checks;
  it caught two would-be-shipped bugs: (1) the `.mmg` `blend_type` default is 13
  (AddSub), not 0, so a swatch omitting it would render wrong colors and ship as
  a bogus known-answer, both builders now set `blend_type=0` explicitly; (2) both
  swatches at amount=1 would leave the `amount` factor of `opacity = amount ×
  mask` documented-but-unasserted, so swatch 2 moved to amount=0.5 to assert the
  multiply. Calibrated the check thresholds against the real rendered pixels
  (polarity: left `(30,56,229)`, right `(229,30,30)`; ramp right `(118,44,141)`).

## 🗂️ Changed this session (painted-metal cookbook +5)

- Branch: `main`. Commit `4d72c8b`, **pushed** to `origin/main` (CI triggered).
  Files: `quality/cookbook_painted_metal.py` (new, 5 builders pm01-pm05),
  `docs/AUTHORING.md` (new painted-metal section), 5 tracked albedo thumbnails
  under `docs/images/cookbook-painted-metal/`. Authored `.ptex` + rendered
  maps/previews stay gitignored (regenerable via the builder). No `src/` change,
  so no gate/phase state moved. Memory (`authoring-recipes`, `MEMORY.md`) updated.
- Materials (each authored -> validated -> rendered -> 3D-previewed -> iterated
  with Grayson -> locked): **pm01 powder coat** (rock clone, warp flattened for
  fine orange-peel pebbling), **pm02 automotive enamel** (near-mirror red +
  per-cell flake), **pm03 chipped paint** (green majority chipped to bare metal,
  masked metallic; distinct from the frozen combo01 which chips to rust), **pm04
  hammertone** (medium dimple field, deepest relief, the strongest structural
  read), **pm05 scuffed panel** (directional brushed scuffs, faded utility blue).
- Decisions (+ why): the advisor's steer was the whole frame -- painted metal's
  variation is surface finish, so five materials that differ only in gloss read
  as one gray panel five times; the fix is a distinct STRUCTURAL read per
  material (bump scale, dimple field, chip mask, directional axis), color only
  reinforcing. Two correctness rules held: metallic masked not global (a
  globally-metallic painted panel renders near-black in the preview), and every
  wear mask a hard 0/1 into blend port 2.
- **Durable lesson pinned this session:** a MM `blend` shows its **port-1 input
  where the port-2 mask is 0** and port-0 where the mask is 1. pm03's chip mask
  polarity was inverted twice (metal-majority, then near-all-metal) before this
  landed empirically. Put the MAJORITY layer on port 1; make the hard mask 1 only
  in the minority spots. Recorded in AUTHORING.md + the `authoring-recipes` memory.
- Two per-material fixes worth remembering: pm01's wormy-crackle first render was
  `rock`'s `warp_0` (amount 0.3) smearing cells -- flatten to 0.03; pm05's grainy
  scuffs were 8 perlin octaves -- drop `iterations` to 2 for clean brushed lines.

> 📦 **19 older "Changed this session" write-ups archived** (through
> 2026-08-30, incl. the v0.4.0 release-unblock + README gallery session) --
> the pre-release audit/teardown/doc-fix pass,
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
> cost by the 2026-08-29 teardown (Maintainer lens). **28 older entries are
> now archived there**, from the 2026-08-29 README-images session back
> through the project's Phase 1-2 kickoff on 2026-08-25.


### 2026-09-01 (noise-vocab gallery + 2 backlog + wool take-two) — closed #3/#4, quantified the sameness, wool still open
- Picked up via `pickup` (clean `main` at `198e2ad`, in sync). Grayson batched
  4 items: #2 wool, #3 list_node_types, #4 render_preview, plus "test different
  noise, a lot of the stuff is looking kind of similar." Ran cheapest-first.
- **#3 list_node_types: KEEP** (5KB names vs 260KB catalog). Advisor caught the
  real doc bug: `category` is a name substring, not a taxonomy. Fixed docstring +
  README. **#4 render_preview: documented** (AUTHORING.md workflow step 5).
- **Noise vocabulary:** `advisor` steered it (histogram first, reference gallery
  not a pixel-checked swatch, lead with the fbm sweep). Diagnosis: 38 builders,
  69% clone 3 donors, only base noise added by hand is perlin/voronoi, zero of the
  other 45 noise nodes. Built `quality/noise_gallery.py` (fbm 8-basis sweep +
  cross-family row), 14 renders, 2 tracked contact sheets, AUTHORING.md section.
  Fast suite 262. Committed + pushed `20e485d`.
- **Wool take-two** (bounded `brainstorming` → pattern-Bounce approach, approved):
  authored + rendered + 3D-previewed. Result reads tufted/quilted (square bump
  lattice), not knit loops — the square grid is inherent to `pattern` multiplying
  two axis-aligned waves. Reverted f04 to the committed weave partial; recipe +
  next-steps (offset rows / truchet Circle / keep-as-quilted-slot) captured in the
  Changed-this-session block. Then wrapped.
- Wrote `_agent-commons\log\2026-09-01-claude-code-mm-mcp-noise-vocab-backlog-batch.md`.

### 2026-09-01 (blend-opacity debug swatches) — +2 known-answer diagnostics, all pass
- Picked up via `pickup`; Grayson pre-picked the move in the args (build the
  blend-opacity debug swatch). Clean `main` at `c0b96d7`, in sync.
- Read `blend.mmg` FIRST to derive the known-answers from source: Normal-mode
  output `opacity*s1 + (1-opacity)*s2`, `opacity = amount × mask × s1.alpha`,
  port 0 = Foreground, port 1 = Background, port 2 = Mask.
- Called `advisor` before writing the checks. It caught two would-be-shipped
  bugs: (1) `.mmg` `blend_type` default is 13 (AddSub), so a swatch omitting it
  renders wrong colors and ships a bogus known-answer, both builders now set
  `blend_type=0` explicitly; (2) both swatches at amount=1 would leave the
  `amount` factor unasserted, so swatch 2 moved to amount=0.5.
- Built `blend_mask_polarity` (hard mask, polarity case) + `blend_opacity_ramp`
  (ramp mask, amount=0.5, the partial-opacity/sf03 shape) in
  `quality/debug_swatches.py` + their pixel checks + registry entries. Rendered
  both via `render_one.py` (one Godot at a time), eyeballed, sampled real pixels
  to calibrate thresholds, sent both previews to Grayson.
- Tests: the 2 new blend integration checks pass live (auto-parametrized), fast
  suite 262. Docs: new blend family section in `docs/DEBUG_SWATCHES.md` +
  AUTHORING.md cross-ref. Committed `80256d0`, pushed to `origin/main`, in sync.
- Wrote `_agent-commons\log\2026-09-01-claude-code-mm-mcp-blend-opacity-debug-swatch.md`.

### 2026-09-01 (painted-metal cookbook) — new category, +5 materials, all HIT
- Picked up via `pickup` (clean `main` at `a849784`, in sync). Grayson chose the
  pick: a new cookbook category. Ran `brainstorming` (bounded), he chose painted
  metal, 5 materials.
- Called `advisor` before committing to the set. Key steer: painted metal's
  variation is surface finish, so five gloss-only variants read as one gray panel
  five times; design each around a distinct STRUCTURAL read. Presented the set
  (pm01-pm05, each with its structural read named), Grayson approved.
- Built `quality/cookbook_painted_metal.py`, validated all 5 against the catalog
  (fast, no Godot), then rendered + 3D-previewed each one Godot at a time via
  `render_one.py` + a scratchpad preview helper. pm01 needed a warp-flatten pass
  (wormy crackle -> fine pebbling); pm03 needed two mask-polarity passes before
  the blend port-1/port-0 semantics were pinned; pm05 needed octaves dropped 8->2
  for clean directional scuffs. Sent Grayson all 5 previews; he locked them.
- Finalized: 5 tracked albedo thumbnails to `docs/images/cookbook-painted-metal/`,
  the 5 recipes into `docs/AUTHORING.md`, memory (`authoring-recipes` + index)
  updated with the blend-port fact. Committed `4d72c8b`, pushed to `origin/main`
  (CI triggered), confirmed in sync.
- Wrote `_agent-commons\log\2026-09-01-claude-code-mm-mcp-painted-metal-cookbook.md`.

### 2026-09-01 (masonry cookbook + render pipe-hang fix) — +5 stone materials, fixed a latent render hang
- Picked up via `pickup` (clean `main` at `d946942`, in sync). Grayson chose to
  do all 5 masonry materials; ran `brainstorming` (bounded, extends the existing
  `cookbook_stone.py`), locked the set (cobblestone anchor + 4 he picked).
- **s07 cobblestone** first: built + rendered, hit the render hang (below),
  then two visual passes — widened the muted per-cobble tone gradient and
  dropped `warp_0` 0.4→0.12 to kill a crack-smear haze (a high-contrast test
  gradient was the diagnostic that proved the haze was the warp, not the ramp).
  3D-previewed, locked. Closes backlog C (true irregular cobblestone).
- **s08–s11** each authored → rendered → 3D-previewed → locked, one Godot at a
  time: s08 fieldstone (grayer/denser, warp kept 0.12 after 0.20 re-introduced
  haze without adding angularity), s09 ashlar (switched donor to `stone_wall`'s
  Bricks node — voronoi can't do coursed rectangles; Bricks port 1 = per-brick
  random), s10 flagstone (big flat slabs, normal `param1` 0.99→0.5 for flat
  tops), s11 marble (dry_earth veins, `warp` pushed to 0.5 — the one place the
  smear IS the look — metallic zeroed, roughness 0.15).
- **Render-hang investigation (reversed once):** first blamed `render.py`; a
  clean A/B proved the 180s hangs were a `python -c` harness artifact (the same
  `render()` runs in 7.4s from a script FILE). But the detour found a REAL
  latent bug — `_run_godot`'s `communicate()` blocks on a pipe held by MM's
  lingering child. Fixed via temp-file redirect + `process.wait()` (TDD: a
  real-subprocess RED test that the old mocks couldn't catch, + a
  timeout-teardown test). Kept as MCP-server hardening. Added
  `quality/render_one.py` and the "render via a script file, never `python -c`"
  rule. Fast suite 262 green.
- Docs: 5 recipes + a tooling note in `docs/AUTHORING.md`, a `render_one` note
  in `quality/README.md`, 5 doc thumbnails, STATUS/HANDOFF/memory. Committed +
  pushed (`4c14f8f`).
- **Then closed sf03 (backlog D)** via `systematic-debugging`. Reproduced the
  trace-bleed-through, root-caused it from `blend.mmg` (opacity = `amount * a`,
  port 2 = the mask) + the wiring + a render matching the predicted 65% opacity:
  the chips' albedo colorize (0.65) was reused as the opacity mask. Fixed by
  splitting a hard 0/1 mask off the albedo; same fix on the traces (Grayson
  asked to make them solid gold too). AUTHORING.md + memory updated to resolved.
  Committed + pushed (`6667b4b`).

### 2026-08-30 (v0.4.0 release + gallery) — unblocked release-please, shipped 0.4.0, enlarged README gallery
- Picked up via `pickup` (clean `main` at `6b2a070`, in sync). Grayson chose
  next-move #1: unblock release-please.
- Confirmed the blocker was the repo's "Allow GitHub Actions to create and
  approve pull requests" toggle (off by default). Explained pushing files (always
  worked) vs. a bot opening a PR (gated). Grayson flipped it; re-ran the failed
  run (`gh run rerun 33298317643`) → PR #1 opened.
- Merged PR #1 with a merge commit (`--merge`, what release-please needs).
  release-please tagged **v0.4.0**, cut the GitHub Release (Latest), attached the
  built wheel + sdist. Post-merge `tests` on `main` green (1m16s); a PR-branch
  `tests` run had failed but its logs were purged and main is green, so not
  chased. `main` fast-forwarded to `c2aa170`.
- Grayson then asked to enlarge the README gallery: went 4-col-with-captions →
  2-col-no-captions (~2x larger images). Showed a PIL preview at GitHub's real
  content width before pushing. Committed `8f7f515`, pushed.
- Wrote `_agent-commons\log\2026-08-30-claude-code-mm-mcp-releaseplease-unblock-gallery.md`.

_(Older entries continue in [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).)_

