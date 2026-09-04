# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-03 (plastics category + Donegal tweed cookbook additions) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**Plastics (new category) and a second, differently-flecked tweed both
landed in the cookbook: `p01_glossy_plastic` and `f08_donegal_tweed`.**
`main` is at `68c51dc`, pushed and in sync. Cookbook is now 46 materials
across ten categories (was 44/nine).
- Picked up on the two smallest open backlog items from the prior session's
  briefing (plastics, two-color tweed). Scoped via `brainstorming` (bounded
  path): plastics differentiates through the ABSENCE of visible
  micro-pattern (every other category so far uses one), so it's the first
  cookbook material built from scratch via `_from_scratch_noise_material`
  rather than cloned from a donor. Tweed differentiates through color
  (flecks) rather than weave geometry (f07's chevron).
- `p01_glossy_plastic`: narrow near-single-color saturated red albedo, low
  roughness (glossy), non-metallic, normal relief kept just above zero
  (`param1=0.04`, `param4=0`). Hit the same scalar-roughness ORM gap
  `gl01_frosted_glass` did; fixed the same way, a flat `rough_const`
  texture wired into `Material` port 2.
- `f08_donegal_tweed`: plain `weave2` base (`stitch=1`) plus a SEPARATE
  `voronoi` node purely for flecks (retyping the base loses its own
  rand3 output), hard-thresholded to the top ~20% of cells for sparse
  coverage, cream/rust two-tone color. First pass was too sparse (~4
  flecks per crop, sent to Grayson, revised); second pass approved.
  Composited via `blend` (`blend_type=0`, base on majority port 1, flecks
  on minority port 0, mask on port 2).
- Both promoted through `promote_cookbook.py`, carded, thumbnailed
  (`_make_previews.py`). README counts updated (44/nine -> 46/ten).
  **Real gotcha hit and worked around:** re-rendering a whole
  `cookbook-<category>` label for one new entry re-renders and
  re-thumbnails every case in it; `f04_wool_knit`'s thumbnail came out
  byte-different (render non-determinism, not a content change) and had
  to be reverted before committing. Fast suite 447 -> 453.

**Before this, the "image-to-material decomposition" backlog idea closed: a
reference-photo authoring workflow is documented and proven with a real
cookbook material.**
- Scoped via `brainstorming`: the decomposition reasoning happens in
  Claude's own vision during a chat session, no new server code, no new MCP
  tool, no new dependency, which downgraded the task from architectural to
  bounded (a documented workflow, not a subsystem).
- New "Authoring from a reference photo" section in `docs/AUTHORING.md`,
  extends the existing step-1 workflow with a decomposition rubric
  (color/tone, pattern topology, scale, roughness, relief cues), reusing
  the noise vocabulary and cross-material lessons already documented rather
  than inventing new taxonomy.
- Proved it out end to end: sourced a real CC-BY-SA 4.0 macro photo of
  sandblasted glass (Wikimedia Commons), decomposed it, and authored
  `cookbook/glass/gl01_frosted_glass`, cloning `dry_earth`'s connected-
  crack-network topology at a much finer scale, judged in the 3D preview,
  promoted through the normal `promote_cookbook.py` path. First entry in a
  new `glass` category, closes half of the glass/plastics backlog gap.
  Fast suite 444 -> 447.
- Also cleared a pre-existing stale local build artifact
  (`quality/authored/cookbook-fabrics/f04_wool_knit/`, gitignored, left
  over from the 2026-09-01 wool-knit exploration) that was making
  `promote_cookbook.py --check` report false drift.

**Before this, v0.6.0 was released and both items surfaced two sessions ago
were done: the `author.py` split and the donor-vendoring project.**
- **v0.6.0 released** by merging release-please PR #3, a pure metadata bump
  (CHANGELOG + version, no code changes). Fast-forwarded local `main`.
- **`quality/author.py` split (bounded task, no spec doc):** the file mixed
  ~11 pure graph-surgery helpers with the 12 Phase-3 `build_*` case builders.
  Extracted the helpers into a new `quality/author_helpers.py`; `author.py`
  now holds only the builders, the `BUILDERS` registry, and the CLI. 10
  consumer files (`quality/cookbook_*.py` x8, `debug_swatches.py`,
  `noise_gallery.py`, plus `tests/test_author_helpers.py`) repointed at the
  new module. Pure move, zero behavior change, verified byte-identical.
- **Donor-vendoring project (the scope-corrected "fold examples" item):**
  "`examples/`" in the last handoff meant `cfg.examples_dir`, Material
  Maker's own 43 bundled upstream demo graphs inside the external, un-tracked
  `z-Git\material-maker` checkout, not this repo's local `examples/`
  showcase folder (unrelated, never code-referenced). Auditing every
  `load_example()` call site found only **9 of the 43 are load-bearing**
  donors for the Phase 3 authoring pipeline. Vendored just those 9 into a
  new tracked `quality/donors/` directory; `load_example()` now reads from
  there. Everything else that reads `cfg.examples_dir` (the MCP
  browse-examples feature, the setup doctor, the Phase 1 gate test
  validating all 43, two render/preview smoke tests) is deliberately
  untouched and still reads live from the external checkout.
- **Process:** spec (`docs/superpowers/specs/2026-09-03-vendor-donor-examples-design.md`)
  + plan (`docs/superpowers/plans/2026-09-03-author-helpers-donor-vendor.md`,
  4 tasks) -> `subagent-driven-development` on branch
  `author-helpers-donor-vendor`. One task-level fix round (Task 3's brief
  omitted `tests/test_donors.py` from its own commit command, fixed with a
  follow-up commit). Final whole-branch review (opus): "with fixes" -> one
  fix wave (7 stale "author.py" doc references left over from the split) ->
  clean. Fast-forward-merged to `main` (no divergence to reconcile), pushed.
  Fast suite 424 -> 444.

Older write-ups/log beyond the cap live in
[docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).

## 📌 Where we stopped

`main` at `68c51dc`, pushed and in sync. Plastics category and Donegal tweed
both promoted, carded, and green on the fast suite. Natural stopping point,
no open decision blocking the next session.

## ▶️ Next concrete step

Nothing is blocking on Grayson right now.
1. **This session's tool list showed `mcp__unreal-engine__*` tools
   connected** (see the drift note an earlier pickup briefing surfaced).
   **A. Unreal UE5 export verification** has been blocked for multiple
   sessions on "needs a live Unreal Editor with the MCP bridge connected,
   Grayson said it wasn't as of an older session" — worth a live check now
   that the bridge appears to be up, before assuming it's still blocked.
2. **"Material Maker for dummies" — a simplified interface, unscoped.**
   Grayson's backlog idea (captured in full in
   `_agent-commons/ideas/Tool-MaterialMaker-MCP.md`): the real node graph
   can be intimidating to a non-technical viewer; is there a simpler
   on-ramp? Explicitly deferred pending its own `brainstorming` session,
   worth checking against `docs/NORTH_STAR.md`'s round-trip-learning-tool
   framing first, since hiding the graph outright vs. exposing a simplified
   parameter panel on top of a graph mm-mcp already authored are very
   different scope bets.
