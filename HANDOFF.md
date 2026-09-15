# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-14 (evening CT) — normal/albedo registration audit + fixes on a
feature branch `showcase-lighting-refresh`, NOT yet merged to `main`. This began as a
front-page "re-render the showcase with the new lighting rig" task and pivoted into a
cookbook-quality fix after Grayson's eye caught a real normal bug._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything older is one
line in the session log. "Heads-up" is a bounded list of live gotchas. Git history is the
archive.

## 🎯 Current state

On branch **`showcase-lighting-refresh`** (off `main` at `341a212`), four commits, **not merged**:
- `7d9f2a2` `quality/_make_showcase.py` — reproducible front-page render pipeline
  (still / hero-montage / gif modes) + 6 unit tests. Replaces the ad-hoc way hero+gallery
  were made. NOT yet used to regen the tracked gallery.
- `9678006` `quality/normal_albedo_audit.py` — static audit that traces each material's
  albedo-source vs normal-source generators (across subgraph gen_inputs/gen_outputs proxies)
  and flags materials where the two sets are DISJOINT (relief built from a different noise
  than the color, so it does not register). Reviewer hand-verified the traversal.
- `ee7a6eb` granite fix — `s02_gray_granite` normal now derives from the fleck voronoi
  (was a separate coarse voronoi). Audit flagged=False. Grayson-approved (param1=0.3).
- `644e820` 4 more fixes — `s06_river_pebbles`, `s04_scattered_river_stones`, `t03_gravel`
  (normal from the albedo cell source), `pm04_hammertone` (inverted: albedo from the dimple
  warp field, dimples stay hero). All audit flagged=False, full suite green.

The audit found **8/71** materials with this normal/albedo mismatch, all sharing the
"separate relief subgraph" idiom. Triage (visual, since the r-metric alone over-flags
smooth-albedo materials) sorted them: **fixed** = granite + the 4 above; **left as fine by
design** = `t02_fresh_snow`, `pm01_powder_coat`, `pm02_automotive_enamel` (smooth/uniform
albedo, relief is the intended feature, nothing to misregister).

Grayson approved `pm04_hammertone` and `s04_scattered_river_stones` as-is. He wants
`s06_river_pebbles` and `t03_gravel` **softened to domes** (they currently read faceted
because raw voronoi cells feed the normal as flat-topped facets) — NOT done yet.

The original showcase work (regen hero + 8 gallery stills with the new rig, top-5 GIF strip,
cube triplanar + bevel) is all still **pending** behind this normal detour.

## 📌 Where we stopped

Grayson said wrap up. pm04 + s04 approved; s06 + t03 need dome-softening next. Nothing
merged; branch is clean (this wrap-up commits the plan doc + a scratch-file cleanup).

## ▶️ Next concrete step

**Soften `s06_river_pebbles` + `t03_gravel` relief to domes**: in their builders
(`quality/cookbook_stone.py`, `quality/cookbook_terrain.py`), feed the normal from the
voronoi DISTANCE field (port 0, domed) instead of the hard per-cell value (port 1, flat
facets), or add a light warp back; re-render previews, get Grayson's ok. Audit must stay
flagged=False. Then:
- Alt A: **cube triplanar + bevel** in `preview.gd` (Grayson's other request: seamless
  tiling around the cube corners + a modeled bevel; the per-face BoxMesh UVs seam at every
  edge today).
- Alt B: **resume the showcase plan** (`docs/superpowers/plans/2026-09-14-showcase-lighting-refresh.md`):
  regen all 8 gallery stills + hero via `_make_showcase`, pick 5 GIF favorites, add a README
  motion strip.
- Alt C: **merge `showcase-lighting-refresh` to `main`** once the material work is signed off
  (norm-ask gate; not yet requested).

## ❓ Open questions

- Merge the branch to `main` now (5 material fixes + 2 new tools are done and green) or hold
  until the s06/t03 dome pass + the showcase renders are also on it? Grayson to call.
- s06/t03 dome method: voronoi distance-field vs a re-added light warp (visual preference).
- The 3 "fine by design" flagged materials (snow, powder-coat, enamel): confirmed leave-as-is
  this session; revisit only if a future eye disagrees.
- Original showcase open items still stand: which 5 materials become GIFs, GIF size budget,
  hero trio.

## ⚠️ Heads-up for the next agent

