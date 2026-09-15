# Reflections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make metallic and specular-dielectric surfaces show a readable environment reflection in the 3D preview rig, without changing the lighting on the 71 existing matte materials.

**Architecture:** The rig (`preview.gd`) currently drives both ambient light and reflection from one procedural sky, so brightening the sky to make reflections read would silently re-light every material. Decouple: pin ambient to an explicit color matched to today's sky-derived ambient (matte lighting unchanged by construction), then enrich the reflection sky only. Prove the decouple with a pixel-diff of the 3D preview composite of matte materials before/after. Then author two reflective materials (a metallic polished chrome and a dielectric wet dark stone) that exercise the improved environment.

**Tech Stack:** Python 3.13, Godot 4.7.1 headless (Material Maker checkout), Pillow. Material graphs authored via `quality/cookbook_*.py` + `quality/author_helpers`, promoted with `quality/promote_cookbook.py`. Pixel compare via `quality/render_compare.renders_match`.

**Spec:** `docs/superpowers/specs/2026-09-14-reflections-design.md`

## Global Constraints

- Shell is PowerShell 5.1: sequence with `;`, `Push-Location`/`Pop-Location`, `& "C:\path\tool.exe"`. `&&` is a parse error. (The Bash tool accepts `&&`; reformat before handing Grayson a command.)
- Python: `C:\Program Files\Python313\python.exe`. Godot: `C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64.exe`.
- **Rendering:** one Godot process at a time; `render()`/preview need an **absolute** outdir (a relative one idles to the 180s timeout with an empty log); never drive a render from `python -c` (use a script file); recover a hang with `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (double slashes in Git Bash).
- Never type material/category counts into README by hand; they recompute from the tree (`tests/test_readme_counts.py`). Change the tree, then the number.
- New cookbook materials must: be built by a `build_<id>(catalog) -> str` in the right `quality/cookbook_<category>.py`, registered in that file's `BUILDERS` dict, have role-named nodes (`tests/test_cookbook_naming_gate.py`), and promote cleanly (`promote_cookbook --check`). Card tables are generated, never hand-edited (`tests/test_cookbook_card_table_gate.py`).
- Gate rule: a task is done only when its objective gate is green AND (for a visual task) Grayson has approved the render. A subagent has no chat channel to Grayson: an authoring/visual task ends by rendering and STOPPING; the controller sends the render via SendUserFile and waits for Grayson's real reply before the task is marked done.

---

### Task 1: No-regress gate helper + capture the pre-change baseline

The existing `quality/render_tracked.py` compares the PBR **maps** (albedo/normal/orm), which the rig change never touches — it would show zero diff and prove nothing. We need a helper that compares the **3D preview composite** (what the rig actually produces) for a fixed set of matte materials, and we must capture the "before" baseline while the rig is still unchanged.

**Files:**
- Create: `quality/preview_regress.py`
- Create: `tests/test_preview_regress.py`

**Interfaces:**
- Consumes: `mm_mcp.render.render(ptex_dict, outdir=, basename=, cfg=) -> RenderResult(.ok, .images, .error)`; `mm_mcp.preview.render_preview(albedo, normal, orm, outdir=, basename=, tile=, cfg=) -> PreviewResult(.ok, .image, .error)`; `mm_mcp.config.load_config()`; `quality.render_compare.renders_match(path_a, path_b) -> bool` and `grid_mean_abs_diff(path_a, path_b) -> float`.
- Produces: `render_matte_previews(idents: list[str], outdir: Path) -> list[str]` (renders each ident's 3D preview composite to `<outdir>/<ident>.png`, returns list of problem strings, empty on success); `compare_previews(baseline: Path, current: Path, idents: list[str]) -> list[str]` (problem strings for any ident whose composite differs beyond tolerance). Module constant `MATTE_SET = ["s07_cobblestone", "f07_herringbone_tweed", "t02_fresh_snow", "s02_gray_granite"]`.

- [ ] **Step 1: Write the failing test**

`tests/test_preview_regress.py`. Test the pure comparison logic without invoking Godot — feed it two identical PNGs (a match) and two different PNGs (a mismatch), assert `compare_previews` reports empty vs non-empty. Build the fixtures with Pillow in a `tmp_path`, laid out as `<dir>/<ident>.png`.

```python
from pathlib import Path
from PIL import Image
from quality.preview_regress import compare_previews

