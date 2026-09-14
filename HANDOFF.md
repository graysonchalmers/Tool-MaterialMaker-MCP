# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-13 (enum out-of-range reclassified to a hard error; reconciled with the sibling branch, merged to `main` and pushed) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

**Closed the deferred enum-validation follow-up: an out-of-range enum INDEX is
now a hard `severity:error`, not a warning. Reconciled with a sibling branch
that fixed the same thing a different way, merged to `main` and pushed.** The
noise/distortion + core-toolbox plan from the prior session was already merged
to `main` (`0169446`) and pushed; the baton had drifted (said "unmerged"), now
corrected.

The follow-up's framing turned out wrong: detection already worked. `validate_graph`
correctly flagged t09's `type=-3` (int) even inside its subgraph. The real hole
was ENFORCEMENT: that finding was a `warning`, and every automated path filters
to errors only (`test_cookbook_gate.py:44`, `render_tracked.py:41`) or never
validates (`promote_cookbook`). So the one class of mistake that produced t09
was a warning no gate caught. Fix (Grayson chose reclassify + better message):
- `validator.py`: out-of-range enum index -> `error` (numeric slider ranges stay
  advisory warnings). The message explains the clamp-to-0 wrong-render and says
  "use the option's INDEX". When the bad value matches a known raw literal,
  `_enum_literal_hint` names the intended index (`type=-3` -> "looks like the
  raw literal for index 4 'Mult 3', use 4"); otherwise it lists every valid
  option by index (folded in from the sibling branch). Range NOT widened.
- `catalog_builder.py`: capture `value_literals` only for enums whose numeric
  literals mismatch their index (wavelet type). Name-literal enums (blend, fbm)
  stay lean. Added `_as_int` helper.
- `test_cookbook_gate.py`: ratchet test injecting a bad enum index into a real
  cookbook graph, asserting the gate's own error collection fails.
- `test_catalog_parse.py`: folded in the sibling's guard pinning wavelet
  min=0/max=4 (do not derive the range from the underlying literals).
- Verified against the real pre-fix t09 graph: now returns the named-index error,
  located to `ripple_color/RippleField`. Fast suite 1045 passed / 31 deselected.

## 📌 Where we stopped

Reconciled fix merged to `main` and pushed. Nothing in flight.

## ▶️ Next concrete step

Nothing required. The sibling branch `claude/zealous-ritchie-cb051a` is now
SUPERSEDED (its good parts, the options-by-index message and the wavelet
range-pin test, were folded into the merged fix); it can be deleted, local and
remote, when convenient. release-please will fold the enum fix into the next
version PR on the pushed commits. Deferred-minor follow-ups still open (none
blocking): the contact-sheet `<img alt>` counts are not test-gated; a few
over-long/stale docstrings noted in the noise-plan ledger.

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

- **An out-of-range enum INDEX is now a hard `error`** (was a warning), so it
  fails `test_cookbook_gate` and makes `render_tracked` SKIP that graph (records
  a problem) instead of rendering-with-warning. Latent only: the cookbook has
  zero out-of-range enums today. `validate` names the intended index when the
  bad value matches a known literal (via the new catalog `value_literals`).
  A string-stored literal (`"-3"`) is still skipped by the
  `isinstance(pval,(int,float))` guard: deliberately left, t09's value was an int.
- **Buffer/compute-shader nodes do NOT render headless** under `--export-material`
  (`shader_compile_spirv_from_source` on null -> all-black). This kills
  `slope_blur` and the whole `warp_dilation` family for cookbook materials even
  though they validate. `normal_map` only survives because its `switch` bypasses
  its internal buffer when `param4=0`. Use `directional_warp`/`warp2` for
  distortion instead (they render).
- **`truchet` output is a smooth distance field, range ~0.5-0.95** (not 0/1),
  shaped like interlocking tubes. Threshold/gradient INSIDE that range, and feed
  the raw field into `normal_map` for rounded tube relief. Diagnose any unknown
  node's real value range by rendering its noise-gallery/debug swatch and
  sampling with `quality/pngread.py` before tuning a builder against it.
- **The 3D preview scene renders METALS dark** (dark environment, metals reflect
  it). m01/m02/m03 all look dark with bright highlights; that is the scene, not a
  broken material. Judge metals by the pattern/relief, or read the ORM.
- **Controller render tools for material self-screen:** `python -m
  quality.render_one <label> <case> [size]` renders the promoted flat maps to
  `quality/cookbook/<label>/<case>/` (absolute paths, ~10-30s at 512), then the
  MCP `render_preview` tool (or `quality/_make_previews`) composites the 3D
  sphere/cube preview. One Godot at a time. (The old `scratchpad/preview_material.py`
  was a per-session scratch file and does not persist.)
- **Material authoring flow (this plan):** implementer authors builder + validates
  + promotes (NO Godot); controller renders + self-screens for gross misses and
  variety collisions, then Grayson is the visual judge. A "new base" material can
  still drift into an existing look (t09 clay -> voronoi plates; s12 -> wood) so
  actively differentiate.
- **The 2026-09-05 nightly backup truncation is FIXED (2026-09-06).** The cause
  was NOT the `git diff HEAD --binary` `NativeCommandError` at
  `Backup.Common.ps1:229` (that is a benign CRLF warning already handled by the
  EAP relax at lines 217-232). The powershell process was idle-slept mid-run
  before the top-level `finally { Stop-Transcript }`. `Backup-All.ps1` now holds
  a `SetThreadExecutionState(ES_SYSTEM_REQUIRED)` wake-lock for the run's
  duration (commit `f7e809d`, push pending). The true truncation signature is a
  missing `transcript end` footer, not the git error. A forced sleep (lid close)
  or `StopIfGoingOnBatteries` can still truncate, far more rarely.
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
- **The user-scope `mm-mcp.exe` is an EDITABLE install** (`pip show mm-mcp` ->
  `Editable project location: C:\Projects-local\Tool-MaterialMaker-MCP`), so
  on-disk source == what the server imports; no reinstall is ever needed for a
  code change. Only a server process already running from BEFORE a change holds
  stale code in memory. Fix = restart that process (idle-exit retires it, or
  `/mcp` reconnect, or session restart), not `pip install`. Verified 2026-09-06:
  the `577592f` subgraph-descent fix is live in the MCP `validate` tool this
  session (probe returned `where: sub1/inner`).

## 🕓 Session log

Newest first. Keep at most 8 entries; older ones are in `git log` (search the
commit subjects, every session ends with a `docs:` wrap-up commit).

### 2026-09-13 (enum-index validation enforcement, MERGED to main): `pickup` (caught baton drift: noise branch already merged `0169446`/pushed, baton said unmerged), Grayson picked the deferred enum follow-up. Advisor-prompted investigation flipped the premise: detection already worked (`validate_graph` flags t09's `type=-3` int, even in-subgraph); the hole was ENFORCEMENT (out-of-range enum was a `warning`, all gates filter to errors / promote never validates). Fix: out-of-range enum index -> `error`; message explains the clamp and either names the intended index via `_enum_literal_hint` (literal match) or lists all valid options; `catalog_builder` captures `value_literals` for numeric index-mismatched enums only; ratchet test in `test_cookbook_gate`. Wrap-up surfaced a sibling branch `claude/zealous-ritchie-cb051a` (2 commits, unmerged) fixing the same thing as a warning-with-options-list; Grayson said reconcile, so its options-list message + wavelet range-pin test were folded into this branch (sibling now superseded). TDD red->green, fast suite 1039->1045. Ruled out: string-literal guard hole (left; t09 was int) and the stale gitignored `catalog/catalog.json` artifact (not a bug). Commons log written.
### 2026-09-13 (noise/distortion vocabulary + core toolbox, MERGED `0169446` + pushed): `pickup` -> `subagent-driven-development` resumed at Task 8, finished the plan (all 14 tasks, per-task + final opus review clean). Shipped 6 proof materials on unused bases (s13 marble/fbm, m03 titanium/anisotropic, sf07 conduit/truchet, s12 sandstone/directional_warp, t09 wet sand/wavelet, gl02 cut gem/voronoi_triangle; cookbook 53->59), 19 diagnostic swatches, README un-collapse + count-gated "Core toolbox" section, AUTHORING distortion note. Fast suite 1039; final fix `4905d37` (gl02 card node count). Merged next session; a follow-up t09 enum fix `4d1187f` landed post-merge.
### 2026-09-06 (backup-ops wake-lock, cross-project): `pickup` here, Grayson picked next-step #2. Root-caused the 09-05 nightly truncation as idle-sleep mid-run (the git `NativeCommandError` is a handled CRLF warning; true signature is a missing `transcript end` footer, not a code bug), and added a `SetThreadExecutionState` wake-lock to `backup-ops\Backup-All.ps1` (acquire in try, release in finally). Verified compile + parse; commit `f7e809d` local, PUSH PENDING (ssh-agent not loaded this session). Commons log written. No MM-MCP code changed.
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
### 2026-09-05 (teardown #3 executed): examples/ folded into the cookbook (46 -> 53), mm-play port diagnostic, backup exclusions, baton diet (`87be578`, `5b93785`); v0.7.0 released. (Older entries: see `git log`.)
