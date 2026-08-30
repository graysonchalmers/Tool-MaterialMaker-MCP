# Phase 4 hardening: path bounding, inspect_project, CI + release automation

Design spec. Three additions that close out Phase 4 (public packaging),
prompted by a compare against `dcc-mcp/dcc-mcp-material-maker` (a headless
export/inspection adapter for the same app). That project is a different
product from ours (it never authors graphs), but its engineering rigor around
sandboxing and release packaging is worth borrowing. This spec takes the three
items that fit our North Star without threatening it.

## Framing: Phase 4 completion, not a new phase

Phase 4 in `STATUS.md` is 🔌 wired, with "cross-platform still unverified" and
"PyPI on hold" as the open items. CI, release automation, and path bounding are
exactly what a public alpha needs before strangers rely on it, so they land
under the existing Phase 4 gate rather than orphaned outside the ledger. No new
phase number.

Stale-note cleanup to do in passing: `STATUS.md` line 9 says the render-timeout
work is on branch `claude/confident-tesla-ee9400` "not yet merged." It is merged;
`main` is clean and contains `cd1fcb9 fix(render): kill the whole Godot process
tree on render timeout`. Correct that note when STATUS is next updated.

## Non-goals

- **No PyPI publish.** Distribution stays GitHub-clone + GitHub Release
  artifacts, per the current STATUS decision. release-please builds and attaches
  a wheel + sdist to the Release; it does not upload to PyPI.
- **No guarding of operator-controlled config.** `MM_OUTPUT_DIR` /
  `MM_PROJECT_PATH` come from the operator's own env; they are trusted and not
  subject to the allowed-roots check.
- **No live/overlay path bounding in v1.** `live.py` / `overlay.py` filesystem
  paths are out of scope for this pass; only the batch-mode client-facing tools
  are guarded. Named here so a later pass can pick it up deliberately.
- **Not making path bounding mandatory.** Opt-in by design (see Item 1). The
  daily me-first workflow stays frictionless; safety is one env var away and is
  surfaced in `--check`.

## Item 1: Allowed-roots path bounding (opt-in)

### Problem

Several batch tools accept client-supplied paths or path fragments with no
bounding:

- `save_graph(path)` writes JSON to any absolute path.
- `render_preview(albedo_path, normal_path, orm_path)` reads any paths.
- `render_graph` / `render_node_output` / `render_preview` take a
  `basename` that is joined as `os.path.join(outdir, basename + ".ptex")`
  (`render.py:162`) and scanned via `startswith(basename + "_")`. A
  `basename="../../evil"` escapes `outdir`.
- `load_example(name)` does `os.path.join(cfg.examples_dir, name + ".ptex")`
  (`server.py:159`). A `name` containing `..` or a separator escapes
  `examples_dir`.

### Design

A new pure module `src/mm_mcp/paths.py`:

```python
def ensure_within_roots(path: str, roots: list[str]) -> str:
    """Return the realpath of `path` if it is inside one of `roots`.
    Empty `roots` => passthrough (still returns realpath). Raises
    PathNotAllowed otherwise."""
```

Rules, each with a dedicated test:

- Resolve with `os.path.realpath` (not `abspath`) so a symlink inside a root
  cannot point outside it.
- Compare with `os.path.commonpath([root, candidate]) == root` after
  realpath-normalizing both, or an equivalent normalized-prefix check with an
  explicit trailing-separator guard, so `/allowed` does not match
  `/allowed-evil`.
- Case-fold on Windows (`os.path.normcase`) so `C:\Foo` matches `c:\foo`.
- Empty `roots` list => passthrough (the opt-in): normalize and return, never
  raise.

A separate always-on helper for the fragment vector:

```python
def reject_path_fragment(name: str) -> str:
    """Return `name` unchanged if it is a bare filename component. Raises
    PathNotAllowed if it contains a path separator (os.sep / os.altsep) or
    any `..` component. Always enforced, independent of MM_ALLOWED_ROOTS."""
```

`PathNotAllowed` is a module-level exception. The pure helpers raise it; the
`server.py` tool wrappers catch it and return `{"ok": False, "error": str(exc)}`
(errors-as-data, per project convention), so Claude self-corrects rather than
seeing a stack trace.

### Config

`config.py` gains one field:

```python
allowed_roots: list[str]   # parsed from MM_ALLOWED_ROOTS, os.pathsep-separated
```

Parsed in `load_config` from `env["MM_ALLOWED_ROOTS"]` (added to `_DEFAULTS` as
`""`), split on `os.pathsep`, empties dropped. Empty list is the default and
means unrestricted. No entry in `require_valid` (an unset value is legal).

