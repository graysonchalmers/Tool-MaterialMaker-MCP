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
    # wavelet_noise's real trap: numeric literals that don't equal their index.
    "wav": {"type": "wav", "inputs": [], "outputs": [{"type": "f"}],
            "parameters": [{"name": "type", "type": "enum",
                            "values": ["Add 1", "Add 2", "Add 3",
                                       "Mult 2", "Mult 3"],
                            "value_literals": ["1", "2", "3", "-2", "-3"],
                            "min": 0, "max": 4, "default": 4}]},
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


def test_enum_param_out_of_range_is_an_error():
    """An enum's min/max is a valid-index range, not a UI hint. An out-of-range
    index silently clamps to 0 (a wrong render), so it is a hard error, not an
    advisory warning - reclassified 2026-09-13 after t09 shipped a wrong enum
    index that every error-gated check (test_cookbook_gate, render_tracked) let
    through because it was only a warning."""
    g = _good()
    g["nodes"][1]["parameters"] = {"blend_type": 9}
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    msg = next(e["message"] for e in errs if "blend_type" in e["message"])
    # names the options by index and explains the clamp, so the fix is obvious
    assert "enum index range" in msg
    assert "clamp" in msg
    assert "INDEX" in msg
    assert "0=normal" in msg and "1=multiply" in msg
    # numeric slider ranges stay advisory warnings, not errors
    warns = [p for p in validate_graph(g, CATALOG) if p["severity"] == "warning"]
    assert not any("blend_type" in w["message"] for w in warns)


def test_enum_out_of_range_names_intended_index_when_literal_matches():
    """When the out-of-range value is one of the enum's numeric literals, the
    error names the index the author almost certainly meant. This is the exact
    t09 case: type=-3 is the literal for index 4 ('Mult 3')."""
    g = _good()
    g["nodes"].append({"name": "w", "type": "wav", "parameters": {"type": -3}})
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    msg = next(e["message"] for e in errs if e["where"] == "w")
    assert "index 4" in msg
    assert "Mult 3" in msg


def test_enum_out_of_range_without_matching_literal_still_errors_generically():
    """An out-of-range enum value that matches no known literal is still a hard
    error, with the generic message (no crash when there is nothing to name)."""
    g = _good()
    g["nodes"].append({"name": "w", "type": "wav", "parameters": {"type": 99}})
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    msg = next(e["message"] for e in errs if e["where"] == "w")
    assert "outside enum index range" in msg
    assert "index" in msg


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


def _nested():
    """A top-level graph carrying one subgraph node ('sub') with a clean interior."""
    g = _good()
    g["nodes"].append({"name": "sub", "type": "graph", "nodes": [
        {"name": "ip", "type": "perlin", "parameters": {"scale_x": 4}},
        {"name": "ib", "type": "blend", "parameters": {"blend_type": 1}},
    ], "connections": [
        {"from": "ip", "from_port": 0, "to": "ib", "to_port": 0},
    ]})
    return g


def test_clean_subgraph_has_no_errors():
    errs = [p for p in validate_graph(_nested(), CATALOG) if p["severity"] == "error"]
    assert errs == []


def test_dangling_connection_inside_subgraph_is_error():
    """Regression (found by dogfooding the MCP path 2026-09-06): a connection to a
    missing node INSIDE a subgraph must be reported, and be locatable to the
    subgraph by name."""
    g = _nested()
    g["nodes"][-1]["connections"][0]["to"] = "missing"
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("missing" in e["message"] for e in errs)
    assert any("sub" in str(e["where"]) for e in errs)


def test_unknown_node_type_inside_subgraph_is_error():
    g = _nested()
    g["nodes"][-1]["nodes"][0]["type"] = "nope"
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("nope" in e["message"] for e in errs)
    assert any("sub" in str(e["where"]) for e in errs)


def test_port_out_of_range_inside_subgraph_is_error():
    g = _nested()
    g["nodes"][-1]["connections"][0]["to_port"] = 9
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("port" in e["message"].lower() for e in errs)
    assert any("sub" in str(e["where"]) for e in errs)


def test_deeply_nested_subgraph_is_validated():
    """Recursion must reach a subgraph inside a subgraph."""
    g = _nested()
    inner = {"name": "deep", "type": "graph", "nodes": [
        {"name": "dp", "type": "nope", "parameters": {}},
    ], "connections": []}
    g["nodes"][-1]["nodes"].append(inner)
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("nope" in e["message"] for e in errs)
    assert any("sub/deep" in str(e["where"]) for e in errs)
