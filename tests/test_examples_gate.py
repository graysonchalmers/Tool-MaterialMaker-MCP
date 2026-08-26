import glob
import json
import os
import pytest
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.validator import validate_graph

cfg = load_config()
CATALOG = build_catalog(cfg.nodes_dir)
EXAMPLES = sorted(glob.glob(os.path.join(cfg.examples_dir, "*.ptex")))


def _all_graphs(node):
    """Yield the node itself and every nested subgraph (has a 'nodes' list)."""
    if isinstance(node, dict) and "nodes" in node:
        yield node
        for child in node["nodes"]:
            yield from _all_graphs(child)


@pytest.mark.parametrize("path", EXAMPLES, ids=[os.path.basename(p) for p in EXAMPLES])
def test_example_has_no_type_or_connection_errors(path):
    with open(path, encoding="utf-8") as fh:
        root = json.load(fh)
    hard_errors = []
    for g in _all_graphs(root):
        for p in validate_graph(g, CATALOG):
            if p["severity"] == "error":
                hard_errors.append(p["message"])
    assert hard_errors == [], f"{os.path.basename(path)}: {hard_errors[:5]}"
