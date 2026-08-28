# Live-Control Addon — Design Spec (Phase 5)

- **Date:** 2026-08-26
- **Status:** Approved; both feasibility risks retired via spike (2026-08-26,
  see "Known risks" below). Ready for gated implementation (step 1 = `overlay.py`).
- **Author:** Claude (Sonnet 5) with Grayson Chalmers
- **Classification:** Architectural (new subsystem)
- **Relationship to prior spec:** extends
  [2026-08-25-material-maker-mcp-design.md](2026-08-25-material-maker-mcp-design.md),
  which sketched Phase 5 as "a GDScript plugin inside a forked Material Maker."
  This spec replaces "forked" with an additive, disposable overlay (see
  Architecture) after brainstorming surfaced that a real fork was unwanted.

## Goal

Let Grayson open Material Maker's GUI and collaborate with Claude on a
material live: Claude can see whatever graph is currently on the active tab,
propose and apply changes that appear in the running window immediately, and
trigger a render, all without Grayson copying files back and forth. Turn-based,
not simultaneous: Claude acts, Grayson looks and reacts, back and forth.

This is explicitly a **later, deferred phase**. The existing batch pipeline
(Phases 0-3, verified 15/15 usable-hit-rate) already covers the "just make me
a texture, headless, no GUI" use case and is unaffected by this work. Live
control is a second, additive interaction mode for when the GUI is open.

"Done" for this phase: Grayson has Material Maker open, asks Claude to build
or tweak a material, and watches nodes appear and connect in the live window
as Claude works, then asks for a render and sees the preview update in place.

## Scope decisions (from brainstorming)

- **No source fork.** Grayson explicitly rejected maintaining a diverging copy
  of Material Maker's codebase. The `z-Git\material-maker` checkout stays the
  pristine upstream reference, untouched, forever.
- **Addon, not core modification.** The live-control code is a self-contained
  Godot addon, the same additive mechanism Material Maker's own
  `addons/material_maker` uses, not a patch to existing Material Maker files.
- **Turn-based collaboration, not real-time sync.** Grayson accepted giving up
  true simultaneous editing for v1. No conflict resolution is designed for
  concurrent writes from both sides at once.
- **Single active tab.** Live tools always operate on whatever graph is
  currently focused in the GUI. No multi-tab addressing.
- **Claude can launch Material Maker.** If nothing is listening on the known
  port, a live tool call launches it rather than erroring out.
- **Zero manual sync, for Grayson and for anyone else who clones this repo.**
  The addon ships inside this repo's git history. A build step keeps a
  disposable working copy in sync with both the addon and the pristine
  checkout automatically, so nobody ever hand-copies files.

## Architecture

Three new pieces sit alongside the existing four Phase 1-3 units
(`catalog_builder.py`, `graph.py`, `render.py`, `server.py`), reusing
`graph.py`'s `validate_graph` rather than duplicating it:

1. **Addon** (`live_addon/`, GDScript) — versioned in this repo. Runs inside
   the live Material Maker process once loaded; exposes a local socket server.
2. **Overlay builder** (`overlay.py`, Python) — produces and refreshes a
   disposable working copy of the Material Maker project: the pristine
   checkout plus the addon plus one autoload line in `project.godot`. Rebuilt
   automatically whenever it's stale, never hand-maintained.
3. **Live session manager** (`live.py`, Python) — owns process lifecycle
   (probe the port, rebuild the overlay if stale, launch or attach) and the
   socket client.

### Why an overlay instead of an addon dropped straight into the pristine checkout

Godot's addon-loading mechanism for a *running* project (not the editor)
needs a one-line registration in that project's `project.godot`
(`[autoload]` section) so the addon's entry script starts when the project
runs. That's a config edit, not a source-code fork, but it does mean the
directory Material Maker actually runs from can't be the pristine checkout
verbatim. The overlay is that directory: generated, disposable, and
regenerated on demand, so the pristine checkout never needs to change and
there is nothing to keep in sync by hand.

**Staleness check:** the overlay stores a marker file recording a hash of the
addon folder's contents and the pristine checkout's path. Before every launch
or attach attempt, `live.py` compares the marker to current state and
rebuilds the overlay if either has changed. This is what makes updates to the
addon (by Claude, during development, or by a future contributor) show up
automatically, no copy step, for Grayson or for anyone else who clones the
repo.

### Components

- **Addon (GDScript), inside the live process:**
  - Starts a `TCPServer` on a fixed localhost port at project startup (via the
    autoload entry).
  - Handlers, each a small JSON-in/JSON-out command:
    - `get_graph` — serializes the active tab's current `{nodes, connections}`
      in the same shape as a `.ptex`, so Claude can reuse existing
      catalog/validator logic against it unchanged.
    - `add_node`, `connect_nodes`, `set_param` — mutate the live scene
      directly; changes are visible in the GUI immediately because they act
      on the same objects the GUI renders.
    - `render` — invokes Material Maker's own existing preview/export code
      path (not a new render implementation) so live-rendered output matches
      batch-rendered output.
    - `ping` — liveness check used by the session manager's probe.
  - Deliberately thin: no validation logic lives here. It trusts what it's
    given, because everything mutating arrives pre-validated from the Python
    side.

