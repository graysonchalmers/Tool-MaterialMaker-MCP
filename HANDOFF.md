# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-14 (night CT) — preview-rig overhaul (rounded-bevel cube,
unified triplanar tiling, cutaway ball → lathed chess rook) + front-page showcase
recuration to 8 new materials + 5 GIFs. All merged/committed to `main` (`24ff854`), only
the final showcase commit + this wrap-up unpushed._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything older is one
line in the session log. "Heads-up" is a bounded list of live gotchas. Git history is the
archive.

## 🎯 Current state

The preview rig (`src/mm_mcp/preview_project/preview.gd`) and the front-page showcase are
fully reworked and committed to `main`, every step Grayson visual-approved:
- **Rounded-bevel cube**: `_rounded_box` helper (dense subdivided box pushed onto a box+sphere
  Minkowski surface, analytic normals, flat faces preserved) + a triplanar material, so the
  texture wraps seamlessly across faces and the rounded edges. `_rounded_box` welds coincident
  verts into a manifold (required for it to work as a CSG cutter).
- **Unified tiling**: every object (sphere/cube/ground/rook) shares one triplanar material at a
  single world-space density; the old per-object UV/multiplier scales are gone. Default tile
  lowered 1.0 → **0.45** (preview.py `render_preview`/`_sweep` + the .gd fallback).
- **Chess rook** replaces the cutaway ball: a lathe (`_lathe`, surface of revolution) driven by
  a Catmull-Rom profile (`_catmull_profile`) — bold molding silhouette (base torus + cornice)
  with smooth vertex normals so it flows, plain circular top, height matched to the cube. The
  lathe carries UVs + `generate_tangents()` (missing tangents rendered it black under triplanar
  normal mapping); its outward normal sign was verified in-render (the geometric guess was
  inverted).
- **Showcase recuration** (`24ff854`): gallery swapped to 8 higher-contrast materials —
  cobblestone, ashlar wall, marble, raw crystal, hazard stripe, herringbone tweed, cracked ice,
  riverbed pebbles — chosen off a full-71 browse. New hero (cobblestone/marble/crystal), a new
  "In motion" README strip of 5 light-sweep GIFs, and per-material tile overrides baked into
  `quality/_make_showcase._TILE_OVERRIDES` (one global tile can't fit every material's baked
  feature size). GIFs shrunk to ~0.7–0.9MB (448px/14f, shared 128-colour palette + optimize).

The concurrent coin-profile session's s06/t03 work merged into `main` cleanly (`abaecee`); it
superseded this session's earlier intermediate dome-soften of s06/t03.

## 📌 Where we stopped

Showcase regen fully committed (`24ff854`), gates green (README/showcase/package suites). Two
backlog items captured for next session (reflections; self-illumination/lava — see below).
Wrap-up in progress; `main` is 1 commit ahead of origin (the showcase commit) plus this wrap-up.

## ▶️ Next concrete step

**Push `main`** (approval standing this session) so the showcase + rig land on origin. Then the
two new backlog items are the natural next work:
- Alt A: **Reflections / reflection mapping** — materials have no reflectivity/env-reflection
  control yet. Add a reflection/metallic-reflection path (likely an ORM-metallic + environment
  probe already partly present in the rig; expose/author it per material).
- Alt B: **Self-illumination (emission)** — add an emissive channel and author a glowing
  material (lava / something that emits light). The rig would need to honour an emission map.
- Alt C: **GIF polish** — the sweep GIFs are functional; revisit palette/dither if any bands.

## ❓ Open questions

- Reflections: author per-material, or a global rig reflection strength? Where does MM's ORM
  metallic feed the reflection today vs what needs adding?
- Emission: does a lava material want a separate emission map output from the graph, and does
  `render_preview`/ORMMaterial3D need an emission_texture wired?
- Rook proportions/molding are Grayson-approved as-is; revisit only if a future eye disagrees.

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
- **Front-page hero + `docs/images/gallery/*.png` ARE lit 3D `render_preview` renders** (now on
  the CURRENT rook rig at per-material tile), UNLIKE the cookbook thumbnails
  `docs/images/cookbook-*/*.png` which are flat ALBEDO downscales. Only the former need regen
  for a lighting/rig change. Regen via `python -m quality._make_showcase still|hero|gif`.
- **Per-material tile lives in `quality/_make_showcase._TILE_OVERRIDES`** — a material that reads
  too small/large in the showcase gets a tile there (lower = bigger cells), not a global change.
  The rig default is 0.45.
- **`_rounded_box` / `_lathe` in `preview.gd` are hand-built meshes.** The lathe needs
  UVs + `generate_tangents()` or triplanar normal-mapping renders it BLACK (no tangent basis).
  Both are welded/manifold. Two materials had NO normal output (m01_weathered_copper,
  combo01_rusted_painted_steel) so they can't show relief — unusable for the 3D showcase.
- **GIF budget**: keep sweep GIFs ≤~1.5MB (they live in git forever). `cmd_gif` now quantizes to
  a shared 128-colour palette + `optimize=True`; 448px/14f lands ~0.7–0.9MB. Eyeball glossy
  materials for palette banding.
- **`promote_cookbook` full-category runs churn every card's line endings (autocrlf)**;
  `git checkout --` the unintended `.md` churn so only the changed material's files stage.
