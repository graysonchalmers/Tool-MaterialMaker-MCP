"""Material Maker node interfaces shared by validation and graph authoring."""

import math
import re

from mm_mcp.catalog_builder import EXPORT_NODE, _parse_generic_node, _parse_node_data, _parse_port


PORT_TYPE_GROUPS = (
    frozenset({"f", "rgb", "rgba"}),
    frozenset({"sdf3d", "sdf3dc"}),
    frozenset({"tex3d", "tex3d_gs"}),
)


def node_schema(node: dict, catalog: dict, *, local: bool = True) -> dict | None:
    node_type = node.get("type")
    if not isinstance(node_type, str):
        return None
    if node_type == "export":
        return EXPORT_NODE
    if local and node_type == "ios":
        ports = [_parse_port(port) for port in node.get("ports", []) if isinstance(port, dict)]
        name = node.get("name")
        return {"type": node_type, "parameters": [],
                "inputs": [] if name == "gen_inputs" else ports,
                "outputs": [] if name == "gen_outputs" else ports}
    if local and node_type == "graph":
        return _parse_generic_node(node, node_type, catalog)
    if local and isinstance(node.get("shader_model"), dict):
        return _parse_node_data(node, node_type)
    return catalog.get(node_type)


def graph_connections(graph: dict) -> list:
    """Read current connection arrays and the compact form native .ptex accepts."""
    connections = graph.get("connections", [])
    if isinstance(connections, list):
        return connections
    if not isinstance(connections, dict):
        raise ValueError("Graph connections must be an array or native compact object")
    expanded = []
    for target, sockets in connections.items():
        if not isinstance(sockets, dict):
            raise ValueError("Compact connections must map each target to a socket object")
        for index, source in sockets.items():
            if not isinstance(source, dict) or not isinstance(index, str) or not index.isascii() or not index.isdigit():
                raise ValueError("Compact connections must index source objects by port number")
            expanded.append({"from": source.get("node"), "from_port": source.get("port"),
                             "to": target, "to_port": int(index)})
    return expanded


def set_graph_connections(graph: dict, edges: list[dict]) -> None:
    if isinstance(graph.get("connections"), dict):
        compact = {}
        for edge in edges:
            compact.setdefault(edge["to"], {})[str(edge["to_port"])] = {
                "node": edge["from"], "port": edge["from_port"],
            }
        graph["connections"] = compact
    else:
        graph["connections"] = edges


def named_ports(schema: dict, direction: str) -> list[dict]:
    return [
        {"index": index, "name": spec.get("name") or spec.get("desc") or f"port_{index}",
         "type": spec.get("type"), **({"description": spec["desc"]} if spec.get("desc") else {})}
        for index, spec in enumerate(schema.get(direction, []))
    ]


def are_ports_compatible(source: str | None, target: str | None) -> bool:
    # Material Maker's io_types.mmt supports conversions within these groups.
    return (source == target or source in (None, "any") or target in (None, "any")
            or any(source in group and target in group for group in PORT_TYPE_GROUPS))


def is_number(value) -> bool:
    return type(value) is int or (type(value) is float and math.isfinite(value))


EDITABLE_PARAMETER_TYPES = frozenset({"float", "int", "size", "enum", "seed", "boolean", "color", "gradient"})


def parameter_has_valid_type(spec: dict, value) -> bool:
    kind = spec.get("type")
    if kind == "float":
        return is_number(value)
    if kind in {"int", "size", "enum", "seed"}:
        return type(value) is int or (type(value) is float and value.is_integer())
    if kind == "boolean":
        return type(value) is bool
    if kind in {"string", "file", "text"}:
        return isinstance(value, str)
    if kind == "color":
        return (isinstance(value, dict) and value.get("type", "Color") == "Color"
                and all(is_number(value.get(key)) for key in "rgba"))
    if kind == "gradient":
        if isinstance(value, list):  # Native legacy format.
            points = value
        elif isinstance(value, dict) and value.get("type") == "Gradient":
            interpolation = value.get("interpolation", 1)
            if type(interpolation) is not int or not 0 <= interpolation <= 3:
                return False
            points = value.get("points")
        else:
            return False
        return (isinstance(points, list) and bool(points)
                and all(isinstance(point, dict) and all(is_number(point.get(key)) for key in ("r", "g", "b", "pos"))
                        and is_number(point.get("a", 1)) for point in points))
    return True


def safe_export_suffix(value) -> bool:
    return (isinstance(value, str) and value not in {".", ".."}
            and re.search(r'[\\/\x00-\x1f:<>"|?*]', value) is None)


def problem(code: str, where: str, message: str, *, severity: str = "error",
            alternatives: list | None = None) -> dict:
    result = {"severity": severity, "where": where, "code": code, "message": message}
    if alternatives is not None:
        result["alternatives"] = alternatives
    return result
