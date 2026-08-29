class Graph:
    def __init__(self):
        self._nodes = []
        self._connections = []

    def add_node(self, name, type, parameters=None, x=0, y=0):
        self._nodes.append({
            "name": name,
            "type": type,
            "node_position": {"x": x, "y": y},
            "parameters": dict(parameters or {}),
        })

    def connect(self, from_node, from_port, to_node, to_port):
        self._connections.append({
            "from": from_node, "from_port": from_port,
            "to": to_node, "to_port": to_port,
        })

    def to_ptex(self):
        return {
            "type": "graph",
            "name": "graph",
            "label": "Graph",
            "node_position": {"x": 0, "y": 0},
            "parameters": {},
            "connections": list(self._connections),
            "nodes": list(self._nodes),
        }

    @classmethod
    def from_ptex(cls, d):
        g = cls()
        for n in d.get("nodes", []):
            pos = n.get("node_position", {"x": 0, "y": 0})
            g.add_node(n["name"], n["type"], n.get("parameters", {}),
                       pos.get("x", 0), pos.get("y", 0))
        for c in d.get("connections", []):
            g.connect(c["from"], c["from_port"], c["to"], c["to_port"])
        return g


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
