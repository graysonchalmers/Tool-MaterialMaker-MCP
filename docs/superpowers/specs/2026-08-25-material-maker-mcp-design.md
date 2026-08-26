# Material Maker MCP — Design Spec

- **Date:** 2026-08-25
- **Status:** Approved in brainstorming, pending spec review
- **Author:** Claude (Opus) with Grayson Chalmers
- **Classification:** Architectural (new subsystem)

## Goal

Let a user describe a material in natural language and have Claude author a
Material Maker node graph that renders to usable PBR texture maps, with one or
more variants shown back, and the editable `.ptex` handed off so the user can
tweak it in the live app. Claude does 80% of the setup; the human finishes.

"Done" for the whole project: a prompt like "weathered copper" reliably yields
a `.ptex` that opens in Material Maker and reads as weathered copper without
manual repair, plus rendered map previews Claude showed inline.

## Why this is feasible (grounded in the upstream repo)

Verified against `RodZill4/material-maker` (MIT, Godot 4.7) clone in
`C:\Projects-local\z-Git\material-maker`:

1. **Headless render already ships (VERIFIED end to end).** `parse_args.gd`
   implements a CLI export mode. Working command on this machine:
   `Godot_..._console.exe --path <mm_project> --export-material <file.ptex>
   -t "Godot/Godot 4 Standard" -o <outdir> --size <n>`. It loads a graph via
   `mm_loader.load_gen`, walks the node tree, and calls `export_material` to
   write `_albedo/_normal/_heightmap/_orm` PNGs plus a `.tres`. No GUI window
   needed. Gotchas: use `--export-material` not the engine-reserved `--export`;
   do not pass the main scene `parse_args.tscn` as an arg; use the `_console.exe`
   variant to capture logs; do not use `--headless` (rendering needs a real
   context).
2. **Graph format is plain JSON.** A `.ptex` file is a JSON object with
   `connections` (`from`, `from_port`, `to`, `to_port`) and `nodes` (each
   `{name, type, node_position:{x,y}, parameters:{...}}`). LLM-authorable
   directly, no binary format.
3. **Node vocabulary is machine-readable.** ~392 node types live as `.mmg`
   files under `addons/material_maker/nodes/`. Each carries a `shader_model`
   declaring typed `inputs`, `outputs`, and `parameters` with type, min, max,
   step, default, enum `values`, and `shortdesc`/`longdesc`. This is a full
   schema we can turn into a catalog.
4. **~100+ example graphs** ship under `material_maker/examples/*.ptex` as
   real, working reference patterns.

## Scope decisions (from brainstorming)

- **Interaction model:** Start thin (batch render), structured so a thick
  live-control layer can be added later. Phase 1 makes NO changes to the
  Material Maker Godot source.
- **Audience:** Me-first. Hardcoded/config paths acceptable now; keep code
  clean enough that public packaging is a later phase, not a rewrite.
- **Relationship to upstream:** `z-Git\material-maker` stays a pristine
  upstream reference. This project sits on top of it and reads its `.mmg`
  files + drives its Godot `--export`. A true source-fork is deferred to the
  live-control phase, when we actually modify Material Maker.

## Architecture (Phase 1, thin/batch)

A Python MCP server between Claude and the user's installed Godot + Material
Maker project. Four units, each with one job and a clean interface.

### 1. Node catalog builder (`catalog_builder.py`)
- **Does:** Reads all `.mmg` files under `<MM_PROJECT>/addons/material_maker/nodes/`,
  emits `catalog/catalog.json`: per node type, its inputs (name, type, desc),
  outputs (type), and parameters (name, type, min, max, step, default, enum
  values, desc).
- **Depends on:** `MM_PROJECT_PATH`. Rerunnable when upstream updates.
- **Interface:** `build_catalog(mm_project_path) -> dict` and a CLI entry.

### 2. Graph builder + validator (`graph.py`)
- **Does:** Assembles `.ptex` JSON and validates against the catalog: node
  types exist, referenced ports exist, connections point to real ports,
  parameters are known and in range/enum. Returns structured problems, not
  exceptions, so Claude can self-correct.
- **Depends on:** the catalog dict. Pure Python, no Godot, fully unit-testable.
- **Interface:** `validate_graph(ptex, catalog) -> list[Problem]`,
  helpers to add nodes/connections/params.

