# Idle-exit watchdog: implementation report

## Files changed

- `src/mm_mcp/idle.py` (new) — `IdleWatchdog` class per spec: fake-clock-testable,
  `touch()`/`idle_seconds()`/`expired()`/`check()`/`start()`, `_default_exit` prints
  to stderr and calls `os._exit(0)`.
- `tests/test_idle.py` (new) — 6 tests: before/at/after timeout, touch() reset,
  ValueError on non-positive timeout, start() twice keeps one thread (poll_s=0.01,
  clock that never expires, no sleeping, no default-exit path triggered).
- `src/mm_mcp/config.py` — added `MM_IDLE_EXIT_MINUTES` default `"0"`,
  `Config.idle_exit_minutes: int = 0`, `_parse_idle_exit_minutes()` helper raising
  `ValueError("MM_IDLE_EXIT_MINUTES must be a non-negative integer, got ...")` for
  non-integer or negative values, wired into `load_config`.
- `tests/test_config.py` — 4 new tests: default 0, reads env, rejects "abc", rejects "-5".
- `src/mm_mcp/server.py` — imports `IdleWatchdog`; module-level `_idle = None`;
  `_touch_idle()` no-ops when `_idle is None`; `_ensure_ready()` now calls
  `_touch_idle()` unconditionally on every call (not just first materialization).
  Verified all 17 tools (`list_node_types`, `describe_node`, `validate`,
  `render_graph`, `render_node_output`, `render_preview`, `save_graph`,
  `list_examples`, `load_example`, `inspect_project`, `live_start`,
  `live_get_graph`, `live_apply`, `live_render`, `live_render_node_output`,
  `live_clear`, `live_load`) call `_ensure_ready()` directly as their first line,
  so no per-tool edits were needed. `main()` starts the watchdog (`cfg.idle_exit_minutes
  * 60` seconds) and prints a stderr notice when `idle_exit_minutes > 0`, right
  before `mcp.run()`.
- `tests/test_server_idle.py` (new) — 3 tests: `_ensure_ready()` touches a fake
  idle object; `main([])` with `idle_exit_minutes=0` leaves `server._idle is None`;
  with `idle_exit_minutes=2` sets `server._idle` to an `IdleWatchdog` with
  `_timeout == 120` (`IdleWatchdog.start` monkeypatched to a no-op, `mcp.run`
  monkeypatched to a no-op). Autouse fixture resets `server._idle = None`
  before/after each test.
- `.env.example` — commented `MM_IDLE_EXIT_MINUTES=` entry with explanation.
- `README.md` — new paragraph in "Connect it to an MCP client" explaining the
  opt-in trade-off, and `"MM_IDLE_EXIT_MINUTES": "120"` added to the JSON example.

## TDD evidence

RED (idle.py absent):
```
$ python -m pytest tests/test_idle.py -q
ModuleNotFoundError: No module named 'mm_mcp.idle'
```
GREEN: `6 passed in 0.08s`

RED (config.py not yet touched):
```
$ python -m pytest tests/test_config.py -q -k idle_exit
4 failed - AttributeError: 'Config' object has no attribute 'idle_exit_minutes' (x2)
           Failed: DID NOT RAISE ValueError (x2)
```
GREEN: `21 passed in 0.10s` (full test_config.py)

RED (server.py not yet touched):
```
$ python -m pytest tests/test_server_idle.py -q
2 failed, 1 passed
  test_ensure_ready_touches_idle_watchdog: assert [] == [True]
  test_main_starts_idle_watchdog_when_enabled: assert False == isinstance(None, IdleWatchdog)
```
GREEN: `3 passed in 1.37s`

Combined check: `test_server_tools.py + test_config.py + test_idle.py + test_server_idle.py`
= `63 passed in 12.16s`

## Full suite

```
python -m pytest -q -m "not integration"
981 passed, 25 deselected in 57.45s
```

`tests/test_readme_counts.py` also re-run standalone after the README edit: `5 passed`.

## Commits (on branch idle-exit, not pushed/merged)

- `5557965` feat(idle): add IdleWatchdog for opt-in stdio server idle-exit
- `ff23a81` feat(server): wire idle-exit watchdog behind MM_IDLE_EXIT_MINUTES
- `46c22f3` docs: document MM_IDLE_EXIT_MINUTES opt-in idle exit

