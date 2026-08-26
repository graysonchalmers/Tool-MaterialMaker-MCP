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
- A smooth source is still fine when the target is genuinely near-flat (polished
  granite `s02`); the fix is for when you *want* the generator's pattern in the
  normal.

`m02` brushed aluminum (previously "still open — crisp directional relief") is
covered by the same lever: its streaks read in albedo + roughness already, and
`param4=0` would add real directional micro-relief if a sharper normal is wanted.
