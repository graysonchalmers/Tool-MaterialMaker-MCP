# Showcase Lighting Refresh + GIF Strip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regenerate the README front-page still showcase (hero + 8 gallery tiles) with the new `render_preview` lighting rig, add a tasteful animated-GIF strip of ~5 favorites, and leave behind a reproducible script so the next rig change is one command instead of an ad-hoc redo.

**Architecture:** A single new dev-only script `quality/_make_showcase.py` owns the whole front-page image pipeline: resolve a material source (cookbook label OR explicit `.ptex` path) → render flat maps via `render.py` → composite via `preview.render_preview` (still) or `preview.render_preview_sweep` (GIF) → write to `docs/images/gallery/` (or `docs/images/hero.png` via a montage mode). Pure logic (source resolution, output-path mapping, montage crop/concat, GIF downscale) is fast-unit-tested; the Godot renders and every visual sign-off are explicit human/controller gates, not manufactured pytest assertions. Renders serialize on one Godot process.

**Tech Stack:** Python 3.13, Pillow (existing dev-only tool), Godot 4.7.1 headless via the existing `render.py` + `preview.py`, existing MCP server unchanged.

**Spec:** No separate spec doc; this plan is driven by the 2026-09-14 pickup briefing and the `preview.py` lighting-rig overhaul (`6ce84c6`). NORTH_STAR unaffected (docs-only front-page assets).

## Global Constraints

- Shell is PowerShell 5.1: `;` to sequence, `Push-Location`/`Pop-Location`, `& "C:\path\tool.exe"`. `&&` is a parse error. In the Bash tool, `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (and the GUI exe).
- **One Godot render at a time.** Pass `render()` / preview an ABSOLUTE `outdir` (relative → GUI opens → 180s timeout, empty log). Never launch a render from `python -c`.
- Run quality scripts as `python -m quality.<module>` from repo root (`pip install -e .` prerequisite).
- Gallery still native size is **1024×576**; hero is **2049×560** (three ~683×560 panels concatenated). Preserve these exactly so the README table/layout does not reflow.
- `render_preview` / `render_preview_sweep` take already-rendered `albedo/normal/orm` PATHS, not a `.ptex`. Render maps are named `<basename>_albedo.png`, `_normal.png`, `_orm.png`, `_heightmap.png`.
- Tracked binaries live in git history forever: decide GIF size budget UP FRONT and check actual output bytes before any commit. Target each GIF **≤ ~1.5 MB** (≈512px wide, 18 frames, 80ms). GIF is 8-bit palette (256 colors), so eyeball the glossy metals for banding.
- Implementer/controller split (from HANDOFF.md): implementers render + self-screen only; ONLY the controller runs `SendUserFile` and waits for Grayson's real approval. A subagent has no chat channel to Grayson.
- `bricks_grayson_edit` resolves from `saved_graphs/bricks_grayson_edit.ptex` (NOT a cookbook label): the script's source resolver MUST accept a path, or this tile is silently dropped.
- Tracked cookbook thumbnails (`docs/images/cookbook-*/*.png`) are flat ALBEDO downscales and the contact sheet is built from them: neither is touched by this work. Do NOT regen them.

---

### Task 1: Reproducible showcase pipeline script

**Files:**
- Create: `quality/_make_showcase.py`
- Test: `tests/test_make_showcase.py`

**Interfaces:**
- Consumes: `mm_mcp.render.render`, `mm_mcp.preview.render_preview`, `mm_mcp.preview.render_preview_sweep`, `mm_mcp.config.load_config`; cookbook graphs under `cookbook/<category>/<id>.ptex`; `saved_graphs/*.ptex`.
- Produces (pure, fast-tested helpers other tasks and tests rely on):
  - `resolve_source(ident: str) -> Path` — if `ident` ends in `.ptex` treat as a path (resolve relative to repo root); else search `cookbook/*/<ident>.ptex`; raise `FileNotFoundError` naming `ident` if neither hits.
  - `gallery_out_path(ident: str) -> Path` — `docs/images/gallery/<stem>.png` where `stem` is the label or the path's stem.
  - `montage(panel_paths: list[Path], out_path: Path, panel_w: int = 683, panel_h: int = 560) -> None` — center-crop each source PNG to `panel_w×panel_h`, concat horizontally, save.
  - `downscale_gif_frames(frame_paths: list[Path], width: int) -> list[PIL.Image]` — LANCZOS-resize each frame to `width` preserving aspect.

- [ ] **Step 1: Write failing tests for the pure helpers**

```python
# tests/test_make_showcase.py
from pathlib import Path
from PIL import Image
import pytest
from quality import _make_showcase as ms

ROOT = Path(__file__).resolve().parent.parent

def test_resolve_source_accepts_ptex_path():
    p = ms.resolve_source("saved_graphs/bricks_grayson_edit.ptex")
    assert p.is_file() and p.name == "bricks_grayson_edit.ptex"

