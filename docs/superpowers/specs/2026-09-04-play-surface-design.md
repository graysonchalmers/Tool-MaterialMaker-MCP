# Design Spec: Live Web Play Surface

_Date: 2026-09-04_
_Status: approved in brainstorming, pending Grayson spec review_
_Sub-project: "Material Maker for dummies" sub-project 2 (sub-project 1, the
cookbook subgraph retrofit, is complete as of 2026-09-04)._

## Purpose

A browser-based "play surface" that lets a non-technical person tweak one of
the cookbook materials through a handful of friendly sliders and watch the
result on a live 3D sphere, without ever seeing the raw node graph. This is the
direct answer to the origin of the "Material Maker for dummies" idea: the raw
node graph "scared the shit off" a non-technical viewer Grayson showed it to.

The subgraph retrofit (sub-project 1) already made each of the 46 cookbook
materials expose a curated, named set of parameters on its collapsed subgraph
nodes. This project surfaces those exposed parameters as web sliders. No
re-authoring of materials is required.

### Audience and North Star relationship

This surface is deliberately aimed at the North Star's **secondary** audience
("anyone who finds the public repo and wants a lower-friction way in"), and it
deliberately hides the node graph, which is the opposite of the core learning
loop (step 3 of the North Star: open the `.ptex` and learn the graph). That is
an intentional, scoped exception, not scope creep into the core:

- The play surface is a **companion**, launched by its own command, separate
  from both the MCP server and Material Maker's own UI. It does not replace
  either.
- Even its export hands back the real editable `.ptex`, not only flattened
  PNGs, so a curious player who wants to go deeper still gets the graph.
- A one-line note is added to `docs/NORTH_STAR.md` recording that a secondary
  play surface exists and why it hides the graph, so the exception is documented
  rather than silently contradicting the stated non-goals.

## Non-goals

- Not a material editor. The user can only move the sliders the author chose to
  expose; they cannot rewire nodes, add nodes, or change anything outside the
  exposed set.
- Not a replacement for Material Maker's own UI or for the MCP round-trip loop.
- Not a multi-user or hosted web service. It is a local, single-user server
  bound to localhost, launched on demand.
- Not photoreal. Same quality bar as the rest of the project.
- Not authentication, accounts, or persistence beyond a single session.

## Scope (v1)

All four of the following are in the first shippable cut (Grayson's call):

1. **Cookbook gallery picker** : a thumbnail gallery of the 46 cookbook
   materials; click one to load its sliders.
2. **Standalone headless render loop** : the local server applies slider
   changes to the material's graph JSON and renders maps via the existing
   headless `render.py`, with no Material Maker window required.
3. **Live auto-detect** : if a live Material Maker session is already up, drive
   it via the existing live-control path instead, so the person also sees it
   move in-app.
4. **Download maps** : export the current tweaked material's four PBR maps plus
   its `.ptex` as a zip.

Internal build order (for the plan, not a scope reduction): standalone core
working end to end first (gallery, sliders, headless render, WebGL preview),
then the live auto-detect layer, then download.

## Architecture

A new standalone web server in its own package, separate from the MCP server.
The MCP server stays a pure MCP surface for Claude; the play server is a pure
web surface for a human. They share the render and graph plumbing but not the
transport. Rejected alternatives (recorded so they are not revisited): bolting
HTTP endpoints onto the MCP `server.py` (mixes two transports and audiences in
the one module the teardowns keep clean), and a pure static frontend talking to
MCP directly (browsers cannot speak MCP's stdio JSON-RPC, so it needs a bridge
server anyway, which collapses back into this design).

The Python HTTP layer is the **standard library `http.server`**, not FastAPI or
another framework: the endpoint set is tiny, concurrency is low (renders are
debounced and serialized), and it honors the project's minimal-dependency ethos
(the same reason the project uses the stdlib `pngread.py` instead of Pillow).
three.js is vendored as a static file in the package, so there is no runtime CDN
dependency.

### Module layout (units)

New package `src/mm_mcp/play/`, each unit with one clear job:

- `play/server.py` : the stdlib `http.server` application, routing, static-file
  serving, and the `mm-play` entry point. Owns the socket and nothing else.
- `play/api.py` : the request handlers (list materials, get a material's
  sliders, apply-and-render, export). Pure functions that take already-parsed
  input and return JSON-serializable data or bytes, so they are unit-testable
  without a socket.
- `play/sliders.py` : the slider-derivation bridge (see below). Turns a
  material's subgraph widgets plus the catalog into slider specs, and applies a
  set of slider values back onto a graph.
- `play/renderer.py` : a thin facade that selects the render path (standalone
  `render.py` vs live `live.py`) and returns rendered map file paths. The only
  unit that knows both paths exist.
- `play/static/` : `index.html`, `app.js` (three.js PBR sphere plus the slider
  UI), a vendored `three.min.js`, `style.css`.

Reused as-is: `cookbook.py` (list/find materials), the catalog (parameter
ranges), `render.py` (headless render of a graph dict), `live.py` (the live
path), and `paths.py` guards for any file the server reads or serves.

### The slider-derivation bridge (`play/sliders.py`)

This is the one genuinely new piece of logic and the payoff of the subgraph
retrofit.

**Deriving sliders from a material.** For a loaded material graph, walk every
top-level `type: "graph"` node. For each, read its `gen_parameters` remote
node's `widgets` list. For each widget, resolve its `linked_widgets` binding
(the internal node name plus internal param name) to that internal node's
**type**, then look up that param in the catalog to get its `type`, `default`,
`min`, `max`, and `step`. The catalog already carries these fields per parameter
(verified: `catalog_builder.py` emits `default`/`min`/`max`/`step`, and for
enum-valued params derives `min`/`max` from the value-list length).

Output, one entry per exposed widget:

```
{
  "group": "<subgraph node label, e.g. 'Dune Ripples'>",
  "slot_id": "<e.g. 'param0'>",
  "label": "<author's friendly shortdesc, e.g. 'Ripple scale'>",
  "kind": "float" | "int" | "enum" | "color",
  "min": <number, absent for color>,
  "max": <number, absent for color>,
  "step": <number, absent for color>,
  "value": <current value read from the widget's stored param>,
  "binding": {"node": "<internal node name>", "widget": "<internal param>"}
}
```

The author-written `shortdesc` (e.g. "Ripple scale") supplies the friendly
label, so no re-authoring of the 46 materials is needed. `color`/gradient
widgets are flagged with `kind: "color"`; v1 may render them as a read-only
swatch or omit them from the panel, but the bridge still reports them so the UI
decides.

**Applying values back.** Given a material graph and a `{slot_id: value}` map,
for each slider write its value into the linked internal node's parameter (the
reverse of the binding above) and into the subgraph node's own mirrored
`parameters`/`gen_parameters` copy, so the change is consistent whether rendered
headless (reads the internal node) or via a live session. This is a pure graph
transform returning a new graph dict.