- **A git worktree needs its own `.env`** (copy from the main checkout). Without it
  `cfg.nodes_dir` resolves to a relative path that doesn't exist and `render_one` aborts at
  validation with a wall of "unknown node type 'material'" — the catalog silently failed to
  load, not a real graph error.
- **`normal_albedo_audit` is blind to per-LAYER misregistration.** It only checks whether the
  albedo and normal source-generator SETS are disjoint. A two-layer material whose fine relief
  layer has no matching fine COLOUR still passes (both share the coarse voronoi). Judge fine
  layers by eye, not the audit.
- Standing render gotchas: one Godot at a time; `render()` needs ABSOLUTE outdir; in Git Bash
  `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (double slashes) to recover a hang;
  every session spawns its own `mm-mcp.exe`.
- SDD ledger for this work: `.superpowers/sdd/2026-09-14-showcase-lighting-refresh/progress.md`.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

### 2026-09-14 (night: preview-rig overhaul + showcase recuration, committed to `main` `24ff854`)
Long visual-iteration session, every step Grayson-approved. Rig (`preview.gd`): cube → `_rounded_box` (Minkowski box+sphere, analytic normals) + triplanar; unified ALL objects on one triplanar material (dropped per-object UV/multiplier scales); cutaway ball → chess rook via `_lathe` + `_catmull_profile` (bold molding silhouette, smooth normals, circular top, cube height). Debugged: lathe rendered black until it got UVs + `generate_tangents()` (triplanar normal-map needs a tangent basis); its outward-normal sign was inverted vs the (r,y) guess and fixed in-render. Baked default tile 1.0→0.45, then per-material `_TILE_OVERRIDES` in `_make_showcase`. Recurated the front page: browsed all 71, rendered a 12-candidate 3D contact sheet, Grayson picked 8 (cobblestone/ashlar/marble/crystal/hazard/herringbone/ice/pebbles) + hero (cobblestone/marble/crystal) + 5 GIFs. Fixed a `cmd_gif` Windows temp-cleanup crash (unclosed handle) and added GIF quantize+optimize (~0.7–0.9MB). Backlog logged: reflections/reflection-mapping + self-illumination (lava). See memory [[preview-rig-rook-and-showcase-recuration]].
### 2026-09-14 (late evening: s06/t03 coin + grit + two-scale, committed `4b0948f`, pushed, NOT merged)
Follow-up shape tuning after 206b730's dome-softening, all Grayson visual-approved iteration by iteration. Coin profile = `clamp(cos(port0*B)*1.5)` plateau + `smoothstep` bevel (raw clamp alone rang as washer rings — the C1 kink under param4=0 edge-detect, same family as the earlier banding; smoothstep's zero-slope endpoints kill both kinks). Grit into the normal via 0.15*perlin_grain added onto the dome height; t03 also got the albedo grain it lacked. Seam substrate = dome-masked matte grit roughness. Two-scale = a finer `voronoi_fine` with its own nestled (*0.65) coin chain, `max`-composited so small stones fill the coarse seams (tiny/medium/bigger) and s06's regular seam network breaks up; the fine layer needs its OWN per-cell colour composited by the same selection or the small stones are colourless bumps (the audit is BLIND to that — both layers share voronoi_0). Grouping cleanup: one `Stone Profile` subgraph, kept out of Relief to avoid a subgraph cycle (dome_mix reads the coarse dome AND feeds height_relief). Committed 4b0948f, pushed branch. See memory [[coin-profile-two-scale-gravel]].
### 2026-09-14 (evening: normal/albedo audit + 5 fixes, MERGED to main)
Started as "re-render the front-page showcase with the new lighting rig". Built `_make_showcase.py`. Granite drift-check passed, but Grayson's eye caught the normal not registering with the surface. A/B green-flip test proved it was NOT a normal-convention flip. A no-render albedo-vs-normal pixel overlay + reading the builder found the cause: normal built from a SEPARATE coarse voronoi than the fleck albedo (MM position-seeding means they can't align). Built `normal_albedo_audit.py` to size it (8/71 flagged). Fixed granite + 4 siblings (normal derives from albedo source; pm04 inverted). Grayson approved granite/pm04/s04; s06+t03 to be softened to domes next; snow/powder-coat/enamel left fine-by-design. Merged main in first (reconciling HANDOFF/STATUS vs the concurrent task_73027cd8 work), then merged to main. Backlog idea logged: a "quality ops" runner to do these multi-step flows in fewer agent tokens.
### 2026-09-14 (task_73027cd8 compound-default fix, MERGED PR #11 `948a8e7`): `_parse_generic_node` now sources a compound param's `default` from the node's own remote/gen_parameters block, not the linked inner leaf (crystal.param0 was 4, real 16). Concurrent session.
### 2026-09-14 (worktree hygiene, no MM-MCP code): PEB-read process scan cleared a stuck Windows worktree lock (a hung `find /` + orphaned bash wrappers).
### 2026-09-14 (noise-vocabulary round 3 + catalog range fix, MERGED): 6 materials (cookbook 65->71), catalog_builder compound-node range fixpoint fix.
### 2026-09-14 (preview lighting overhaul, MERGED `6ce84c6`): render_preview rig reworked (soft key shadow, shadow-casting rim, sky bounce, SSAO, precession sweep). Tracked thumbnails are flat albedo so no regen needed.
### 2026-09-14 (pickup): ran `render_preview_sweep` for real, Grayson confirmed the GIF; promoted it ✅.
