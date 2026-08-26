# AUTHORING.md — how to author a Material Maker graph from a prompt

> **Phase 3 status:** This file is a STUB during sub-phase 3B (baseline). The
> recipe sections below are intentionally empty so the baseline run measures
> authoring with only the raw catalog + examples as a control. Sub-phase 3C
> fills them in from the miss taxonomy and re-measures. Do not add recipes
> before the baseline scorecard is recorded.

## Scoring rubric (frozen with the test set)

A prompt-to-graph attempt is scored per `quality/test_set.json`:

- **Any-variant scoring:** a case is a HIT if at least one of its 2-3 rendered
  variants is usable.
- **Usable** = the rendered PBR maps read as the prompted material without
  manual graph repair. Tweaking to taste in the app is fine; fixing breakage is
  a miss. Usable requires ALL of:
  1. every `must_have` criterion visibly present,
  2. no `must_not` criterion present,
  3. no render errors (all four maps produced),
  4. no obviously broken map (flat-black/white albedo, uniform-blue normal,
     uniform heightmap/orm).

## Authoring workflow (invariant across phases)

1. Read the prompt; pick the closest bundled example(s) with `list_examples` /
   `load_example` as a starting pattern.
2. Draft 2-3 variant graphs using the catalog (`list_node_types`,
   `describe_node`, or the `catalog://nodes` resource) for exact ports/params.
3. `validate_graph` each variant; fix every error-severity problem.
4. Render via the harness (`quality/run_case.py`) or `render_graph`.
5. Judge the maps against the rubric; log why any miss missed.

## Node & pattern recipes

_Filled during 3C from the bundled examples + the miss taxonomy. Each recipe
names a base example and the edit that turns it toward a prompt._

### The recolor lever (highest payoff)

Many materials differ from a bundled example only in COLOR, not structure. A
`colorize` node holds a `gradient.points` list of `{pos, r, g, b, a}`. Find the
colorize whose points are **saturated** (not gray): that is the albedo color
ramp. The gray-valued colorize nodes feed roughness/height/metallic — leave them
unless you mean to change surface response.

Verified conversions (baseline MISS → iter1 HIT):
- **Brown leather** ← `crocodile_skin`: recolor the green albedo ramp
  (`colorize_1`) to brown `(0,.20,.11,.05)→(1,.52,.34,.18)`. Cellular grain is
  already right.
- **Weathered barn wood** ← `wood`: recolor the vivid albedo ramp (`colorize_2`)
  to faded gray-brown, and push the roughness ramp (`colorize_0`) high
  (`.72→.9`). Grain + knots are already right.

### Two-layer weathering (base metal + patina)

`rusted_metal` is the reusable pattern: a `blend` composites a **base** colorize
over a **patch** colorize through a **mask** colorize; a separate mask drives
metallic down on the patches. Recolor both layers to retarget the weathering:
- **Weathered copper** ← `rusted_metal`: base `colorize_2` gray→copper
  `(0,.45,.22,.10)→(1,.72,.40,.19)`; patch `colorize_1` orange-rust→verdigris
  `(0,.05,.20,.15)→(1,.33,.60,.47)`. Widen the patina by lowering the mask
  threshold (`colorize_3` 0.45→0.35).
- **Rusted iron** = `rusted_metal` as-is (already a HIT).

### Surface pattern generators (brick, tile, hex, planks)

- **Brick / block coursing**: `bricks` / `improved_brick` (running bond, mortar
  in normal+height) — a HIT for red brick as-is; recolor for other brick tones.
- **Cracked ground**: `dry_earth` (voronoi plates + recessed cracks) — a HIT for
  dry mud as-is.
- Planks: `wooden_floor` gives plank divisions but weak grain; the `wood`
  example has strong grain but no divisions. Oak planks wants BOTH (open item —
  needs a blend of plank cuts over strong grain).
- Hex cells (grating, hex tiles) are an open item — no single example ships a
  hexagon generator wired to a material; needs `shape`/`pattern` hex authored in.

## Common pitfalls (from the miss taxonomy)

