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
    assert len(ENTRIES) >= 53, f"expected at least the 53 promoted graphs, found {len(ENTRIES)}"


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


def test_gate_rejects_an_out_of_range_enum_index():
    """Ratchet (2026-09-13): prove the gate ITSELF rejects an out-of-range enum
    index, not merely that validate_graph can emit one. This is the exact class
    of bug t09 shipped (wavelet type=-3 -> should be index 4); it slipped
    through only because an out-of-range enum was a warning and this gate
    collects errors. Inject a bad enum index into a copy of a real cookbook
    graph and assert the gate's own hard-error collection is non-empty, so a
    future refactor that stops treating it as an error breaks here."""
    with open(ENTRIES[0].path, encoding="utf-8") as fh:
        root = json.load(fh)
    # blend.blend_type is a universal enum (indices 0..14); 99 is out of range.
    root.setdefault("nodes", []).append(
        {"name": "_bad_enum_probe", "type": "blend",
         "parameters": {"blend_type": 99}})
    hard_errors = []
    for g in _all_graphs(root):
        for p in validate_graph(g, CATALOG):
            if p["severity"] == "error":
                hard_errors.append(p["message"])
    assert any("blend_type" in m for m in hard_errors), hard_errors


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