## Concerns

- No test exercises the real default-exit path (`os._exit(0)`) or a live thread
  actually calling it — by design, per the instructions ("No test may trigger the
  default exit"). That path is a one-line print + `os._exit`, low risk, but is
  the one bit of behavior that only a hands-on run of `mm-mcp` with
  `MM_IDLE_EXIT_MINUTES=1` (or similar) would confirm end to end. Not done here
  (out of scope: "do not launch Godot" / no live server run required by the task).
- `_touch_idle()` fires on every `_ensure_ready()` call, including the very first
  one at server startup before `main()` has created `_idle` — harmless since
  `_idle` is `None` at that point, but worth knowing the touch is unconditional,
  not gated on the watchdog existing yet (that's what makes it a no-op-safe design).

## Fix round 1

Two review findings fixed on top of the original implementation.

### Finding 1 (Critical): `save_graph` and `inspect_project` never touched the watchdog

Both called `load_config()` directly, bypassing `_ensure_ready()` (and its
`_touch_idle()` call). Fixed by adding `_touch_idle()` as the first line of
each function in `src/mm_mcp/server.py`.

Replaced the old single-fake-tool touch test in `tests/test_server_idle.py`
with a comprehensive one that iterates every registered tool. Coverage is
pinned to an explicit list of **17 tool names** matching all 17
`mcp.tool()(...)` registrations at the bottom of `server.py`; a companion
test (`test_tool_registration_count_matches_covered_list`) counts
`mcp.tool()(` occurrences via `inspect.getsource(server)` and asserts it
equals `len(_ALL_TOOL_NAMES)`, so a new tool added later without a matching
test-coverage entry fails loudly instead of silently going untested.

Each tool is called with cheap, fast-failing arguments (invalid node type,
empty ptex, nonexistent example/node/file names) and the heavy callees
(`server._ensure_live_session`, `server.render`, `server._render_preview`)
are monkeypatched to raise a sentinel exception, so nothing launches Godot
or a live socket. A fresh fake idle recorder is installed before each call
and the test asserts it saw at least one touch.

RED (both tools skip the touch; captured before re-applying the fix, via
`git checkout -- src/mm_mcp/server.py` then restoring the edits):
```
$ python -m pytest tests/test_server_idle.py -q
FAILED tests/test_server_idle.py::test_main_starts_idle_watchdog_when_enabled
FAILED tests/test_server_idle.py::test_idle_exit_closes_live_session_before_calling_os_exit
FAILED tests/test_server_idle.py::test_every_registered_tool_touches_idle_watchdog
  AssertionError: tool 'save_graph' did not touch the idle watchdog
3 failed, 3 passed in 2.36s
```
(The other two failures in that RED run are Finding 2's tests, since both
fixes were reverted together for the RED capture.)

GREEN: `12 passed in 1.48s` (`tests/test_server_idle.py tests/test_idle.py`)

### Finding 2 (Important): `os._exit(0)` skipped `atexit`, orphaning a live overlay

Added `_idle_exit(idle_s)` in `src/mm_mcp/server.py`: prints the same-shaped
stderr notice, calls `_close_live_session_atexit()`, then `os._exit(0)`.
`main()` now constructs the watchdog with `on_expire=_idle_exit` instead of
relying on `IdleWatchdog`'s default (which is unchanged and still used when
no `on_expire` is supplied).

New tests:
- `test_idle_exit_closes_live_session_before_calling_os_exit` — monkeypatches
  `server._close_live_session_atexit` and `server.os._exit` with recorders,
  calls `server._idle_exit(7200.0)` directly, asserts call order
  `["close", ("exit", 0)]` and that the captured stderr mentions "min".
- `test_main_starts_idle_watchdog_when_enabled` extended to assert
  `server._idle._on_expire is server._idle_exit`.

### Combined result

```
$ python -m pytest tests/test_server_idle.py tests/test_idle.py -q
12 passed in 1.48s

$ python -m pytest -q -m "not integration"
984 passed, 25 deselected in 48.49s
```

(984 vs the prior round's 981: +3 new tests in `test_server_idle.py`.)

**Exact tool count covered: 17** — matches the 17 `mcp.tool()(...)`
registrations in `src/mm_mcp/server.py`.