**Gate.** A parametrized test across all 46 cookbook materials asserts each
yields a non-empty, catalog-consistent slider set (every reported `min`/`max`
present for numeric kinds, every binding resolvable), mirroring the existing
`test_cookbook_subgraph_gate.py`.

### Render loop and latency

Rotating and relighting the WebGL sphere is free and instant in the browser; it
never hits the server. A **slider value change** posts the full current slider
state to `POST /api/render`, which applies the values onto the graph
(`sliders.apply`) and renders the four maps.

Latency levers, all part of the design:

- **Small interactive renders.** The interactive render is 256px, which returns
  in roughly a couple of seconds, versus full-size (512 or larger) on demand.
- **Client debounce.** The client fires one render on slider release (or after a
  short idle), not once per frame during a drag.
- **Server-side serialization.** Renders are serialized: only one Godot process
  runs at a time, per the project's own render-orphan-contention rule. A render
  request that arrives while one is in flight supersedes the queued pending
  request (latest values win) rather than launching a parallel Godot. The
  serialization is owned by `renderer.py`.
- **Full-quality button.** A "Render full quality" control re-renders at full
  size on demand for the final look.

### Standalone vs live auto-detect (`play/renderer.py`)

On each render request, `renderer.py` cheaply checks for a live Material Maker
session: the existing `live.ping` on the known port with a short timeout. If one
answers and reports `has_graph`, it drives the live path
(`live.set_param` per changed slider, then `live.render`); otherwise it renders
headless via `render.render(graph_dict, size=...)`. The web page behaves
identically either way; only the backend path differs. Building order in the
plan: headless first (the whole loop works with no MM), then the ping-and-switch
layer on top.

Note on the live path and material source: the live session renders whatever
graph is currently loaded in Material Maker, which may not be the material the
user picked in the gallery. How v1 handles that mismatch is specified once under
"Open questions / known limitations" below.

### Data flow / endpoints

- `GET /` : the static play page.
- `GET /api/materials` : gallery data from `cookbook.py` (id, category,
  thumbnail URL).
