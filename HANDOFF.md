# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-04 (v0.5.0 released, AUTHORING split landed, hygiene pass) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**Three teardown-order items landed in one session: v0.5.0 was released, the
AUTHORING split shipped, and a hygiene pass followed.** `main` is at `cd900f0`,
pushed and in sync. release-please PR #3 proposes 0.6.0 (open, Grayson's to merge).
- **v0.5.0 released** by merging release-please PR #2 (the cookbook-as-data
  milestone). `bump-minor-pre-major` held: it cut 0.5.0, not 1.0.0.
- **AUTHORING split (merge `6c2edf0`, 6 commits, subagent-driven):** the
  996-line `docs/AUTHORING.md` monolith became a 308-line invariant guide plus
  43 per-material recipe cards at `cookbook/<category>/<id>.md`. The guide is
  now served as the `guide://authoring` MCP resource (`server.py`:
  `_authoring_guide_path`/`read_authoring_guide` + a one-line `@mcp.resource`
  wrapper mirroring `catalog://nodes`; resolves `<repo>/docs/AUTHORING.md`,
  graceful notice when absent). Cross-material lessons (topology-not-donor,
  masonry diagnostics, blend port/opacity) were lifted UP into a new
  "Cross-material lessons" guide section; per-material recipes moved down to the
  cards. A `test_cookbook_graph_has_recipe_card` parity gate requires every
  cookbook `.ptex` to carry a card. Fast suite 424 (was 378). README lists two
  resources now. Final whole-branch review clean on opus.
- **Hygiene pass (`cd900f0`):** `quality/README.md` dropped the stale "informal"
  framing and swept its em dashes; `docs/superpowers/README.md` labels that
  directory as execution history; the contact sheet shrank 5.45MB to 0.99MB via
  256-color palette; one em dash swept from `server.py`'s render_preview
  docstring.
- **Deferred, surfaced to Grayson (NOT done):** folding `examples/` into the
  cookbook (it is load-bearing: `server.py`'s `_bundled_examples`/`list_examples`
  serve `cfg.examples_dir`, and it holds the frozen Phase-3 test-set graphs and
  is referenced by 7 test files, config, doctor, and quality tooling, so it is
  its own scoped project, not hygiene) and deleting `docs/HANDOFF_ARCHIVE.md`
  (a workflow call: it trades a browsable 2015-line history for git archaeology,
  which matters more for a non-SWE, and rewrites the wrap-up trim convention).

Older write-ups/log beyond the cap live in
[docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).

## 📌 Where we stopped

`main` at `cd900f0`, pushed and in sync. v0.5.0 released, AUTHORING split and
hygiene pass landed. release-please PR #3 (0.6.0) is open, Grayson's to merge.
Natural stopping point.

## ▶️ Next concrete step

Two decisions are waiting on Grayson (both surfaced this session):
1. **Merge release-please PR #3 to cut v0.6.0.** It captures the guide resource
   (a feat) plus this session's docs/chore commits. Merge when ready; it is the
   release-cadence call.
2. **Decide the two deferred hygiene items:** (a) whether to fold `examples/`
   into the cookbook (its own scoped project, since it is load-bearing on the
   frozen test set and the example-serving MCP path), and (b) whether to delete
   `docs/HANDOFF_ARCHIVE.md` (kill browsable history for git archaeology, and
   rewire the wrap-up trim convention) or keep it.

Then continue the teardown's v2 order (each is one session or less):
3. **`quality/author.py` refactor** (teardown Refactor item, not yet done):
   split the 8 graph-surgery helpers from the 13 Phase-3 builders.
4. **Cookbook backlog** (glass/plastics category; two-color tweed) now
   compounds: new materials land in `cookbook/` via `promote_cookbook.py`, then
   get a card at `cookbook/<category>/<id>.md`.

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
- **B. More cookbook categories** — fabrics, organics, sci-fi, terrain, wood,
  stone, leather, painted-metal are all represented; terrain now includes the
  natural-surface set (ice/lava/forest floor/pebbles). **Glass and plastics are
  the remaining uncovered quick-wins.**
- **C. True cobblestone — DONE.** `s07_cobblestone` (voronoi-plate `dry_earth`
  approach) closed this in a prior session; the `s05` hex-grid partial is
  superseded.
