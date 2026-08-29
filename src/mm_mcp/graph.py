def find_material_node(ptex: dict) -> dict:
    """Return the graph's single top-level node of type 'material'.

    Raises ValueError if there isn't exactly one -- callers that need to
    target "the" material node (e.g. isolate_node_output) have no sane
    fallback when a graph has zero or more than one.
    """
    materials = [n for n in ptex.get("nodes", []) if n.get("type") == "material"]
    if len(materials) != 1:
        raise ValueError(
            f"expected exactly one 'material' node in the graph, found {len(materials)}")
    return materials[0]


def isolate_node_output(ptex: dict, node_name: str, port: int = 0) -> dict:
    """Return a copy of ptex with node_name's output `port` wired directly
    into the graph's material node's albedo_tex input (port 0), replacing
    whatever fed it before. The rest of the graph is untouched.

    Raises ValueError if node_name isn't in the graph, or if
    find_material_node's own preconditions aren't met.
    """
    if not any(n.get("name") == node_name for n in ptex.get("nodes", [])):
        raise ValueError(f"no node named '{node_name}' in the graph")
    material_name = find_material_node(ptex)["name"]
    connections = [c for c in ptex.get("connections", [])
                   if not (c.get("to") == material_name and c.get("to_port", 0) == 0)]
    connections.append({"from": node_name, "from_port": port,
                         "to": material_name, "to_port": 0})
    return {**ptex, "connections": connections}
