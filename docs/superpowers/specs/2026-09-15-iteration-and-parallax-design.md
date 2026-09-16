# Material Iteration + Deep Parallax — Design Spec

_Date: 2026-09-15 · Status: approved, ready for plan · Cycle: post-reflections iteration
(applies Grayson's s14/m06 feedback) + a new, separate feature prototype (Deep Parallax)_

## Problem — two independent threads, one session

**Thread A (iteration, not new scope):** the reflections cycle (`007d493`, merged) shipped
`s14_wet_river_stone` and `m06_car_paint` mid-iteration. Grayson reviewed the renders and gave
concrete, unresolved feedback — this is the tail of an already-approved cycle, not a new design.

**Thread B (new, scoped this session):** Grayson asked whether the project could demonstrate
Godot's Deep Parallax (parallax occlusion mapping). Investigation this session (reading the
pristine `z-Git/material-maker` checkout directly) found the plumbing already exists on both
sides — MM's own `material` output node has an unused `depth_tex` input, and MM's own
"Godot/Godot 4 Standard" export target already writes native `heightmap_enabled` +
`heightmap_deep_parallax` when that input is connected (`addons/material_maker/nodes/material.mmg`
lines 656-663 of the checkout). This is a real round-trip feature (ships in the exported
`.tres`), unlike the preview-only clearcoat garnish from the reflections cycle. Two gaps: no
cookbook material feeds `depth_tex`, and the preview rig (`preview.gd`) never loads a heightmap.

These threads touch different files (`quality/cookbook_stone.py` + `quality/cookbook_metal.py`
for A; `src/mm_mcp/preview.py` + `preview.gd` + a new cookbook material for B) and ship
independently — B is not blocked by A. They are bundled into one cycle only because both were
scoped in the same pickup session, matching this project's precedent of one spec/plan per
session's worth of related work (see the reflections cycle, which bundled a rig change with two
authoring tasks the same way).

## Thread A — s14 / m06 iteration feedback

### s14_wet_river_stone (`quality/cookbook_stone.py:1342`, `build_s14_wet_river_stone`)

Grayson's exact feedback, three complaints:

1. **"Pebbles need ACTUAL reflection on their faces (not only in the crevices — right now tops
   are fully matte)."** Root cause: `colorize_2`/`colorize_dry` (the wet/dry roughness gradients,
   both driven by `dome_smooth`'s height field) ramp roughness UP toward the tops — `WetRoughness`
   tops out at 0.35, `DryRoughness` at 0.60. A dielectric at roughness 0.35-0.60 reads as
   effectively matte under this rig's lighting. Fix direction: lower both gradients' TOP-END
   value so tops keep a readable partial sheen (semi-wet, not bone-dry) while crevices stay the
   glossiest point — the contrast (crevice glossier than top) is the "graded wetness" read
   Grayson wants kept, only the ceiling needs to come down.
2. **"Tops are too flat."** Root cause: `dome_flatten` (`math` op 2, `default_in2=1.5`, clamped)
   deliberately widens the coin's flat plateau (this is s06's proven "coin, not full dome"
   profile, cloned verbatim into s14). For s14 specifically, less flattening (a smaller
   `default_in2`, more of the cos-bell curvature surviving) gives the tops visible curvature
   without abandoning the coin-profile normal-relief technique that avoids the ring/banding
   artifacts documented in s06's build history.
3. **"Pebbles are all the same size — VARY the size."** s14 currently uses s06's *single-scale*
   dome (deliberately, per the build's own docstring: "single-scale version... the extra detail
   layers aren't needed to prove the reflection path"). That reasoning no longer holds now that
   Grayson wants size variation. s06 already solves this exact problem (`s06_river_pebbles`,
   `build_s06_river_pebbles`): a second, finer voronoi (`voronoi_fine`) with its own identical
   coin chain, nestled lower (`* 0.65`) and MAX-composited with the coarse dome so small stones
   fill the coarse dome's seams without flattening them. Port that pattern into s14, remembering
   the s06 "registration" lesson verbatim: **the roughness/albedo masks must ALSO branch on the
   same coarse/fine selection**, or every small stone is a colorless, roughness-mismatched bump
   inheriting the big cell's values (this is exactly what s06's `sel_fine` mask + `colorize_fine`
   + `blend_layer_color` exist to prevent — s14's `WetRoughness`/`DryRoughness`/`PatchMask` chain
   needs the equivalent, not just the color).

### m06_car_paint (`quality/cookbook_metal.py:314`, `build_m06_car_paint`)

