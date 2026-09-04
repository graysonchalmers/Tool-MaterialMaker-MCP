# cookbook/

Tracked, authored Material Maker graphs: one `.ptex` per material, grouped by
category. These are the shipped form of the cookbook that `quality/cookbook_*.py`
builds and `docs/AUTHORING.md` explains.

## Use

- **In Material Maker:** open any `<category>/<id>.ptex`. The node network is
  the worked example; tweak it, save it somewhere else, keep iterating.
- **Over MCP:** `list_examples(source="cookbook")` lists them with their
  category; `load_example("<id>")` returns the graph. `mm-mcp --check` reports
  how many the server can see.
- **Config:** the server finds this folder automatically from a source
  checkout. Set `MM_COOKBOOK_DIR` to point it somewhere else.

## Regenerate

The builders are the source; this folder is their locked output.

1. Rebuild a category: `.venv\Scripts\python.exe quality\cookbook_<category>.py`
2. Verify nothing drifted: `.venv\Scripts\python.exe quality\promote_cookbook.py --check`
3. Accept new output: `.venv\Scripts\python.exe quality\promote_cookbook.py`

`tests/test_cookbook_gate.py` validates every graph here against the node
catalog and checks that each has a thumbnail under `docs/images/cookbook-<category>/`.