- **Wrong nearest example**: the closest-named example often depicts a different
  material (e.g. `tiles` is fish-scale scallops, not hexagons; `marble` is veined
  + gold-framed, not speckled granite). Check the render, don't trust the name.
- **Albedo-only examples**: some examples (e.g. `paper`) emit only an albedo, no
  normal/height/orm — unusable under the "all four maps" rule. Build the material
  outputs explicitly.
- **Transient Godot crash**: renders intermittently die with exit `0xC0000005` /
  `0xC0000409` mid-export (GPU, not the graph). `render.py` now retries these
  transient codes up to 3x.
- **Normals need a SHARP-EDGED source (resolved)**: a hand-assembled
  `perlin -> normal_map -> Material.normal` chain renders a FLAT normal, and so
  does cloning a *smooth* example (`rock`). The fix that works: CLONE a working
  example whose generator has **sharp edges** — `dry_earth` (voronoi cracks)
  gives the `normal_map` real gradients to work from, so recoloring it to green
  produced a moss with rich ground relief (`o01`). Rule of thumb: for a material
  that needs surface relief, start from a sharp-edged example (cracks, bricks,
  cells), not a smooth blobby one. A smooth source (`rock`) is fine only when
  the target is genuinely near-flat, e.g. polished granite (`s02`).
## The flat-normal fix: `normal_map` `param4=0` (the real root cause)

The "normals render flat" problem has a definitive cause and a one-parameter fix.

`normal_map` is a **compound** node. Internally:

```
input -> buffer(size 2^param0) -> switch(source = param4) -> edge_detect(param1) -> normal
                    \-------------------> (switch port 0, raw input) ---/
```

- `param0` = internal buffer size (2^n)
- `param1` = relief **strength** (the edge_detect amount)
- `param4` = the **switch**: `1` = edge-detect the pre-rendered *buffer*; `0` =
  edge-detect the *raw* input directly.

With the default **`param4=1`**, edge_detect runs on a buffered copy of the
input. For an input fed **directly from an analytic generator** (voronoi,
`diagonal_weave`, perlin through a colorize), that buffer comes back effectively
constant, so the normal is **FLAT**. This is why every crocodile_skin / wood
donor normal rendered flat (and why hand-built `generator -> normal_map` chains
looked flat too).

**The fix: set `param4=0`.** That routes the raw analytic input straight into
edge_detect, and the generator's real gradients produce relief. Then tune
`param1` for strength (0.2–0.4 is a good subtle range; 1+ oversaturates).

```python
node(g, "normal_map_0")["parameters"] = {
    "param0": 11, "param1": 0.25, "param2": 0, "param4": 0}
```

This unblocked `f01` denim (a clean diagonal twill in the normal, from
`diagonal_weave`) and is a **general lever**: any graph whose normal is fed
directly from an analytic generator can get a real normal this way. Examples
that already looked fine (`dry_earth`/`bricks` donors, `param4=1`) work because
their input reaches `normal_map` through a `blend`/buffered chain, so the buffer
path has real content.

Practical guidance now:
- Relief from a **cloned working chain** (dry_earth cracks, bricks, beehive
  heightmap): keep it as-is, it works.
- Relief from a **directly-fed analytic generator** (weave, stretched noise,
  voronoi): set `normal_map` `param4=0` and tune `param1`.
- Even a chain that *looks* buffered (a `blend` node ahead of `normal_map`) can
  still be directly-fed if the blend's real input is an un-warped, un-buffered
  generator — the switch cares about what the buffer actually renders, not the
  node type sitting in front of it. `m02` brushed aluminum is the example: its
  `blend_0 -> normal_map_0` chain looked like the "working" pattern, but once
  `blend_0` was straightened to take `perlin_2` directly (killing the warp), the
  buffer was flat again.

