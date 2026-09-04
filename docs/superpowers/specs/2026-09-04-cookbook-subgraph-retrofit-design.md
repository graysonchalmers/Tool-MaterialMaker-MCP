# Design: subgraph retrofit for the cookbook

_2026-09-04_

## Problem

Grayson's backlog idea, captured in `_agent-commons/ideas/Tool-MaterialMaker-MCP.md`
(2026-08-29 pickup session): a "Material Maker for dummies" simplified interface, because
"if you showed someone the material maker node network it just scared the shit out of them."

Brainstorming this idea surfaced a real, feasible answer that costs no new infrastructure.
Material Maker already has a native mechanism for exactly this: **subgraph nodes**. Select
a cluster of nodes, group them (Ctrl+G in the app), and Material Maker collapses them into
a single node of `type: "graph"`, with an internal **Parameters** remote node exposing a
curated, named subset of the cluster's parameters as ordinary widgets on the collapsed
node. Opening a graph that uses subgraphs shows a handful of friendly, labeled nodes
instead of every raw node and wire, with the full detail still one double-click away.

This is not a new mechanism this project has to invent. It's the same shape Material Maker
already uses for its own 50 bundled compound "graph"-family nodes (`normal_map`,
`occlusion`, etc.), which `mm_mcp`'s catalog builder already treats as a special type
(`SPECIAL_TYPES`, see `CLAUDE.md`). `normal_map.mmg` was read as a concrete reference for
the exact JSON shape (see Design below). Godot's render path treats `type: "graph"`
generically, so a hand-authored subgraph node renders correctly through the existing
headless `render_graph` path with zero Material Maker GUI interaction required to build or
validate it.

Grayson chose the larger of two possible scopes: not just applying this to materials
authored from now on, but retrofitting all 46 existing cookbook materials, so the benefit
lands immediately across the whole cookbook rather than trickling in as new materials get
added.

## Decision

Build one new pure graph-surgery primitive, `group_into_subgraph`, in
`quality/author_helpers.py`, alongside the existing `rewire`/`retype`/`drop_conn`/`add_node`
family. Then retrofit all 46 existing cookbook materials by editing each
`quality/cookbook_<category>.py` builder to call it, re-promoting through the existing
`promote_cookbook.py` pipeline. No new MCP tool, no live-control change, no new
infrastructure: this is graph-authoring-time surgery, the same category of work as every
other authoring lever documented in `docs/AUTHORING.md`.

This is explicitly an **organizational** change, not a recipe change. A retrofitted
material must look and render the same as it does today; only the internal shape of its
top-level graph changes (fewer, friendlier, collapsible nodes instead of many raw ones).

## Design

### The `group_into_subgraph` primitive

Signature:

```python
def group_into_subgraph(graph: dict, member_names: list[str], name: str, label: str,
                         exposed: list[tuple[str, str, str, str]]) -> None:
    """Collapse the named nodes (and the connections between them) into one
    node of type "graph", replacing them in `graph` in place.

    exposed: (internal_node_name, internal_param_name, slot_id, friendly_label)
    tuples. Each becomes one widget on the collapsed node's Parameters remote,
    linked back to the real internal parameter it controls. slot_id is the
    external-facing parameter name (paramN by convention, matching how
    normal_map.mmg names its own exposed slots).
    """
```

Algorithm, working from the reference shape in `normal_map.mmg`:

1. **Partition connections.** Split `graph["connections"]` into three groups relative to
   `member_names`: fully internal (both endpoints inside the group), incoming boundary
   (external source into a member node), and outgoing boundary (member node into an
   external target). Everything else is untouched.
2. **Build `gen_inputs`/`gen_outputs`.** Two `type: "ios"` nodes. Each incoming boundary
   connection becomes one port on `gen_inputs`; each outgoing boundary connection becomes
   one port on `gen_outputs`. A port's declared `type` (e.g. `f`, `rgb`, `rgba`) is looked
   up from the catalog for the node/port it used to connect to, so the collapsed node's
   ports type-check the same way the original wiring did.
3. **Rewire internally.** Boundary connections get rehomed to point at the new
   `gen_inputs`/`gen_outputs` ports instead of the outside world; fully internal
   connections are copied unchanged. This becomes the new node's own `"connections"`.
4. **Build the Parameters remote.** One `type: "remote"` node (conventionally named
   `gen_parameters`) with a `widgets` list, one `linked_control` entry per `exposed` tuple,
   pointing at `{node: internal_node_name, widget: internal_param_name}`, exactly the shape
   `normal_map.mmg`'s `gen_parameters` node uses. The collapsed node's own top-level
   `"parameters"` dict gets one entry per `slot_id`, seeded from the current value of the
   internal parameter it's linked to (so the retrofit doesn't change any effective value).
