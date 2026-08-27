# Phase 5 Overlay Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `ensure_overlay()`, a pure-filesystem function that produces and
refreshes a disposable Material Maker project overlay (pristine checkout +
live-control addon + one autoload registration line), so later Phase 5 steps
have something real to launch Godot against.

**Architecture:** A single new module, `src/mm_mcp/overlay.py`, with one public
function (`ensure_overlay`) and small private helpers for content hashing,
autoload-line injection, and a staleness marker. No Godot process is ever
launched by this module; everything is `shutil`/`os` filesystem work, which is
what makes it unit-testable without Godot per the spec's Testing section.

**Tech Stack:** Python 3.13, stdlib only (`hashlib`, `json`, `os`, `shutil`),
pytest with `tmp_path`.

**Spec:** [docs/superpowers/specs/2026-08-26-live-control-addon-design.md](../specs/2026-08-26-live-control-addon-design.md)
— this plan implements sub-plan step 1 ("Overlay builder") only. Steps 2-4
(addon skeleton, mutating commands, MCP tool surface) are separate future
plans; do not build them here.

## Global Constraints

- **Windows-only project** (see STATUS.md Phase 4) — no new cross-platform
  requirement introduced by this module.
- **Pure filesystem work.** This module never launches Godot or imports
  anything Godot-related. That is what makes the spec's unit tests possible
  without Godot.
