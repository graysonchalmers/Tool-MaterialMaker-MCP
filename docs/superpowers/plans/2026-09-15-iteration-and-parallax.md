# Material Iteration + Deep Parallax Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close out Grayson's s14/m06 iteration feedback from the reflections cycle, and
separately prototype Godot's Deep Parallax (parallax occlusion mapping) as a real, round-trip
cookbook feature — not a preview-only garnish.

**Architecture:** Two independent threads sharing one cycle. Thread A retunes two already-merged
cookbook materials in place (no rig changes). Thread B adds one opt-in, default-off kwarg pair to
the preview rig (mirroring the existing `clearcoat` pattern exactly, so every existing render is
byte-identical by construction) and authors one cookbook material that connects its existing
height signal to Material Maker's long-unused `depth_tex` input — which MM's own Godot 4 export
target already turns into a native, round-trip-safe `heightmap_enabled`/`heightmap_deep_parallax`
material, verified by reading the pristine MM checkout directly this session.

**Tech Stack:** Python 3.13, Godot 4.7.1 headless (Material Maker checkout), Pillow. Material
graphs authored via `quality/cookbook_*.py` + `quality/author_helpers.py`, promoted with
`quality/promote_cookbook.py`.

**Spec:** `docs/superpowers/specs/2026-09-15-iteration-and-parallax-design.md`

## Global Constraints