3. **More cookbook categories/materials** remain an open-ended, no
   specific quick-win flagged right now (glass, plastics, and a second
   tweed variant all landed across the last two sessions). New materials
   land in `cookbook/` via `promote_cookbook.py`, then get a card at
   `cookbook/<category>/<id>.md`.

The older open backlog, unchanged unless noted:
- **2 findings ruled out, not fixed** (deliberate): #8 (`_cmd_clear_graph`'s
  guard is correct, `new_material()` creates the generator, doesn't read
  one) and #10 (`generic_size or 1` coercion is safer than passing an
  explicit 0). Both annotated in-code. Findings 3-7 and 9 are fixed.
- **`list_node_types` tool decision — KEEP.** ~5KB name list vs the ~260KB
  full `catalog://nodes` resource, so it's the cheap discovery lever, not
  redundant with the resource + `describe_node`.
- **B. More cookbook categories** — fabrics, organics, sci-fi, terrain, wood,
  stone, leather, painted-metal, glass, and now plastics are all
  represented (ten categories, 46 materials); terrain includes the
  natural-surface set (ice/lava/forest floor/pebbles). No specific
  remaining gap flagged right now.
- **C. True cobblestone — DONE.** `s07_cobblestone` closed this; the `s05`
  hex-grid partial is superseded.