def test_resolve_source_finds_cookbook_label():
    p = ms.resolve_source("s02_gray_granite")
    assert p.is_file() and p.parent.parent.name == "cookbook"

def test_resolve_source_missing_raises_naming_ident():
    with pytest.raises(FileNotFoundError, match="no_such_mat"):
        ms.resolve_source("no_such_mat")

def test_gallery_out_path_uses_stem():
    assert ms.gallery_out_path("s02_gray_granite").name == "s02_gray_granite.png"
    assert ms.gallery_out_path("saved_graphs/bricks_grayson_edit.ptex").name == "bricks_grayson_edit.png"

def test_montage_crops_and_concats(tmp_path):
    srcs = []
    for i, c in enumerate([(200, 0, 0), (0, 200, 0), (0, 0, 200)]):
        s = tmp_path / f"p{i}.png"; Image.new("RGB", (1024, 576), c).save(s); srcs.append(s)
    out = tmp_path / "hero.png"
    ms.montage(srcs, out, panel_w=683, panel_h=560)
    assert Image.open(out).size == (683 * 3, 560)

def test_downscale_gif_frames_preserves_aspect(tmp_path):
    fr = tmp_path / "f.png"; Image.new("RGB", (1024, 576)).save(fr)
    out = ms.downscale_gif_frames([fr], width=512)
    assert out[0].size == (512, 288)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_make_showcase.py -v`
Expected: FAIL (module `_make_showcase` not found).

- [ ] **Step 3: Implement `quality/_make_showcase.py`**

Implement the four pure helpers above plus a `main(argv)` CLI:
- `python -m quality._make_showcase still <ident> [<ident> ...]` — for each: resolve → `render()` maps to an absolute temp outdir → `render_preview()` → copy/save the composite to `gallery_out_path(ident)` at native 1024×576.
- `python -m quality._make_showcase hero <identA> <identB> <identC>` — render each still to temp, then `montage([...], docs/images/hero.png)`.
- `python -m quality._make_showcase gif <ident> [--width 512] [--frames 18] [--duration 80]` — resolve → `render()` maps → `render_preview_sweep(frames=..., frame_duration_ms=...)` → `downscale_gif_frames` → reassemble a looping GIF to `docs/images/gallery/<stem>.gif`; print the output byte size.
- All Godot outdirs MUST be absolute. One material at a time.

Keep the pure helpers import-safe (no Godot at import time) so the fast tests never launch Godot.

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_make_showcase.py -v`
Expected: PASS (all 6).

- [ ] **Step 5: Commit**

```bash
git add quality/_make_showcase.py tests/test_make_showcase.py
git commit -m "feat(quality): reproducible front-page showcase render script"
```

---

### Task 2: Single-tile drift proof (human gate, FIRST render executed)

**Files:** none created; produces one throwaway render into the scratchpad.

**Interfaces:** Consumes Task 1's `still` mode.

- [ ] **Step 1: Render granite with the new rig**

Run: `& "C:\Program Files\Python313\python.exe" -m quality._make_showcase still s02_gray_granite`
(writes `docs/images/gallery/s02_gray_granite.png`; keep the old one staged/unstaged so it can be diffed).

- [ ] **Step 2: Confirm dimensions unchanged**

Run a Pillow size check: the new `s02_gray_granite.png` MUST be `(1024, 576)`.
Expected: `(1024, 576)`. If not, the rig moved the render resolution — STOP and fix the script's size handling before proceeding.

- [ ] **Step 3: CONTROLLER GATE — visual framing check**

Controller `SendUserFile`s the new granite next to the old tracked one and asks Grayson to confirm the camera/composition/framing did not drift (only lighting should differ). This is a human gate, not an assertion.
Expected: Grayson confirms framing matches (lighting improved, composition same). If composition drifted, that is a `preview.gd` question, not a script bug — surface it and pause.