- **Addon entry script is fixed at `live_server.gd`.** The addon folder's
  basename becomes its Godot autoload name (`addon_name`), and the module
  always wires `res://addons/<addon_name>/live_server.gd` — this module is
  purpose-built for the one `mm_live` addon Phase 5 needs, not a generic
  addon installer (YAGNI: don't build a generic abstraction for one caller).
- **Exact autoload line format** (verified live against real Material Maker in
  tonight's 2026-08-26 spike): `mm_live="*res://addons/mm_live/live_server.gd"`
  appended to `project.godot`'s existing `[autoload]` section.
- **`steam_appid.txt` must survive into the overlay** or Material Maker
  self-relaunches and exits immediately (documented gotcha in this project's
  CLAUDE.md). Copying the whole checkout wholesale satisfies this
  automatically — no special-casing needed, but a test must assert it.
- **Staleness is addon-content-hash + checkout-path, not checkout-content-hash.**
  The spec is explicit: "a hash of the addon folder's contents and the
  pristine checkout's path." A real Material Maker checkout is ~266MB;
  hashing it on every launch would be slow. A checkout *swap* (different
  path passed in) is what triggers a rebuild, not edits inside the checkout
  (which stays pristine/untouched per this project's other standing rules
  anyway).

---

### Task 1: Stable directory content hash

**Files:**
- Create: `src/mm_mcp/overlay.py`
- Test: `tests/test_overlay.py`

**Interfaces:**
- Produces: `_hash_dir(path: str) -> str` — sha256 hex digest, stable for
  identical directory contents, sensitive to file content changes and to
  files being added/removed/renamed.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_overlay.py
import os
from mm_mcp.overlay import _hash_dir


def _write(path, rel, content):
    full = os.path.join(path, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)


def test_hash_dir_stable_for_identical_contents(tmp_path):
    a = tmp_path / "a"
    a.mkdir()
    _write(str(a), "one.txt", "hello")
    _write(str(a), "sub/two.txt", "world")

    assert _hash_dir(str(a)) == _hash_dir(str(a))


def test_hash_dir_changes_when_file_content_changes(tmp_path):
    a = tmp_path / "a"
    a.mkdir()
    _write(str(a), "one.txt", "hello")
    before = _hash_dir(str(a))

    _write(str(a), "one.txt", "hello world")
    after = _hash_dir(str(a))

    assert before != after


def test_hash_dir_changes_when_file_added(tmp_path):
    a = tmp_path / "a"
    a.mkdir()
    _write(str(a), "one.txt", "hello")
    before = _hash_dir(str(a))

    _write(str(a), "two.txt", "new")
    after = _hash_dir(str(a))

    assert before != after
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: FAIL (collection error) — `mm_mcp.overlay` module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/mm_mcp/overlay.py
import hashlib
import os


def _hash_dir(path: str) -> str:
    """Stable content hash of a directory: sensitive to file content and to
    which relative paths exist, not to filesystem walk order or OS path
    separators, so it hashes the same on repeated calls and across the
    fake directories the overlay tests build."""
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            h.update(rel.encode("utf-8"))
            with open(full, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/overlay.py tests/test_overlay.py
git commit -m "feat(overlay): add stable directory content hash"
```

---

### Task 2: Idempotent autoload-line injection

**Files:**
- Modify: `src/mm_mcp/overlay.py`
- Test: `tests/test_overlay.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `_append_autoload(project_godot_path: str, addon_name: str) -> None`
  — appends `<addon_name>="*res://addons/<addon_name>/live_server.gd"` to the
  file's `[autoload]` section if not already present; no-op if it already is.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_overlay.py (append)
from mm_mcp.overlay import _append_autoload

_FAKE_PROJECT_GODOT = """; fake project.godot, mirrors real MM's shape

[application]

config/name="fake"

[autoload]

mm_globals="*res://material_maker/globals.tscn"
Html5="*res://material_maker/html5.gd"
"""


def test_append_autoload_adds_the_line(tmp_path):
    pg = tmp_path / "project.godot"
    pg.write_text(_FAKE_PROJECT_GODOT, encoding="utf-8")

    _append_autoload(str(pg), "mm_live")

    content = pg.read_text(encoding="utf-8")
    assert 'mm_live="*res://addons/mm_live/live_server.gd"' in content


def test_append_autoload_is_idempotent(tmp_path):
    pg = tmp_path / "project.godot"
    pg.write_text(_FAKE_PROJECT_GODOT, encoding="utf-8")

    _append_autoload(str(pg), "mm_live")
    _append_autoload(str(pg), "mm_live")

    content = pg.read_text(encoding="utf-8")
    assert content.count('mm_live="*res://addons/mm_live/live_server.gd"') == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: FAIL — `_append_autoload` not defined.

- [ ] **Step 3: Write minimal implementation**

```python
# src/mm_mcp/overlay.py (append)
def _autoload_line(addon_name: str) -> str:
    return f'{addon_name}="*res://addons/{addon_name}/live_server.gd"'


def _append_autoload(project_godot_path: str, addon_name: str) -> None:
    line = _autoload_line(addon_name)
    with open(project_godot_path, encoding="utf-8") as fh:
        content = fh.read()
    if line in content:
        return
    if not content.endswith("\n"):
        content += "\n"
    with open(project_godot_path, "w", encoding="utf-8") as fh:
        fh.write(content + line + "\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/overlay.py tests/test_overlay.py
git commit -m "feat(overlay): add idempotent autoload-line injection"
```

---

### Task 3: Staleness marker (read / write / compare)

**Files:**
- Modify: `src/mm_mcp/overlay.py`
- Test: `tests/test_overlay.py`

**Interfaces:**
- Consumes: nothing from Tasks 1-2 directly (independent helpers).
- Produces:
  - `_write_marker(overlay_dir: str, addon_hash: str, mm_project_path: str) -> None`
  - `_is_stale(overlay_dir: str, addon_hash: str, mm_project_path: str) -> bool`
    — `True` if no marker exists yet, or if either input differs from what's
    recorded.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_overlay.py (append)
from mm_mcp.overlay import _write_marker, _is_stale


def test_is_stale_true_when_no_marker(tmp_path):
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    assert _is_stale(str(overlay), "hash1", "/mm/project") is True


def test_is_stale_false_when_marker_matches(tmp_path):
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    _write_marker(str(overlay), "hash1", "/mm/project")
    assert _is_stale(str(overlay), "hash1", "/mm/project") is False


def test_is_stale_true_when_addon_hash_differs(tmp_path):
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    _write_marker(str(overlay), "hash1", "/mm/project")
    assert _is_stale(str(overlay), "hash2", "/mm/project") is True


def test_is_stale_true_when_mm_project_path_differs(tmp_path):
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    _write_marker(str(overlay), "hash1", "/mm/project")
    assert _is_stale(str(overlay), "hash1", "/mm/other_project") is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: FAIL — `_write_marker`/`_is_stale` not defined.

- [ ] **Step 3: Write minimal implementation**

```python
# src/mm_mcp/overlay.py (append)
import json

_MARKER_NAME = ".mm_overlay_marker.json"


def _marker_path(overlay_dir: str) -> str:
    return os.path.join(overlay_dir, _MARKER_NAME)


def _read_marker(overlay_dir: str) -> dict | None:
    path = _marker_path(overlay_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _write_marker(overlay_dir: str, addon_hash: str, mm_project_path: str) -> None:
    with open(_marker_path(overlay_dir), "w", encoding="utf-8") as fh:
        json.dump({"addon_hash": addon_hash, "mm_project_path": mm_project_path}, fh)


def _is_stale(overlay_dir: str, addon_hash: str, mm_project_path: str) -> bool:
    marker = _read_marker(overlay_dir)
    if marker is None:
        return True
    return (marker.get("addon_hash") != addon_hash
            or marker.get("mm_project_path") != mm_project_path)
```

Move the `import json` to the top of the file with the other imports rather
than inline.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/overlay.py tests/test_overlay.py
git commit -m "feat(overlay): add staleness marker read/write/compare"
```

---

### Task 4: `ensure_overlay` — first build

**Files:**
- Modify: `src/mm_mcp/overlay.py`
- Test: `tests/test_overlay.py`

**Interfaces:**
- Consumes: `_hash_dir` (Task 1), `_append_autoload` (Task 2), `_write_marker`
  (Task 3).
- Produces: `ensure_overlay(mm_project_path: str, addon_path: str, overlay_dir: str) -> str`
  — the public entry point. This task covers only the first-build path (no
  existing overlay); Task 5 covers no-op and rebuild.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_overlay.py (append)
import pytest
from mm_mcp.overlay import ensure_overlay


@pytest.fixture
def fake_checkout(tmp_path):
    checkout = tmp_path / "mm_checkout"
    checkout.mkdir()
    _write(str(checkout), "project.godot", _FAKE_PROJECT_GODOT)
    _write(str(checkout), "steam_appid.txt", "4110830")
    _write(str(checkout), "material_maker/globals.gd", "# real MM file")
    return checkout


@pytest.fixture
def fake_addon(tmp_path):
    addon = tmp_path / "mm_live"
    addon.mkdir()
    _write(str(addon), "live_server.gd", "extends Node\n# v1")
    return addon


def test_ensure_overlay_first_build(tmp_path, fake_checkout, fake_addon):
    overlay_dir = str(tmp_path / "overlay")

    result = ensure_overlay(str(fake_checkout), str(fake_addon), overlay_dir)

    assert result == overlay_dir
    project_godot = (tmp_path / "overlay" / "project.godot").read_text(encoding="utf-8")
    assert 'mm_live="*res://addons/mm_live/live_server.gd"' in project_godot
    assert (tmp_path / "overlay" / "addons" / "mm_live" / "live_server.gd").read_text(
        encoding="utf-8") == "extends Node\n# v1"
    # steam_appid.txt gotcha: must survive the whole-checkout copy or MM
    # self-relaunches and exits (see CLAUDE.md).
    assert (tmp_path / "overlay" / "steam_appid.txt").read_text(encoding="utf-8") == "4110830"
    assert (tmp_path / "overlay" / "material_maker" / "globals.gd").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: FAIL — `ensure_overlay` not defined.

- [ ] **Step 3: Write minimal implementation**

```python
# src/mm_mcp/overlay.py (append)
import shutil


def ensure_overlay(mm_project_path: str, addon_path: str, overlay_dir: str) -> str:
    """Build or refresh a disposable working copy of a Material Maker project
    checkout with the live-control addon layered in and registered as a
    Godot autoload. Pure filesystem work; never launches Godot.

    Rebuilds when overlay_dir doesn't exist yet, when addon_path's contents
    changed since the last build, or when mm_project_path differs from what
    this overlay_dir was last built from. Otherwise a fast no-op returning
    the existing overlay_dir unchanged (see Task 5).
    """
    mm_project_path = os.path.abspath(mm_project_path)
    addon_path = os.path.abspath(addon_path)
    addon_hash = _hash_dir(addon_path)

    if os.path.isdir(overlay_dir) and not _is_stale(overlay_dir, addon_hash, mm_project_path):
        return overlay_dir

    if os.path.isdir(overlay_dir):
        shutil.rmtree(overlay_dir)
    shutil.copytree(mm_project_path, overlay_dir)

    addon_name = os.path.basename(os.path.normpath(addon_path))
    shutil.copytree(addon_path, os.path.join(overlay_dir, "addons", addon_name))
    _append_autoload(os.path.join(overlay_dir, "project.godot"), addon_name)
    _write_marker(overlay_dir, addon_hash, mm_project_path)
    return overlay_dir
```

Move `import shutil` to the top of the file with the other imports.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/overlay.py tests/test_overlay.py
git commit -m "feat(overlay): ensure_overlay first-build path"
```

---

### Task 5: `ensure_overlay` — no-op and rebuild-on-change

**Files:**
- Modify: `tests/test_overlay.py` (no production code changes; this task
  proves behavior Task 4's implementation already provides)

**Interfaces:**
- Consumes: `ensure_overlay` (Task 4), `fake_checkout`/`fake_addon` fixtures
  (Task 4).
- Produces: nothing new — this task is the spec's remaining two required
  behaviors ("no-op on unchanged inputs", "rebuild-on-addon-change",
  "rebuild-on-checkout-change").

A canary file proves rebuild-vs-no-op without mocking: `_build overlay`
always does `rmtree` + `copytree`, so a file placed directly in `overlay_dir`
after the first build survives a no-op call and is destroyed by a rebuild.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_overlay.py (append)
def test_ensure_overlay_is_noop_when_nothing_changed(tmp_path, fake_checkout, fake_addon):
    overlay_dir = str(tmp_path / "overlay")
    ensure_overlay(str(fake_checkout), str(fake_addon), overlay_dir)

    canary = tmp_path / "overlay" / "CANARY"
    canary.write_text("still here?", encoding="utf-8")

    ensure_overlay(str(fake_checkout), str(fake_addon), overlay_dir)

    assert canary.exists()


def test_ensure_overlay_rebuilds_on_addon_change(tmp_path, fake_checkout, fake_addon):
    overlay_dir = str(tmp_path / "overlay")
    ensure_overlay(str(fake_checkout), str(fake_addon), overlay_dir)

    canary = tmp_path / "overlay" / "CANARY"
    canary.write_text("still here?", encoding="utf-8")
    _write(str(fake_addon), "live_server.gd", "extends Node\n# v2, changed")

    ensure_overlay(str(fake_checkout), str(fake_addon), overlay_dir)

    assert not canary.exists()
    rebuilt = (tmp_path / "overlay" / "addons" / "mm_live" / "live_server.gd").read_text(
        encoding="utf-8")
    assert rebuilt == "extends Node\n# v2, changed"


def test_ensure_overlay_rebuilds_on_checkout_path_change(tmp_path, fake_checkout, fake_addon):
    overlay_dir = str(tmp_path / "overlay")
    ensure_overlay(str(fake_checkout), str(fake_addon), overlay_dir)

    canary = tmp_path / "overlay" / "CANARY"
    canary.write_text("still here?", encoding="utf-8")

    other_checkout = tmp_path / "other_mm_checkout"
    other_checkout.mkdir()
    _write(str(other_checkout), "project.godot", _FAKE_PROJECT_GODOT)
    _write(str(other_checkout), "steam_appid.txt", "4110830")
    _write(str(other_checkout), "material_maker/globals.gd", "# different checkout")

    ensure_overlay(str(other_checkout), str(fake_addon), overlay_dir)

    assert not canary.exists()
    assert (tmp_path / "overlay" / "material_maker" / "globals.gd").read_text(
        encoding="utf-8") == "# different checkout"
```

- [ ] **Step 2: Run tests to verify they fail or pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: all 13 pass immediately — Task 4's implementation already provides
this behavior. This task's job is proving it with dedicated tests, per the
spec's explicit Testing section requirement to cover these cases separately.
If any fails, the bug is in Task 4's `ensure_overlay`, not a missing feature.

- [ ] **Step 3: (implementation)**

No production code change needed. If Step 2 revealed a failure, fix
`ensure_overlay` in `src/mm_mcp/overlay.py` directly (most likely cause: the
staleness check or the rmtree/copytree ordering).

- [ ] **Step 4: Run the full test file one more time**

Run: `.venv\Scripts\python.exe -m pytest tests/test_overlay.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_overlay.py
git commit -m "test(overlay): cover no-op and rebuild-on-change behavior"
```

---

## Gate (matches the spec's step-1 gate)

Run the full fast suite to confirm nothing else broke, then manually inspect
a built overlay:

```bash
.venv\Scripts\python.exe -m pytest -q -m "not integration"
```

Expected: all previously-passing tests plus the 13 new `test_overlay.py`
tests green (122 total, up from 109).

Manual inspection (mirrors the spec's stated gate: "manual inspection of a
built overlay directory shows the autoload line present and addon files
copied"):

```bash
.venv\Scripts\python.exe -c "
from mm_mcp.overlay import ensure_overlay
p = ensure_overlay(
    r'C:\Projects-local\z-Git\material-maker',
    r'C:\Projects-local\Tool-MaterialMaker-MCP\addons\mm_live',  # not created by this plan
    r'C:\Projects-local\Tool-MaterialMaker-MCP\output\mm_live_overlay')
print(p)
"
```

Note: this manual check needs a real `addons/mm_live/` directory with a
`live_server.gd` in it, which does not exist in the repo yet (tonight's spike
version lived only in scratchpad). Either point the manual check at a copy of
the scratchpad addon, or defer this exact manual run to Task/Step 2 of the
spec's sub-plan (Addon skeleton), when the addon is committed for real. The
automated test suite's coverage (fake checkout + fake addon fixtures) is the
actual correctness gate for this plan; the manual run is a sanity spot-check
once a real addon exists.

## Explicitly out of scope for this plan

- The real `addons/mm_live/live_server.gd` addon script (spec sub-plan step 2).
- `live.py` (session manager: process launch, port probing, socket client) —
  spec sub-plan steps 2-3. `overlay_dir`'s default location (e.g. under
  `cfg.output_dir`) is `live.py`'s decision to make when it's built; this
  plan keeps `overlay_dir` an explicit caller-supplied parameter so the
  module has zero `Config` dependency and stays fully unit-testable.
- Any MCP tool surface (`server.py` changes) — spec sub-plan step 4.
