# CLAUDE.md — Tool-MaterialMaker-MCP

Standing instructions for agent sessions on this project.

## What this is

An MCP server (Python) that lets Claude author Material Maker node graphs,
render them headlessly, and return editable `.ptex` files. Read
[docs/superpowers/specs/2026-08-25-material-maker-mcp-design.md](docs/superpowers/specs/2026-08-25-material-maker-mcp-design.md)
for the full design before making changes.

Read [docs/NORTH_STAR.md](docs/NORTH_STAR.md) before proposing new scope —
this is a round-trip learning tool (assistant drafts, human tweaks the real
graph in Material Maker), not a one-shot texture generator. If a change
doesn't serve that loop, check with Grayson before building it.

## The baton

- [HANDOFF.md](HANDOFF.md) is the session baton. Read it at pickup, write it at wrap-up.
- [STATUS.md](STATUS.md) is the gate ledger. Three states only: verified, wired, not started.
- [docs/PLAN.md](docs/PLAN.md) holds the phase plan and exit gates.
- Baton shape (adopted 2026-09-05 after teardown #3 found the baton had become
  the archive): HANDOFF.md's "Current state" describes the latest session
  only; older sessions are one line each in the session log (max 8 entries);
  "Heads-up" is a bounded list of live gotchas, dropped once a mechanism makes
  one moot. STATUS.md cells hold state + one line + an evidence pointer;
  corrections and narrative go to the session log or `git log`, never into a
  cell. There is no archive file: git history is the archive (every session
  ends with a `docs:` wrap-up commit, so `git log --grep` finds it).
- Never type counts (materials, categories, tools) into README.md by hand;
  `tests/test_readme_counts.py` recomputes them from the tree and the wording
  it parses is fixed. Change the tree, then the number.

## Environment (this machine)

- Shell is PowerShell 5.1. Use `;` to sequence, `Push-Location`/`Pop-Location`,
  and `& "C:\path\tool.exe"` for quoted executables. `&&` is a parse error.
- Python: `C:\Program Files\Python313\python.exe` (Python 3.13).
- Godot 4.7.1: `C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64.exe`.
- Material Maker project checkout: `C:\Projects-local\z-Git\material-maker`
  (pristine upstream, do not modify in Phase 1).
- Config lives in `.env` (copy from `.env.example`). Never echo its contents.

## Key facts about Material Maker (verified)

- Graph files (`.ptex`) are JSON: `connections` + `nodes`.
- Node instance: `{name, type, node_position:{x,y}, parameters:{...}}`.
- Node definitions: `<MM_PROJECT>/addons/material_maker/nodes/*.mmg`, each with a
  `shader_model` declaring typed inputs/outputs/parameters.
- Headless render (VERIFIED working): `Godot_..._console.exe --path <MM_PROJECT>
  --export-material <file.ptex> --target "Godot/Godot 4 Standard" -o <outdir> --size <n>`.
  Gotchas learned the hard way:
  - Use `--export-material`, NOT `--export`. Godot 4 reserved `--export` as an
    engine flag (build export); the app flag is `--export-material`.
  - Use `--target`, NOT `-t` — Material Maker's own arg parser silently
    ignores `-t` and falls back to its hardcoded default profile (found and
    fixed in `render.py` 2026-08-28; the CLI itself has the same trap).
  - Do NOT pass `parse_args.tscn`; it is the project main scene and would be
    loaded as a material file. Just pass the flags.
  - Use the `_console.exe` binary to capture stdout; the GUI exe returns empty logs.
  - Do NOT use `--headless`; texture rendering needs a real rendering context.
  - Produces `<name>_albedo.png`, `_normal.png`, `_heightmap.png`, `_orm.png` + `.tres`.
- The MM project needs `steam_appid.txt` (`4110830`) or it self-relaunches and
  exits immediately. Already present in the z-Git clone.

## Conventions

- Gate rule: never start Phase N+1 until Phase N's gate is green and recorded in STATUS.md.
- Validation errors are returned as data, not raised, so Claude can self-correct.
- Keep units isolated: catalog builder, graph/validator, render runner, MCP server.
- Me-first now; keep code clean enough that Phase 4 public packaging is not a rewrite.