`s02` gray granite and `m02` brushed aluminum both got the `param4=0` upgrade
(2026-08-26, post-15/15 polish pass): granite's `voronoi_1 -> warp_0 ->
normal_map_0` chain and aluminum's straightened `blend_0 -> normal_map_0` chain
were both directly-fed analytic sources rendering flat. `param4=0` at low
`param1` (0.3–0.45) now gives granite real polished-stone micro-relief and
aluminum real parallel brush-scratch relief, without changing either case's
albedo/roughness or its HIT verdict.

## Fabric cookbook (cookbook growth, informal — 2026-08-26)

Grown beyond the frozen 15-case test set (`f01` denim, `f02` leather) to widen
category coverage. **Not scored against the Phase 3 rubric** — 1 variant per
material, self-judged by eye, no scorecard/gate. Builders:
`quality/cookbook_fabrics.py`; render harness: `quality/render_cookbook.py`
(mirrors `run_case.py`'s validate+render but skips the frozen `test_set.json`
lookup, so it doesn't touch scored infra). Outputs under
`quality/authored/cookbook-fabrics/` and `quality/cookbook/cookbook-fabrics/`
(both gitignored, regenerable). Downscaled albedo previews below are made by
`quality/_make_previews.py` (same one-off Pillow technique as
`examples/images/`) and live in `docs/images/cookbook-fabrics/`, tracked in
git since they're documentation, not renders.

| Preview | Material | Verdict |
|---|---|---|
| ![](images/cookbook-fabrics/f03_canvas_burlap.png) | Canvas/burlap | HIT |
| ![](images/cookbook-fabrics/f04_wool_knit.png) | Wool/chunky knit | Partial (basket-weave, not true loops) |
| ![](images/cookbook-fabrics/f05_silk_satin.png) | Silk/satin | HIT |
| ![](images/cookbook-fabrics/f06_velvet.png) | Velvet | HIT |

- **Canvas/burlap (HIT):** retype the generator to `weave` (plain over/under,
  one output) at a coarse scale (`columns`/`rows` ~10) with `width` ~0.6 so
  gaps show between thick threads. Natural tan, high roughness, `param4=0`
  normal fix at moderate strength for pronounced coarse-thread relief.
- **Wool/chunky knit (PARTIAL — be honest about this one):** tried `weave2`'s
  `stitch` param first, expecting loop softness — it just renders a crisp
  herringbone/basket diagonal, structurally the same hard-crossing weave as
  `weave`. **This catalog has no true loop-knit generator.** The workable
  stand-in: `weave` at a COARSE scale with near-max `width` (few, wide,
  almost-touching ribs) reads as chunky blocky yarn rows, not fine thread —
  closer to a basket/chunky-weave textile than true knit loops, but a
  reasonable substitute. Don't oversell it as "knit" in user-facing copy.
- **Silk/satin (HIT):** retype to `diagonal_weave` at a FINE scale (~48, vs
  denim's ~20) so the weave is nearly invisible — the differentiator from
  denim/canvas isn't visible thread texture, it's LOW roughness (glossy) +
  saturated low-contrast jewel-tone albedo. Normal strength very low
  (~0.08) — just enough faint sheen-line variation to read as woven, not
  flat plastic.
- **Velvet (HIT, but took two tries):** a soft fibrous pile has NO grid
  pattern, so this isn't a weave graft at all.
  - First attempt reused the granite speckle lever (voronoi **port 2** =
    `rand3`, flat per-cell random) at voronoi's max scale (32). Looked
    mottled/faceted like crystal or stone, not soft fabric — voronoi cells
    are still ~60px wide on a 2048px render, and a flat per-cell random
    value creates hard, high-contrast patch edges no matter how narrow the
    color gradient is (the per-cell value still spans the full gradient
    range).
  - Tried grafting a `fast_blur_shader` node between the voronoi and the
    colorize feeds to soften those edges — hit a Godot "invalid shader"
    render failure (its input port is `rgba`; voronoi port 2 is `rgb`).
    Not worth chasing for a one-off; noted here so nobody re-tries it blind.
  - **What actually worked:** retype the generator to `perlin` instead of
    voronoi. Perlin is continuous (no cell edges) and `iterations` (octaves,
    up to 10) layers in fine high-frequency detail on top of the base noise
    — genuinely reads as soft fiber grain. Deep saturated wine albedo, high
    roughness, and a very low `normal_map` `param1` (~0.12, still `param4=0`
    since perlin is a directly-fed analytic generator) for soft nap relief
    instead of hard relief.
  - **General lesson:** for a SOFT/continuous material (velvet, felt, fog,
    skin), reach for `perlin`/`fbm` first, not `voronoi` — voronoi's cell
    boundaries are inherently hard-edged even when blurred at the color
    level; perlin has no edges to begin with.

## Organics cookbook (cookbook growth, informal — 2026-08-26)

Same informal convention, widening organism SURFACES beyond the frozen set's
GROUND organics (`o01` moss, `o02` dry mud). Builders:
`quality/cookbook_organics.py`. All 4 were HITs on the first pass, no
iteration needed — every one reused an already-proven lever.

| Preview | Material | Verdict |
|---|---|---|
| ![](images/cookbook-organics/o03_tree_bark.png) | Tree bark | HIT |
| ![](images/cookbook-organics/o04_snake_scales.png) | Snake scales | HIT |
| ![](images/cookbook-organics/o05_coral.png) | Coral | HIT |
| ![](images/cookbook-organics/o06_lichen_crusted_rock.png) | Lichen-crusted rock | HIT |

- **Tree bark:** clone `wood` UNMODIFIED structurally — unlike `m02` aluminum
  (which straightens the grain to kill wood's knots), bark WANTS the knotty
  waviness, so leave `wood`'s knot-overlay chain alone. Just the recolor
  lever (weathered gray-brown, multi-stop for tonal variation) + push
  roughness high. `wood`'s own normal chain already works unmodified (`w01`/
  `w02` are proof), so no `param4` fix needed.
- **Snake scales:** `crocodile_skin`'s own default voronoi cellular pattern
  IS already a reptile-scale layout — that's what it was built to look like.
  No retype, pure recolor lever (olive-to-khaki, lower roughness than
  leather for a scale sheen). Proactively applied the `param4=0` fix even
  though `f02` leather's HIT never depended on it: `crocodile_skin`'s normal
  chain (`voronoi_0 -> colorize_0 -> normal_map_0`) is directly-fed with no
  buffer, the same shape as the denim blocker, so it renders flat by
  default. The faceted per-cell relief this produces is a better tell for
  "scales" than the albedo, which stays fairly soft/blurred by the donor's
  own design (same as leather's albedo) — for THIS material, that's fine:
  the read comes through the normal.
- **Coral:** retype the generator to `fbm` with `noise=2` (Cellular) instead
  of `voronoi` — same "distinct cells" family, but fbm's cellular noise
  gives a porous, irregularly-pitted surface rather than voronoi's flat-
  faceted cells, a better match for coral's texture. Coral pink/orange,
  matte, pronounced `param4=0` relief for the pitted bumps.
  General note: `fbm`'s `noise` enum (Value/Perlin/Cellular×6) is a whole
  family of generator shapes worth remembering as an alternative to
  `voronoi` for cell-like patterns.
- **Lichen-crusted rock:** clone `rusted_metal`'s two-layer masked-blend
  structure (the same one `m01` weathered copper already proved) but
  recolor to stone+lichen instead of metal+patina — base (`colorize_2`) to
  gray stone, patch (`colorize_1`) to lichen green-gray, widen the mask
  (`colorize_3` threshold) for more coverage. One real gotcha:
  `rusted_metal` wires the Material's metallic input straight off the mask
  (`colorize_3`) — correct for a metal donor, wrong once recolored to
  stone, so `drop_conn` that connection and force the Material's own
  `metallic` scalar to 0. Also grafted a light `normal_map` fed from the
  mask (`rusted_metal` ships with no normal chain at all) so lichen patches
  read as faintly raised rather than a pure flat-color swap — a nice-to-have
  the donor's own verified `m01`/`m03` cases don't bother with.

## Sci-fi panels cookbook (cookbook growth, informal, 2026-08-26)

A category with no frozen-set precedent at all -- nearest bundled examples
(`metal_pattern_2`/`3`) are undocumented anywhere else in this project.
Builders: `quality/cookbook_scifi.py`. Introduces the **`pattern`** node
family (independent x/y wave generators -- Sine/Triangle/Square/Sawtooth/
Constant/Bounce -- combined via a mix mode) as a new lever alongside weave/
voronoi/perlin/fbm. 3/4 HIT; the 4th is an honest partial with an unresolved
bug, documented rather than papered over.

**Not worth wiring:** Material's `emission_tex` port (port 3). The render
pipeline's export target ("Godot/Godot 4 Standard") only produces albedo/
normal/heightmap/orm -- an emission-only "glowing panel" material would be
invisible in the actual 4-map product output. Ruled out a glowing-tech-panel
idea for this reason before building anything; swapped in the vent grille
instead.

| Preview | Material | Verdict |
|---|---|---|
| ![](images/cookbook-scifi/sf01_hull_plating.png) | Diamond-plate hull panel | HIT |
| ![](images/cookbook-scifi/sf02_hazard_stripe_panel.png) | Hazard stripe panel | HIT |
| ![](images/cookbook-scifi/sf03_circuit_board.png) | Circuit board | Partial -- see bug below |
| ![](images/cookbook-scifi/sf04_vent_grille_panel.png) | Vent grille panel | HIT |

- **Hull plating:** clone `metal_pattern_2` (a bundled example with a
  working grid-line normal chain, but NO albedo texture at all -- it relies
  entirely on Material's flat scalar `albedo_color`). Graft the SAME grid
  pattern (`blend_0`'s output) into new `colorize` nodes feeding both
  albedo AND roughness, so panel seams read as visibly darker/duller, not
  just normal-lit. Proactive `param4=0` -- `blend_0`'s inputs are pattern
  generators (analytic), the same directly-fed shape as every other
  flat-normal blocker.
- **Hazard stripe panel:** built fresh (no donor has diagonal stripes).
  `pattern` node with `x_wave=Square` for alternating bars, `y_wave=
  Constant` so bars run along Y before rotation. Wiring order matters:
  `pattern`(f) -> `colorize`(converts to rgba, hard yellow/black threshold)
  -> `transform`(rotate 45). Feeding `transform` directly from `pattern`'s
  'f' output is a port-type mismatch (`transform`'s input is `rgba`) --
  matches `metal_pattern_2`'s own wiring order, which was the tell.
- **Vent grille panel:** ONE `pattern` node with BOTH `x_wave` and `y_wave`
  set to Square and `mix=Min` gives a grid of small square holes in a
  single node (Min of two square waves = their intersection). Distinct
  from `man01`'s hexagonal grating (beehive-based) -- a square punch
  pattern instead.
- **Circuit board (partial, unresolved bug):** dark PCB base + fine bright
  traces (`pattern` Square wave, hard-thresholded, reused as its own mask)
  worked cleanly on its own. Adding scattered "chip" blocks on top did not:
  - v1 used a SECOND `pattern` node with `mix=Xor` of two Square waves for
    the chip mask -- rendered as pure stripes, chip layer completely
    invisible at every threshold tried (checked the normal map: only the
    trace lines show). `pattern`'s mix modes aren't documented beyond the
    enum names, and Xor's actual numeric behavior for continuous wave
    values isn't obvious. Not worth reverse-engineering for a one-off.
  - v2 swapped to the PROVEN granite-speckle lever (voronoi port 2, flat
    per-cell random) instead -- predictable 0..1 range, no guessing. This
    got chip blocks appearing, but at scale 6 they were huge, amorphous,
    camo-pattern blobs covering ~40% of the surface, not small ICs.
  - v3 raised voronoi scale to 18 for small, sparse, genuinely chip-sized
    blocks. Better size/distribution, but a real bug remains: the
    underlying trace stripes faintly bleed through the chip shapes even
    where the mask should be fully opaque (`blend_type=0` "Normal" at
    `amount=1`). Root cause not identified -- possibly the per-cell mask
    value isn't as flat/saturated as assumed inside a cell. Kept as a
    documented partial ("camo-patched circuit board" is still a usable
    sci-fi texture) rather than sunk into a 4th iteration.