- Shell is PowerShell 5.1: sequence with `;`, `Push-Location`/`Pop-Location`, `& "C:\path\tool.exe"`. `&&` is a parse error. (The Bash tool accepts `&&`; reformat before handing Grayson a command.)
- Python: `C:\Program Files\Python313\python.exe`. Godot: `C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64.exe`.
- **Rendering:** one Godot process at a time; `render()`/`render_preview` need an **absolute** outdir (a relative one idles to the 180s timeout with an empty log); never drive a render from `python -c` (use a script file); recover a hang with `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (double slashes in Git Bash).
- Never type material/category counts into README by hand; they recompute from the tree (`tests/test_readme_counts.py`). Change the tree, then the number.
- New/modified cookbook materials must: be built by a `build_<id>(catalog) -> str` in the right `quality/cookbook_<category>.py`, registered in that file's `BUILDERS` dict, have role-named nodes (`tests/test_cookbook_naming_gate.py`), and promote cleanly (`promote_cookbook --check`). Card tables are generated, never hand-edited (`tests/test_cookbook_card_table_gate.py`).
- Gate rule: a task is done only when its objective gate is green AND (for a visual task) Grayson has approved the render. A subagent has no chat channel to Grayson: an authoring/visual task ends by rendering and STOPPING; the controller sends the render via SendUserFile and waits for Grayson's real reply before the task is marked done.
- Do not touch `s07_cobblestone` or any other front-page-approved gallery material as part of this plan — they are locked visual references.

---

### Task 1: `s14_wet_river_stone` — two-scale pebbles, top curvature, face reflection

Applies all three of Grayson's s14 complaints in one authoring pass (one render cycle proves all
three together, since they interact: the two-scale mix changes which pixels count as "top" vs
"crevice", so retuning roughness before the size variation lands would need re-tuning anyway).

**Files:**
- Modify: `quality/cookbook_stone.py:1342-1496` (`build_s14_wet_river_stone`)

**Interfaces:**
- Consumes: `quality.author_helpers` (`load_example`, `set_param`, `set_gradient`, `rewire`,
  `drop_conn`, `add_node`, `_grad`, `group_into_subgraph`, `rename_nodes`, `save_variant`);
  `build_catalog(cfg.nodes_dir)`. Reference implementation for the two-scale pattern:
  `build_s06_river_pebbles` in the same file (lines 347-608), specifically its `voronoi_fine`/
  `dome_curve_f`/`dome_flatten_f`/`dome_smooth_f`/`dome_fine_low`/`dome_mix`/`sel_fine`/
  `colorize_fine`/`blend_layer_color` chain (lines 467-490).
- Produces: cookbook entry `stone/s14_wet_river_stone` (same id, retuned graph — this is an
  in-place edit, not a new id).

- [ ] **Step 1: Port the two-scale dome mix (size variation)**

  After the existing single-scale dome chain (`dome_curve`/`dome_flatten`/`dome_smooth`, s14 lines
  1404-1413), add a second, finer voronoi with its own identical coin chain, nestled lower and
  MAX-composited — the exact s06 pattern, renamed for s14:

  ```python
  add_node(g, "voronoi_fine", "voronoi",
           {"scale_x": 18, "scale_y": 18, "randomness": 1})
  add_node(g, "dome_curve_f", "math", {"op": 16, "default_in2": 2.6, "clamp": True})
  add_node(g, "dome_flatten_f", "math", {"op": 2, "default_in2": 1.5, "clamp": True})
  add_node(g, "dome_smooth_f", "math", {"op": 20, "clamp": True})
  add_node(g, "dome_fine_low", "math", {"op": 2, "default_in2": 0.65})   # nestle lower
  add_node(g, "dome_mix", "math", {"op": 14})                            # 14 = max(coarse, fine)
  add_node(g, "sel_fine", "math", {"op": 15})                            # 15 = A<B (coarse < fine)
  g["connections"] += [
      {"from": "voronoi_fine", "from_port": 0, "to": "dome_curve_f", "to_port": 0},
      {"from": "dome_curve_f", "from_port": 0, "to": "dome_flatten_f", "to_port": 0},
      {"from": "dome_flatten_f", "from_port": 0, "to": "dome_smooth_f", "to_port": 0},
      {"from": "dome_smooth_f", "from_port": 0, "to": "dome_fine_low", "to_port": 0},
      {"from": "dome_smooth", "from_port": 0, "to": "dome_mix", "to_port": 0},
      {"from": "dome_fine_low", "from_port": 0, "to": "dome_mix", "to_port": 1},
      {"from": "dome_smooth", "from_port": 0, "to": "sel_fine", "to_port": 0},
      {"from": "dome_fine_low", "from_port": 0, "to": "sel_fine", "to_port": 1},
  ]
  ```

  Rewire the normal to read the MIXED height instead of the single-scale `dome_smooth`:
  `rewire(g, "normal_map_0", 0, "dome_mix", 0)` (was `dome_smooth`).

- [ ] **Step 2: Registration — the fine layer needs its own color AND roughness, not just height**

  Per s06's own documented lesson ("the audit is BLIND to the fine layer needing its own colour"):
  add a fine-scale color pass and composite by the SAME `sel_fine` selection the height mix uses,
  so small stones aren't colorless bumps inheriting the big cell's tone:

  ```python
  add_node(g, "colorize_fine", "colorize", {"gradient": _grad([
      (0.0,  0.05, 0.05, 0.05), (0.28, 0.10, 0.08, 0.07), (0.52, 0.14, 0.13, 0.12),
      (0.74, 0.09, 0.10, 0.11), (1.0,  0.06, 0.05, 0.05),
  ])})   # same wet-stone palette as colorize_0
  add_node(g, "blend_layer_color", "blend", {"blend_type": 0, "amount": 1})
  g["connections"] += [
      {"from": "voronoi_fine", "from_port": 2, "to": "colorize_fine", "to_port": 0},
      {"from": "colorize_0", "from_port": 0, "to": "blend_layer_color", "to_port": 1},
      {"from": "colorize_fine", "from_port": 0, "to": "blend_layer_color", "to_port": 0},
      {"from": "sel_fine", "from_port": 0, "to": "blend_layer_color", "to_port": 2},
  ]
  rewire(g, "Material", 0, "blend_layer_color", 0)   # albedo <- two-scale color mix
  ```

  Same treatment for roughness: `colorize_2` (WetRoughness) and `colorize_dry` (DryRoughness)
  currently read `dome_smooth` directly — rewire both to `dome_mix` instead so the fine stones'
  crevices/tops get correctly masked too:
  `rewire(g, "colorize_2", 0, "dome_mix", 0)`; `rewire(g, "colorize_dry", 0, "dome_mix", 0)`.

- [ ] **Step 3: Top curvature — reduce the flatten**

  On BOTH dome chains (coarse `dome_flatten` and the new `dome_flatten_f`), lower
  `default_in2` from `1.5` toward `1.0` (less plateau, more of the underlying cos-bell curvature
  survives): `set_param(g, "dome_flatten", "default_in2", 1.0)`;
  `set_param(g, "dome_flatten_f", "default_in2", 1.0)`. Tune against the render in Step 5 — this
  is a starting point, not a locked value.

- [ ] **Step 4: Face reflection — lower the roughness ceiling so tops keep partial sheen**

  Retune the WET/DRY roughness gradients' TOP-END stop (currently `0.35`/`0.60`) down so tops read
  as semi-wet rather than fully matte, while keeping crevices the glossiest point:

  ```python
  set_gradient(g, "colorize_2", [        # WetRoughness: crevice pools, tops now semi-wet
      (0.0,  0.08, 0.08, 0.08),
      (0.35, 0.14, 0.14, 0.14),
      (1.0,  0.20, 0.20, 0.20),          # was 0.35
  ])
  set_gradient(g, "colorize_dry", [      # DryRoughness: mostly dry, tops still catch some sheen
      (0.0,  0.20, 0.20, 0.20),          # was 0.30
      (0.35, 0.30, 0.30, 0.30),          # was 0.42
      (1.0,  0.38, 0.38, 0.38),          # was 0.60
  ])
  ```

  These are starting points — the objective gate can't judge "looks wet," only Grayson's eye can;
  tune against the render in Step 5.

- [ ] **Step 5: Update subgraph grouping + names, then render — STOP for approval**

  Add `voronoi_fine`, `dome_curve_f`, `dome_flatten_f`, `dome_smooth_f`, `dome_fine_low`,
  `dome_mix`, `sel_fine`, `colorize_fine`, `blend_layer_color` into the existing `stone_profile`
  group (mirroring s06's grouping at lines 552-560) instead of `pebble_pattern`, and extend the
  `rename_nodes` call with s06-equivalent labels (`SmallStoneCells`, `SmallDomeCurve`, etc — see
  s06's `rename_nodes` dict at lines 592-603 for the exact label set to reuse). Run:
  `& "C:\Program Files\Python313\python.exe" -m quality.cookbook_stone s14_wet_river_stone`
  then render the 3D preview to a scratch dir (script file, one Godot). Subagent stops.

- [ ] **Step 6: Controller — send render, get approval; iterate**

  Controller sends the preview via SendUserFile, waits for Grayson. Iterate Steps 1-5 until
  approved — the size variation, curvature, and roughness ceiling all interact, so expect at
  least one round of joint retuning.

- [ ] **Step 7: Objective gates green**

  Run: `& "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook cookbook-stone ; & "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook --check ; & "C:\Program Files\Python313\python.exe" -m pytest tests/test_cookbook_naming_gate.py tests/test_cookbook_card_table_gate.py -q`
  Expected: all pass. `git checkout --` any unrelated `.md` line-ending churn.

- [ ] **Step 8: Commit**

  ```bash
  git add quality/cookbook_stone.py cookbook/stone/s14_wet_river_stone.ptex cookbook/stone/s14_wet_river_stone.md
  git commit -m "feat(cookbook): s14 wet stone — two-scale pebbles, curved tops, semi-wet reflection (Grayson-approved)"
  ```

---

### Task 2: `m06_car_paint` — orange-peel surface detail

**Files:**
- Modify: `quality/cookbook_metal.py:314-382` (`build_m06_car_paint`)

**Interfaces:**
- Consumes: `quality.author_helpers` (`add_node`, `_grad`, `set_param`, `group_into_subgraph`,
  `rename_nodes`); existing `_M06_NAMES` dict (line 303).
- Produces: cookbook entry `metal/m06_car_paint` (same id, retuned graph).

- [ ] **Step 1: Add a coarser second noise for the orange-peel wave**

  `MicroNoise` (`perlin_0`, scale 8x8) already drives albedo/roughness/flake fan-out — do not
  retune it (deep base colors are approved). Add an independent, coarser-frequency noise and
  combine it with the existing normal input via a `math` add, the same technique s06 used for
  `grain_scaled` + `height_relief`:

  ```python
  add_node(g, "orange_peel", "perlin", {"scale_x": 14, "scale_y": 14, "iterations": 2})
  add_node(g, "peel_scaled", "math", {"op": 2, "default_in2": 0.6})   # A*B: weight the wave
  add_node(g, "normal_height", "math", {"op": 0})                     # A+B: micro + orange peel
  g["connections"] += [
      {"from": "orange_peel", "from_port": 0, "to": "peel_scaled", "to_port": 0},
      {"from": "perlin_0", "from_port": 0, "to": "normal_height", "to_port": 0},
      {"from": "peel_scaled", "from_port": 0, "to": "normal_height", "to_port": 1},
  ]
  ```

  Rewire `normal_map_0`'s input from `perlin_0` to `normal_height`:
  `rewire(g, "normal_map_0", 0, "normal_height", 0)` (import `rewire` alongside the file's
  existing `author_helpers` import — it is not currently imported in `cookbook_metal.py`, check
  the import line at the top of the file and add it).

- [ ] **Step 2: Raise `normal_amount` enough to read, without going rough**

  `set_param(g, "normal_map_0", "param1", 0.10)` (was `0.04`, set inside
  `_from_scratch_noise_material`'s call — override it after construction with `set_param` rather
  than editing the shared helper call, since chrome/other from-scratch materials still want
  `0.04`). This is a starting point for the render loop in Step 4, not a locked value — Grayson's
  "missing surface detail" complaint is the gate, an objective test can't judge it.

- [ ] **Step 3: Fold the new nodes into the existing subgraph group**

  Add `orange_peel`, `peel_scaled`, `normal_height` to the existing `car_paint_finish` group
  member list (line 371-372) and extend `_M06_NAMES` (line 303) with
  `"orange_peel": "OrangePeelNoise"`, `"peel_scaled": "OrangePeelWeighted"`,
  `"normal_height": "NormalHeightMix"`.

- [ ] **Step 4: Render both plain and clearcoat variants — STOP for approval**

  Run: `& "C:\Program Files\Python313\python.exe" -m quality.cookbook_metal m06_car_paint`
  Render `m06_car_paint`'s 3D preview twice (script file, one Godot at a time): once at
  `clearcoat=0.0` (the real export-faithful look), once at `clearcoat=0.6` (the showcase demo,
  matching the reflections cycle's own approval pattern). Subagent stops.

- [ ] **Step 5: Controller — send both renders, get approval; iterate**

  Controller SendUserFile + wait for Grayson. Iterate Steps 1-2 (peel scale/weight, normal
  strength) until he confirms the flatness complaint is resolved.

- [ ] **Step 6: Objective gates green**

  Run: `& "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook cookbook-metal ; & "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook --check ; & "C:\Program Files\Python313\python.exe" -m pytest tests/test_cookbook_naming_gate.py tests/test_cookbook_card_table_gate.py -q`
  Expected: all pass.

- [ ] **Step 7: Commit**

  ```bash
  git add quality/cookbook_metal.py cookbook/metal/m06_car_paint.ptex cookbook/metal/m06_car_paint.md
  git commit -m "feat(cookbook): m06 car paint — orange-peel surface detail (Grayson-approved)"
  ```

---

### Task 3: Deep Parallax — opt-in heightmap support in the preview rig

Mirrors the existing `clearcoat` param exactly: default off, a true no-op at that default, so
every existing render and the `preview_regress` no-regress gate are unaffected by construction.

**Files:**
- Modify: `src/mm_mcp/preview.py` (`_build_command`, `render_preview` — add
  `heightmap_path: str | None = None`, `heightmap_scale: float = 0.05`)
- Modify: `src/mm_mcp/preview_project/preview.gd` (parse `--heightmap=`/`--heightmap-scale=` in
  `_ready()`; `_make_material` sets `heightmap_enabled`/`heightmap_texture`/`heightmap_scale`/
  `heightmap_deep_parallax`/`heightmap_min_layers`/`heightmap_max_layers` only when a path is given)
- Test: `tests/test_preview.py` (command-construction assertions, same shape as the existing
  `test_build_command_omits_clearcoat_when_zero`/`test_build_command_includes_clearcoat_when_positive`
  at lines 27-39)

**Interfaces:**
- Consumes: existing `render_preview(albedo_path, normal_path, orm_path, outdir=, basename=,
  tile=, clearcoat=0.0, clearcoat_roughness=0.5, cfg=) -> PreviewResult`.
- Produces: `render_preview(..., heightmap_path: str | None = None, heightmap_scale: float = 0.05)`
  — `heightmap_path=None` is a true no-op (no `--heightmap` arg appended at all, matching how
  `clearcoat<=0.0` omits its args today).

- [ ] **Step 1: Write the failing tests**

  In `tests/test_preview.py`, add:

  ```python
  def test_build_command_omits_heightmap_when_none():
      cmd = _build_command(cfg, "/a/albedo.png", "/a/normal.png", "/a/orm.png",
                            "/out/x_preview.png", tile=1.0, heightmap_path=None)
      assert not any(c.startswith("--heightmap") for c in cmd)


  def test_build_command_includes_heightmap_when_given():
      cmd = _build_command(cfg, "/a/albedo.png", "/a/normal.png", "/a/orm.png",
                            "/out/x_preview.png", tile=1.0,
                            heightmap_path="/a/heightmap.png", heightmap_scale=0.08)
      assert "--heightmap=/a/heightmap.png" in cmd
      assert "--heightmap-scale=0.08" in cmd
  ```

- [ ] **Step 2: Run to verify it fails**

  Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_preview.py -k heightmap -v`
  Expected: FAIL — `_build_command() got an unexpected keyword argument 'heightmap_path'`.