- **D. Wool loop-knit — CLOSED as unreachable.** No bundled generator makes
  upright-V stockinette; `f04` stays the honest coarse-weave stand-in and
  `f07_herringbone_tweed` shipped as the closing probe's byproduct.
- **E. Image-to-material decomposition — CLOSED, 2026-09-03.** Shipped as
  the "Authoring from a reference photo" section in `docs/AUTHORING.md`
  plus `cookbook/glass/gl01_frosted_glass` as the worked proof. Scoped to
  Claude's own vision doing the decomposition in-session, no new server
  code or MCP tool.
- **F. PyPI publish** (on hold; GitHub-clone is the current route).
- **J. Load an existing `.ptex` into a live session.** No `live_load`
  equivalent exists. Lowest priority of the remaining live-mode gaps.

## ❓ Open questions

- **New 2026-09-03:** `quality/README.md`'s "Cookbook growth" section was
  corrected this session (it still said helpers were "imported from
  `author.py`"), but hasn't been re-read end to end for other drift since
  the split. Worth a skim next time that file is touched.
- **New 2026-09-03 (parked, not fixed, no downstream dependency):**
  `tests/test_donors.py`'s module-level `build_catalog(cfg.nodes_dir)` call
  means a missing `MM_PROJECT_PATH` fails all 20 donor tests together
  (including the 10 that don't actually need the catalog), not just the 9
  catalog-validation ones. Low blast-radius issue, not a correctness bug;
  worth a `pytest.fixture` split only if it ever actually bites.
- Still open, unchanged: does `backup-ops` exclude the ~1GB of regenerable
  renders under `output/`, `quality/cookbook/`, `quality/runs/` (plus the
  266MB `mm_live_overlay/`)? Flagged by an earlier teardown, not verified.
- Still open, unchanged, deferred minors from the cookbook-as-data reviews
  (all small): `tests/test_config.py`'s default-dir test reads the real
  machine env (pre-existing pattern); `_default_cookbook_dir()`'s empty
  branch is untested; `server.py`'s source-validation error string is
  near-duplicated between the two example tools; the contact sheet adds a
  5MB blob per regeneration.
- Still open, unchanged: the cross-engine North Star wording treats UE4's
  export path (PNGs + manual in-editor assembly) as a lesser tier, not a
  real target, Grayson said "sounds good" generally but never explicitly
  confirmed that specific framing. Worth a quick check before it drives real
  scope decisions.
- Still open, unchanged: is `.mcp.json` the right long-term wiring, or
  should it fold into `project-setup`'s standard kit? Not decided.
- Still open, unchanged: PyPI vs. GitHub-clone-only (leaning GitHub-only);
  cross-platform (macOS/Linux) verification, still untested, no machine
  available; two parked-not-fixed overlay-builder findings from a much
  earlier session (staleness marker, `_append_autoload`'s first-occurrence
  match, both verified low-priority).

## 🗂️ Changed this session (plastics category + Donegal tweed)

- **`quality/cookbook_plastics.py`** (new file): `build_p01_glossy_plastic`,
  the first cookbook material built from scratch via
  `_from_scratch_noise_material` rather than cloned from a donor. Narrow
  near-single-color red albedo, non-metallic, low roughness (`0.18`),
  near-zero normal relief (`param1=0.04`, `param4=0` since the fix still
  applies to a directly-fed perlin). Added a `rough_const` flat-roughness
  texture into `Material` port 2 so ORM exports (same gap
  `gl01_frosted_glass` hit).
- **`quality/cookbook_fabrics.py`**: new `build_f08_donegal_tweed`. Plain
  `weave2` base (`stitch=1`, distinct from f07's herringbone `stitch=3`)
  recolored heather gray-brown. A separate `voronoi_fleck` node (not the
  base generator, which loses its rand3 output once retyped) feeds a
  hard-threshold mask (top ~20% of cells) and a cream/rust two-tone color
  layer, composited via `blend` (`blend_type=0`, base weave on majority
  port 1, flecks on minority port 0, mask on port 2). First pass was too
  sparse (~4 flecks visible per 2048px crop, sent to Grayson); revised the
  threshold and added the second fleck tone, approved on the second pass.
- **`cookbook/plastics/p01_glossy_plastic.{ptex,md}`**,
  **`cookbook/fabrics/f08_donegal_tweed.{ptex,md}`**: promoted via
  `promote_cookbook.py`, recipe cards written, gallery thumbnails
  generated (`_make_previews.py`). `README.md` counts bumped 44/nine to
  46/ten, contact-sheet caption updated (not regenerated, same deliberate
  deferral as glass).
- **Gotcha hit and fixed:** `_make_previews.py cookbook-fabrics` (and
  `render_cookbook.py` before it) regenerate every case in the label, not
  just the new one. `f04_wool_knit`'s thumbnail came back byte-different
  (render non-determinism, the graph itself is unchanged) and was reverted
  before committing to keep the diff scoped to the real work.
- **Process:** `pickup` chained straight into `brainstorming` (bounded
  path, no plan doc) since the prior session's briefing already scoped both
  items into concrete numbered options. Two clarifying questions (plastics
  look, tweed's distinguishing lever vs. f07) then a short in-chat design,
  approved. Each material: build, render, 3D-preview, send to Grayson,
  wait for a look, promote. Fast suite 447 -> 453 (2 new gate tests per
  material: recipe-card parity + thumbnail presence, already existed as a
  parametrized test, just gained 2 more cases). Committed (`68c51dc`) and
  pushed to `main` on Grayson's explicit go-ahead (design approval and push
  approval given separately).

## 🗂️ Changed this session (reference-photo authoring workflow + glass cookbook)

- **`docs/AUTHORING.md`**: new "Authoring from a reference photo" section,
  slotted right after the existing "Authoring workflow" (extends step 1,
  "pick the closest starting graph," to cover a photo instead of just a
  text prompt). A decomposition rubric (color/tone, pattern topology, scale,
  roughness, relief cues) that reuses the noise vocabulary and
  cross-material lessons already in the guide rather than a new taxonomy.
- **`cookbook/glass/gl01_frosted_glass`**: first glass-category material,
  authored end to end from a real CC-BY-SA 4.0 macro photo of sandblasted
  glass (J. Koopstra, Wikimedia Commons). Clones `dry_earth`'s connected-
  crack-network topology at a much finer scale (`voronoi_0` scale 60 vs.
  the default 4), recolored cool blue-gray, high uniform roughness, subtle
  relief (`normal_map` `param4=0` at low `param1=0.15`). Card documents an
  honest limitation: Material Maker has no true transparency/refraction
  model, so this approximates frosted glass as an opaque matte diffuse
  surface, which is right for how it will be used but not a light-
  transmission simulation. `quality/cookbook_glass.py` new builder,
  promoted through the normal `promote_cookbook.py` path.
- **`README.md`**: material/category counts bumped 43/eight to 44/nine; the
  contact-sheet caption now notes it has not been regenerated to include
  glass yet (real cost, a multi-MB image rebuild, left as a deliberate
  follow-up).
- Cleared a pre-existing stale local build artifact
  (`quality/authored/cookbook-fabrics/f04_wool_knit/`, gitignored, left
  over from the 2026-09-01 wool-knit exploration) that was making
  `promote_cookbook.py --check` report false drift on an unrelated
  category. Local-only fix, nothing to commit (the path is gitignored).
- **Process:** `pickup` -> `brainstorming` on the "image-to-material
  decomposition" backlog idea. Two scoping questions collapsed the task
  from architectural to bounded: the decomposition reasoning happens in
  Claude's own vision during a chat session (no new server code, no new
  MCP tool, no new dependency), so the actual deliverable is a documented
  workflow, not a subsystem. Sourced the reference photo via `WebSearch` +
  `WebFetch` against Wikimedia Commons after an early attempt to browse
  `ambientcg.com` hit a malicious ad redirect to a fake "McAfee Security"
  scareware page (`securesweep.pro`); closed the tab immediately without
  interacting. Implemented directly (bounded path, no plan doc), committed
  and pushed to `main` on Grayson's explicit approval of both the design
  and the push.
- Fast suite 444 -> 447.

## 🗂️ Changed this session (v0.6.0 release + author.py split + donor vendoring)

- **v0.6.0 released:** merged release-please PR #3 (`88dcaa9`), synced local
  `main`. Pure metadata bump (CHANGELOG + version), no code changes.
- **Scope correction (the session's key finding):** "fold `examples/` into
  the cookbook" from last session's handoff was ambiguous between this
  repo's own local `examples/` showcase folder and `cfg.examples_dir`
  (Material Maker's 43 bundled demo graphs in the external checkout).
  Confirmed it meant the latter, then audited every `quality/*.py`
  `load_example("...")` call site and found only 9 names in real use:
  `beehive`, `crocodile_skin`, `dry_earth`, `metal_pattern_2`, `rock`,
  `rusted_metal`, `stone_wall`, `wood`, `wooden_floor`. Grayson chose to
  vendor just those 9, not all 43, and to keep browsing/the Phase 1 gate
  live against the external checkout (not also scope those down).
- **`author.py` split, branch `author-helpers-donor-vendor` (bounded task,
  no spec):** `quality/author_helpers.py` (new) now holds `load_example`,
  `node`, `set_gradient`, `set_param`, `save_variant`, `rewire`,
  `drop_conn`, `add_node`, `retype`, `_grad`, `_from_scratch_noise_material`.
  `quality/author.py` keeps only the 12 `build_*` functions, `BUILDERS`, and
  `main()`. 10 files repointed (`from author import ...` -> `from
  author_helpers import ...`): `cookbook_fabrics.py`, `cookbook_stone.py`,
  `cookbook_scifi.py`, `cookbook_painted_metal.py`, `cookbook_organics.py`,
  `cookbook_leather.py`, `cookbook_wood.py`, `cookbook_terrain.py`,
  `debug_swatches.py`, `noise_gallery.py`, `tests/test_author_helpers.py`.
- **Donor vendoring:** new tracked `quality/donors/` (9 `.ptex` files,
  byte-for-byte copies of Material Maker's bundled examples, sha256-verified
  identical to source, plus a provenance `README.md`). `author_helpers.py`'s
  `load_example()` now reads from `quality/donors/` instead of
  `_CFG.examples_dir`. New `tests/test_donors.py` (20 tests: presence + JSON
  validity + catalog validation + a source-path pin). Config, doctor,
  `server.py`'s `list_examples`/`load_example` MCP tools, the Phase 1 gate
  test, and the render/preview smoke tests are all untouched, confirmed by
  the final review against the plan's explicit out-of-scope list.
- **Process:** `pickup` chained the merge into `brainstorming` (classified
  the `author.py` split as bounded, the donor question as architectural)
  -> spec -> `writing-plans` (4 tasks) -> `subagent-driven-development`.
  Worked on a feature branch in the main checkout, not a worktree, same
  reason as the AUTHORING split session (`.venv` is an editable install
  resolving `mm_mcp` from the main checkout's `src/`). One task-level fix
  round: Task 3's own brief only staged `quality/donors/` in its commit
  command, leaving `tests/test_donors.py` uncommitted; fixed with a
  follow-up commit, not an amend. Final whole-branch review (opus) found 1
  Important + 6 Minor, all the same shape (stale "author.py" doc references
  left over from the split, e.g. `quality/README.md`'s "Cookbook growth"
  section); one fix wave addressed all 7, scoped re-review clean.
  Fast-forward-merged to `main` (54693fb), pushed, branch deleted, SDD
  workspace removed. Fast suite 424 -> 444.
- **Decisions (+ why):** vendor 9 of 43, not all 43, most of the other 34
  are Material Maker's own art/pattern demos (mandelbrot, skulls,
  raymarching), not material recipes, folding them into a curated,
  recipe-carded cookbook would blur what the cookbook is for. Browsing
  stays live against the external checkout (Option A of two presented) so
  only the authoring pipeline's own reproducibility improves, not the
  MCP-facing discovery surface. New commits over amends for the Task 3 fix,
  per this repo's standing convention.
- Six rulings made on Claude's own authority during execution (worktree vs.
  branch; ratifying the implementer's `_grad`/`_ROOT` fix to a gap in the
  plan's own brief; the Task 3 commit fix; batching the final review's 7
  findings into one fix dispatch; two parked test-design nits in
  `tests/test_donors.py`) are listed in full in the commons log
  `_agent-commons\log\2026-09-03-claude-code-mm-mcp-v060-release-donor-vendor-spec.md`
  and this session's own wrap-up report.

> 📦 **24 older "Changed this session" write-ups archived**, newest first the
> 2026-09-04 v0.5.0 release + AUTHORING split + hygiene session, then the
> 2026-09-03 teardown #2 + cookbook-as-data session, then through
> 2026-09-01, incl. the wool-knit closure/f07/terrain session, the blend-opacity
> debug swatches, the painted-metal cookbook, and the v0.4.0 release-unblock
> + README gallery session --
> the pre-release audit/teardown/doc-fix pass,
> render_node_output/live_render_node_output (item H), saved_graphs/
> round-trip, Unity export proof, wood/stone cookbooks, the overlay
> read-only `rmtree` fix, Phase 5 hands-on verification + `live_clear`, the
> `connect_or_launch` readiness race, and the Phase 5 MCP tool surface --
> moved to [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md) per the trim
> convention (see the note above the Session log below).

## ⚠️ Heads-up for the next agent

- **`render_cookbook.py <label>` and `_make_previews.py <label>` operate on
  the WHOLE label, not just the case you're adding.** Adding one material to
  an existing category (e.g. `f08_donegal_tweed` to `cookbook-fabrics`) and
  running these regenerates and re-thumbnails every other case in that
  category too. Godot's own render is not perfectly deterministic run to
  run, so an unrelated case's thumbnail can come back byte-different with
  zero content change. Always `git status` after these before committing,
  and revert anything that changed only because it got swept up in the same
  label's regen.
- **`ambientcg.com` redirected to a malicious scareware page during this
  session** (a fake "McAfee Security" page at `securesweep.pro`, hit via
  the in-app Browser pane's `navigate`). Closed the tab immediately without
  interacting; switched to Wikimedia Commons for reference photos instead,
  which worked cleanly. Worth avoiding `ambientcg.com` until/unless
  verified safe again.
- **`docs/AUTHORING.md` now has an "Authoring from a reference photo"
  section** right after the main workflow list. If a future session is
  asked to build a material from an attached photo, read that section
  first, it's a decomposition rubric that plugs into the existing donor/
  topology vocabulary, not a separate pipeline.
- **`quality/author.py` is now a builders-only file; graph-surgery helpers
  live in `quality/author_helpers.py`.** If you're adding a new cookbook
  category or debug swatch, `from author_helpers import ...` the helpers
  (`load_example`, `node`, `set_gradient`, `set_param`, `save_variant`,
  `rewire`, `drop_conn`, `add_node`, `retype`, `_grad`), not `from author
  import ...`, that module now only exports the 12 Phase-3 `build_*`
  functions, `BUILDERS`, and `main()`.
- **Donor graphs (`beehive`, `crocodile_skin`, `dry_earth`, `metal_pattern_2`,
  `rock`, `rusted_metal`, `stone_wall`, `wood`, `wooden_floor`) load from
  `quality/donors/`, a tracked directory in this repo, not the external
  Material Maker checkout anymore.** If you add a 10th donor to any builder,
  vendor its `.ptex` into `quality/donors/` too (copy from
  `<MM_PROJECT_PATH>/material_maker/examples/<name>.ptex`), `load_example()`
  won't find it in the external checkout's path anymore. Browsing all 43 of
  Material Maker's bundled examples over MCP (`list_examples(source=
  "material_maker")`) and the Phase 1 gate test are unaffected by any of
  this, they still read live from the external checkout.
- **`list_examples` / `load_example` changed shape 2026-09-03.** `list_examples`
  returns `{"ok": True, "examples": [{"name", "source", "category"}]}` (not a list
  of names); `load_example` returns `{"ok": False, "error": ...}` for unknown
  names instead of raising, and tries `cookbook/` before Material Maker's bundled
  examples. Cookbook materials are edited by rebuilding with
  `quality/cookbook_<category>.py` then `quality/promote_cookbook.py`; edit the
  builder, never the tracked `.ptex` by hand (`--check` would flag it).
- **The 2026-08-29 8-angle code review found 10 verified correctness bugs.
  As of a prior cleanup session: 7 are fixed (findings 1-7 and 9), and 2 are
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
  before `rmtree` -- fixed a prior session, real and load-bearing, not
  theoretical.** The overlay is a full copy of the real git checkout at
  `z-Git\material-maker`; git marks `.git/objects/pack/*.idx` read-only,
  and `shutil.rmtree` can't delete a read-only file on Windows without
  help. Fixed via a `_clear_readonly()` helper in `overlay.py`, called right
  before `rmtree`. If `live_start`/`connect_or_launch` ever fails again with
  a bare, detail-free MCP error, reproduce directly via
  `.venv\Scripts\python.exe -c "from mm_mcp import live; live.connect_or_launch()"`
  rather than trusting the MCP tool's error message -- it swallows
  exception detail on a raise; the real traceback only shows up outside it.
- **`ping`'s response has a `has_graph` field alongside `ready`, and they
  mean different things -- don't conflate them.** `ready` is purely
  "main_window resolved." `has_graph` is "a graph tab actually exists"
  (`get_current_graph_edit()`/`.generator` non-null). `connect_or_launch`
  requires both before declaring a session usable.
- **`server.py` has four live MCP tools consuming `live.py`:**
  `live_start`/`live_get_graph`/`live_apply`/`live_render`, all going through
  a shared `_ensure_live_session(cfg, launch_timeout=60.0)` helper that
  calls `live.connect_or_launch` fresh every time. **Do not read
  `server._live_session` directly** to check on a launched process --
  always call `_ensure_live_session(cfg)` yourself, the module global is
  internal bookkeeping, not a public handle.
- **`live_apply(ops)` dispatches via `_LIVE_OP_HANDLERS`, a dict keyed by
  `op["op"]`** (`"add_node"`/`"connect_nodes"`/`"set_param"`), stops at the
  first failing op, and reports a malformed op as a data-shaped error rather
  than raising. If you add a fourth op kind, add its handler to that dict
  and nowhere else.
- **Run tests with `.venv\Scripts\python.exe`** (or activate the venv).
  Fast suite: `pytest -q -m "not integration"` (444 passed, 23 deselected).
  `pytest -q` adds the Godot-launching integration tests.
- **`mm-mcp --check`** is the setup doctor (green/red preflight); `--version`,
  `--help` also work. Build/release tooling lives in the `release` extra
  (`pip install -e .[release]` -> build, twine).
- All Phase 1-2 render gotchas still hold (see CLAUDE.md): `--export-material`,
  `_console.exe`, no `--headless`, `steam_appid.txt`.
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
> cost by the 2026-08-29 teardown (Maintainer lens). **31 older entries are
> now archived there**, from the 2026-09-01 noise-vocab-gallery session back
> through the project's Phase 1-2 kickoff on 2026-08-25.


### 2026-09-03 (plastics category + Donegal tweed): a smooth surface and a fleck lever, both closing out the same backlog batch
- `pickup` reconciled clean (`main` at `5239283`). Grayson picked "1 + 4"
  from the briefing's numbered options: the plastics cookbook entry and
  two-color tweed.
- `brainstorming` (bounded path, no plan doc): two clarifying questions
  settled the specifics (glossy vs. matte vs. textured plastic; flecked
  Donegal-style vs. two-tone herringbone for the tweed), then a short
  in-chat design, approved.
- `p01_glossy_plastic`: built from scratch (no donor fits a "smooth,
  patternless" surface), narrow near-single-color red albedo, low
  roughness, near-zero relief. Hit and fixed the same scalar-roughness ORM
  gap `gl01_frosted_glass` did. Preview sent, approved first try.
- `f08_donegal_tweed`: plain-weave base plus a separate voronoi node for
  sparse cream/rust flecks via the port-2 rand3 lever, composited with
  `blend`. First preview read too sparse (~4 flecks per crop); revised the
  mask threshold and added a second fleck tone, second preview approved.
- Both promoted, carded, thumbnailed, README counts updated (44/nine to
  46/ten). Reverted an unrelated `f04_wool_knit` thumbnail regeneration
  (render non-determinism, not a real change) before committing. Fast
  suite 447 -> 453. Committed (`68c51dc`) and pushed on explicit
  instruction ("push it + wrap"). Then this wrap-up.

### 2026-09-03 (reference-photo authoring workflow + glass cookbook): the assistant learns to read a photo, not just a sentence
- `pickup` reconciled clean (`main` at `692057b`). Grayson picked backlog
  item #4, "image-to-material decomposition," from the briefing's numbered
  options.
- `brainstorming` classified it architectural at first (a new subsystem),
  then a scoping question collapsed it to bounded: the decomposition
  reasoning happens in Claude's own vision during the chat session itself,
  not a new server-side vision tool, so the real deliverable is a
  documented workflow addition to `docs/AUTHORING.md`, not a subsystem.
  Grayson also chose to include a worked proof (not guidance-only) and to
  commit the proof as a real cookbook entry (not throwaway).
- Sourced a CC-BY-SA 4.0 reference photo. An early attempt to browse
  `ambientcg.com` hit a malicious ad redirect to a fake "McAfee Security"
  scareware page (`securesweep.pro`); closed the tab immediately without
  interacting and switched to Wikimedia Commons, which worked cleanly.
- Wrote the "Authoring from a reference photo" section, then authored
  `cookbook/glass/gl01_frosted_glass` end to end from the photo: decomposed
  it against the new rubric, matched it to `dry_earth`'s connected-crack-
  network topology at a much finer scale, built and rendered the graph,
  judged it in the 3D preview (sent to Grayson for a look), promoted it
  through `promote_cookbook.py`. Fast suite 444 -> 447. Committed and
  pushed to `main` (`9a02a8d`) on Grayson's explicit go-ahead.
- Wrote the session's commons log entry, then Grayson asked for one more
  fix: a stale gitignored build artifact (`f04_wool_knit`, unrelated to
  this session) was making `promote_cookbook.py --check` report false
  drift. Cleared it, confirmed clean, then this wrap-up.

### 2026-09-03 (v0.6.0 release + author.py split + donor vendoring): the pipeline stops depending on the external checkout
- `pickup` reconciled clean (`main` at `677f852`), then merged release-please
  PR #3 straight away (0.6.0, pure metadata bump) since it was the standing
  next step. Grayson picked options 1 + 2 from the briefing: decide the two
  deferred hygiene items, and scope the `author.py` refactor.
- Asked Grayson directly: fold `examples/` into the cookbook (chosen), keep
  `docs/HANDOFF_ARCHIVE.md` (chosen, no longer an open item). `brainstorming`
  on both remaining tasks surfaced the scope correction: "examples/" meant
  `cfg.examples_dir` (Material Maker's 43 bundled demos in the external
  checkout), not this repo's own `examples/` folder. Auditing every
  `load_example()` call site found only 9 of 43 are load-bearing donors.
  Grayson chose to vendor just those 9 and keep browsing/the gate live
  against the external checkout.
- Spec written and approved
  (`docs/superpowers/specs/2026-09-03-vendor-donor-examples-design.md`),
  4-task plan (`docs/superpowers/plans/2026-09-03-author-helpers-donor-vendor.md`)
  -> `subagent-driven-development` on branch `author-helpers-donor-vendor`
  (feature branch in the main checkout, not a worktree, same editable-`.venv`
  reason as the AUTHORING split). Task 1 extracted the helpers into
  `author_helpers.py` (the implementer caught and fixed a real gap in my own
  brief: it omitted `_grad`/`_ROOT`, which `author.py`'s own remaining code
  still needs). Task 2 repointed 10 consumer files. Task 3 vendored the 9
  donors (one fix round: a required test file was created but never
  committed, because the plan's own commit command omitted it, fixed with a
  follow-up commit). Task 4 repointed `load_example()`, proved byte-identical
  builder output before/after via a real before/after hash comparison.
- Final whole-branch review (opus): "with fixes" -- 1 Important + 6 Minor,
  all stale "author.py" doc references left over from the split (e.g.
  `quality/README.md`'s Cookbook-growth section). One fix wave, scoped
  re-review clean. Fast-forward-merged to `main` (`54693fb`), pushed, branch
  deleted, SDD workspace removed. Fast suite 424 -> 444.
- Then this wrap-up (HANDOFF baton, memory, commons log).

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

_(Older entries continue in [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).)_
