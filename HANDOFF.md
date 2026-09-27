# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-27 04:35 CDT. Teardown #6 plus the truth pass are MERGED to `main` (`bfeaac1`) and pushed, CI green. v0.8.0 is released; release PR #14 (0.8.1) is open._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05, teardown #3):**
- "Current state" describes the latest session only.
- Anything older is one line in the session log.
- "Heads-up" is a bounded list of live gotchas.
- Git history is the archive.

## 🎯 Current state

This session had four parts:
- **Housekeeping.** Merged release PR #6, so v0.8.0 is out. Pruned branches: local from 10 to 3, remote from 8 to 2. Re-sent the s14/m06 renders, and Grayson **approved** them.
- **Teardown #6** ran as 5 parallel lens agents, and every red finding was hand-verified. The report is `docs/teardowns/TEARDOWN-2026-09-27.md`. Verdict: **not a rebuild.** The core is small and sound, but two weeks of breadth work (proof materials, preview polish) went through `quality/`, not the MCP, and moved neither use nor reach.
- **Grayson set the direction:** no new materials. Features go onto existing ones, for a smaller, feature-rich library. The report's appendix proposes 74 → about 29 host materials, pending his approval.
- **The truth pass shipped:**
  - `size` works now. Material Maker always bakes at 2048, so smaller sizes are downsampled. The range is 16-2048 and the default is 2048.
  - A render now reports ok only on exit 0 with maps that decode.
  - The flat-normal race gets one retry. It was reproduced on s07 and on Unity/URP, and the retry fixed it both times.
  - The outdir is forced absolute.
  - The 4 core tools are now described, and a test enforces that every tool has a description.
  - The MCP preview tile default is 0.45.
  - mm-play renders at 2048.

Gates: the fast suite has 1233 passing. The integration suite has 26 of 26 passing (the live-GUI tests were not run).

## 📌 Where we stopped

Everything is merged and pushed. Two decisions are with Grayson: the outside PRs, and the cookbook keep/merge/cut list.

## ▶️ Next concrete step

**Grayson's call on waskosky's PRs.** The draft replies and triage are in `docs/teardowns/2026-09-27-pr-triage-draft.md`.
- #13 (sweep publication) and #7 (play Download): merge after changes.
- #8: close as superseded by `fdd2ac7`.
- Nothing gets posted, and none of their code is run, without his go.

Alternatives:
- **(a) The m02 host pilot.** m02 absorbs m03, m04 and m05 as exposed layers. It needs Grayson to approve the keep/merge/cut list first.
- **(b) Grayson's hands-on step-3 session.** It is the North Star's own test and costs no agent time. First lay out the 32 subgraphs whose nodes are all at (0,0), so they don't open as a pile in Material Maker; that layout is render-identical.
- **Also pending:** merging release PR #14 (0.8.1), and restarting the MCP server so it runs the new code.

## ❓ Open questions

- **The cookbook keep/merge/cut list:** does Grayson approve, and are 29 hosts the right number?
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
- **Open outside PRs #7, #8 and #13 (`waskosky`) are untrusted code.** Read them with `gh pr view/diff` only, until Grayson says go. Their fork is 46 commits ahead.
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

- **2026-09-27** (teardown #6 + truth pass, merged `bfeaac1`): v0.8.0 released; branches pruned; s14/m06 approved; report in `docs/teardowns/`; `size`, render-success, flat-normal retry and tool descriptions fixed; play at 2048.
- **2026-09-15/16** (iteration-and-parallax, merged): s14/m06 retunes; the Deep Parallax prototype on `s09_ashlar_wall` (`depth_tex`, sphere swap, `parallax_spin`); the BlockAO/BlockHeight swap fixed.
- **2026-09-15** (reflections cycle, merged `007d493`): sun-disc, SSR and opt-in clearcoat rig; m05, s14 and m06 added; the global normal green-flip was reverted (`4e239da`).
- **2026-09-14 night** (rig overhaul, `24ff854`): rounded-box cube, unified triplanar, lathed rook; front page recurated to 8 materials plus GIFs.
- **2026-09-14 late** (`4b0948f`): coin profile and two-scale gravel for s06/t03.
- **2026-09-14 evening** (merged): `normal_albedo_audit.py` and `_make_showcase.py`; 5 normal-registration fixes.
- **2026-09-14** (PR #11 `948a8e7`): the compound-node param default is now sourced from the remote node.
- **2026-09-14** (noise-vocabulary round 3, merged): 6 proof materials (65→71); the catalog_builder fixpoint fix.
