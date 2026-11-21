"""Describe and edit saved Material Maker graphs without touching a live tab."""

from copy import deepcopy

from mm_mcp.graph_schema import (
    EDITABLE_PARAMETER_TYPES, graph_connections, is_number, named_ports, node_schema,
    parameter_has_valid_type, problem, safe_export_suffix, set_graph_connections,
)
from mm_mcp.play.sliders import apply_values
from mm_mcp.validator import validate_graph


class GraphEditError(ValueError):
    def __init__(self, finding: dict):
        super().__init__(finding["message"])
        self.problem = finding


def _graph_nodes(graph: dict) -> list[dict]:
    nodes = graph.get("nodes", []) if isinstance(graph, dict) else None
    if not isinstance(nodes, list):
        _fail("invalid_graph", "$", "Graph nodes must be an array")
    return [node for node in nodes if isinstance(node, dict) and node.get("name")]


def _walk_nodes(graph: dict, prefix: str = ""):
    for node in _graph_nodes(graph):
        path = f"{prefix}{node['name']}"
        yield path, node
        if node.get("type") == "graph":
            yield from _walk_nodes(node, f"{path}/")


def _describe_connections(graph: dict, prefix: str = "") -> list[dict]:
    connections = [{**edge, "from": f"{prefix}{edge.get('from', '')}",
                     "to": f"{prefix}{edge.get('to', '')}"}
                    for edge in _connection_array(graph, prefix.rstrip("/") or "$") if isinstance(edge, dict)]
    for node in _graph_nodes(graph):
        if node.get("type") == "graph":
            connections.extend(_describe_connections(node, f"{prefix}{node['name']}/"))
    return connections


def _control(path: str, node: dict, spec: dict) -> dict:
    name = spec["name"]
    params = node.get("parameters")
    value = params.get(name, spec.get("default")) if isinstance(params, dict) else spec.get("default")
    output = {key: spec[key] for key in ("name", "type", "default", "min", "max", "step", "values") if key in spec}
    output.update({"id": f"{path}/{name}", "node": path, "value": value,
                   "label": spec.get("desc") or name,
                   "editable": spec.get("type") in EDITABLE_PARAMETER_TYPES
                   or (node.get("type") == "export" and name == "suffix")})
    if spec.get("type") == "enum" and isinstance(value, (int, float)):
        choices = spec.get("values", [])
        if parameter_has_valid_type(spec, value) and 0 <= value < len(choices):
            output["value_label"] = choices[int(value)]
    return output


def describe_graph(graph: dict, catalog: dict) -> dict:
    """Describe selectable controls, ports and exports without returning shader code."""
    nodes, controls, exports = [], [], []
    for path, node in _walk_nodes(graph):
        schema = _schema(node, catalog, path)
        entry = {"path": path, "type": node.get("type"), "label": node.get("label") or node["name"]}
        if schema is not None:
            entry["inputs"] = named_ports(schema, "inputs")
            entry["outputs"] = named_ports(schema, "outputs")
            controls.extend(_control(path, node, spec) for spec in schema["parameters"] if spec.get("name"))
        nodes.append(entry)
        if node.get("type") == "export":
            params = {spec["name"]: _control(path, node, spec) for spec in schema["parameters"]}
            exports.append({"node": path, "type": "export", "suffix": params["suffix"]["value"],
                            "size_exponent": params["size"]["value"],
                            "format": params["format"].get("value_label")})
        elif node.get("type") == "material":
            exports.append({"node": path, "type": "material"})
    return deepcopy({"nodes": nodes, "controls": controls, "exports": exports,
                     "connections": _describe_connections(graph)})


def _fail(code: str, where: str, message: str, alternatives: list | None = None):
    raise GraphEditError(problem(code, where, message, alternatives=alternatives))


def _schema(node: dict, catalog: dict, where: str) -> dict | None:
    try:
        return node_schema(node, catalog)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise GraphEditError(problem("invalid_node_schema", where, "Malformed graph-local node definition")) from exc


