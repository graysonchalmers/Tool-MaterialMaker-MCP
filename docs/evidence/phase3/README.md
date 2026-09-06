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
`59d788f` (`git show 59d788f:quality/run_case.py`). The runner had not been
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