- [ ] **Step 3: Implement in `preview.py`**

  ```python
  def _build_command(cfg: Config, albedo_path: str, normal_path: str, orm_path: str,
                      out_path: str, tile: float, clearcoat: float = 0.0,
                      clearcoat_roughness: float = 0.5, heightmap_path: str | None = None,
                      heightmap_scale: float = 0.05) -> list[str]:
      cmd = [
          cfg.console_binary, "--path", _PREVIEW_PROJECT, "--",
          f"--albedo={albedo_path}", f"--normal={normal_path}",
          f"--orm={orm_path}", f"--out={out_path}", f"--tile={tile}",
      ]
      if clearcoat > 0:
          cmd.append(f"--clearcoat={clearcoat}")
          cmd.append(f"--clearcoat-roughness={clearcoat_roughness}")
      if heightmap_path:
          cmd.append(f"--heightmap={heightmap_path}")
          cmd.append(f"--heightmap-scale={heightmap_scale}")
      return cmd
  ```

  Thread the same two kwargs through `render_preview` (add `heightmap_path: str | None = None,
  heightmap_scale: float = 0.05` to its signature, resolve `heightmap_path` to an absolute path
  with `os.path.abspath` when given — same treatment as `albedo_path`/`normal_path`/`orm_path` —
  and pass both through to `_build_command`). Do not add an `isfile` check that hard-fails when
  `heightmap_path` is given but missing beyond what the existing albedo/normal/orm checks already
  do; a missing optional file should surface as a Godot-side load failure, not a Python-side one,
  same tier of strictness as an absent clearcoat.

