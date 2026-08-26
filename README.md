# Tool-MaterialMaker-MCP

An MCP server that lets Claude author [Material Maker](https://github.com/RodZill4/material-maker)
node graphs from natural language, render them headlessly to PBR texture maps,
and hand back editable `.ptex` files you finish in the live app.

Claude gets a material 80% of the way there. You tweak the rest.

## Status

Phase 0 (harness). See [STATUS.md](STATUS.md) for the gate ledger and
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
```

A green smoke run proves the render path is alive end to end. Each later phase
adds a probe to the smoke harness.

## Upstream

Material Maker is MIT, (c) Rodolphe Suescun and contributors. The pristine
upstream clone lives at `C:\Projects-local\z-Git\material-maker` and is not
modified by this project in Phase 1.