- **Overlay builder (`overlay.py`):**
  - `ensure_overlay(mm_project_path, addon_path) -> overlay_path`: builds or
    refreshes the overlay directory, returns its path. Pure filesystem work,
    unit-testable without Godot.

- **Live session manager (`live.py`):**
  - `LiveSession.connect_or_launch()`: probes the known port; if silent,
    ensures the overlay is current, launches Godot against it, polls for the
    port, connects.
  - Client methods mirroring the addon's commands: `get_graph()`,
    `add_node(...)`, `connect_nodes(...)`, `set_param(...)`, `render(...)`.
  - Every mutating call runs the op through `graph.py`'s `validate_graph`
    first (against the current live graph state, fetched via `get_graph`)
    and returns validator problems as data, exactly like the batch path,
    before anything is sent over the socket.

- **New MCP tools (`server.py`):**
  - `live_start()` — connect-or-launch, returns session status.
  - `live_get_graph()` — current active-tab graph as `.ptex`-shaped JSON.
  - `live_apply(ops)` — validated batch of mutations.
  - `live_render()` — trigger a render, return image paths, same
    `RenderResult` shape the batch tools already use.

### Data flow

Grayson opens Material Maker himself, or asks Claude to (`live_start`). Claude
calls `live_get_graph` to see what's actually on screen. Claude reasons about
it using the existing catalog, proposes edits, validates them locally against
the fetched state, and sends validated ops through `live_apply`; the addon
applies them to the live scene and the GUI updates in place. Claude calls
`live_render` to trigger a preview the same way the app's own UI would.
Turn-based: Claude acts, Grayson looks and reacts, next turn.

## Error handling

- **No concurrency conflict resolution in v1.** The model is turn-based by
  design (see Scope decisions), so simultaneous edits from both sides aren't
  designed for. The addon always reflects whatever the scene tree currently
  holds when asked; there is no "the user changed something mid-operation"
  detection.
- **Socket errors are explicit, never a silent hang.** Connection refused,
  dropped mid-command, or timeout all surface as a clear MCP error naming the
  failure and suggesting reconnect-or-relaunch, mirroring `render.py`'s
  existing "never silently succeed" philosophy.
- **Stale overlay is self-healing.** Detected and rebuilt automatically
  before every connect-or-launch attempt (see Staleness check above); it is
  never a state a caller has to notice or fix manually.
- **Mutations referencing stale state** (e.g. a node id the user already
  deleted in the GUI) return a structured problem from the addon, same shape
  as `validate_graph`'s `Problem` objects, not a raw exception.

## Testing

- **`overlay.py`:** unit tests against a fake pristine-checkout directory and
  a fake addon directory; no Godot needed. Covers first-build, no-op on
  unchanged inputs, rebuild-on-addon-change, rebuild-on-checkout-change.
- **Socket protocol (`live.py`):** unit tests against a fake local TCP
  server standing in for the addon, covering the command/response shapes and
  the validate-before-send behavior, no real Godot needed.
- **Addon + integration:** a Godot-launching integration test in the same
  style as the existing `tests/test_render.py` integration case (skippable
  via `-m "not integration"`): launch the overlay project for real, connect,
  `get_graph` on a known bundled example, `add_node`, `render`, assert a PNG
  appears and the graph reflects the added node on a follow-up `get_graph`.

## Distribution and docs

- The addon folder is committed to this repo; nobody downloads it separately.
- The only manual setup step for a new clone remains what Phase 4 already
  documented: clone `material-maker` upstream, point `MM_PROJECT_PATH` at it.
  Live mode needs no addon-specific install step; the overlay builds itself
  on first use of any `live_*` tool.
- README gets a short "Live mode" section once this phase is implemented,
  covering what it is, that it's optional, and that batch mode remains the
  default/simpler path.

## Phases and gates (this sub-plan)

Sketch only, to be broken into real gated steps by `writing-plans` when this
phase is picked up for implementation:

1. **Overlay builder** — `ensure_overlay` builds and detects staleness
   correctly. *Gate: unit tests green, manual inspection of a built overlay
   directory shows the autoload line present and addon files copied.*
2. **Addon skeleton** — socket server + `ping`/`get_graph` only. *Gate:
   Python connects, launches Material Maker via the overlay, gets a real
   graph back for a bundled example.*
3. **Mutating commands** — `add_node`/`connect_nodes`/`set_param`/`render`.
   *Gate: a scripted sequence of live ops visibly builds a simple graph in a
   real running window and renders it.*
4. **MCP tool surface** — wire `live_start`/`live_get_graph`/`live_apply`/
   `live_render` into `server.py`. *Gate: Claude can hold an actual live
   session against a real open Material Maker window.*

## Feasibility verified (spike, 2026-08-26)

