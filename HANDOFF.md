# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-14 (late evening CT) — s06/t03 shape tuning: coin profile,
grit-into-normal + seam substrate, two-scale size mix. Committed `4b0948f` and pushed to
branch `claude/unruffled-brattain-3ed050` (NOT yet merged to `main`)._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything older is one
line in the session log. "Heads-up" is a bounded list of live gotchas. Git history is the
archive.

## 🎯 Current state

`s06_river_pebbles` + `t03_gravel` shape tuning fully landed on branch
`claude/unruffled-brattain-3ed050` (commit `4b0948f`, pushed, **not yet merged to `main`**),
all Grayson visual-approved across the session, fast suite 1217 green:
- **Coin profile**: `cos(port0*B)` bell → `clamp(cos*1.5)` plateau → `smoothstep` bevel.
  Flat-topped stones with a rounded rim. smoothstep removes the clamp's C1 kinks that
  otherwise ring as washers under the param4=0 edge-detect normal.
- **Grit into the normal** (not just albedo): 0.15 of `perlin_grain` added onto the dome
  height before edge-detect. t03 also gained the grain-over-albedo it lacked.
- **Seam substrate**: dome field masks a rougher matte grit into the recessed seams; stone
  tops keep the wetter sheen (distinct roughness, not a dark gradient).
- **Two-scale mix**: a second finer voronoi (`voronoi_fine`, s06 scale 18 / t03 36) with its
  own nestled coin chain, `max`-composited so small stones fill the big ones' seams
  (tiny/medium/bigger). Breaks s06's old regular seam network. Fine layer carries its own
  per-cell colour via the same selection the height uses (NOT colourless bumps).
- **Grouping**: the two-scale apparatus is one `Stone Profile` subgraph (exposes Small stone
  size / Small stone height / Top flatness); kept OUT of Relief to avoid a subgraph cycle
  (dome_mix reads the coarse dome and feeds height_relief).

`normal_albedo_audit` flagged=False on both (relief shares the albedo's voronoi + voronoi_fine).

The original showcase work (regen hero + 8 gallery stills with the new rig, top-5 GIF strip,
cube triplanar + bevel) is still **pending** from the prior session — untouched here.

## 📌 Where we stopped

Committed `4b0948f` (coin + grit + seam + two-scale for s06/t03) and pushed the branch. Wrap-up
in progress. Branch is NOT merged to `main` — no PR opened yet.

## ▶️ Next concrete step

**Open a PR for `claude/unruffled-brattain-3ed050` → `main`** (or merge it) so s06/t03 land on
`main`. Then, options:
- Alt A: **note 3b** — a seam-substrate ALBEDO tint (darker muddy grit colour in the gaps),
  the one deferred piece of Grayson's "not just a dark gradient" ask. Small add: a
  dome_mix-masked blend darkening the seam albedo, mirror of `blend_rough`.
- Alt B: **cube triplanar + bevel** in `preview.gd` (seamless tiling around cube corners +
  modeled bevel; per-face BoxMesh UVs seam at every edge today).
- Alt C: **resume the showcase plan** (`docs/superpowers/plans/2026-09-14-showcase-lighting-refresh.md`):
  regen all 8 gallery stills + hero via `_make_showcase`, pick 5 GIF favorites, README motion strip.

## ❓ Open questions

- Size spread: Grayson OK'd s06 fine=18 / t03 fine=36 and nestle 0.65; note that t03 reads
  finer overall than s06 (different base scales) — not flagged as a problem, revisit if it is.
- note 3b seam-albedo tint: build it, or is roughness-only enough? (deferred, not decided).
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
  flat ALBEDO downscales. Only the former need regen for a lighting/rig change.
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

### 2026-09-14 (late evening: s06/t03 coin + grit + two-scale, committed `4b0948f`, pushed, NOT merged)
Follow-up shape tuning after 206b730's dome-softening, all Grayson visual-approved iteration by iteration. Coin profile = `clamp(cos(port0*B)*1.5)` plateau + `smoothstep` bevel (raw clamp alone rang as washer rings — the C1 kink under param4=0 edge-detect, same family as the earlier banding; smoothstep's zero-slope endpoints kill both kinks). Grit into the normal via 0.15*perlin_grain added onto the dome height; t03 also got the albedo grain it lacked. Seam substrate = dome-masked matte grit roughness. Two-scale = a finer `voronoi_fine` with its own nestled (*0.65) coin chain, `max`-composited so small stones fill the coarse seams (tiny/medium/bigger) and s06's regular seam network breaks up; the fine layer needs its OWN per-cell colour composited by the same selection or the small stones are colourless bumps (the audit is BLIND to that — both layers share voronoi_0). Grouping cleanup: one `Stone Profile` subgraph, kept out of Relief to avoid a subgraph cycle (dome_mix reads the coarse dome AND feeds height_relief). Committed 4b0948f, pushed branch. See memory [[coin-profile-two-scale-gravel]].
### 2026-09-14 (evening: normal/albedo audit + 5 fixes, MERGED to main)
Started as "re-render the front-page showcase with the new lighting rig". Built `_make_showcase.py`. Granite drift-check passed, but Grayson's eye caught the normal not registering with the surface. A/B green-flip test proved it was NOT a normal-convention flip. A no-render albedo-vs-normal pixel overlay + reading the builder found the cause: normal built from a SEPARATE coarse voronoi than the fleck albedo (MM position-seeding means they can't align). Built `normal_albedo_audit.py` to size it (8/71 flagged). Fixed granite + 4 siblings (normal derives from albedo source; pm04 inverted). Grayson approved granite/pm04/s04; s06+t03 to be softened to domes next; snow/powder-coat/enamel left fine-by-design. Merged main in first (reconciling HANDOFF/STATUS vs the concurrent task_73027cd8 work), then merged to main. Backlog idea logged: a "quality ops" runner to do these multi-step flows in fewer agent tokens.
### 2026-09-14 (task_73027cd8 compound-default fix, MERGED PR #11 `948a8e7`): `_parse_generic_node` now sources a compound param's `default` from the node's own remote/gen_parameters block, not the linked inner leaf (crystal.param0 was 4, real 16). Concurrent session.
### 2026-09-14 (worktree hygiene, no MM-MCP code): PEB-read process scan cleared a stuck Windows worktree lock (a hung `find /` + orphaned bash wrappers).
### 2026-09-14 (noise-vocabulary round 3 + catalog range fix, MERGED): 6 materials (cookbook 65->71), catalog_builder compound-node range fixpoint fix.
### 2026-09-14 (preview lighting overhaul, MERGED `6ce84c6`): render_preview rig reworked (soft key shadow, shadow-casting rim, sky bounce, SSAO, precession sweep). Tracked thumbnails are flat albedo so no regen needed.
### 2026-09-14 (pickup): ran `render_preview_sweep` for real, Grayson confirmed the GIF; promoted it ✅.
### 2026-09-14 (noise-vocabulary round 2, MERGED): 6 materials (cookbook 59->65), `node_usage_audit.py`, wood-donor metallic bug closed.