- **New tool `quality/normal_albedo_audit.py`** is the objective gate for "does relief
  register with color": `audit_graph(ptex)["flagged"]` False = shares a source. Run
  `python -m quality.normal_albedo_audit` for the full 71-material report. Use it to verify
  any normal-relief fix instead of eyeballing.
- **New tool `quality/_make_showcase.py`** regenerates hero/gallery/GIFs in one command
  (still/hero/gif modes). Gallery still native size is 1024x576; hero is a 3-panel montage
  (683x560 x3 = 2049x560). Use it for the pending showcase regen rather than re-doing it
  ad-hoc.
- **The normal/albedo bug pattern**: MM seeds voronoi from NODE POSITION, so two different
  voronoi nodes never share a cell layout even at equal scale. A normal that must register
  with the albedo has to derive from the SAME generator node. Granite/s04/s06/t03/pm04 are
  the fixed examples; mirror them.
- **The r-metric in `scratchpad/triage_normal_align.py` is CONFOUNDED**: r~0 fires both on
  real misregistration AND on smooth-albedo materials (nothing to correlate). Judge with the
  visual contact sheet, not the number alone.
- **Front-page hero + `docs/images/gallery/*.png` ARE lit 3D `render_preview` renders** (still
  on the OLD rig), UNLIKE the cookbook thumbnails `docs/images/cookbook-*/*.png` which are
  flat ALBEDO downscales. Only the former need regen for a lighting/rig change. (Corrects the
  earlier baton implication that "no regen needed".)
- **`promote_cookbook` full-category runs churn every card's line endings (autocrlf)**;
  `git checkout --` the unintended `.md` churn so only the changed material's files stage.
- **Branch not merged**: `showcase-lighting-refresh` holds all this session's work; `main` is
  untouched. Don't assume `main` has the fixes.
- Standing render gotchas: one Godot at a time; `render()` needs ABSOLUTE outdir; in Git Bash
  `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (double slashes) to recover a hang;
  every session spawns its own `mm-mcp.exe`.
- SDD ledger for this work: `.superpowers/sdd/2026-09-14-showcase-lighting-refresh/progress.md`.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

### 2026-09-14 (evening: normal/albedo audit + fixes, branch showcase-lighting-refresh, NOT merged)
Started as "re-render the front-page showcase with the new lighting rig". Built `_make_showcase.py` (Task 1). Drift-check on granite passed, but Grayson's eye caught the normal not registering with the surface. Ran controlled A/B (green-channel flip) on hex + granite: flip barely changed anything => NOT a global normal-convention bug. New hypothesis via a no-render albedo-vs-normal pixel overlay + reading the builder: granite's normal came from a SEPARATE coarse voronoi than its fleck albedo (MM position-seeding means they can never align). Built `normal_albedo_audit.py` (Task A) to size it: 8/71 flagged. Fixed granite (Task B) + 4 siblings (Task C, opus): normal derives from the albedo source; pm04 inverted (albedo from dimple field). Grayson approved granite/pm04/s04; s06+t03 to be softened to domes next; snow/powder-coat/enamel left as fine-by-design. All fixes audit-clean + full suite green. Backlog idea logged (commons ideas file): a "quality ops" runner to do these multi-step flows in fewer agent tokens.
### 2026-09-14 (worktree hygiene, no MM-MCP code): PEB-read process scan cleared a stuck Windows worktree lock (a hung `find /` + orphaned bash wrappers, not Godot/Python); `task_86ba47bd` dismissed.
### 2026-09-14 (noise-vocabulary round 3 + catalog fix, MERGED): 6 materials (cookbook 65->71), real catalog_builder compound-node range fix (fixpoint loop). `task_73027cd8` spawned for compound default-field accuracy.
### 2026-09-14 (preview lighting overhaul, MERGED `6ce84c6`): render_preview rig reworked (soft key shadow, shadow-casting rim, sky bounce fixing dark metals, SSAO, precession-default sweep). Tracked thumbnails are flat albedo so no regen was needed.
### 2026-09-14 (pickup): ran `render_preview_sweep` for real through the MCP surface, Grayson confirmed the GIF; promoted it ✅.
### 2026-09-14 (noise-vocabulary round 2, MERGED): 6 materials (cookbook 59->65), `node_usage_audit.py`, wood-donor metallic bug closed w04/w05/w06.
### 2026-09-14 (rotating-key-light sweep, MERGED `58e35ab`): `render_preview_sweep` azimuth mode + 11th MCP tool, TDD.
### 2026-09-13 (enum-index validation enforcement, MERGED): out-of-range enum index -> hard error with intended-index hint; ratchet test.