### 3. Render runner (`render.py`)
- **Does:** Writes a `.ptex` to a temp path, runs the Godot `--export`
  subprocess with a target profile, size, and output dir; parses exit code and
  stdout log; returns produced image paths + any errors.
- **Depends on:** `MM_GODOT_BINARY`, `MM_PROJECT_PATH`.
- **Interface:** `render(ptex, size, maps, outdir) -> RenderResult`.

### 4. MCP server (`server.py`)
- **Does:** Exposes the tools below and serves the catalog as an MCP resource
  so Claude can look up nodes on demand.

### Data flow
prompt -> Claude drafts graph JSON (1..n variants) using the catalog ->
`validate_graph` per variant -> `render` per valid variant ->
Claude views thumbnails, shows the set -> `save_graph` writes `.ptex` files
the user opens in Material Maker to tweak. The `.ptex` handoff is why thin is
enough: the escape hatch to live editing is the file itself.

## MCP tool surface (Phase 1)

- `list_node_types(category?)` — catalog summary.
- `describe_node(type)` — full ports + params for one node.
- `validate_graph(ptex_json)` — ok or concrete problems.
- `render_graph(ptex_json, size?, maps?)` — render, return image paths + errors.
- `save_graph(ptex_json, path)` — write a `.ptex` for the user to open.
- `list_examples()` / `load_example(name)` — read bundled example graphs so
  Claude can learn and remix real patterns.

## Error handling

- Validation errors are data (a list of problems with node/port/param + reason),
  surfaced to Claude to fix before rendering.
- Render errors: non-zero Godot exit or missing output files -> `RenderResult`
  with `ok=False` and the parsed log tail. The runner never silently succeeds.
- Missing config (`MM_GODOT_BINARY` / `MM_PROJECT_PATH` absent or wrong) fails
  fast at server start with an actionable message.

## Testing

- **Unit:** catalog builder against a few known `.mmg` files; validator against
  hand-made good and bad graphs.
- **Integration/smoke:** render a known bundled example headlessly and assert a
  PNG is produced and non-empty. This is the Phase 0 gate and the standing
  smoke test.
- **Phase 3 quality harness:** a small set of prompt -> expected-material cases,
  scored by usable-hit-rate, used to tune catalog descriptions and authoring
  guidance.

## Phases and gates

- **Phase 0 — Harness.** Project scaffold + smoke test that renders a known
  example `.ptex` and checks a PNG appears. *Gate: smoke passes.*
- **Phase 1 — Catalog.** Generate `catalog.json`; spot-check nodes vs `.mmg`.
  *Gate: every bundled example validates against the catalog.*
- **Phase 2 — Render MCP.** Wire the four units; render a hand-written graph
  end to end via an MCP call. *Gate: "render this example" works over MCP.*
- **Phase 3 — Authoring quality.** Prompt-to-graph on a test set; tune. *Gate:
  agreed usable-hit-rate on the material test set.*
- **Phase 4 — Public packaging (later, sketched).** Config-driven paths,
  cross-platform, install docs, binary auto-detect.
- **Phase 5 — Live-control (later, sketched).** GDScript plugin inside a forked
  Material Maker exposing add-node/connect/set-param/render over a socket for
  interactive, watchable building.

## Dependencies and environment

- Python 3.13 (already installed).
- Godot 4.7.1 binary at
  `C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64.exe`.
- Material Maker project checkout at `C:\Projects-local\z-Git\material-maker`.
- Config via `.env` (`MM_GODOT_BINARY`, `MM_PROJECT_PATH`, `MM_OUTPUT_DIR`).

## Known risks / honest boundaries

- **Phase 3 is the hard part.** Rendering is trivial; authoring a graph that
  reads as the requested material is the open problem. The catalog makes it
  tractable, not automatic.
- **Steam gotcha carried by the project:** the MM project needs a
  `steam_appid.txt` (`4110830`) present or it self-relaunches; already added to
  the z-Git clone. Render runs must use that project dir.
- **Godot binary path is hardcoded** until Phase 4.
- **`--export` runs the full MM project;** startup cost per render is seconds,
  acceptable for batch, a reason live-control is worth it later.
