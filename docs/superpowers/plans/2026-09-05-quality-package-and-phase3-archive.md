# quality/ Package + Phase-3 Archive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `quality/` an honest importable package with no `sys.path` hacks, drop the false "frozen" label on `author.py`, thread one catalog through the last three builders, archive the closed Phase-3 gate apparatus under `docs/evidence/phase3/`, and stop the donor tests from failing at collection.

**Architecture:** `quality/` stays where it is and gets an `__init__.py`; every intra-package import becomes `from quality.<module> import ...`; scripts run as `python -m quality.<module>` from the repo root; pytest gets `"."` on its `pythonpath`. Phase-3 files move by `git mv` into `docs/evidence/phase3/` with a README; the retired runners are `git rm`'d. No cookbook `.ptex` changes: `promote_cookbook.py --check` is the invariant.

**Tech Stack:** Python 3.13, pytest, git. Windows, PowerShell 5.1 for anything Grayson runs (`;` not `&&`).

**Spec:** `docs/superpowers/specs/2026-09-05-quality-package-and-phase3-archive-design.md`

## Global Constraints

- Repo root: `C:\Projects-local\Tool-MaterialMaker-MCP`. Python: `.\.venv\Scripts\python.exe`. Run everything from the repo root.
- Fast suite command: `.\.venv\Scripts\python.exe -m pytest -q -m "not integration" -p no:cacheprovider`. Baseline before this plan: 638 passed, 25 deselected.
- No cookbook `.ptex` may change. After any task that touches builder code, `.\.venv\Scripts\python.exe -m quality.promote_cookbook --check` must print `cookbook/ is in sync with quality/authored/`. Running the builders first (`python -m quality.cookbook_<category>`) regenerates `quality/authored/`, which is gitignored.
- Never launch a Godot render from `python -c`. None of these tasks needs a render.
- No em dashes in any prose written to disk. Use a colon, a comma, or a spaced hyphen.
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Never edit `.env`; never echo it.

---

### Task 1: Make `quality/` an importable package and remove every path hack

**Files:**
- Create: `quality/__init__.py`
- Modify: `pyproject.toml` (`[tool.pytest.ini_options] pythonpath`)
- Modify: every `quality/*.py` that has `sys.path.insert` or a bare intra-package import (`author.py`, `author_helpers.py`, the twelve `cookbook_*.py`, `debug_swatches.py`, `noise_gallery.py`, `verify_hero_fold.py`, `render_cookbook.py`, `render_one.py`, `_make_previews.py`, `contact_sheet.py`, `promote_cookbook.py`, `render_compare.py`, `pngread.py`, `run_case.py`, `score_baseline.py`; the sed steps below find them, do not hand-pick)
- Modify: `tests/test_author_helpers.py:13-15,214`, `tests/test_debug_swatches.py:17-19`, `tests/test_donors.py:60-67`, `tests/test_promote_cookbook.py:6-8`, `tests/test_render_compare.py:5-6`
- Modify: `MANIFEST.in:1-3` (comment only)
- Modify: docs that show the invocation: `cookbook/README.md:25-28`, `quality/README.md` (every `python quality/<x>.py` and `.venv\Scripts\python.exe quality\<x>.py`), `docs/DEBUG_SWATCHES.md:19-20`, `docs/AUTHORING.md:163-165`, `HANDOFF.md` heads-up bullet "Run `quality/*.py` from the repo root"
- Test: `tests/test_quality_package.py` (new)

**Interfaces:**
- Produces: `quality` is a package. `from quality.author_helpers import load_example, node, set_param, ...`, `from quality import author`, `from quality.promote_cookbook import promote`, `from quality.render_compare import grid_mean_abs_diff, renders_match`, `from quality.pngread import read_png, Sampler`, `from quality import debug_swatches`. Scripts run as `python -m quality.<module>`. Later tasks use these forms.

- [ ] **Step 1: Write the failing gate test**

Create `tests/test_quality_package.py`:

```python
"""quality/ is an importable package: no sys.path hacks anywhere, every
intra-package import is package-qualified, and the modules tests depend on
import cleanly by their package name."""
import importlib
import os
import re

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_QUALITY = os.path.join(_ROOT, "quality")
_TESTS = os.path.join(_ROOT, "tests")

INTRA_MODULES = (
    "author", "author_helpers", "render_compare", "pngread", "promote_cookbook",
    "debug_swatches", "noise_gallery", "render_cookbook", "render_one",
)


def _py_files(folder):
    return sorted(
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.endswith(".py") and f != "__init__.py"
    )


def test_quality_is_a_package():
    assert os.path.isfile(os.path.join(_QUALITY, "__init__.py"))


@pytest.mark.parametrize("path", _py_files(_QUALITY) + _py_files(_TESTS))
def test_no_sys_path_hacks(path):
    src = open(path, encoding="utf-8").read()
    assert "sys.path.insert" not in src, f"{os.path.relpath(path, _ROOT)} still edits sys.path"


@pytest.mark.parametrize("path", _py_files(_QUALITY) + _py_files(_TESTS))
def test_no_bare_intra_package_imports(path):
    src = open(path, encoding="utf-8").read()
    bare = re.findall(
        r"^\s*(?:from|import)\s+(" + "|".join(INTRA_MODULES) + r")\b(?!\.)",
        src, flags=re.M,
    )
    assert bare == [], f"{os.path.relpath(path, _ROOT)} imports {bare} by bare name; use quality.<module>"


@pytest.mark.parametrize("name", [
    "quality.author_helpers", "quality.promote_cookbook", "quality.render_compare",
    "quality.pngread", "quality.debug_swatches",
])
def test_package_modules_import_by_name(name):
    importlib.import_module(name)
```