### Enforcement points

| Guard shape | Tools / inputs | Gated by MM_ALLOWED_ROOTS? |
|---|---|---|
| `ensure_within_roots` (full path) | `save_graph(path)`, `render_preview(albedo_path, normal_path, orm_path)`, `inspect_project(path)` | Yes (empty roots => passthrough) |
| `reject_path_fragment` (component) | `render_graph(basename)`, `render_node_output(basename)`, `render_preview(basename)`, `load_example(name)` | No, always on |

The full-path guard is a no-op when `MM_ALLOWED_ROOTS` is unset (Grayson's daily
case). The fragment guard is always on because a traversal in a "name" is never
legitimate and costs nothing.

### Discoverability (doctor + README)

`doctor.py` (`--check`) gains one check line: report `MM_ALLOWED_ROOTS` as set
(listing the roots) or unset, with a plain note that unset means writes/reads
are unrestricted. This is informational, not a failure: unset is green with a
note, not red. Mirror the variable in the README `.env` / config block with a
one-line explanation.

### Testing

- `tests/test_paths.py`: `ensure_within_roots` inside-root pass, outside-root
  raise, symlink-escape raise, `/allowed` vs `/allowed-evil` non-match, Windows
  case-insensitive match, empty-roots passthrough; `reject_path_fragment`
  accepts a bare name, rejects `..`, rejects both separators.
- Per-tool tests in the existing server tests: a blocked path returns an error
  dict (not a raise) and an allowed path passes, for each guarded tool. With
  `MM_ALLOWED_ROOTS` set for the full-path tools; unconditionally for the
  fragment tools.
- `tests/test_doctor.py`: the new set/unset report line.

## Item 2: inspect_project tool

### Problem

We have no read-only "what's in this .ptex" tool. In the round-trip loop, when
Grayson brings back a hand-edited file, a quick metrics readout is useful and
costs nothing to render.

### Design

New pure module `src/mm_mcp/inspect.py`:

```python
def inspect_ptex(ptex: dict, file_bytes: bytes | None = None) -> dict:
    """Return metrics for a parsed .ptex graph. If file_bytes is given,
    include its sha256."""
```

Returns:

```json
{
  "sha256": "<hex of the file bytes, or null if not provided>",
  "node_count": <int>,
  "connection_count": <int>,
  "node_types": {"<type>": <count>, ...},
  "material_outputs": ["<name>", ...]
}
```

- `node_count` / `connection_count`: `len(ptex["nodes"])` /
  `len(ptex["connections"])`, defensive against missing keys.
- `node_types`: histogram of each node's `type`.
- `material_outputs`: names of nodes whose type is a material output (reuse the
  existing material-node detection in `graph.py`'s `find_material_node` logic;
  factor out a shared helper if needed rather than duplicating the type set).

`server.py` wraps it as batch tool #10:

```python
def inspect_project(path: str) -> dict:
    cfg, _ = _ensure_ready()
    # ensure_within_roots(path, cfg.allowed_roots), catch PathNotAllowed
    # read bytes, json.loads, catch FileNotFoundError / JSONDecodeError
    # return {"ok": True, **inspect_ptex(ptex, file_bytes)}
    #  or {"ok": False, "error": ...}
```

All failure modes (blocked path, missing file, malformed JSON) return an error
dict, not an exception. Registered in the tool list; README "Tools" table grows
from nine batch tools to ten.

### Testing

- `tests/test_inspect.py`: `inspect_ptex` on a known bundled example gives the
  expected counts and histogram; sha256 present when bytes passed, null when
  not; empty/missing keys handled.
- Server-level: `inspect_project` on a real example path returns `ok: True` with
  metrics; missing file and bad JSON return `ok: False`; blocked path (roots
  set) returns `ok: False`.

## Item 3: CI + release-please

### Version single-sourcing (prerequisite)

Version currently lives in two places: `pyproject.toml` `version = "0.3.0"` and
`src/mm_mcp/__init__.py` `__version__ = "0.3.0"`. Collapse to one source so
release-please only edits `pyproject.toml`:

```python
# src/mm_mcp/__init__.py
from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("mm-mcp")
except PackageNotFoundError:      # not installed (tests import via pythonpath=src)
    __version__ = "0.0.0+unknown"
```

The fallback is load-bearing: `tool.pytest.ini_options` sets
`pythonpath = ["src"]`, so tests import `mm_mcp` without an install and
`version("mm-mcp")` raises `PackageNotFoundError`. `test_doctor.py:74` asserts
`__version__ in` the `--version` output; both the installed value and the
fallback satisfy that (the output is `mm-mcp <value>`), so the test stays green
either way. CI runs `pip install -e .[dev]`, so `--version` reports the true
version there.

