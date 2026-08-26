# HANDOFF — Tool-MaterialMaker-MCP

The session baton. Read at pickup, rewrite at wrap-up.

## Where things stand

- **Date:** 2026-08-25
- **Phase:** 0 (harness) — scaffolding just created.
- Project bootstrapped from the approved design. Nothing implemented yet beyond
  scaffold. Upstream Material Maker verified to render headlessly on this machine.

## What just happened

- Brainstormed and approved the design: thin batch-render MCP first, live-control
  deferred. Me-first audience.
- Confirmed feasibility against the upstream repo: `.ptex` is JSON, `--export`
  renders headless, ~392 nodes carry machine-readable schemas.
- Created project scaffold + design spec. Pushed to GitHub.

## Next concrete step

- Have Grayson review the design spec
  ([docs/superpowers/specs/2026-08-25-material-maker-mcp-design.md](docs/superpowers/specs/2026-08-25-material-maker-mcp-design.md)).
- Then create the implementation plan (writing-plans skill) and start Phase 0:
  the smoke test that renders a known example `.ptex` and asserts a PNG appears.

## Open questions

- Phase 3 usable-hit-rate target (the quality bar) not yet set.
- Whether Phase 1 ships variant generation or defers it.

## Heads-up for the next agent

- Do not modify `C:\Projects-local\z-Git\material-maker` in Phase 1; it is the
  pristine upstream reference and the render target.
- Render runs need the MM project's `steam_appid.txt` present or Godot exits fast.
