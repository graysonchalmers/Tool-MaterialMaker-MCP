# Design Spec: `live_load` (load a graph into a live Material Maker session)

_Date: 2026-09-04_
_Status: approved in brainstorming, pending Grayson spec review_
_Closes backlog item J ("Load an existing `.ptex` into a live session"). Unblocks
the play surface's "push the picked material into a live session" flow (the
deferred v1 open question in `2026-09-04-play-surface-design.md`)._

## Purpose

Add the one missing verb in the live-control stack: replacing the graph currently
shown in a running Material Maker session with a caller-supplied one. Today the
live tools can add nodes, wire them, set params, reposition, render, and clear to
an empty material, but there is no way to load a whole existing graph. That gap is
what forces the play surface to fall back to headless whenever the material a
person picks in the gallery is not already the one open in Material Maker.

Two audiences get it at once:

- **Claude / MCP (primary):** a new `live_load` MCP tool, so Claude can push a
  freshly-authored or on-disk graph into the live window and watch it appear,
  the natural companion to the existing `live_get_graph`.
- **The play surface (secondary):** `play/renderer.py` calls the same client
  method to push the picked cookbook material into a live session before driving
  its sliders, so the live path works for any pick, not only a coincidental match.

## Non-goals

- Not a save. `live_load` changes what is shown in the running session; it never
  writes a `.ptex` to disk. Export stays the existing separate path.
- Not a new tab manager. It replaces the current tab's graph in place. It does
  not add, close, or switch tabs.
- Not a live-reload watcher. One load per call, driven by the caller.
- No change to how the play surface drives slider tweaks (still per-param
  `set_param` after the initial load).

## Scope

1. `load_graph` command in the addon (`addons/mm_live/live_server.gd`).
2. `live.load_graph(graph=None, path=None, cfg=...)` client method
   (`src/mm_mcp/live.py`).
3. `live_load` MCP tool (`src/mm_mcp/server.py`).
4. Play-surface wiring in `play/renderer.py` (push the picked material into a
   live session on a pick change, inside the render lock).
5. Tests (unit + one integration) and docs (STATUS, README, live-control notes,
   HANDOFF, item J closed).

## Architecture

The live stack is a three-layer pipe that every existing live verb already
follows, and `live_load` adds one rung to each layer without changing the shape:

```
MCP tool (server.py)  ->  client (live.py)  ->  socket  ->  addon command (live_server.gd)  ->  Material Maker's own method
live_load                 load_graph                        _cmd_load_graph                    graph_edit.set_new_generator
```

### 1. Addon command `_cmd_load_graph` (`live_server.gd`)

Registered in `_dispatch`'s `match` as `"load_graph"`, `await`ed (it awaits a
coroutine internally, see below).

Behavior:

1. Guard `main_window` and the current `graph_edit` exactly as the sibling
   handlers do (`main_window not ready` / `no active graph tab`).
2. Read the command's `data` field (a JSON string carrying the graph).
3. Parse it with `MMLoader.string_to_dict_tree(data)`, NOT a raw
   `JSON.parse`. `string_to_dict_tree` runs `replace_arrays_with_multiline_strings`,
   which converts a Material-Maker-native save's array-of-lines shader fields
   (`code`/`global`/`template`/...) back into the `\n`-joined strings
   `create_gen`/`deserialize` expects. It is a targeted no-op on data that is
   already in string form (our Python-saved cookbook graphs and anything
   `get_graph`/`serialize()` returns), so it is safe for every input and only
   load-bearing for the path-convenience case (an MM-UI-saved `.ptex`). Reject an
   empty/`{}` parse result as `"load_graph: could not parse graph data"`.
4. `var gen = await mm_loader.create_gen(data_dict)`. If `gen == null`, return
   `{"ok": false, "error": "Material Maker could not build a generator from the graph"}`.
5. `graph_edit.set_new_generator(gen)` to replace the current tab's generator in
   place. This is the same call `graph_edit.load_from_data`/`load_file` make after
   building the generator; calling it directly is what avoids
   `do_load_material_from_data`'s `create_new_graph_edit_if_needed()`, which opens
   a fresh tab whenever the current tab already holds a real material (verified in
   `main_window.gd:820-850`). In place, no tab pileup across repeated picks.
6. Do NOT call `set_save_path` with a real path (that is `load_from_data`'s one
   side effect we are deliberately dropping): leaving the tab's save path unset,
   or set to a synthetic non-path label, means a person's stray Ctrl+S in the
   window cannot silently overwrite a tracked cookbook `.ptex`. If a save path is
   wanted for the window title, use a synthetic label like `"live_load"`, never a
   filesystem path into the repo.
