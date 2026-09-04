# quality/ - Phase 3 authoring-quality harness

Measures whether prompt-to-graph authoring produces usable materials.

## Layout

- `test_set.json`: the 15 frozen cases + the scoring rubric (`_rubric`).
- `run_case.py`: renders authored variants for a case and (re)builds the
  scorecard. Reuses `mm_mcp` render + validate; adds no render logic.
- `runs/<run>/<case_id>/variant_N/`: per-variant outputs, 4 PBR maps +
  `source.ptex`. `runs/<run>/<case_id>/_result.json` holds the case's render
  results and the judge verdict fields.
- `scorecards/<run>.md`: one auto-generated scorecard per run.
- `scorecards/README.md`: the freeze rule for the test set.

## Flow

1. Claude authors 2-3 variant `.ptex` graphs for a case (this is what Phase 3
   measures).
2. `run_case.py --run <label> --case <id> --variants a.ptex b.ptex c.ptex`
   validates + renders each and writes `_result.json`.
3. The judge (Claude vision) fills the `verdict` block in each `_result.json`
   against the rubric; Grayson audits.
4. `run_case.py --run <label> --rebuild-scorecard` regenerates the Markdown.

## Runs are named, not numbered

- `<date>-baseline`: the 3B control (no AUTHORING.md recipes).
- `<date>-iter<N>`: each 3C tuning iteration.

The **gate** is a scorecard showing >= 70% (>= 11/15) any-variant hit-rate,
Grayson-audited, recorded in `STATUS.md`.

## Cookbook growth (beyond the frozen 15)

`test_set.json`'s 15 cases are frozen (see its `_meta`/freeze note) and stay
that way. To grow the recipe library into new material categories WITHOUT
touching frozen infra, use the `cookbook_fabrics.py` pattern instead of
`author.py`/`run_case.py`: a small `quality/cookbook_<category>.py` (same
graph-surgery helpers, imported from `author.py`) writes variants to
`quality/authored/cookbook-<category>/`, and `render_cookbook.py <label>`
validates + renders them to `quality/cookbook/<label>/` for eyeballing, no
`test_set.json` entry, no scorecard, no gate. Invariants that generalize
across materials belong in `docs/AUTHORING.md` (the lean guide, also served
as the `guide://authoring` resource); a recipe that pans out for one material
gets written up in that graph's own card, `cookbook/<category>/<id>.md`.
Both output dirs are gitignored (regenerable).

When a material is locked (rendered, 3D-previewed, written up), promote it:
`python quality/promote_cookbook.py` copies each `v1.ptex` into the tracked
`cookbook/<category>/<id>.ptex` tree the MCP server serves through
`list_examples` / `load_example`. `promote_cookbook.py --check` diffs
regenerated output against the tracked copies and exits 1 on any drift, which
is the regression baseline for the cookbook (non-scorecard) materials.

While iterating on ONE material, use `render_one.py <label> <case>` (renders a
single case, one Godot at a time) instead of `render_cookbook.py` (which renders
every case under the label). Run either as a script FILE, never `python -c`.
Driving a Godot render from `python -c` leaves the launcher process not exiting
and reads as a bogus 180s timeout.
