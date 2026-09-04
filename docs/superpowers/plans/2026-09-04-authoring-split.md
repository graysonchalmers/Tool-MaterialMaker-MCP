# AUTHORING split + `guide://authoring` resource Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the 996-line `docs/AUTHORING.md` monolith into a lean invariant guide (served on demand as a `guide://authoring` MCP resource) plus one per-material recipe card beside each cookbook graph.

**Architecture:** The invariant half (rubric, workflow, noise vocabulary, cross-material levers, pitfalls, the `param4=0` fix, and cross-material lessons lifted up out of the cookbook sections) stays in `docs/AUTHORING.md` and gains a `guide://authoring` MCP resource that serves it, mirroring the existing `catalog://nodes` resource. The eight per-material cookbook sections become 43 Markdown cards at `cookbook/<category>/<id>.md`, one beside each `.ptex`. The cookbook tooling is `.ptex`-specific (verified below), so cards are invisible to `list_cookbook`, the gate, and `promote_cookbook.py --check`.

**Tech Stack:** Python 3.13, the vendored `MCPServer` (`mcp.server.mcpserver`), pytest.

**Spec:** This plan. Design decisions come from the 2026-09-03 teardown #2 (recorded in `HANDOFF.md`'s "Next concrete step" #1) and the Phase-0 investigation captured in the Design section below. No separate spec doc: this is one subsystem (a docs refactor plus one read-only resource), not a multi-subsystem build.

## Global Constraints

- **No em dashes in any prose written to disk.** A Stop hook bans `—` in every file this session writes (cards, guide edits, READMEs, docstrings, commit messages). Use a period or comma in running prose; for a `Label — text` separator use `Label: text` or `Label - text`. Do not substitute parentheses.
- **Shell is PowerShell 5.1.** Sequence with `;`, use `Push-Location`/`Pop-Location`, `& "C:\path\tool.exe"`. `&&` is a parse error. Run Python via `.venv\Scripts\python.exe`.
- **Fast suite:** `.venv\Scripts\python.exe -m pytest -q -m "not integration"`. This is the gate for every task; no task needs Godot.
- **Never hand-edit a tracked `.ptex`.** Cards are new `.md` files only; no task touches a `.ptex`.
- **Follow the "pure function + thin wrapper" pattern** already in the codebase (`render.py`'s `_collect_fresh_images`, `preview.py`'s `_build_command`): put testable logic in a plain function, keep the decorated resource a one-liner.
- **Validation and errors are returned as data, never raised** (project convention), where applicable.

---

## Design

### Phase-0 investigation (done, load-bearing)

- **Cards can live at `cookbook/<category>/<id>.md`.** All three cookbook tools are `.ptex`-specific:
  - `src/mm_mcp/cookbook.py:27` globs `os.path.join(glob.escape(cookbook_dir), "*", "*.ptex")` only.
  - `tests/test_cookbook_gate.py:14` parametrizes over `list_cookbook(...)` output, i.e. that same glob.
  - `quality/promote_cookbook.py` only ever writes and diffs `.ptex` copied from `quality/authored/cookbook-*/<id>/v1.ptex`; it never scans `cookbook/` for extra files.
  A `.md` sibling is therefore invisible to all of them.
- **Split boundary in `docs/AUTHORING.md` (996 lines):**
  - **Invariant guide, keep (lines 1 to 247):** intro, "Scoring rubric", "Human-editability constraint", "Authoring workflow", "Noise vocabulary", "Node & pattern recipes" (the recolor lever, two-layer weathering, surface pattern generators, which are cross-material levers), "Common pitfalls", "The flat-normal fix: `normal_map` `param4=0`".
  - **Per-material cookbook sections, carve to cards (lines 248 to 996):** Fabric, Organics, Sci-fi, Terrain (incl. the natural-surfaces subsection), Wood, Stone/masonry (incl. the masonry-expansion subsection), Leather, Painted-metal.