7. Re-confirm `_has_active_graph()` before returning `{"ok": true}`; if it is
   false after the load, return an error naming that the load did not settle.
8. Optionally reuse `_show_transient_notice("Claude loaded a graph")` so a person
   watching the window sees why it changed, matching `clear_graph`.

Traps handled, each recorded here so a later "simplification" does not reintroduce
them:

- **Un-awaited coroutine.** `create_gen` awaits `deserialize` internally, so it is
  a coroutine; it MUST be `await`ed in the handler (and `_dispatch` must `await`
  the handler), the same class of bug that hit `_cmd_render`'s `export_material`
  and that `_cmd_clear_graph`'s comment memorializes. Material Maker's own
  `do_load_material_from_data` does NOT await `load_from_data` (`main_window.gd:847`),
  so "MM does it this way" is not a safe guide here; we assert completion via the
  return value and the `has_graph` re-probe rather than trusting the await alone.
- **`.mmcr` rescue dialog.** `graph_edit.load_file` pops a blocking `AcceptDialog`
  when a `.ptex.mmcr` recovery file exists (`graph_edit.gd:785`), which would hang
  the socket on a human at the keyboard. `set_new_generator(create_gen(...))`
  bypasses `load_file` entirely, so it never triggers. Do not "simplify" this to
  `load_file`.

### 2. Client method `live.load_graph` (`live.py`)

```
def load_graph(graph=None, path=None, *, cfg=None, timeout=30.0) -> LiveResult
```

- Exactly one of `graph` / `path` is required. Zero or both is a data error
  (`LiveResult(ok=False, error="load_graph requires exactly one of graph= or path=")`),
  returned, never raised.
- `path` branch: resolve and bound the path through `paths.py`
  (`reject_path_fragment` first, which RAISES on a traversal fragment, so it is
  called for effect, not truthiness, the exact misuse the play-surface plan
  corrected once; then `ensure_within_roots` when `cfg.allowed_roots` is set),
  read the file, `json.loads` it. A read/parse failure is returned as a data
  error.
- Both branches then validate the resulting dict against the catalog with the
  same `validate_graph` every other mutating client call uses; validation errors
  are returned as data, before the socket is ever touched.
- `json.dumps` the (validated) dict and send `{"cmd": "load_graph", "data": <string>}`
  via the existing `_send_command`. Return its `LiveResult`.
- Timeout defaults to 30s (a load compiles shaders, like the mutating ops), not
  the 5s read-only default, consistent with the finding-7 fix already applied to
  the mutation ops.

### 3. MCP tool `live_load` (`server.py`)

```
@mcp.tool()
def live_load(graph: dict | None = None, path: str | None = None) -> dict
```

- Resolves the config and session through the shared `_ensure_live_session(cfg)`
  helper (calls `connect_or_launch` fresh, cheap when already up), exactly like
  the other five live tools. Do not read `server._live_session` directly.
- Delegates to `live.load_graph(graph=graph, path=path, cfg=cfg)` and returns the
  `LiveResult` as the tool's dict result.
- Docstring states: replaces the graph shown in the running session in place;
  accepts a graph dict (primary) or a `.ptex` path (convenience); validates before
  loading; does not save. Notes the Claude Code restart requirement for the tool
  to appear, matching every other live tool.

### 4. Play-surface wiring (`play/renderer.py`)

`render_material` currently, when a live session answers `ping` with `has_graph`,
calls `_try_live`, which applies each slider change via `set_param` and renders.
The change:

- Thread the picked material's id and graph into the render path (the caller in
  `api.py` already has both; pass `material_id` and the material `graph` dict into
  `render_material`).
- Add module state: the id of the material this surface last successfully pushed
  live (`_last_pushed_id`, guarded by the same `_RENDER_LOCK`).
- Inside the lock, before applying slider changes on the live path: if
  `material_id != _last_pushed_id`, call `live.load_graph(graph=<picked graph>,
  cfg=cfg)`. On success, set `_last_pushed_id = material_id`. On failure, leave it
  unchanged and fall through to headless (return `None` from the live helper, the
  existing signal).
- The load happens INSIDE `_RENDER_LOCK`, because a load is a Godot-touching
  operation and must not interleave with an in-flight render (the
  render-orphan-contention rule). `_last_pushed_id` is only ever read/written
  under that lock.
