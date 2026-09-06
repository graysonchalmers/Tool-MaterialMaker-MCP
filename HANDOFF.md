# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-05 (teardown #4: hygiene sweep + quality/ packaged + Phase-3 harness archived) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

`main` at the merge `6e4568f` (+ the docs commit that lands this file), pushed.
Fast suite **809 passed**, 25 integration deselected. `python -m
quality.promote_cookbook --check` in sync. `mm-mcp --check` reports 53
cookbook materials and now prints the Material Maker checkout revision
(`ad19fcf`, the same sha CI pins).

This session ran `pickup` + a fourth adversarial `teardown`, then executed
Grayson's picks 2 and 3 (pick 1, the hands-on loop session, is his):

- **Teardown #4 (read-only, report delivered as a file).** No Rebuild
  verdicts; `src/` is already the v2 core. The headline finding was the
  premise, not the structure: the North Star's step 3 (Grayson opens and
  edits the authored graph) has two `saved_graphs/` entries, both from
  2026-08-28, and about 24 MCP-path renders in 12 days, against 53
  Claude-authored materials and 677 MB of harness renders. Second finding,
  cross-project: the 2026-09-05 21:00 nightly backup aborted after five
  projects with no summary line (see Heads-up).
- **Pick 2, hygiene sweep (direct commits `c836d38`, `d420ed8`).** CI clones
  Material Maker at a pinned sha (`MM_UPSTREAM_PIN` in `mm_mcp/__init__.py`,
  mirrored as `MM_PIN` in `test.yml`, a test keeps them equal) and the doctor
  prints the local checkout's sha beside it. README no longer claims "no test
  coverage beyond a small smoke and unit set". PLAN.md's `--export` and
  7-tool list fixed. Baton dates corrected (the previous wrap-up wrote
  09-06 for a 21:03 CT commit). Stale merged worktree
  `.claude/worktrees/confident-tesla-ee9400` removed. Commons state file
  written (it had never existed) and resolution lines appended to the three
  shipped ideas in `_agent-commons/ideas/`.
- **Pick 3, `quality/` as a package + Phase-3 archive (branch merged
  `--no-ff` as `6e4568f`).** `quality/` is an importable package in place
  (no rename): `from quality.<module> import ...`, scripts run as `python -m
  quality.<module>` from the repo root, pytest `pythonpath = ["src", "."]`,
  39 `sys.path` hacks gone, a gate test forbids their return. Every cookbook
  builder is `build_<id>(catalog)` (wood/glass/plastics threaded, gate test
  over all 53). The Phase-3 gate apparatus (frozen `test_set.json`,
  freeze rule, both scorecards) lives under `docs/evidence/phase3/` with a
  README and a sha256 pin; `run_case.py`, `score_baseline.py`,
  `verify_hero_fold.py` are removed (last carried at `59d788f`);
  `quality/runs/` (290 MB) moved to `_to_delete`; its `.gitignore` line and
  the backup-ops exclusion are gone (`backup-ops` `3c3aca8`). `author.py`
  lost the "frozen, do not edit" label: six builders import it and `--check`
  is the real freeze. `tests/test_donors.py` builds the catalog in a
  module fixture. Spec + plan under `docs/superpowers/` dated 2026-09-05.

Built with `writing-plans` -> `subagent-driven-development` (4 tasks, each
reviewed, one fix round on Task 3, opus whole-branch review "with fixes",
one fix wave, scoped re-review clean). Plan defect worth remembering: the
plan's verification greps were keyed to file paths, not to the claims the
change invalidated, which is how "frozen" survived in six comments until the
final review.

## 📌 Where we stopped

Picks 2 and 3 are merged and pushed. Pick 1 (the hands-on loop session) is
Grayson's and has not happened. Nothing is in flight.

## ▶️ Next concrete step

1. **Grayson: run the loop by hand.** Open three cookbook graphs in Material
   Maker, edit each, save to `saved_graphs/`, note what was hard to read.
   Doubles as the `live_load` / `mm-play` live-session verification. This is
   the only item four teardowns never tested; do it before adding materials.
2. **`backup-ops`: find out why the 2026-09-05 nightly run died** after
   `Skills` at 21:05 with no summary line. Until a run completes, the
   MaterialMaker exclusion override (2026-09-05) is unproven.
3. **Unreal UE5 export** (backlogged: memory pressure with a live Unreal
   Editor + bridge; run a `stop-node-hogs` sweep first).
4. **More cookbook materials** only after item 1 has produced a signal.

## ❓ Open questions

- PyPI vs GitHub-clone-only (leaning GitHub-only); macOS/Linux never run, no
  machine. **v0.7.0 released 2026-09-05 CT** (CHANGELOG dates it 09-06 in
  UTC). release-please will open the next PR on the pushed commits; cadence
  still undecided.
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

- **The 2026-09-05 nightly backup aborted** (`backup-ops\logs\Backup-All_2026-09-05_210003.log`,
  89 lines, ends at `OK: Skills`, no summary). Plausible cause: a
  `NativeCommandError` from `git diff HEAD --binary` printing an LF/CRLF
  warning on stderr at `Backup.Common.ps1:229`. Not this repo's bug; needs a
  `backup-ops` session.
