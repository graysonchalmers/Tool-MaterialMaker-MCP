# 🧭 Session Handoff — Tool-MaterialMaker-MCP

_Last updated: 2026-08-26 06:05 CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**Shipped a first public release, then kept improving it.** The repo is **public**
on GitHub with an MIT license, a public README (gallery + super-alpha disclaimer),
a pip-installable package (`mm-mcp` entry point), a six-material `examples/`
showcase, a social-preview card (`docs/social-preview.png`, needs manual upload
via repo Settings → Social preview), and a tagged **`v0.1.0`** release. Phases 0-3
are all done and verified; **Phase 3 authoring quality is now at 13/15 (87%)**
after landing the two hex cases (man01 metal grating + man02 ceramic hex tiles)
via a beehive clone. Working tree is clean and `main` is level with `origin/main`.
Nothing is mid-edit.

## 📌 Where we stopped

Everything for the release is landed, pushed, and public. Last commit is
`4eaaca9` (the super-alpha disclaimer); `v0.1.0` tags it. The session's final act
was cutting the release. There is no unfinished work in flight.

## ▶️ Next concrete step

Nothing is required — v0.1.0 is a clean stopping point. When you want to keep
going, pick from the **Next-up options** menu below (that's the "bunch of next-up
options" you asked to record).

## 🧭 Next-up options (pick any; none are blocking)

**A. Polish the public page (cheap, high-visibility)**
- Eyeball the live README render for image/table correctness:
  https://github.com/graysonchalmers/Tool-MaterialMaker-MCP
- Add a repo social-preview image (Settings → General → Social preview) so link
  shares show a material, not a gray box. A contact sheet of the gallery works.
- Consider a short GIF/screen-capture of an assistant authoring a material end to
  end (prompt → graph → render) for the README top.

**B. Push authoring quality past 13/15 (the fun artist work)**
Two MISS cases remain (both harder composites):
- `f01` denim weave — needs a woven twill pattern with a real normal (the paper
  example emits albedo only). Look for a fabric/weave generator to clone; the
  `weave`/`weave2` nodes may exist, else build a crossed-directional pattern.
- `combo01` paint-over-rust-with-peel — a flat colored paint coat blended over
  `rusted_metal` via an irregular peel mask, with roughness contrast between
  smooth paint and rough rust. A masked two-layer blend, like the copper patina
  but with a harder-edged peel mask.
- Reusable recipes proven so far (see `docs/AUTHORING.md`): voronoi port-2
  per-cell-random flecks (granite), wood-grain-as-brush-streaks (aluminum),
  **beehive hex clone** (both hex cases — man01 relief via heightmap, man02
  drives albedo off the clean hex field bypassing the per-cell random).

**C. Robustness / cross-platform (makes "verified on one machine" less scary)**
- Test on macOS/Linux (path handling, `_console.exe` is Windows-only — the code
  already falls back to the plain binary, but it's untested off-Windows).
- Widen validator param ranges or clamp gracefully: voronoi/perlin `scale_*`
  emit "outside [1,32]" warnings at the fleck/streak scales that actually render
  fine. Cosmetic now, but noisy for users.
- Add a couple more unit tests around `author.py`'s new `rewire`/`drop_conn`
  helpers so future graph surgery is guarded.

**D. Phase 4/5 from the original plan (bigger lifts)**
- **Phase 4 (public packaging, deeper):** publish to PyPI so `pip install mm-mcp`
  works without a clone; a real quickstart; maybe a Dockerfile.
- **Phase 5 (live control):** drive Material Maker over its in-app socket for a
  watchable, interactive build instead of batch render.

**E. The flat-normal question (quality ceiling)**
- Both new hits (granite, aluminum) render **flat normals**, defensible for
  polished/brushed surfaces but a real ceiling for materials that need relief.
  Worth a focused investigation into *why* hand-built and some cloned normal
  chains render flat, since it's blocked multiple cases. If cracked, it reopens
  from-scratch authoring.

## ❓ Open questions

- Do you want a PyPI publish (Phase 4), or is clone-and-`pip install -e .` fine
  for the alpha audience?
- Keep authoring 2 variants/case, or drop to 1 for speed? (Scoring has only ever
  needed variant 1.)
- Is the flat-normal limitation acceptable long-term, or worth a dedicated dig
  (option E)?

## 🗂️ Changed this session

- Branch: `feat/phase3` → merged to `main` (`ed6986b`), pushed. Tag `v0.1.0` at
  `4eaaca9`. Repo flipped **public**.
- **Phase 3 gate closed 10/15 → 11/15**: rewrote two `author.py` builders.
  - `s02` granite: root-caused the fog (cloned `rock` but only shrank the perlin,
    leaving the albedo voronoi at scale 4). Fix feeds the albedo colorize from
    **voronoi output port 2** (`rand3` = flat random value per cell) at a fine
    scale → crisp multi-tone mineral flecks. Added a `rewire` helper.
  - `m02` brushed aluminum: cloned `wood` (directional-streak generator with a
    **working** normal chain), straightened the grain (fed `blend_0` from the
    un-warped `perlin_2`), neutralized to gray, forced metallic (`drop_conn`
    helper drops the grain-driven metallic map so the scalar `metallic=1`
    applies). Streaks read in albedo + roughness.
- **Packaging:** added MIT `LICENSE`; made `pyproject.toml` pip-installable
  (src layout, build-system) with an `mm-mcp` console entry point (`server.main`);
  rewrote `README.md` for a public audience (gallery, generic install/config, MCP
  client snippet, tool table, gotchas, attribution); fixed the stale `--export`
  ref; added `examples/` (6 `.ptex` + 512px previews + table); refreshed
  `__init__` (v0.1.0).
- **Disclaimer:** prominent super-alpha / artist-built warning added to README,
  STATUS.md, and examples/README ("verified" = "worked on the one machine").
- Recorded s02/m02 verdicts in the iter1 `_result.json`s and rebuilt the
  scorecard; STATUS.md Phase 3 rows → ✅ verified.

## ⚠️ Heads-up for the next agent

- **Run tests with `.venv\Scripts\python.exe`** (or activate the venv). The
  package is now `pip install -e .`, so `import mm_mcp` works from anywhere.
  Fast suite: `pytest -q -m "not integration"` (80 passed).
- **Pillow is installed in `.venv` but deliberately NOT in `pyproject.toml`** — it
  was a one-time tool to downscale the `examples/images/` previews. Don't add it
  as a dependency.
- `quality/runs/` and `quality/authored/` are gitignored (heavy PNGs / regen'd);
  scorecards + test_set are the committed evidence, `author.py` reproduces renders.
- All Phase 1-2 render gotchas still hold (see CLAUDE.md): `--export-material`,
  `_console.exe`, no `--headless`, `steam_appid.txt`.
- `normal_map` is a compound node; real params `param0` (size), `param1`
  (strength), `param2`, `param4` — NOT `amount`/`size`.
- Voronoi **output port 2** = `rand3` random-per-cell (the fleck/speckle source);
  ports 0/1 are distance fields. Reusable for any granular material.

---

## 🕓 Session log

### 2026-08-26 (pm) — Close Phase 3 gate + ship v0.1.0 public release
- Audited the flagged `s02` granite: called it a real MISS (foggy albedo, not the
  flat normal). Fixed it with a fine voronoi **port-2 per-cell-random** fleck
  source → genuine HIT. Then fixed `m02` brushed aluminum by cloning `wood`'s
  directional-streak-with-working-normal chain and straightening it. Scorecard
  went 10/15 → **11/15 (73%)**, gate met and recorded in STATUS.md.
- Packaging pass: MIT LICENSE, pip-installable `pyproject` with `mm-mcp` entry
  point, public README rewrite (gallery + tool table + gotchas), `examples/`
  showcase (6 materials), fixed the `--export` typo.
- Added a prominent **super-alpha / artist-built** disclaimer across README,
  STATUS, examples README (Grayson's explicit ask: make clear it's very early and
  he's an artist/animator, not a software engineer).
- Merged `feat/phase3` → `main`, pushed, **flipped the repo public** (with
  description + topics), cut **`v0.1.0`** release.
- Verified: editable install works, `mm_mcp` imports anywhere, `mm-mcp` on PATH,
  80 fast tests pass. Recorded a Next-up options menu (A-E) above.

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
