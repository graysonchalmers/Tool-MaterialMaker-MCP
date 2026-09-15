# Reflections — Design Spec

_Date: 2026-09-14 · Status: approved, ready for plan · Cycle: reflections (emission is a separate later cycle)_

## Problem

The 3D preview rig already uses `ORMMaterial3D` with sky-source reflections, so metallic
surfaces *should* reflect the environment. They don't read as reflective. A calibration
render of the two already-metallic cookbook materials (`m02_brushed_aluminum`,
`m04_scratched_steel`) on the current rig confirmed the cause: the procedural sky is flat,
low-contrast gray with no bright region, and the scene is dark, so even fairly smooth metal
shows only a dim gray smear — there is nothing bright to reflect. **The environment is the
lever, not the per-material authoring.**

## Goal

Metallic (and specular dielectric) surfaces show a *readable* environment reflection in the
preview rig, without altering the lighting on the 71 existing matte materials — especially the
8 front-page materials already visual-approved.

## Non-goals (explicitly dropped, YAGNI)

- **A separate per-material "reflection strength" knob.** In PBR, reflection *is*
  `metallic` + `roughness`, already authorable per material via the MM material node's scalar
  params (`metallic`, `roughness`) and texture ports (`metallic_tex`, `roughness_tex`). A
  parallel knob would be redundant.
- **A `ReflectionProbe`.** Four gray-ish objects on a gray ground reflecting each other adds
  gray blobs, not recognizable chrome structure. Godot 4 sky reflection is already a filtered
  radiance cubemap with roughness-driven mip selection, so "crisp" is available once the sky
  has content. An unbaked probe on a single captured frame is the black-lathe class of bug.
- **Emission / lava.** Separate later cycle (own design + plan).

## Design

### 1. Rig: decouple ambient from reflection (`src/mm_mcp/preview_project/preview.gd`)

Today both `env.ambient_light_source = AMBIENT_SOURCE_SKY` and
`env.reflected_light_source = REFLECTION_SOURCE_SKY` read the same procedural sky. Enriching
the sky for reflection would also change ambient on every material. Decouple:

- Set `env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR` and
  `env.ambient_light_color` / `ambient_light_energy` to an explicit value **matched to what the
  current sky-derived ambient produces**, so matte lighting is unchanged *by construction*.
- Keep `env.reflected_light_source = REFLECTION_SOURCE_SKY`.
- Enrich the reflection sky only: raise `sky_energy_multiplier` and increase
  sky-top/horizon/ground contrast (and/or a visible bright band) so metallic surfaces get
  bright/dark structure to reflect. Tune constants against a live render.
- **Verify the enum split behaves**: after the change, ambient must be driven by the color and
  reflection by the sky. Confirm in Godot 4.7 (a render proves it via the no-regress gate).

The rig's key/rim/fill lights and shadows are unchanged.

### 2. Authoring (`quality/author.py` + `cookbook/`)

Span metallic **and** dielectric — do not ship two chromes:

- **Polished metal** — low-roughness chrome/polished-steel. Pure metallic case (`metallic`≈1,
  low `roughness`). New cookbook id under `metal/` (e.g. `m05_polished_chrome`).
- **Wet dark stone** — a *dielectric* reflecting via specular, not metallic (`metallic`≈0, very
  low `roughness`, dark albedo, wet sheen). Exercises a different physical path and is distinct
  from existing m01–m04. New id (category `stone/`, e.g. `s14_wet_river_stone`, or clone an
  existing stone base and drive roughness low + darken).

Follow the established authoring workflow (clone a base with a working normal chain; role-name
nodes; per-material card with generated node table; `promote_cookbook --check` baseline). Node
count wording in README recomputes from the tree — change the tree, then the number.

### 3. Gate — objective, not eyeball

- **No-regress (the load-bearing gate):** pixel-compare 3–4 matte materials (e.g.
  `s01`-class cobblestone, `f07_herringbone_tweed`, `t02_fresh_snow`) rendered before vs after
  the decouple. They must come back essentially identical (within a small tolerance). This
  *proves* the ambient decoupling actually isolated matte lighting. A scratch/quality helper
  that renders a fixed set to two dirs and diffs them; reuse `render_tracked`'s compare logic
  if it fits.