def _png(p: Path, color):
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), color).save(p)

def test_identical_previews_match(tmp_path):
    base, cur = tmp_path / "b", tmp_path / "c"
    _png(base / "s07_cobblestone.png", (120, 120, 120))
    _png(cur / "s07_cobblestone.png", (120, 120, 120))
    assert compare_previews(base, cur, ["s07_cobblestone"]) == []

def test_differing_previews_flagged(tmp_path):
    base, cur = tmp_path / "b", tmp_path / "c"
    _png(base / "s07_cobblestone.png", (30, 30, 30))
    _png(cur / "s07_cobblestone.png", (200, 200, 200))
    problems = compare_previews(base, cur, ["s07_cobblestone"])
    assert len(problems) == 1 and "s07_cobblestone" in problems[0]

def test_missing_current_flagged(tmp_path):
    base, cur = tmp_path / "b", tmp_path / "c"
    _png(base / "s07_cobblestone.png", (120, 120, 120))
    cur.mkdir()
    problems = compare_previews(base, cur, ["s07_cobblestone"])
    assert len(problems) == 1 and "missing" in problems[0].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_preview_regress.py -v`
Expected: FAIL — `ModuleNotFoundError: quality.preview_regress`.

- [ ] **Step 3: Write minimal implementation**

`quality/preview_regress.py`. `compare_previews` mirrors `render_tracked.compare_dirs` but on `<dir>/<ident>.png` (no per-category subdir). `render_matte_previews` mirrors `_make_showcase._render_still` (render → pick `_albedo`/`_normal`/`_orm` → `render_preview` at `tile=0.45` → copy the composite to `<outdir>/<ident>.png`). Resolve idents to `cookbook/**/<ident>.ptex`. Godot-touching imports lazy so the module imports without a render.

```python
"""Render the 3D PREVIEW COMPOSITE of a fixed matte set and pixel-compare two
runs. This is the no-regress gate for a rig (preview.gd) change: render_tracked
compares the PBR maps, which a rig change never touches, so it cannot prove a
lighting change left matte materials alone. Run as a script, never python -c;
outdir is resolved absolute before Godot sees it. One Godot at a time."""
import shutil
from pathlib import Path

from quality.render_compare import renders_match, grid_mean_abs_diff

_ROOT = Path(__file__).resolve().parent.parent
_COOKBOOK = _ROOT / "cookbook"
MATTE_SET = ["s07_cobblestone", "f07_herringbone_tweed", "t02_fresh_snow", "s02_gray_granite"]


def _resolve(ident: str) -> Path:
    hits = list(_COOKBOOK.glob(f"**/{ident}.ptex"))
    if not hits:
        raise FileNotFoundError(f"no cookbook graph for {ident!r}")
    return hits[0]


