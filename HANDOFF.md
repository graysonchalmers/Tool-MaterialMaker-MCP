# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-27 06:20 CDT. Teardown #6 plus the truth pass are on `main` and released as **v0.8.1**. Two workstreams are IN FLIGHT and unmerged: branch `pr-merge` (outside PRs #13 and #7) and branch `m02-host-pilot` (cookbook host pilot)._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05, teardown #3):**
- "Current state" describes the latest session only.
- Anything older is one line in the session log.
- "Heads-up" is a bounded list of live gotchas.
- Git history is the archive.

## 🎯 Current state

This session had four parts:
- **Housekeeping.** Merged release PR #6, so v0.8.0 is out. Pruned branches: local from 10 to 3, remote from 8 to 2. Re-sent the s14/m06 renders, and Grayson **approved** them.
- **Teardown #6** ran as 5 parallel lens agents, and every red finding was hand-verified. The report is `docs/teardowns/TEARDOWN-2026-09-27.md`. Verdict: **not a rebuild.** The core is small and sound, but two weeks of breadth work (proof materials, preview polish) went through `quality/`, not the MCP, and moved neither use nor reach.
- **Grayson set the direction:** no new materials. Features go onto existing ones, for a smaller, feature-rich library. He **approved** the report's keep/merge/cut list (74 → about 29 host materials) on 2026-09-27.
- **The truth pass shipped:**
  - `size` works now. Material Maker always bakes at 2048, so smaller sizes are downsampled. The range is 16-2048 and the default is 2048.
  - A render now reports ok only on exit 0 with maps that decode.
  - The flat-normal race gets one retry. It was reproduced on s07 and on Unity/URP, and the retry fixed it both times.
  - The outdir is forced absolute.
  - The 4 core tools are now described, and a test enforces that every tool has a description.
  - The MCP preview tile default is 0.45.
  - mm-play renders at 2048.

Gates: the fast suite has 1233 passing. The integration suite has 26 of 26 passing (the live-GUI tests were not run).
- **Afterwards:**
  - Release PR #14 was merged, so **v0.8.1** is out.
  - The `.venv` editable install metadata was fixed to 0.8.1. It hit the locked-exe trap in the heads-up and was recovered.
- **Outside PRs:**
  - #8: reply posted and the PR closed as superseded.
  - #13 and #7: squash-merged onto branch **`pr-merge`** (worktree `.claude/worktrees/pr-merge`) as `waskosky`'s own commits. Our follow-ups restore #13's dropped Deep Parallax heightmap forwarding and add #7's snapshot pruning (keep the newest 20), each with a test. The fast suite there has 1297 passing. **Not pushed.**
- **The m02 host pilot** was dispatched to a subagent on branch **`m02-host-pilot`** (worktree `pickup-teardown-commands-dfb4c2`): m02 absorbs m03 hairline, m04 scratches and m05 polish as exposed layers, default OFF, so m02 stays render-identical. It had no commits yet at wrap time.

## 📌 Where we stopped

**`pr-merge` is waiting on two Godot checks before it goes to `main`.** Godot was busy with the m02 pilot. **The m02 pilot subagent was still running** when this was written. Its preset boards (default / titanium / scratched steel / chrome, plus an m03-m05 original-vs-host board) go to Grayson for visual approval. m03, m04 and m05 are retired ONLY after he approves.

## ▶️ Next concrete step

**Verify and land `pr-merge`**, once no other Godot is running:
1. From `.claude/worktrees/pr-merge`, run `pytest -q -m integration -p no:cacheprovider tests/test_preview.py tests/test_preview_sweep.py tests/test_render.py`.
2. Hands-on mm-play from that worktree with `MM_PLAY_PORT=8799`:
   - Pick w03 and move its slider to 24.
   - Click Download.
   - Assert the zip's `.ptex` carries 24 and its maps are 2048².
   - Take a screenshot for Grayson.
3. `git merge --no-ff pr-merge` into `main`, then push.
4. Post the #13 and #7 replies. Grayson already approved posting them. Reword the drafts in `docs/teardowns/2026-09-27-pr-triage-draft.md` to say "we did the rebase and follow-up on our side (commits …), merged in …". Then close both PRs with a link, since a squash keeps GitHub from auto-marking them merged.

Alternatives:
- **(a) Collect the m02 pilot result.**
  - Check `git log main..m02-host-pilot`, the render-identical proof, and the boards in its report.
  - Send the boards to Grayson.
  - After he approves, retire m03, m04 and m05. That means their builders, `.ptex`/`.md` files, thumbnails and AUTHORING mentions, the README count, and the `test_cookbook_gate` floor. Node coverage stays the same because the nodes were carried into m02.
- **(b) Grayson's hands-on step-3 session.** First lay out the 32 subgraphs whose nodes are all at (0,0).
- **Also pending:**
  - Release PR #15 (0.8.2, from a docs commit; it can wait and ride with the next fix).
  - Restarting the MCP servers so they run v0.8.1.

## ❓ Open questions

- **m02 id:** the host covers aluminium, titanium, steel and chrome. Keep the id `m02_brushed_aluminum`, or rename it to something like `m02_brushed_metal`? Renaming touches play tests and cards.
- **The North Star amendment** (library shape, a measurable step 3): the draft is in the report, and every inference is marked ⚠️ CONFIRM.
- **Emission (parked since the reflections cycle):** does "Godot 4 Standard" write `_emission.png` unconditionally? t06 is the only material that uses emission.
- **Only 1 of 74 materials drives AO (s09).** The rest export flat AO. This is the first "feature depth" candidate.

