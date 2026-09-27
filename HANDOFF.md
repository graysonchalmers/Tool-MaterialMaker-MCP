# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-27 07:40 CDT. Everything from this session is MERGED to `main` (`7c64a8d`) and pushed. **v0.8.1** is released. Release PR #15 (**0.9.0**) is open and not merged._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05, teardown #3):**
- "Current state" describes the latest session only.
- Anything older is one line in the session log.
- "Heads-up" is a bounded list of live gotchas.
- Git history is the archive.

## 🎯 Current state

This was one long session on 2026-09-27, ending with everything merged and pushed:
- **Teardown #6** (`docs/teardowns/TEARDOWN-2026-09-27.md`): **not a rebuild.** Grayson set the direction (no new materials, depth over breadth) and **approved** the keep/merge/cut list (74 → about 29 host materials).
- **Truth pass** (v0.8.1):
  - `size` is honoured by downsampling MM's fixed 2048 bake.
  - A render reports ok only on exit 0 with maps that decode.
  - The 4 core tools are described.
  - The MCP preview tile default is 0.45.
  - mm-play renders at 2048.
- **Flat-normal race.** MM sometimes bakes a flat normal and logs "invalid shader". A survey of the 19 cookbook graphs with a buffered `normal_map` baked flat **14 of 57** raw renders, mostly on a graph's first, cold-cache render. m06 went flat twice in a row. `render()` now allows **two retries** (`a70bc47`) and fails only if all three attempts are flat.
- **The first cookbook host is done: m02.** `m02_brushed_aluminum` gained Hairline, Scratch Wear and Polish layers, default OFF, so it stays render-identical. m03, m04 and m05 were **retired** (74 → **71**), and node coverage is unchanged at 20/53. Grayson approved the look.
- **Outside PRs (`waskosky`), all closed with replies:**
  - #13 (atomic sweep publication) and #7 (play Download bound to its render snapshot) are **merged** as squashes authored by `waskosky`.
  - Our follow-ups: heightmap forwarding restored in sweeps, and snapshot pruning (keep the newest 20).
  - #8 is closed as superseded.
  - Verified on Windows: sweep and render integration tests pass 6/6, and mm-play Download carries the moved slider value with 2048 maps.

Gates: the fast suite has 1274 passing. The integration suite passed 26/26 earlier in the session, with the 7 live-GUI tests not run. Its preview, sweep and render tests were re-run against the PR merges (6/6 passed); the rest were not re-run after that.

## 📌 Where we stopped

Everything is merged and pushed. There is no in-flight work.

## ▶️ Next concrete step

**The next host consolidation, from the approved list.** Suggested next hosts, in order:
- **s14 wet river stone** absorbs s04, s06 and t08 (pebbles, with a wet/dry control).
- **s07 cobblestone** absorbs s08 and s10 (layout modes).

Follow the m02 pattern: layers default OFF with render-identical proof; boards for Grayson; retire only after he approves.

Alternatives:
- **(a) Fix the 19 buffered-normal graphs at the source.** That means `param4=0`, AUTHORING's documented fix, which would remove the flat race instead of retrying around it. It can change each graph's relief, so every one needs Grayson's eye.
- **(b) Grayson's hands-on step-3 session.** First lay out the 32 subgraphs whose nodes are all at (0,0).
- **(c) Merge release PR #15 (0.9.0).**

## ❓ Open questions

- **m02 id:** keep `m02_brushed_aluminum` now that it covers titanium, chrome and scratched steel, or rename it (e.g. `m02_brushed_metal`)?
- **m02's steel preset** sits on a grainy brushed base. m04's smooth matte base isn't reachable, because Polish also forces a mirror finish. Grayson approved it as is; a "Brush relief" slider is the known upgrade.
- **The North Star amendment** (library shape, measurable step 3): the draft is in the teardown report.
- **Emission:** only t06 uses it. Does the Godot 4 export write `_emission.png` unconditionally?
- **Only s09 drives AO.** The rest export flat AO, which makes AO a strong first "feature depth" candidate for the next hosts.

## 🗂️ Changed this session

- **Merges to `main`:**
  - `bfeaac1`: teardown + truth pass.
  - `37f6de8`: m02 host pilot and the m03-m05 retirement.
  - `7c64a8d`: PRs #13 and #7, with the flat-retry raise.
- **Key files:**
  - `src/mm_mcp/{render,server,preview}.py`, `src/mm_mcp/play/{api,server}.py`, `play/static/app.js`
  - `quality/cookbook_metal.py`, `cookbook/metal/*`
  - `tests/test_{render,server_tools,preview_sweep,play_api,play_browser,debug_swatches}.py`
  - `README.md`, `docs/AUTHORING.md`, `docs/teardowns/*`, `STATUS.md`