def render_matte_previews(idents, outdir: Path) -> list[str]:
    import json, tempfile
    from mm_mcp.render import render
    from mm_mcp.preview import render_preview
    from mm_mcp.config import load_config

    cfg = load_config()
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    problems = []
    for ident in idents:
        ptex = json.loads(_resolve(ident).read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp = str(Path(tmp).resolve())
            rr = render(ptex, outdir=tmp, basename=ident, cfg=cfg)
            if not rr.ok:
                problems.append(f"{ident}: render failed: {rr.error}"); continue
            try:
                albedo = next(p for p in rr.images if p.endswith("_albedo.png"))
                normal = next(p for p in rr.images if p.endswith("_normal.png"))
                orm = next(p for p in rr.images if p.endswith("_orm.png"))
            except StopIteration:
                problems.append(f"{ident}: missing albedo/normal/orm map"); continue
            pr = render_preview(albedo, normal, orm, outdir=tmp, basename=ident, tile=0.45, cfg=cfg)
            if not pr.ok:
                problems.append(f"{ident}: preview failed: {pr.error}"); continue
            shutil.copyfile(pr.image, outdir / f"{ident}.png")
    return problems


def compare_previews(baseline: Path, current: Path, idents) -> list[str]:
    baseline, current = Path(baseline), Path(current)
    problems = []
    for ident in idents:
        a, b = baseline / f"{ident}.png", current / f"{ident}.png"
        if not a.is_file():
            problems.append(f"{ident}: no baseline preview"); continue
        if not b.is_file():
            problems.append(f"{ident}: missing in current"); continue
        if not renders_match(str(a), str(b)):
            problems.append(f"{ident}: differs, mean abs diff {grid_mean_abs_diff(str(a), str(b)):.2f}")
    return problems


def main(argv) -> int:
    def _arg(flag, default=None):
        return argv[argv.index(flag) + 1] if flag in argv else default
    out = _arg("--out")
    if not out:
        print(__doc__); return 2
    out = Path(out).resolve()
    baseline = _arg("--compare")
    problems = render_matte_previews(MATTE_SET, out)
    if baseline:
        problems += compare_previews(Path(baseline).resolve(), out, MATTE_SET)
    for p in problems:
        print(p)
    print(f"{len(MATTE_SET)} preview(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_preview_regress.py -v`
Expected: PASS (all three).

- [ ] **Step 5: Capture the pre-change baseline (real Godot render, rig still unchanged)**

Run: `& "C:\Program Files\Python313\python.exe" -m quality.preview_regress --out scratchpad/reflect-baseline`
Expected: `4 preview(s), 0 problem(s)`, four PNGs under `scratchpad/reflect-baseline/`. These are the "before" composites Task 2 diffs against. `scratchpad/` is gitignored — do not commit the PNGs.

- [ ] **Step 6: Commit**

```bash
git add quality/preview_regress.py tests/test_preview_regress.py
git commit -m "test(preview): 3D-composite no-regress gate for rig changes"
```

---

### Task 2: Decouple ambient from reflection (rig)

Split the single sky into an explicit ambient **color** (matte lighting frozen) plus a sky used **only** for reflection. Prove matte materials are pixel-identical via Task 1's gate. Do NOT enrich the sky yet — that is Task 3; keeping the change isolated makes the no-regress proof meaningful (a clean decouple should move zero matte pixels).

**Files:**
- Modify: `src/mm_mcp/preview_project/preview.gd:222-224` (the ambient/reflection source lines, in context of the sky block 206-243)

**Interfaces:**
- Consumes: nothing new.
- Produces: no code interface; the rig now honors `AMBIENT_SOURCE_COLOR` for ambient and `REFLECTION_SOURCE_SKY` for reflection.

- [ ] **Step 1: Make the decouple edit**

In the env block, replace the sky-driven ambient with an explicit color matched to the current sky-derived ambient, and keep reflection on the sky. The current sky ambient is roughly the average of its four colors; start from that and let the gate confirm. Change:

```gdscript
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
```
to:
```gdscript
	# Ambient is pinned to an explicit color (matched to what the sky above
	# derived) so enriching the reflection sky (below / next change) does NOT
	# re-light the matte materials. Reflection still reads the sky.
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.4, 0.42, 0.46)
	env.ambient_light_energy = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
```

- [ ] **Step 2: Render the matte set on the changed rig**

Run: `& "C:\Program Files\Python313\python.exe" -m quality.preview_regress --out scratchpad/reflect-after --compare scratchpad/reflect-baseline`
Expected: ideally `4 preview(s), 0 problem(s)`.

- [ ] **Step 3: Tune the ambient color until the gate is green**

If Step 2 reports diffs, the pinned `ambient_light_color` doesn't match the sky-derived ambient. Adjust the `Color(...)` toward the reported direction (brighter if the after is darker, etc.) and re-run Step 2. Repeat until `0 problem(s)`. This convergence IS the proof the decouple isolated matte lighting. (`renders_match` tolerance is a small mean-abs-diff, not byte-identity, so a near-exact match passes.)

- [ ] **Step 4: Commit**

```bash
git add src/mm_mcp/preview_project/preview.gd
git commit -m "feat(preview): decouple ambient (color) from reflection (sky)"
```

---

### Task 3: Enrich the reflection sky (visual)

Now that ambient is frozen, give the reflection sky bright/dark content so metallic surfaces show a recognizable reflection. Verify against `m04_scratched_steel` (the smoothest existing metal) and confirm the matte gate STILL passes (enriching the sky must not leak into ambient — if it does, the enum split isn't isolating and this must be reconsidered).

**Files:**
- Modify: `src/mm_mcp/preview_project/preview.gd:213-218` (the `ProceduralSkyMaterial` block)

- [ ] **Step 1: Enrich the sky material**

Raise contrast and energy so there is a bright region to reflect. Starting point (tune against the render):

```gdscript
	sky_mat.sky_top_color = Color(0.22, 0.30, 0.48)
	sky_mat.sky_horizon_color = Color(0.85, 0.88, 0.95)
	sky_mat.ground_bottom_color = Color(0.10, 0.09, 0.08)
	sky_mat.ground_horizon_color = Color(0.30, 0.30, 0.32)
	sky_mat.sky_energy_multiplier = 2.5
```

- [ ] **Step 2: Confirm the matte gate still passes**

Run: `& "C:\Program Files\Python313\python.exe" -m quality.preview_regress --out scratchpad/reflect-sky --compare scratchpad/reflect-baseline`
Expected: `4 preview(s), 0 problem(s)`. If matte materials now differ, ambient is NOT fully decoupled from the sky — STOP and report; the design assumption (the enum split isolates) has failed and needs revisiting before proceeding.

- [ ] **Step 3: Render the reflection check (metal) — then STOP for approval**

Render `m04_scratched_steel` on the enriched rig into a scratch dir (reuse the calibration pattern in `scratchpad/calib_reflect.py`, or `quality.preview_regress.render_matte_previews(["m04_scratched_steel"], Path("scratchpad/reflect-metal"))` from a script file). The subagent stops here — it cannot reach Grayson.

- [ ] **Step 4: Controller — send the render, get Grayson's approval**

Controller (not the subagent) sends `scratchpad/reflect-metal/m04_scratched_steel.png` (and the calibration before-shot for A/B) via SendUserFile and waits for Grayson's reply. Iterate Steps 1–3 on the sky constants until he approves the reflection reads. Only then continue.

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/preview_project/preview.gd
git commit -m "feat(preview): enrich reflection sky so metals read (Grayson-approved)"
```

---

### Task 4: Author a polished metal — `m05_polished_chrome` (visual)

Pure metallic case: `metallic`≈1, low `roughness`, near-neutral bright albedo, minimal relief. Prove the metallic path reads against the enriched env.

**Files:**
- Modify: `quality/cookbook_metal.py` (add `build_m05_polished_chrome(catalog) -> str`; register in the `BUILDERS` dict)
- Create (build output, gitignored): `quality/authored/cookbook-metal/m05_polished_chrome/v1.ptex`
- Create (promoted, tracked): `cookbook/metal/m05_polished_chrome.ptex` + `.md`

**Interfaces:**
- Consumes: `quality.author_helpers` (`save_variant`, `set_param`, `group_into_subgraph`, `rename_nodes`, `_from_scratch_noise_material`, `retype`, `add_node`, `_grad`); `build_catalog(cfg.nodes_dir)`; existing metal builders as reference (`build_m04_scratched_steel`).
- Produces: cookbook entry `metal/m05_polished_chrome`.

- [ ] **Step 1: Write the builder**

Clone/adapt an existing metal builder (e.g. take `m04`'s structure or start from `_from_scratch_noise_material`), then drive the material node: `metallic`≈1.0 scalar, `roughness` low (~0.08–0.15) with faint variation, albedo a bright near-neutral (slight warm/cool), very shallow micro-normal. Role-name every node (mirror `_M01_NAMES`-style dicts). Return `save_variant(g, _LABEL, "m05_polished_chrome", 1)`. Register `"m05_polished_chrome": build_m05_polished_chrome` in `BUILDERS`.

- [ ] **Step 2: Build + promote**

Run: `& "C:\Program Files\Python313\python.exe" -m quality.cookbook_metal ; & "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook cookbook-metal`
Expected: `cookbook/metal/m05_polished_chrome.ptex` + `.md` written. `git checkout --` any unrelated `.md` line-ending churn (autocrlf) so only m05 stages.

- [ ] **Step 3: Render the preview — then STOP for approval**

Render `m05_polished_chrome`'s 3D preview into a scratch dir (script file, one Godot). Subagent stops.

- [ ] **Step 4: Controller — send render, get approval; iterate**

Controller sends the preview via SendUserFile, waits for Grayson. Iterate the builder (Steps 1–3) until he approves. Visual-approval is the gate; there is no unit test for "looks like chrome".

- [ ] **Step 5: Objective gates green**

Run: `& "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook --check ; & "C:\Program Files\Python313\python.exe" -m pytest tests/test_cookbook_naming_gate.py tests/test_cookbook_card_table_gate.py tests/test_readme_counts.py -q`
Expected: all pass (counts recompute to include m05). If README count wording is stale, it's a code/tree recompute — do not hand-edit the number.

- [ ] **Step 6: Commit**

```bash
git add quality/cookbook_metal.py cookbook/metal/m05_polished_chrome.ptex cookbook/metal/m05_polished_chrome.md cookbook/README.md
git commit -m "feat(cookbook): m05_polished_chrome — metallic reflection proof (Grayson-approved)"
```

---

### Task 5: Author a wet dark stone — `s14_wet_river_stone` (visual)

Dielectric case: `metallic`≈0, very low `roughness` (wet sheen), dark albedo, reflecting via specular not metallic. Different physical path from the metals; the more valuable env test.

**Files:**
- Modify: `quality/cookbook_stone.py` (add `build_s14_wet_river_stone(catalog) -> str`; register in `BUILDERS`)
- Create (gitignored): `quality/authored/cookbook-stone/s14_wet_river_stone/v1.ptex`
- Create (tracked): `cookbook/stone/s14_wet_river_stone.ptex` + `.md`

**Interfaces:**
- Consumes: same `author_helpers`; existing stone builders as reference (`build_s06_river_pebbles` for the pebble/voronoi base with a working normal chain).
- Produces: cookbook entry `stone/s14_wet_river_stone`.

- [ ] **Step 1: Write the builder**

Clone a pebble/river-stone base that already has a working normal chain (e.g. `s06_river_pebbles`), then: darken albedo, drop `roughness` low and roughly uniform (wet), keep `metallic`≈0 (dielectric — reflection comes from Godot's default specular, not metallic). Keep the existing relief. Role-name nodes. Return `save_variant(g, _LABEL, "s14_wet_river_stone", 1)`; register in `BUILDERS`.

- [ ] **Step 2: Build + promote**

Run: `& "C:\Program Files\Python313\python.exe" -m quality.cookbook_stone ; & "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook cookbook-stone`
Expected: `cookbook/stone/s14_wet_river_stone.ptex` + `.md`. `git checkout --` unrelated `.md` churn.

- [ ] **Step 3: Render the preview — then STOP for approval**

Render `s14_wet_river_stone`'s 3D preview to a scratch dir (script file). Subagent stops.

- [ ] **Step 4: Controller — send render, get approval; iterate**

Controller SendUserFile + wait for Grayson. Iterate the builder until approved.

- [ ] **Step 5: Objective gates green**

Run: `& "C:\Program Files\Python313\python.exe" -m quality.promote_cookbook --check ; & "C:\Program Files\Python313\python.exe" -m pytest tests/test_cookbook_naming_gate.py tests/test_cookbook_card_table_gate.py tests/test_readme_counts.py -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add quality/cookbook_stone.py cookbook/stone/s14_wet_river_stone.ptex cookbook/stone/s14_wet_river_stone.md cookbook/README.md
git commit -m "feat(cookbook): s14_wet_river_stone — dielectric wet reflection (Grayson-approved)"
```

---

### Task 6: Full suite + optional showcase, then close

**Files:**
- Optional: `quality/_make_showcase.py` (`_TILE_OVERRIDES` if a new material needs a tile), `docs/images/gallery/*`, `docs/images/hero.png`, `cookbook/README.md`.

- [ ] **Step 1: Run the full test suite**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest -q`
Expected: green (fast suite). Note any pre-existing concurrent-Godot flake (the live-overlay round-trip test) and re-run it alone if it trips.

- [ ] **Step 2: Optional — add a reflective material to the front-page gallery**

Only if Grayson wants it in the gallery. Add its tile to `_make_showcase._TILE_OVERRIDES` if it reads wrong at 0.45, then regen the affected stills: `& "C:\Program Files\Python313\python.exe" -m quality._make_showcase still <ident>` (and `hero` if it enters the hero montage). Controller sends the regen via SendUserFile for approval. Gallery curation is Grayson's call — skip if he doesn't ask.

- [ ] **Step 3: Commit any showcase changes**

```bash
git add quality/_make_showcase.py docs/images/gallery cookbook/README.md
git commit -m "docs(showcase): add reflective material to front-page gallery"
```

- [ ] **Step 4: Update STATUS.md + HANDOFF.md**

Flip nothing to ✅ that Grayson hasn't approved. Record: reflections rig decouple + enriched sky (verified via the composite no-regress gate), `quality/preview_regress.py` new gate, m05/s14 new materials, cookbook count bump. Note the emission cycle is next (with the parked `_emission.png`-unconditional question). This is the wrap-up commit.

---

## Self-Review

**Spec coverage:**
- Rig decouple (spec §1) → Task 2. Enrich reflection sky (spec §1) → Task 3. Verify enum split → Task 3 Step 2 (gate) + Task 2. ✓
- Dropped knob/probe (spec non-goals) → not built. ✓
- Polished metal (spec §2) → Task 4. Wet dark stone / dielectric (spec §2) → Task 5. ✓
- No-regress objective gate (spec §3) → Task 1 + used in Tasks 2/3. Reflection-reads check → Task 3 Step 3–4. Showcase optional → Task 6 Step 2. Full suite → Task 6 Step 1. ✓
- Emission parked (spec §4) → noted Task 6 Step 4, no work. ✓

**Placeholder scan:** Authoring Tasks 4/5 Step 1 describe the material target rather than giving an exact node graph — this is intended: material authoring is visual iteration against Grayson's eye, not a deterministic function, and the objective gates (promote --check, naming/card/README) plus his approval are the real acceptance. Not a hidden-code placeholder; the builder pattern, helpers, registration, and gates are all concrete.

**Type consistency:** `render_matte_previews`/`compare_previews`/`MATTE_SET` used consistently across Task 1 and referenced in Task 3. `build_<id>(catalog) -> str` + `save_variant(..., 1)` + `BUILDERS` registration consistent across Tasks 4/5, matching `cookbook_metal.py`/`cookbook_stone.py`. RenderResult/`.ok`/`.images` and PreviewResult/`.ok`/`.image` match the real signatures read from `render.py`/`_make_showcase.py`. ✓
