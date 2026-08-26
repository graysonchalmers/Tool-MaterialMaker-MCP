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
