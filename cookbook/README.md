# cookbook/

Tracked, authored Material Maker graphs: one `.ptex` per material, grouped by
category. These are the shipped form of the cookbook that `quality/cookbook_*.py`
builds; the invariants behind them are in `docs/AUTHORING.md`.

## Use

- **In Material Maker:** open any `<category>/<id>.ptex`. The node network is
  the worked example; tweak it, save it somewhere else, keep iterating.
- **Over MCP:** `list_examples(source="cookbook")` lists them with their
  category; `load_example("<id>")` returns the graph. `mm-mcp --check` reports
  how many the server can see.
- **Config:** the server finds this folder automatically from a source
  checkout. Set `MM_COOKBOOK_DIR` to point it somewhere else.

## Recipe cards

Each graph has a recipe card beside it, `<category>/<id>.md`, describing what
it is, the levers that made it work, and where to look in the graph.

Every card ends with a generated `## Nodes` table between `<!-- nodes:begin -->`
and `<!-- nodes:end -->` markers: one row per node in the shipped graph with the
subgraph it lives in and its type. `python -m quality.promote_cookbook` writes
it and `--check` fails if it is missing or stale, so the card and the `.ptex`
cannot disagree about node names. Prose above the markers is hand-written and
may mention donor nodes (`wood`'s `colorize_2`) as the recipe's starting point;
the table is the map of what is actually in the file.

## Regenerate

The builders are the source; this folder is their locked output.

1. Rebuild a category: `.venv\Scripts\python.exe -m quality.cookbook_<category>`
2. Verify nothing drifted: `.venv\Scripts\python.exe -m quality.promote_cookbook --check`
3. Accept new output: `.venv\Scripts\python.exe -m quality.promote_cookbook`

`tests/test_cookbook_gate.py` validates every graph here against the node
catalog and checks that each has a thumbnail under `docs/images/cookbook-<category>/`
and a recipe card.