- [ ] **Step 2: Run the gate test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_quality_package.py`
Expected: FAIL. `test_quality_is_a_package` fails (no `__init__.py`), the `sys.path` and bare-import checks fail for most files, and the import-by-name tests fail with `ModuleNotFoundError: No module named 'quality'`.

- [ ] **Step 3: Create the package marker and put the repo root on pytest's path**

Create `quality/__init__.py`:

```python
"""quality/: the cookbook factory.

Builder scripts that regenerate the tracked cookbook/ graphs
(cookbook_<category>.py), the shared graph-surgery helpers they use
(author_helpers.py, author.py), the promote/--check regression baseline,
render helpers, the diagnostic swatches, and the vendored PNG reader.
Importable as a package (`from quality.author_helpers import ...`); run
scripts as `python -m quality.<module>` from the repo root. Not shipped in
the wheel: these need Godot and a Material Maker checkout.
"""
```

In `pyproject.toml`, change:

```toml
pythonpath = ["src"]
```

to:

```toml
pythonpath = ["src", "."]
```

- [ ] **Step 4: Rewrite every intra-package import and delete every path hack**

Run this once from the repo root (it edits in place; review the diff afterwards):

```bash
./.venv/Scripts/python.exe - <<'EOF'
import os, re, glob
files = glob.glob("quality/*.py") + [
    "tests/test_author_helpers.py", "tests/test_debug_swatches.py",
    "tests/test_donors.py", "tests/test_promote_cookbook.py",
    "tests/test_render_compare.py",
]
mods = ["author_helpers", "author", "render_compare", "pngread", "promote_cookbook",
        "debug_swatches", "noise_gallery", "render_cookbook", "render_one"]
for path in files:
    if path.endswith("__init__.py"):
        continue
    s = open(path, encoding="utf-8").read()
    orig = s
    # drop every sys.path.insert line (and a trailing '# noqa' on the same line)
    s = re.sub(r"^[ \t]*sys\.path\.insert\([^\n]*\n", "", s, flags=re.M)
    for m in mods:
        s = re.sub(rf"^(\s*)from {m} import", rf"\1from quality.{m} import", s, flags=re.M)
        s = re.sub(rf"^(\s*)import {m} as (\w+)", rf"\1from quality import {m} as \2", s, flags=re.M)
        s = re.sub(rf"^(\s*)import {m}\b(?!\.)([^\n]*)", rf"\1from quality import {m}\2", s, flags=re.M)
    if s != orig:
        open(path, "w", encoding="utf-8", newline="\n").write(s)
        print("rewrote", path)
