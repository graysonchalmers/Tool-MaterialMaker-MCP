# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-06 (idle-exit watchdog shipped; validate() descends into subgraphs; crate round-trip prep) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

`main` at `ebba5b6` plus the idle-exit merge `f669f8c` and this docs commit, pushed, in sync (0/0). Two sessions ran on this checkout in parallel today; this file merges both. Fast suite **993 passed, 1
flaked** (the one flake was `test_live.py::test_load_graph_round_trips_a_cookbook_material`,
a live-overlay test that collided with a concurrent Godot render; it passes
in 25 s on its own and its material validates with 0 errors under the new
code). `promote_cookbook --check` and `naming --cookbook` untouched this
session.

Short `pickup` + do-it session. Grayson picked two of the five surfaced
moves and both landed:

- **Pick 2 (option 2 in the pickup list): `validate` now descends into
  subgraphs.** TDD: five subgraph-descent tests written failing first
  (clean nested case, dangling inner connection, unknown inner type, inner
  port out of range, doubly-nested), then `validate_graph` made to recurse
  into `graph`-typed nodes, prefixing inner problems' `where` with the
  subgraph path (e.g. `sub/deep`) so they stay locatable.
  `tests/test_validator.py` 19/19. Commit `577592f`, pushed. This closes the
  "found by dogfooding, not fixed" bug from the prior session.
- **Pick 1 prep (option 1): crate round-trip readied for Grayson's hands-on
  half.** The Unity side was verified from disk (no Unity launch needed):
  `SM_Crate_A.prefab` points at `M_Crate_Pine.mat` on both slots, and that
  .mat references all three `T_Crate_Pine_*` textures by matching guids. A
  3D starting-point preview of `saved_graphs/crate_pine_mcp_authored.ptex`
  was rendered and sent to Grayson (session scratchpad only, not tracked).
  The hand-edit itself is deliberately left to him: it is the experiment the
  moratorium wants.
- **Idle-exit watchdog (other session, merge `f669f8c`, suite 989).**
  `MM_IDLE_EXIT_MINUTES` (default 0 = off) makes the stdio server exit after
  that many minutes without a tool call: `src/mm_mcp/idle.py`, every one of
  the 17 tools touches it (a test pins the count against the registrations),
  and the exit path closes any live Material Maker session before
  `os._exit(0)`. Grayson's user-scope registration and this repo's `.mcp.json`
  carry `120`. Built in a git worktree because this checkout was mid-edit;
  worktree removed. Thirteen stale per-session servers were killed by hand.

## 📌 Where we stopped

Both picks done and pushed. Grayson's hands-on half of pick 1 (use-session
one of the moratorium's three) has NOT happened. Nothing is in flight.

## ▶️ Next concrete step

1. **Grayson: close the loop by hand.** Open `_UnityQA-Sandbox` in Unity and
   confirm `SM_Crate_A` shows the crate material. Then open
   `saved_graphs/crate_pine_mcp_authored.ptex` in Material Maker, edit it,
   save as `saved_graphs/crate_pine_grayson_edit.ptex`, note what was hard to
   read. This is use-session one of the three the moratorium asks for.
2. **`backup-ops`: the 2026-09-05 nightly abort** is still unexamined.
3. **Unreal UE5 export** (backlogged: memory pressure with a live Unreal
   Editor + bridge; run a `stop-node-hogs` sweep first).
4. More cookbook materials only after a consumer project asks for one.
5. Optional: note in README/AUTHORING that `validate` now covers subgraph
   internals (currently only in the validator and its tests).

## ❓ Open questions

- PyPI vs GitHub-clone-only (leaning GitHub-only); macOS/Linux never run.
  release-please will open the next PR on the pushed commits.
- NORTH_STAR treats UE4's export path as a lesser tier; never confirmed.
- `.mcp.json` question resolved in practice: user-scope registration is the
  wiring; `.mcp.json` stays for this repo's own dev sessions. Whether
  `project-setup` should register MCP servers user-wide is open.