- **Decisions and why:**
  - **The default `size` is 2048,** because every caller always got 2048.
  - **The flat check needs both signals:** a std≈0 normal *and* "invalid shader". The survey saw the log line on a non-flat render.
  - **Three attempts, not two,** because m06 went flat twice in a row.
  - **The outside PRs were squashed with our own follow-ups** rather than sent back for a rebase, since Grayson said merge. Their authorship is preserved.
  - **m02's hairline runs vertically** so that it runs along m02's streak; unrotated, it crosshatched at mid values.

## ⚠️ Heads-up for the next agent

- **Direction (Grayson, 2026-09-27): no new cookbook materials.** Add features to existing materials. Node-coverage counts are a diagnostic, not a goal.
- **Outside contributor `waskosky`:** #7, #8 and #13 are all resolved. Their fork ("Material Workshop" on mm-play) is ahead of us. Review any NEW PR as untrusted before running it, and do watch the queue: they went 19 days unanswered last time.
- **The user-wide MCP server is an EDITABLE install of the MAIN checkout's `src`** (`.venv\Scripts\mm-mcp.exe`; metadata fixed to 0.8.1 on 2026-09-27). It picks up merged code only after a restart.
- **Never `pip install -e .` into `.venv` while any session's `mm-mcp.exe` is running.** The exe is locked (WinError 32): pip uninstalls first and then fails, which leaves the venv with NO `mm_mcp`. Recovery: `pip install --no-deps -e . --prefix <scratch>`, then copy the `.pth` and `dist-info` into `.venv\Lib\site-packages`, leaving the locked exe in place (it is a generic launcher).
- **A worktree has no `.env`.** Copy it from the main checkout without printing it. Without it, the examples gate silently collapses to 1 skipped test.
- **Material Maker ignores `--size`.** `render()` downsamples. Anything that calibrates on pixels must render at the size it measures (see the swatch test).
- **Godot 4.7 cannot combine heightmap/parallax with `uv1_triplanar = true`.** Any future Deep Parallax object needs the sphere's non-triplanar material swap.
- **Three tile constants live in `preview.gd`, each in different units:** CLI `tile`, `SPHERE_HEIGHTMAP_UV_SCALE`, and `SPHERE_MATCHED_TRIPLANAR_TILE`. Heightmap mode silently overrides the caller's tile.
- **The contact sheet `docs/images/cookbook-contact-sheet.png` is stale** (its 71 tiles include the now-retired m03/m04 and miss m06/s14), and no script writes its tracked path.
- **`promote_cookbook --check` compares against the gitignored `quality/authored/`.** After retiring or changing a material, re-run its category builder (`python -m quality.cookbook_<cat>`) and move stale `authored/` dirs aside, or `--check` reports false drift.
- **Standing render gotchas:**
  - One Godot at a time.
  - Never render from `python -c`.
  - Recover a hang with `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe`.
  - Port 8788 (mm-play) is sometimes held by another project's node server; use `MM_PLAY_PORT`.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

- **2026-09-27** (teardown #6, truth pass, m02 host pilot, outside PRs; merged through `7c64a8d`): v0.8.1; `size`/render-success/flat-retry fixes; cookbook 74→71 (m02 absorbs m03-m05); PRs #13/#7 merged, #8 closed.
- **2026-09-15/16** (iteration-and-parallax, merged): s14/m06 retunes; the Deep Parallax prototype on `s09_ashlar_wall` (`depth_tex`, sphere swap, `parallax_spin`); the BlockAO/BlockHeight swap fixed.
- **2026-09-15** (reflections cycle, merged `007d493`): sun-disc, SSR and opt-in clearcoat rig; m05, s14 and m06 added; the global normal green-flip was reverted (`4e239da`).
- **2026-09-14 night** (rig overhaul, `24ff854`): rounded-box cube, unified triplanar, lathed rook; front page recurated to 8 materials plus GIFs.
- **2026-09-14 late** (`4b0948f`): coin profile and two-scale gravel for s06/t03.
- **2026-09-14 evening** (merged): `normal_albedo_audit.py` and `_make_showcase.py`; 5 normal-registration fixes.
- **2026-09-14** (PR #11 `948a8e7`): the compound-node param default is now sourced from the remote node.
- **2026-09-14** (noise-vocabulary round 3, merged): 6 proof materials (65→71); the catalog_builder fixpoint fix.
