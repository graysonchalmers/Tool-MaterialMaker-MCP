import hashlib
from mm_mcp.inspect import inspect_ptex


def _sample():
    return {
        "type": "graph",
        "nodes": [
            {"name": "mat", "type": "material"},
            {"name": "v1", "type": "voronoi"},
            {"name": "v2", "type": "voronoi"},
        ],
        "connections": [{"from": "v1", "from_port": 0, "to": "mat", "to_port": 0}],
    }


def test_counts_and_histogram():
    r = inspect_ptex(_sample())
    assert r["node_count"] == 3
    assert r["connection_count"] == 1
    assert r["node_types"] == {"material": 1, "voronoi": 2}
    assert r["material_outputs"] == ["mat"]


def test_sha256_present_when_bytes_given():
    raw = b'{"nodes":[],"connections":[]}'
    r = inspect_ptex({"nodes": [], "connections": []}, file_bytes=raw)
    assert r["sha256"] == hashlib.sha256(raw).hexdigest()


def test_sha256_none_when_no_bytes():
    r = inspect_ptex({"nodes": [], "connections": []})
    assert r["sha256"] is None


def test_missing_keys_are_tolerated():
    r = inspect_ptex({})
    assert r["node_count"] == 0
    assert r["connection_count"] == 0
    assert r["node_types"] == {}
    assert r["material_outputs"] == []
