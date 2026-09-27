# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-27 15:05 CDT. `main` @ merged host rounds, pushed. **v0.8.1** released; release PR #15 (0.9.0) open, not merged. One round in flight: f07 (WIP branch `f07-host`)._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05, teardown #3):**
- "Current state" describes the latest session only.
- Anything older is one line in the session log.
- "Heads-up" is a bounded list of live gotchas.
- Git history is the archive.

## 🎯 Current state

Long session, 2026-09-27. Teardown #6 → truth pass → outside PRs → cookbook consolidation into host materials (Grayson-approved keep/merge/cut list, 74 → ~29):
- **Cookbook is 66 materials.** Hosts merged, each with sliders whose defaults are pixel-identical to the pre-host material (Pillow diff at 2048, 0 px on every map, hand-verified by the lead):
  - **m02 brushed metal**: Hairline / Scratch Wear / Polish; m03, m04, m05 retired.
  - **s14 river pebbles**: Dryness / Grain / Contact Gaps / Sediment Bed / Packing; s04, s06, t08 retired (s06 preset is bit-identical). README gallery t08 tile → s14.
  - **s07 paved stone**: Joint width / Tones follow joints / Top flatness / Mortar; s08, s10 retired (both were s07's graph with other params; presets pixel-identical).
- **Fixes merged:** `size` honoured (MM always bakes 2048, render() downsamples); render ok only on exit 0 + decodable maps; flat-normal race and missing-export retried (3 attempts total); mm-play Download bound to its render snapshot (PR #7) and drives every multi-linked widget; atomic sweep publication (PR #13). #8 closed.
- **Gates:** fast suite 1238 passing on `main`.

## 📌 Where we stopped

Round 3, **f07 herringbone tweed** absorbing f01, f05, f08, f09, was mid-flight when the session restarted. Partial builder work is a WIP commit `43a7c09` on branch **`f07-host`** (worktree `pickup-teardown-commands-dfb4c2`): untested, not promoted, no boards.

Also pending (Grayson approved 2026-09-27): re-render the s14 README gallery tile at the **damp** preset (today's default reads as black bubbles).

## ▶️ Next concrete step

**Finish round 3 (f07).** Review `git show 43a7c09`, then either continue it or restart the round from `main` with the same brief (defaults pixel-identical to today's f07, which is in the gallery and `preview_regress` MATTE_SET; carry f08 flecks / f09 plaid in as layers; boards for Grayson; retire f01/f05/f08/f09 only after approval).

Alternatives:
- **(a) Damp s14 gallery tile** (small, Godot): set s14 Dryness≈0.5 on a copy, `_make_showcase still`, commit.
- **(b) Next hosts from the appendix:** l07 leather (l01/l02/l03), combo01 wear stack (pm03/pm05/pm06), pm01 finishes (p01/pm04), gl04 crystal (gl02/gl03), w05 wood (w04/w06), man02 tiles (s05/man03).
- **(c) Merge release PR #15 (0.9.0).**

## ❓ Open questions

- **m02 id:** keep `m02_brushed_aluminum` or rename (e.g. `m02_brushed_metal`)?
- **19 buffered-normal graphs (param4=1):** fix at source (param4=0, AUTHORING's documented fix) instead of retrying? Changes relief, needs Grayson's eye.
- **Slider ranges:** some host presets need typed values above the catalog slider max (s14 Top flatness 1.5/4, Grain scale 128; s07 Grain scale 48), which mm-play can't reach.
- **North Star amendment** (library shape, measurable step 3): draft in the teardown report.

## 🗂️ Changed this session

- **Merges to `main`:** `bfeaac1` truth pass · `37f6de8` m02 host · `7c64a8d` PRs #13/#7 · `6de8672` s14 host · `9c03c12` mm-play multi-link · `22469d6` missing-export retry · `c8f9635`/`9206b1c` s07 host + s04/s06/t08 retirement · `cf3a03b` s14 gallery tile · `589ec5f` s08/s10 retirement.
- **Decisions and why:**
  - **Host rounds merge sliders immediately** (defaults render-identical = no visual change); **retirement waits for Grayson's board approval**.
  - **Pixel-identity proof by Pillow full-image diff**, not `render_tracked` (its 16x16 grid missed a flat normal).
  - **Height ops as math nodes, not blends** (blends caused 1-LSB normal drift).
  - **Retired files copied to `_to_delete\MaterialMaker-retired-*-2026-09-27`** before `git rm`.

## ⚠️ Heads-up for the next agent

- **Direction (Grayson, 2026-09-27): no new cookbook materials.** Add features to existing materials. Node-coverage counts are a diagnostic, not a goal.
- **Outside contributor `waskosky`:** #7, #8 and #13 are all resolved. Their fork ("Material Workshop" on mm-play) is ahead of us. Review any NEW PR as untrusted before running it, and do watch the queue: they went 19 days unanswered last time.
- **The user-wide MCP server is an EDITABLE install of the MAIN checkout's `src`** (`.venv\Scripts\mm-mcp.exe`; metadata fixed to 0.8.1 on 2026-09-27). It picks up merged code only after a restart.
- **Never `pip install -e .` into `.venv` while any session's `mm-mcp.exe` is running.** The exe is locked (WinError 32): pip uninstalls first and then fails, which leaves the venv with NO `mm_mcp`. Recovery: `pip install --no-deps -e . --prefix <scratch>`, then copy the `.pth` and `dist-info` into `.venv\Lib\site-packages`, leaving the locked exe in place (it is a generic launcher).
- **A worktree has no `.env`.** Copy it from the main checkout without printing it. Without it, the examples gate silently collapses to 1 skipped test.
- **Material Maker ignores `--size`.** `render()` downsamples. Anything that calibrates on pixels must render at the size it measures (see the swatch test).
- **Godot 4.7 cannot combine heightmap/parallax with `uv1_triplanar = true`.** Any future Deep Parallax object needs the sphere's non-triplanar material swap.
- **Three tile constants live in `preview.gd`, each in different units:** CLI `tile`, `SPHERE_HEIGHTMAP_UV_SCALE`, and `SPHERE_MATCHED_TRIPLANAR_TILE`. Heightmap mode silently overrides the caller's tile.
- **The contact sheet `docs/images/cookbook-contact-sheet.png` is stale** (built at 71; several tiles are now retired materials), and no script writes its tracked path.
- **`promote_cookbook --check` compares against the gitignored `quality/authored/`.** After retiring or changing a material, re-run its category builder (`python -m quality.cookbook_<cat>`) and move stale `authored/` dirs aside, or `--check` reports false drift.
- **Standing render gotchas:**
  - One Godot at a time.
  - Never render from `python -c`.
  - Recover a hang with `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe`.
  - Port 8788 (mm-play) is sometimes held by another project's node server; use `MM_PLAY_PORT`.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

- **2026-09-27** (teardown #6, truth pass, PRs #13/#7, hosts m02/s14/s07; cookbook 74→66): see git log `bfeaac1..589ec5f`; f07 round WIP on `f07-host`.
- **2026-09-15/16** (iteration-and-parallax, merged): s14/m06 retunes; the Deep Parallax prototype on `s09_ashlar_wall` (`depth_tex`, sphere swap, `parallax_spin`); the BlockAO/BlockHeight swap fixed.
- **2026-09-15** (reflections cycle, merged `007d493`): sun-disc, SSR and opt-in clearcoat rig; m05, s14 and m06 added; the global normal green-flip was reverted (`4e239da`).
- **2026-09-14 night** (rig overhaul, `24ff854`): rounded-box cube, unified triplanar, lathed rook; front page recurated to 8 materials plus GIFs.
- **2026-09-14 late** (`4b0948f`): coin profile and two-scale gravel for s06/t03.
- **2026-09-14 evening** (merged): `normal_albedo_audit.py` and `_make_showcase.py`; 5 normal-registration fixes.
- **2026-09-14** (PR #11 `948a8e7`): the compound-node param default is now sourced from the remote node.
- **2026-09-14** (noise-vocabulary round 3, merged): 6 proof materials (65→71); the catalog_builder fixpoint fix.
