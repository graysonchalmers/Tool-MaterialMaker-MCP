# Material Maker MCP (Phase 3 — Authoring Quality) Plan

> **For agentic workers:** This phase is an iterative tuning loop, NOT bite-sized TDD.
> Sub-phases 3A/3B/3C each have a binary gate; run the phased-rebuild loop per
> sub-phase (read → confirm scope → implement → gate → record in STATUS.md).
> Task 3C repeats until its gate is green.

**Goal:** A prompt like "weathered copper" reliably yields a `.ptex` that renders
as weathered copper without manual repair. Measured, not vibes: a frozen material
test set scored by usable-hit-rate.

**Decisions locked (Grayson, 2026-08-26):**
- **Gate target: ≥ 70% usable-hit-rate** on the frozen test set (≥ 11 of 15 cases).
- **Multi-variant ships in Phase 3:** 2-3 variants per prompt; a case scores a
  **hit if ANY variant is usable**. "Usable" = the rendered maps read as the
  prompted material without manual graph repair (opening in MM to *tweak taste*
  is fine; opening it to *fix breakage* is a miss).

**Spec:** `docs/superpowers/specs/2026-08-25-material-maker-mcp-design.md`
(§ Phase 3 quality harness, § Known risks — "Phase 3 is the hard part").

## Global constraints

- All Phase 1-2 constraints carry over (PowerShell 5.1 `;` sequencing, console
  exe for renders, `z-Git\material-maker` read-only, never echo `.env`).
- **The test set freezes at the end of 3A.** Tuning (3C) may change the catalog,
  guidance docs, and authoring workflow — never the test cases or the rubric.
  Adding cases later is a new scorecard, not an edit to an old one.
- Graph authoring is **Claude-in-the-loop** over the MCP tools (that's the thing
  being measured). The harness automates everything around it: rendering,
  contact-sheet assembly, scorecard bookkeeping.
- Judging: Claude vision scores each case against the rubric; Grayson audits the
  scorecard (at minimum every miss + a sample of hits). A disputed case counts
  as Grayson rules, not as Claude scored.

## What gets built

| Artifact | What it is |
|---|---|
| `quality/test_set.json` | 15 frozen cases: `{id, prompt, category, must_have[], must_not[]}` |
| `quality/run_case.py` | Renders 2-3 authored variants for a case, writes a per-case contact sheet dir |
| `quality/scorecards/<date>-<label>.md` | One scorecard per full run: per-case verdict + evidence paths + hit-rate |
| `docs/AUTHORING.md` | The authoring guide Claude follows: patterns, recipes, pitfalls (the main tuning lever) |
| Catalog description enrichment | Improved `shortdesc`/`longdesc` where the `.mmg` text misleads authoring |

---

## Sub-phase 3A — Test set + scoring harness

**Scope:** Build the measuring stick before touching quality.