5. **Assemble the collapsed node.** `{"name": name, "label": label, "type": "graph",
   "node_position": <centroid of the replaced nodes>, "parameters": {...from step 4},
   "nodes": [gen_inputs, gen_outputs, gen_parameters, *member_nodes],
   "connections": [...from step 3]}`.
6. **Update the parent graph.** Remove the member nodes from `graph["nodes"]`, append the
   collapsed node. Remove the fully-internal connections from `graph["connections"]`;
   repoint each former boundary connection's member-node endpoint at the collapsed node's
   corresponding new port index instead.

This is pure JSON surgery, no Godot dependency, and testable in isolation the same way
`tests/test_author_helpers.py` already tests `rewire`/`retype`.

### Per-material retrofit process

Ten dispatches, one per cookbook category (fabrics, organics, sci-fi, terrain, wood, stone,
leather, painted-metal, glass, plastics), matching the batching pattern already used for the
donor-vendoring and AUTHORING-split sessions. Each dispatch:

1. Reads its category's `quality/cookbook_<category>.py` builder.
2. For every `build_*` function, decides 2 to 4 sensible groupings by node role (a common
   starting shape: "Base Color", "Surface Detail", "Roughness/Height", but the actual
   grouping is a per-material judgment call, not a fixed template) and 1 to 3 friendly
   exposed parameters per group.
3. Adds calls to `group_into_subgraph` at the end of each `build_*` function, before it
   returns.
4. Re-promotes through `promote_cookbook.py`, updates thumbnails via `_make_previews.py`
   for that category only (per the existing whole-label-regen gotcha, checking `git status`
   afterward and reverting anything swept up that wasn't actually changed).
5. Proves non-regression (see Testing) before the dispatch's own review.

### What is explicitly out of scope

- No change to `validator.py`'s core validation logic; `type: "graph"` nodes are already a
  recognized, generically-handled type.
- No change to the live-control stack (`live.py`, `addons/mm_live`) — this retrofit is
  offline authoring surgery only, not something Grayson does through a live session.
- No change to `catalog_builder.py`'s existing `SPECIAL_TYPES`/`generic_size` handling;
  those concern Material Maker's own bundled `graph`-family nodes (registered catalog
  types), not one-off subgraphs embedded inline in a single material's own `.ptex`, which
  don't need catalog registration to render.
- Sub-project 2 (the standalone live web companion) is a separate, later spec, deliberately
  sequenced after this one so it can read its slider definitions from the exposed
  parameters this retrofit produces, instead of inventing a separate curation mechanism.

## Testing

**New tests for the primitive itself** (`tests/test_author_helpers.py`), no Godot required:
boundary-connection detection, `ios` port generation and typing, widget/parameter linkage,
and a round-trip check that a simple two-node grouping produces a `type: "graph"` node
matching the `normal_map.mmg` reference shape.

**The regression gate**, since Godot's render is already documented as non-deterministic
run to run (a real, previously-hit gotcha, not theoretical): for every retrofitted
material, render before and after the retrofit and compare. The bar is not byte-identity;
it's that `validate_graph` still passes with zero errors, the top-level node count actually
dropped, and the rendered maps match within a small tolerance consistent with Godot's known
render noise (not a structural difference like a missing pattern or a different color). A
new parametrized gate test, alongside the existing recipe-card-parity test, checks this
across all 46 retrofitted cases.

**Docs**: `docs/AUTHORING.md` gets a new lever entry describing subgraph grouping, and
`quality/README.md`'s cookbook-growth section gets a one-line mention that new categories
should group into subgraphs from the start rather than needing a later retrofit pass.

Run the full fast suite (`pytest -q -m "not integration"`) after each category dispatch and
again at the end of the whole retrofit.

## Risks

- **Per-material judgment quality (accepted, mitigated by review).** Unlike the mechanical,
  fully-scriptable donor-vendoring change, deciding *which* nodes group together and what
  to call them is a real design choice per material, done by a dispatched task rather than
  a formula. Each dispatch's grouping choices get reviewed before merge, the same way past
  cookbook additions were reviewed.
- **Render-noise false positives (known, already documented).** A prior session hit exactly
  this shape of problem (`f04_wool_knit`'s thumbnail came back byte-different from
  unrelated render non-determinism). The tolerance-based comparison in Testing above is
  designed around that known behavior rather than re-discovering it mid-retrofit.
- **Scope creep into sub-project 2 (guarded against).** The live web companion is
  explicitly out of scope here; this spec produces the exposed-parameter structure that
  project will consume later, nothing more.