- Two parked overlay-builder findings (2026-08-28): no rollback if `copytree`
  fails partway; staleness check hashes only the addon.
- README's "10 batch-mode tools" is the one count not test-enforced.
- `m01_weathered_copper` ships without a normal map (content gap surfaced by
  the render baseline).

## ⚠️ Heads-up for the next agent

- **The 2026-09-05 nightly backup aborted** (`backup-ops\logs\Backup-All_2026-09-05_210003.log`,
  ends at `OK: Skills`, no summary). Plausible cause: a `NativeCommandError`
  from `git diff HEAD --binary` at `Backup.Common.ps1:229`. Needs a
  `backup-ops` session.
- **Run quality scripts as `python -m quality.<module>` from the repo root**
  (`pip install -e .` is a prerequisite; running from inside `quality/`
  breaks `.env` lookup). Never launch a Godot render from `python -c`.
  Renders are one Godot at a time.
- **Pass `render()` an absolute `outdir`.** Godot runs with the Material Maker
  checkout as its cwd, so a relative outdir is never found, Material Maker
  opens its GUI instead, and the render idles to the 180 s timeout with an
  empty log (cost two implementer runs on 2026-09-06).
  `quality/render_tracked.py` resolves its own paths; `src/mm_mcp/render.py`
  still accepts a relative one.
- **Subagents lose long Godot runs.** Run `render_tracked` per category; the
  stone and terrain compares take 6 to 9 minutes because `quality/pngread.py`
  decodes 2048x2048 normal maps in pure Python. Tell implementers to poll the
  output file rather than return. One re-render of an unchanged graph once
  measured 21.89 mean abs diff and 0.0 on two reruns: a single compare
  failure is a rerender first, a regression second.
