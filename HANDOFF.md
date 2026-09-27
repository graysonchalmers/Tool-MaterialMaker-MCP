# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-27 17:10 CDT. `main` @ `6505f17` + wrap-up, pushed. **v0.9.0** released; release PR #16 (0.9.1) open, not merged. Nothing in flight._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05, teardown #3):**
- "Current state" describes the latest session only.
- Anything older is one line in the session log.
- "Heads-up" is a bounded list of live gotchas.
- Git history is the archive.

## 🎯 Current state

Evening session, 2026-09-27. Four jobs, all merged and pushed:
- **f07 herringbone tweed host** (round 3): Pattern selector (weave / twill / crosshatch), Plaid Overlay, Fleck Layer. Default and the f01/f05/f08/f09 presets are 0 px different on albedo, normal and ORM at 2048; the lead re-ran the diff. Grayson approved the boards, so **f01, f05, f08, f09 are retired. Cookbook is 62.**
- **s14 gallery tile** re-rendered at Dryness 0.5 (damp) through a `_make_showcase` `_PARAM_OVERRIDES` table. s14's cookbook default is unchanged.
- **param4 source fix** (Grayson approved the boards): 11 `normal_map` nodes (man02, m06, o01, s07, s09, s11, t01, t05, t06, w03, w05) switched to the direct path, param4=0, **with param1 unchanged**. Measured: the normal matches within 0.37/255, sweep minima fall exactly at the old param1, man02 went 3/3 flat → 0/3 and m06 2/3 → 0/3. AUTHORING now says to prefer param4=0 always. Only o03, s05, w04 and w06 still use param4=1; all four are due to retire into hosts.
- **render() retry race fixed** (`3db6167`): each attempt re-snapshotted mtimes and required `mtime > prev`, so a retry that rewrote the map inside one filesystem tick looked like a missing export. That was the Windows CI flake at 589ec5f and 75d4fbe. A failed attempt's maps are now removed before the retry, with a pinned-mtime regression test.
- **Gates:** fast suite 1209 passing, CI green on `3db6167`.

## 📌 Where we stopped

Clean. Every branch is merged, and every worktree from this session is retired.

## ▶️ Next concrete step

**Next host round from the teardown appendix** (`docs/teardowns/TEARDOWN-2026-09-27.md:289-317`). Pick **w05 wood** (absorbs w04 and w06): it also retires two of the four remaining param4=1 graphs. Same recipe as before: defaults pixel-identical by Pillow diff at 2048, boards for Grayson, retire only after his approval.

Alternatives:
- **man02 tiles** (absorbs s05, man03): retires another param4=1 graph.
- **Merge release PR #16 (0.9.1)**: carries the param4 fix. Wait until CI on main is green.

## ❓ Open questions

- **m02 id:** keep `m02_brushed_aluminum` or rename it (e.g. `m02_brushed_metal`)?
- **Slider ranges:** some host presets need typed values above the catalog slider max (s14 Top flatness 1.5/4, Grain scale 128; s07 Grain scale 48; f07 Fleck density 36 > 32), which mm-play can't reach.
- **f07 Plaid Overlay** at strength 1 reads flat, because its Normal blend replaces the ribbon shading. Is a multiply or shaded variant wanted?
- **North Star amendment** (library shape, measurable step 3): the draft is in the teardown report.

## 🗂️ Changed this session

- **Merges to `main`:**
  - `53a4832` f07 host
  - `7f5f15a` f01/f05/f08/f09 retirement
  - `75d4fbe` s14 damp tile
  - `3db6167` render retry fix
  - `6b12f8d` release 0.9.0
  - `6505f17` param4 fix
- **Decisions and why:**
  - **param4 source fix without a param1 retune.** Cloned buffered chains are not directly-fed generators, so the old "lower param1" advice doesn't apply to them. It was measured on 11 graphs.
  - **The param4 fix skipped graphs about to retire** (o03, s05, w04, w06), because fixing a graph that is about to be deleted is wasted work.
  - **Retired files copied first** to `_to_delete\MaterialMaker-retired-f01-f05-f08-f09-2026-09-27`, before `git rm`.

## ⚠️ Heads-up for the next agent

- **Direction (Grayson, 2026-09-27): no new cookbook materials.** Add features to existing materials. Node-coverage counts are a diagnostic, not a goal.
- **"invalid shader" in the MM log is not a flat-normal signal on its own.** It showed up on many correct param4=0 renders. `_flat_normal` checks both the log line and the pixels; keep it that way.
- **Stale builder docstrings:** t01 ("wood's own normal chain already works unmodified"), s09 ("stone_wall's, unchanged") and w05 ("Pure recolor") predate the param4=0 switch.
- **Outside contributor `waskosky`:** review any NEW PR as untrusted before running it, and watch the queue (they once went 19 days unanswered).
- **The user-wide MCP server is an EDITABLE install of the MAIN checkout's `src`.** It picks up merged code (the retry fix, for one) only after a session restart. Never `pip install -e .` into `.venv` while any `mm-mcp.exe` is running: the locked exe leaves the venv without `mm_mcp`. Recovery: a `--prefix` install, then copy the `.pth` and `dist-info`.
- **A worktree has no `.env`.** Copy it from the main checkout without printing it, or the catalog silently fails.
- **Material Maker ignores `--size`.** `render()` downsamples. Anything that calibrates on pixels must render at the size it measures.
- **Godot 4.7 cannot combine heightmap/parallax with `uv1_triplanar = true`.**
- **The contact sheet `docs/images/cookbook-contact-sheet.png` is stale** (built at 71). No script writes its tracked path.
- **`promote_cookbook --check` compares against the gitignored `quality/authored/`.** After retiring a material, re-run its builder and move stale `authored/` dirs aside.
- **Standing render gotchas:**
  - One Godot at a time.
  - Never render from `python -c`.
  - Recover a hang with `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe`.
  - Use `MM_PLAY_PORT` if 8788 is taken.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

- **2026-09-27 evening** (f07 host + f01/f05/f08/f09 retired, cookbook 62; s14 damp tile; param4=0 on 11 normals; render retry mtime race; v0.9.0): see git log `53a4832..6505f17`.
- **2026-09-27** (teardown #6, truth pass, PRs #13/#7, hosts m02/s14/s07; cookbook 74→66): see git log `bfeaac1..a132a9f`.
- **2026-09-15/16** (iteration-and-parallax, merged): s14/m06 retunes; the Deep Parallax prototype on `s09_ashlar_wall`; the BlockAO/BlockHeight swap fixed.
- **2026-09-15** (reflections cycle, merged `007d493`): sun-disc, SSR and opt-in clearcoat rig; the global normal green-flip was reverted (`4e239da`).
- **2026-09-14 night** (rig overhaul, `24ff854`): rounded-box cube, unified triplanar, lathed rook; front page recurated.
- **2026-09-14 late** (`4b0948f`): coin profile and two-scale gravel for s06/t03.
- **2026-09-14 evening** (merged): `normal_albedo_audit.py` and `_make_showcase.py`; 5 normal-registration fixes.
- **2026-09-14** (PR #11 `948a8e7`): the compound-node param default is now sourced from the remote node.