- [ ] **Test set.** Author `quality/test_set.json` with 15 prompts spread across
  categories so the score can't be gamed by one strength: metals (3), stone/
  masonry (3), wood (2), fabric/leather (2), organic/ground (2), manufactured
  (2), weathering-combo stress cases (1, e.g. "rusted painted steel, paint
  peeling"). Each case lists 2-4 `must_have` visual criteria ("green-brown
  patina over copper base", "visible brick coursing in the normal map") and any
  `must_not` ("not clean polished copper").
- [ ] **Rubric.** Write the usable/miss rubric into the test set file's header
  comment + `docs/AUTHORING.md` stub: usable = all `must_have` present, no
  `must_not`, no render errors, no obviously broken map (flat normal, black
  albedo, etc.). Any-variant-hits scoring.
- [ ] **Harness.** `quality/run_case.py`: given a case id and 2-3 `.ptex` paths
  (or inline JSON), validates + renders each via the existing `mm_mcp` modules
  at `--size 512`, writes `quality/runs/<run>/<case_id>/variant_N/` with the 4
  maps + the source `.ptex`, and appends a row to the run's scorecard skeleton.
  Reuses `render.py`/`validator` — no new render logic.
- [ ] **Scorecard template.** Markdown: per case — prompt, per-variant verdicts,
  case verdict, evidence path; footer — hit-rate fraction and percentage.

**Gate 3A (binary):** `run_case.py` on one trivial known-good case (e.g. the
bricks example posing as "red brick wall") produces a filled contact-sheet dir
and a scorecard row, exit 0. Test set contains 15 cases, reviewed by Grayson,
and is declared frozen in the scorecard dir's README.

## Sub-phase 3B — Baseline measurement

**Scope:** Measure where authoring stands today, before any tuning. No fixes
during this pass, however tempting — misses are data.

- [ ] For each of the 15 cases: Claude authors 2-3 variants using only the
  current catalog + examples (no AUTHORING.md yet — that's the treatment, this
  is the control), renders via the harness.
- [ ] Score all 15 cases per the rubric; Grayson audits.
- [ ] Write `quality/scorecards/<date>-baseline.md` and record the number in
  STATUS.md. Capture a **miss taxonomy** while scoring: for every miss, one
  line on *why* (wrong node choice, bad parameter ranges, missing pattern
  knowledge, catalog description misled, render pipeline issue). This taxonomy
  is the 3C worklist.

**Gate 3B (binary):** Baseline scorecard exists with all 15 cases scored and a
miss-taxonomy section; hit-rate recorded in STATUS.md. (The *number* doesn't
gate — measuring it does.)

## Sub-phase 3C — Tuning loop (repeat until green)

**Scope:** Raise the hit-rate to ≥ 70% by improving the inputs to authoring.
Each iteration = pick levers from the miss taxonomy → apply → re-run the full
set → new scorecard. Never edit the test set.

Levers, in expected order of payoff:
1. **`docs/AUTHORING.md`** — mine the ~100 bundled examples for reusable
   patterns (base-noise → color-ramp → blend stacks, edge-wear via curvature/AO,
   brick/tile workflows, metal+roughness pairing) and write them as recipes
   Claude follows when authoring. This is where most of the win should live.
2. **Catalog description enrichment** — where a miss traces to a misleading or
   empty `shortdesc`/`longdesc`, override it in the catalog build (an overrides
   file merged by `catalog_builder`, so upstream `.mmg` files stay pristine).
3. **Server-side guidance** — if warranted, expose AUTHORING.md (or a distilled
   version) as an MCP resource next to `catalog://nodes`, so authoring guidance
   travels with the server instead of living only in this repo.
4. **Validator warnings** — add advisory warnings for known bad patterns found
   in the miss taxonomy (e.g. output node missing a roughness input) if they
   recur.

Per iteration:
- [ ] Pick the top miss causes; apply lever changes in a focused commit.
- [ ] Re-author + re-render **all 15 cases** fresh (no reusing old hits'
  graphs — the workflow is what's being measured), score, write a new
  scorecard `<date>-iter<N>.md`.
- [ ] Record the delta in STATUS.md. If hit-rate regressed, the iteration's
  changes get reviewed before the next one (no ratchet assumption).

**Gate 3C = Phase 3 gate (binary):** A scorecard shows **≥ 11/15 (≥ 70%)**
usable-hit-rate with any-variant scoring, Grayson has audited it, and the
result + scorecard path are recorded in STATUS.md. Then commit, push (via
`github-push` from cloud sessions), and close the phase in the baton.

---

## Out of scope (explicitly)

- Raising the bar past 70% (a later Phase 3.5 if wanted; the harness makes
  re-measuring cheap).
- Live-control, public packaging (Phases 4-5, unchanged).
- The deferred minors from the Phase 1-2 review (client round-trip test,
  `render_graph` return-key uniformity, etc.) — still parked unless a miss
  traces directly to one of them.

## Risks

- **Overfitting to the 15 cases.** Mitigation: the frozen-set rule, category
  spread, and a 3-5 prompt unfrozen spot-check at the end (advisory evidence,
  not a gate).
- **Judge drift.** Claude scoring its own output is soft; that's why Grayson
  audits every miss + a sample of hits, and disputed cases go his way.
- **Per-render cost.** ~seconds of Godot startup × 15 cases × 3 variants ×
  N iterations. Acceptable for batch; if it drags, drop render size to 256 for
  iteration runs and 512 for gate runs.
