"""Phase A gate for cookbook-as-data: every tracked cookbook graph validates
against the catalog with zero hard errors, ids are unique across categories,
and every graph has its thumbnail. Mirrors tests/test_examples_gate.py."""
import json
import os
import pytest
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.cookbook import list_cookbook
from mm_mcp.validator import validate_graph

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKBOOK_DIR = os.path.join(_ROOT, "cookbook")
ENTRIES = list_cookbook(COOKBOOK_DIR)
cfg = load_config()
CATALOG = build_catalog(cfg.nodes_dir)


def _all_graphs(node):
    """Yield the node itself and every nested subgraph (has a 'nodes' list)."""
    if isinstance(node, dict) and "nodes" in node:
        yield node
        for child in node["nodes"]:
            yield from _all_graphs(child)


def test_cookbook_is_populated():
    assert len(ENTRIES) >= 43, f"expected the 43 promoted graphs, found {len(ENTRIES)}"


def test_cookbook_ids_are_unique_across_categories():
    names = [e.name for e in ENTRIES]
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert dupes == []


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_cookbook_graph_has_no_type_or_connection_errors(entry):
    with open(entry.path, encoding="utf-8") as fh:
        root = json.load(fh)
    hard_errors = []
    for g in _all_graphs(root):
        for p in validate_graph(g, CATALOG):
            if p["severity"] == "error":
                hard_errors.append(p["message"])
    assert hard_errors == [], f"{entry.name}: {hard_errors[:5]}"


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_cookbook_graph_has_thumbnail(entry):
    thumb = os.path.join(_ROOT, "docs", "images", f"cookbook-{entry.category}",
                         f"{entry.name}.png")
    assert os.path.isfile(thumb), f"missing thumbnail {thumb}"


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_cookbook_graph_has_recipe_card(entry):
    card = os.path.join(os.path.dirname(entry.path), f"{entry.name}.md")
    assert os.path.isfile(card), f"missing recipe card {card}"
    assert os.path.getsize(card) > 200, f"card too small to be a real recipe: {card}"
