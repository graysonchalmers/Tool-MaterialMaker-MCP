from collections import defaultdict, deque

from mm_mcp.catalog_builder import SPECIAL_TYPES
from mm_mcp.graph_schema import (
    are_ports_compatible, graph_connections, is_number, named_ports, node_schema,
    parameter_has_valid_type, problem, safe_export_suffix,
)


def _enum_literal_hint(spec: dict, value) -> str | None:
    """Recognize a raw numeric literal where Material Maker expects its ordinal."""
    for index, literal in enumerate(spec.get("value_literals", [])):
        try:
            if int(literal) == value:
                labels = spec.get("values", [])
                label = labels[index] if index < len(labels) else "?"
                return f" (looks like the raw literal for index {index} '{label}', use {index})"
        except (TypeError, ValueError):
            continue
    return None


def _parameter_problems(node: dict, schema: dict, where: str, *, strict: bool) -> list[dict]:
    params = node.get("parameters")
    if params is None:
        return []
    if not isinstance(params, dict):
        return [problem("invalid_parameters", where, "Node parameters must be an object")]
    findings = []
    declared = {p["name"]: p for p in schema["parameters"] if p.get("name")}
    for name, value in params.items():
        spec = declared.get(name)
        if spec is None:
            # Native Material Maker ignores unknown saved parameters. Keep them advisory.
            findings.append(problem("unknown_parameter", where,
                                    f"unknown parameter '{name}' for '{node.get('type')}'",
                                    severity="warning", alternatives=list(declared)))
            continue
        kind = spec.get("type")
        if node.get("type") == "export" and name == "suffix" and not safe_export_suffix(value):
            findings.append(problem("unsafe_export_filename", where,
                                    "Export suffix must be a filename without path components",
                                    alternatives=["$project-$node"]))
            continue
        # Native shader floats may reference exposed controls using a $name string.
        bound_float = (kind == "float" and isinstance(value, str) and value.startswith("$")
                       and value[1:].isidentifier())
        if (strict or node.get("type") == "export") and not bound_float and not parameter_has_valid_type(spec, value):
            findings.append(problem("invalid_parameter_type", where,
                                    f"parameter '{name}' must be of type {kind}",
                                    alternatives=spec.get("values")))
            continue
        lo, hi = spec.get("min"), spec.get("max")
        if not (is_number(value) and is_number(lo) and is_number(hi)) or lo <= value <= hi:
            continue
        if kind == "enum":
            choices = spec.get("values", [])
            details = _enum_literal_hint(spec, value)
            if not details and choices:
                details = " (valid: " + ", ".join(f"{i}={label}" for i, label in enumerate(choices)) + ")"
            findings.append(problem(
                "invalid_enum_index", where,
                f"parameter '{name}'={value} outside enum index range [{lo}, {hi}] - Material Maker "
                f"clamps an out-of-range index to 0 and renders the wrong option; use the option's INDEX{details or ''}",
                alternatives=choices,
            ))
        elif node.get("type") == "export" and name == "size":
            findings.append(problem("invalid_export_size", where,
                                    f"Export size exponent must be between {lo} and {hi}"))
        else:
            findings.append(problem(
                "outside_slider_range", where,
                f"parameter '{name}'={value} outside the editor's default slider range [{lo}, {hi}] - "
                "not shader-clamped, often fine; verify visually", severity="warning",
            ))
    return findings


def _cycles(edges: dict[str, set[str]]) -> set[str]:
    """Find unresolved dependencies in the graph of ordinary node connections."""
    incoming = dict.fromkeys(edges, 0)
    for targets in edges.values():
        for target in targets:
            incoming[target] = incoming.get(target, 0) + 1
    queue = deque(node for node, count in incoming.items() if not count)
    while queue:
        for target in edges.get(queue.popleft(), ()):
            incoming[target] -= 1
            if not incoming[target]:
                queue.append(target)
    return {node for node, count in incoming.items() if count}


