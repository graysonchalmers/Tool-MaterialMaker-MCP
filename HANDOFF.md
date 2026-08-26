# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-26 (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

Phases 0-2 are done and merged to `main`. **Phase 3 (authoring quality) is in
progress on branch `feat/phase3`** and has moved from a 3/15 baseline to
**10/15 (67%) after iteration 1 — one case short of the 11/15 (≥70%) gate.**
The Phase 3 harness (`quality/`) works end to end: it renders authored variants,
lays out contact sheets, and rebuilds a Markdown scorecard from per-case
verdicts. The frozen 15-case test set, the baseline, and the iter1 scorecard are
all committed. Nothing is mid-edit.

## 📌 Where we stopped

Just committed iter1 = 10/15 (`7a4c128`). The blocker that ate most of the round
(from-scratch materials rendering FLAT normals) is **solved**: clone a
sharp-edged bundled example so the `normal_map` has real gradients to work from.
That landed `o01` moss (← `dry_earth`). Two cases are the remaining story: `s02`
granite is counted but **flagged for your audit** (polished stone → near-flat
normal, defensible but strict-rubric-borderline), and `m02` aluminum is still a
miss (needs crisp directional relief).

## ▶️ Next concrete step

**Reach the 11/15 gate** — landing any ONE of these does it:
1. **Audit `s02` granite** (cheapest): if you accept a near-flat normal for
   *polished* granite, s02 is a clean hit and the gate is met at 11/15 as-is.
2. **Fix `m02` brushed aluminum**: needs a sharp *directional* generator feeding
   a working normal_map (stretching smooth `rock` gave soft streaks + flat
   normal). Try a stretched sharp pattern or a directional `warp` of a sharp noise.
3. **Crack one hard composite**: `man01`/`man02` hex (build a hexagon generator
   once, reuse for both), `f01` denim weave, or `combo01` paint-over-rust-with-
   peel-mask. Bigger lift, but headroom past the gate.

Alternatives: stop and audit the whole iter1 scorecard first (several hits are
"modest" — `w01` grain softness, `s02` polished-normal — worth your eyes before
declaring the gate green).

## ❓ Open questions

- **Does a near-flat normal disqualify polished granite (`s02`)?** Your call
  decides whether iter1 is already 11/15 (gate met) or 10/15.
- **`m02` aluminum approach** — sharpen the directional generator, or accept it
  as one of the permanent hard cases?
- Multi-variant is authored (2 variants/case) but scoring only ever needed
  variant 1 so far; keep authoring 2 or drop to 1 for speed?

## 🗂️ Changed this session

- Branch: `feat/phase3` (NOT pushed — all commits are local). Off `main` at `b4524b4`.
- Built `quality/`: `test_set.json` (15 frozen cases + rubric), `run_case.py`
  (harness), `author.py` (reproducible variant builders), `score_baseline.py`,
  `scorecards/` (baseline + iter1). Added `docs/AUTHORING.md` (recipes),
  `docs/superpowers/plans/2026-08-26-material-maker-mcp-phase3.md` (the 3A/3B/3C plan).
- Touched `src/mm_mcp/render.py`: retry loop for transient Godot crash codes
  (`0xC0000005`/`0xC0000409`) — they recur under render volume, graph-independent.
- Key decisions (+ why):
  - **Gate = ≥70% (≥11/15), any-variant, multi-variant ships in Phase 3** (your call).
  - **Test set frozen after your review** (m02 anisotropy softened to "directional
    streaking"); tuning may never touch the cases, only the authoring inputs.
  - **Recolor lever** (rewrite a colorize albedo ramp, keep structure) converted
    5 cases; the two-layer recolor (base + patina) did copper.
  - **Normals need a sharp-edged source** — hand-built and smooth-example clones
    render flat; clone `dry_earth`-type sharp generators for relief.

## ⚠️ Heads-up for the next agent

- **Run tests with `.venv\Scripts\python.exe`** (the `mcp` package is only there);
  system Python 3.13 can run the harness/render but not import `server`.
- `quality/runs/` is gitignored (heavy PNGs); scorecards + test_set are the
  committed evidence, and `author.py`/`score_baseline.py` reproduce the renders.
- All Phase 1-2 render gotchas still hold (see CLAUDE.md): `--export-material`,
  `_console.exe`, no `--headless`, `steam_appid.txt`.
- `normal_map` is a compound node; its real params are `param0` (size),
  `param1` (strength), `param2`, `param4` — NOT `amount`/`size`.

---

## 🕓 Session log

### 2026-08-26 — Scope + execute Phase 3 (authoring quality) to 10/15
- Planned Phase 3 as three gated sub-phases (3A test set + harness, 3B baseline,
  3C tuning); locked the gate at ≥70% any-variant with multi-variant included.
- 3A: authored + froze the 15-case test set (after review), built `run_case.py`
  harness + scorecard machinery. 3B: baseline = 3/15 (nearest-example-as-is) with
  a miss taxonomy. 3C iter1: 3→10/15 via the recolor lever (leather, barn wood,
  copper, concrete), a grain-ramp fix (oak planks), and the clone-a-sharp-edged-
  example insight (moss). Solved the flat-normal blocker; added a render retry.
- Ruled out: hand-assembling `normal_map` (renders flat) and cloning smooth
  examples like `rock` for relief (also flat) — sharp-edged sources are required.

### 2026-08-25 — Set up Material Maker + build the MCP (Phases 1-2)
- Cloned RodZill4/material-maker into `z-Git\` as a reference, got it running (found the
  Steam `steam_appid.txt` self-relaunch gotcha), and confirmed headless `--export-material`
  renders PBR maps.
- Brainstormed and approved the MCP design (thin batch-render first, me-first audience),
  scaffolded `Tool-MaterialMaker-MCP` as a new project, pushed a private GitHub repo.
- Wrote the Phase 1-2 implementation plan, then executed it subagent-driven: 9 TDD tasks,
  each reviewed for spec + quality; fix loops on Tasks 3/5/7/9; whole-branch review (Opus)
  + one fix wave. All reviews clean. Merged to `main`, pushed, branch deleted.
