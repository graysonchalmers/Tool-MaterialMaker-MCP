# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-05 (teardown #4 picks 2 + 3: hygiene sweep, builders packaged, Phase-3 harness archived) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

`main` at the merge `87be578` (+ the docs commit that lands this file), pushed,
in sync. Fast suite **635 passed**, 25 integration deselected.
`promote_cookbook.py --check` in sync. `mm-mcp --check` reports 53 cookbook
materials. CI: see the session log for the result of the run on `87be578`.

This session ran `pickup` + a third adversarial `teardown`, then executed its
picks in Grayson's order (backup exclusions first, then examples fold + port
diagnostic, then the baton diet):

- **Backup fixed (item 3).** `backup-ops/projects.psd1` now has a
  `Tool-MaterialMaker-MCP` override excluding `output/`, `mm_live_overlay/`,
  and `quality/{runs,cookbook,authored}` (full paths for the quality ones so
  the tracked `cookbook/` tree keeps backing up). About 1.3 GB of regenerable
  render output had been mirrored nightly through two teardowns. Committed in
  backup-ops (`ca5b3fb`). The 458 MB `output/` scratch was moved to
  `C:\Projects-local\_to_delete\Tool-MaterialMaker-MCP-output-scratch-2026-09-05`
  and an empty `output/` recreated.
