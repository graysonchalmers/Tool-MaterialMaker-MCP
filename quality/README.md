# quality/ — Phase 3 authoring-quality harness

Measures whether prompt-to-graph authoring produces usable materials.

## Layout

- `test_set.json` — the 15 frozen cases + the scoring rubric (`_rubric`).
- `run_case.py` — renders authored variants for a case and (re)builds the
  scorecard. Reuses `mm_mcp` render + validate; adds no render logic.
- `runs/<run>/<case_id>/variant_N/` — per-variant outputs: 4 PBR maps +
  `source.ptex`. `runs/<run>/<case_id>/_result.json` holds the case's render
  results and the judge verdict fields.
- `scorecards/<run>.md` — one auto-generated scorecard per run.
- `scorecards/README.md` — the freeze rule for the test set.

## Flow

1. Claude authors 2-3 variant `.ptex` graphs for a case (this is what Phase 3
   measures).
2. `run_case.py --run <label> --case <id> --variants a.ptex b.ptex c.ptex`
   validates + renders each and writes `_result.json`.
3. The judge (Claude vision) fills the `verdict` block in each `_result.json`
   against the rubric; Grayson audits.
4. `run_case.py --run <label> --rebuild-scorecard` regenerates the Markdown.

## Runs are named, not numbered

- `<date>-baseline` — the 3B control (no AUTHORING.md recipes).
- `<date>-iter<N>` — each 3C tuning iteration.

The **gate** is a scorecard showing >= 70% (>= 11/15) any-variant hit-rate,
Grayson-audited, recorded in `STATUS.md`.
