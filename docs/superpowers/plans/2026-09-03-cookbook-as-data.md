# Cookbook as Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the 43 authored cookbook graphs from gitignored build output to a tracked `cookbook/` tree that the MCP server's `list_examples` / `load_example` can see alongside Material Maker's bundled examples.

**Architecture:** A promote script copies each builder's `v1.ptex` into `cookbook/<category>/<id>.ptex` (and can diff against it, which is the regression baseline). A small `mm_mcp.cookbook` module walks that tree; `Config` learns `cookbook_dir`; `server.py`'s two example tools become dual-source; the doctor reports the cookbook; a gate test validates every tracked graph in the fast suite.

**Tech Stack:** Python 3.13, pytest, the existing `mm_mcp` catalog/validator, PIL (already in the venv) for the contact sheet.

**Spec:** `docs/superpowers/specs/2026-09-03-cookbook-as-data-design.md`

## Global Constraints

- Shell on this machine is PowerShell 5.1: sequence with `;`, never `&&`. Python is `.venv\Scripts\python.exe` from the repo root (`C:\Projects-local\Tool-MaterialMaker-MCP`).
- Run tests as `.venv\Scripts\python.exe -m pytest -q -m "not integration"`. Baseline before this plan: 262 passed.
- Never drive a Godot render from `python -c`; use a script file.
- Validation errors are returned as data (`{"ok": False, "error": ...}`), never raised, so the assistant can self-correct.
- No em dashes in any prose, docstring, or doc you write. Use a colon, comma, or period.
- Conventional commit messages (`feat:`, `test:`, `docs:`); release-please reads them.
- Do not edit `HANDOFF.md` or `STATUS.md`; the orchestrator's wrap-up owns those.
- `quality/authored/` and `quality/cookbook/` stay gitignored.

---

## Phase A: the tracked tree and its gate

### Task 1: `quality/promote_cookbook.py` and the tracked `cookbook/` tree

**Files:**
- Create: `quality/promote_cookbook.py`
- Create: `tests/test_promote_cookbook.py`
- Create: `cookbook/<category>/<id>.ptex` (43 files, produced by running the script)
- Modify: `.gitignore:26-32` (comment only)

**Interfaces:**
- Produces: `promote(authored_root: Path, cookbook_root: Path, check: bool = False, labels: list[str] | None = None) -> list[str]` (list of problem strings, empty means clean). CLI: `python quality/promote_cookbook.py [--check] [cookbook-<label> ...]`, exit 0 when clean, 1 otherwise.
- Produces: the on-disk layout `cookbook/<category>/<id>.ptex` that Tasks 2 and 3 read. `category` is the authored label minus the `cookbook-` prefix.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_promote_cookbook.py
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "quality"))

from promote_cookbook import promote  # noqa: E402


def _authored(tmp_path: Path, label: str, case: str, payload: dict) -> Path:
    d = tmp_path / "authored" / label / case
    d.mkdir(parents=True)
    p = d / "v1.ptex"
    p.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return p


def test_promote_copies_v1_into_category_dir(tmp_path):
    src = _authored(tmp_path, "cookbook-fabrics", "f07_herringbone_tweed", {"type": "graph"})
    problems = promote(tmp_path / "authored", tmp_path / "cookbook")
    assert problems == []
    dst = tmp_path / "cookbook" / "fabrics" / "f07_herringbone_tweed.ptex"
    assert dst.read_bytes() == src.read_bytes()


def test_promote_reports_case_without_v1(tmp_path):
    (tmp_path / "authored" / "cookbook-wood" / "w09_empty").mkdir(parents=True)
    problems = promote(tmp_path / "authored", tmp_path / "cookbook")
    assert len(problems) == 1
    assert "w09_empty" in problems[0]


def test_check_mode_reports_missing_and_differing(tmp_path):
    _authored(tmp_path, "cookbook-stone", "s11_marble", {"type": "graph", "v": 2})
    _authored(tmp_path, "cookbook-stone", "s10_flagstone", {"type": "graph"})
    tracked = tmp_path / "cookbook" / "stone"
    tracked.mkdir(parents=True)
    (tracked / "s11_marble.ptex").write_text(json.dumps({"type": "graph", "v": 1}, indent=1),
                                             encoding="utf-8")
    problems = promote(tmp_path / "authored", tmp_path / "cookbook", check=True)
    assert any("s11_marble" in p and "differs" in p for p in problems)
    assert any("s10_flagstone" in p and "missing" in p for p in problems)
    assert not (tracked / "s10_flagstone.ptex").exists(), "check mode must not write"


