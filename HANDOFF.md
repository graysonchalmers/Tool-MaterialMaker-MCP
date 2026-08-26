# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-25 (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

Phases 0, 1, and 2 are complete and merged to `main` (pushed to GitHub, at merge
commit `22055fd`). The MCP server works end to end: it parses Material Maker's node
library into a 392-entry catalog, builds and validates `.ptex` graphs, and renders
them headlessly through Godot. Full suite is 81 tests including a real Godot
integration render. The hard remaining work is Phase 3 (authoring quality), which is
a tuning loop, not built yet.

## 📌 Where we stopped

Phases 1-2 landed, reviewed clean (subagent-driven, 9 TDD tasks + whole-branch review
+ one fix wave), merged to `main`, pushed, feature branch deleted. Nothing in flight.
Clean stopping point at the Phase 2 / Phase 3 boundary.

## ▶️ Next concrete step

Scope **Phase 3 (authoring quality)** and write its plan: build a small material test
set (prompt to expected material), run prompt-to-graph, measure a usable-hit-rate, and
tune the catalog descriptions + authoring guidance. This is iterative, not bite-sized
TDD, so it gets its own plan.

Alternatives:
- **Close the deferred minors first** (see below) as a quick cleanup pass before Phase 3.
  Tradeoff: tidy but delays the high-value authoring work.
- **Add an MCP client round-trip test** to cover the protocol layer before building on it.
  Tradeoff: closes a real coverage gap, but small next to Phase 3's payoff.

## ❓ Open questions

- **Phase 3 usable-hit-rate target** (the quality bar for "good enough") not yet set.
- **Multi-variant generation** ("show me 2-3 versions"): ship in Phase 3 or defer?

## 🗂️ Changed this session

- Branch: `main` (feat/phase1-2 merged + deleted) · merge commit `22055fd`.
- Built `src/mm_mcp/`: config, catalog_builder, graph, validator, render, server;
  8 test files (~81 tests); `smoke/smoke_mcp.py`; requirements.txt, pyproject.toml.
- Key decisions (+ why):
  - Thin batch-render architecture first, live-control deferred — proves the vocabulary
    problem before committing to a Godot fork.
  - Unknown-parameter validation is a **warning, not an error** — Material Maker's own
    loader (`gen_base.gd`) tolerates stray param keys, so erroring would reject valid graphs.
  - Compound "generic" nodes parsed via their nested `ios`/`remote` structure — needed to
    catalog ~50 nodes (`normal_map`, etc.) that have no `shader_model`.
  - Server does a fail-fast config preflight (`config.require_valid`) at import.

## ⚠️ Heads-up for the next agent

- Installed `mcp` is **2.x** (`from mcp.server.mcpserver import MCPServer`, not `FastMCP`);
  requirements floor is `mcp>=2,<3`.
- Render gotchas (also in CLAUDE.md): use `--export-material` not `--export`; use the
  `_console.exe` binary for logs; never `--headless`; the MM project needs
  `steam_appid.txt` (`4110830`) or Godot exits instantly.
- `C:\Projects-local\z-Git\material-maker` is the pristine upstream + render target;
  not modified by this project.
- **Deferred minors** (non-blocking, from the whole-branch review): MCP protocol layer has
  no client round-trip test; `render_graph` return keys are non-uniform across paths;
  per-instance `generic_size` override not honored; `dotenv_values` lacks explicit
  `encoding`; `generic_size or 1` treats explicit 0 as absent; render timeout path sets no
  `log_tail`; `test_config_loads_paths` is environment-coupled; no `.gitattributes`.

---

## 🕓 Session log

### 2026-08-25 — Set up Material Maker + build the MCP (Phases 1-2)
- Cloned RodZill4/material-maker into `z-Git\` as a reference, got it running (found the
  Steam `steam_appid.txt` self-relaunch gotcha), and confirmed headless `--export-material`
  renders PBR maps.
- Brainstormed and approved the MCP design (thin batch-render first, me-first audience),
  scaffolded `Tool-MaterialMaker-MCP` as a new project, pushed a private GitHub repo.
- Wrote the Phase 1-2 implementation plan, then executed it subagent-driven: 9 TDD tasks,
  each reviewed for spec + quality; fix loops on Tasks 3/5/7/9; whole-branch review (Opus)
  + one fix wave. All reviews clean. Merged to `main`, pushed, branch deleted.