EOF
```

Then remove the two module-level path lines in `tests/test_donors.py` that the script leaves behind (around former lines 60-63):

```python
import sys
from pathlib import Path
```

Keep `from pathlib import Path` only if `Path` is still used in that file (it is, in `test_load_example_reads_from_the_vendored_donors_dir`); delete the `import sys` if `sys` is no longer used. Do the same `sys`/`Path`/`os` unused-import cleanup in each rewritten file: a leftover `import sys` is fine where `sys.argv` or `sys.exit` is used, and wrong where it was only for `sys.path`. Check with:

```bash
grep -ln "^import sys" quality/*.py tests/*.py | while read f; do grep -q "sys\.\(argv\|exit\|stderr\|stdout\|executable\)" "$f" || echo "unused sys in $f"; done
```

- [ ] **Step 5: Fix `author_helpers.py` root path and the comment in the docstring**

In `quality/author_helpers.py` the deleted `sys.path.insert(0, str(_ROOT / "src"))` line was followed by `from mm_mcp.config import load_config`. That import now relies on `pip install -e .` (the documented install) or pytest's `pythonpath`. Leave `_ROOT = Path(__file__).resolve().parent.parent` as is (it is used for `donors/` and `authored/`). Update the docstring's second paragraph so it reads:

```python
"""Pure graph-surgery helpers for cookbook authoring.

Everything here is pure graph-JSON surgery against the catalog vocabulary; no
Godot. One home for the ~10 helpers shared by author.py's builders and every
quality/cookbook_<category>.py / debug_swatches.py / noise_gallery.py
consumer. Import as `from quality.author_helpers import ...`.
"""
```

- [ ] **Step 6: Run the gate test and the whole fast suite**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_quality_package.py`
Expected: PASS, all parametrized cases.

Run: `.\.venv\Scripts\python.exe -m pytest -q -m "not integration" -p no:cacheprovider`
Expected: 638 + the new test count passed, 25 deselected, 0 failed.

- [ ] **Step 7: Prove the `-m` invocation works for a real builder and the baseline is intact**

Run:

```
.\.venv\Scripts\python.exe -m quality.cookbook_ceramic
.\.venv\Scripts\python.exe -m quality.promote_cookbook --check
```

Expected: the first prints `man02_ceramic_hex_tiles: <path under quality/authored/cookbook-ceramic/>`; the second prints `cookbook/ is in sync with quality/authored/` and exits 0. Also confirm the old form now fails, which is intended: `.\.venv\Scripts\python.exe quality\cookbook_ceramic.py` raises `ModuleNotFoundError: No module named 'quality'`.

- [ ] **Step 8: Update every documented invocation**

Replace each `python quality/<x>.py` / `.venv\Scripts\python.exe quality\<x>.py` with the module form. Exact edits:

`cookbook/README.md` lines 25-28 become:

```markdown
1. Rebuild a category: `.venv\Scripts\python.exe -m quality.cookbook_<category>`
2. Verify nothing drifted: `.venv\Scripts\python.exe -m quality.promote_cookbook --check`
3. Accept new output: `.venv\Scripts\python.exe -m quality.promote_cookbook`
```

`docs/DEBUG_SWATCHES.md` lines 19-20 become:

```
python -m quality.debug_swatches                 # write all swatch .ptex files
python -m quality.render_cookbook debug-swatches # validate + render them
```

`docs/AUTHORING.md` line 164: `Render with \`python quality/render_cookbook.py` becomes `Render with \`python -m quality.render_cookbook`.

`quality/README.md`: change every `python quality/promote_cookbook.py` to `python -m quality.promote_cookbook`, `render_cookbook.py <label>` to `python -m quality.render_cookbook <label>`, `render_one.py <label> <case>` to `python -m quality.render_one <label> <case>`, and add this sentence at the top of the "Layout" section: "`quality/` is a package: import with `from quality.<module> import ...` and run scripts as `python -m quality.<module>` from the repo root (a file-path launch no longer resolves the imports)."

`HANDOFF.md` heads-up bullet that starts "**Run `quality/*.py` from the repo root**" becomes "**Run quality scripts as `python -m quality.<module>` from the repo root** (a file-path launch no longer resolves the package imports; running from inside `quality/` also breaks `.env` lookup)."

`MANIFEST.in` lines 1-3 become:

```
# Keep the sdist to the installable package + its metadata. The test suite
# imports the quality/ package (not shipped), so bundling tests would give
# sdist installers an import error for no benefit.
```

Verify no stale form remains:

```bash
grep -rn "python quality/\|python\.exe quality\\\\\|quality/[a-z_]*\.py <" README.md CLAUDE.md HANDOFF.md STATUS.md docs/*.md cookbook/README.md quality/README.md
```

Expected: only prose references to file names (e.g. "`quality/pngread.py`" as a noun) remain; no invocation lines.

- [ ] **Step 9: Commit**

```bash
git add quality/__init__.py pyproject.toml quality/*.py tests/*.py MANIFEST.in cookbook/README.md quality/README.md docs/DEBUG_SWATCHES.md docs/AUTHORING.md HANDOFF.md
git commit -F - <<'EOF'
refactor(quality): make quality/ an importable package, drop every sys.path hack

quality/ is the cookbook's source (5,961 lines, bigger than src/) but was
wired like a scratch folder: 26 sys.path.insert lines across the scripts
and five test files, bare intra-package imports that only resolved when
Python was launched on the file itself. Now it is a package: every import
is `from quality.<module> import ...`, scripts run as
`python -m quality.<module>` from the repo root, and pytest puts the repo
root on its pythonpath. A gate test forbids sys.path edits and bare
imports from coming back. No builder logic changed; promote --check is in
sync.

Teardown #4 finding 5, spec docs/superpowers/specs/2026-09-05-quality-package-and-phase3-archive-design.md.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 2: Thread one catalog through `cookbook_wood`, `cookbook_glass`, `cookbook_plastics`

**Files:**
- Modify: `quality/cookbook_wood.py:26,83,117,142,161,179,205-214`
- Modify: `quality/cookbook_glass.py:24,76,100-109`
- Modify: `quality/cookbook_plastics.py:23,69,90-99`
- Test: `tests/test_cookbook_builders_signature.py` (new)

**Interfaces:**
- Consumes: `from quality.cookbook_<category> import BUILDERS` (a dict `{case_id: builder}`) for all twelve categories, established by Task 1's package form.
- Produces: every builder in every `BUILDERS` dict has the signature `build_<id>(catalog: dict) -> str`.

- [ ] **Step 1: Write the failing gate test**

Create `tests/test_cookbook_builders_signature.py`:

```python
"""Every cookbook builder takes the catalog as its one parameter, so main()
builds the catalog once and threads it through (the catalog build reads ~400
.mmg files; building it inside each builder was the pattern in three
stragglers). Also guards the BUILDERS contract the promote/--check baseline
relies on."""
import importlib
import inspect

import pytest

CATEGORIES = [
    "ceramic", "fabrics", "glass", "leather", "metal", "organics",
    "painted_metal", "plastics", "scifi", "stone", "terrain", "wood",
]


def _builders():
    for cat in CATEGORIES:
        mod = importlib.import_module(f"quality.cookbook_{cat}")
        for case_id, fn in mod.BUILDERS.items():
            yield pytest.param(cat, case_id, fn, id=f"{cat}/{case_id}")


@pytest.mark.parametrize("category,case_id,fn", list(_builders()))
def test_builder_takes_exactly_one_catalog_parameter(category, case_id, fn):
    params = list(inspect.signature(fn).parameters)
    assert params == ["catalog"], (
        f"quality/cookbook_{category}.py::{fn.__name__} has parameters {params}; "
        "expected exactly ('catalog',)"
    )
```

- [ ] **Step 2: Run it to verify it fails for exactly the three stragglers**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_cookbook_builders_signature.py`
Expected: FAIL for `wood/w03_painted_wood_siding`, `wood/w04_driftwood_gray`, `wood/w05_dark_walnut`, `glass/gl01_frosted_glass`, `plastics/p01_glossy_plastic` (parameters `[]`); PASS for the other 48. If any other category fails, stop and report: that builder's pattern differs from the spec's assumption and the reviewer must rule.

- [ ] **Step 3: Thread the catalog in `cookbook_wood.py`**

For each of the three builders, change the signature from `def build_w03_painted_wood_siding() -> str:` to `def build_w03_painted_wood_siding(catalog: dict) -> str:` and delete the line `catalog = build_catalog(load_config().nodes_dir)` inside it (lines 83, 142, 179). Then make `main()` match the ceramic pattern:

```python
def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0
```

Keep the existing `from mm_mcp.catalog_builder import build_catalog` and `from mm_mcp.config import load_config` imports (main still uses them).

- [ ] **Step 4: Same change in `cookbook_glass.py` and `cookbook_plastics.py`**

`cookbook_glass.py`: `def build_gl01_frosted_glass() -> str:` becomes `def build_gl01_frosted_glass(catalog: dict) -> str:`; delete the `catalog = build_catalog(load_config().nodes_dir)` line at 76; rewrite `main()` exactly as in Step 3.

`cookbook_plastics.py`: `def build_p01_glossy_plastic() -> str:` becomes `def build_p01_glossy_plastic(catalog: dict) -> str:`; delete the `catalog = ...` line at 69; rewrite `main()` exactly as in Step 3.

- [ ] **Step 5: Run the gate test**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_cookbook_builders_signature.py`
Expected: 53 passed.

- [ ] **Step 6: Regenerate the three categories and prove the tracked cookbook did not move**

Run:

```
.\.venv\Scripts\python.exe -m quality.cookbook_wood
.\.venv\Scripts\python.exe -m quality.cookbook_glass
.\.venv\Scripts\python.exe -m quality.cookbook_plastics
.\.venv\Scripts\python.exe -m quality.promote_cookbook --check
git status --short cookbook
```

Expected: each builder prints its case ids and paths; `--check` prints `cookbook/ is in sync with quality/authored/`; `git status --short cookbook` prints nothing.

- [ ] **Step 7: Run the fast suite and commit**

Run: `.\.venv\Scripts\python.exe -m pytest -q -m "not integration" -p no:cacheprovider`
Expected: all passed, 0 failed.

```bash
git add quality/cookbook_wood.py quality/cookbook_glass.py quality/cookbook_plastics.py tests/test_cookbook_builders_signature.py
git commit -F - <<'EOF'
refactor(quality): thread one catalog through the wood, glass, and plastics builders

The other nine cookbook builders take the catalog from main(); these three
built it inside each builder. Now every builder is build_<id>(catalog), and
a gate test asserts that signature across all 53. Regenerated all three
categories; promote --check is in sync, no tracked .ptex changed.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 3: Archive the Phase-3 gate apparatus and drop the "frozen" label

**Files:**
- Create: `docs/evidence/phase3/README.md`
- Move (git mv): `quality/test_set.json` to `docs/evidence/phase3/test_set.json`; `quality/scorecards/2026-08-26-baseline.md` and `quality/scorecards/2026-08-26-iter1.md` to `docs/evidence/phase3/`; `quality/scorecards/README.md` to `docs/evidence/phase3/freeze-rule.md`
- Remove (git rm): `quality/run_case.py`, `quality/score_baseline.py`, `quality/verify_hero_fold.py`
- Modify: `quality/author.py:1-10` (docstring), `quality/README.md` (rewrite), `STATUS.md` (Phase 3 row evidence pointer; the `quality/` Phase-3 harness component row), `README.md:319-321`, `docs/AUTHORING.md:3-6,10,79`, `.gitignore:25-30`, `HANDOFF.md` (the `verify_hero_fold` heads-up bullet), docstring path mentions in `quality/cookbook_fabrics.py:2`, `cookbook_leather.py:3`, `cookbook_painted_metal.py:3`, `cookbook_stone.py:3`, `cookbook_wood.py:3`, `debug_swatches.py:3`, `render_cookbook.py:2`
- Move (filesystem, untracked): `quality/runs/` to `C:\Projects-local\_to_delete\Tool-MaterialMaker-MCP-quality-runs-2026-09-05`
- Modify (other repo): `C:\Projects-local\backup-ops\projects.psd1:33` (drop the `quality\runs` exclusion line; it no longer exists)
- Test: `tests/test_phase3_evidence.py` (new)

**Interfaces:**
- Consumes: package form from Task 1 (`quality.render_compare` still exists and is imported by `tests/test_render_compare.py`; only `verify_hero_fold.py` consumed it from inside `quality/` and it is being removed).
- Produces: `docs/evidence/phase3/test_set.json` (unchanged content, `_meta.frozen == true`, `_meta.case_count == 15`), two scorecards, `freeze-rule.md`, `README.md`.

- [ ] **Step 1: Write the failing evidence test**

Create `tests/test_phase3_evidence.py`:

```python
"""The Phase-3 gate (15/15 on the frozen 15-case set, 2026-08-26) is closed.
Its apparatus is archived under docs/evidence/phase3/ as a record, not as a
live harness: the runner is retired and quality/ no longer carries it."""
import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EVIDENCE = os.path.join(_ROOT, "docs", "evidence", "phase3")


def test_frozen_test_set_is_archived_unchanged():
    with open(os.path.join(_EVIDENCE, "test_set.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["_meta"]["frozen"] is True
    assert data["_meta"]["frozen_date"] == "2026-08-26"
    assert data["_meta"]["case_count"] == 15
    cases = [k for k in data if not k.startswith("_")]
    assert len(cases) == 15


def test_scorecards_and_freeze_rule_are_archived():
    for name in ("2026-08-26-baseline.md", "2026-08-26-iter1.md", "freeze-rule.md", "README.md"):
        assert os.path.isfile(os.path.join(_EVIDENCE, name)), name


def test_phase3_runner_is_retired_from_quality():
    for name in ("run_case.py", "score_baseline.py", "verify_hero_fold.py", "test_set.json"):
        assert not os.path.exists(os.path.join(_ROOT, "quality", name)), f"quality/{name} should be gone"
    assert not os.path.isdir(os.path.join(_ROOT, "quality", "scorecards"))
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_phase3_evidence.py`
Expected: all three FAIL (`FileNotFoundError` for the archive, and the retire assertion fails because the files still exist).

Before moving anything, confirm `test_set.json` has 15 non-underscore top-level keys; if the cases live under a `cases` list instead, change the test's last two lines to `assert len(data["cases"]) == 15` and report the shape in the task summary:

```
.\.venv\Scripts\python.exe -c "import json;d=json.load(open('quality/test_set.json'));print([k for k in d][:20])"
```

- [ ] **Step 3: Record the last commit that carried the runners, then move and remove**

Run and note the sha (it goes into the README in Step 4):

```
git rev-parse --short HEAD
```

Then:

```
mkdir docs\evidence\phase3
git mv quality/test_set.json docs/evidence/phase3/test_set.json
git mv quality/scorecards/2026-08-26-baseline.md docs/evidence/phase3/2026-08-26-baseline.md
git mv quality/scorecards/2026-08-26-iter1.md docs/evidence/phase3/2026-08-26-iter1.md
git mv quality/scorecards/README.md docs/evidence/phase3/freeze-rule.md
git rm quality/run_case.py quality/score_baseline.py quality/verify_hero_fold.py
```

`git mv` leaves an empty `quality/scorecards/` on Windows; delete the empty folder: `Remove-Item quality\scorecards` (PowerShell) or `rmdir quality/scorecards`.

In `docs/evidence/phase3/freeze-rule.md`, replace `quality/test_set.json` with `test_set.json` (same folder now) and replace the one em dash in its title line with a colon (`# scorecards: the freeze rule`) and the one in the freeze log bullet with a colon.

- [ ] **Step 4: Write the evidence README**

Create `docs/evidence/phase3/README.md` (substitute the sha from Step 3 for `<sha>`):

```markdown
# Phase 3 evidence: authoring-quality gate (closed 2026-08-26)

What this folder is: the frozen artifacts that proved Phase 3's exit gate.
It is a record, not a harness. Nothing here runs.

- `test_set.json`: the 15 frozen prompt cases and the scoring rubric
  (`_meta.frozen = true`, 2026-08-26, Grayson-reviewed). Never edited since.
- `freeze-rule.md`: why the ruler could not move while authoring was tuned.
- `2026-08-26-baseline.md`: the 3B control scorecard (no AUTHORING.md recipes).
- `2026-08-26-iter1.md`: the 3C scorecard, 15/15 usable by an artist's
  eyeball standard. The gate was >= 11/15. STATUS.md and README.md cite this.

## What was retired

The runner that produced these (`quality/run_case.py`, its one-off
`score_baseline.py`) and the examples-fold checker `verify_hero_fold.py`
were removed from the tree on 2026-09-05; the last commit carrying them is
`<sha>` (`git show <sha>:quality/run_case.py`). The runner had not been
executed since the gate closed, and `verify_hero_fold.py` depended on the
retired `examples/` folder. Local render output from those runs
(`quality/runs/`, ~290 MB, never tracked) was moved to `_to_delete`.

## What replaced it

Cookbook growth does not use this apparatus. New materials come from
`quality/cookbook_<category>.py` builders, are locked by
`python -m quality.promote_cookbook`, and are regression-gated by
`python -m quality.promote_cookbook --check`. See `quality/README.md`.
Adding prompt cases to a scored set would start a new series under a new
folder here, per `freeze-rule.md`; it would not edit `test_set.json`.
```

- [ ] **Step 5: Drop the "frozen" label and repoint every reference**

`quality/author.py` lines 1-10 become:

```python
"""Material builders shared by six cookbook categories.

Each build_* function codifies the kind of remixing a live authoring session
does (recolor a ramp, swap a generator, blend two layers) so each variant is
reproducible. These started as the Phase-3 case builders and are still the
base that cookbook_ceramic/fabrics/metal/organics/painted_metal/stone import
(via take_variant). Edit them like any other builder: the regression guard is
`python -m quality.promote_cookbook --check`, which fails on any output drift
whichever file caused it. The graph-surgery primitives live in
author_helpers.py. Variants land under quality/authored/<label>/<case>/vN.ptex.
"""
```

Rewrite `quality/README.md` in full:

```markdown
# quality/: the cookbook factory

A Python package (`from quality.<module> import ...`; run scripts as
`python -m quality.<module>` from the repo root). Not shipped in the wheel:
everything here needs Godot and a Material Maker checkout. The tracked
`cookbook/` tree is its locked output; `docs/AUTHORING.md` holds the
invariants the builders follow.

## Layout

- `cookbook_<category>.py` (twelve): builders, one `build_<id>(catalog)` per
  material, `BUILDERS` dict, `main()` builds the catalog once and threads it
  through. Output: `quality/authored/cookbook-<category>/<id>/v1.ptex`
  (gitignored).
- `author_helpers.py`: pure graph-surgery helpers (`load_example`, `node`,
  `set_param`, `set_gradient`, `rewire`, `drop_conn`, `add_node`, `retype`,
  `save_variant`, `take_variant`, `group_into_subgraph`). No Godot.
- `author.py`: the material builders six categories import as their base.
  Edit freely; `--check` is the guard.
- `promote_cookbook.py`: copies each `v1.ptex` into `cookbook/<category>/<id>.ptex`;
  `--check` diffs regenerated output against the tracked copies and exits 1
  on drift. This is the regression baseline for the whole cookbook.
- `render_cookbook.py <label>` / `render_one.py <label> <case> [size]`:
  validate + render authored variants to `quality/cookbook/<label>/`
  (gitignored) for eyeballing. One Godot at a time. Run as a module, never
  from `python -c`.
- `_make_previews.py <label>` and `contact_sheet.py [labels]`: thumbnails
  under `docs/images/cookbook-<category>/` and the README contact sheet
  (save as an 8-bit palette).
- `render_compare.py`: `grid_mean_abs_diff`, `renders_match` (builder-before
  vs builder-after; it does not prove the tracked artifact was right).
- `debug_swatches.py`, `noise_gallery.py`, `pngread.py`: the diagnostic
  swatch gallery (`docs/DEBUG_SWATCHES.md`), the noise vocabulary gallery,
  and the vendored stdlib PNG reader used to verify ORM channels by value.
- `donors/`: the nine vendored Material Maker example graphs the builders
  start from (tracked; `tests/test_donors.py`).

## Workflow

1. Add or edit a builder in `cookbook_<category>.py`; call
   `group_into_subgraph` before `save_variant` returns.
2. `python -m quality.cookbook_<category> [case ...]` regenerates the variants.
3. `python -m quality.render_one cookbook-<category> <id>` to look; judge
   relief in 3D (`render_preview`), verify metallic/roughness/AO with
   `pngread`, not by eye.
4. `python -m quality.promote_cookbook --check` to see what would change;
   `python -m quality.promote_cookbook` to accept. Write or update the card
   `cookbook/<category>/<id>.md` and regenerate the thumbnail.
5. `tests/test_cookbook_gate.py` and `test_cookbook_subgraph_gate.py` keep
   every tracked graph valid, grouped, carded, and thumbnailed.

Run from the repo root (`.env` is read from the working directory). Godot
is not byte-deterministic, so a category-wide re-render can churn unrelated
thumbnails; `git status` and revert anything swept up.

## History

The Phase-3 authoring-quality gate (15/15 on a frozen 15-case set,
2026-08-26) was measured with a runner that lived here. Its frozen test set,
rubric, and scorecards are archived under `docs/evidence/phase3/`; the runner
is retired (see that folder's README).
```

`STATUS.md`: in the Phase 3 row, replace `quality/scorecards/2026-08-26-iter1.md` with `docs/evidence/phase3/2026-08-26-iter1.md`. Replace the component row that starts with ``| `quality/` Phase-3 harness`` with:

```
| `quality/` package (builders, helpers, promote/check, swatches) | ✅ | Importable package, `python -m quality.<module>`; `author.py` is the shared builder base, guarded by `--check`. `tests/test_quality_package.py`, `tests/test_cookbook_builders_signature.py`; `quality/README.md` |
| `docs/evidence/phase3/` | ✅ | Frozen Phase-3 test set, rubric, and both scorecards, archived 2026-09-05; runner retired. `tests/test_phase3_evidence.py` |
```

`README.md` line 320: replace `` `quality/scorecards/` `` with `` `docs/evidence/phase3/` ``. Two lines earlier, "measured against a frozen 15-case test set in [`quality/`](quality/)" becomes "measured against a frozen 15-case test set archived in [`docs/evidence/phase3/`](docs/evidence/phase3/)". Leave the "Material cookbook" paragraph's "The builders that regenerate the graphs live in `quality/`" alone (still true).

`docs/AUTHORING.md`: line 5 `quality/scorecards/` becomes `docs/evidence/phase3/`; line 10 `quality/test_set.json` becomes `docs/evidence/phase3/test_set.json`; line 79 `4. Render via the harness (\`quality/run_case.py\`) or \`render_graph\`.` becomes `4. Render via \`render_graph\` (or \`python -m quality.render_one\` for an authored variant).`

`.gitignore` lines 25-30 become:

```
# Cookbook authoring: the builders (quality/cookbook_*.py) write variants to
# quality/authored/ and renders to quality/cookbook/; both regenerable.
# quality/promote_cookbook.py copies locked variants into the tracked cookbook/.
quality/authored/
```

(Delete the `quality/runs/` line; keep the existing `quality/cookbook/` line and its comment below.)

Docstring mentions: in `quality/cookbook_fabrics.py`, `cookbook_leather.py`, `cookbook_painted_metal.py`, `cookbook_stone.py`, `cookbook_wood.py`, `debug_swatches.py`, `render_cookbook.py`, replace `quality/test_set.json` with `docs/evidence/phase3/test_set.json` and, in `render_cookbook.py` line 2, `test_set.json / runs/ / scorecards/` with `docs/evidence/phase3/`. Verify:

```bash
grep -rn "quality/test_set\|quality/scorecards\|run_case\|score_baseline\|verify_hero_fold\|quality/runs" --include=*.py --include=*.md --include=.gitignore . | grep -v "docs/evidence/\|docs/superpowers/\|CHANGELOG.md"
```

Expected: no hits outside `docs/evidence/`, `docs/superpowers/`, and `CHANGELOG.md`.

`HANDOFF.md`: delete the heads-up sentence "`quality/verify_hero_fold.py` now needs `examples/` restored from `_to_delete` to run (documented in its docstring)." from the `take_variant` bullet. In "Current state" line 40, leave the historical mention of `quality/verify_hero_fold.py` as is (it describes what happened on 2026-09-05).

- [ ] **Step 6: Move the local render scratch and drop the stale backup exclusion**

PowerShell, from anywhere:

```
Move-Item C:\Projects-local\Tool-MaterialMaker-MCP\quality\runs C:\Projects-local\_to_delete\Tool-MaterialMaker-MCP-quality-runs-2026-09-05
```

In `C:\Projects-local\backup-ops\projects.psd1`, delete the line
`'C:\Projects-local\Tool-MaterialMaker-MCP\quality\runs',` (line 33) and change the comment "(~1.3 GB total)" to "(~1 GB total; quality\runs retired 2026-09-05)". Verify the file still parses:

```
powershell -NoProfile -Command "Import-PowerShellDataFile C:\Projects-local\backup-ops\projects.psd1 | Out-Null; 'psd1 ok'"
```

Commit in backup-ops:

```
git -C C:\Projects-local\backup-ops add projects.psd1
git -C C:\Projects-local\backup-ops commit -m "chore: drop the retired quality\runs exclusion for Tool-MaterialMaker-MCP" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 7: Run the evidence test and the fast suite**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_phase3_evidence.py tests/test_quality_package.py tests/test_readme_counts.py`
Expected: all PASS.

Run: `.\.venv\Scripts\python.exe -m pytest -q -m "not integration" -p no:cacheprovider`
Expected: all passed, 0 failed (the count is one less than after Task 2 only if a test file was removed; none was).

Run: `.\.venv\Scripts\python.exe -m quality.promote_cookbook --check`
Expected: `cookbook/ is in sync with quality/authored/`.

- [ ] **Step 8: Commit**

```bash
git add -A docs/evidence quality .gitignore STATUS.md README.md docs/AUTHORING.md HANDOFF.md tests/test_phase3_evidence.py
git status --short
git commit -F - <<'EOF'
refactor(quality): archive the Phase-3 gate apparatus under docs/evidence, retire its runner, unfreeze author.py

The Phase-3 gate closed 2026-08-26 (15/15) and its runner had not been
executed since. The frozen test set, rubric, freeze rule, and both
scorecards move to docs/evidence/phase3/ as a record with a README naming
the commit that last carried run_case.py, score_baseline.py, and
verify_hero_fold.py (the last needed the retired examples/ folder). Local
quality/runs (290 MB, untracked) moved to _to_delete; its .gitignore line
and backup-ops exclusion are gone.

author.py loses the "frozen evidence, do not edit" label: six cookbook
builders import it, so it is a library, and promote --check is a stronger
freeze than the comment was. quality/README.md is rewritten as the package
README. A test pins the archive's shape and forbids the runner's return.

Teardown #4 finding 3, spec docs/superpowers/specs/2026-09-05-quality-package-and-phase3-archive-design.md.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

### Task 4: Build the donor-test catalog in a fixture, not at import

**Files:**
- Modify: `tests/test_donors.py:10-21,54-63`

**Interfaces:**
- Consumes: `quality.author_helpers._EX` (Task 1 form) in the existing last test.
- Produces: none.

- [ ] **Step 1: Reproduce the collection-time failure**

Run (PowerShell):

```
$env:MM_PROJECT_PATH = "C:\no-such-mm"; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_donors.py; Remove-Item Env:MM_PROJECT_PATH
```

Expected today: 1 error at collection, 0 tests run (the module-level `build_catalog(cfg.nodes_dir)` raises). Note the exact exception text for the summary.

- [ ] **Step 2: Replace the module-level build with a module-scoped fixture**

In `tests/test_donors.py`, delete these two module-level lines:

```python
cfg = load_config()
CATALOG = build_catalog(cfg.nodes_dir)
```

and add, right after `DONOR_NAMES`:

```python
@pytest.fixture(scope="module")
def catalog():
    """Built once per module. Only the validation tests need the Material
    Maker checkout; presence and JSON-shape tests must not."""
    return build_catalog(load_config().nodes_dir)
```

Change the validation test to take the fixture:

```python
@pytest.mark.parametrize("name", DONOR_NAMES)
def test_donor_graph_has_no_type_or_connection_errors(name, catalog):
    path = os.path.join(DONORS_DIR, f"{name}.ptex")
    with open(path, encoding="utf-8") as fh:
        root = json.load(fh)
    hard_errors = []
    for g in _all_graphs(root):
        for p in validate_graph(g, catalog):
            if p["severity"] == "error":
                hard_errors.append(p["message"])
    assert hard_errors == [], f"{name}: {hard_errors}"
```

The last test in the file (`test_load_example_reads_from_the_vendored_donors_dir`) stays; after Task 1 it reads `from quality import author_helpers` (module-level import at the top of the file is fine now; move it there and delete the in-function import).

- [ ] **Step 3: Verify the split behaviour**

Run the same command as Step 1.
Expected: 10 passed (presence + 9 JSON-shape) and 9 failed or errored individually (the catalog fixture raises for the 9 validation tests), no collection error. Then run without the override:

`.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_donors.py`
Expected: 20 passed.

- [ ] **Step 4: Fast suite and commit**

Run: `.\.venv\Scripts\python.exe -m pytest -q -m "not integration" -p no:cacheprovider`
Expected: all passed.

```bash
git add tests/test_donors.py
git commit -F - <<'EOF'
test(donors): build the catalog in a module fixture so a missing checkout fails 9 tests, not 20 at collection

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
```

---

## Self-review notes

- Spec coverage: decision 1 = Task 1; decision 2 = Task 3 step 5; decision 3 = Task 3 steps 3, 4, 6; decision 4 = Task 2; decision 5 = Task 4. Verification bullets: fast suite (every task), `--check` (Tasks 1, 2, 3), `grep sys.path.insert` (Task 1 gate test), donor split (Task 4 step 3).
- Names used across tasks: `quality.author_helpers`, `quality.promote_cookbook`, `quality.render_compare`, `quality.pngread`, `quality.debug_swatches`, `BUILDERS`, `build_<id>(catalog)`, `docs/evidence/phase3/`. Consistent.
- Out of scope and deliberately not done: renaming `quality/`, packaging it into the wheel, touching any `.ptex`.