- Injectable seam for tests: `render_material` takes `live_load=live.load_graph`
  as a keyword default, matching the existing `ping`/`live_set_param`/`live_render`
  injection, so the load-on-pick-change logic is unit-testable with a fake.

Known limitation (recorded, v1 accepts it): `_last_pushed_id` is this surface's
belief about what is loaded live. If a person manually switches tabs or opens a
file in Material Maker by hand, the belief goes stale. The next render then skips
the reload (id unchanged), `set_param` fails on nodes that are not in the
hand-loaded graph, `_try_live` returns `None`, and the request falls through to
the existing headless path, which is correct output, just not driven live. v1
does not re-verify the live graph every render to close this; the fallback is
already safe and re-verifying would cost a `get_graph` round trip per render.

## Data flow

- `live_load(graph)`: dict -> validate -> `json.dumps` -> socket -> addon
  `string_to_dict_tree` -> `create_gen` -> `set_new_generator`.
- `live_load(path)`: path -> guard -> read -> `json.loads` -> validate ->
  `json.dumps` -> (same as above).
- Play surface: pick material X while Y is live -> `render_material(material_id=X,
  graph=Xgraph, ...)` -> under lock, `X != _last_pushed_id` -> `live.load_graph(
  graph=Xgraph)` -> `set_param` per slider change -> `live.render` -> copy maps
  into the served dir (unchanged).

## Error handling

- Every failure is data, never a raised exception across the tool/client boundary:
  wrong argument count, path guard rejection (the raise from `reject_path_fragment`
  is caught at the client boundary and returned as data), file read/parse failure,
  catalog validation failure, socket error, and the addon's own parse/`create_gen`/
  `has_graph` failures.
- A failed load on the play-surface path is non-fatal: it returns the headless
  render, so a person never sees a broken surface, only a non-live render.

## Testing strategy

- `live.load_graph` unit tests (`tests/test_live.py`), socket faked:
  - dict input: validated dict is what gets sent; a bad dict is rejected by
    `validate_graph` before the socket.
  - path input: a good `.ptex` is read, parsed, validated, sent; a missing file
    and a malformed file are each returned as a data error; a traversal fragment
    is rejected (the `reject_path_fragment` raise surfaces as a data error, not an
    uncaught exception).
  - argument guard: zero and both of `graph`/`path` are data errors.
- One integration test (`@pytest.mark.integration`, `tests/test_live.py` or
  `test_server_live.py`): launch a real Material Maker, `live_load` a cookbook
  material by dict, then `live_get_graph` and assert the returned graph's node set
  matches the loaded material (the round-trip that proves the shape contract and
  the in-place replace). A second assertion loads a different material and confirms
  the tab count did not grow (no pileup), if cheaply observable; otherwise the
  node-set swap is sufficient proof of in-place replace.
- `live_load` MCP tool test (`tests/test_server_live.py`), `_ensure_live_session`
  faked: delegates to `live.load_graph` with the right arguments and passes its
  result through.
- `play/renderer.py` unit test: with a faked `live.load_graph` and a faked
  `ping`/`set_param`/`render`, a render for a new `material_id` triggers exactly
  one `load_graph`; a second render for the same id triggers none; a render for a
  changed id triggers one more; a `load_graph` failure falls through to headless.
- Fast suite (`pytest -q -m "not integration"`) stays green; the integration test
  runs under the full suite only.

## Rollout / docs

- STATUS.md: update the live-control component row (`live_load` is the seventh
  live tool, after `live_start`/`live_get_graph`/`live_apply`/`live_render`/
  `live_clear`/`live_render_node_output`) and mark backlog item J closed.
- README: add `live_load` to the live-tools list and the two-audience note.
- HANDOFF.md: new "Changed this session" write-up and session-log entry.
- No new config, no new dependency, no packaging change (the addon ships in the
  overlay build already; `live_load` is one more command in the existing file).
- Claude Code restart is required for the new MCP tool to appear in an
  already-running session, the standard requirement for every live tool.

## Success criteria

- `live_load(graph=<a cookbook material dict>)` against a running Material Maker
  replaces the shown graph in place, and `live_get_graph` returns the loaded
  material (round-trip proven by the integration test).
- Loading a second material does not add a tab.
- A malformed graph, a bad path, and a wrong argument count each come back as a
  data error, not a raised exception or a hung socket.
- In the play surface, picking a material while a different one is live pushes the
  pick into the session (the person sees it switch), and subsequent slider tweaks
  drive it live; a manual tab switch degrades safely to headless.
- Fast suite stays green; the one integration test renders/round-trips for real.
- Backlog item J is closed.
