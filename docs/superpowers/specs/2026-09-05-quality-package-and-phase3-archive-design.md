# quality/ as a package + Phase-3 harness archive (design)

Source: teardown #4 (2026-09-05), findings 3 and 5, verdict table rows
"quality/cookbook_*.py + author_helpers.py" (Refactor), "quality/author.py
frozen" (Refactor), "quality/run_case.py, test_set.json, scorecards/, runs/"
(Archive). Grayson picked this as option 3 the same evening.

## Problem

`quality/` holds 5,961 lines of Python that regenerate the 53 tracked cookbook
graphs, plus the diagnostic swatches, the PNG reader the ORM checks depend
on, and the promote/check baseline. It is bigger than `src/` and the docs call
it "the source" of the cookbook. It is wired like a scratch folder:

- Every script and five test files put `quality/` (and `src/`) on `sys.path`
  by hand, 26 `sys.path.insert` lines in all. Scripts import each other by
  bare name (`from author_helpers import`), which only resolves when Python
  is launched on the file itself from the right directory.
- `author.py` (455 lines) is labeled "frozen Phase-3 evidence, do not edit"
  in `quality/README.md` and STATUS, yet six of twelve cookbook builders
  import it and `take_variant` exists to run its builders under cookbook
  labels. The label forbids fixing a load-bearing library. The real freeze is
  `promote_cookbook.py --check`, which fails on any output drift whichever
  file caused it.
- `run_case.py` (233 lines), `score_baseline.py`, `test_set.json`, and
  `scorecards/` are the Phase-3 gate apparatus. The gate closed 2026-08-26
  (15/15) and the runner has not been executed since. `quality/runs/`
  (290 MB, gitignored) is its local output. `verify_hero_fold.py` needs a
  folder that now lives in `_to_delete`.
- `cookbook_wood/glass/plastics.py` build the catalog inside each builder;
  the other nine take one catalog from `main()`.
- `tests/test_donors.py` builds the catalog at module import, so a missing
  `MM_PROJECT_PATH` fails all 20 donor tests at collection instead of the 9
  that need it.

## Decisions

1. **`quality/` becomes an importable package in place. No rename.** Add
   `quality/__init__.py`, qualify every intra-package import as
   `from quality.<module> import ...`, delete every `sys.path.insert`, and
   add `"."` to pytest's `pythonpath` so tests import `quality.*` directly.
   Scripts are invoked as `python -m quality.<module> [args]` from the repo
   root; the `if __name__ == "__main__"` blocks and argv contracts do not
   change. Rationale for not renaming or moving under `src/mm_mcp/`: the
   builders need Godot and a Material Maker checkout, nobody pip-installs
   them, and a rename touches ten memory files, the backup override, and
   every doc for no behavioral gain. Making the imports honest is the fix.
2. **The "frozen" label on `author.py` goes.** Its docstring, `quality/README.md`,
   and the STATUS row describe it as the shared base for six cookbook
   categories, guarded by `--check`. Nothing else changes in the file.
3. **The Phase-3 gate apparatus moves to `docs/evidence/phase3/`** as a
   record: `test_set.json` (still `frozen: true`), both scorecards, and the
   freeze rule, with a README explaining what they proved and that the runner
   is retired. `run_case.py`, `score_baseline.py`, and `verify_hero_fold.py`
   are removed from the tree (git history keeps them; the evidence README
   names the last commit that had them). Local `quality/runs/` moves to
   `_to_delete`; its `.gitignore` line and the backup-ops exclusion for it
   are dropped.
4. **`cookbook_wood/glass/plastics.py` take `catalog` as a parameter** like
   the other nine. A gate test asserts every cookbook builder has exactly one
   parameter.
5. **`tests/test_donors.py` builds the catalog in a module-scoped fixture.**
   Presence and JSON-shape tests no longer depend on the Material Maker
   checkout.

## Non-goals

- No change to any cookbook `.ptex`. `promote_cookbook.py --check` must stay
  in sync after every task.
- No new CLI wrappers, console scripts, or packaging of `quality/` into the
  wheel.
- No edits to the tracked evidence files' content beyond moving them.

## Verification

- Fast suite green (`pytest -q -m "not integration"`).
- `python -m quality.promote_cookbook --check` reports in sync after Task 2
  (the only task that touches builder code paths).
- `grep -rn "sys.path.insert" quality tests` returns nothing.
- `MM_PROJECT_PATH` pointed at a nonexistent dir: `tests/test_donors.py`
  collects, presence/JSON tests pass, catalog tests fail individually.