- [ ] **Step 4: Implement in `preview.gd`**

  In `_ready()`, alongside the existing clearcoat arg parsing (lines 58-68):

  ```gdscript
      var heightmap_path := ""
      if args.has("heightmap"):
          heightmap_path = args["heightmap"]
      var heightmap_scale := 0.05
      if args.has("heightmap-scale"):
          heightmap_scale = args["heightmap-scale"].to_float()
  ```

  Change the `_make_material` call site to pass these through, and update `_make_material`'s
  signature and body:

  ```gdscript
  func _make_material(albedo_tex: ImageTexture, normal_tex: ImageTexture,
          orm_tex: ImageTexture, tile: float, clearcoat: float = 0.0,
          clearcoat_roughness: float = 0.5, heightmap_path: String = "",
          heightmap_scale: float = 0.05) -> ORMMaterial3D:
      var mat := ORMMaterial3D.new()
      mat.albedo_texture = albedo_tex
      mat.normal_enabled = true
      mat.normal_texture = normal_tex
      mat.orm_texture = orm_tex
      mat.uv1_scale = Vector3(tile, tile, 1)
      mat.texture_repeat = true
      if clearcoat > 0.0:
          mat.clearcoat_enabled = true
          mat.clearcoat = clearcoat
          mat.clearcoat_roughness = clearcoat_roughness
      # Opt-in Deep Parallax (Godot's native parallax occlusion mapping) -- see
      # docs/superpowers/specs/2026-09-15-iteration-and-parallax-design.md. Mirrors
      # Material Maker's own "Godot/Godot 4 Standard" export target values
      # (heightmap_min_layers/max_layers = 8/32) so the preview matches what a
      # real exported .tres would show. Empty path is a true no-op.
      if heightmap_path != "":
          var height_tex := _load_tex(heightmap_path)
          if height_tex != null:
              mat.heightmap_enabled = true
              mat.heightmap_texture = height_tex
              mat.heightmap_scale = heightmap_scale
              mat.heightmap_deep_parallax = true
              mat.heightmap_min_layers = 8
              mat.heightmap_max_layers = 32
      return mat
  ```

  Update the one call site (`_make_material(albedo_tex, normal_tex, orm_tex, tile, clearcoat,
  clearcoat_roughness)`) to pass `heightmap_path, heightmap_scale` through.