- **Run quality scripts as `python -m quality.<module>` from the repo root**
  (the scripts import `mm_mcp`, so `pip install -e .` is a prerequisite; a
  file-path launch no longer resolves the package imports; running from
  inside `quality/` breaks `.env` lookup). Never launch a Godot render from
  `python -c` (the launcher does not exit; use `python -m quality.render_one`
  or a script file). Renders are one Godot at a time.
- **Edit cookbook materials by changing the builder and re-promoting**, never
  the tracked `.ptex` by hand; `python -m quality.promote_cookbook --check`
  flags drift. `--check` compares against the existing gitignored
  `quality/authored/` tree, so regenerate the category first when you want
  proof a code change did not move outputs. `render_cookbook` /
  `_make_previews` regenerate the WHOLE label and Godot is not
  byte-deterministic, so unrelated thumbnails can churn: `git status` and
  revert anything swept up.
- **`quality/render_compare.renders_match` proves builder-before == builder-after**,
  not that the tracked artifact was already right.
- **`group_into_subgraph` fails silently on a mistyped member name** (the node
  just stays top-level). Check names against the graph first.
- **A `blend` shows port-1 where its port-2 mask is 0 and port-0 where it is 1**;
  put the majority layer on port-1. Opacity = amount x mask, so never feed a
  mid-value colorize as the mask. `normal_map` `param4=0` is the flat-normal
  fix for directly-fed analytic generators. Voronoi output port 2 is the
  per-cell random (fleck) source.
- **Verify metallic/roughness/AO fixes by reading the exported ORM channel**
  (`quality/pngread.py`), not by eye.
- **`take_variant(builder, label, keep_n)`** (author_helpers) runs an
  `author.py` builder under a cookbook label, returns the requested variant,
  and deletes every variant file it wrote; the caller must re-save as v1.
- **Bumping the Material Maker pin** means changing `MM_UPSTREAM_PIN` in
  `src/mm_mcp/__init__.py` AND `MM_PIN` in `.github/workflows/test.yml`
  (a test fails if they differ), pulling the local `z-Git\material-maker`
  checkout to the same sha, then regenerating every category and running
  `--check`.
- **Stale mm-play on 8788 is now a startup error with the PID**, not a mystery.
  If you ever see the old symptom anyway (renders "fail" while the code is
  fine), `Get-NetTCPConnection -LocalPort 8788 -State Listen`.
- **The SPIRV `SCRIPT ERROR` at `parse_args.gd:59` prints on every successful
  export.** Red herring; never treat it as evidence of a broken render.
- **`ambientcg.com` redirected to a scareware page (2026-09-03).** Use Wikimedia
  Commons for reference photos until re-verified.
- **Donors load from `quality/donors/`** (tracked), not the external MM
  checkout; vendor any new donor `.ptex` there.
- **release-please has `bump-minor-pre-major: true`**; a `feat!` cuts 0.x, not
  1.0.0. Do not remove it.
- **`.mcp.json` and `.env` are gitignored; never echo `.env`.**

## 🕓 Session log

Newest first. Keep at most 8 entries; older ones are in `git log` (search the
commit subjects, every session ends with a `docs:` wrap-up commit).

### 2026-09-05 (teardown #4 executed): hygiene sweep, quality/ packaged, Phase-3 archived
- `pickup` clean, then `teardown` #4: no Rebuild verdicts; headline finding
  is the untested premise (two hand-edits in 12 days) plus the aborted
  nightly backup. Grayson: "I'll do 1 later, can you do 2 for me + 3".
- Pick 2 as direct commits: CI pin (`c836d38`), honesty sweep (`d420ed8`),
  worktree prune, commons state + ideas resolutions.
- Pick 3 via `writing-plans` -> `subagent-driven-development`: 4 tasks,
  Task 3 one fix round (seven cookbook cards still cited the moved
  scorecard), final opus review 3 Important (all docs the branch made
  stale: "frozen" comments, a false HANDOFF bullet, README/NORTH_STAR
  scorecard pointers) fixed in one wave, re-review clean. Merged `--no-ff`
  as `6e4568f`, pushed. Suite 638 -> 809.
### 2026-09-05 (teardown #3 executed): examples/ folded into the cookbook (46 -> 53), mm-play port diagnostic, backup exclusions, baton diet (`87be578`, `5b93785`); v0.7.0 released.
### 2026-09-05 (mm-play verified): Grayson ran `play.bat` hands-on; row promoted 🔌 -> ✅ (`056dcd4`).
### 2026-09-04 (blocker correction): the "host can't render" blocker was a stale server squatting 8788, not GPU (`b016f1b`).
### 2026-09-04 (live_load): seventh live tool, in-place graph replace; play surface pushes the picked material live (`d523ad6`).
### 2026-09-04 (play-surface UI nits): slider panel docks; canvas re-fills on resize (`c7e85ee`).
### 2026-09-04 (play.bat + play-surface verified): one-click launcher; "MM for dummies" arc closed.
### 2026-09-04 (cookbook bug fixes): t01 metallic wire, l02/l05 blend port order (`5cd9e0b`).