- **Reflection reads:** re-render `m04_scratched_steel` + the two new materials on the new rig;
  the new polished metal must show a recognizable reflection (the before-shot is the calibration
  render already captured this session).
- **Showcase:** optionally add one reflective material to the front-page gallery via
  `quality/_make_showcase.py`; regen only affected stills (`still`/`hero`). Not required to
  land the cycle — gallery curation is Grayson's call.
- Full suite green (README counts, cookbook naming/card-table gates, package suite).

## Files touched

- `src/mm_mcp/preview_project/preview.gd` — ambient/reflection decouple + sky enrich.
- `src/mm_mcp/preview.py` — only if an ambient/sky constant needs surfacing as a param
  (default: none; keep it in the rig).
- `quality/author.py`, `cookbook/metal/…`, `cookbook/stone/…` — two new materials + cards.
- `cookbook/README.md` / any count-gated wording — recomputed from the tree.
- Possibly a small no-regress render/diff helper under `quality/` or `scratchpad/`.

## Risks / heads-up

- Standing render gotchas apply: one Godot at a time; `render()` needs an **absolute** outdir;
  `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (double slashes in Git Bash) to
  recover a hang; a worktree needs its own `.env` or the catalog silently fails.
- The ambient-color match is the crux. If `AMBIENT_SOURCE_COLOR` can't reproduce the current
  sky ambient closely, the no-regress gate will catch it — retune the color, don't ship drift.
- New showcase stills (if added) are lit `render_preview` renders needing regen; flat-albedo
  cookbook thumbnails are not.

## Parked for the emission cycle (no work now)

- Confirm whether "Godot 4 Standard" export writes `_emission.png` unconditionally or only when
  `emission_tex` is connected — decides whether `render.py` must tolerate its absence.
- Emission subjects when we get there: lava (dark crust + glowing molten veins) + one more
  (heated metal / glowing runes / bioluminescence).

---

## Cycle expansion (2026-09-15, Grayson request mid-execution)

After the sun-disc reflection baseline (Task 3) landed and was approved, Grayson asked for
more reflective character: grazing-angle "car paint" Fresnel, and "proper ray traced
reflections". Honest scoping:

- **True path-traced RT is out of scope.** The Godot headless preview is not a path tracer;
  real RT would mean a different renderer (Blender Cycles etc.), a separate track. Not built.
- **SSR (screen-space reflections) IS the practical closest** and is added. Forward+ confirmed
  in `preview_project/project.godot`.
- **Clearcoat is preview-only.** MM's material node has no clearcoat channel (albedo/metallic/
  roughness/emission/normal/ao/depth/opacity/sss) and the Godot export writes no clearcoat map,
  so a Godot clearcoat lobe cannot round-trip. Grayson chose **both**: deliver the grazing look
  through a *real* low-roughness colored-metallic car-paint material (exports faithfully) AND
  add an **opt-in, default-off** preview clearcoat param for the flashy showcase look, labeled
  preview-only.

### Added work

- **SSR (rig):** `Environment.ssr_enabled` + tuned params. Gate-check: SSR reflects on-screen
  geometry into surfaces, roughness-weighted; matte materials must stay within the no-regress
  tolerance (≤3). If SSR trips matte, tune fade/steps or accept with Grayson's eye.
- **Clearcoat preview param:** add optional `clearcoat` (and `clearcoat_roughness`) to
  `render_preview`/`render_preview_sweep` (`preview.py`) → `preview.gd` → `ORMMaterial3D`
  clearcoat. **Default 0.0**, so every existing render and the matte gate are unaffected by
  construction. Set >0 only for a car-paint showcase render. Verify the exact Godot 4.7 clearcoat
  API (`clearcoat` float + `clearcoat_roughness`; enable flag if the version needs one).
- **Car-paint material (authoring):** a real low-roughness colored-metallic material (e.g.
  `m06_car_paint` under `metal/`, or a `plastics`/`scifi` home if a flake look fits better) whose
  grazing Fresnel is genuine and exports. Optionally rendered with the preview clearcoat on for
  the showcase.

Non-goal reaffirmed: true path-traced RT (different renderer). Emission still a later cycle.