def test_check_mode_is_clean_after_promote(tmp_path):
    _authored(tmp_path, "cookbook-terrain", "t05_cracked_ice", {"type": "graph"})
    assert promote(tmp_path / "authored", tmp_path / "cookbook") == []
    assert promote(tmp_path / "authored", tmp_path / "cookbook", check=True) == []


def test_labels_filter_limits_scope(tmp_path):
    _authored(tmp_path, "cookbook-wood", "w05_dark_walnut", {"type": "graph"})
    _authored(tmp_path, "cookbook-scifi", "sf01_hull_plating", {"type": "graph"})
    promote(tmp_path / "authored", tmp_path / "cookbook", labels=["cookbook-wood"])
    assert (tmp_path / "cookbook" / "wood" / "w05_dark_walnut.ptex").exists()
    assert not (tmp_path / "cookbook" / "scifi").exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_promote_cookbook.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'promote_cookbook'`

- [ ] **Step 3: Write the script**

```python
# quality/promote_cookbook.py
"""Promote locked cookbook graphs into the tracked cookbook/ tree.

    quality/authored/cookbook-<category>/<id>/v1.ptex  ->  cookbook/<category>/<id>.ptex

quality/authored/ is gitignored build output from the cookbook_*.py builders.
cookbook/ is the tracked, shipped copy the MCP server serves through
list_examples / load_example and that a person can open in Material Maker.

Usage (from the repo root):
  .venv\\Scripts\\python.exe quality\\promote_cookbook.py                 # copy every category
  .venv\\Scripts\\python.exe quality\\promote_cookbook.py cookbook-stone  # one label
  .venv\\Scripts\\python.exe quality\\promote_cookbook.py --check         # diff, do not write

--check is the regression baseline: rebuild with the builders, then --check.
Any tracked file that is missing or differs from its authored v1.ptex is
reported and the exit code is 1. Run without --check to accept the new output.
"""
import filecmp
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
AUTHORED = _ROOT / "quality" / "authored"
COOKBOOK = _ROOT / "cookbook"
PREFIX = "cookbook-"


