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
                # Material Maker's own loader (gen_base.gd deserialize) sets any
                # key found under "parameters" unconditionally, so stray/renamed
                # parameter names from older files are silently stored and never
                # read rather than rejected. Match that tolerance: flag as a
                # warning, not a hard error.
                problems.append({"severity": "warning", "where": n.get("name", "?"),
                                 "message": f"unknown parameter '{pname}' for '{t}'"})
                continue
            spec = declared[pname]
            if isinstance(pval, (int, float)) and "min" in spec and "max" in spec:
                if pval < spec["min"] or pval > spec["max"]:
                    if spec.get("type") == "enum":
                        # min/max on an enum are the valid index range, not a
                        # UI hint - an out-of-range index is a real problem.
                        msg = (f"parameter '{pname}'={pval} outside enum index "
                               f"range [{spec['min']}, {spec['max']}] - likely "
                               f"invalid, will probably render wrong or fail")
                    else:
                        # min/max on a numeric slider come from Material
                        # Maker's editor UI, not a shader-enforced clamp;
                        # values outside it commonly still render correctly
                        # (e.g. a fine voronoi/perlin scale for flecks or
                        # brush streaks), so this is advisory, not alarming.
                        msg = (f"parameter '{pname}'={pval} outside the "
                               f"editor's default slider range "
                               f"[{spec['min']}, {spec['max']}] - not "
                               f"shader-clamped, often fine; verify visually")
                    problems.append({"severity": "warning", "where": n.get("name", "?"),
                                     "message": msg})

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
                if from_port < 0 or from_port >= n_out:
                    problems.append({"severity": "error", "where": src.get("name", "?"),
                                     "message": f"from_port {from_port} out of range "
                                                f"(valid port indices are 0..{n_out - 1})"})
        dst = by_name.get(c.get("to"))
        if dst:
            dst_type = dst.get("type")
            if dst_type in catalog:
                n_in = len(catalog[dst_type]["inputs"])
                to_port = c.get("to_port", 0)
                if to_port < 0 or to_port >= n_in:
                    problems.append({"severity": "error", "where": dst.get("name", "?"),
                                     "message": f"to_port {to_port} out of range "
                                                f"(valid port indices are 0..{n_in - 1})"})
    return problems