- **In the Git Bash tool, `taskkill /F` is rewritten to `F:/`.** Use
  `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (and the GUI exe).
- **Every Claude Code session on this machine spawns its own `mm-mcp.exe`**
  (user-scope registration). Since `f669f8c` a server with no tool call for
  `MM_IDLE_EXIT_MINUTES` (120 in Grayson's registration) closes its live
  session and exits on its own. Claude Code does NOT restart an exited stdio
  server: a tab idle for two hours loses its Material Maker tools until it
  reconnects (`/mcp`) or the session restarts. Servers started before the
  change keep running without the timer.
- **Node names never affect renders** (Material Maker seeds from node
  position), so a rename pass is render-identical by construction; add
  materials through a builder that ends with `rename_nodes(g, {...})` after
  grouping, and never rename a subgraph node (`mm-play` slider ids).
- **Edit cookbook materials by changing the builder and re-promoting**, never
  the tracked `.ptex` or the generated card table by hand;
  `promote_cookbook --check` flags both. `--check` compares against the
  gitignored `quality/authored/`, so regenerate the category first. Godot is
  not byte-deterministic: do not regenerate thumbnails for a name-only change.
- **`group_into_subgraph` fails silently on a mistyped member name.**
- **A `blend` shows port-1 where its port-2 mask is 0 and port-0 where it is 1**;
  put the majority layer on port-1. Opacity = amount x mask. `normal_map`
  `param4=0` is the flat-normal fix. Voronoi output port 2 is the per-cell
  random source.
- **Verify metallic/roughness/AO fixes by reading the exported ORM channel**
  (`quality/pngread.py`), not by eye.
- **`take_variant(builder, label, keep_n)`** returns one variant and deletes
  the files it wrote; the caller re-saves as v1.
- **Bumping the Material Maker pin** means `MM_UPSTREAM_PIN` in
  `src/mm_mcp/__init__.py` AND `MM_PIN` in `.github/workflows/test.yml`,
  then the local checkout, then regenerate every category and `--check`.
- **Stale mm-play on 8788 is a startup error with the PID.**
- **The SPIRV `SCRIPT ERROR` at `parse_args.gd:59` prints on every successful
  export.** Red herring.
- **`ambientcg.com` redirected to scareware (2026-09-03).** Use Wikimedia.
- **Donors load from `quality/donors/`** (tracked); vendor new donors there.
- **release-please has `bump-minor-pre-major: true`**; do not remove it.
- **`.mcp.json` and `.env` are gitignored; never echo `.env`.** The user-scope
  registration in `~/.claude.json` carries the same paths.
- **A second Claude session is active on this machine and its `Push-Repo`
  runs `git add -A`.** On 2026-09-06 it swept this session's untracked
  `_agent-commons` log into its own commit (`f94c240`, subject "vibecheck
  s102...") and pushed it. Content is intact, but the log is not findable by
  commit subject: search the commons by filename, not `git log --grep`. It
  also committed a `docs:` correction (`868d16a`) to THIS file. `git fetch`
  and re-read before editing shared files.
- **The user-scope `mm-mcp.exe` runs the INSTALLED package, not the working
  tree.** The `577592f` validator change is live in local pytest but NOT in
  the MCP `validate` tool until a reinstall/restart of that server.

## 🕓 Session log

Newest first. Keep at most 8 entries; older ones are in `git log` (search the
commit subjects, every session ends with a `docs:` wrap-up commit).

### 2026-09-06 (idle-exit watchdog): `MM_IDLE_EXIT_MINUTES` opt-in idle exit, 17/17 tools touch it, live session closed on exit; review found and fixed the two untouched tools and the atexit skip; merged `--no-ff` as `f669f8c`, suite 989; registration set to 120.
### 2026-09-06 (validate subgraph descent + crate round-trip prep)
- `pickup`; Grayson picked options 1 + 2 ("automate most of 1 for me").
- Option 2 TDD: `validate_graph` recurses into subgraph nodes, inner
  problems path-prefixed; 5 new tests; `577592f` pushed. Closes the prior
  session's dogfooding bug.
- Option 1: Unity crate wiring verified from disk; 3D preview rendered and
  sent. Hand-edit left to Grayson (use-session one).
- Full suite 993 passed / 1 flake (live-overlay test, Godot contention;
  passes alone). A concurrent session's `Push-Repo` swept this session's
  commons log into its `f94c240` and pushed it.
### 2026-09-06 (teardown #5 executed): MCP user-wide, crate into the Unity sandbox, kit-map layer 4b, role-named cookbook
- `pickup`, then `teardown` #5 from usage evidence (48 transcripts, MCP
  registration, portfolio survey). Grayson: "1, and do 2 + 3 in the same
  session", then "merge, push, and wrap".
- Pick 1: user-scope registration; crate authored over MCP only; Unity/URP
  export placed in `_UnityQA-Sandbox` (`T_` names, prefab repointed).
  `validate` found not to check subgraph internals.
- Pick 2: gProdDevKit layer 4b, D-KIT-9, tools.json, README (local commit).
- Pick 3 via `writing-plans` -> `subagent-driven-development`: 12 tasks.
  Root cause of two lost implementer runs was the plan's own relative
  `--out` (Godot cwd); compare rewritten to cover every map the baseline
  holds (heightmaps, m01 no normal); per-category compares as the whole-tree
  proof. Final opus review found three ratchets (subgraph-rename guard,
  card-table gate, the HANDOFF heads-up); all landed. Merged `dbf66fc`,
  pushed. Suite 809 -> 964.
### 2026-09-05 (teardown #4 executed): hygiene sweep (CI pinned to the MM sha), `quality/` packaged, Phase-3 harness archived (`6e4568f`, `c5d473c`).
### 2026-09-05 (teardown #3 executed): examples/ folded into the cookbook (46 -> 53), mm-play port diagnostic, backup exclusions, baton diet (`87be578`, `5b93785`); v0.7.0 released.
### 2026-09-05 (mm-play verified): Grayson ran `play.bat` hands-on; row promoted 🔌 -> ✅ (`056dcd4`).
### 2026-09-04 (blocker correction): the "host can't render" blocker was a stale server squatting 8788, not GPU (`b016f1b`).
### 2026-09-04 (live_load): seventh live tool, in-place graph replace; play surface pushes the picked material live (`d523ad6`).