def promote(authored_root: Path, cookbook_root: Path, check: bool = False,
            labels: list[str] | None = None) -> list[str]:
    """Copy (or, with check=True, compare) every cookbook-*/<id>/v1.ptex.
    Returns a list of problem strings; empty means clean."""
    problems: list[str] = []
    label_dirs = sorted(d for d in authored_root.glob(PREFIX + "*") if d.is_dir())
    if labels:
        label_dirs = [d for d in label_dirs if d.name in labels]
    for label_dir in label_dirs:
        category = label_dir.name[len(PREFIX):]
        for case_dir in sorted(p for p in label_dir.iterdir() if p.is_dir()):
            src = case_dir / "v1.ptex"
            if not src.is_file():
                problems.append(f"{case_dir}: no v1.ptex to promote")
                continue
            dst = cookbook_root / category / f"{case_dir.name}.ptex"
            if check:
                if not dst.is_file():
                    problems.append(f"{dst}: missing (run promote_cookbook.py to add it)")
                elif not filecmp.cmp(src, dst, shallow=False):
                    problems.append(f"{dst}: differs from {src}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
    return problems


def main(argv: list[str]) -> int:
    check = "--check" in argv
    labels = [a for a in argv if a != "--check"] or None
    problems = promote(AUTHORED, COOKBOOK, check=check, labels=labels)
    for p in problems:
        print(p)
    if problems:
        print(f"{len(problems)} problem(s)")
        return 1
    print("cookbook/ is " + ("in sync with quality/authored/" if check else "updated"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_promote_cookbook.py -q`
Expected: 5 passed

- [ ] **Step 5: Run the script for real and inspect the tree**

Run: `.venv\Scripts\python.exe quality\promote_cookbook.py; .venv\Scripts\python.exe quality\promote_cookbook.py --check`
Expected: first prints `cookbook/ is updated`, second prints `cookbook/ is in sync with quality/authored/`, both exit 0.

Run: `Get-ChildItem cookbook -Recurse -Filter *.ptex | Measure-Object`
Expected: `Count : 43`, spread over `fabrics` (5), `leather` (6), `organics` (4), `painted-metal` (5), `scifi` (4), `stone` (8), `terrain` (8), `wood` (3).

- [ ] **Step 6: Update the .gitignore comment**

Replace lines 25-28 of `.gitignore` (the `# Phase 3 quality:` block through `quality/authored/`) with:

```
# Phase 3 quality: keep test_set + scorecards; ignore heavy renders and the
# authored .ptex variants (author.py regenerates them deterministically).
# The locked cookbook graphs are promoted from quality/authored/cookbook-*/
# into the tracked cookbook/ tree by quality/promote_cookbook.py.
quality/runs/
quality/authored/
```

- [ ] **Step 7: Commit**

```
git add quality/promote_cookbook.py tests/test_promote_cookbook.py cookbook .gitignore
git commit -m "feat(cookbook): promote the 43 authored graphs into a tracked cookbook/ tree"
```

---

### Task 2: `mm_mcp.cookbook` lookup module

**Files:**
- Create: `src/mm_mcp/cookbook.py`
- Create: `tests/test_cookbook.py`

**Interfaces:**
- Produces: `CookbookEntry` (frozen dataclass: `name: str`, `category: str`, `path: str`); `list_cookbook(cookbook_dir: str) -> list[CookbookEntry]` sorted by `(category, name)`, empty list when `cookbook_dir` is empty or not a directory; `find_cookbook(cookbook_dir: str, name: str) -> CookbookEntry | None`.
- Consumed by Tasks 3, 5, 6.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cookbook.py
import os
from mm_mcp.cookbook import CookbookEntry, list_cookbook, find_cookbook


def _make(tmp_path, category, name):
    d = tmp_path / category
    d.mkdir(exist_ok=True)
    p = d / f"{name}.ptex"
    p.write_text('{"type": "graph"}', encoding="utf-8")
    return str(p)


def test_list_cookbook_walks_category_dirs_sorted(tmp_path):
    p_wood = _make(tmp_path, "wood", "w05_dark_walnut")
    p_fab = _make(tmp_path, "fabrics", "f07_herringbone_tweed")
    entries = list_cookbook(str(tmp_path))
    assert entries == [
        CookbookEntry(name="f07_herringbone_tweed", category="fabrics", path=p_fab),
        CookbookEntry(name="w05_dark_walnut", category="wood", path=p_wood),
    ]


def test_list_cookbook_ignores_non_ptex_and_top_level_files(tmp_path):
    _make(tmp_path, "stone", "s11_marble")
    (tmp_path / "stone" / "README.md").write_text("x", encoding="utf-8")
    (tmp_path / "stray.ptex").write_text("{}", encoding="utf-8")
    assert [e.name for e in list_cookbook(str(tmp_path))] == ["s11_marble"]


def test_list_cookbook_empty_when_dir_missing_or_unset(tmp_path):
    assert list_cookbook("") == []
    assert list_cookbook(str(tmp_path / "nope")) == []


def test_find_cookbook_returns_entry_or_none(tmp_path):
    p = _make(tmp_path, "terrain", "t05_cracked_ice")
    found = find_cookbook(str(tmp_path), "t05_cracked_ice")
    assert found is not None and found.path == p and found.category == "terrain"
    assert find_cookbook(str(tmp_path), "no_such_thing") is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_cookbook.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'mm_mcp.cookbook'`

- [ ] **Step 3: Write the module**

```python
# src/mm_mcp/cookbook.py
"""Lookup for the tracked cookbook: <cookbook_dir>/<category>/<id>.ptex.

These are graphs this project authored (see quality/cookbook_*.py and
docs/AUTHORING.md), promoted into the repo by quality/promote_cookbook.py.
The server serves them next to Material Maker's own bundled examples so an
assistant can start from the nearest cookbook graph, and a person can open
the same file in Material Maker.
"""
import glob
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CookbookEntry:
    name: str
    category: str
    path: str


def list_cookbook(cookbook_dir: str) -> list[CookbookEntry]:
    """Every <category>/<id>.ptex under cookbook_dir, sorted by (category, name).
    Empty list when cookbook_dir is unset or not a directory."""
    if not cookbook_dir or not os.path.isdir(cookbook_dir):
        return []
    entries = []
    for path in glob.glob(os.path.join(cookbook_dir, "*", "*.ptex")):
        entries.append(CookbookEntry(
            name=os.path.splitext(os.path.basename(path))[0],
            category=os.path.basename(os.path.dirname(path)),
            path=path,
        ))
    return sorted(entries, key=lambda e: (e.category, e.name))


def find_cookbook(cookbook_dir: str, name: str) -> CookbookEntry | None:
    """The entry whose id is `name`, or None."""
    for entry in list_cookbook(cookbook_dir):
        if entry.name == name:
            return entry
    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_cookbook.py -q`
Expected: 4 passed

- [ ] **Step 5: Commit**

```
git add src/mm_mcp/cookbook.py tests/test_cookbook.py
git commit -m "feat: add mm_mcp.cookbook lookup for the tracked cookbook/ tree"
```

---

### Task 3: the cookbook gate test

**Files:**
- Create: `tests/test_cookbook_gate.py`

**Interfaces:**
- Consumes: `mm_mcp.cookbook.list_cookbook` (Task 2), the `cookbook/` tree (Task 1), `validate_graph` and `build_catalog` as used by `tests/test_examples_gate.py`.

- [ ] **Step 1: Write the gate test**

```python
# tests/test_cookbook_gate.py
"""Phase A gate for cookbook-as-data: every tracked cookbook graph validates
against the catalog with zero hard errors, ids are unique across categories,
and every graph has its thumbnail. Mirrors tests/test_examples_gate.py."""
import json
import os
import pytest
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.cookbook import list_cookbook
from mm_mcp.validator import validate_graph

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKBOOK_DIR = os.path.join(_ROOT, "cookbook")
ENTRIES = list_cookbook(COOKBOOK_DIR)
cfg = load_config()
CATALOG = build_catalog(cfg.nodes_dir)


def _all_graphs(node):
    """Yield the node itself and every nested subgraph (has a 'nodes' list)."""
    if isinstance(node, dict) and "nodes" in node:
        yield node
        for child in node["nodes"]:
            yield from _all_graphs(child)


def test_cookbook_is_populated():
    assert len(ENTRIES) >= 43, f"expected the 43 promoted graphs, found {len(ENTRIES)}"


def test_cookbook_ids_are_unique_across_categories():
    names = [e.name for e in ENTRIES]
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert dupes == []


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_cookbook_graph_has_no_type_or_connection_errors(entry):
    with open(entry.path, encoding="utf-8") as fh:
        root = json.load(fh)
    hard_errors = []
    for g in _all_graphs(root):
        for p in validate_graph(g, CATALOG):
            if p["severity"] == "error":
                hard_errors.append(p["message"])
    assert hard_errors == [], f"{entry.name}: {hard_errors[:5]}"


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_cookbook_graph_has_thumbnail(entry):
    thumb = os.path.join(_ROOT, "docs", "images", f"cookbook-{entry.category}",
                         f"{entry.name}.png")
    assert os.path.isfile(thumb), f"missing thumbnail {thumb}"
```

- [ ] **Step 2: Run it**

Run: `.venv\Scripts\python.exe -m pytest tests/test_cookbook_gate.py -q`
Expected: 88 passed (2 + 43 + 43). If any `validate` case fails, stop and report the failing id and message to the orchestrator; do not edit the `.ptex`.

- [ ] **Step 3: Run the full fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: 359 passed (262 baseline + 5 + 4 + 88), 23 deselected.

- [ ] **Step 4: Commit**

```
git add tests/test_cookbook_gate.py
git commit -m "test(cookbook): gate every tracked cookbook graph on catalog validation"
```

**Phase A gate (orchestrator runs after Task 3):** `pytest tests/test_cookbook_gate.py` green and `promote_cookbook.py --check` exit 0. Record in STATUS.md at wrap-up.

---

## Phase B: the server sees the cookbook

### Task 4: `Config.cookbook_dir` and `MM_COOKBOOK_DIR`

**Files:**
- Modify: `src/mm_mcp/config.py` (the `_DEFAULTS` dict at lines 12-18, the `Config` dataclass at lines 28-37, `load_config` at lines 75-96)
- Modify: `tests/test_config.py` (append tests)

**Interfaces:**
- Produces: `Config.cookbook_dir: str`. Resolution order: `MM_COOKBOOK_DIR` (env, `.env`, or `overrides`) if set; else `<repo>/cookbook` computed from the package's own location when that directory exists; else `""`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_config.py`:

```python
def test_cookbook_dir_defaults_to_repo_cookbook_when_present():
    cfg = load_config()
    assert cfg.cookbook_dir.endswith("cookbook")
    assert os.path.isdir(cfg.cookbook_dir)


def test_cookbook_dir_override_wins(tmp_path):
    cfg = load_config(overrides={"MM_COOKBOOK_DIR": str(tmp_path)})
    assert cfg.cookbook_dir == str(tmp_path)


def test_cookbook_dir_env_var_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("MM_COOKBOOK_DIR", str(tmp_path))
    assert load_config().cookbook_dir == str(tmp_path)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config.py -q`
Expected: 3 new failures with `AttributeError: 'Config' object has no attribute 'cookbook_dir'`

- [ ] **Step 3: Implement**

In `src/mm_mcp/config.py`:

Add to `_DEFAULTS`:
```python
    "MM_COOKBOOK_DIR": "",
```

Add a field to `Config` after `allowed_roots` (last field, with a default, so nothing that builds a `Config` by hand breaks):
```python
    cookbook_dir: str = ""
```

Add this helper above `load_config`:
```python
def _default_cookbook_dir() -> str:
    """<repo>/cookbook when running from a source checkout (this file is
    src/mm_mcp/config.py, so three dirname hops up is the repo root). Empty
    when that directory does not exist, e.g. an installed wheel, which does
    not package the cookbook; the example tools then serve only Material
    Maker's bundled examples."""
    here = os.path.abspath(__file__)
    repo = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    candidate = os.path.join(repo, "cookbook")
    return candidate if os.path.isdir(candidate) else ""
```

In `load_config`, before the `return Config(...)`:
```python
    cookbook_dir = env["MM_COOKBOOK_DIR"] or _default_cookbook_dir()
```
and add `cookbook_dir=cookbook_dir,` to the `Config(...)` call.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config.py -q`
Expected: 15 passed

- [ ] **Step 5: Commit**

```
git add src/mm_mcp/config.py tests/test_config.py
git commit -m "feat(config): add cookbook_dir (MM_COOKBOOK_DIR, defaults to the checkout's cookbook/)"
```

---

### Task 5: dual-source `list_examples` and `load_example`

**Files:**
- Modify: `src/mm_mcp/server.py:198-206` (`list_examples`, `load_example`) plus the import block at lines 1-16
- Modify: `tests/test_server_tools.py:35-39` (`test_list_and_load_example`) and append new tests
- Check, do not modify: `smoke/smoke_mcp.py:11` still works (`load_example("bricks")` returns the graph dict).

**Interfaces:**
- Consumes: `Config.cookbook_dir` (Task 4), `list_cookbook` / `find_cookbook` (Task 2).
- Produces: `list_examples(source: str = "all") -> dict` returning `{"ok": True, "examples": [{"name": str, "source": "material_maker" | "cookbook", "category": str | None}, ...]}` or `{"ok": False, "error": str}`. `load_example(name: str, source: str = "auto") -> dict` returning the raw graph on success or `{"ok": False, "error": str}`.

- [ ] **Step 1: Update the existing test and add the new ones**

Replace `test_list_and_load_example` in `tests/test_server_tools.py` with:

```python
def test_list_and_load_example():
    res = server.list_examples()
    assert res["ok"] is True
    names = [e["name"] for e in res["examples"]]
    assert "bricks" in names
    d = server.load_example("bricks")
    assert d["type"] == "graph"


def test_list_examples_tags_both_sources():
    res = server.list_examples()
    by_source = {}
    for e in res["examples"]:
        by_source.setdefault(e["source"], []).append(e)
    assert "bricks" in [e["name"] for e in by_source["material_maker"]]
    cookbook_names = [e["name"] for e in by_source["cookbook"]]
    assert "f07_herringbone_tweed" in cookbook_names
    tweed = next(e for e in by_source["cookbook"] if e["name"] == "f07_herringbone_tweed")
    assert tweed["category"] == "fabrics"
    assert all(e["category"] is None for e in by_source["material_maker"])


def test_list_examples_source_filter():
    only_cookbook = server.list_examples(source="cookbook")["examples"]
    assert only_cookbook and all(e["source"] == "cookbook" for e in only_cookbook)
    only_mm = server.list_examples(source="material_maker")["examples"]
    assert only_mm and all(e["source"] == "material_maker" for e in only_mm)


def test_list_examples_unknown_source_is_data_not_exception():
    res = server.list_examples(source="nope")
    assert res["ok"] is False and "nope" in res["error"]


def test_load_example_finds_cookbook_graph_by_default():
    d = server.load_example("f07_herringbone_tweed")
    assert d["type"] == "graph"
    assert any(n.get("type") == "weave2" for n in d["nodes"])


def test_load_example_source_restricts_lookup():
    res = server.load_example("f07_herringbone_tweed", source="material_maker")
    assert res["ok"] is False
    res = server.load_example("bricks", source="cookbook")
    assert res["ok"] is False


def test_load_example_unknown_name_is_data_not_exception():
    res = server.load_example("no_such_material_anywhere")
    assert res["ok"] is False and "no_such_material_anywhere" in res["error"]


def test_load_example_unknown_source_is_data_not_exception():
    res = server.load_example("bricks", source="nope")
    assert res["ok"] is False and "nope" in res["error"]


def test_list_examples_without_cookbook_dir_serves_only_bundled(monkeypatch):
    monkeypatch.setenv("MM_COOKBOOK_DIR", os.path.join(os.getcwd(), "no-such-cookbook-dir"))
    server._reset()
    try:
        res = server.list_examples()
        assert res["ok"] is True
        assert all(e["source"] == "material_maker" for e in res["examples"])
    finally:
        monkeypatch.delenv("MM_COOKBOOK_DIR", raising=False)
        server._reset()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_tools.py -q`
Expected: the updated `test_list_and_load_example` fails with `TypeError: list indices must be integers` (list_examples still returns a list) and the new tests fail.

- [ ] **Step 3: Implement**

In `src/mm_mcp/server.py`, add to the imports:
```python
from mm_mcp.cookbook import list_cookbook, find_cookbook
```

Replace the existing `list_examples` and `load_example` (lines 198-206) with:

```python
_EXAMPLE_SOURCES = ("material_maker", "cookbook")


def _bundled_examples(cfg) -> list[dict]:
    return [{"name": os.path.splitext(os.path.basename(p))[0],
             "source": "material_maker", "category": None}
            for p in sorted(glob.glob(os.path.join(cfg.examples_dir, "*.ptex")))]


def list_examples(source: str = "all") -> dict:
    """Starting graphs from two sources: Material Maker's bundled examples
    (`material_maker`) and this repo's tracked cookbook of authored materials
    (`cookbook`, see cookbook/ and docs/AUTHORING.md). `source` is `all`,
    `material_maker`, or `cookbook`. Returns {"ok": True, "examples": [
    {"name", "source", "category"}]}; `category` is None for bundled
    examples. Prefer a cookbook graph as the starting pattern when one is
    close to the prompt: it already encodes a recipe that rendered well."""
    if source not in ("all",) + _EXAMPLE_SOURCES:
        return {"ok": False, "error": f"unknown source '{source}'; expected one of: "
                                      f"all, {', '.join(_EXAMPLE_SOURCES)}"}
    cfg, _ = _ensure_ready()
    examples: list[dict] = []
    if source in ("all", "material_maker"):
        examples += _bundled_examples(cfg)
    if source in ("all", "cookbook"):
        examples += [{"name": e.name, "source": "cookbook", "category": e.category}
                     for e in list_cookbook(cfg.cookbook_dir)]
    return {"ok": True, "examples": examples}


def load_example(name: str, source: str = "auto") -> dict:
    """Load one starting graph by name as a .ptex dict. `source` is `auto`
    (cookbook first, then bundled), `material_maker`, or `cookbook`. Unknown
    name or source returns {"ok": False, "error": ...} as data."""
    if source not in ("auto",) + _EXAMPLE_SOURCES:
        return {"ok": False, "error": f"unknown source '{source}'; expected one of: "
                                      f"auto, {', '.join(_EXAMPLE_SOURCES)}"}
    cfg, _ = _ensure_ready()
    try:
        name = reject_path_fragment(name)
    except PathNotAllowed as exc:
        return {"ok": False, "error": str(exc)}
    path = None
    if source in ("auto", "cookbook"):
        entry = find_cookbook(cfg.cookbook_dir, name)
        if entry is not None:
            path = entry.path
    if path is None and source in ("auto", "material_maker"):
        candidate = os.path.join(cfg.examples_dir, name + ".ptex")
        if os.path.isfile(candidate):
            path = candidate
    if path is None:
        return {"ok": False, "error": f"no example named '{name}' (source={source}); "
                                      "call list_examples to see what exists"}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_tools.py -q`
Expected: 32 passed (24 before, 1 rewritten, 8 added)

- [ ] **Step 5: Run the smoke and the full fast suite**

Run: `.venv\Scripts\python.exe smoke\smoke_mcp.py`
Expected: `SMOKE PASS: rendered 4 image(s)`, exit 0 (this launches Godot once, about 10 seconds).

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: 370 passed, 23 deselected (359 after Task 3, +3 from Task 4, +8 here).

- [ ] **Step 6: Commit**

```
git add src/mm_mcp/server.py tests/test_server_tools.py
git commit -m "feat!: list_examples/load_example serve the tracked cookbook alongside bundled examples"
```

(The `!` marks the return-shape change of `list_examples`; release-please will bump the minor version, which is right for a 0.x breaking change.)

---

### Task 6: doctor reports the cookbook

**Files:**
- Modify: `src/mm_mcp/doctor.py` (insert after the `examples` check, lines 45-48; add an import)
- Modify: `tests/test_doctor.py` (append tests)

**Interfaces:**
- Consumes: `Config.cookbook_dir` (Task 4), `list_cookbook` (Task 2).
- Produces: a `Check("cookbook", True, ...)` line in `mm-mcp --check`. Never a failing check.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_doctor.py`:

```python
def test_check_setup_reports_cookbook_count():
    cookbook = next(c for c in check_setup(load_config()) if c.name == "cookbook")
    assert cookbook.ok
    assert "43" in cookbook.detail or "materials" in cookbook.detail


def test_check_setup_cookbook_missing_is_informational_not_failing(tmp_path):
    cfg = load_config(overrides={"MM_COOKBOOK_DIR": str(tmp_path / "nope")})
    cookbook = next(c for c in check_setup(cfg) if c.name == "cookbook")
    assert cookbook.ok
    assert "not found" in cookbook.detail
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_doctor.py -q`
Expected: 2 failures with `StopIteration` (no check named `cookbook`).

- [ ] **Step 3: Implement**

In `src/mm_mcp/doctor.py`, add to the imports:
```python
from mm_mcp.cookbook import list_cookbook
```

Insert directly after the `examples` check block (after the line `checks.append(Check("examples", False, f"missing: '{cfg.examples_dir}'"))`):
```python
    if cfg.cookbook_dir and os.path.isdir(cfg.cookbook_dir):
        n = len(list_cookbook(cfg.cookbook_dir))
        checks.append(Check("cookbook", True, f"{n} materials in '{cfg.cookbook_dir}'"))
    else:
        checks.append(Check("cookbook", True,
                            "not found (optional: cookbook/ ships with the git checkout; "
                            "set MM_COOKBOOK_DIR to point at one)"))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_doctor.py -q`
Expected: 15 passed

Run: `.venv\Scripts\mm-mcp.exe --check`
Expected: a `[PASS] cookbook: 43 materials in '...cookbook'` line among the checks, exit 0.

- [ ] **Step 5: Commit**

```
git add src/mm_mcp/doctor.py tests/test_doctor.py
git commit -m "feat(doctor): report the cookbook directory and material count"
```

**Phase B gate (orchestrator runs after Task 6):** fast suite green, and a one-off script file renders `load_example("f07_herringbone_tweed")` through `render_graph` and produces 4 PNGs. Record in STATUS.md at wrap-up.

---

## Phase C: the docs tell the truth

### Task 7: README, cookbook/README, quality/README, AUTHORING, contact sheet

**Files:**
- Modify: `README.md:62-77` (Material cookbook section) and `README.md:224-225` (tool table rows)
- Create: `cookbook/README.md`
- Modify: `quality/README.md` (the "Cookbook growth" section)
- Modify: `docs/AUTHORING.md:44-45` (workflow step 1)
- Regenerate: `docs/images/cookbook-contact-sheet.png` (43 tiles)

**Interfaces:**
- Consumes: the tool signatures from Task 5 and the `promote_cookbook.py` CLI from Task 1. No code.

- [ ] **Step 1: Regenerate the contact sheet at 43 materials**

Run: `.venv\Scripts\python.exe quality\contact_sheet.py`
Expected: `wrote ...docs\images\contact-sheet-fabrics-leather-organics-painted-metal-scifi-stone-terrain-wood.png (43 tiles, 3x15)`

Then replace the tracked sheet with it and drop the intermediate:
```
Move-Item -Force docs\images\contact-sheet-fabrics-leather-organics-painted-metal-scifi-stone-terrain-wood.png docs\images\cookbook-contact-sheet.png
```
Confirm: `Get-Item docs\images\cookbook-contact-sheet.png` shows a fresh timestamp, and `git status --short docs/images` shows exactly one modified file.

- [ ] **Step 2: Rewrite the README cookbook section**

Replace lines 62-77 of `README.md` (from `## Material cookbook` through the closing `</details>`) with:

```markdown
## Material cookbook

Beyond the frozen gallery above, the cookbook is 43 more materials across
eight categories, each one a real graph this server authored and then locked
after a 3D-preview pass. Every one ships as a tracked `.ptex` under
[`cookbook/`](cookbook/): open `cookbook/<category>/<id>.ptex` in Material
Maker to see the node network, or start from it over MCP with
`load_example("f07_herringbone_tweed")`. The recipes and the levers behind them
are in [docs/AUTHORING.md](docs/AUTHORING.md); the builders that regenerate
them live in [`quality/`](quality/).

<details>
<summary><b>Show the cookbook contact sheet</b> (43 materials: fabrics, leather, organics, painted metal, sci-fi, stone, terrain, wood)</summary>

<p align="center">
  <img src="docs/images/cookbook-contact-sheet.png" alt="Contact sheet of 43 cookbook materials across eight categories" width="100%">
</p>

</details>
```

- [ ] **Step 3: Update the README tool table rows**

Replace the two rows at `README.md:224-225`:
```markdown
| `list_examples` | List the bundled Material Maker examples |
| `load_example` | Load a bundled example as a `.ptex` graph |
```
with:
```markdown
| `list_examples` | List starting graphs from both sources: Material Maker's bundled examples and this repo's `cookbook/` (filter with `source`) |
| `load_example` | Load one starting graph by name as a `.ptex` (cookbook first, then bundled) |
```

- [ ] **Step 4: Write `cookbook/README.md`**

```markdown
# cookbook/

Tracked, authored Material Maker graphs: one `.ptex` per material, grouped by
category. These are the shipped form of the cookbook that `quality/cookbook_*.py`
builds and `docs/AUTHORING.md` explains.

## Use

- **In Material Maker:** open any `<category>/<id>.ptex`. The node network is
  the worked example; tweak it, save it somewhere else, keep iterating.
- **Over MCP:** `list_examples(source="cookbook")` lists them with their
  category; `load_example("<id>")` returns the graph. `mm-mcp --check` reports
  how many the server can see.
- **Config:** the server finds this folder automatically from a source
  checkout. Set `MM_COOKBOOK_DIR` to point it somewhere else.

## Regenerate

The builders are the source; this folder is their locked output.

1. Rebuild a category: `.venv\Scripts\python.exe quality\cookbook_<category>.py`
2. Verify nothing drifted: `.venv\Scripts\python.exe quality\promote_cookbook.py --check`
3. Accept new output: `.venv\Scripts\python.exe quality\promote_cookbook.py`

`tests/test_cookbook_gate.py` validates every graph here against the node
catalog and checks that each has a thumbnail under `docs/images/cookbook-<category>/`.
```

- [ ] **Step 5: Update `quality/README.md`**

In the "Cookbook growth" section, after the sentence ending `both output dirs are gitignored (regenerable).`, add a new paragraph:

```markdown
When a material is locked (rendered, 3D-previewed, written up), promote it:
`python quality/promote_cookbook.py` copies each `v1.ptex` into the tracked
`cookbook/<category>/<id>.ptex` tree the MCP server serves through
`list_examples` / `load_example`. `promote_cookbook.py --check` diffs
regenerated output against the tracked copies and exits 1 on any drift, which
is the regression baseline for the informal (non-scorecard) materials.
```

- [ ] **Step 6: Update `docs/AUTHORING.md` workflow step 1**

Replace lines 44-45:
```
1. Read the prompt; pick the closest bundled example(s) with `list_examples` /
   `load_example` as a starting pattern.
```
with:
```
1. Read the prompt; pick the closest starting graph with `list_examples` /
   `load_example`. Two sources: Material Maker's bundled examples and the
   tracked `cookbook/` (`source="cookbook"`). Prefer a cookbook graph when one
   is close, it already encodes a recipe that rendered well.
```

- [ ] **Step 7: Verify the counts match the tree**

Run: `(Get-ChildItem cookbook -Recurse -Filter *.ptex).Count; (Get-ChildItem cookbook -Directory).Count; Select-String -Path README.md -Pattern "43 materials|eight categories" | Measure-Object | Select-Object -ExpandProperty Count`
Expected: `43`, `8`, and at least `2` README matches.

- [ ] **Step 8: Commit**

```
git add README.md cookbook/README.md quality/README.md docs/AUTHORING.md docs/images/cookbook-contact-sheet.png
git commit -m "docs(cookbook): README/AUTHORING describe the tracked cookbook; contact sheet at 43"
```

**Phase C gate (orchestrator):** counts in README match `cookbook/` on disk; push and confirm CI green.