def validate_graph(ptex: dict, catalog: dict, _path: str = "", *, strict: bool = False) -> list[dict]:
    """Check saved graph data. Strict mode checks graph-local schemas and topology."""
    where = _path or "$"
    if not isinstance(ptex, dict):
        return [problem("invalid_graph", where, "Graph must be an object")]
    nodes = ptex.get("nodes", [])
    if not isinstance(nodes, list):
        return [problem("invalid_graph", where, "Graph nodes must be an array")]
    try:
        connections = graph_connections(ptex)
    except ValueError as exc:
        return [problem("invalid_graph", where, str(exc))]
    prefix = f"{_path}/" if _path else ""
    findings = []
    by_name = {}
    schemas = {}
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            findings.append(problem("invalid_node", f"{prefix}nodes[{index}]", "Node must be an object"))
            continue
        name = node.get("name")
        if not isinstance(name, str) or not name:
            findings.append(problem("invalid_node_name", f"{prefix}nodes[{index}]", "Node needs a non-empty name"))
            continue
        node_where = f"{prefix}{name}"
        if name in by_name and strict:
            findings.append(problem("duplicate_node_name", node_where, f"Duplicate node name '{name}'"))
            continue
        by_name[name] = node
        node_type = node.get("type")
        if isinstance(node_type, str) and node_type in SPECIAL_TYPES and not strict:
            continue
        try:
            schema = node_schema(node, catalog, local=strict)
        except (AttributeError, KeyError, TypeError, ValueError):
            findings.append(problem("invalid_node_schema", node_where, "Malformed graph-local node definition"))
            continue
        if schema is None:
            if strict and node_type == "shader":
                findings.append(problem("missing_shader_model", node_where, "Inline shader needs a shader_model object"))
            elif not isinstance(node_type, str) or node_type not in SPECIAL_TYPES:
                findings.append(problem("unknown_node_type", node_where, f"unknown node type '{node_type}'"))
            continue
        schemas[name] = schema
        findings.extend(_parameter_problems(node, schema, node_where, strict=strict))

    if strict and not _path and not any(node.get("type") in ("material", "export") for node in by_name.values()):
        findings.append(problem("missing_output", where, "Graph needs a material or export output",
                                alternatives=["material", "export"]))

    occupied_inputs = set()
    dependencies = defaultdict(set)
    for index, connection in enumerate(connections):
        edge_where = f"{prefix}connections[{index}]"
        if not isinstance(connection, dict):
            findings.append(problem("invalid_connection", edge_where, "Connection must be an object"))
            continue
        types = []
        for side, direction in (("from", "outputs"), ("to", "inputs")):
            name = connection.get(side)
            if not isinstance(name, str) or (name != "graph" and name not in by_name):
                findings.append(problem("unknown_connection_node", edge_where,
                                        f"connection references missing node '{name}'", alternatives=list(by_name)))
                types.append(None)
                continue
            field = f"{side}_port"
            port = connection.get(field, None if strict else 0)
            schema = schemas.get(name)
            ports = named_ports(schema, direction) if schema is not None else None
            if type(port) is not int or port < 0 or (ports is not None and port >= len(ports)):
                available = f" (valid port indices are 0..{len(ports) - 1})" if ports else ""
                findings.append(problem("invalid_port_index", f"{prefix}{name}",
                                        f"{field} {port} out of range{available}", alternatives=ports))
                types.append(None)
                continue
            types.append(ports[port]["type"] if ports is not None else None)
            if strict and side == "to":
                if (name, port) in occupied_inputs:
                    findings.append(problem("duplicate_input_connection", edge_where,
                                            f"Input {name}[{port}] already has a source"))
                occupied_inputs.add((name, port))
        if strict and not are_ports_compatible(*types):
            findings.append(problem("incompatible_port_types", edge_where,
                                    f"Cannot connect {types[0]} to {types[1]}"))
        source, target = connection.get("from"), connection.get("to")
        # Subgraphs may route unrelated input/output pairs. Treating each as
        # a single vertex would report cycles that the native graph allows.
        if strict and all(isinstance(name, str) and name in by_name and by_name[name].get("type") != "graph"
                          for name in (source, target)):
            dependencies[source].add(target)

    if strict and (unresolved := _cycles(dependencies)):
        findings.append(problem("connection_cycle", where,
                                "A connection cycle blocks: " + ", ".join(sorted(unresolved))))
    for name, node in by_name.items():
        if strict and node.get("type") == "export" and (name, 0) not in occupied_inputs:
            findings.append(problem("unconnected_export", f"{prefix}{name}", "Export requires a texture input"))
    for node in nodes:
        if isinstance(node, dict) and node.get("type") == "graph":
            child_path = f"{prefix}{node.get('name', '?')}"
            findings.extend(validate_graph(node, catalog, child_path, strict=strict))
    return findings