def _connection_array(graph: dict, where: str) -> list:
    try:
        return graph_connections(graph)
    except ValueError as exc:
        raise GraphEditError(problem("invalid_graph", where, str(exc))) from exc


def _resolve_node(graph: dict, path) -> tuple[dict, dict]:
    if not isinstance(path, str) or not path:
        _fail("invalid_node_path", "$", "Select a named node path")
    scope = graph
    parts = path.split("/")
    for depth, part in enumerate(parts):
        nodes = _graph_nodes(scope)
        matches = [node for node in nodes if node["name"] == part]
        if len(matches) != 1:
            prefix = "/".join(parts[:depth])
            alternatives = [f"{prefix}/{node['name']}" if prefix else node["name"] for node in nodes]
            _fail("ambiguous_node" if matches else "unknown_node", path,
                  f"Cannot resolve node path '{path}'", alternatives)
        node = matches[0]
        if depth == len(parts) - 1:
            return scope, node
        if node.get("type") != "graph":
            _fail("invalid_node_path", path, f"'{part}' is not a subgraph")
        scope = node


def _parameter_name(specs: list[dict], name) -> dict | None:
    matches = [spec for spec in specs if spec.get("name") == name or spec.get("desc") == name]
    exact = next((spec for spec in matches if spec.get("name") == name), None)
    return exact or (matches[0] if len(matches) == 1 else None)


def _parameter_value(spec: dict, value, path: str, *, export_suffix: bool = False):
    kind = spec.get("type")
    choices = spec.get("values", [])
    if kind == "enum" and isinstance(value, str):
        matches = [index for index, choice in enumerate(choices)
                   if isinstance(choice, str) and value.strip().casefold() == choice.casefold()]
        if len(matches) == 1:
            return matches[0]
        _fail("invalid_enum_label", path, f"Unknown or ambiguous enum label '{value}'", choices)
    if kind not in EDITABLE_PARAMETER_TYPES and not export_suffix:
        _fail("unsupported_parameter_type", path, f"Native type {kind or 'unknown'} has no typed patch support")
    if not parameter_has_valid_type(spec, value):
        _fail("invalid_parameter_type", path, f"Parameter value must have native type {kind or 'unknown'}",
              choices or None)
    if kind in {"size", "int", "seed", "enum"}:
        value = int(value)
    if kind == "enum" and not 0 <= value < len(choices):
        _fail("invalid_enum_index", path, "Enum index is out of range", choices)
    if kind in {"float", "size", "int", "seed"}:
        minimum, maximum = spec.get("min"), spec.get("max")
        if (is_number(minimum) and value < minimum) or (is_number(maximum) and value > maximum):
            range_spec = {key: spec[key] for key in ("min", "max", "step") if key in spec}
            _fail("parameter_out_of_range", path, "Value falls outside the exposed control range", [range_spec])
    return value


def _set_parameter(graph: dict, edit: dict, catalog: dict) -> dict:
    path = edit.get("node")
    _, node = _resolve_node(graph, path)
    schema = _schema(node, catalog, path)
    specs = schema["parameters"] if schema is not None else []
    name = edit.get("parameter")
    spec = _parameter_name(specs, name) if isinstance(name, str) and name else None
    if spec is None:
        _fail("unknown_parameter", path, f"Unknown or ambiguous parameter '{name}'",
              [spec["name"] for spec in specs if spec.get("name")])
    name = spec["name"]
    where = f"{path}/{name}"
    if "value" not in edit:
        _fail("missing_parameter_value", where, "Set-parameter edit needs a value")
    export_suffix = node.get("type") == "export" and name == "suffix"
    value = _parameter_value(spec, edit["value"], where, export_suffix=export_suffix)
    if export_suffix and not safe_export_suffix(value):
        _fail("unsafe_export_filename", where, "Export suffix must be a filename without path components",
              ["$project-$node"])
    params = node.setdefault("parameters", {})
    if not isinstance(params, dict):
        _fail("invalid_parameters", path, "Node parameters must be an object")
    old_value = params.get(name, spec.get("default"))
    if node.get("type") == "graph":
        # Reuse the established control application path for linked bindings.
        applied = apply_values({"nodes": [node]}, {f"{node['name']}/{name}": value})["nodes"][0]
        node.update(applied)
    else:
        params[name] = deepcopy(value)
    return {"op": "set_param", "node": path, "parameter": name, "before": old_value, "after": value}


