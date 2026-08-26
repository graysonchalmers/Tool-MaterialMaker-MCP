# Tool-MaterialMaker-MCP

An MCP server that lets Claude author [Material Maker](https://github.com/RodZill4/material-maker)
node graphs from natural language, render them headlessly to PBR texture maps,
and hand back editable `.ptex` files you finish in the live app.

Claude gets a material 80% of the way there. You tweak the rest.

## Status

Phase 1-2 complete (catalog, graph, render, and MCP server all wired end to
end). See [STATUS.md](STATUS.md) for the gate ledger and
[docs/PLAN.md](docs/PLAN.md) for the phase plan. Design lives in
[docs/superpowers/specs/2026-08-25-material-maker-mcp-design.md](docs/superpowers/specs/2026-08-25-material-maker-mcp-design.md).

## How it works

Material Maker graphs are plain JSON (`.ptex`), and Material Maker ships a
headless CLI export mode. This project sits on top of an existing Material Maker
checkout:

1. A catalog builder reads Material Maker's ~392 node definitions into a
   machine-readable `catalog.json` that Claude authors against.
2. Claude drafts a graph as `.ptex` JSON, the server validates it against the
   catalog, then renders it with Godot's `--export` mode.
3. Rendered maps come back as images; the `.ptex` is saved for you to open.

## Requirements

- Python 3.13
- Godot 4.7.x binary
- A Material Maker project checkout (the `z-Git\material-maker` clone works)

Copy `.env.example` to `.env` and set the paths.

## How to verify

```bash
# Phase 0 smoke: render a known example headlessly and confirm a PNG appears
pwsh smoke/smoke.ps1

# Phase 2 smoke: load a bundled example through the MCP layer and render it
.\.venv\Scripts\python.exe smoke\smoke_mcp.py
```

A green smoke run proves the render path is alive end to end. Each later phase
adds a probe to the smoke harness.

## MCP server

Run the server with:

```
.\.venv\Scripts\python.exe -m mm_mcp.server
```

The server needs a working Material Maker checkout and Godot binary configured
per `.env` (copy from `.env.example`) — same requirements as the render path
above. The node catalog is built in-process at import time (`build_catalog()`
runs when `mm_mcp.server` is imported), so there is no separate build step
required to start the server. If you want a `catalog/catalog.json` on disk
(for inspection, or to avoid rebuilding it repeatedly), you can generate one
explicitly:

```
.\.venv\Scripts\python.exe -m mm_mcp.catalog_builder
```

The server exposes seven tools (`list_node_types`, `describe_node`, `validate`,
`render_graph`, `save_graph`, `list_examples`, `load_example`) and one resource
(`catalog://nodes`).

## Upstream

Material Maker is MIT, (c) Rodolphe Suescun and contributors. The pristine
upstream clone lives at `C:\Projects-local\z-Git\material-maker` and is not
modified by this project in Phase 1.
