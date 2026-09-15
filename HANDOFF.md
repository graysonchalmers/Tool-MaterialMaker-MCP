# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-15 01:45 CT — reflections cycle MERGED to `main` (`007d493`, pushed):
rig (ambient decouple + sun-disc reflection + SSR + opt-in clearcoat) + 3 reflective cookbook
materials. Materials need one more iteration pass next session (Grayson feedback below)._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything older is one
line in the session log. "Heads-up" is a bounded list of live gotchas. Git history is the
archive.

## 🎯 Current state

Reflections cycle, executed subagent-driven, **MERGED to `main` (`007d493`, pushed)**, fast
suite 1217 green. Two halves:

- **Rig (`preview.gd` + `preview.py`), all reviewed clean:** ambient decoupled from reflection
  (`AMBIENT_SOURCE_COLOR` pinned so enriching reflection can't re-light matte); a **sun-disc**
  reflection via a `SKY_ONLY` DirectionalLight (`reflection_sun`) so metals read while matte
  stays within tolerance; **SSR** (`ssr_enabled`) for object-to-object/ground reflections;
  an **opt-in clearcoat** param (`render_preview(clearcoat=, clearcoat_roughness=)`, default
  0.0 = no-op, preview-only since MM can't export clearcoat). New objective gate
  `quality/preview_regress.py` compares the 3D preview COMPOSITE (render_tracked only compares
  PBR maps, which a rig change never moves).
- **Materials (cookbook 71→74):** `m05_polished_chrome` (metallic mirror), `s14_wet_river_stone`
  (dielectric, roughness masked so crevices pool wet + tops dry), `m06_car_paint` (saturated
  candy-red metallic, real grazing Fresnel; can be shown with the preview clearcoat). All build,
  promote, gate-pass, and have flat-albedo thumbnails.

**Normal-inversion detour (important):** m04's scratches looked raised. I chased it to a
"global triplanar green-flip" fix (Task 10) — WRONG: it inverted the 8 approved materials
(cobblestone etc. were correct before). **Reverted** (`4e239da`). The triplanar rig renders
correctly-authored normals correctly (cobblestone proves it); m04's raised scratches are an
**m04-specific pre-existing authoring quirk**, out of this cycle's scope.

## 📌 Where we stopped

All 3 materials rendered and sent to Grayson. He gave iteration feedback (not final approval)
and chose to wrap. Nothing merged; final whole-branch review deferred to next session.

## ▶️ Next concrete step

**Apply Grayson's material feedback, then finalize + merge.**
- **s14 wet stone:** pebbles need ACTUAL reflection on their faces (not only in the crevices —
  right now tops are fully matte); tops are too flat; pebbles are all the same size — VARY the
  size. (So: partial wet sheen on pebble tops, add top curvature, size variation in the voronoi.)
- **m06 car paint (#3, clearcoat version):** feels flat / "missing surface detail" — add micro
  surface detail (orange-peel micro-normal, or a subtle flake normal). Deep base colors are ✅.
- Then: regen the stale contact sheet (72→74). (Cycle already merged to `main`; the deferred
  final whole-branch review can run against the merged history or be folded into the iteration.)

Alternatives: (a) fix m04's normal as a separate small per-material follow-up; (b) start the
emission cycle instead (reflections is landed).

## ❓ Open questions

- s14: how to give pebble FACES reflection without losing the crevice-pooling read? (graded
  wetness — wettest in crevices, semi-wet on tops — plus voronoi size variation.)
- m06 clearcoat: what surface detail reads as car paint — orange-peel micro-normal vs flake normal?
- Merge timing: hold all 3 materials until final, or merge rig+chrome+carpaint and iterate s14?
- Emission cycle (next after reflections): does "Godot 4 Standard" write `_emission.png`
  unconditionally or only when `emission_tex` connected? (decides if render.py must tolerate absence.)

## 🗂️ Changed this session

- Branch: `reflections` (14 commits, unmerged, NOT pushed). Fast suite 1217 green, tree clean.
- Key files: `src/mm_mcp/preview_project/preview.gd`, `src/mm_mcp/preview.py`,
  `quality/preview_regress.py` (new gate + test), `quality/cookbook_metal.py` (m05, m06),
  `quality/cookbook_stone.py` (s14), `cookbook/metal|stone/*`, `docs/images/cookbook-*/*` thumbs,
  spec+plan under `docs/superpowers/`.
- Decisions (+ why): sun-disc not global sky energy (global energy re-lit matte — the enum split
  isolates ambient SOURCE but reflection still hits every material's specular); clearcoat kept
  preview-only + opt-in (MM has no clearcoat channel, would break the round-trip); Task 10 global
  normal flip REVERTED (verify any normal fix against an APPROVED material first).

## ⚠️ Heads-up for the next agent

- **Reflections cycle is MERGED to `main` (`007d493`, pushed).** Branch `reflections` also on
  origin. Next-session material iteration can branch fresh from `main`.
- **`quality/preview_regress.py` is the no-regress gate for ANY rig/lighting change** — it
  renders the 3D preview COMPOSITE of a matte set and pixel-compares. Baseline lives at
  `scratchpad/reflect-baseline` (gitignored; recapture after an intended rig change).
- **Do NOT globally flip normals.** The triplanar rig renders correctly-authored normals
  correctly (cobblestone/s06 prove it). m04's raised scratches are an isolated per-material quirk.
  Verify any normal change against an APPROVED gallery material (e.g. s07_cobblestone) BEFORE shipping.
- **Clearcoat param is preview-only** (MM can't export it); `clearcoat=0.0` is a true no-op.
- **SSR + sun-disc are load-bearing** for reflections reading; `reflection_sun` is `SKY_ONLY`
  (cannot light objects directly) — that's what lets it be bright without disturbing matte.
- **SDD workspace kept** (final review deferred): `.superpowers/sdd/2026-09-14-reflections/progress.md`
  has the full task ledger, the rulings, and the regression story. Spec:
  `docs/superpowers/specs/2026-09-14-reflections-design.md`; plan:
  `docs/superpowers/plans/2026-09-14-reflections.md` (Tasks 1-10).
- **Contact sheet `docs/images/cookbook-contact-sheet.png` is stale at 72** (cookbook now 74) —
  regen in the wrap/showcase step (ungated, cosmetic).
- Standing render gotchas: one Godot at a time; `render()`/preview need ABSOLUTE outdir; never
  render from `python -c`; `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` to recover a hang.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

### 2026-09-15 (reflections cycle: rig + 3 materials, MERGED to `main` `007d493`)
Subagent-driven. Rig: ambient decouple (`befb1bf`), sun-disc reflection (`4ec9177`), SSR
(`fa8c526`), opt-in clearcoat param (`055b2e8`), + no-regress gate `quality/preview_regress.py`
(`3746d14`). Materials: m05 chrome (`059c5d9`), s14 wet stone dielectric (`ab8ff24`) then
roughness-masked v2 (`afa90f8`), m06 car paint (`b9ff20e`), thumbnails (`1c4c5f2`). Big detour:
a global normal green-flip (Task 10, `f7ac0d3`) that "fixed" m04 but INVERTED the 8 approved
materials — caught by comparing the approved gallery cobblestone, REVERTED (`4e239da`). m04's
raised scratches are a separate m04 quirk. Grayson likes car-paint colors; wants s14 pebbles to
reflect on faces + vary size + less-flat tops, and the car-paint clearcoat to gain surface
detail. Merged to `main` (`007d493`) mid-iteration at Grayson's call. See memory [[reflections-cycle-rig-and-materials]].
### 2026-09-14 (night: preview-rig overhaul + showcase recuration, committed to `main` `24ff854`)
Rig (`preview.gd`): cube → `_rounded_box` (Minkowski) + triplanar; unified ALL objects on one
triplanar material; cutaway ball → lathed chess rook. Recurated front page to 8 materials + hero
+ 5 GIFs. See memory [[preview-rig-rook-and-showcase-recuration]].
### 2026-09-14 (late evening: s06/t03 coin + grit + two-scale, committed `4b0948f`)
Coin profile + two-scale gravel for s06/t03. See memory [[coin-profile-two-scale-gravel]].
### 2026-09-14 (evening: normal/albedo audit + 5 fixes, MERGED to main)
Built `normal_albedo_audit.py` + `_make_showcase.py`; fixed granite + 4 siblings' normal
registration. See memory [[normal-albedo-registration-audit]].
### 2026-09-14 (task_73027cd8 compound-default fix, MERGED PR #11 `948a8e7`)
`_parse_generic_node` sources compound param default from the remote node, not the linked leaf.
### 2026-09-14 (noise-vocabulary round 3 + catalog range fix, MERGED)
6 materials (cookbook 65→71), catalog_builder compound-node range fixpoint fix.
### 2026-09-14 (preview lighting overhaul, MERGED `6ce84c6`)
render_preview rig reworked (soft key shadow, shadow-casting rim, sky bounce, SSAO, precession sweep).
### 2026-09-14 (pickup): ran `render_preview_sweep` for real, Grayson confirmed the GIF; promoted it ✅.