Grayson: **"feels flat / missing surface detail"** on the clearcoat-on variant (the preview
`clearcoat` param demo). Deep base colors are approved — do not touch `colorize_0`'s albedo
gradient. Root cause: `normal_amount` is pinned at 0.04 (chrome's near-mirror value, inherited
from `m05_polished_chrome`'s precedent of "not 0, which bakes Godot's dead-flat default, but as
close to flat as a genuine mirror needs"). Car paint under a flashy clearcoat needs to read as a
painted panel, not a mirror — real automotive base-coat has a faint "orange peel" texture (a
soft, medium-frequency undulation from spray application) that a mirror-flat clearcoat still
reveals underneath. Fix direction: add a second, coarser-frequency noise (distinct scale from
the existing `MicroNoise`, which is fine high-frequency grain feeding albedo/roughness/flake) INTO
the normal chain — combined with the existing normal input via a `math` add (the same technique
s06 used to fold `grain_scaled` into `height_relief` before `normal_map_0`) — and raise
`normal_amount` modestly so the orange-peel wave is visible without turning the paint rough or
matte (roughness/albedo/metallic stay as approved). Do not swap to a flake-bump approach unless
the orange-peel direction visually fails — Grayson's wording ("orange-peel micro-normal vs flake
normal", his own open question from the handoff) makes orange-peel the more literal match for
"missing surface detail" on a painted panel.

### Housekeeping

The cookbook contact sheet (`docs/images/cookbook-contact-sheet.png`) is stale at 72; cookbook is
now 74 (75 after Thread B's new material). Regen once both materials are approved — no separate
approval needed, it is a mechanical regen of an already-approved gallery.

## Thread B — Deep Parallax prototype

### What already works (verified this session, not assumed)

- `material.mmg`'s `material` output node ships a `depth_tex` float input (0-1 height) on EVERY
  cookbook `.ptex` — it has always been there, just never connected by any builder.
- The "Godot/Godot 4 Standard" export target (`render.py`'s `--target` flag) already emits, when
  `depth_tex` is connected: `heightmap_enabled = true`, `heightmap_deep_parallax = true`,
  `heightmap_scale = 25.0 * depth_scale` (the material node's own `depth_scale` param, default
  0.5, already present on every material node — see `_from_scratch_noise_material`'s
  `"depth_scale": 1` default), `heightmap_min_layers = 8`, `heightmap_max_layers = 32`, plus a
  `<name>_heightmap.png` file. Verified directly in
  `C:\Projects-local\z-Git\material-maker\addons\material_maker\nodes\material.mmg` lines 656-663.
  This is real, round-trip-safe (ships in the actual exported `.tres` a Godot user would import),
  not a preview-only garnish like the reflections cycle's clearcoat.
- `Material.to_port` indices (confirmed by cross-referencing `_from_scratch_noise_material`'s own
  wiring — `to_port 0` = albedo, `to_port 2` = roughness, `to_port 4` = normal, both matching the
  node's declared input order): `depth_tex` is **`to_port 6`**.

### What's missing (two additive gaps, not a redesign)

1. **No cookbook material connects anything to `depth_tex`.** Needs one new (or retrofitted)
   material whose existing height/relief signal — most materials already generate one for their
   normal map or roughness masking — also feeds `to_port 6` on the `Material` node.
2. **`preview.gd`'s `_make_material` (lines 354-371) never loads a heightmap.** It wires
   `albedo_texture`/`normal_texture`/`orm_texture` only. Needs the same opt-in, default-off
   pattern already proven for `clearcoat` (`preview.py` → CLI arg → `preview.gd` parse → material
   property), so every existing render and the `preview_regress` no-regress gate are unaffected
   by construction when no heightmap is passed.

### Open technical risk — triplanar + heightmap composition (verify, don't assume)

The preview rig's shared material uses `mat.uv1_triplanar = true` (position-projected UVs,
blended by normal) for every object. Godot's built-in parallax/heightmap offset math is normally
expressed in terms of the mesh's own UV1 and the view vector in tangent space; whether Godot 4.7's
`BaseMaterial3D`/generated shader actually composes a heightmap offset correctly under triplanar
projection is NOT something to assume from documentation — it must be checked with a real render.
If it does not visibly work (no parallax depth at an oblique angle even with an exaggerated
`heightmap_scale`), the fallback is a small NON-triplanar, plain-UV test plane added to the rig
specifically for the parallax demo, rather than trying to make the shared triplanar objects show
it. Do not build that fallback preemptively — only reach for it if the empirical check fails.

### Choosing the demo material

Parallax occlusion mapping reads best on relief with real per-cell DEPTH at a coarse-ish scale
(mortar joints, plate gaps) rather than fine surface grain, since POM needs enough visually
distinguishable depth steps to register. `s09_ashlar_wall` (blocky masonry with real recessed
joints, not currently on the front-page gallery so a rough first pass carries no regression risk
to an already-approved material) is the leading candidate; `s07_cobblestone`-style plate gaps are
a plausible second. Final pick is a visual call, same as any authoring task — build the plumbing
generically enough that trying a second material costs a re-run, not a rewrite.

### Non-goals

- **Retrofitting `depth_tex` onto every material.** One (maybe two) worked example(s) proves the
  path; blanket rollout is separate scope, explicitly out per Grayson's own framing ("an example
  or two").
- **Changing the default rig lighting/camera for parallax specifically.** The existing oblique-ish
  camera (`cam.position = Vector3(0, 1.4, 6.5)`, `fov 36`, `look_at` origin) and the existing
  `render_preview_sweep` are the verification tools; parallax is view-angle-dependent, so lean on
  the sweep rather than building a new camera mode.
- **Solving the export-side emission question** (parked from the reflections cycle) — unrelated.

## Gate — objective, not eyeball

- **Thread A:** `promote_cookbook.py --check`, `quality/preview_regress.py` (only if the rig
  itself is touched, which it is not for Thread A), full fast suite, cookbook naming/card-table/
  README-count gates, and Grayson's visual approval on the re-rendered s14/m06.
- **Thread B rig change:** the `clearcoat`-pattern TDD (a command-construction test proving the
  heightmap arg is a true no-op at its default), then `quality/preview_regress.py` against the
  existing baseline (`scratchpad/reflect-baseline`) to prove the opt-in default doesn't move any
  existing render.
- **Thread B material:** same authoring gates as any new/modified cookbook entry, plus a real
  `render()` call confirming `_heightmap.png` is actually produced and the exported `.tres`
  contains `heightmap_enabled = true` (a `grep`/string check on the `.tres`, not just "the PNG
  exists" — the whole point is proving the round-trip, not just the preview).
- Full suite green before the wrap-up commit.

## Files touched

- `quality/cookbook_stone.py` — `build_s14_wet_river_stone` retune (two-scale dome, roughness
  ceiling, flatten curvature).
- `quality/cookbook_metal.py` — `build_m06_car_paint` orange-peel normal addition.
- `src/mm_mcp/preview.py` — optional `heightmap_path`/`heightmap_scale` kwargs on `render_preview`
  (and `render_preview_sweep` if trivial), mirroring the existing `clearcoat` kwargs exactly.
- `src/mm_mcp/preview_project/preview.gd` — parse the new args in `_make_material`; set
  `heightmap_enabled`/`heightmap_texture`/`heightmap_scale`/`heightmap_deep_parallax` only when a
  heightmap path is given.
- `tests/test_preview.py` — command-construction tests for the new kwargs (same shape as the
  existing clearcoat tests at lines 27-39).
- One new or retrofitted cookbook material (`cookbook/masonry/s09_ashlar_wall.ptex` or similar) +
  its card.
- `docs/images/cookbook-contact-sheet.png` — regen after both threads land.
- `HANDOFF.md` / `STATUS.md` — wrap-up.

## Logged, not scoped this session

Grayson raised a cookbook curation idea mid-conversation ("at some point," not a request to act
now): the gallery has grown enough that some entries may not be pulling weight — named
candidates: `hazard stripe` (possible cut), `circuit board` (doesn't read as circuit board),
and stone-category overlap (`dry_earth`-family entries — dry stone wall, flagstone, cobblestone —
feel similar; river pebbles "don't actually look like river pebbles"). This is a curation/teardown
question about the *existing* 74-material set, not new authoring — it belongs in its own session
(the `teardown` skill's lens, or a dedicated curation pass) once Grayson is ready to commit to it,
not folded into this iteration cycle. Recorded in `HANDOFF.md`'s open questions.

## Risks / heads-up

- Standing render gotchas apply: one Godot at a time; `render()`/`render_preview` need an
  **absolute** outdir; `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` to recover a
  hang; never drive a render from `python -c`.
- s14/m06 are visual-approval tasks — a subagent cannot reach Grayson; every authoring task ends
  by rendering and stopping, controller does `SendUserFile` + waits for the real reply.
- The two-scale port into s14 is closely modeled on s06's own solution — read
  `build_s06_river_pebbles`'s full docstring and node chain before touching s14, the registration
  lesson there is exactly the trap to avoid here too.
- Do not let Thread B's `depth_tex` wiring anywhere near `s07_cobblestone` or any other
  front-page-approved material without explicit Grayson sign-off — those are locked references
  for the "don't globally flip normals" verification rule; touching one muddies that reference.
