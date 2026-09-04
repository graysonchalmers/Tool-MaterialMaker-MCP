# Cookbook as data: design

_2026-09-03. Follows the second teardown (same date). Scope: one `phased-rebuild` pass._

## The problem

The cookbook is the project's highest-value asset and its least reachable one.
43 authored materials across 8 categories live only as the output of
`quality/cookbook_*.py` builders, written to the gitignored
`quality/authored/cookbook-<category>/<id>/v1.ptex`. What the repo tracks is
43 PNG thumbnails of them. The MCP server's `list_examples` / `load_example`
read only Material Maker's own bundled `examples/` dir, so neither a person
cloning the repo nor an assistant authoring over MCP can start from a cookbook
graph. NORTH_STAR step 3 ("open the `.ptex` the assistant built") is being
withheld for exactly the graphs that took the most work.

Secondary: the 28 informal cookbook materials have no regression baseline. 26
of 43 builders sit on three upstream donor files (`crocodile_skin`, `rock`,
`dry_earth`); an upstream change would silently alter every dependent graph.

## Decisions

1. **Tracked location:** `cookbook/<category>/<id>.ptex` at the repo root.
   `category` is the builder label minus its `cookbook-` prefix (`fabrics`,
   `leather`, `organics`, `painted-metal`, `scifi`, `stone`, `terrain`,
   `wood`). One file per material, byte-identical to the builder's `v1.ptex`.
   Thumbnails stay where they are (`docs/images/cookbook-<category>/<id>.png`);
   consolidating the image sets is a separate hygiene item.
2. **Promotion, not un-ignoring.** `quality/authored/` stays gitignored. A new
   `quality/promote_cookbook.py` copies each `v1.ptex` into `cookbook/`, and
   `--check` mode diffs the regenerated output against the tracked files and
   exits non-zero on any difference. That diff is the regression baseline:
   rebuild with the builders, then `--check`.
3. **Config:** new `MM_COOKBOOK_DIR` env var and `Config.cookbook_dir` field.
   Default resolution: the env var if set; else `<repo>/cookbook` resolved
   from the package's own location when that directory exists; else empty
   (no cookbook, tools fall back to bundled examples only). The wheel does not
   package `cookbook/` in this pass; the distribution route is GitHub clone,
   where it is present.
4. **Lookup module:** `src/mm_mcp/cookbook.py` with `list_cookbook(dir)` and
   `find_cookbook(dir, name)`. Keeps `server.py` thin and gives the gate test
   and the doctor one shared walker.
5. **Tool surface (breaking, deliberate, zero external users):**
   - `list_examples(source="all") -> {"ok": True, "examples": [{"name", "source", "category"}]}`.
     `source` is one of `all`, `material_maker`, `cookbook`. `category` is
     `None` for bundled examples. An unknown `source` returns
     `{"ok": False, "error": ...}` as data.
   - `load_example(name, source="auto") -> dict`. Success returns the raw
     graph dict, unchanged from today (existing callers use it directly as a
     `ptex`). `auto` tries the cookbook first, then bundled examples. Unknown
     name, unknown source, or a path-traversal name returns
     `{"ok": False, "error": ...}` instead of raising.
6. **Gate test:** `tests/test_cookbook_gate.py` mirrors `test_examples_gate.py`:
   every tracked cookbook graph validates against the catalog with zero hard
   errors, ids are unique across categories, and every graph has its
   thumbnail. Runs in the fast suite, so CI covers it.
7. **Doctor:** `mm-mcp --check` gains a `cookbook` line reporting the count and
   directory, or "not found (optional)". Never a failing check.
8. **Docs:** README tool table and cookbook section (43 materials, eight
   categories, how to open one, contact sheet regenerated at 43),
   `cookbook/README.md`, `quality/README.md` promote step, AUTHORING.md
   workflow step 1 mentions the cookbook source.

## Non-goals (this pass)

- Per-material metadata cards or a `cookbook://index` resource.
- Splitting `docs/AUTHORING.md` or exposing it as a resource.
- Folding `examples/` into the cookbook, or consolidating the image sets.
- Packaging `cookbook/` into the wheel.

## Phases and gates

| Phase | Deliverable | Gate |
|---|---|---|
| A | `promote_cookbook.py`, tracked `cookbook/` tree, `cookbook.py`, gate test | `pytest tests/test_cookbook_gate.py` green (43 graphs validate, ids unique, thumbnails present); `promote_cookbook.py --check` exit 0 |
| B | `cookbook_dir` config, dual-source `list_examples`/`load_example`, doctor line | fast suite green; a real render of `load_example("f07_herringbone_tweed")` through `render_graph` produces 4 PNGs |
| C | README, cookbook/README, quality/README, AUTHORING, contact sheet | counts in README match `cookbook/` on disk; CI green on push |
