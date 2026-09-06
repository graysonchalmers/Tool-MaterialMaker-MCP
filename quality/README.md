# quality/: the cookbook factory

A Python package (`from quality.<module> import ...`; run scripts as
`python -m quality.<module>` from the repo root). The scripts import
`mm_mcp`, so the editable install (`pip install -e .`, see the root README)
is a prerequisite. Not shipped in the wheel: everything here needs Godot and
a Material Maker checkout. The tracked
`cookbook/` tree is its locked output; `docs/AUTHORING.md` holds the
invariants the builders follow.

## Layout

- `cookbook_<category>.py` (twelve): builders, one `build_<id>(catalog)` per
  material, `BUILDERS` dict, `main()` builds the catalog once and threads it
  through. Output: `quality/authored/cookbook-<category>/<id>/v1.ptex`
  (gitignored). Every builder ends with `rename_nodes(g, {...})` so the
  shipped graph carries role names (see `docs/AUTHORING.md`, Name every node
  by role).
- `author_helpers.py`: pure graph-surgery helpers (`load_example`, `node`,
  `set_param`, `set_gradient`, `rewire`, `drop_conn`, `add_node`, `retype`,
  `rename_nodes`, `save_variant`, `take_variant`, `group_into_subgraph`). No Godot.
- `author.py`: the material builders six categories import as their base.
  Edit freely; `--check` is the guard.
- `promote_cookbook.py`: copies each `v1.ptex` into `cookbook/<category>/<id>.ptex`;
  `--check` diffs regenerated output against the tracked copies and exits 1
  on drift. This is the regression baseline for the whole cookbook.
- `render_cookbook.py <label>` / `render_one.py <label> <case> [size]`:
  validate + render authored variants to `quality/cookbook/<label>/`
  (gitignored) for eyeballing. One Godot at a time. Run as a module, never
  from `python -c`.
- `naming.py`: the role-name rules for cookbook nodes and a checker
  (`python -m quality.naming --cookbook [category]`, exit 1 on any
  auto-name, bare type name, or sibling collision). `tests/test_naming.py`
  covers the rules; the rename pass (2026-09-06) is what gets the real
  `cookbook/` tree to pass this check category by category. The gate test
  `tests/test_cookbook_naming_gate.py` runs the same check over every
  tracked graph.
- `render_tracked.py`: renders the tracked `cookbook/` graphs one Godot at a
  time into a directory and, with `--compare BASELINE`, proves a builder
  change moved no pixels (`render_compare.renders_match`). Used by the
  2026-09-06 rename pass with `output/naming-baseline` as the baseline.
- `_make_previews.py <label>` and `contact_sheet.py [labels]`: thumbnails
  under `docs/images/cookbook-<category>/` and the README contact sheet
  (save as an 8-bit palette).
- `render_compare.py`: `grid_mean_abs_diff`, `renders_match` (builder-before
  vs builder-after; it does not prove the tracked artifact was right).
- `debug_swatches.py`, `noise_gallery.py`, `pngread.py`: the diagnostic
  swatch gallery (`docs/DEBUG_SWATCHES.md`), the noise vocabulary gallery,
  and the vendored stdlib PNG reader used to verify ORM channels by value.
- `donors/`: the nine vendored Material Maker example graphs the builders
  start from (tracked; `tests/test_donors.py`).

## Workflow

1. Add or edit a builder in `cookbook_<category>.py`; call
   `group_into_subgraph` before `save_variant` returns.
2. `python -m quality.cookbook_<category> [case ...]` regenerates the variants.
3. `python -m quality.render_one cookbook-<category> <id>` to look; judge
   relief in 3D (`render_preview`), verify metallic/roughness/AO with
   `pngread`, not by eye.
4. `python -m quality.promote_cookbook --check` to see what would change;
   `python -m quality.promote_cookbook` to accept. Write or update the card
   `cookbook/<category>/<id>.md` and regenerate the thumbnail.
5. `tests/test_cookbook_gate.py` and `test_cookbook_subgraph_gate.py` keep
   every tracked graph valid, grouped, carded, and thumbnailed.

Run from the repo root (`.env` is read from the working directory). Godot
is not byte-deterministic, so a category-wide re-render can churn unrelated
thumbnails; `git status` and revert anything swept up.

## History

The Phase-3 authoring-quality gate (15/15 on a frozen 15-case set,
2026-08-26) was measured with a runner that lived here. Its frozen test set,
rubric, and scorecards are archived under `docs/evidence/phase3/`; the runner
is retired (see that folder's README).
