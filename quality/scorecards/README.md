# scorecards/ — the freeze rule

The test set (`quality/test_set.json`) and its rubric **freeze at the end of
sub-phase 3A**, after Grayson's review, by setting `_meta.frozen = true`.

Once frozen:

- **3C tuning may NOT change** the cases, their `must_have`/`must_not` criteria,
  or the rubric. Tuning changes only the *inputs to authoring* (`docs/AUTHORING.md`,
  catalog description overrides, server guidance, validator warnings).
- Every full run of the 15 cases produces one scorecard here
  (`<date>-baseline.md`, `<date>-iter1.md`, ...).
- Adding or changing cases later starts a **new** scorecard series and a new
  baseline. It is never an edit to an existing scored run.

This is what keeps the hit-rate honest: the ruler doesn't move while we tune the
thing being measured.

## Freeze log

- **2026-08-26** — FROZEN. Grayson reviewed the 15 cases; `m02_brushed_aluminum`
  anisotropy criterion softened to "directional streaking (aligned along one
  axis), not isotropic noise" before locking. `_meta.frozen = true`.