## 🗂️ Changed this session

- **Branch:** `claude/pickup-teardown-commands-dfb4c2`, merged `--no-ff` as `bfeaac1`.
- **Key files:**
  - `src/mm_mcp/render.py`, `server.py`, `preview.py`, `play/api.py`, `play/static/app.js`
  - `quality/render_{one,tracked,cookbook}.py`
  - `tests/test_render.py`, `tests/test_server_tools.py`, `tests/test_debug_swatches.py`
  - `README.md`, `docs/AUTHORING.md`, `docs/teardowns/TEARDOWN-2026-09-27.md`, `STATUS.md`
- **Decisions and why:**
  - **The default `size` is 2048, not 512.** Every caller had always received 2048, and the quality pipeline and previews depend on that. The `quality/` callers pin 2048, so their outputs stay byte-identical.
  - **Nonzero exit now means failure.** 12 of 12 successful Godot probes and 5 of 5 Unity probes exited 0, so the old tolerance for nonzero exits bought nothing.
  - **The flat check needs both signals:** a std≈0 normal *and* "invalid shader" in the log. A graph with no normal input legitimately bakes flat.
  - **The swatch test renders at 2048,** because its thresholds were calibrated against 2048 maps. It had asked for 128, but it never got 128.
  - **mm-play is back at 2048,** because a smaller request only meant a blurrier sphere with no speed gain.
  - **Sweep/preview publication and the play Download bug were left to PRs #13 and #7,** out of respect for the outside contributor. #8's intent was landed narrowly by hand, because as written it would break every real render.

## ⚠️ Heads-up for the next agent

- **Direction (Grayson, 2026-09-27): no new cookbook materials.** Add features to existing materials. Node-coverage counts are a diagnostic, not a goal.
- **Outside PRs (`waskosky`):** Grayson said go on 2026-09-27. #8 is closed. #13 and #7 are squashed onto `pr-merge` and unverified with Godot; their replies are not yet posted. Their fork is 46 commits ahead, so treat any NEW PR from it as untrusted until reviewed.
- **The user-wide MCP server is an EDITABLE install of the MAIN checkout's `src`** (`.venv\Scripts\mm-mcp.exe`; metadata fixed to 0.8.1 on 2026-09-27). It picks up merged code only after a restart.
- **Never `pip install -e .` into `.venv` while any session's `mm-mcp.exe` is running.** The exe is locked (WinError 32): pip uninstalls first and then fails, which leaves the venv with NO `mm_mcp`. Recovery: `pip install --no-deps -e . --prefix <scratch>`, then copy the `.pth` and `dist-info` into `.venv\Lib\site-packages`, leaving the locked exe in place (it is a generic launcher).
- **A worktree has no `.env`.** Copy it from the main checkout without printing it. Without it, the examples gate silently collapses to 1 skipped test.
- **Material Maker ignores `--size`.** `render()` downsamples. Anything that calibrates on pixels must render at the size it measures (see the swatch test).
- **Godot 4.7 cannot combine heightmap/parallax with `uv1_triplanar = true`.** Any future Deep Parallax object needs the sphere's non-triplanar material swap.
- **Three tile constants live in `preview.gd`, each in different units:** CLI `tile`, `SPHERE_HEIGHTMAP_UV_SCALE`, and `SPHERE_MATCHED_TRIPLANAR_TILE`. Heightmap mode silently overrides the caller's tile.
- **The contact sheet `docs/images/cookbook-contact-sheet.png` is stale** (71 of 74), and no script writes its tracked path.
- **Standing render gotchas:**
  - One Godot at a time.
  - Never render from `python -c`.
  - Recover a hang with `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe`.
  - Port 8788 (mm-play) is sometimes held by another project's node server; use `MM_PLAY_PORT`.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

- **2026-09-27** (teardown #6 + truth pass, merged `bfeaac1`): v0.8.0 released; branches pruned; s14/m06 approved; report in `docs/teardowns/`; `size`, render-success, flat-normal retry and tool descriptions fixed; play at 2048. Later: v0.8.1 released; venv metadata fixed; keep/merge/cut list approved; #8 closed, #13/#7 on `pr-merge`; m02 pilot started on `m02-host-pilot`.
- **2026-09-15/16** (iteration-and-parallax, merged): s14/m06 retunes; the Deep Parallax prototype on `s09_ashlar_wall` (`depth_tex`, sphere swap, `parallax_spin`); the BlockAO/BlockHeight swap fixed.
- **2026-09-15** (reflections cycle, merged `007d493`): sun-disc, SSR and opt-in clearcoat rig; m05, s14 and m06 added; the global normal green-flip was reverted (`4e239da`).
- **2026-09-14 night** (rig overhaul, `24ff854`): rounded-box cube, unified triplanar, lathed rook; front page recurated to 8 materials plus GIFs.
- **2026-09-14 late** (`4b0948f`): coin profile and two-scale gravel for s06/t03.
- **2026-09-14 evening** (merged): `normal_albedo_audit.py` and `_make_showcase.py`; 5 normal-registration fixes.
- **2026-09-14** (PR #11 `948a8e7`): the compound-node param default is now sourced from the remote node.
- **2026-09-14** (noise-vocabulary round 3, merged): 6 proof materials (65→71); the catalog_builder fixpoint fix.
