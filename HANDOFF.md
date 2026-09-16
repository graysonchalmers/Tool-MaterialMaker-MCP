# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-16 — iteration-and-parallax cycle MERGED to `main` and pushed: s14/m06
retunes (code-clean, visual approval still outstanding) + a real Deep Parallax prototype
(Grayson-approved). See below._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything older is one
line in the session log. "Heads-up" is a bounded list of live gotchas. Git history is the
archive.

## 🎯 Current state

`iteration-and-parallax` cycle, executed subagent-driven (5 tasks + a final whole-branch review +
one fix wave), **MERGED to `main` and pushed**, fast suite 1254 green. Two threads:

- **s14/m06 iteration (Thread A), code-review clean, Grayson's VISUAL approval still
  outstanding:** `s14_wet_river_stone` got a two-scale pebble mix (size variation, ported from
  `s06_river_pebbles`'s pattern), curved (less-flattened) tops, and a lowered roughness ceiling so
  tops keep partial reflective sheen instead of reading fully matte. `m06_car_paint` got a
  coarser "orange peel" noise combined into its normal chain (relief 0.04→0.10) for surface
  detail under the clearcoat demo. Both were rendered and sent to Grayson; the conversation moved
  to Thread B before he replied — this is a known, tracked gap, not an oversight.
- **Deep Parallax prototype (Thread B), Grayson-approved after 4 rounds of live iteration:**
  confirmed this session (by reading the pristine MM checkout directly) that Material Maker's
  `material` node has a long-unused `depth_tex` input, and MM's own "Godot/Godot 4 Standard"
  export target already writes native `heightmap_enabled`/`heightmap_deep_parallax` when it's
  connected — a real round-trip feature, not a preview-only garnish like clearcoat. Added opt-in
  `heightmap_path`/`heightmap_scale` params to the preview rig. Discovered (and confirmed via
  engine warning + byte-identical render) that **Godot 4.7 flatly refuses to compose
  heightmap/parallax with triplanar UV mapping** — a hard engine limitation, not a bug. Iterated
  through Grayson's live feedback: a demo plane (rejected, nearly invisible) → swapping the rig's
  existing SPHERE to a non-triplanar material only when a heightmap is given (kept) → fixing the
  sphere's tile scale for legibility + adding a `parallax_spin` sweep mode (rotates the sphere,
  not the light — the existing light-sweep can't reveal parallax at all) → matching cube/rook/
  ground's tile density to the sphere's so the whole demo scene reads consistently. Wired
  `s09_ashlar_wall` to actually export it (`depth_scale` 0.2→0.3, `to_port 6` repointed to
  `colorize_6`); round-trip verified via a real `.tres` string-check, not just "a PNG exists."
- **Two things discovered mid-cycle, worth remembering:** (1) `s09_ashlar_wall`'s donor
  (`stone_wall`) already had an ACCIDENTAL, unexamined `depth_tex` connection — Deep Parallax was
  silently half-working before this session touched it; this cycle made it deliberate and fixed
  its polarity (the brief's draft `blend_2` tap was tried and rendered backwards). (2) that same
  investigation found `s09_ashlar_wall`'s `BlockAO`/`BlockHeight` role names were SWAPPED
  relative to actual wiring — fixed in the final-review fix wave. Grayson independently started
  a background session to fix the identical bug in parallel (unprompted, from an earlier
  suggestion); since redundant with the fix already on this branch, its commits were preserved
  under `archive/task_925ceb53-blockao-blockheight-fix` rather than merged twice.
- **Contact sheet regen DEFERRED, not done this session** — `docs/images/cookbook-contact-sheet.png`
  was already stale (72 vs 74) before this cycle and still needs a render pass across s14/m06's
  new look (s09 isn't gallery-facing, no thumbnail needed). Cosmetic/ungated; skipped this session
  per Grayson's "wrap and push" to avoid another render cycle.

## 📌 Where we stopped

Merged and pushed to `main` at Grayson's explicit "wrap and push." s14/m06 visual sign-off is
the one open loop — renders are already in his hands, just needs a reply.

## ▶️ Next concrete step

**Get Grayson's visual call on s14_wet_river_stone and m06_car_paint** (renders already sent
this session — pick up the reply, don't re-render unless he asks for changes). Then: regen the
contact sheet (still stale). Alternatives: (a) author 1-2 more Deep Parallax examples now that
the plumbing + one working material exist (original ask was "an example or two"); (b) the
emission cycle (parked since the reflections cycle, still untouched).

## ❓ Open questions

- s14/m06: same open loop as above — no new design questions, just needs Grayson's eyes.
- Deep Parallax has exactly ONE example (`s09_ashlar_wall`) — worth more, or is one proof-of-concept enough?
- Cookbook curation: Grayson raised (not scoped, "at some point") trimming the gallery — named
  candidates: `hazard stripe` (cut candidate), `circuit board` (doesn't read as circuit board),
  and stone-category overlap (dry stone wall/flagstone/cobblestone feel similar; river pebbles
  don't read as river pebbles). Likely a `teardown`-skill session when Grayson is ready to commit
  to it — not folded into any authoring cycle.
- Emission cycle (parked since reflections): does "Godot 4 Standard" write `_emission.png`
  unconditionally or only when `emission_tex` is connected?

## 🗂️ Changed this session

- Branch: `iteration-and-parallax`, 20 commits, MERGED to `main`, pushed.
- Key files: `quality/cookbook_stone.py` (s14, s09), `quality/cookbook_metal.py` (m06),
  `src/mm_mcp/preview.py` + `src/mm_mcp/preview_project/preview.gd` (opt-in heightmap params,
  sphere material swap, `parallax_spin` sweep), `src/mm_mcp/server.py` (docstring),
  `tests/test_preview.py`, `cookbook/stone|metal/*`, spec+plan under `docs/superpowers/`.
- Decisions (+ why): sphere-swap not a new demo object (Grayson: "same shaped objects, no new
  object"); `parallax_spin` rotates the object not the light (parallax is camera-angle-dependent,
  a light sweep can't show it); `depth_tex` wired via `rewire()` not `append()` on `s09` (a
  connection already existed — an `append` would've left two edges into one port); the
  `BlockAO`/`BlockHeight` swap fixed on this branch rather than merging the parallel duplicate fix.

## ⚠️ Heads-up for the next agent

- **Godot 4.7 cannot combine heightmap/parallax with `uv1_triplanar = true`** — confirmed via
  engine warning + byte-identical render, not assumed. Any FUTURE object that needs Deep Parallax
  in the preview rig needs the same non-triplanar-material-swap pattern the sphere uses now, not
  a triplanar material with heightmap fields set (those get silently ignored by Godot).
- **Three tile/density constants now live in `preview.gd`, each with different UV-space
  semantics** — the CLI `tile` param (triplanar, world-space), `SPHERE_HEIGHTMAP_UV_SCALE`
  (equirect, sphere-only), `SPHERE_MATCHED_TRIPLANAR_TILE` (triplanar, but tuned to visually
  match the sphere when heightmap mode is active). Don't assume any two of these should share a
  value — they were each hand-tuned by rendering, not derived from a formula.
- **Known parked Minor (not fixed, low severity):** `shared_tile` selection is gated on
  `heightmap_path != ""` alone, while whether the sphere ACTUALLY gets its parallax material also
  depends on the texture load succeeding — in the rare case a given heightmap path fails to load,
  cube/rook/ground would render at the sphere-matched tile even though the sphere itself silently
  fell back to normal. Error-path only; no real render has ever hit this.
- **SDD workspace deleted** (final review clean, fix wave landed) — the full task ledger, every
  ruling, and the visual-iteration history live in `git log` on this branch now. Spec:
  `docs/superpowers/specs/2026-09-15-iteration-and-parallax-design.md`; plan:
  `docs/superpowers/plans/2026-09-15-iteration-and-parallax.md` (Tasks 1-5, all checked off,
  amended in place multiple times to record real deviations — read it as history, not just intent).
- **Contact sheet `docs/images/cookbook-contact-sheet.png` is stale** (needs s14/m06/s09 re-render)
  — still true, carried over, not this session's regression.
- Standing render gotchas: one Godot at a time; `render()`/preview need ABSOLUTE outdir; never
  render from `python -c`; `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` to recover a hang.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

### 2026-09-15/16 (iteration-and-parallax: s14/m06 retunes + Deep Parallax prototype, MERGED to `main`)
Subagent-driven, 5 tasks + final whole-branch review + 1 fix wave. s14 two-scale pebbles/curvature/
reflection retune and m06 orange-peel normal: code-review clean, Grayson's visual approval still
outstanding (renders sent, conversation moved on before reply). Deep Parallax: confirmed `depth_tex`
+ MM's Godot-4-export round-trip by reading the pristine MM checkout; discovered Godot 4.7 can't
compose heightmap/parallax with triplanar (engine warning + byte-identical render); iterated
through Grayson's live feedback across 4 rounds (demo plane → sphere swap → tile-scale+sweep fix →
density match) to a Grayson-approved result; wired `s09_ashlar_wall` for real (found + fixed an
accidental pre-existing donor connection, wrong-polarity draft caught by render, and a swapped
BlockAO/BlockHeight naming bug independently also fixed by Grayson's own parallel background
session — reconciled, not double-merged). Final review: 2 Important + 3 Minor findings, one fix
wave, all addressed; full suite 1254 green throughout. See ledger:
`.superpowers/sdd/2026-09-15-iteration-and-parallax/progress.md` (workspace deleted post-merge,
history lives in git). Contact sheet regen deferred to next session.
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