- **D. Wool loop-knit — CLOSED as unreachable (2026-09-03).** An isolation-render
  probe confirmed no bundled generator makes upright-V stockinette (see the
  Changed-this-session block); `f04` stays the honest coarse-weave stand-in and
  `f07_herringbone_tweed` shipped as the probe's byproduct. sf03's
  circuit-board bleed-through was fixed 2026-09-01 (hard 0/1 opacity mask).
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

- **New 2026-09-03:** does `backup-ops` exclude the ~1GB of regenerable renders
  under `output/`, `quality/cookbook/`, `quality/runs/` (plus the 266MB
  `mm_live_overlay/`)? Flagged by the teardown, not verified.
- **New 2026-09-03, deferred minors from the cookbook-as-data reviews (all
  small):** `tests/test_config.py`'s default-dir test reads the real machine env
  (pre-existing pattern); `_default_cookbook_dir()`'s empty branch is untested;
  `server.py`'s source-validation error string is near-duplicated between the two
  example tools; the contact sheet adds a 5MB blob per regeneration.
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
- **Resolved 2026-09-03:** wool loop-knit (closed as unreachable) and true
  cobblestone (`s07` done) are both off the open list now.
- Still open, unchanged: PyPI vs. GitHub-clone-only (leaning GitHub-only);
  cross-platform (macOS/Linux) verification, still untested, no machine
  available; two parked-not-fixed overlay-builder findings from a much
  earlier session (staleness marker, `_append_autoload`'s first-occurrence
  match, both verified low-priority).

## 🗂️ Changed this session (v0.5.0 release + AUTHORING split + hygiene)

- **v0.5.0 released:** merged release-please PR #2 (`35484e3`), synced local
  `main`. `bump-minor-pre-major` cut 0.5.0 not 1.0.0, as intended.
- **AUTHORING split, feature branch `authoring-split` merged `--no-ff` as
  `6c2edf0`, pushed; branch deleted.** 6 commits `ec72228..a2455b8`. Files:
  `src/mm_mcp/server.py` (the `guide://authoring` resource: `_authoring_guide_path`
  / `read_authoring_guide` pure helpers + the `@mcp.resource` wrapper),
  `tests/test_guide_resource.py` (new), `docs/AUTHORING.md` (996 to 308 lines,
  now the invariant guide with a new "Cross-material lessons" section),
  `cookbook/**/*.md` (43 new recipe cards, one per graph),
  `tests/test_cookbook_gate.py` (new `test_cookbook_graph_has_recipe_card`
  parity gate), plus reference fixups in `README.md`, `quality/README.md`,
  `cookbook/README.md`, `src/mm_mcp/cookbook.py`. Fast suite 424 (was 378).
- **Hygiene pass (`cd900f0`):** `quality/README.md` (dropped "informal", swept
  em dashes), `docs/superpowers/README.md` (new, labels the dir as execution
  history), `docs/images/cookbook-contact-sheet.png` (5.45MB to 0.99MB, 256-color
  palette), `src/mm_mcp/server.py` (one docstring em dash).
- **Process:** `pickup` reconciled clean (0.5.0 PR correctly at 0.5.0 confirming
  the earlier `bump-minor-pre-major` fix). `phased-rebuild` -> `writing-plans`
  (spec-in-plan + 11 tasks, `docs/superpowers/plans/2026-09-04-authoring-split.md`)
  -> `subagent-driven-development`. The 8 per-category card tasks were batched
  into 3 dispatches by independence (disjoint dirs, add-only); every dispatch
  reviewed as a unit; final whole-branch review clean on opus. All card and
  guide prose written em-dash-free (the repo pre-commit hook checks added lines).