- **All 43 cookbook ids appear in `docs/AUTHORING.md`**, so every graph has real recipe content to migrate. No stub fabrication is needed.
- **Resource pattern:** `server.py:514` `@mcp.resource("catalog://nodes")`. `os` is already imported in `server.py`. `config._default_cookbook_dir()` (config.py:50) resolves `<repo>/cookbook` via three `os.path.dirname` hops from `src/mm_mcp/config.py`, returning `""` when absent (wheel). The guide resource resolves `<repo>/docs/AUTHORING.md` the same way.

### The residue rule (name it so subagents decide alike)

**A single-material recipe becomes a card. A cross-material lesson stays in (or moves up into) the guide.** Concretely, these blocks are cross-material lessons and must land in the guide, not a card:

- Terrain's "topology-not-donor" lesson (pick the base generator by surface topology: connected-crack-network vs discrete-packed-cells vs scattered-pieces), currently at `docs/AUTHORING.md:524` inside the Terrain section.
- Masonry's diagnostic techniques inside the masonry-expansion subsection (the high-contrast-test-gradient diagnostic; "`warp_0.amount` cuts both ways"; "Bricks port-1 = per-brick random").
- Any "levers that did not pan out" note that is phrased as a general caution rather than one material's recipe.

When a task carves a section that contains such a block, it moves the lesson text into the guide (Phase 3 does the actual guide edit; Phase 2 card tasks leave the lesson OUT of the card and note it for Phase 3). Per-material specifics (this donor, these params, this material's own pitfall) go in the card.

### Card format

Each card is `cookbook/<category>/<id>.md` with this shape (Markdown, no YAML front matter, no em dashes):

```markdown
# <id> — <human-readable name>

_Category: <category>. Open the graph: `cookbook/<category>/<id>.ptex`._

<one or two sentence description of the material and its structural read>

## Recipe

<the migrated per-material recipe from docs/AUTHORING.md: donor/base generator,
key nodes and parameters, the levers that make this material work, and any
pitfall specific to THIS material>

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
```

Note: the card title uses `<id> - <name>` rendered with a spaced hyphen, not an em dash (Global Constraints).

### Card index

Phase 4 adds a short "Recipe cards" pointer to `cookbook/README.md` (cards live beside their graphs) and updates `docs/AUTHORING.md`'s former cookbook region to a one-line pointer at the cards. No generated index file: the tree itself is the index.

---

## Phase 1: the `guide://authoring` resource (plumbing first, content unchanged)

Add the resource against the current, un-split `AUTHORING.md`. This de-risks the resource mechanism independently of the content move.

### Task 1: `guide://authoring` MCP resource + pure reader helper

**Files:**
- Modify: `src/mm_mcp/server.py` (add `_authoring_guide_path`, `read_authoring_guide`, and the `@mcp.resource("guide://authoring")` wrapper near the existing `catalog_resource` at line 514)
- Test: `tests/test_guide_resource.py` (create)

**Interfaces:**
- Produces: `read_authoring_guide() -> str` (the guide markdown, or an unavailable notice when `docs/AUTHORING.md` is absent), `_authoring_guide_path() -> str` (absolute path or `""`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_guide_resource.py
"""guide://authoring serves docs/AUTHORING.md through a pure reader."""
import os
from mm_mcp.server import read_authoring_guide, _authoring_guide_path


def test_authoring_guide_path_points_at_the_repo_doc():
    path = _authoring_guide_path()
    assert path.endswith(os.path.join("docs", "AUTHORING.md"))
    assert os.path.isfile(path)


def test_read_authoring_guide_returns_the_invariant_guide():
    text = read_authoring_guide()
    assert "## Scoring rubric" in text
    assert "param4=0" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_guide_resource.py -v`
Expected: FAIL with `ImportError` (functions not defined).

- [ ] **Step 3: Add the helper, reader, and resource in `src/mm_mcp/server.py`** (immediately after `catalog_resource`, around line 518)

```python
def _authoring_guide_path() -> str:
    """<repo>/docs/AUTHORING.md when running from a source checkout (this
    file is src/mm_mcp/server.py, so three dirname hops up is the repo root).
    Empty string when that file does not exist, e.g. an installed wheel,
    which does not package docs/."""
    here = os.path.abspath(__file__)
    repo = os.path.dirname(os.path.dirname(os.path.dirname(here)))
    candidate = os.path.join(repo, "docs", "AUTHORING.md")
    return candidate if os.path.isfile(candidate) else ""


def read_authoring_guide() -> str:
    """The authoring guide markdown, or a short unavailable notice when
    docs/AUTHORING.md is not on disk (e.g. an installed wheel)."""
    path = _authoring_guide_path()
    if not path:
        return (
            "# Authoring guide unavailable\n\n"
            "docs/AUTHORING.md was not found next to this install. The wheel "
            "does not package docs/; use a source checkout to read the guide."
        )
    with open(path, encoding="utf-8") as fh:
        return fh.read()


@mcp.resource("guide://authoring")
def authoring_guide_resource() -> str:
    return read_authoring_guide()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_guide_resource.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Run the fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS (prior fast-suite count + 2).

- [ ] **Step 6: Commit**

```
git add src/mm_mcp/server.py tests/test_guide_resource.py
git commit -m "feat(server): serve docs/AUTHORING.md as the guide://authoring resource"
```

**Phase 1 gate:** `test_guide_resource.py` green; fast suite green; the resource returns the guide markdown. Record in STATUS.md.

---

## Phase 2: carve per-material recipes into cards (one task per category)

Each task reads its category's section in `docs/AUTHORING.md`, writes one card per cookbook id, and leaves `docs/AUTHORING.md` untouched (Phase 3 trims it). Cross-material lessons are left out of the cards and noted for Phase 3 per the residue rule.

**Shared procedure for every card task (Tasks 2 to 9):**
1. Read the category's section in `docs/AUTHORING.md` (line range given per task) and read `cookbook/README.md` for the card format.
2. For each id, create `cookbook/<category>/<id>.md` using the card template in the Design section. Pull the material's donor/base, key params, levers, and material-specific pitfall from its recipe text. Keep the human-readable name from the `.ptex` filename (e.g. `f03_canvas_burlap` -> "Canvas / burlap").
3. Do NOT include cross-material lessons (residue rule); if the section contains one, note it in the commit body for Phase 3.
4. Gate: every expected card exists and is non-trivial; fast suite still green (cards do not affect it); commit.

Per-task gate check command (PowerShell, substitute `<category>` and `<N>`):

```
$cards = Get-ChildItem "cookbook/<category>/*.md" | Where-Object { $_.Length -gt 200 }
if ($cards.Count -lt <N>) { "FAIL: fewer than <N> non-trivial cards" } else { "OK: $($cards.Count) cards" }
```

### Task 2: fabrics cards (5)

**Files:** Create `cookbook/fabrics/{f03_canvas_burlap,f04_wool_knit,f05_silk_satin,f06_velvet,f07_herringbone_tweed}.md`
**Source:** `docs/AUTHORING.md` Fabric section (lines ~248 to 331).
**Notes:** `f04_wool_knit` is the honest coarse-weave stand-in (wool-knit was closed as unreachable); the card must say so, not claim true stockinette. `f07` came from `weave2` stitch=3. Gate: 5 non-trivial cards; fast suite green; commit `docs(cookbook): fabrics recipe cards`.

### Task 3: leather cards (6)

**Files:** Create `cookbook/leather/{l01_black_oiled_leather,l02_distressed_two_tone,l03_suede,l04_reptile_exotic,l05_quilted_leather,l06_topstitched_leather}.md`
**Source:** Leather section (lines ~798 to 913).
**Notes:** l05/l06 each appear twice in the source; fold both mentions into the one card. Gate: 6 cards; fast suite green; commit `docs(cookbook): leather recipe cards`.

### Task 4: organics cards (4)

**Files:** Create `cookbook/organics/{o03_tree_bark,o04_snake_scales,o05_coral,o06_lichen_crusted_rock}.md`
**Source:** Organics section (lines ~332 to 383).
**Notes:** none special. Gate: 4 cards; fast suite green; commit `docs(cookbook): organics recipe cards`.

### Task 5: painted-metal cards (5)

**Files:** Create `cookbook/painted-metal/{pm01_powder_coat,pm02_automotive_enamel,pm03_chipped_paint,pm04_hammertone,pm05_scuffed_panel}.md`
**Source:** Painted-metal section (lines ~914 to 996).
**Notes:** the blend port/opacity fact (a blend shows port-1 where its mask is 0, port-0 where it is 1; put the majority layer on port-1) is a cross-material lesson: leave it OUT of the cards, note it for Phase 3. Keep each material's own structural read (orange-peel, enamel, chip mask, hammertone, scuffs). Gate: 5 cards; fast suite green; commit `docs(cookbook): painted-metal recipe cards`.

### Task 6: scifi cards (4)

**Files:** Create `cookbook/scifi/{sf01_hull_plating,sf02_hazard_stripe_panel,sf03_circuit_board,sf04_vent_grille_panel}.md`
**Source:** Sci-fi section (lines ~384 to 465).
**Notes:** `sf03` records the fixed trace-bleed-through (hard 0/1 opacity mask, not a mid-value albedo colorize). That fix is a general blend-opacity lesson: keep the sf03-specific "how the traces were masked" in the card, but the general "a blend's opacity is amount x port-2 mask" statement is a cross-material lesson for Phase 3. Gate: 4 cards; fast suite green; commit `docs(cookbook): sci-fi recipe cards`.

### Task 7: stone cards (8)

**Files:** Create `cookbook/stone/{s04_scattered_river_stones,s05_hex_stone_tile,s06_river_pebbles,s07_cobblestone,s08_dry_stone_wall,s09_ashlar_wall,s10_flagstone,s11_marble}.md`
**Source:** Stone/masonry section (lines ~630 to 797, incl. the masonry-expansion subsection at ~720).
**Notes:** the masonry-expansion diagnostic techniques (high-contrast-test-gradient; "`warp_0.amount` cuts both ways", haze to kill on paving vs the look on marble; "Bricks port-1 = per-brick random") are cross-material lessons: leave them OUT of the cards, note for Phase 3. Keep each material's own recipe (s07 cobblestone = voronoi-plate dry_earth; s09 ashlar needs the Bricks donor; s11 marble roughness via the Material node's own param). `s05` appears many times (it is the superseded hex-grid partial); its card should note it is superseded by s07 for true cobblestone. Gate: 8 cards; fast suite green; commit `docs(cookbook): stone recipe cards`.

### Task 8: terrain cards (8) + flag the topology lesson

**Files:** Create `cookbook/terrain/{t01_sand_dunes,t02_fresh_snow,t03_gravel,t04_grass_field,t05_cracked_ice,t06_cooled_lava,t07_forest_floor,t08_riverbed_pebbles}.md`
**Source:** Terrain section (lines ~466 to 576, incl. the natural-surfaces subsection at ~524).
**Notes:** the "topology-not-donor" lesson (pick the base by surface topology: connected-crack-network = dry_earth plates; discrete-packed-cells = voronoi + warp ~0.02; scattered-pieces = fbm Cellular 4) is the marquee cross-material lesson: leave it OUT of the cards, and reproduce its full text verbatim in the commit body so Phase 3 can lift it into the guide without re-deriving it. Keep each material's own recipe (t06 lava glow via emission port 3; t05 ice smoothness via crack-only colorize into normal; the flat-roughness-texture-for-ORM detail belongs with whichever materials use `_dry_earth_plates`). Gate: 8 cards; fast suite green; commit `docs(cookbook): terrain recipe cards + flag topology lesson for the guide`.

### Task 9: wood cards (3)

**Files:** Create `cookbook/wood/{w03_painted_wood_siding,w04_driftwood_gray,w05_dark_walnut}.md`
**Source:** Wood section (lines ~577 to 629).
**Notes:** none special. Gate: 3 cards; fast suite green; commit `docs(cookbook): wood recipe cards`.

**Phase 2 gate:** all 43 cards exist and are non-trivial (`(Get-ChildItem cookbook -Recurse -Filter *.md | Where-Object { $_.Name -ne 'README.md' -and $_.Length -gt 200 }).Count` equals 43); fast suite green; cookbook tooling unaffected (`list_cookbook` still returns 43; `promote_cookbook.py --check` still in sync). Record in STATUS.md.

---

## Phase 3: trim `docs/AUTHORING.md` to the invariant guide

One task, one file, one coherent author: remove the eight per-material cookbook sections (now migrated to cards), lift the cross-material lessons flagged in Phase 2 commit bodies up into the guide, and leave a one-line pointer at the cards. Git preserves the old file, so this is reversible.

### Task 10: trim the guide and absorb the cross-material lessons

**Files:**
- Modify: `docs/AUTHORING.md`
- Test: `tests/test_guide_resource.py` (extend)

**Interfaces:**
- Consumes: `read_authoring_guide()` from Task 1.

- [ ] **Step 1: Extend the test to assert the split shape**

```python
def test_guide_keeps_invariants_and_drops_per_material_sections():
    text = read_authoring_guide()
    # invariants stay
    assert "## Scoring rubric" in text
    assert "## Authoring workflow" in text
    assert "## Noise vocabulary" in text
    assert "param4=0" in text
    # the topology-not-donor lesson was lifted up into the guide
    assert "topology" in text.lower()
    # per-material cookbook sections are gone (now cards)
    assert "## Fabric cookbook" not in text
    assert "## Leather cookbook" not in text
    assert "## Painted-metal cookbook" not in text
    # a pointer at the cards exists
    assert "cookbook/" in text
```

- [ ] **Step 2: Run it, watch it fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_guide_resource.py::test_guide_keeps_invariants_and_drops_per_material_sections -v`
Expected: FAIL (the cookbook sections still exist).

- [ ] **Step 3: Edit `docs/AUTHORING.md`**
  - Delete the eight per-material cookbook sections (the region from the "## Fabric cookbook" heading through end of "## Painted-metal cookbook").
  - Into the "Common pitfalls" area (or a new "## Cross-material lessons" section directly after it), add, in prose with no em dashes: the topology-not-donor lesson (verbatim from Task 8's commit body), the blend port/opacity lesson (Tasks 5 and 6), and the masonry diagnostic techniques (Task 7).
  - Replace the deleted region with a one-line pointer: `Per-material recipes now live as cards beside their graphs: see cookbook/<category>/<id>.md (and cookbook/README.md).`

- [ ] **Step 4: Run the resource tests + fast suite**

Run: `.venv\Scripts\python.exe -m pytest tests/test_guide_resource.py -v ; .venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS.

- [ ] **Step 5: Sanity-check the size**

Run: `(Get-Content docs/AUTHORING.md).Count`
Expected: roughly 300 lines or fewer (down from 996), confirming the recipes left.

- [ ] **Step 6: Commit**

```
git add docs/AUTHORING.md tests/test_guide_resource.py
git commit -m "refactor(docs): AUTHORING.md is now the invariant guide; recipes moved to cards"
```

**Phase 3 gate:** the extended resource test green; `docs/AUTHORING.md` has no per-material cookbook section and does have the lifted cross-material lessons plus the cards pointer; fast suite green. Record in STATUS.md.

---

## Phase 4: fix inbound references, READMEs, docstrings, and add the card-parity test

### Task 11: reference fixup + card-parity regression test

**Files:**
- Modify: `README.md`, `quality/README.md`, `cookbook/README.md`, `src/mm_mcp/server.py` (the `load_example`/`list_examples` docstrings that mention AUTHORING), `src/mm_mcp/cookbook.py` (module docstring)
- Test: `tests/test_cookbook_gate.py` (add a card-parity test)

**Interfaces:**
- Consumes: `list_cookbook` (already imported in the gate test).

- [ ] **Step 1: Add the card-parity test to `tests/test_cookbook_gate.py`**

```python
@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_cookbook_graph_has_recipe_card(entry):
    card = os.path.join(os.path.dirname(entry.path), f"{entry.name}.md")
    assert os.path.isfile(card), f"missing recipe card {card}"
    assert os.path.getsize(card) > 200, f"card too small to be a real recipe: {card}"
```

- [ ] **Step 2: Run it, expect PASS** (Phase 2 already created all 43 cards)

Run: `.venv\Scripts\python.exe -m pytest tests/test_cookbook_gate.py -q`
Expected: PASS (43 new parametrized cases green). If any fail, a card is missing or too small: fix the card, not the test.

- [ ] **Step 3: Fix the inbound references** (grep first: `grep -rn "AUTHORING" README.md quality/README.md cookbook/README.md src/mm_mcp/server.py src/mm_mcp/cookbook.py`)
  - `quality/README.md`: change "see AUTHORING.md for every recipe" to point invariants at `docs/AUTHORING.md` (the guide) and per-material recipes at the cards.
  - `README.md`: where it describes the cookbook/AUTHORING, note the guide-plus-cards split and the `guide://authoring` resource (add it to the resources list alongside `catalog://nodes`).
  - `cookbook/README.md`: add a short "Recipe cards" line (each graph has a `<id>.md` card beside it).
  - `src/mm_mcp/server.py` and `src/mm_mcp/cookbook.py` docstrings: where they say "see docs/AUTHORING.md", keep that for invariants and add "and the per-material card `cookbook/<category>/<id>.md`".
  - Do NOT touch history files: `CHANGELOG.md`, `HANDOFF.md`, `docs/HANDOFF_ARCHIVE.md`, `STATUS.md`, `docs/superpowers/**`, `quality/scorecards/**`, and the `quality/cookbook_*.py` builder comments (they point at the recipe that is now a card, but rewriting generated-history comments is out of scope; leave them).

- [ ] **Step 4: Run the fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS (fast suite + 43 card-parity cases).

- [ ] **Step 5: Commit**

```
git add README.md quality/README.md cookbook/README.md src/mm_mcp/server.py src/mm_mcp/cookbook.py tests/test_cookbook_gate.py
git commit -m "docs: point references at the guide+cards split; add card-parity gate"
```

**Phase 4 gate:** card-parity test green (43 cards); no stale "AUTHORING.md for every recipe" pointer remains in live docs; README lists the `guide://authoring` resource; fast suite green; CI green after push. Record in STATUS.md.

---

## Self-Review

**Spec coverage:** guide resource (Phase 1) ✓; cards for all 43 graphs (Phase 2, 8 category tasks covering fabrics 5 + leather 6 + organics 4 + painted-metal 5 + scifi 4 + stone 8 + terrain 8 + wood 3 = 43) ✓; residue rule applied (Phases 2 flag, Phase 3 absorbs) ✓; guide trim (Phase 3) ✓; references + parity gate (Phase 4) ✓.

**Placeholder scan:** every task lists exact filenames, ids, source line ranges, and concrete test code. No TBD/TODO.

**Type consistency:** `read_authoring_guide()` and `_authoring_guide_path()` are defined in Task 1 and only re-consumed (not redefined) in Tasks 10 and 11. The card path convention `cookbook/<category>/<id>.md` is identical in the Design section, every Phase 2 task, Phase 3's pointer, and Phase 4's parity test.
