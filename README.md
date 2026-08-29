# Material Maker MCP

An [MCP](https://modelcontextprotocol.io) server that lets an AI assistant
author [Material Maker](https://github.com/RodZill4/material-maker) node graphs
from natural language, render them headlessly to PBR texture maps, and hand back
editable `.ptex` files you finish in the app.

You describe a material in a sentence. The assistant drafts the node graph,
the server validates it against Material Maker's own node catalog and renders it
with Godot, and you get back the maps plus an editable graph. The assistant gets
you most of the way there; you tweak the rest in Material Maker.

Why this project exists and what it's actually optimizing for is in
[docs/NORTH_STAR.md](docs/NORTH_STAR.md).

> ## ⚠️ Super, super, super alpha. Read this first.
>
> I am an artist and animator in the game industry, not a software engineer. I do
> not really know what I am doing on the code side. This project was built mostly
> by AI assistants with me steering, and it is at an extremely early, rough,
> experimental stage.
>
> What that means for you:
> - **Expect breakage.** Rough edges, sharp corners, things that only work on the
>   one machine they were built on. It has been verified on exactly one setup
>   (Windows, a specific Godot build, a specific Material Maker checkout).
> - **No stability promises.** Anything can change or break between versions. There
>   is no test coverage beyond a small smoke and unit set.
> - **Not production-ready.** Please do not rely on this for anything that matters.
>   Back up your work. Assume it will misbehave.
> - **The material "quality" bar is deliberately low.** The goal is "gets you 80%
>   of the way there so you finish in the app," not "photoreal." See the
>   `quality/` scorecard for exactly how well (and badly) it does on 15 prompts:
>   it currently passes 11 of them by a generous, artist's eyeball standard.
>
> I am sharing it in the open because it is a fun experiment and someone might find
> it useful or want to build on it, not because it is polished. Feedback, issues,
> and "you're doing this wrong" corrections from actual developers are very
> welcome.

## Gallery

Each of these was authored by the server from the one-line prompt beside it, then
rendered headlessly. Full graphs and previews are in [`examples/`](examples/).

| | | | |
|:--:|:--:|:--:|:--:|
| ![polished gray granite](examples/images/s02_gray_granite.png) | ![woven denim](examples/images/f01_woven_denim.png) | ![weathered copper](examples/images/m01_weathered_copper.png) | ![rusted painted steel](examples/images/combo01_rusted_painted_steel.png) |
| "polished gray granite" | "blue denim fabric" | "weathered copper" | "rusted painted steel, peeling" |
| ![ceramic hex tiles](examples/images/man02_ceramic_hex_tiles.png) | ![brushed aluminum](examples/images/m02_brushed_aluminum.png) | ![mossy forest floor](examples/images/o01_mossy_forest_floor.png) | ![red brick wall](examples/images/s01_red_brick_wall.png) |
| "white ceramic hexagon tiles" | "brushed aluminum" | "mossy forest floor" | "red brick wall" |

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

- **Python 3.10+** (developed and verified on 3.13; older versions declared but
  not exercised)
- **Windows** is the only fully verified platform. The render runner falls back
  to the plain Godot binary on macOS/Linux, but that path is untested.
- **Godot 4.7.x** (the standard desktop binary; the server prefers the matching
  `_console.exe` build on Windows when present, to capture render logs)
- **A Material Maker project checkout** on disk. The server reads that checkout's
  node definitions and bundled examples and drives its headless export. Clone it
  from [github.com/RodZill4/material-maker](https://github.com/RodZill4/material-maker).
  Material Maker needs a `steam_appid.txt` (containing `4110830`) at the checkout
  root, or the app self-relaunches and exits on headless render; the upstream
  clone already includes one.

## Install

Install from a clone (the supported path for now):

```bash
git clone https://github.com/graysonchalmers/Tool-MaterialMaker-MCP.git
cd Tool-MaterialMaker-MCP
python -m venv .venv
# Windows:  .\.venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Then edit `.env`:

```
MM_GODOT_BINARY=/path/to/Godot_v4.7.x_console.exe
MM_PROJECT_PATH=/path/to/material-maker
MM_OUTPUT_DIR=/path/to/where/rendered/maps/should/go
```

`.env` is gitignored and read from the current working directory (or from the
path in `MM_DOTENV` if set). Config can also be supplied via `MM_*` environment
variables, which take precedence over `.env`. `MM_OUTPUT_DIR` is optional and
defaults to an `output/` folder in the working directory.

Either way you get an `mm-mcp` command on your PATH. (A `pip install mm-mcp`
from PyPI is packaged and ready but not yet published; the clone above is the
current route.)

## Check your setup

Before wiring it into a client, confirm every prerequisite is in place:

```bash
mm-mcp --check
```

It prints a green/red checklist (Godot binary, Material Maker checkout, node
definitions, examples, `steam_appid.txt`, output dir, and a catalog build) and
exits non-zero if anything is missing, so you find problems before your MCP
client does. `mm-mcp --version` prints the version.

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

The server speaks MCP over stdio. After installing it is on your PATH as
`mm-mcp`. Point your client at that command with the `MM_*` variables set.

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

The server exposes nine batch-mode tools and one resource (plus six more in Live mode, below):

| Tool | What it does |
|---|---|
| `list_node_types` | List catalog node types, optionally filtered by category |
| `describe_node` | Full typed inputs/outputs/parameters for one node type |
| `validate` | Validate a `.ptex` graph against the catalog; returns problems as data |
| `render_graph` | Render a `.ptex` to PBR maps at a given size |
| `render_node_output` | Render one node's output in isolation, without editing the real graph |
| `render_preview` | Composite already-rendered maps onto a sphere/cube/cutaway-ball preview scene |
| `save_graph` | Write a `.ptex` graph to a path |
| `list_examples` | List the bundled Material Maker examples |
| `load_example` | Load a bundled example as a `.ptex` graph |

Resource `catalog://nodes` exposes the full node catalog.

## Live mode (optional)

Batch mode above (`render_graph` et al.) is the default, simplest path: no
Material Maker GUI involved. Live mode is a second, additive way to work --
open Material Maker yourself, and Claude can see the graph on your active
tab, build and edit it live, and trigger renders, so you watch it happen in
the GUI instead of copying files back and forth.

| Tool | What it does |
|---|---|
| `live_start` | Attach to an already-open Material Maker, or launch it against a disposable overlay if nothing's listening |
| `live_get_graph` | Fetch the active tab's current graph, `.ptex`-shaped |
| `live_apply` | Apply a batch of validated mutations (`add_node`/`connect_nodes`/`disconnect_nodes`/`set_param`) to the live graph |
| `live_render` | Trigger a render in the live window, same result shape as `render_graph` |
| `live_render_node_output` | Render one node's output in isolation on the live graph, previewing then restoring the original wiring |
| `live_clear` | Reset the live graph to a single default Material node, discarding everything else |

No manual setup beyond what batch mode already needs -- the addon ships in
this repo and builds its own disposable working copy on first use. Live
mode is turn-based, not simultaneous: there's no conflict resolution for
edits from both sides at once. See
[docs/superpowers/specs/2026-08-26-live-control-addon-design.md](docs/superpowers/specs/2026-08-26-live-control-addon-design.md)
for the full design.

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

Very early alpha (see the warning up top). Phases 0 through 3 of my own rough plan
are done and verified on one machine. See [STATUS.md](STATUS.md) for the gate
ledger and [docs/PLAN.md](docs/PLAN.md) for the phase plan. Authoring quality is
measured against a frozen 15-case test set in [`quality/`](quality/); the current
scorecard is 15/15 usable by an artist's eyeball standard (see
`quality/scorecards/`). "Verified" here means "worked when I ran it," not
"battle-tested."

## License and attribution

This project is MIT licensed (see [LICENSE](LICENSE)).

Material Maker is MIT licensed, Copyright (c) Rodolphe Suescun and contributors.
This project drives a separate Material Maker checkout and does not modify or
redistribute it.
