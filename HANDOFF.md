# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-06 (teardown #5 executed: MCP user-wide, crate into the Unity sandbox, kit-map layer, role-named cookbook) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

`main` at the merge `dbf66fc` (+ the docs commit that lands this file), pushed.
Fast suite **964 passed**, 25 integration deselected. `python -m
quality.promote_cookbook --check` in sync; `python -m quality.naming --cookbook`
reports 53 graphs, 0 problems.

This session ran `pickup` + a fifth `teardown` with a usage angle (are we
using the tool, from where, for what), then executed all three of Grayson's
picks the same day:

- **Teardown #5 (report delivered as a file).** Headline: in 48 sessions the
  MCP authoring path (`validate`, `render_graph`, `save_graph`) had zero
  calls; all 53 cookbook materials came from `quality/` builders; the server
  was registered only in this repo's `.mcp.json`, so no other project could
  call it; five portfolio consumers need PBR maps and none had received any
  (gProdDevKit's kit map had no texture layer). Grayson's one hand-edit was a
  rename pass; the cookbook was 66% auto-named. Verdict on the teardown
  cadence itself: **moratorium until three use-sessions exist.**
- **Pick 1, reachability + MCP-only authoring.** `material-maker` is now a
  USER-scope MCP server (`claude mcp add --scope user`, absolute `MM_*`
  env); verified connected from `_UnityQA-Sandbox` and exercised by a
  headless `claude -p` run from that folder. A crate material was authored
  over the MCP tools only (`load_example` w03 -> edit -> `validate` ->
  `render_graph` -> `render_preview` -> `render_graph target="Unity/URP"` ->
  `save_graph`): `saved_graphs/crate_pine_mcp_authored.ptex` (tracked, the
  first shipped graph built that way and the naming-convention reference).
  Its Unity export sits in `_UnityQA-Sandbox/Assets/Materials/CratePine/`
  under UnityQA's `T_` naming with `.meta` guids, and `SM_Crate_A.prefab`
  points at it (uncommitted there; not yet opened in Unity).
- **Pick 2, gProdDevKit.** `KIT_MAP.md` gained layer `4b Texture / Material`,
  a member row, decision D-KIT-9, a section 6 note; `kit-hub/web/tools.json`
  has a `materialmaker` entry; README table row. `Test-Tools.ps1` green.
  Committed locally in that repo, not pushed.
- **Pick 3, role-named nodes (branch `role-named-nodes`, 24 commits, merged
  `--no-ff` as `dbf66fc`).** `rename_nodes(graph, mapping)` in
  `author_helpers.py` (recursive over subgraphs, validates before mutating,
  refuses reserved names, sibling collisions, duplicate targets, and any
  `type == "graph"` node so `mm-play` slider ids stay stable);
  `quality/naming.py` checker (`python -m quality.naming --cookbook [cat]`);
  `quality/render_tracked.py` (renders tracked graphs, compares every map
  the baseline holds, resolves paths absolute); promote writes a generated
  `## Nodes` table into every card between `<!-- nodes:begin/end -->`
  markers and `--check` verifies it; every builder ends with
  `rename_nodes`; all 53 graphs renamed with a per-category render-identical
  proof and, at final review, a structural diff proving only
  name/from/to/linked_widgets changed; gates
  `tests/test_cookbook_naming_gate.py` and
  `tests/test_cookbook_card_table_gate.py`; the "Name every node by role"
  lever in `docs/AUTHORING.md`. Built with `writing-plans` ->
  `subagent-driven-development` (12 tasks, 5 fix rounds, final opus review
  "with fixes", one fix wave, re-review clean).

Bug found by walking the MCP path, not fixed: `validate` checks only
top-level nodes and connections; a dangling connection inside a subgraph
passes silently (`src/mm_mcp/validator.py`).

## 📌 Where we stopped

Everything above is merged and pushed. Grayson's part of pick 1 has not
happened: open the sandbox in Unity, and edit the crate `.ptex` in Material
Maker. Nothing is in flight.

## ▶️ Next concrete step

1. **Grayson: close the loop by hand.** Open `_UnityQA-Sandbox` in Unity and
   confirm `SM_Crate_A` shows the crate material. Then open
   `saved_graphs/crate_pine_mcp_authored.ptex` in Material Maker, edit it,
   save as `saved_graphs/crate_pine_grayson_edit.ptex`, note what was hard to
   read. This is use-session one of the three the moratorium asks for.
2. **`validate` should descend into subgraphs** (errors as data for inner
   connections and unknown inner types). Small, testable, found by dogfooding.
3. **`backup-ops`: the 2026-09-05 nightly abort** is still unexamined.
4. **Unreal UE5 export** (backlogged: memory pressure with a live Unreal
   Editor + bridge; run a `stop-node-hogs` sweep first).
5. More cookbook materials only after a consumer project asks for one.

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
- **Every Claude Code session on this machine now spawns its own `mm-mcp.exe`**
  (user-scope registration); 13 launcher chains (26 python processes) were
  alive at once on 2026-09-06, one per live `claude.exe`, none orphaned.
  Killing one only disconnects that session's MCP; check `claude.exe` parents
  before sweeping.
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
- **A second Claude session may be active on this checkout** (it committed to
  the feature branch and to `origin/main` on 2026-09-06). Check `git status`
  and `git fetch` before branch switches and merges.

## 🕓 Session log

Newest first. Keep at most 8 entries; older ones are in `git log` (search the
commit subjects, every session ends with a `docs:` wrap-up commit).

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
### 2026-09-04 (play-surface UI nits): slider panel docks; canvas re-fills on resize (`c7e85ee`).
### 2026-09-04 (play.bat + play-surface verified): one-click launcher; "MM for dummies" arc closed.
