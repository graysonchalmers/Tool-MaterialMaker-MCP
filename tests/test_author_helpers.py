"""Unit tests for quality/author.py's graph-surgery helpers (rewire, drop_conn).

These are pure JSON-graph transforms with no Godot/render dependency, but they
back every Phase 3 authoring recipe (denim's weave graft, granite's port-2
rewire, aluminum's grain-straightening, combo01's blend splice), so a bug here
would silently corrupt authored materials. Import path: quality/ isn't a
package, so we add it to sys.path directly rather than relying on pytest's
configured pythonpath (which only covers src/).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "quality"))

from author import rewire, drop_conn, node, add_node  # noqa: E402


def _graph():
    return {
        "nodes": [
            {"name": "a", "type": "perlin", "parameters": {}},
            {"name": "b", "type": "voronoi", "parameters": {}},
            {"name": "c", "type": "colorize", "parameters": {}},
        ],
        "connections": [
            {"from": "a", "from_port": 0, "to": "c", "to_port": 0},
        ],
    }


def test_node_finds_by_name():
    g = _graph()
    assert node(g, "b")["type"] == "voronoi"


def test_node_raises_on_missing_name():
    g = _graph()
    try:
        node(g, "nope")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_rewire_repoints_existing_connection():
    g = _graph()
    rewire(g, "c", 0, "b", 2)
    conns = [c for c in g["connections"] if c["to"] == "c" and c["to_port"] == 0]
    assert len(conns) == 1
    assert conns[0] == {"from": "b", "from_port": 2, "to": "c", "to_port": 0}


def test_rewire_appends_when_no_existing_connection():
    g = _graph()
    rewire(g, "c", 1, "b", 0)
    conns = [c for c in g["connections"] if c["to"] == "c" and c["to_port"] == 1]
    assert conns == [{"from": "b", "from_port": 0, "to": "c", "to_port": 1}]
    # the original (to_port 0) connection is untouched
    assert any(c["to_port"] == 0 and c["from"] == "a" for c in g["connections"])


def test_rewire_only_touches_the_matching_port():
    g = _graph()
    g["connections"].append({"from": "b", "from_port": 0, "to": "c", "to_port": 1})
    rewire(g, "c", 0, "b", 2)
    # to_port 1 connection must survive unchanged
    assert {"from": "b", "from_port": 0, "to": "c", "to_port": 1} in g["connections"]
    assert len(g["connections"]) == 2


def test_drop_conn_removes_matching_connection():
    g = _graph()
    drop_conn(g, "c", 0)
    assert g["connections"] == []


def test_drop_conn_is_noop_when_nothing_matches():
    g = _graph()
    before = list(g["connections"])
    drop_conn(g, "c", 5)
    assert g["connections"] == before


def test_drop_conn_only_removes_the_matching_port():
    g = _graph()
    g["connections"].append({"from": "b", "from_port": 0, "to": "c", "to_port": 1})
    drop_conn(g, "c", 1)
    assert g["connections"] == [{"from": "a", "from_port": 0, "to": "c", "to_port": 0}]


def test_add_node_appends_with_given_type_and_params():
    g = _graph()
    add_node(g, "d", "blend", {"blend_type": 0, "amount": 1})
    added = node(g, "d")
    assert added["type"] == "blend"
    assert added["parameters"] == {"blend_type": 0, "amount": 1}


def test_rewire_then_drop_conn_composes():
    """The combo01 pattern: rewire a Material input, then later drop it."""
    g = _graph()
    rewire(g, "c", 0, "b", 1)
    drop_conn(g, "c", 0)
    assert g["connections"] == []