### CI test workflow

`.github/workflows/test.yml`:

- Triggers: `push` and `pull_request` targeting `main`.
- Runner: `windows-latest` (our only end-to-end-verified platform; adding
  ubuntu is deferred until a cross-platform pass actually verifies the
  off-Windows render fallback).
- Provision the toolchain the fast suite needs. `_ensure_ready` calls
  `require_valid`, which requires a real Material Maker checkout (project path,
  node defs, examples) AND a Godot binary *file that exists*. No fast test
  actually launches Godot (that is the `integration` marker), so the binary can
  be a zero-byte stub. Steps:
  1. `git clone --depth 1 https://github.com/RodZill4/material-maker mm-checkout`
     (MIT, redistribution-free to clone in CI).
  2. Write `4110830` to `mm-checkout/steam_appid.txt`.
  3. Create a stub Godot binary file, e.g. `godot-stub/Godot_v4.7.1_win64.exe`
     containing a single byte (only its existence is checked).
  4. Set env for the test step: `MM_PROJECT_PATH=<...>/mm-checkout`,
     `MM_GODOT_BINARY=<...>/godot-stub/Godot_v4.7.1_win64.exe`,
     `MM_OUTPUT_DIR=<...>/output`, and `MM_DOTENV=<nonexistent path>` so a
     stray `.env` can never leak in.
- Then: checkout, `actions/setup-python` (3.13), `pip install -e .[dev]`,
  `pytest -q -m "not integration"`.
- **Verified locally before writing this plan:** the exact recipe above (real MM
  checkout + a stub Godot binary + `.env` neutralized via `MM_DOTENV`) runs
  `232 passed, 21 deselected`. An earlier probe that only unset the `MM_*` vars
  was misleading because the repo `.env` still fed real paths; neutralizing
  `.env` is what reproduces a bare runner.

### release-please

Three files:

- `release-please-config.json`: single package at repo root, `"release-type":
  "python"`, `"include-component-in-tag": false`. Points its version bump at
  `pyproject.toml`.
- `.release-please-manifest.json`: seeded `{".": "0.3.0"}` so the first computed
  release is 0.4.0, not 0.1.0.
- `.github/workflows/release-please.yml`: on push to `main`, runs
  `googleapis/release-please-action`. It maintains a release PR that
  accumulates conventional-commit changes into `CHANGELOG.md` + the version
  bump; merging that PR tags the release and creates the GitHub Release.

Post-release artifact build: a job in the same workflow (gated on the
release-please `release_created` output) checks out the tag, runs
`python -m build`, and uploads `dist/*` (wheel + sdist) to the just-created
GitHub Release. No PyPI step.

Conventional commits are already de facto in use (`fix(render):`, `docs:` in
recent history), so this imposes no new authoring burden; agents write the
commits.

### Human-only prerequisite (call out in the plan, cannot be done from a session)

GitHub repo Settings -> Actions -> General -> Workflow permissions -> enable
"Allow GitHub Actions to create and approve pull requests." Without it,
release-please cannot open its release PR. This is Grayson's one manual click.

### Testing / verification

- CI: the test workflow going green on its first PR is its own proof.
- release-please: verified when the first release PR opens against `main` and,
  on merge, produces a tagged GitHub Release with `dist/*` attached. This is an
  end-to-end check that happens on the real repo, not a unit test.

## Build order

1. **paths.py + guards + config field + doctor line** (the security boundary;
   nothing depends on it yet).
2. **inspect.py + inspect_project tool** (consumes `ensure_within_roots`).
3. **Version single-sourcing + test.yml** (green CI on a complete main).
4. **release-please** (config + manifest + workflow), last, so it lands on a
   main that is already green and already carries items 1 through 3.

## Files touched

- New: `src/mm_mcp/paths.py`, `src/mm_mcp/inspect.py`,
  `.github/workflows/test.yml`, `.github/workflows/release-please.yml`,
  `release-please-config.json`, `.release-please-manifest.json`,
  `tests/test_paths.py`, `tests/test_inspect.py`.
- Edited: `src/mm_mcp/config.py` (allowed_roots), `src/mm_mcp/server.py`
  (guards on 5 tools + new inspect_project), `src/mm_mcp/__init__.py`
  (version), `src/mm_mcp/doctor.py` (roots report line),
  `tests/test_doctor.py`, `README.md` (config block + tools table),
  `STATUS.md` (Phase 4 evidence + stale-branch note).
