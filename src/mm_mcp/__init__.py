"""Material Maker MCP server package.

Lets an MCP client author Material Maker node graphs, validate them against a
catalog built from the app's own node definitions, and render them headlessly
to PBR texture maps. Units:
  catalog_builder.py  build catalog.json from the .mmg node definitions
  graph.py            build/validate .ptex graph JSON
  validator.py        validate a graph against the catalog
  render.py           headless Godot render runner
  server.py           the MCP server (seven tools + catalog resource)
"""

__version__ = "0.2.0"
