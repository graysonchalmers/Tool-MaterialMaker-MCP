from mm_mcp.catalog_builder import SPECIAL_TYPES


def _enum_literal_hint(spec: dict, pval) -> str | None:
    """If `pval` is out of an enum's index range but equals one of the enum's
    raw numeric `value` literals, return a hint naming the index the author
    almost certainly meant. This is the wavelet_noise.type trap that produced
    the t09 bug: type=-3 is the literal for index 4 ('Mult 3'), and Material
    Maker stores the index, not the literal. Returns None when the enum carries
    no confusable literals (value_literals is only populated for numeric,
    index-mismatched literals) or none matches `pval`."""
    literals = spec.get("value_literals")
    if not literals:
        return None
    for i, lit in enumerate(literals):
        try:
            if int(lit) == pval:
                names = spec.get("values", [])
                name = names[i] if i < len(names) else "?"
                return (f" - looks like the raw enum literal for index {i} "
                        f"('{name}'); Material Maker stores the index, use {i}")
        except (TypeError, ValueError):
            continue
    return None


def validate_graph(ptex: dict, catalog: dict, _path: str = "") -> list[dict]:
    problems = []
    nodes = ptex.get("nodes", [])
    by_name = {n.get("name"): n for n in nodes if n.get("name") is not None}
    # A subgraph node is itself type "graph" and carries its own nodes/connections;
    # prefix inner problems with the subgraph path so they stay locatable.
    prefix = f"{_path}/" if _path else ""

    def _where(w):
        return f"{prefix}{w}" if prefix else w

    for n in nodes:
        t = n.get("type")
        if t in SPECIAL_TYPES:
            continue
        node_def = catalog.get(t)
        if node_def is None:
            problems.append({"severity": "error", "where": _where(n.get("name", "?")),
                             "message": f"unknown node type '{t}'"})
            continue
        declared = {p["name"]: p for p in node_def["parameters"]}
        for pname, pval in (n.get("parameters") or {}).items():
            if pname not in declared:
                # Material Maker's own loader (gen_base.gd deserialize) sets any
                # key found under "parameters" unconditionally, so stray/renamed
                # parameter names from older files are silently stored and never
                # read rather than rejected. Match that tolerance: flag as a
                # warning, not a hard error.
                problems.append({"severity": "warning", "where": _where(n.get("name", "?")),
                                 "message": f"unknown parameter '{pname}' for '{t}'"})
                continue
            spec = declared[pname]
            if isinstance(pval, (int, float)) and "min" in spec and "max" in spec:
                if pval < spec["min"] or pval > spec["max"]:
                    if spec.get("type") == "enum":
                        # min/max on an enum are the valid index range, not a UI
                        # hint. An out-of-range index silently clamps to 0 (a
                        # wrong render), so it is a hard error, not an advisory
                        # warning (reclassified 2026-09-13 after t09 shipped a
                        # wrong index that every error-gated check let through).
                        severity = "error"
                        msg = (f"parameter '{pname}'={pval} outside enum index "
                               f"range [{spec['min']}, {spec['max']}]")
                        hint = _enum_literal_hint(spec, pval)
                        msg += hint if hint else (" - likely invalid, will "
                                                  "probably render wrong or fail")
                    else:
                        # min/max on a numeric slider come from Material
                        # Maker's editor UI, not a shader-enforced clamp;
                        # values outside it commonly still render correctly
                        # (e.g. a fine voronoi/perlin scale for flecks or
                        # brush streaks), so this is advisory, not alarming.
                        severity = "warning"
                        msg = (f"parameter '{pname}'={pval} outside the "
                               f"editor's default slider range "
                               f"[{spec['min']}, {spec['max']}] - not "
                               f"shader-clamped, often fine; verify visually")
                    problems.append({"severity": severity, "where": _where(n.get("name", "?")),
                                     "message": msg})

    for c in ptex.get("connections", []):
        for end in ("from", "to"):
            if c.get(end) not in by_name and c.get(end) not in ("graph",):
                problems.append({"severity": "error", "where": _where(str(c)),
                                 "message": f"connection references missing node '{c.get(end)}'"})
        src = by_name.get(c.get("from"))
        if src:
            src_type = src.get("type")
            if src_type in catalog:
                n_out = len(catalog[src_type]["outputs"])
                from_port = c.get("from_port", 0)
                if from_port < 0 or from_port >= n_out:
                    problems.append({"severity": "error", "where": _where(src.get("name", "?")),
                                     "message": f"from_port {from_port} out of range "
                                                f"(valid port indices are 0..{n_out - 1})"})
        dst = by_name.get(c.get("to"))
        if dst:
            dst_type = dst.get("type")
            if dst_type in catalog:
                n_in = len(catalog[dst_type]["inputs"])
                to_port = c.get("to_port", 0)
                if to_port < 0 or to_port >= n_in:
                    problems.append({"severity": "error", "where": _where(dst.get("name", "?")),
                                     "message": f"to_port {to_port} out of range "
                                                f"(valid port indices are 0..{n_in - 1})"})

    # Descend into subgraph nodes: a subgraph is a "graph"-typed node carrying its
    # own nodes/connections, which the top-level loops skip (graph is a SPECIAL_TYPE).
    # Recurse so dangling inner connections and unknown inner types are caught too.
    for n in nodes:
        if n.get("type") == "graph" and isinstance(n.get("nodes"), list):
            child_path = f"{_path}/{n.get('name', '?')}" if _path else n.get("name", "?")
            problems.extend(validate_graph(n, catalog, child_path))
    return problems