- [ ] **Step 5: Run tests to verify they pass**

  Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_preview.py -v`
  Expected: PASS (all, including the two new heightmap tests and the existing clearcoat/tile ones
  unaffected).

- [ ] **Step 6: No-regress gate — default-off is a true no-op**

  Run: `& "C:\Program Files\Python313\python.exe" -m quality.preview_regress --out scratchpad/parallax-noop --compare scratchpad/reflect-baseline`
  Expected: `4 preview(s), 0 problem(s)` (the matte set renders with `heightmap_path` defaulting
  to none — must be byte-for-byte the same behavior as before this task).

- [ ] **Step 7: Empirical check — does triplanar + heightmap actually compose in Godot 4.7?**

  This is a genuine unknown flagged in the spec, not assumed. Render `s07_cobblestone` (an
  APPROVED reference material, read-only here — do not modify it) with its own `_heightmap.png`
  IF it has one (it likely does not yet, since no cookbook material connects `depth_tex` before
  Task 4 lands) — if no heightmap PNG exists yet for any material, generate a throwaway synthetic
  one for this check only (e.g. a Pillow-generated radial gradient PNG in `scratchpad/`, never
  committed) and pass it via `heightmap_path` at an exaggerated `heightmap_scale` (e.g. `0.3`) on
  any existing material, purely to prove the Godot-side plumbing moves pixels. Render at an
  oblique angle (the rig's existing camera is already fairly oblique — `fov 36`,
  `cam.position = Vector3(0, 1.4, 6.5)`) and zoom into the result. Read it:
  - If a visible parallax offset/depth appears: the triplanar rig supports it, proceed to Task 4
    using the shared rig objects.
  - If nothing visible even at an exaggerated scale: STOP and report to the controller — the
    spec's fallback (a small non-triplanar plane object added specifically for this demo) needs a
    scoping decision before Task 4 proceeds, do not silently build it.

- [ ] **Step 8: Commit**

  ```bash
  git add src/mm_mcp/preview.py src/mm_mcp/preview_project/preview.gd tests/test_preview.py
  git commit -m "feat(preview): opt-in Deep Parallax heightmap param (default off)"
  ```

---

### Task 4: Deep Parallax cookbook material — connect `depth_tex`

> **Amended 2026-09-15 after Task 3 landed.** Task 3's Step 7 empirical check came back
> definitively negative: Godot 4.7 refuses to combine heightmap/parallax with triplanar UV
> mapping (engine warning: "Height mapping is not supported on triplanar materials. Ignoring
> height mapping in favor of triplanar mapping."; confirmed by a byte-identical render with vs
> without the heightmap param). This is the spec's own named contingency ("Open technical risk —
> triplanar + heightmap composition") now triggered for real.
>
> **Amended again 2026-09-15 after Grayson's visual feedback on the first Step 0 attempt.** The
> first version of Step 0 (below, superseded — see `f1ce303`/`9d396fe` in git history) added a new
> floating demo plane. Grayson found the effect nearly invisible on it and explicitly asked to see
> it on the SAME shaped objects already in the rig, not a new one. Redesigned: instead of a new
> plane, swap the existing SPHERE's material to a non-triplanar one when a heightmap path is
> given (leaving cube/rook/ground on the shared triplanar material, unaffected, for visual
> context). The sphere is a stock `SphereMesh` with real per-vertex UV1 and auto-generated
> tangents — the same prerequisite the plane needed, but on an object already in every render, and
> a smaller diff than adding a new mesh. A sphere's continuously-curving surface also means a
> single static shot already spans a gradient of viewing angles (near-tangent at the limb, face-on
> at the center), so the effect should read clearly near the sphere's edge without needing the
> plane's specific tilt/positioning tuning.

**Files:**
- Modify: `src/mm_mcp/preview_project/preview.gd` (Step 0: swap the sphere to a non-triplanar
  material when a heightmap path is given — superseded the original plane-based approach)
- Modify: `quality/cookbook_stone.py` (add `build_s09_ashlar_wall`'s `depth_tex` wiring — this is
  an in-place retune of an EXISTING, already-shipped material, not a new id; `s09_ashlar_wall` is
  not on the front-page gallery, so this carries no regression risk to an approved visual
  reference) — OR, if Task 3 Step 7's empirical check demands a coarser-relief candidate instead,
  substitute the equivalent block in whichever category's builder holds the chosen material.
- Test/verification: a real `render()` call + a string check on the produced `.tres`.

**Interfaces:**
- Consumes: `Material.to_port 6` = `depth_tex` (confirmed by cross-referencing
  `_from_scratch_noise_material`'s own wiring, where `to_port 2` = roughness and `to_port 4` =
  normal, both matching `material.mmg`'s declared input order: albedo=0, metallic=1, roughness=2,
  emission=3, normal=4, ao=5, depth=6, opacity=7, sss=8). `rewire(g, "Material", 6, <source_node>,
  <source_port>)`.
- Produces: the chosen material's exported `.tres` gains `heightmap_enabled = true`,
  `heightmap_deep_parallax = true`, `heightmap_texture`, plus a `<name>_heightmap.png` file — a
  real round-trip Deep Parallax export, not a preview-only effect.

- [ ] **Step 0 (redesigned): swap the SPHERE's material to non-triplanar when a heightmap is given**

  **Superseded the original plane-based Step 0** (git history: `f1ce303`, `9d396fe`) per Grayson's
  feedback — see the amendment note above. In `preview.gd`, right after the sphere is constructed
  (`sphere.mesh = SphereMesh.new()` ... `sphere.position = Vector3(-2.0, 0, 0)`, before
  `sphere.set_surface_override_material(0, mat)`), give it its OWN material when a heightmap path
  is given instead of the shared triplanar `mat` — same albedo/normal/orm textures, `uv1_triplanar`
  left at its default `false`. Cube/rook/ground keep using the shared `mat` unchanged. When
  `heightmap_path` is empty (every existing render, and every render of a heightmap-less
  material), `sphere_mat` is just `mat` itself — a true no-op, same discipline as Task 3's params.

  ```gdscript
  # Deep Parallax demo (opt-in): Godot 4.7 refuses to compose heightmap/parallax
  # with triplanar UV mapping (confirmed via engine warning + a byte-identical
  # render, Task 3 Step 7). The sphere is a stock SphereMesh with real,
  # non-triplanar UV1 and auto-generated tangents (unlike the hand-built
  # _rounded_box/_lathe meshes) -- the exact prerequisite parallax needs. When a
  # heightmap is given, give JUST the sphere its own non-triplanar material
  # carrying it; cube/rook/ground stay on the shared triplanar `mat`, unaffected,
  # for visual context. Empty heightmap_path is a true no-op: sphere_mat is mat.
  var sphere_mat := mat
  if heightmap_path != "":
      var height_tex := _load_tex(heightmap_path)
      if height_tex != null:
          sphere_mat = ORMMaterial3D.new()
          sphere_mat.albedo_texture = albedo_tex
          sphere_mat.normal_enabled = true
          sphere_mat.normal_texture = normal_tex
          sphere_mat.orm_texture = orm_tex
          sphere_mat.uv1_scale = Vector3(tile, tile, 1)
          sphere_mat.texture_repeat = true
          sphere_mat.heightmap_enabled = true
          sphere_mat.heightmap_texture = height_tex
          sphere_mat.heightmap_scale = heightmap_scale
          sphere_mat.heightmap_deep_parallax = true
          sphere_mat.heightmap_min_layers = 8
          sphere_mat.heightmap_max_layers = 32
          # uv1_triplanar intentionally left at its default false -- that's the point.
  ```

  Then change `sphere.set_surface_override_material(0, mat)` to
  `sphere.set_surface_override_material(0, sphere_mat)`. A sphere's continuously-curving surface
  means a single static shot already spans a gradient of viewing angles — near-tangent at the
  limb/edge (where parallax is most visible), face-on at the center (where it's least visible) —
  so render a crop/zoom on the sphere's edge region for the approval renders, not just the full
  frame at the same scale as before.

  This goes in `_ready()`, after the existing objects are added and after `_make_material`'s
  `heightmap_path`/`heightmap_scale` locals are parsed (Task 3), so it has the same texture
  paths/args already in scope — it does not need its own CLI flags.

- [x] **Step 1: Route an existing height signal into `depth_tex`** — done differently than
  drafted, see note.

  **Executed 2026-09-15, deviated from the draft below after render verification** (commit
  `26b80d7`): the draft assumed `depth_tex` was unconnected and suggested tapping `blend_2`
  directly. Investigation found `s09_ashlar_wall`'s donor (`stone_wall`) already had an
  ACCIDENTAL, undocumented connection into `Material.to_port 6` via `colorize_6` — Deep Parallax
  export was silently already working before this task touched it. A direct `blend_2` tap was
  tried and rendered WRONG POLARITY (mortar joints bulging out instead of recessing); `colorize_6`
  is the correctly-inverted signal the donor already used. Real change:
  `rewire(g, "Material", 6, "colorize_6", 0)` (repointing the existing edge, not adding a new
  one — an `append()` would have left two connections into one port) plus
  `set_param(g, "Material", "depth_scale", 0.3)`. Verified via a real `.tres` round-trip check
  (`heightmap_enabled = true`, `heightmap_deep_parallax = true`). Original draft, preserved for
  context (do NOT apply as written — it produces wrong polarity):

  ```python
  g["connections"].append(
      {"from": "blend_2", "from_port": 0, "to": "Material", "to_port": 6})
  ```

- [ ] **Step 2: Confirm `depth_scale` is sane**

  Every material node already carries a `depth_scale` parameter (default `0.5`-`1` depending on
  which helper built the graph) — this is what the Godot 4 Standard export multiplies by 25.0 into
  `heightmap_scale`. Check the chosen material's current `depth_scale` value
  (`node(g, "Material")["parameters"].get("depth_scale")`); if unset or clearly wrong for a
  masonry-scale relief, set it explicitly: `set_param(g, "Material", "depth_scale", 0.3)`
  (starting point — tune in Step 4).

- [ ] **Step 3: Rebuild, promote, and verify the REAL export produces the round-trip material**

  Run: `& "C:\Program Files\Python313\python.exe" -m quality.cookbook_stone s09_ashlar_wall ; & "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook cookbook-stone`
  Then, in a script file (never `python -c`), call `mm_mcp.render.render()` on the promoted
  `.ptex` with an absolute outdir and read back the produced `.tres` as text, asserting it
  contains `heightmap_enabled = true` and `heightmap_deep_parallax = true`, and that a
  `s09_ashlar_wall_heightmap.png` file exists in the outdir. This is the objective proof the
  round-trip actually works, independent of how it looks in the preview.

