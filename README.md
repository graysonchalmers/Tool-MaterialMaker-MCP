# Material Maker MCP

An [MCP](https://modelcontextprotocol.io) server that lets an AI assistant
author [Material Maker](https://github.com/RodZill4/material-maker) node graphs
from natural language, render them headlessly to PBR texture maps, and hand back
editable `.ptex` files you finish in the app.

You describe a material in a sentence. The assistant drafts the node graph,
the server validates it against Material Maker's own node catalog and renders it
with Godot, and you get back the maps plus an editable graph. The assistant gets
you most of the way there; you tweak the rest in Material Maker.

## Gallery

Each of these was authored by the server from the one-line prompt beside it, then
rendered headlessly. Full graphs and previews are in [`examples/`](examples/).

| | | |
|:--:|:--:|:--:|
| ![red brick wall](examples/images/s01_red_brick_wall.png) | ![polished gray granite](examples/images/s02_gray_granite.png) | ![brushed aluminum](examples/images/m02_brushed_aluminum.png) |
| "red brick wall" | "polished gray granite" | "brushed aluminum" |
| ![weathered copper](examples/images/m01_weathered_copper.png) | ![mossy forest floor](examples/images/o01_mossy_forest_floor.png) | ![brown leather](examples/images/f02_brown_leather.png) |
| "weathered copper" | "mossy forest floor" | "brown leather" |

## How it works

Material Maker graphs are plain JSON (`.ptex`), and Material Maker ships a
headless CLI export mode. This server sits on top of an existing Material Maker
checkout:

1. A catalog builder reads Material Maker's node definitions
   (`addons/material_maker/nodes/*.mmg`) into a machine-readable catalog the
   assistant authors against.
2. The assistant drafts a graph as `.ptex` JSON. The server validates it against
   the catalog (returning errors as data so the assistant can self-correct), then
   renders it by driving Godot's `--export-material` mode.
3. Rendered maps come back as image files (albedo, normal, roughness/metallic,
   height), and the `.ptex` is saved for you to open in Material Maker.

## Requirements

- **Python 3.13+**
- **Godot 4.7.x** (the standard desktop binary; the server prefers the matching
  `_console.exe` build on Windows when present, to capture render logs)
- **A Material Maker project checkout** on disk. The server reads that checkout's
  node definitions and bundled examples and drives its headless export. Clone it
  from [github.com/RodZill4/material-maker](https://github.com/RodZill4/material-maker).
  Material Maker needs a `steam_appid.txt` (containing `4110830`) at the checkout
  root, or the app self-relaunches and exits on headless render; the upstream
  clone already includes one.

## Install

```bash
git clone https://github.com/graysonchalmers/Tool-MaterialMaker-MCP.git
cd Tool-MaterialMaker-MCP
python -m venv .venv
# Windows:  .\.venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -e .
```

Then copy the environment template and point it at your machine:

```bash
cp .env.example .env
```

Edit `.env`:

```
MM_GODOT_BINARY=/path/to/Godot_v4.7.x_console.exe
MM_PROJECT_PATH=/path/to/material-maker
MM_OUTPUT_DIR=/path/to/where/rendered/maps/should/go
```

`.env` is gitignored. Config can also be supplied via `MM_*` environment
variables, which take precedence over `.env`.

## Verify

Two smoke scripts prove the render path is alive end to end:

```bash
# Render a bundled example headlessly and confirm PNGs appear
python smoke/smoke_mcp.py
```

On Windows there is also a PowerShell smoke that renders directly through Godot:

```
pwsh smoke/smoke.ps1
```

Run the test suite (the one Godot-launching test is marked `integration`):

```bash
pytest -q -m "not integration"   # fast unit + validation tests
pytest -q                        # everything, including a real render
```

## Connect it to an MCP client

The server speaks MCP over stdio. After `pip install -e .` it is on your PATH as
`mm-mcp`. Point your client at that command with the three `MM_*` variables set.

Claude Desktop / Claude Code (`claude_desktop_config.json` or an equivalent MCP
config) example:

```json
{
  "mcpServers": {
    "material-maker": {
      "command": "mm-mcp",
      "env": {
        "MM_GODOT_BINARY": "C:\\path\\to\\Godot_v4.7.1-stable_win64_console.exe",
        "MM_PROJECT_PATH": "C:\\path\\to\\material-maker",
        "MM_OUTPUT_DIR": "C:\\path\\to\\output"
      }
    }
  }
}
```

If `mm-mcp` is not on the client's PATH, use the venv's Python instead:
`"command": "/abs/path/.venv/bin/python"`, `"args": ["-m", "mm_mcp.server"]`.

Config is validated at startup, so a missing or wrong `MM_GODOT_BINARY` /
`MM_PROJECT_PATH` fails fast with an actionable message rather than partway
through a render.

## Tools

The server exposes seven tools and one resource:

| Tool | What it does |
|---|---|
| `list_node_types` | List catalog node types, optionally filtered by category |
| `describe_node` | Full typed inputs/outputs/parameters for one node type |
| `validate` | Validate a `.ptex` graph against the catalog; returns problems as data |
| `render_graph` | Render a `.ptex` to PBR maps at a given size |
| `save_graph` | Write a `.ptex` graph to a path |
| `list_examples` | List the bundled Material Maker examples |
| `load_example` | Load a bundled example as a `.ptex` graph |

Resource `catalog://nodes` exposes the full node catalog.

## Notes and gotchas

Learned while getting headless rendering to work reliably (all verified on this
project's setup):

- Use `--export-material`, not `--export`. Godot 4 reserved `--export` for its
  own build-export flag; the Material Maker app flag is `--export-material`.
- Use the `_console.exe` binary on Windows to capture stdout; the GUI exe returns
  empty logs.
- Do **not** pass `--headless`; texture rendering needs a real rendering context.
- The Material Maker checkout needs `steam_appid.txt` (`4110830`) or it
  self-relaunches and exits immediately.
- The `normal_map` node is a compound node: its real parameters are `param0`
  (buffer size), `param1` (strength), `param2`, `param4`, not `amount`/`size`.

## Project status

Phases 0 through 3 are complete and verified. See [STATUS.md](STATUS.md) for the
gate ledger and [docs/PLAN.md](docs/PLAN.md) for the phase plan. Authoring
quality is measured against a frozen 15-case test set in [`quality/`](quality/);
the current scorecard is 11/15 usable (see `quality/scorecards/`).

## License and attribution

This project is MIT licensed (see [LICENSE](LICENSE)).

Material Maker is MIT licensed, Copyright (c) Rodolphe Suescun and contributors.
This project drives a separate Material Maker checkout and does not modify or
redistribute it.