- **Decisions (+ why):** cards live at `cookbook/<category>/<id>.md` because all
  three cookbook tools glob `*.ptex` specifically (verified), so `.md` siblings
  are invisible to `list_cookbook`, the gate, and `promote --check`. Residue
  rule: a single-material recipe becomes a card, a cross-material lesson stays in
  or moves up into the guide (topology-not-donor, masonry diagnostics, blend
  port/opacity all lifted). Worked on a feature branch in the main checkout, not
  a worktree, because the editable `.venv` resolves `mm_mcp` from the main
  checkout's `src/`. Deferred `examples/` fold (load-bearing) and
  `HANDOFF_ARCHIVE.md` deletion (Grayson's workflow call), both surfaced.
- One parked minor from the final review: the voronoi port-0 polarity
  cross-material note stayed in the cards (l04 full, l01/s04 reference it) rather
  than being lifted to the guide. Not content loss; a one-line guide addition
  could close it later.

## 🗂️ Changed this session (teardown #2 + cookbook-as-data)

- Branch: feature branch `cookbook-as-data` (11 commits `6c3083c..f31d753`),
  merged `--no-ff` into `main` as `530ad0f`, **pushed**; branch deleted locally
  and on origin. Files: `cookbook/**/*.ptex` (43, new) + `cookbook/README.md`;
  `quality/promote_cookbook.py`; `src/mm_mcp/cookbook.py`, `config.py`,
  `server.py`, `doctor.py`; `tests/test_cookbook.py`, `test_cookbook_gate.py`,
  `test_promote_cookbook.py` (new), `test_config.py`, `test_doctor.py`,
  `test_server_tools.py`; `README.md`, `quality/README.md`, `docs/AUTHORING.md`,
  `.env.example`, `.gitignore` (comment), `docs/images/cookbook-contact-sheet.png`
  (43 tiles), `release-please-config.json`; spec + plan under `docs/superpowers/`.
  This wrap-up also capped STATUS.md's header and moved its old text to the
  archive.
- **Process:** `pickup` chained into `teardown` (six lenses, verdict table, v2
  sketch; report sent as a file). Grayson chose next-move #1. `phased-rebuild`
  framed three gated phases; `writing-plans` produced the spec + 7-task plan;
  `subagent-driven-development` executed it: fresh subagent per task, a task
  review per task (two fix rounds total: Task 1 had dropped the
  `quality/cookbook/` ignore rule, Task 6's doctor call was unguarded), a final
  whole-branch review on the most capable model, one fix wave, one scoped
  re-review, clean.
- **Gates recorded:** Phase A `promote --check` in sync + gate test 88 passed;
  Phase B fast suite green + a real render of `load_example("f07_herringbone_tweed")`
  byte-identical to the locked cookbook render (3 maps: f07 wires no height
  input, so the spec's "4 PNGs" wording was corrected); Phase C README counts
  match the tree, CI success (tests workflow on windows-latest, run 2026-09-03).
- **Decisions (+ why):** promote-not-unignore (a tracked copy is a regression
  baseline; `quality/authored/` stays build output); `MM_COOKBOOK_DIR` defaults
  from the package location so a clone needs no config, and the wheel does not
  package `cookbook/` (GitHub-clone is the distribution route); `list_examples`
  shape change accepted as a 0.x breaking change with zero external users;
  `--check` compares parsed JSON, not bytes, because builders write CRLF on
  Windows while git checks out LF (do not pin `*.ptex eol=lf` without keeping
  that); `promote --check` left to fail loudly on malformed JSON (dev tooling).
- Seven rulings made on Grayson's behalf are listed in the commons log
  `_agent-commons\log\2026-09-03-claude-code-mm-mcp-teardown2-cookbook-as-data.md`.

## 🗂️ Changed this session (wool-knit closed, f07 herringbone tweed, +4 terrain)

- Branches/commits: `main`, `8ca2c2b` (f07 herringbone tweed + wool-knit closure)
  and `6ed5773` (terrain t05-t08), both **pushed** to `origin/main` (CI triggered).
  Files: `quality/cookbook_fabrics.py` (f07 builder), `quality/cookbook_terrain.py`
  (`_dry_earth_plates` helper + t05-t08 builders), `docs/AUTHORING.md` (f07 recipe
  + wool-knit closure; terrain topology-not-donor section + 4 recipes), 5 tracked
  thumbnails (`docs/images/cookbook-fabrics/f07_herringbone_tweed.png`,
  `docs/images/cookbook-terrain/t05-t08.png`). Authored `.ptex` + renders (incl.
  throwaway `scratch-knit/`) stay gitignored. No `src/` change, no gate/phase moved.
- **Wool loop-knit CLOSED as unreachable.** Isolation-render probe (each candidate
  generator's raw pattern through a gray ramp, look for the knit tell) tested 4
  leads: pattern-Bounce + `bricks` Running Bond = staggered pillow honeycomb;
  `weave2` stitch=1 = basket weave; `weave2` stitch=3 = herringbone chevrons that
  reverse band-to-band = herringbone, not knit. **Reframe: "offset rows" and
  "V-columns in aligned wales" are INDEPENDENT; only the second is the knit tell.**
- **`f07_herringbone_tweed`** = weave2 stitch=3, warm Harris-tweed 3-tone, soft
  `param1` 0.35 `param4=0`. One-tone limit noted (weave2 emits one grayscale).
- **Terrain t05-t08 + the topology-not-donor lesson (the durable takeaway).** First
  pass cloned `dry_earth` 4x -> siblings; Grayson caught it. Fix: pick base by
  surface TOPOLOGY. Connected crack network (ice, lava) = dry_earth plates (lava
  glow: `warp_0` crack signal -> `colorize_glow` -> Material emission port 3,
  `emission_energy` 1.0). Discrete packed cells (pebbles) = voronoi + `warp_0`
  ~0.02 (recessed contact joints, not crack lines). Scattered pieces (forest floor)
  = re-based OFF dry_earth onto `fbm` noise=Cellular 4 (the scattered-clump base
  from the noise gallery). Ice smoothness pass: feed the crack-only signal
  (`colorize_4`) into the normal instead of the grainy `blend_1` height. New
  `_dry_earth_plates` helper feeds a FLAT roughness texture so an ORM map exports
  for the preview (dry_earth leaves the roughness input unconnected otherwise).
- Process: `brainstorming` (bounded) + `advisor` twice (the chevron reframe on
  wool, the topology reframe on terrain). Judged every material in 3D via
  `render_preview` and sent previews to Grayson each pass. `render_preview` has no
  emission slot, so lava's glow was judged on the exported emission map.

> 📦 **21 older "Changed this session" write-ups archived** (through
> 2026-09-01, incl. the blend-opacity debug swatches, the painted-metal cookbook, and the v0.4.0 release-unblock
> + README gallery session) --
> the pre-release audit/teardown/doc-fix pass,
> render_node_output/live_render_node_output (item H), saved_graphs/
> round-trip, Unity export proof, wood/stone cookbooks, the overlay
> read-only `rmtree` fix, Phase 5 hands-on verification + `live_clear`, the
> `connect_or_launch` readiness race, and the Phase 5 MCP tool surface --
> moved to [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md) per the trim
> convention (see the note above the Session log below).

## ⚠️ Heads-up for the next agent

- **`list_examples` / `load_example` changed shape 2026-09-03.** `list_examples`
  returns `{"ok": True, "examples": [{"name", "source", "category"}]}` (not a list
  of names); `load_example` returns `{"ok": False, "error": ...}` for unknown
  names instead of raising, and tries `cookbook/` before Material Maker's bundled
  examples. Cookbook materials are edited by rebuilding with
  `quality/cookbook_<category>.py` then `quality/promote_cookbook.py`; edit the
  builder, never the tracked `.ptex` by hand (`--check` would flag it).
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
> cost by the 2026-08-29 teardown (Maintainer lens). **29 older entries are
> now archived there**, from the 2026-08-29 README-images session back
> through the project's Phase 1-2 kickoff on 2026-08-25.


### 2026-09-04 (v0.5.0 release + AUTHORING split + hygiene): the guide becomes a resource, recipes become cards
- `pickup` reconciled clean (`main` at `66661f5`); confirmed release PR #2 now
  correctly proposed 0.5.0 (the `bump-minor-pre-major` fix from last session held).
  Grayson picked briefing options 1, 2, 3 (AUTHORING split, merge release, hygiene).
- Sequenced 2 -> 1 -> 3 (advisor confirmed merge-first avoids a PR rebase). Merged
  release-please PR #2 -> v0.5.0; synced local `main`.
- AUTHORING split via `phased-rebuild` -> `writing-plans` (11-task plan) ->
  `subagent-driven-development`. Phase-0 investigation cleared the advisor's blocker
  (all cookbook tooling globs `*.ptex`, so `.md` cards are safe beside graphs).
  Task 1 = the `guide://authoring` resource; 3 batched card dispatches = 43 cards;
  Task 10 = guide trim (996->308, cross-material lessons lifted); Task 11 =
  references + parity gate + em-dash/backtick sweeps. Every dispatch reviewed;
  final whole-branch review clean on opus. Merged `--no-ff` (`6c2edf0`), pushed,
  branch deleted, SDD workspace removed.
- Hygiene pass (`cd900f0`): quality/README "informal" fix + em-dash sweep,
  docs/superpowers/README execution-history label, contact sheet 5.45->0.99MB,
  server.py docstring em dash. Deferred (surfaced): `examples/` fold (load-bearing)
  and `HANDOFF_ARCHIVE.md` deletion (Grayson's call).
- release-please opened PR #3 (0.6.0), left for Grayson. Then this wrap-up.

### 2026-09-03 (teardown #2 + cookbook-as-data): the cookbook becomes tracked, MCP-served data
- `pickup` (clean `main` at `4136c9e`) chained into `teardown` #2. Evidence: full
  tree, git log, per-area line counts, GitHub API (0 stars, 8 unique viewers in
  14 days, release PR #2 open since 08-30). Headline: the 43 cookbook graphs were
  gitignored build output invisible to the MCP tools while 21MB of their PNGs
  were tracked; STATUS.md header a 7.3KB paragraph; README said 28 materials /
  seven categories vs 43 / eight on disk; live-control unused since 08-28.
  Verdicts: keep core + live (frozen) + swatches + gallery + test set; refactor
  cookbook, `author.py`, AUTHORING, STATUS header, image sets, release cadence;
  kill `examples/` and the archive. Report sent as a file.
- Grayson picked #1. `phased-rebuild` -> `writing-plans` (spec + 7-task plan) ->
  `subagent-driven-development` on branch `cookbook-as-data`. Task reviews caught
  two real issues (dropped `quality/cookbook/` ignore rule; unguarded doctor
  call). Final review (most capable model): "with fixes", the big one being that
  release-please lacked `bump-minor-pre-major`, so the `feat!` commit would have
  cut 1.0.0; also `glob.escape` on the user-configurable cookbook dir, a
  `--check` false-positive "in sync" on a missing/unmatched authored dir, a
  byte-vs-JSON compare, `load_example` raising on malformed JSON. One fix wave,
  scoped re-review clean. Fast suite 378.
- Merged `--no-ff` (`530ad0f`), pushed, branch deleted, SDD workspace removed.
  Wrap-up capped STATUS.md's header (old text archived verbatim), wrote memory
  and the commons log.

### 2026-09-03 (wool-knit closed, f07 herringbone tweed, +4 terrain) — topology-not-donor
- Picked up via `pickup` (clean `main` at `e7bb420`). Grayson chose wool loop-knit
  lead #1 (offset rows). `brainstorming` + `advisor` reframed it: stockinette's
  tell is chevron/V in ALIGNED wales, not offset rows. Cheap isolation-render probe
  (raw generator through a gray ramp) tested 4 leads and confirmed the catalog has
  NO stockinette-knit generator. Closed wool-knit as unreachable; shipped the
  probe's byproduct as `f07_herringbone_tweed`. Finalized + pushed (`8ca2c2b`).
- Grayson: "more natural surfaces." Built terrain t05-t08 (ice/lava/forest floor/
  pebbles). First pass cloned `dry_earth` 4x -> siblings; Grayson caught it.
  `advisor` reframe -> pick base by TOPOLOGY not donor. Re-based (crack-network vs
  packed-cells vs scattered-pieces); lava glow via emission port 3; forest floor
  onto `fbm` Cellular 4; ice smoothness pass; flat-roughness-texture for ORM export.
  All 4 authored -> rendered -> 3D-previewed -> locked. Finalized + pushed (`6ed5773`).
- Wrote `_agent-commons/log/2026-09-03-claude-code-mm-mcp-herringbone-tweed-knit-probe.md`.
  Then this wrap-up (HANDOFF/STATUS baton).

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

_(Older entries continue in [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).)_

