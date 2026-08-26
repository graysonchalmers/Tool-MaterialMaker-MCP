from mm_mcp.catalog_builder import SPECIAL_TYPES


def validate_graph(ptex: dict, catalog: dict) -> list[dict]:
    problems = []
    nodes = ptex.get("nodes", [])
    by_name = {n.get("name"): n for n in nodes if n.get("name") is not None}

    for n in nodes:
        t = n.get("type")
        if t in SPECIAL_TYPES:
            continue
        node_def = catalog.get(t)
        if node_def is None:
            problems.append({"severity": "error", "where": n.get("name", "?"),
                             "message": f"unknown node type '{t}'"})
            continue
        declared = {p["name"]: p for p in node_def["parameters"]}
        for pname, pval in (n.get("parameters") or {}).items():
            if pname not in declared:
                problems.append({"severity": "error", "where": n.get("name", "?"),
                                 "message": f"unknown parameter '{pname}' for '{t}'"})
                continue
            spec = declared[pname]
            if isinstance(pval, (int, float)) and "min" in spec and "max" in spec:
                if pval < spec["min"] or pval > spec["max"]:
                    problems.append({"severity": "warning", "where": n.get("name", "?"),
                                     "message": f"parameter '{pname}'={pval} outside "
                                                f"[{spec['min']}, {spec['max']}]"})

    for c in ptex.get("connections", []):
        for end in ("from", "to"):
            if c.get(end) not in by_name and c.get(end) not in ("graph",):
                problems.append({"severity": "error", "where": str(c),
                                 "message": f"connection references missing node '{c.get(end)}'"})
        src = by_name.get(c.get("from"))
        if src:
            src_type = src.get("type")
            if src_type in catalog:
                n_out = len(catalog[src_type]["outputs"])
                from_port = c.get("from_port", 0)
                if from_port >= n_out:
                    problems.append({"severity": "error", "where": src.get("name", "?"),
                                     "message": f"from_port {from_port} out of range "
                                                f"(node has {n_out} outputs)"})
        dst = by_name.get(c.get("to"))
        if dst:
            dst_type = dst.get("type")
            if dst_type in catalog:
                n_in = len(catalog[dst_type]["inputs"])
                to_port = c.get("to_port", 0)
                if to_port >= n_in:
                    problems.append({"severity": "error", "where": dst.get("name", "?"),
                                     "message": f"to_port {to_port} out of range "
                                                f"(node has {n_in} inputs)"})
    return problems