- [x] **Step 4: Render the sphere with the new heightmap param — STOP for approval** — done,
  see note (supersedes the text below, kept for history).

  ~~Using Task 3's new `render_preview(..., heightmap_path=<the _heightmap.png from Step 3>)`,
  which now (Step 0) also spawns the non-triplanar demo plane, render `s09_ashlar_wall` twice:
  once WITHOUT `heightmap_path` (the plane doesn't exist — shows only the familiar triplanar
  sphere/cube/rook, a sanity check that nothing regressed) and once WITH it (the plane appears,
  showing real Deep Parallax at its grazing angle). The comparison that matters is the plane
  itself, not a before/after of the shared triplanar objects (which structurally cannot show this
  effect, per Task 3 Step 7). Subagent stops.~~

  **Executed 2026-09-15 per the Step 0 redesign** (commit `588f842`): rendered `s09_ashlar_wall`
  WITHOUT `heightmap_path` (sphere renders on the shared triplanar `mat`, byte-identical to any
  normal render — sanity check) and WITH it at `heightmap_scale=0.3` (sphere swaps to its own
  non-triplanar material). Cropped both to the sphere's edge region for direct comparison
  (`s09_sanity_zoom.png` vs `s09_scale03_zoom.png`), plus an amplified (6x) pixel diff isolating
  the pure parallax contribution from the material-switch's own visual change. Sent to Grayson —
  see the session/ledger for his honest-disclosure caveat (most of the visible difference is the
  necessary triplanar->real-UV1 switch, not the parallax offset itself, which is real but subtle
  at this camera distance) and the open question of whether to keep or park the feature.

