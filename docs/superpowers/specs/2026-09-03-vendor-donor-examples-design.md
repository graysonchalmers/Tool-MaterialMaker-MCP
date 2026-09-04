# Design: vendor the 9 load-bearing donor examples

_2026-09-03_

## Problem

The Phase 3 authoring pipeline (`quality/author.py`'s `load_example()`, consumed
by `author.py` itself and by all 9 `quality/cookbook_<category>.py` builders,
`debug_swatches.py`, and `noise_gallery.py`) reads its starting graphs from
`cfg.examples_dir`, which resolves to `<MM_PROJECT_PATH>/material_maker/examples`,
a folder inside the external, un-tracked Material Maker checkout
(`C:\Projects-local\z-Git\material-maker`).

That checkout is a separate project on Grayson's machine, not part of this repo.
Every cookbook rebuild, and any future authoring work, depends on that checkout
existing, at the right path, with its bundled examples unchanged. This is the
same class of hidden dependency the 2026-09-03 cookbook-as-data migration
already removed for the 43 authored cookbook graphs (previously gitignored
build output); the donor graphs those builders read *from* were never brought
along.

Auditing every `load_example(...)` call site across `quality/*.py` found
exactly 9 distinct names in use, out of the 43 examples Material Maker bundles:
`beehive`, `crocodile_skin`, `dry_earth`, `metal_pattern_2`, `rock`,
`rusted_metal`, `stone_wall`, `wood`, `wooden_floor`. The other 34 bundled
examples (art/pattern demos like `mandelbrot`, `raymarching`, `pentagram`,
`skulls`, `mmm_donuts`) are never read by anything in this repo.

## Decision

Vendor only the 9 load-bearing donor graphs into this repo as tracked data.
Leave every other consumer of `cfg.examples_dir` untouched:

- `list_examples(source="material_maker")` / `load_example(source="material_maker")`
  in `server.py` keep browsing the live external checkout, all 43 examples,
  same as today.
- `doctor.py`'s `examples` check keeps reporting on `cfg.examples_dir`,
  unchanged.
- `tests/test_examples_gate.py` (the Phase 1 gate, "every bundled example
  validates") keeps globbing `cfg.examples_dir/*.ptex` and validating all 43,
  unchanged. It still requires the external checkout to run, same as today.
- `tests/test_render.py` and `tests/test_preview.py` keep loading
  `bricks.ptex` from `cfg.examples_dir` for their render/preview smoke tests,
  unchanged (`bricks` is not one of the 9 donors and is unrelated to the
  authoring pipeline).
- `tests/test_config.py`'s `examples_dir` assertion is unchanged.

Only the authoring pipeline's own donor-loading path changes. This is
intentionally the narrower of the two options discussed (vendor just the 9
vs. vendor all 43): the other 34 examples are mostly non-material demo
content, and folding them into a curated, recipe-carded cookbook would blur
what the cookbook is for. Browsing them over MCP is a separate concern from
the authoring pipeline's reproducibility, and stays live.

## Design

### File layout

New tracked directory: `quality/donors/`, sibling to `quality/authored/`
(gitignored builder output) and `cookbook/` (tracked, curated, recipe-carded
output). `quality/donors/` holds:

- The 9 `.ptex` files, copied byte-for-byte from
  `<MM_PROJECT_PATH>/material_maker/examples/<name>.ptex`, unmodified.
- `quality/donors/README.md`: a short note that these are vendored copies of
  specific Material Maker bundled examples (names the source path and that
  they're upstream Material Maker content, not first-party recipes), so
  nobody later mistakes them for cookbook material or tries to give them
  recipe cards.

`quality/donors/` is tracked in git (not gitignored), same as `cookbook/`.

### Code change

This spec assumes the separately-approved `author.py` refactor (extracting
graph-surgery helpers into `quality/author_helpers.py`) lands first, since
`load_example()` is one of the extracted helpers. If that refactor has not
landed yet when this is implemented, apply the same change directly to
`load_example()` in `quality/author.py` instead; the substance is identical
either way.

`load_example()`'s body changes from:

```python
_EX = Path(_CFG.examples_dir)

def load_example(name: str) -> dict:
    with open(_EX / f"{name}.ptex", encoding="utf-8") as fh:
        return json.load(fh)
```

to reading from the new tracked path instead of `_CFG.examples_dir`:

```python
_DONORS = Path(__file__).resolve().parent / "donors"

def load_example(name: str) -> dict:
    with open(_DONORS / f"{name}.ptex", encoding="utf-8") as fh:
        return json.load(fh)
```

`_CFG`/`load_config()` stays imported and used elsewhere in the same module
(e.g. `save_variant`'s output path is unrelated to this change), so this is
a targeted change to `load_example()` and its module-level path constant
only, not a removal of the config dependency from the whole file.

Every call site (`author.py`'s own `build_*` functions, plus the 9 files
that `from author import load_example` or `from author_helpers import
load_example` after the refactor) is unaffected by this change: they all
call `load_example("some_name")` the same way before and after, since the
function's signature and return shape (a parsed graph dict) don't change,
only where it reads from.

### What is explicitly out of scope

- No change to `Config`, `cfg.examples_dir`, `MM_PROJECT_PATH`, or
  `.env.example`.
- No change to `server.py`'s `list_examples`/`load_example` MCP tools or
  their `source` parameter.
- No change to `doctor.py`.
- No change to `tests/test_examples_gate.py`'s scope (still all 43, still
  requires the external checkout to run).
- No recipe cards for the 9 donor files. They are not cookbook entries.
- No `--check`/promote tooling like `promote_cookbook.py`. These are static
  vendored copies with no builder regenerating them, unlike cookbook's
  authored-from-builder pattern; a one-time copy plus a presence/validity
  test is enough.

## Testing

Add a small test, in a new `tests/test_donors.py` (kept separate from
`tests/test_author_helpers.py` since it tests tracked data, not the pure
graph-surgery functions), that:

1. Asserts all 9 expected files exist under `quality/donors/`.
2. Asserts each parses as valid JSON with `nodes` and `connections` keys.
3. Validates each against the catalog (`validate_graph`) with zero
   `error`-severity problems, mirroring the Phase 1 gate's per-file check
   but scoped to the 9 tracked donors instead of the live external
   checkout's 43.

Manual verification: before making the code change, run
`python quality/author.py iter1` (or an equivalent invocation covering all
current `BUILDERS`) and note the output. After vendoring the files and
switching `load_example()`, re-run the same command and confirm the
generated `.ptex` variants are byte-identical (or JSON-content-identical,
matching the `--check` comparison convention `promote_cookbook.py` already
uses for the same CRLF-on-Windows-vs-LF-in-git reason) to the pre-change
run. This proves the switch changed *where* graphs load from without
changing *what* loads.

Run the full fast suite (`pytest -q -m "not integration"`) after the change
to confirm nothing else regressed.

## Risks

- **Drift risk (low, accepted):** if Material Maker's own bundled examples
  are ever updated upstream, the vendored copies won't pick up that change
  automatically. This is the same tradeoff `cookbook/`'s tracked `.ptex`
  files already accept, and these 9 files are stable, long-unmodified parts
  of Material Maker's own example set, not a fast-moving dependency.
- **Provenance clarity (mitigated):** `quality/donors/README.md` exists
  specifically so a future session (or Grayson) doesn't mistake these for
  first-party cookbook content or wonder why they lack recipe cards.
