from mm_mcp.validator import validate_graph

CATALOG = {
    "perlin": {"type": "perlin", "inputs": [], "outputs": [{"type": "f"}],
               "parameters": [{"name": "scale_x", "type": "float",
                               "min": 1, "max": 32, "default": 4}]},
    "blend": {"type": "blend",
              "inputs": [{"name": "s1"}, {"name": "s2"}, {"name": "a"}],
              "outputs": [{"type": "rgba"}],
              "parameters": [{"name": "blend_type", "type": "enum",
                              "values": ["normal", "multiply"],
                              "min": 0, "max": 1, "default": 0}]},
}


def _good():
    return {"type": "graph", "nodes": [
        {"name": "p", "type": "perlin", "parameters": {"scale_x": 4}},
        {"name": "b", "type": "blend", "parameters": {"blend_type": 1}},
    ], "connections": [
        {"from": "p", "from_port": 0, "to": "b", "to_port": 0},
    ]}


def test_good_graph_has_no_errors():
    problems = validate_graph(_good(), CATALOG)
    assert [p for p in problems if p["severity"] == "error"] == []


def test_unknown_node_type_is_error():
    g = _good()
    g["nodes"][0]["type"] = "nope"
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("nope" in e["message"] for e in errs)


def test_dangling_connection_is_error():
    g = _good()
    g["connections"][0]["to"] = "missing"
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("missing" in e["message"] for e in errs)


def test_port_out_of_range_is_error():
    g = _good()
    g["connections"][0]["to_port"] = 9
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("port" in e["message"].lower() for e in errs)


def test_negative_to_port_is_error():
    g = _good()
    g["connections"][0]["to_port"] = -1
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("to_port" in e["message"] for e in errs)


def test_negative_from_port_is_error():
    g = _good()
    g["connections"][0]["from_port"] = -1
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("from_port" in e["message"] for e in errs)


def test_unknown_param_is_warning():
    """Material Maker's own loader (gen_base.gd deserialize) stores any key found
    under "parameters" unconditionally and never errors on it - stray/renamed
    parameter names from older files are silently ignored, not rejected. Match
    that tolerance: an unknown parameter is a warning, not a hard error, so it
    never fails the Phase 1 examples gate on legacy example files."""
    g = _good()
    g["nodes"][0]["parameters"] = {"bogus": 1}
    problems = validate_graph(g, CATALOG)
    errs = [p for p in problems if p["severity"] == "error"]
    warns = [p for p in problems if p["severity"] == "warning"]
    assert not any("bogus" in e["message"] for e in errs)
    assert any("bogus" in w["message"] for w in warns)


def test_param_out_of_range_is_warning():
    g = _good()
    g["nodes"][0]["parameters"] = {"scale_x": 999}
    warns = [p for p in validate_graph(g, CATALOG) if p["severity"] == "warning"]
    assert any("scale_x" in w["message"] for w in warns)


def test_numeric_param_out_of_range_reads_as_advisory():
    """A slider's min/max is an editor UI hint, not a shader clamp (verified:
    voronoi scale_x=40/44/48 render fine for the granite/aluminum cases). The
    message for a numeric param should say so, not read like a real problem."""
    g = _good()
    g["nodes"][0]["parameters"] = {"scale_x": 40}
    warns = [p for p in validate_graph(g, CATALOG) if p["severity"] == "warning"]
    msg = next(w["message"] for w in warns if "scale_x" in w["message"])
    assert "not shader-clamped" in msg
    assert "invalid" not in msg


def test_enum_param_out_of_range_reads_as_a_real_problem():
    """An enum's min/max is a valid-index range, not a UI hint - an
    out-of-range index is a genuine problem, so the message should say so."""
    g = _good()
    g["nodes"][1]["parameters"] = {"blend_type": 9}
    warns = [p for p in validate_graph(g, CATALOG) if p["severity"] == "warning"]
    msg = next(w["message"] for w in warns if "blend_type" in w["message"])
    assert "invalid" in msg


def test_special_type_is_accepted():
    g = _good()
    g["nodes"].append({"name": "c", "type": "comment", "parameters": {}})
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert errs == []


def test_malformed_graph_never_raises():
    """Regression: node missing 'name' and 'type'; connection missing port keys."""
    bad = {"type": "graph",
           "nodes": [{"parameters": {}}],
           "connections": [{"from": "p", "to": "p"}]}
    problems = validate_graph(bad, CATALOG)  # must NOT raise
    assert isinstance(problems, list)


def test_node_with_name_no_type_referenced_by_connection():
    """Regression: node has name but missing type, referenced in connection."""
    bad = {"type": "graph",
           "nodes": [{"name": "n1", "parameters": {}}],
           "connections": [{"from": "n1", "from_port": 0, "to": "n1", "to_port": 0}]}
    problems = validate_graph(bad, CATALOG)  # must NOT raise
    assert isinstance(problems, list)
    # Should have errors for unknown type and dangling connection (n1 not in catalog)
    errs = [p for p in problems if p["severity"] == "error"]
    assert len(errs) > 0


def test_node_missing_required_keys():
    """Regression: node is completely empty dict."""
    bad = {"type": "graph",
           "nodes": [{}],
           "connections": []}
    problems = validate_graph(bad, CATALOG)  # must NOT raise
    assert isinstance(problems, list)
    # Should report unknown type since type is missing (None)
    errs = [p for p in problems if p["severity"] == "error"]
    assert len(errs) > 0