- [x] **Step 5: Controller — send both renders, get Grayson's approval; iterate** — decision made
  (KEEP), one more iteration round in progress, see note.

  Controller SendUserFile + wait. Iterate `depth_scale` (Step 2) and `heightmap_scale` (the
  preview-side param) until the parallax reads as real depth without obvious texture-swim
  artifacts at the rendered angle. If Grayson prefers a different candidate material entirely,
  redo Step 1 on that material instead — the wiring pattern is generic.

  **Iteration round 2 (2026-09-15), after Grayson's first reply:** he confirmed KEEP the feature,
  with two real follow-ups to fix before final sign-off — (a) the sphere's UV tile scale reuses
  the shared triplanar `tile` value, but a `SphereMesh`'s native (equirectangular) UV1 has
  completely different tiling semantics, so the crop didn't show enough repeats of the ashlar
  pattern to read clearly — needs its own, independently-tuned scale; (b) he asked to see it "in
  the sweep" — `render_preview_sweep` only rotates the key LIGHT, which cannot reveal parallax at
  all (it is camera-angle-dependent, not light-angle-dependent) — instead of building that
  (it would show nothing), add a new sweep mode that rotates the SPHERE itself across frames
  (camera/lights fixed), reusing the existing frame-loop/GIF-assembly plumbing with a new
  `sweep_kind` value rather than new infrastructure. Also clarified for Grayson directly (not a
  code change): Deep Parallax does not displace mesh geometry or change the silhouette — it is a
  per-pixel texture-sampling illusion only.

