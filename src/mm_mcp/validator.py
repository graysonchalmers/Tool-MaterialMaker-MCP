from mm_mcp.catalog_builder import SPECIAL_TYPES


def validate_graph(ptex: dict, catalog: dict) -> list[dict]:
    problems = []
    nodes = ptex.get("nodes", [])
    by_name = {n["name"]: n for n in nodes}

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
                problems.append({"severity": "error", "where": n["name"],
                                 "message": f"unknown parameter '{pname}' for '{t}'"})
                continue
            spec = declared[pname]
            if isinstance(pval, (int, float)) and "min" in spec and "max" in spec:
                if pval < spec["min"] or pval > spec["max"]:
                    problems.append({"severity": "warning", "where": n["name"],
                                     "message": f"parameter '{pname}'={pval} outside "
                                                f"[{spec['min']}, {spec['max']}]"})

    for c in ptex.get("connections", []):
        for end in ("from", "to"):
            if c.get(end) not in by_name and c.get(end) not in ("graph",):
                problems.append({"severity": "error", "where": str(c),
                                 "message": f"connection references missing node '{c.get(end)}'"})
        src = by_name.get(c.get("from"))
        if src and src["type"] in catalog:
            n_out = len(catalog[src["type"]]["outputs"])
            if c.get("from_port", 0) >= n_out:
                problems.append({"severity": "error", "where": src["name"],
                                 "message": f"from_port {c['from_port']} out of range "
                                            f"(node has {n_out} outputs)"})
        dst = by_name.get(c.get("to"))
        if dst and dst["type"] in catalog:
            n_in = len(catalog[dst["type"]]["inputs"])
            if c.get("to_port", 0) >= n_in:
                problems.append({"severity": "error", "where": dst["name"],
                                 "message": f"to_port {c['to_port']} out of range "
                                            f"(node has {n_in} inputs)"})
    return problems