def _resolve_port(node: dict, selector, direction: str, path: str, catalog: dict) -> int:
    schema = _schema(node, catalog, path)
    if schema is None:
        _fail("unknown_port_schema", path, f"No {direction} schema is available for this node")
    ports = named_ports(schema, direction)
    if type(selector) is int and 0 <= selector < len(ports):
        return selector
    if isinstance(selector, str):
        matches = [port["index"] for port in ports
                   if selector == port["name"] or selector == port.get("description")]
        if len(matches) == 1:
            return matches[0]
    _fail("unknown_port", path, f"Unknown or ambiguous {direction} port '{selector}'", ports)


def _change_connection(graph: dict, edit: dict, catalog: dict) -> dict:
    source_path, target_path = edit.get("from_node"), edit.get("to_node")
    source_scope, source = _resolve_node(graph, source_path)
    target_scope, target = _resolve_node(graph, target_path)
    if source_scope is not target_scope:
        _fail("cross_scope_connection", target_path, "Connect nodes in the same graph through its named interface")
    out = _resolve_port(source, edit.get("from_port"), "outputs", source_path, catalog)
    inp = _resolve_port(target, edit.get("to_port"), "inputs", target_path, catalog)
    wire = {"from": source["name"], "from_port": out, "to": target["name"], "to_port": inp}
    connections = _connection_array(source_scope, target_path)
    previous = [edge for edge in connections if isinstance(edge, dict)
                and edge.get("to") == target["name"] and edge.get("to_port") == inp]
    kind = edit["op"]
    if kind == "disconnect":
        matching = [edge for edge in previous if all(edge.get(key) == value for key, value in wire.items())]
        if not matching:
            _fail("connection_missing", target_path, "Selected connection does not exist", previous)
        set_graph_connections(source_scope, [edge for edge in connections if edge not in matching])
        return {"op": kind, "from_node": source_path, "to_node": target_path, "before": matching, "after": None}
    if len(previous) != 1 or not all(previous[0].get(key) == value for key, value in wire.items()):
        set_graph_connections(source_scope, [edge for edge in connections if edge not in previous] + [wire])
    return {"op": kind, "from_node": source_path, "to_node": target_path, "before": previous, "after": wire}


def patch_graph(graph: dict, edits: list, catalog: dict) -> dict:
    """Apply an ordered batch to a copy and publish only a valid final graph."""
    if not isinstance(edits, list) or not edits:
        _fail("invalid_edits", "$", "Provide a non-empty array of graph edits")
    result = deepcopy(graph)
    diff = []
    for index, edit in enumerate(edits):
        try:
            kind = edit.get("op") if isinstance(edit, dict) else None
            if kind == "set_param":
                change = _set_parameter(result, edit, catalog)
            elif kind in ("connect", "disconnect"):
                change = _change_connection(result, edit, catalog)
            else:
                _fail("unknown_edit", "$", f"Unknown graph edit '{kind}'", ["set_param", "connect", "disconnect"])
            diff.append(change)
        except GraphEditError as exc:
            exc.problem["edit_index"] = index
            raise
    findings = validate_graph(result, catalog, strict=True)
    if error := next((finding for finding in findings if finding["severity"] == "error"), None):
        raise GraphEditError(error)
    return {"graph": result, "diff": diff}