- **examples/ folded into the cookbook (item 1).** The 8 Phase-3 hero graphs
  the README gallery linked to lived outside the cookbook, ungrouped (7 of 8
  had zero subgraph nodes), ungated, unserved. Seven are now cookbook
  materials via the frozen `author.py` builders + a new `take_variant` helper
  + `group_into_subgraph`: `s02_gray_granite` (stone), `f01_woven_denim`
  (fabrics), `o01_mossy_forest_floor` (organics),
  `combo01_rusted_painted_steel` (painted-metal), `m01_weathered_copper` +
  `m02_brushed_aluminum` (NEW `metal`), `man02_ceramic_hex_tiles` (NEW
  `ceramic`). `s01_red_brick_wall` was a verbatim copy of the bundled `bricks`
  example and was dropped. Every fold was render-verified against the
  original (`quality/verify_hero_fold.py`, all 7 at `grid_mean_abs_diff=0.000`).
  Cookbook 46 -> 53 materials, 10 -> 12 categories. `examples/` copied to
  `C:\Projects-local\_to_delete\Tool-MaterialMaker-MCP-examples-2026-09-05`
  then `git rm`'d. README repointed; counts stated in digits and enforced by
  `tests/test_readme_counts.py` (materials, categories, live-tool count and
  table). Contact sheet regenerated (53 tiles) and saved as an 8-bit palette
  (1.6 MB; the RGB save was 7 MB and was kept out of `main`'s history).
- **mm-play port diagnostic (item 4).** `play/server.py` probes the port with
  a plain connect before binding (Windows `SO_REUSEADDR` let a second bind
  succeed beside a stale listener, which is how the 2026-09-04 false "GPU
  dead" scare happened), names the owning PID and process via
  netstat/tasklist, prints `Stop-Process -Id N` and the `MM_PLAY_PORT`
  alternative, and binds strictly (`allow_reuse_address = os.name != "nt"`).
  Three real-socket tests.
- **Baton diet (item 2).** This file and STATUS.md rewritten to the shape
  rules above; `docs/HANDOFF_ARCHIVE.md` retired (git is the archive; teardown
  Kill verdict twice); CLAUDE.md trim rule amended; `.env.example` personal
  paths replaced with placeholders.

Built with `writing-plans` -> `subagent-driven-development` (7 tasks, each
reviewed, one plan defect caught and ruled on mid-run, opus whole-branch
review "with fixes", one fix wave, scoped re-review clean). Plan:
`docs/superpowers/plans/2026-09-05-fold-examples-into-cookbook.md`.

## 📌 Where we stopped

Teardown #3's four picks are all done. Nothing is in flight. The teardown
report itself was delivered as a file to Grayson, not committed (same
convention as #1 and #2).

## ▶️ Next concrete step

No forced order. Candidates:

1. **Hands-on verify the `live_load` play path.** Drive `mm-play` against a
   live Material Maker session, pick a material that differs from what is
   loaded, watch it switch in-app, tweak sliders. Promotes "tested" to "you
   saw it work". Ten minutes.
2. **Unreal UE5 export** (backlogged 2026-09-05: memory pressure with a live
   Unreal Editor + bridge; run a `stop-node-hogs` sweep first).
3. **More cookbook materials.** New ones land via `quality/cookbook_<category>.py`
   -> `promote_cookbook.py`, with a card and `group_into_subgraph` from the
   start (see `docs/AUTHORING.md`). No specific gap flagged.
4. **Small hygiene left from teardown #3** (none blocking): thread one catalog
   through `cookbook_wood/glass/plastics.py` like the other builders; move the
   retired plans under `docs/superpowers/` out of the tracked tree or banner
   them as history; `tests/test_donors.py` module-level catalog build makes a
   missing `MM_PROJECT_PATH` fail all 20 donor tests (fixture split).

## ❓ Open questions

- PyPI vs GitHub-clone-only (leaning GitHub-only); macOS/Linux never run, no
  machine. **v0.7.0 released 2026-09-05 CT** (CHANGELOG dates it 09-06 in
  UTC; Grayson had PR #4 merged; it
  carries the play surface, `live_load`, and the examples fold). Release
  cadence is still undecided; release-please opens the next PR automatically.
- NORTH_STAR treats UE4's export path as a lesser tier; Grayson never
  explicitly confirmed that specific framing.
- Is `.mcp.json` the right long-term wiring, or should it fold into
  `project-setup`'s standard kit?
- Two parked, low-priority overlay-builder findings (2026-08-28): no rollback
  if `copytree` fails partway; staleness check hashes only the addon, not the
  MM checkout.
- README's "10 batch-mode tools" is the one count not test-enforced (no robust
  way to count batch tools without a fragile heuristic; ruled skip 2026-09-05).

## ⚠️ Heads-up for the next agent

- **Run quality scripts as `python -m quality.<module>` from the repo root**
  (a file-path launch no longer resolves the package imports; running from
  inside `quality/` also breaks `.env` lookup). Never launch a Godot render
  from `python -c` (the launcher does not exit; use `quality/render_one.py`
  or a script file).
  Renders are one Godot at a time.
- **Edit cookbook materials by changing the builder and re-promoting**, never
  the tracked `.ptex` by hand; `promote_cookbook.py --check` flags drift.
  `render_cookbook.py <label>` / `_make_previews.py <label>` regenerate the
  WHOLE label and Godot is not byte-deterministic, so unrelated thumbnails can
  churn: `git status` and revert anything that changed only by being swept up.
- **`quality/render_compare.renders_match` proves builder-before == builder-after**,
  not that the tracked artifact was already right. Diff the tracked `.ptex`
  against a fresh build before trusting a clean 0.0.
- **`group_into_subgraph` fails silently on a mistyped member name** (the node
  just stays top-level). Check names against the graph first.
- **A `blend` shows port-1 where its port-2 mask is 0 and port-0 where it is 1**;
  put the majority layer on port-1. Opacity = amount x mask, so never feed a
  mid-value colorize as the mask. `normal_map` `param4=0` is the flat-normal
  fix for directly-fed analytic generators. Voronoi output port 2 is the
  per-cell random (fleck) source.
- **Verify metallic/roughness/AO fixes by reading the exported ORM channel**
  (`quality/pngread.py`), not by eye.
- **`take_variant(builder, label, keep_n)`** (author_helpers) runs a frozen
  `author.py` builder under a cookbook label, returns the requested variant,
  and deletes every variant file it wrote; the caller must re-save as v1.
- **Stale mm-play on 8788 is now a startup error with the PID**, not a mystery.
  If you ever see the old symptom anyway (renders "fail" while the code is
  fine), `Get-NetTCPConnection -LocalPort 8788 -State Listen`.
- **The SPIRV `SCRIPT ERROR` at `parse_args.gd:59` prints on every successful
  export.** Red herring; never treat it as evidence of a broken render.
- **`ambientcg.com` redirected to a scareware page (2026-09-03).** Use Wikimedia
  Commons for reference photos until re-verified.
- **`quality/cookbook_wood/glass/plastics.py` still build the catalog inside
  each builder**; the other 9 thread one catalog through `main()`.
- **Donors load from `quality/donors/`** (tracked), not the external MM
  checkout; vendor any new donor `.ptex` there.
- **release-please has `bump-minor-pre-major: true`**; a `feat!` cuts 0.x, not
  1.0.0. Do not remove it.
- **`.mcp.json` and `.env` are gitignored; never echo `.env`.**

## 🕓 Session log

Newest first. Keep at most 8 entries; older ones are in `git log` (search the
commit subjects, every session ends with a `docs:` wrap-up commit).

### 2026-09-05 (teardown #3 executed): examples/ folded, port diagnostic, baton diet
- `pickup` clean, then `teardown` #3: no Rebuild verdicts; findings were the
  ungrouped front-door `examples/`, the baton-as-archive, and 1.3 GB of
  regenerable output in the nightly backup. Grayson picked "3, then 1 + 4, then 2".
- Item 3: backup-ops override + `output/` scratch moved to `_to_delete`.
- Items 1 + 4: `writing-plans` -> `subagent-driven-development`, 7 tasks,
  merged `--no-ff` as `87be578`, pushed. One plan defect (take_variant left
  the kept file) ruled and fixed in Task 2. Final opus review: 3 Important
  (brittle README regexes, 7 MB RGB contact sheet, stale verify docstring),
  fixed in one wave, re-review clean; the palette fix was folded into the
  retire commit by amend + cherry-pick so the 7 MB blob never reached `main`.
- Item 2: STATUS/HANDOFF rewritten to the shape rules above, archive retired,
  CLAUDE.md rule amended, `.env.example` de-personalized.
### 2026-09-05 (mm-play verified): Grayson ran `play.bat` hands-on; row promoted 🔌 -> ✅ (`056dcd4`).
### 2026-09-04 (blocker correction): the "host can't render" blocker was a stale server squatting 8788, not GPU (`b016f1b`).
### 2026-09-04 (live_load): seventh live tool, in-place graph replace; play surface pushes the picked material live (`d523ad6`).
### 2026-09-04 (play-surface UI nits): slider panel docks; canvas re-fills on resize (`c7e85ee`).
### 2026-09-04 (play.bat + play-surface verified): one-click launcher; "MM for dummies" arc closed.
### 2026-09-04 (cookbook bug fixes): t01 metallic wire, l02/l05 blend port order (`5cd9e0b`).
### 2026-09-04 (subgraph retrofit): all 46 materials grouped, 524 -> 179 top-level nodes (`034aeaf`).
