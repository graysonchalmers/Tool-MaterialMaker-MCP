"""Material Maker MCP server package.

Lets an MCP client author Material Maker node graphs, validate them against a
catalog built from the app's own node definitions, and render them headlessly
to PBR texture maps. Units:
  catalog_builder.py  build catalog.json from the .mmg node definitions
  graph.py            pure .ptex graph helpers (find material node, isolate node output)
  validator.py        validate a graph against the catalog
  render.py           headless Godot render runner
  overlay.py          build/refresh the live-control addon overlay (disposable working copy)
  paths.py            client-path guards (allowed-roots bounding, traversal rejection)
  inspect.py          read-only .ptex metrics (for the inspect_project tool)
  server.py           the MCP server (ten batch tools, six live tools, catalog resource)
"""

from importlib.metadata import version as _pkg_version, PackageNotFoundError

try:
    __version__ = _pkg_version("mm-mcp")
except PackageNotFoundError:  # not pip-installed (tests import via pythonpath=src)
    __version__ = "0.0.0+unknown"
