"""Gate: every recipe card's generated node table matches the tracked graph
beside it, so a hand-written card or a stale table fails CI, not just
promote --check."""
import json
import os
from pathlib import Path

import pytest
from mm_mcp.cookbook import list_cookbook
from quality.promote_cookbook import check_card_block

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKBOOK_DIR = os.path.join(_ROOT, "cookbook")
ENTRIES = list_cookbook(COOKBOOK_DIR)


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_card_node_table_matches_tracked_graph(entry):
    with open(entry.path, encoding="utf-8") as fh:
        graph = json.load(fh)
    card = Path(entry.path).with_suffix(".md")
    assert check_card_block(card, graph) is None