- [ ] **Step 6: Objective gates green**

  Run: `& "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook --check ; & "C:\Program Files\Python313\python.exe" -m pytest tests/test_cookbook_naming_gate.py tests/test_cookbook_card_table_gate.py tests/test_readme_counts.py -q`
  Expected: all pass.

- [ ] **Step 7: Commit**

  ```bash
  git add quality/cookbook_stone.py cookbook/stone/s09_ashlar_wall.ptex cookbook/stone/s09_ashlar_wall.md cookbook/README.md
  git commit -m "feat(cookbook): s09 ashlar wall — Deep Parallax via depth_tex (Grayson-approved)"
  ```

---

### Task 5: Full suite, contact sheet regen, wrap-up

**Files:**
- `docs/images/cookbook-contact-sheet.png` (regen).
- `HANDOFF.md`, `STATUS.md`.

- [ ] **Step 1: Run the full test suite**

  Run: `& "C:\Program Files\Python313\python.exe" -m pytest -q`
  Expected: green (fast suite). Note any pre-existing concurrent-Godot flake (the live-overlay
  round-trip test) and re-run it alone if it trips.

- [ ] **Step 2: Regenerate the contact sheet**

  Run whatever the project's existing contact-sheet regen entrypoint is (check
  `cookbook/README.md` or `quality/` for the script that produced the current 72-entry sheet — do
  not hand-build a new one). Controller sends the regenerated sheet via SendUserFile for a quick
  sanity look (not a full approval gate, just "does it look complete").

- [ ] **Step 3: Log the cookbook curation idea (do not act on it)**

  Add an open question to `HANDOFF.md`: Grayson wants to eventually trim the gallery — named
  candidates are `hazard stripe` (cut candidate), `circuit board` (doesn't read as circuit board),
  and stone-category overlap (dry stone wall / flagstone / cobblestone feel similar; river pebbles
  don't read as river pebbles). Frame it explicitly as "at some point," not scoped, and point at
  the `teardown` skill as the likely vehicle for that pass when Grayson is ready. Do not touch any
  of the named materials as part of this task.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/images/cookbook-contact-sheet.png HANDOFF.md STATUS.md
  git commit -m "docs: wrap up s14/m06 iteration + Deep Parallax prototype, log cookbook curation idea"
  ```

---

## Self-Review

**Spec coverage:**
- s14 face reflection / curvature / size variation (spec Thread A) → Task 1, all three sub-issues
  addressed with an explicit registration step mirroring s06's own documented lesson. ✓
- m06 surface detail (spec Thread A) → Task 2, orange-peel direction per Grayson's own framing,
  base colors untouched. ✓
- Contact sheet regen (spec housekeeping) → Task 5 Step 2. ✓
- Deep Parallax plumbing verified this session (spec Thread B "what already works") → documented
  in Task 4's Interfaces block, not re-derived. ✓
- Rig opt-in heightmap support (spec Thread B gap 2) → Task 3, TDD, mirrors `clearcoat` exactly,
  no-regress gate included. ✓
- Triplanar+heightmap composition risk (spec's explicit open risk) → Task 3 Step 7, empirical
  check with a named STOP condition rather than an assumed pass. ✓
- `depth_tex` cookbook material (spec Thread B gap 1) → Task 4, generic wiring pattern + objective
  `.tres` string-check gate (not just "the PNG exists"). ✓
- Non-goals (blanket depth_tex rollout, new camera mode, emission) → not built. ✓
- Cookbook curation idea (spec "logged, not scoped") → Task 5 Step 3, explicitly not acted on. ✓

**Placeholder scan:** Tasks 1/2/4's visual-tuning values (roughness ceilings, `default_in2`,
`normal_amount`, `depth_scale`/`heightmap_scale`) are given as concrete starting points, not
placeholders — each has a real number and an explicit "tune against the render" note, matching
the reflections plan's own precedent for authoring tasks (Self-Review there makes the same call).
Task 3's code is fully concrete (TDD, no visual judgment involved). Task 4's Step 1 offers a
named fallback path (a different material) rather than a vague "or something else."

**Type consistency:** `render_preview(..., heightmap_path: str | None = None, heightmap_scale:
float = 0.05)` used consistently across Task 3's Steps 1/3/4/6 and Task 4's Step 4.
`_make_material`'s new signature in Task 3 Step 4 matches the call-site update in the same step.
`Material.to_port 6` used consistently in the spec and Task 4 Steps 1/3. `dome_mix`/`sel_fine`
naming in Task 1 matches s06's own names (traceable back to the cited reference implementation),
not invented fresh.
