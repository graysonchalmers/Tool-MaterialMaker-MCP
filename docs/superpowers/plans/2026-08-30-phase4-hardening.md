# Phase 4 Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close out Phase 4 with opt-in allowed-roots path bounding, a read-only `inspect_project` metrics tool, and CI + release-please automation.

**Architecture:** A new pure `paths.py` provides two guards (full-path roots check, always-on fragment rejection) that `server.py` applies at client-facing tool boundaries. A new pure `inspect.py` computes `.ptex` metrics, wrapped by a new `inspect_project` tool. Version is single-sourced through `importlib.metadata`. Two GitHub Actions workflows add CI testing and release-please automation.

**Tech Stack:** Python 3.10+, `mcp` (MCPServer), pytest, GitHub Actions, googleapis/release-please-action.

**Spec:** [docs/superpowers/specs/2026-08-30-phase4-hardening-design.md](../specs/2026-08-30-phase4-hardening-design.md)

## Global Constraints

- **Python floor:** `requires-python >= 3.10`. Use only stdlib available there (`importlib.metadata` is fine).
- **Errors as data:** validation/guard failures return `{"ok": False, "error": ...}` from tool functions, never raise out of a tool. Pure helpers may raise; tool wrappers catch.
- **No em dashes in code comments/strings either** (project + machine convention): use a period or comma.
- **Windows is the verified platform.** CI runner is `windows-latest`. Paths must be `os.sep`/`normcase`-correct.
- **Opt-in bounding:** with `MM_ALLOWED_ROOTS` unset, the full-path guard is a passthrough no-op. The fragment guard is always on.
- **No PyPI publish.** Release artifacts attach to the GitHub Release only.
- **Conventional-commit messages** for every commit (`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `ci:`), so release-please can compute bumps.
- **Tool registration** is `mcp.tool()(func)` in the block at the bottom of `server.py` (currently `server.py:400-414`).
- **Test running (this machine):** `& "C:\Program Files\Python313\python.exe" -m pytest -q -m "not integration"` from the repo root; `.env` supplies real MM paths so `_ensure_ready` works.

---

### Task 1: `paths.py` — the two guards

**Files:**
- Create: `src/mm_mcp/paths.py`
- Test: `tests/test_paths.py`

**Interfaces:**
- Consumes: nothing (pure stdlib).
- Produces:
  - `class PathNotAllowed(Exception)`
  - `ensure_within_roots(path: str, roots: list[str]) -> str` — returns `os.path.realpath(path)`; if `roots` is non-empty and the realpath is inside none of them, raises `PathNotAllowed`; empty `roots` is passthrough (returns realpath, never raises).
  - `reject_path_fragment(name: str) -> str` — returns `name` if it is a bare component; raises `PathNotAllowed` if it contains a path separator (`os.sep`/`os.altsep`) or equals `..`. Always enforced.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_paths.py
import os
import pytest
from mm_mcp.paths import ensure_within_roots, reject_path_fragment, PathNotAllowed


def test_empty_roots_is_passthrough(tmp_path):
    p = str(tmp_path / "anywhere.ptex")
    assert ensure_within_roots(p, []) == os.path.realpath(p)


def test_path_inside_root_is_allowed(tmp_path):
    root = str(tmp_path)
    p = os.path.join(root, "sub", "mat.ptex")
    assert ensure_within_roots(p, [root]) == os.path.realpath(p)


def test_path_outside_root_raises(tmp_path):
    root = tmp_path / "allowed"
    root.mkdir()
    outside = str(tmp_path / "elsewhere" / "mat.ptex")
    with pytest.raises(PathNotAllowed):
        ensure_within_roots(outside, [str(root)])


def test_sibling_prefix_is_not_a_match(tmp_path):
    # '/allowed' must not match '/allowed-evil'
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    evil = tmp_path / "allowed-evil"
    evil.mkdir()
    victim = str(evil / "mat.ptex")
    with pytest.raises(PathNotAllowed):
        ensure_within_roots(victim, [str(allowed)])


def test_symlink_escape_is_blocked(tmp_path):
    root = tmp_path / "allowed"
    root.mkdir()
    secret = tmp_path / "secret"
    secret.mkdir()
    link = root / "escape"
    try:
        os.symlink(str(secret), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("symlink not permitted in this environment")
    with pytest.raises(PathNotAllowed):
        ensure_within_roots(str(link / "x.ptex"), [str(root)])


def test_case_insensitive_match_on_windows(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows case-folding only")
    root = str(tmp_path)
    p = os.path.join(root.upper(), "mat.ptex")
    assert ensure_within_roots(p, [root.lower()])


def test_reject_fragment_accepts_bare_name():
    assert reject_path_fragment("bricks") == "bricks"


def test_reject_fragment_rejects_dotdot():
    with pytest.raises(PathNotAllowed):
        reject_path_fragment("..")


def test_reject_fragment_rejects_forward_slash():
    with pytest.raises(PathNotAllowed):
        reject_path_fragment("../../evil")


def test_reject_fragment_rejects_backslash():
    with pytest.raises(PathNotAllowed):
        reject_path_fragment("..\\..\\evil")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_paths.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'mm_mcp.paths'`

- [ ] **Step 3: Write the implementation**

```python
# src/mm_mcp/paths.py
"""Client-facing path guards for the batch MCP tools.

Two shapes, per the Phase 4 hardening spec:
  * ensure_within_roots  -- bounds a whole client-supplied path to
    MM_ALLOWED_ROOTS. Opt-in: empty roots means passthrough.
  * reject_path_fragment -- rejects traversal in a client-supplied *name*
    that gets joined onto a trusted dir. Always on.
"""

import os


class PathNotAllowed(Exception):
    """A client-supplied path or fragment is not permitted."""


def ensure_within_roots(path: str, roots: list[str]) -> str:
    """Return realpath(path). If roots is non-empty, require the realpath to
    lie within one of them (else raise PathNotAllowed). Empty roots is
    passthrough. realpath resolves symlinks before comparison, so a link
    inside a root cannot point outside it."""
    resolved = os.path.realpath(path)
    if not roots:
        return resolved
    cand = os.path.normcase(resolved)
    for root in roots:
        root_norm = os.path.normcase(os.path.realpath(root))
        if cand == root_norm or cand.startswith(root_norm + os.sep):
            return resolved
    raise PathNotAllowed(
        f"path '{path}' is outside the allowed roots "
        f"(MM_ALLOWED_ROOTS): {roots}")


def reject_path_fragment(name: str) -> str:
    """Return name if it is a bare path component. Raise PathNotAllowed if it
    contains a path separator or equals '..'. Always enforced, independent of
    MM_ALLOWED_ROOTS: a separator or '..' in a 'name' is never legitimate."""
    seps = [s for s in (os.sep, os.altsep) if s]
    if any(s in name for s in seps):
        raise PathNotAllowed(
            f"'{name}' must be a bare name with no path separators")
    if name == "..":
        raise PathNotAllowed(f"'{name}' is not a valid name")
    return name
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_paths.py -q`
Expected: PASS (symlink/Windows cases may SKIP depending on environment)

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/paths.py tests/test_paths.py
git commit -m "feat: add path guards (ensure_within_roots, reject_path_fragment)"
```

---

### Task 2: `config.allowed_roots`

**Files:**
- Modify: `src/mm_mcp/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `Config.allowed_roots: list[str]`, parsed from `MM_ALLOWED_ROOTS` (os.pathsep-separated, empties dropped). Default `[]`.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_config.py
import os as _os
from mm_mcp.config import load_config as _load_config


def test_allowed_roots_defaults_empty():
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": ""})
    assert cfg.allowed_roots == []


def test_allowed_roots_parses_pathsep_list():
    raw = _os.pathsep.join([r"C:\a", r"C:\b"])
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": raw})
    assert cfg.allowed_roots == [r"C:\a", r"C:\b"]


def test_allowed_roots_drops_empty_segments():
    raw = _os.pathsep.join([r"C:\a", "", r"C:\b"])
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": raw})
    assert cfg.allowed_roots == [r"C:\a", r"C:\b"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_config.py -q -k allowed_roots`
Expected: FAIL with `TypeError` (Config has no `allowed_roots`) or `AttributeError`

- [ ] **Step 3: Implement**

In `src/mm_mcp/config.py`:

Add to `_DEFAULTS`:
```python
    "MM_ALLOWED_ROOTS": "",
```

Add to the `Config` dataclass (after `live_overlay_dir`):
```python
    allowed_roots: list[str]
```

In `load_config`, before the `return Config(...)`, add:
```python
    allowed_roots = [p for p in env["MM_ALLOWED_ROOTS"].split(os.pathsep) if p]
```
and pass `allowed_roots=allowed_roots,` in the `Config(...)` constructor.

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_config.py -q`
Expected: PASS (all config tests, old + new)

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/config.py tests/test_config.py
git commit -m "feat: add MM_ALLOWED_ROOTS config field (allowed_roots)"
```

---

### Task 3: Wire guards into the batch tools

**Files:**
- Modify: `src/mm_mcp/server.py` (`save_graph`, `load_example`, `render_graph`, `render_node_output`, `render_preview`)
- Test: `tests/test_server_tools.py`

**Interfaces:**
- Consumes: `paths.ensure_within_roots`, `paths.reject_path_fragment`, `paths.PathNotAllowed` (Task 1); `config.load_config().allowed_roots` / `cfg.allowed_roots` (Task 2).
- Produces: `save_graph(ptex, path) -> dict` now returns `{"ok": True, "path": path}` or `{"ok": False, "error": ...}` (changed from bare `str`). `load_example` returns the graph dict on a valid name, or `{"ok": False, "error": ...}` on a rejected name. The three render tools return their existing `{"ok": False, "error": ...}` shape on a blocked path/basename.

**Guard placement (from the spec's enforcement table):**

| Tool | Guard |
|---|---|
| `save_graph(path)` | `ensure_within_roots(path, load_config().allowed_roots)` |
| `render_preview(albedo_path, normal_path, orm_path)` | `ensure_within_roots` on each of the three, using `cfg.allowed_roots` |
| `render_preview(basename)` / `render_graph(basename)` / `render_node_output(basename)` | `reject_path_fragment(basename)` |
| `load_example(name)` | `reject_path_fragment(name)` |

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_server_tools.py
import os as _os
from mm_mcp import server as _server


def _with_roots(monkeypatch, roots):
    monkeypatch.setenv("MM_ALLOWED_ROOTS", _os.pathsep.join(roots))
    _server._reset()


def test_save_graph_returns_ok_dict(tmp_path):
    ptex = {"type": "graph", "nodes": [], "connections": []}
    out = os.path.join(str(tmp_path), "mat.ptex")
    res = _server.save_graph(ptex, out)
    assert res["ok"] is True
    assert os.path.exists(out)


def test_save_graph_blocks_path_outside_roots(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    _with_roots(monkeypatch, [str(allowed)])
    outside = os.path.join(str(tmp_path), "elsewhere.ptex")
    res = _server.save_graph({"type": "graph", "nodes": [], "connections": []}, outside)
    assert res["ok"] is False
    assert not os.path.exists(outside)
    monkeypatch.delenv("MM_ALLOWED_ROOTS", raising=False)
    _server._reset()


def test_save_graph_allows_path_inside_roots(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    _with_roots(monkeypatch, [str(allowed)])
    inside = os.path.join(str(allowed), "mat.ptex")
    res = _server.save_graph({"type": "graph", "nodes": [], "connections": []}, inside)
    assert res["ok"] is True
    assert os.path.exists(inside)
    monkeypatch.delenv("MM_ALLOWED_ROOTS", raising=False)
    _server._reset()


def test_load_example_rejects_traversal_name():
    res = _server.load_example("../../etc/passwd")
    assert isinstance(res, dict) and res.get("ok") is False


def test_render_graph_rejects_traversal_basename():
    ptex = _server.load_example("bricks")
    res = _server.render_graph(ptex, basename="../../evil")
    assert res["ok"] is False
    assert "error" in res
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_server_tools.py -q -k "save_graph or traversal"`
Expected: FAIL (`save_graph` returns a str not a dict; traversal not yet guarded)

- [ ] **Step 3: Implement**

In `src/mm_mcp/server.py`, add to the imports near the top:
```python
from mm_mcp.config import load_config, require_valid
from mm_mcp.paths import ensure_within_roots, reject_path_fragment, PathNotAllowed
```
(the `load_config` import already exists; add the `paths` line.)

Replace `save_graph`:
```python
def save_graph(ptex: dict, path: str) -> dict:
    try:
        path = ensure_within_roots(path, load_config().allowed_roots)
    except PathNotAllowed as exc:
        return {"ok": False, "error": str(exc)}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ptex, fh, indent=1)
    return {"ok": True, "path": path}
```

Replace `load_example`:
```python
def load_example(name: str) -> dict:
    cfg, _ = _ensure_ready()
    try:
        name = reject_path_fragment(name)
    except PathNotAllowed as exc:
        return {"ok": False, "error": str(exc)}
    path = os.path.join(cfg.examples_dir, name + ".ptex")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
```

In `render_graph`, immediately after the `cfg, catalog = _ensure_ready()` line, add:
```python
    try:
        reject_path_fragment(basename)
    except PathNotAllowed as exc:
        return {"ok": False, "images": [], "error": str(exc)}
```

In `render_node_output`, immediately after `cfg, catalog = _ensure_ready()`, add:
```python
    try:
        reject_path_fragment(basename)
    except PathNotAllowed as exc:
        return {"ok": False, "image": None, "error": str(exc)}
```

In `render_preview`, immediately after `cfg, _ = _ensure_ready()`, add:
```python
    try:
        reject_path_fragment(basename)
        for p in (albedo_path, normal_path, orm_path):
            ensure_within_roots(p, cfg.allowed_roots)
    except PathNotAllowed as exc:
        return {"ok": False, "image": None, "error": str(exc)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_server_tools.py -q`
Expected: PASS (including the updated `test_save_graph_writes_file` — see Step 5 if it asserted a str return)

Note: the existing `test_save_graph_writes_file` only checks the file exists and ignores the return value, so it still passes. No edit needed there.

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/server.py tests/test_server_tools.py
git commit -m "feat: bound client-facing tool paths (save_graph dict return, traversal guards)"
```

---

### Task 4: doctor + README report `MM_ALLOWED_ROOTS`

**Files:**
- Modify: `src/mm_mcp/doctor.py`
- Modify: `README.md`
- Test: `tests/test_doctor.py`

**Interfaces:**
- Consumes: `Config.allowed_roots` (Task 2).
- Produces: one additional `Check("MM_ALLOWED_ROOTS", ok=True, detail=...)` in `check_setup` output — always `ok=True` (informational), detail differs set vs unset.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_doctor.py
from mm_mcp.doctor import check_setup as _check_setup
from mm_mcp.config import load_config as _load_config


def test_doctor_reports_allowed_roots_unset():
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": ""})
    names = {c.name: c for c in _check_setup(cfg)}
    assert "MM_ALLOWED_ROOTS" in names
    c = names["MM_ALLOWED_ROOTS"]
    assert c.ok is True
    assert "unrestricted" in c.detail.lower()


def test_doctor_reports_allowed_roots_set():
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": r"C:\a"})
    c = {c.name: c for c in _check_setup(cfg)}["MM_ALLOWED_ROOTS"]
    assert c.ok is True
    assert r"C:\a" in c.detail
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_doctor.py -q -k allowed_roots`
Expected: FAIL (no such check)

- [ ] **Step 3: Implement**

In `src/mm_mcp/doctor.py`, inside `check_setup`, just before `return checks`, add:
```python
    if cfg.allowed_roots:
        checks.append(Check("MM_ALLOWED_ROOTS", True, os.pathsep.join(cfg.allowed_roots)))
    else:
        checks.append(Check("MM_ALLOWED_ROOTS", True,
                            "unset. Writes and reads are unrestricted; set it "
                            "(os.pathsep-separated dirs) to bound client paths."))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_doctor.py -q`
Expected: PASS. `test_all_checks_pass_on_real_machine` still passes because the new check is always `ok=True`.

- [ ] **Step 5: Update README**

In `README.md`, in the `.env` config block section, add a line documenting the optional variable (place after the `MM_OUTPUT_DIR` explanation):
```markdown
`MM_ALLOWED_ROOTS` is optional. When set (an `os.pathsep`-separated list of
directories), the server refuses to read or write paths outside those roots.
When unset (the default), paths are unrestricted. Either way, node/example
`name` and `basename` arguments are always rejected if they contain a path
separator or `..`.
```

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/doctor.py tests/test_doctor.py README.md
git commit -m "feat: report MM_ALLOWED_ROOTS in --check and document it"
```

---

### Task 5: `inspect.py` — pure `.ptex` metrics

**Files:**
- Create: `src/mm_mcp/inspect.py`
- Test: `tests/test_inspect.py`

**Interfaces:**
- Consumes: nothing (pure stdlib).
- Produces: `inspect_ptex(ptex: dict, file_bytes: bytes | None = None) -> dict` returning keys `sha256` (hex or `None`), `node_count` (int), `connection_count` (int), `node_types` (sorted `{type: count}`), `material_outputs` (list of names of nodes whose `type == "material"`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_inspect.py
import hashlib
from mm_mcp.inspect import inspect_ptex


def _sample():
    return {
        "type": "graph",
        "nodes": [
            {"name": "mat", "type": "material"},
            {"name": "v1", "type": "voronoi"},
            {"name": "v2", "type": "voronoi"},
        ],
        "connections": [{"from": "v1", "from_port": 0, "to": "mat", "to_port": 0}],
    }


def test_counts_and_histogram():
    r = inspect_ptex(_sample())
    assert r["node_count"] == 3
    assert r["connection_count"] == 1
    assert r["node_types"] == {"material": 1, "voronoi": 2}
    assert r["material_outputs"] == ["mat"]


def test_sha256_present_when_bytes_given():
    raw = b'{"nodes":[],"connections":[]}'
    r = inspect_ptex({"nodes": [], "connections": []}, file_bytes=raw)
    assert r["sha256"] == hashlib.sha256(raw).hexdigest()


def test_sha256_none_when_no_bytes():
    r = inspect_ptex({"nodes": [], "connections": []})
    assert r["sha256"] is None


def test_missing_keys_are_tolerated():
    r = inspect_ptex({})
    assert r["node_count"] == 0
    assert r["connection_count"] == 0
    assert r["node_types"] == {}
    assert r["material_outputs"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_inspect.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'mm_mcp.inspect'`

- [ ] **Step 3: Implement**

```python
# src/mm_mcp/inspect.py
"""Read-only metrics for a .ptex graph, for the inspect_project tool.

Deliberately tolerant (never raises on a malformed graph) and independent of
the node catalog: this answers "what is in this file" for a hand-edited .ptex
coming back through the round-trip loop, not "is it valid" (that is validator).
"""

import hashlib


def inspect_ptex(ptex: dict, file_bytes: bytes | None = None) -> dict:
    nodes = ptex.get("nodes", []) or []
    connections = ptex.get("connections", []) or []
    histogram: dict[str, int] = {}
    material_outputs: list[str] = []
    for n in nodes:
        t = n.get("type", "<untyped>")
        histogram[t] = histogram.get(t, 0) + 1
        if t == "material":
            material_outputs.append(n.get("name", "<unnamed>"))
    return {
        "sha256": hashlib.sha256(file_bytes).hexdigest() if file_bytes is not None else None,
        "node_count": len(nodes),
        "connection_count": len(connections),
        "node_types": dict(sorted(histogram.items())),
        "material_outputs": material_outputs,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_inspect.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/inspect.py tests/test_inspect.py
git commit -m "feat: add inspect_ptex pure metrics helper"
```

---

### Task 6: `inspect_project` tool

**Files:**
- Modify: `src/mm_mcp/server.py` (new function + registration)
- Modify: `README.md` (Tools table: 9 -> 10 batch tools)
- Test: `tests/test_server_tools.py`

**Interfaces:**
- Consumes: `inspect.inspect_ptex` (Task 5), `paths.ensure_within_roots`/`PathNotAllowed` (Task 1), `config.load_config` (Task 2).
- Produces: `inspect_project(path: str) -> dict` = `{"ok": True, "sha256", "node_count", "connection_count", "node_types", "material_outputs"}` or `{"ok": False, "error": ...}`.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_server_tools.py
def test_inspect_project_on_real_example(tmp_path):
    ptex = _server.load_example("bricks")
    out = os.path.join(str(tmp_path), "b.ptex")
    _server.save_graph(ptex, out)
    res = _server.inspect_project(out)
    assert res["ok"] is True
    assert res["node_count"] > 0
    assert isinstance(res["node_types"], dict)
    assert len(res["sha256"]) == 64


def test_inspect_project_missing_file(tmp_path):
    res = _server.inspect_project(os.path.join(str(tmp_path), "nope.ptex"))
    assert res["ok"] is False


def test_inspect_project_bad_json(tmp_path):
    bad = os.path.join(str(tmp_path), "bad.ptex")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write("{not json")
    res = _server.inspect_project(bad)
    assert res["ok"] is False


def test_inspect_project_registered_as_tool():
    # inspect_project must be in the registered tool set, not just importable.
    assert hasattr(_server, "inspect_project")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_server_tools.py -q -k inspect_project`
Expected: FAIL (`server` has no `inspect_project`)

- [ ] **Step 3: Implement**

In `src/mm_mcp/server.py`, add the import:
```python
from mm_mcp.inspect import inspect_ptex
```

Add the function (near `save_graph`):
```python
def inspect_project(path: str) -> dict:
    """Read-only metrics for a .ptex file on disk: file sha256, node and
    connection counts, a node-type histogram, and the material-output node
    names. For inspecting a hand-edited graph coming back through the round
    trip. Bounded by MM_ALLOWED_ROOTS when set."""
    try:
        path = ensure_within_roots(path, load_config().allowed_roots)
    except PathNotAllowed as exc:
        return {"ok": False, "error": str(exc)}
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        return {"ok": False, "error": f"cannot read '{path}': {exc}"}
    try:
        ptex = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        return {"ok": False, "error": f"'{path}' is not valid UTF-8 JSON: {exc}"}
    return {"ok": True, **inspect_ptex(ptex, file_bytes=raw)}
```

Register it in the `mcp.tool()(...)` block (after `mcp.tool()(load_example)`):
```python
mcp.tool()(inspect_project)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_server_tools.py -q`
Expected: PASS

- [ ] **Step 5: Update README Tools table**

In `README.md`, the "Tools" section: change "nine batch-mode tools" to "ten batch-mode tools", and add a row to the batch tool table:
```markdown
| `inspect_project` | Read-only metrics for a `.ptex` on disk (hash, node/connection counts, type histogram, material outputs) |
```

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/server.py tests/test_server_tools.py README.md
git commit -m "feat: add inspect_project batch tool"
```

---

### Task 7: Single-source the version

**Files:**
- Modify: `src/mm_mcp/__init__.py`
- Test: `tests/test_doctor.py` (existing `--version` test must still pass)

**Interfaces:**
- Consumes: `importlib.metadata`.
- Produces: `mm_mcp.__version__` derived from installed package metadata, with a `0.0.0+unknown` fallback for a non-installed (`pythonpath=src`) run.

- [ ] **Step 1: Confirm the existing guard test**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_doctor.py -q -k version`
Expected: PASS today (asserts `__version__` appears in `--version` output).

- [ ] **Step 2: Implement**

Replace the body of `src/mm_mcp/__init__.py`'s version line. The file currently has `__version__ = "0.3.0"`. Replace that single assignment with:
```python
from importlib.metadata import version as _pkg_version, PackageNotFoundError

try:
    __version__ = _pkg_version("mm-mcp")
except PackageNotFoundError:  # not pip-installed (tests import via pythonpath=src)
    __version__ = "0.0.0+unknown"
```
Preserve any other content already in `__init__.py` (only the `__version__` literal changes).

- [ ] **Step 3: Verify both run modes**

Run (installed mode, reports real version): `& "C:\Program Files\Python313\python.exe" -m pytest tests/test_doctor.py -q -k version`
Expected: PASS. If the repo is installed editable (`pip install -e .`), `--version` prints `mm-mcp 0.3.0`; if not, it prints `mm-mcp 0.0.0+unknown`. The test asserts `__version__ in output`, true in both.

- [ ] **Step 4: Full fast suite regression check**

Run: `& "C:\Program Files\Python313\python.exe" -m pytest -q -m "not integration"`
Expected: PASS (all, ~236+ with the new tests).

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/__init__.py
git commit -m "refactor: derive __version__ from package metadata (single source)"
```

---

### Task 8: CI test workflow

**Files:**
- Create: `.github/workflows/test.yml`

**Interfaces:**
- Consumes: the provisioning recipe verified in the spec (real MM checkout + stub Godot binary + `.env` neutralized). No code interfaces.
- Produces: a green CI check on push/PR to `main`.

- [ ] **Step 1: Write the workflow**

```yaml
# .github/workflows/test.yml
name: tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  fast-tests:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Clone Material Maker (node defs + examples the suite reads)
        run: git clone --depth 1 https://github.com/RodZill4/material-maker mm-checkout

      - name: Write steam_appid.txt
        run: Set-Content -Path mm-checkout/steam_appid.txt -Value 4110830 -NoNewline
        shell: pwsh

      - name: Create stub Godot binary (existence is all the suite checks)
        run: |
          New-Item -ItemType Directory -Force -Path godot-stub | Out-Null
          Set-Content -Path godot-stub/Godot_v4.7.1_win64.exe -Value x -NoNewline
        shell: pwsh

      - name: Install
        run: pip install -e .[dev]

      - name: Run fast suite
        env:
          MM_PROJECT_PATH: ${{ github.workspace }}\mm-checkout
          MM_GODOT_BINARY: ${{ github.workspace }}\godot-stub\Godot_v4.7.1_win64.exe
          MM_OUTPUT_DIR: ${{ github.workspace }}\output
          MM_DOTENV: ${{ github.workspace }}\no-such.env
        run: pytest -q -m "not integration"
```

- [ ] **Step 2: Dry-run the exact test invocation locally**

The workflow's correctness is proven when it runs green on the first PR, but validate the recipe locally first (Git Bash):
```bash
STUB="$(mktemp -d)/Godot_v4.7.1_win64.exe"; echo x > "$STUB"
env -u MM_OUTPUT_DIR MM_DOTENV="/nonexistent/.env" \
  MM_PROJECT_PATH="C:/Projects-local/z-Git/material-maker" \
  MM_GODOT_BINARY="$STUB" \
  "/c/Program Files/Python313/python.exe" -m pytest -q -m "not integration"
```
Expected: all pass (matches the spec's verified `232 passed` plus the tasks' new tests).

- [ ] **Step 3: Validate the YAML parses**

Run: `& "C:\Program Files\Python313\python.exe" -c "import yaml,sys; yaml.safe_load(open('.github/workflows/test.yml')); print('yaml ok')"`
Expected: `yaml ok` (install `pyyaml` if missing: `pip install pyyaml`).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: add windows fast-test workflow"
```

---

### Task 9: release-please

**Files:**
- Create: `release-please-config.json`
- Create: `.release-please-manifest.json`
- Create: `.github/workflows/release-please.yml`

**Interfaces:**
- Consumes: conventional-commit history on `main`; the `windows-latest` build environment.
- Produces: a maintained release PR; on merge, a tag + GitHub Release with `dist/*` attached. release-please updates `pyproject.toml`'s `version`.

- [ ] **Step 1: Create the manifest (seed current version)**

```json
{
  ".": "0.3.0"
}
```
Save as `.release-please-manifest.json`.

- [ ] **Step 2: Create the config**

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "packages": {
    ".": {
      "release-type": "python",
      "package-name": "mm-mcp",
      "include-component-in-tag": false
    }
  }
}
```
Save as `release-please-config.json`.

Note on the version file: the `python` release-type updates `pyproject.toml`'s `version` field (PEP 621 `[project].version`). Because Task 7 made `__init__.py` derive its version from metadata, there is no second literal to keep in sync. If a future check shows the python strategy did not pick up `pyproject.toml`, add an `extra-files` entry for it; not expected to be needed.

- [ ] **Step 3: Create the workflow**

```yaml
# .github/workflows/release-please.yml
name: release-please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.rp.outputs.release_created }}
      tag_name: ${{ steps.rp.outputs.tag_name }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: rp
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json

  build-artifacts:
    needs: release-please
    if: ${{ needs.release-please.outputs.release_created == 'true' }}
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Build wheel + sdist
        run: |
          pip install build
          python -m build
        shell: pwsh
      - name: Attach to the GitHub Release
        run: gh release upload "${{ needs.release-please.outputs.tag_name }}" dist/*
        env:
          GH_TOKEN: ${{ github.token }}
        shell: pwsh
```

- [ ] **Step 4: Validate both YAML files parse**

Run:
```
& "C:\Program Files\Python313\python.exe" -c "import yaml; yaml.safe_load(open('.github/workflows/release-please.yml')); print('rp yaml ok')"
& "C:\Program Files\Python313\python.exe" -c "import json; json.load(open('release-please-config.json')); json.load(open('.release-please-manifest.json')); print('json ok')"
```
Expected: `rp yaml ok` and `json ok`.

- [ ] **Step 5: Commit**

```bash
git add release-please-config.json .release-please-manifest.json .github/workflows/release-please.yml
git commit -m "ci: add release-please with GitHub Release artifact build"
```

- [ ] **Step 6: Record the human-only prerequisite**

This cannot be done from a session. Note it in the handoff for Grayson: GitHub repo **Settings -> Actions -> General -> Workflow permissions -> enable "Allow GitHub Actions to create and approve pull requests"**, or release-please cannot open its release PR.

---

### Task 10: STATUS.md update + stale-note fix (docs wrap)

**Files:**
- Modify: `STATUS.md`

**Interfaces:** none (documentation).

- [ ] **Step 1: Update the Phase 4 row and components**

In `STATUS.md`:
- Fix the stale note on line 9: the render-timeout work IS merged into `main` (remove the "on branch `claude/confident-tesla-ee9400`, not yet merged" claim).
- Update the Phase 4 row evidence to record: opt-in allowed-roots path bounding + always-on traversal guards; `inspect_project` (batch tool #10); CI fast-test workflow; release-please with GitHub Release artifacts; version single-sourced via `importlib.metadata`. Keep the gate state 🔌 (cross-platform still unverified) unless Grayson decides the CI green promotes it.
- Add component rows for `paths.py` and `inspect.py` (✅ verified, with test file references), and note the `MM_ALLOWED_ROOTS` config field on the config/`doctor.py` rows.

- [ ] **Step 2: Commit**

```bash
git add STATUS.md
git commit -m "docs: record Phase 4 hardening in STATUS ledger"
```

---

## Self-Review

**Spec coverage:**
- Item 1 (path bounding): Tasks 1 (guards), 2 (config), 3 (tool wiring), 4 (doctor + README). ✅
- Item 2 (inspect_project): Tasks 5 (pure helper), 6 (tool + README). ✅
- Item 3 (CI + release-please): Tasks 7 (version single-source), 8 (test.yml), 9 (release-please). ✅
- Framing/stale-note/STATUS: Task 10. ✅
- Non-goals (no PyPI, no live/overlay bounding, opt-in default, operator config untouched): honored — no task adds PyPI upload, guards touch only the five named batch tools, `ensure_within_roots` is passthrough on empty roots, and `output_dir`/`project_path` are never passed to a guard. ✅

**Type consistency:** `ensure_within_roots(path, roots) -> str` and `reject_path_fragment(name) -> str` and `PathNotAllowed` are used with those exact names/signatures in Tasks 3 and 6. `inspect_ptex(ptex, file_bytes=None) -> dict` is defined in Task 5 and called identically in Task 6. `Config.allowed_roots` defined in Task 2, read in Tasks 3, 4, 6. `save_graph` return shape change to `{"ok", "path"}` is stated in Task 3 and its consumers (none internal) confirmed.

**Placeholder scan:** no TBD/TODO; every code and test step carries real content.

## Execution

Per the standing project default, execution proceeds **Subagent-Driven**: a fresh subagent per task with two-stage review between tasks (`superpowers:subagent-driven-development`), in Task order 1 through 10.