Both risks below were retired by a two-part spike before any implementation.
Throwaway spike code lived in the session scratchpad, not committed; the real
addon/overlay get built via the gated plan above. The verdicts and the
constraints they surfaced:

- **Risk #1 (autoload socket) — PROVEN.** A standalone Godot project with a
  one-line `[autoload]` entry opened a `TCPServer` on project run (not editor),
  and an external Python client connected and exchanged JSON line commands
  (`ping`/`get_graph`/`quit`). Confirmed a second time inside the real MM
  overlay below.
- **Risk #2 (in-process mutation surface) — RETIRED.** Material Maker exposes a
  GUI-grade API that mirrors the batch `.ptex` shape, reached from the addon
  via the `mm_globals` autoload:
  - `mm_globals.main_window.get_current_graph_edit()` — active tab's
    `MMGraphEdit` (the singleton node is at `/root/mm_globals`; `console.gd:63`
    uses this exact path at runtime).
  - `graph_edit.create_nodes({nodes, connections}, pos)` — add (takes the
    `.ptex` node-dict shape directly; also accepts a single `{type, parameters}`).
  - `graph_edit.do_connect_node(from, from_slot, to, to_slot)` — wire.
  - `graph_edit.set_node_parameters(node, params)` — set params.
  - `graph_edit.generator.serialize()` — read the active graph back out as
    `.ptex`-shaped JSON (the `get_graph` handler; verified end-to-end returning
    the default new-material graph from a live window).
- **Constraints these surfaced (bake into the build):**
  - `create_nodes`/`do_create_nodes` are `await`-based (`await
    mm_loader.add_to_gen_graph(...)`). The addon's command loop must be a
    coroutine that awaits the result before writing the socket response, or it
    replies with a coroutine-state object instead of the array. (`get_graph` via
    `serialize()` is synchronous; the write handlers are not.)
  - `mm_globals.main_window` is **null at autoload `_ready()`** (autoloads start
    before the main scene). Resolve it lazily per command, never cache at boot.
    The session manager's readiness probe should poll `ping` until
    `main_window` is wired before issuing graph commands.
  - **Amendment (2026-08-27, found during Phase 5 step 4's manual
    verification, fixed by `docs/superpowers/plans/
    2026-08-27-connect-or-launch-readiness-race.md`):** `main_window`
    resolving does NOT mean a graph tab exists yet -- the default
    new-material graph tab is created in a later boot step. `ping` reports
    this separately as `has_graph`; `connect_or_launch` must poll until
    BOTH `ready` and `has_graph` are true, not `ready` alone, or the first
    mutating call can race ahead of tab creation and fail with `"no active
    graph"`.
  - **Amendment (2026-08-27, found during the same task's whole-branch
    final review):** requiring `has_graph` introduced its own failure mode
    on the "attach to an already-listening instance" path -- if that
    instance answers `ping` and even reports `ready` (main_window resolved)
    but never reports `has_graph`, the naive fix would hang for the full
    `launch_timeout` (60s, on every `live_*` MCP tool call) and then report
    a misleading "timed out waiting for the live server to become ready"
    about a process that's actually running fine. `connect_or_launch` now
    fails fast, within the existing grace period (`_SQUATTED_PORT_GRACE`),
    with a diagnosis that names the instance as responsive rather than
    dead, when this happens. The two real-world triggers this guards
    against: (1) a pre-upgrade `mm_live` addon that predates the
    `has_graph` field entirely and so never sends it, and (2) a genuinely
    tab-less instance (main_window up, no material/graph tab open). Both
    point at the same recovery: close the stale/tab-less instance and let
    `connect_or_launch` launch a fresh one carrying the current addon, or
    open a graph tab and retry.
  - The overlay **must** carry `steam_appid.txt` (`4110830`) or MM
    self-relaunches and exits (the CLAUDE.md gotcha). `overlay.py` copies it.
  - Autoload line `overlay.py` appends to the `[autoload]` section:
    `mm_live="*res://addons/mm_live/live_server.gd"`.
  - `live.py` must **not** `PIPE` the launched Godot's stdout without draining
    it; redirect to a file or DEVNULL. An undrained pipe fills and blocks the
    child (this faked a failure during the spike until spotted).

## Still-open / deferred risks

- **The `render` handler is unverified.** "Invoke Material Maker's own existing
  preview/export code path" (not a new render impl) is still an assumption, a
  step-3 concern, not yet checked against source.
- **Live-scene mutation proven to exist, not yet exercised live.** The write
  API above is confirmed present in source; the spike only exercised the read
  path (`get_graph`) end-to-end. Actually adding/wiring/param-setting a node in
  a running window is build step 3's gate.
- **Windows-only, like the rest of this project** (see STATUS.md Phase 4).
  No new cross-platform risk introduced here beyond what already exists.
- **Deferred, not scheduled.** Per Grayson's call in brainstorming, this
  phase has no target date. This spec exists so the design is ready whenever
  it's picked up, not to commit to building it now.