- `GET /api/material/<id>` : the material's slider specs (via the bridge) plus
  the URLs of its current rendered maps (an initial render at load, or the
  material's existing cookbook thumbnail maps if cheaper).
- `POST /api/render` : body `{material_id, values, size}`; applies values,
  renders via the auto-detect path, returns the four map URLs.
- `GET /api/maps/<token>/<name>.png` : serves a rendered map PNG from the
  per-session output directory, bounded by `paths.py` guards.
- `POST /api/export` : zips the current material's four maps plus its tweaked
  `.ptex`; returns the zip as a download.

All request bodies are small JSON. The server binds to `127.0.0.1` on a fixed
default port (configurable), single-user, no auth.

### Download (`/api/export`)

Bundles the four current maps plus the tweaked `.ptex` into a zip returned as a
file download. Including the `.ptex` keeps the export honest against the North
Star: even the play export hands back the real editable graph, so a curious
player can still open it in Material Maker later.

### Frontend (`play/static/`)

A single static page, intentionally minimal and vendored (no build step, no
package manager):

- A left panel: the cookbook gallery (thumbnails grouped by category) and, once
  a material is picked, the slider list grouped by the material's subgraph
  labels. Numeric sliders for float/int, a stepped control for enum, a swatch or
  omission for color.
- A right panel: a three.js scene with a single sphere shaded by
  `MeshStandardMaterial` using the four rendered maps (albedo, normal, roughness
  or ORM, height as displacement or bump). Orbit controls for free rotation; a
  simple light the user can move. A "Render full quality" button and a
  "Download" button.
- Client logic: debounced render requests, a "rendering..." indicator, and map
  texture reloads when a render returns.

three.js is vendored as `play/static/three.min.js` (pinned version recorded in a
short `play/static/VENDOR.md`), loaded by a local `<script>` tag, so there is no
runtime network dependency.

### Packaging / launch

- A new `mm-play` console script in `pyproject.toml` alongside `mm-mcp`, its
  entry point in `play/server.py`. Running `mm-play` starts the server and opens
  the default browser to `http://127.0.0.1:<port>`.
- Static assets ship in the wheel via `tool.setuptools.package-data`, the same
  mechanism `preview_project/` already uses (verified pattern).
- `doctor.py` gains one informational line reporting that the play surface is
  installed and on which port it defaults to.
- Config: a `MM_PLAY_PORT` (default in `config.py`) and reuse of the existing
  `MM_COOKBOOK_DIR`, `MM_OUTPUT_DIR`, and render config. No new required config.

## Testing strategy

- `play/sliders.py`: pure unit tests, including the all-46-materials
  parametrized gate (non-empty, catalog-consistent slider sets; round-trip
  derive-then-apply preserves unrelated params).
- `play/api.py`: pure unit tests of each handler against real cookbook graphs
  with a faked renderer (correct JSON shapes, error-as-data on unknown material
  id / bad body / out-of-range value).
- `play/renderer.py`: unit tests of path selection with a faked `live.ping`
  (live when ping reports `has_graph`, headless otherwise), and the
  serialization behavior (a second request supersedes the pending one).
- `play/server.py`: a thin smoke test (server boots, serves `/`, returns 404 on
  an unknown path, 400 on a malformed body).
- One integration test (`@pytest.mark.integration`): `POST /api/render` end to
  end against real headless Godot, asserting four non-empty map PNGs, mirroring
  the existing live/preview integration tests.
- Fast suite (`pytest -q -m "not integration"`) stays green; the integration
  test runs under the full suite only.

## Error handling

- All API errors are returned as JSON data (`{"ok": false, "error": ...}`) with
  an appropriate HTTP status, never an unhandled 500 traceback, consistent with
  the project convention that validation and lookup errors are data, not
  exceptions.
- Unknown material id, malformed request body, and out-of-range slider values
  are each reported as a specific error the frontend can show.
- A render timeout or Godot failure returns an error the frontend surfaces as a
  "render failed" state, leaving the last good preview in place; the underlying
  render-orphan cleanup (`_kill_tree`) already exists in `render.py`.
- Path-bounded file serving: `/api/maps/...` and `/api/export` run their paths
  through `paths.py` guards, refusing anything outside the allowed output dir.

## Open questions / known limitations (recorded, not blocking)

- **Live path material mismatch.** In v1 the live path only drives a live
  session when the picked material matches what is loaded in Material Maker;
  otherwise it falls back to headless. Pushing the picked material into the live
  session first is out of v1 scope and overlaps the deferred `live_load`
  backlog item.
- **Color/gradient widgets.** v1 renders exposed color widgets as a read-only
  swatch or omits them; interactive gradient editing is deferred.
- **Displacement vs normal in WebGL.** The height map may be used as either a
  bump or a small displacement on the sphere; the exact three.js material config
  is a build-time detail to tune against the real maps, not a spec-level
  decision.
- **Concurrency.** The single-Godot serialization means two rapid full-quality
  renders queue; acceptable for a single-user local surface.

## Success criteria

- `mm-play` launches, opens a browser, and shows the 46-material gallery.
- Picking a material shows its author-named sliders with sane ranges.
- Moving a slider updates the WebGL sphere within a few seconds (headless path),
  with free rotation/relight in between.
- With a live Material Maker session open on the matching material, the same
  tweak also moves the in-app preview.
- Download returns a zip with four maps plus the `.ptex`.
- The all-46 slider-derivation gate passes; the fast suite stays green; the one
  integration test renders real maps.