- [ ] **Step 4: No commit** (granite is re-rendered as part of Task 3's batch; this task only de-risks the batch).

---

### Task 3: Regenerate all 8 gallery stills

**Files:**
- Modify (regenerate): `docs/images/gallery/*.png` (all 8)

**Interfaces:** Consumes Task 1 `still` mode.

- [ ] **Step 1: Render the 7 cookbook tiles + the round-trip tile**

Run, one at a time (serialize on Godot):
`python -m quality._make_showcase still s02_gray_granite f01_woven_denim o03_tree_bark w05_dark_walnut man02_ceramic_hex_tiles m02_brushed_aluminum o01_mossy_forest_floor`
then:
`python -m quality._make_showcase still saved_graphs/bricks_grayson_edit.ptex`

- [ ] **Step 2: Implementer self-screen**

Implementer opens each new PNG, confirms it is a lit 3D composite (not blank, not flat albedo), 1024×576, and visibly improved over the old-rig look. Note any material that reads worse under the new rig (e.g. a metal gone too dark) for the controller to flag.

- [ ] **Step 3: CONTROLLER GATE — batch approval**

Controller `SendUserFile`s all 8 refreshed stills in ONE message, waits for Grayson's real approval. Address any per-tile re-render requests before proceeding.
Expected: Grayson approves the 8 stills (or names specific re-renders).

- [ ] **Step 4: Commit**

```bash
git add docs/images/gallery/
git commit -m "docs(images): regenerate gallery stills with new lighting rig"
```

---

### Task 4: Regenerate the hero montage

**Files:**
- Modify (regenerate): `docs/images/hero.png`

**Interfaces:** Consumes Task 1 `hero` mode; sources are three approved Task 3 materials.

- [ ] **Step 1: Confirm the hero trio**

Default trio matching the current hero (cobblestone/flagstone, moss, ceramic tile): controller proposes three identifiers from the approved gallery set (default `saved_graphs/bricks_grayson_edit.ptex`, `o01_mossy_forest_floor`, `man02_ceramic_hex_tiles`) and gets Grayson's yes or a swap. Human gate.

- [ ] **Step 2: Render the montage**

Run: `python -m quality._make_showcase hero <idA> <idB> <idC>`
Confirm output is `(2049, 560)` (or the exact panel math for the chosen `panel_w×3`).

- [ ] **Step 3: CONTROLLER GATE — hero approval**

Controller `SendUserFile`s the new `hero.png`, waits for approval.
Expected: Grayson approves (or requests a different trio/crop).

- [ ] **Step 4: Commit**

```bash
git add docs/images/hero.png
git commit -m "docs(images): regenerate hero montage with new lighting rig"
```

---

### Task 5: Render the ~5 showcase GIFs

**Files:**
- Create: `docs/images/gallery/<stem>.gif` (≈5 files)

**Interfaces:** Consumes Task 1 `gif` mode; sources are Grayson's 5 favorites from the approved stills.

- [ ] **Step 1: Grayson picks the 5 favorites**

Controller asks Grayson to name 5 from the approved stills (cobblestone is a strong candidate — his approved lighting-verification pick). Human gate. Do not guess.

- [ ] **Step 2: Render each GIF within budget**

Run per material, one at a time:
`python -m quality._make_showcase gif <ident> --width 512 --frames 18 --duration 80`
Print and record each output's byte size. Any GIF over ~1.5 MB: drop `--width` to 448 or `--frames` to 14 and re-render before proposing it.

- [ ] **Step 3: CONTROLLER GATE — GIF approval (loop + banding)**

Controller `SendUserFile`s the 5 GIFs, confirms the loop reads well and the 8-bit palette does not band badly on any (especially metals). Waits for approval.
Expected: Grayson approves the 5 (or swaps any that band/loop poorly).

- [ ] **Step 4: Commit**

```bash
git add docs/images/gallery/*.gif
git commit -m "docs(images): add showcase sweep GIFs for the front page"
```

---

### Task 6: Embed the GIF strip in the README + gate

**Files:**
- Modify: `README.md` (Gallery section, add a motion strip)

**Interfaces:** References the Task 5 GIF paths.

- [ ] **Step 1: Add the motion strip**

Insert a tasteful "In motion" subsection under the Gallery (before the cookbook), embedding the 5 GIFs (a compact row or 2-wide table), each with descriptive alt text. Add one sentence explaining the sweep shows relief the static frame hides. Do NOT touch the material/category counts prose (`test_readme_counts.py` parses it).

- [ ] **Step 2: Run the README + fast gates**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_readme_counts.py tests/test_make_showcase.py -v`
Expected: PASS. Then eyeball the README render (GitHub-flavored markdown) locally or via a preview.

- [ ] **Step 3: CONTROLLER GATE — final README look**

Controller confirms with Grayson the front page reads well with stills + GIF strip together.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add animated showcase strip to README front page"
```

---

## Self-Review

**Spec coverage:** (1) refresh stills with new rig → Tasks 2–4; (2) reproducible script so next time is one command → Task 1; (3) top-5 GIFs, GitHub renders them → Tasks 5–6; (4) tasteful placement → Task 6. Covered.

**Placeholder scan:** GIF budget, sizes, source list, and identifiers are all concrete. The only deliberately-deferred values are Grayson's human picks (hero trio, 5 favorites), which are explicit human gates, not placeholders.

**Type consistency:** `resolve_source` / `gallery_out_path` / `montage` / `downscale_gif_frames` signatures are used identically in Task 1's tests and referenced by later tasks. `still` / `hero` / `gif` CLI subcommands are consistent across Tasks 2–5.

**Known risks:** (a) a material may read worse under the new rig (dark metal) — surfaced in Task 3 self-screen; (b) GIF bytes — gated in Task 5 Step 2; (c) hero panel crop math — verified in Task 4 Step 2.
