"""Unit tests for quality/author_helpers.py's graph-surgery helpers (rewire, drop_conn).

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

from author_helpers import rewire, drop_conn, node, add_node, group_into_subgraph  # noqa: E402


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


_FAKE_CATALOG = {
    "perlin": {"inputs": [], "outputs": [{"type": "f"}], "parameters": []},
    "colorize": {
        "inputs": [{"name": "in", "type": "f", "desc": ""}],
        "outputs": [{"type": "rgba"}], "parameters": [],
    },
    "material": {
        "inputs": [{"name": "albedo", "type": "rgb", "desc": ""}],
        "outputs": [], "parameters": [],
    },
}


def _simple_graph():
    return {
        "nodes": [
            {"name": "perlin_0", "type": "perlin",
             "node_position": {"x": 0, "y": 0},
             "parameters": {"scale": 4}},
            {"name": "colorize_0", "type": "colorize",
             "node_position": {"x": 200, "y": 0},
             "parameters": {"amount": 1}},
            {"name": "Material", "type": "material",
             "node_position": {"x": 400, "y": 0},
             "parameters": {}},
        ],
        "connections": [
            {"from": "perlin_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
            {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
        ],
    }


def test_group_into_subgraph_collapses_named_nodes():
    g = _simple_graph()
    group_into_subgraph(
        g, ["perlin_0"], "base_noise", "Base Noise",
        [("perlin_0", "scale", "param0", "Scale")], _FAKE_CATALOG,
    )
    names = {n["name"] for n in g["nodes"]}
    assert "perlin_0" not in names
    assert "base_noise" in names
    assert "colorize_0" in names and "Material" in names


def test_group_into_subgraph_new_node_is_type_graph_with_exposed_param():
    g = _simple_graph()
    group_into_subgraph(
        g, ["perlin_0"], "base_noise", "Base Noise",
        [("perlin_0", "scale", "param0", "Scale")], _FAKE_CATALOG,
    )
    collapsed = node(g, "base_noise")
    assert collapsed["type"] == "graph"
    assert collapsed["label"] == "Base Noise"
    assert collapsed["parameters"]["param0"] == 4
    remote = next(n for n in collapsed["nodes"] if n["type"] == "remote")
    widget = remote["widgets"][0]
    assert widget["name"] == "param0"
    assert widget["shortdesc"] == "Scale"
    assert widget["linked_widgets"] == [{"node": "perlin_0", "widget": "scale"}]


def test_group_into_subgraph_preserves_outer_wiring():
    g = _simple_graph()
    group_into_subgraph(
        g, ["perlin_0"], "base_noise", "Base Noise",
        [("perlin_0", "scale", "param0", "Scale")], _FAKE_CATALOG,
    )
    # perlin_0 -> colorize_0 becomes base_noise -> colorize_0
    outer = [c for c in g["connections"] if c["to"] == "colorize_0"]
    assert outer == [{"from": "base_noise", "from_port": 0,
                       "to": "colorize_0", "to_port": 0}]
    # colorize_0 -> Material is untouched (neither endpoint was grouped)
    untouched = [c for c in g["connections"] if c["to"] == "Material"]
    assert untouched == [{"from": "colorize_0", "from_port": 0,
                           "to": "Material", "to_port": 0}]


def test_group_into_subgraph_handles_incoming_and_outgoing_boundary():
    g = _simple_graph()
    group_into_subgraph(
        g, ["colorize_0"], "recolor", "Recolor", [], _FAKE_CATALOG,
    )
    collapsed = node(g, "recolor")
    gen_inputs = next(n for n in collapsed["nodes"] if n["name"] == "gen_inputs")
    gen_outputs = next(n for n in collapsed["nodes"] if n["name"] == "gen_outputs")
    assert len(gen_inputs["ports"]) == 1
    assert gen_inputs["ports"][0]["type"] == "f"       # perlin_0's output type
    assert len(gen_outputs["ports"]) == 1
    assert gen_outputs["ports"][0]["type"] == "rgba"   # colorize_0's output type
    # parent-level connections now point at "recolor" instead of "colorize_0"
    assert {"from": "perlin_0", "from_port": 0,
            "to": "recolor", "to_port": 0} in g["connections"]
    assert {"from": "recolor", "from_port": 0,
            "to": "Material", "to_port": 0} in g["connections"]
    # the internal connection is rehomed onto gen_inputs/gen_outputs
    inner = collapsed["connections"]
    assert {"from": "gen_inputs", "from_port": 0,
            "to": "colorize_0", "to_port": 0} in inner
    assert {"from": "colorize_0", "from_port": 0,
            "to": "gen_outputs", "to_port": 0} in inner
