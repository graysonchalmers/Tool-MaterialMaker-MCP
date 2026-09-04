# AUTHORING.md: how to author a Material Maker graph from a prompt

> **Phase 3 status:** done. The recipe sections below were filled in during
> sub-phase 3C from the baseline miss taxonomy, and the frozen 15-case test
> set now scores 15/15. See `quality/scorecards/` for the scorecards and
> STATUS.md for the phase gate.

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

## Human-editability constraint (invariant, added 2026-08-28)

Every authored graph must be legible to Grayson if he opens it cold in
Material Maker, per `docs/NORTH_STAR.md`'s round-trip loop: step 3 only
teaches him anything if the graph reads as "how would I build this," not as
a technically-correct tangle. This is a real constraint, not just a nicety:
a graph can pass validation and render correctly while still being a mess to
open. Concretely:

- Prefer simple, linear node chains over deeply nested or highly branched
  graphs when a simpler equivalent produces the same result.
- Give non-default nodes descriptive names where Material Maker's UI exposes
  renaming (not just the default `node_2`, `node_3`, ...) when the recipe
  calls for more than one or two of the same type.
- Lay out `node_position` so related nodes sit near each other and
  connections don't have to cross the whole canvas to be traced by eye.
- When a recipe has a real simpler equivalent, prefer it: cleverness that
  only pays off in fewer nodes but costs readability is the wrong trade here.

## Grouping into subgraphs

A subgraph is Material Maker's own native mechanism for the readability goal
above: select a cluster of nodes in the app and press `Ctrl+G` to collapse
them into a single node of `type: "graph"`, with an internal Parameters
remote that exposes a curated, named subset of the cluster's widgets on the
collapsed node itself. It is not a project-specific invention — it's the
same shape Material Maker uses for its own bundled compound nodes
(`normal_map`, `occlusion`, etc.). Opening a graph built this way shows a
handful of friendly, labeled nodes (e.g. "Base Color", "Surface Detail")
instead of every raw generator and wire, with the full detail still one
double-click away.

Cookbook and Phase 3 builders can do the same collapse in code, without
touching the Material Maker GUI, via `group_into_subgraph(graph,
member_names, name, label, exposed, catalog)` in `quality/author_helpers.py`.
`member_names` is the list of node names to fold together; `exposed` is a
list of `(internal_node_name, internal_param_name, slot_id, friendly_label)`
tuples, one per widget that should surface on the collapsed node (`slot_id`
is the external-facing parameter name, `paramN` by convention). `catalog` is
loaded the same way the rest of the authoring tools do:
`build_catalog(load_config().nodes_dir)`. Call it at the end of a `build_*`
function, before `save_variant(...)`, once the recipe's real node graph is
finished — grouping is purely organizational surgery on top of a working
graph, not a step that changes what the material looks like. New cookbook
materials should reach for this from the start rather than shipping a raw
tangle that needs a later retrofit pass.

## Authoring workflow (invariant across phases)

1. Read the prompt; pick the closest starting graph with `list_examples` /
   `load_example`. Two sources: Material Maker's bundled examples and the
   tracked `cookbook/` (`source="cookbook"`). Prefer a cookbook graph when one
   is close: it already encodes a recipe that rendered well.
2. Draft 2-3 variant graphs using the catalog (`list_node_types`,
   `describe_node`, or the `catalog://nodes` resource) for exact ports/params.
3. `validate` each variant; fix every error-severity problem.
4. Render via the harness (`quality/run_case.py`) or `render_graph`.
5. **Judge in 3D, not off the flat albedo.** Feed the render's output paths
   into `render_preview(albedo_path, normal_path, orm_path)` to composite the
   maps onto a sphere, a cube, and a cutaway ball on a tiled ground plane. This
   is where relief actually reads: a normal map that looks like noise on a flat
   swatch shows its real bump under lighting here, and it is the only reliable
   check for a flat-normal miss. `render_preview` does not render a graph, it
   only visualizes maps that already exist, so always call `render_graph` (or
   the harness) first. Two standing caveats, both seen in the recipes below:
   the preview scene's dark backdrop undersells gloss and reads pure metals as
   near-black (see the marble and painted-metal notes), and `tile` raises the
   UV repeat if you want to check how the material reads at a smaller physical
   scale.
6. Judge the maps against the rubric; log why any miss missed.

## Authoring from a reference photo

_Added 2026-09-03, first exercised by `cookbook/glass/gl01_frosted_glass.md`._

When the input is one or more reference photos instead of (or alongside) a
text description, step 1 of the workflow above ("pick the closest starting
graph") becomes a decomposition pass: read the photo against a short rubric,
then use the *same* vocabulary this guide already documents (the noise table
below, the cross-material lessons) to pick a donor and levers. This is not a
separate pipeline or a new tool, it is the existing authoring loop with a
richer step 1.

**Decomposition rubric.** Read the photo for:

- **Color/tone.** Base hue, saturation, value range. Is it uniform across the
  surface, or does it vary by region (a patina, a weathered patch, a grain
  color shift)?
- **Pattern topology.** This is the highest-leverage read, and it reuses the
  "pick the base generator by surface topology, not by grabbing a familiar
  donor" lesson in the Cross-material lessons section below: is the surface a
  CONNECTED CRACK NETWORK (dry_earth's voronoi-plate family), DISCRETE PACKED
  CELLS (voronoi with recessed contact joints), SCATTERED OVERLAPPING PIECES
  (`fbm` Cellular 4), or a DIRECTIONAL/STREAKED pattern (`noise_anisotropic`,
  brushed/woven/grain-direction materials)? Naming the topology narrows the
  donor choice before touching any node.
- **Scale/frequency.** How fine or coarse is the repeating unit, relative to
  materials already in the cookbook (e.g. granite's fine-fleck voronoi at
  scale 44, gravel's pebble scale at 14)? A photo's pattern is often much
  finer or coarser than the nearest-topology donor's default.
- **Roughness/gloss read.** Matte and diffuse, or does it show specular
  highlights and reflections? This sets the Material's roughness value (and
  whether it should vary across the surface via a texture, or stay a uniform
  scalar).
- **Relief cues.** Does the photo show real macro-scale bump (cracks, weave,
  brick coursing), or is the visible detail a color/tone pattern with little
  to no actual surface height (a printed pattern, a micro-surface scattering
  effect like frosted glass)? Don't assume relief just because the pattern
  is visually crisp in the photo, physical reasoning about the real material
  matters here, not just what reads sharp in a 2D image.

**From observations to a graph.** Once the topology, scale, and roughness
read are named, the rest of the workflow is unchanged: clone the
nearest-topology donor (`list_examples`/`load_example`), retune its
scale/warp/roughness/normal parameters toward the photo's read, recolor via
the recolor lever, and judge in 3D per step 5 above. The photo is a richer
starting *description*, not a different authoring path.

**Worked example.** `cookbook/glass/gl01_frosted_glass.md` walks a real photo
(a macro shot of sandblasted glass) through this rubric end to end: connected
crack network topology (same family as `dry_earth`), pushed to a much finer
scale than any existing dry_earth-derived material, cool low-saturation
color, high uniform roughness, and deliberately subtle relief because the
photo's crisp facet edges are a 2D read of what is physically a near-flat,
micro-scattering surface, not a macro bump to chase literally. That last
point is worth restating as its own lesson: a photo can make a pattern look
like it has more physical relief than it does, reason about the real
material, not just the pixels.

## Noise vocabulary (reach past voronoi + perlin)

_Added 2026-09-01 after "a lot of the stuff is looking kind of similar."_

**The problem, measured.** A histogram of the 38 cookbook builders found 69%
clone just three donors (`crocodile_skin` x12, `rock` x7, `wood` x5, all
voronoi-cellular or wood-grain), and the only base noise ever ADDED by hand is
`perlin` (x9) and `voronoi` (x1). The catalog carries 47 noise/pattern nodes;
the cookbook effectively used two. Same structural DNA recolored = materials
that read alike. The fix is a wider base-noise vocabulary, not more recolors.

Gallery source: `quality/noise_gallery.py` (single node -> grey ramp -> albedo,
so you see the raw field). Render with `python quality/render_cookbook.py
noise-gallery`. Tracked contact sheets:

![fbm bases](images/noise-gallery/fbm-bases.png)
![cross-family](images/noise-gallery/cross-family.png)

**Biggest single lever: `fbm`'s `noise` enum.** One node, 8 bases, and they are
NOT interchangeable:

| `noise` | Reads as | Reach for it when |
|---|---|---|
| 0 Value | soft low-freq blobs | broad tonal drift, underlays |
| 1 Perlin | classic soft cloud | gentle variation (its only close cousin is Value) |
| 2 Cellular 1 | worley cells, dark centers | pores, stippling, scattered spots |
| 3 Cellular 2 | cracked-plate network | dry earth, marble veining, crazing |
| 4 Cellular 3 | woven crosshatch grid | plaid, coarse fabric, basketry |
| 5 Cellular 4 | crystalline shard mesh | shattered / faceted stone |
| 6 Cellular 5 | soft diagonal weave | brushed cloth, quilted softness |
| 7 Cellular 6 | bright-cell network (inverse of C2) | raised mortar, cell walls |

Value and Perlin ARE close cousins (honest finding: don't expect variety
between those two). The Cellular family (2-7) is the untapped range, and it is
multi-octave, which plain `voronoi` is not: `fbm` noise=3 is the dry-earth /
marble vein look the stone cookbook built by hand from a `voronoi` donor, in one
node with `folds` and `iterations` to push it further.

**Cross-family characters `fbm` cannot make:**

| Node | Reads as | Reach for it when |
|---|---|---|
| `noise_anisotropic` | directional streaks (`scale_y` >> `scale_x`) | brushed metal, wood/fabric grain direction, hair |
| `truchet` (Line) | bold maze / chevron / circuit lines | circuit boards, mazes, woven tape, greebles |
| `truchet` (Circle) | interlocking pipes / worms | cables, tubing, organic interlock |
| `voronoi_triangle` | hex-ish faceted cells | scales, honeycomb, gems, foam |
| `wavelet_noise` | fine grainy salt-and-pepper | sand grain, static, sensor noise, fine tooth |
| `shard_fbm` | turbulent cloud AT DEFAULTS | NOT plug-and-play: push `sharp` up and `folds` for the crystalline look the name implies; at `sharp=0.7 folds=0` it reads soft |

**Two traps when auditing noise variety:**
- **Judge relief with `normal_map` `param4=0`.** With the default `param4=1`
  every analytic generator's normal comes back FLAT (the Phase 3C flat-normal
  blocker), so you would wrongly conclude the noise choice does not matter. It
  bites hardest in exactly this kind of comparison.
- **`fbm_variations` is not usable as-is.** Its enum labels come back as
  unresolved `$?1..$?4` placeholders in the catalog. Lead with `fbm` (whose
  enum resolves cleanly); check `fbm_variations`'s `.mmg` before featuring it.

For a soft, continuous material (velvet, felt, fog, skin), reach for
`perlin`/`fbm` first, not `voronoi`: voronoi's cell boundaries are inherently
hard-edged even when blurred at the color level, while perlin has no edges
to begin with.

## Node & pattern recipes

_Filled during 3C from the bundled examples + the miss taxonomy. Each recipe
names a base example and the edit that turns it toward a prompt._

### The recolor lever (highest payoff)

Many materials differ from a bundled example only in COLOR, not structure. A
`colorize` node holds a `gradient.points` list of `{pos, r, g, b, a}`. Find the
colorize whose points are **saturated** (not gray): that is the albedo color
ramp. The gray-valued colorize nodes feed roughness/height/metallic: leave them
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
  in normal+height), a HIT for red brick as-is; recolor for other brick tones.
- **Cracked ground**: `dry_earth` (voronoi plates + recessed cracks), a HIT for
  dry mud as-is.
- Planks: `wooden_floor` gives plank divisions but weak grain; the `wood`
  example has strong grain but no divisions. Oak planks wants BOTH (open item:
  needs a blend of plank cuts over strong grain).
- Hex cells (grating, hex tiles) are an open item: no single example ships a
  hexagon generator wired to a material; needs `shape`/`pattern` hex authored in.

## Common pitfalls (from the miss taxonomy)

- **Wrong nearest example**: the closest-named example often depicts a different
  material (e.g. `tiles` is fish-scale scallops, not hexagons; `marble` is veined
  + gold-framed, not speckled granite). Check the render, don't trust the name.
- **Albedo-only examples**: some examples (e.g. `paper`) emit only an albedo, no
  normal/height/orm, unusable under the "all four maps" rule. Build the material
  outputs explicitly.
- **Transient Godot crash**: renders intermittently die with exit `0xC0000005` /
  `0xC0000409` mid-export (GPU, not the graph). `render.py` now retries these
  transient codes up to 3x.
- **Normals need a SHARP-EDGED source (resolved)**: a hand-assembled
  `perlin -> normal_map -> Material.normal` chain renders a FLAT normal, and so
  does cloning a *smooth* example (`rock`). The fix that works: CLONE a working
  example whose generator has **sharp edges**: `dry_earth` (voronoi cracks)
  gives the `normal_map` real gradients to work from, so recoloring it to green
  produced a moss with rich ground relief (`o01`). Rule of thumb: for a material
  that needs surface relief, start from a sharp-edged example (cracks, bricks,
  cells), not a smooth blobby one. A smooth source (`rock`) is fine only when
  the target is genuinely near-flat, e.g. polished granite (`s02`).

## Cross-material lessons (lifted from the cookbook)

These lessons showed up while building specific per-material recipes, but
the lesson itself applies well beyond the material that surfaced it. The
per-material recipes now live as cards in `cookbook/`; these lessons stay
here because they are invariant guidance, not any one recipe's property.

**Pick the base generator by surface topology, not by grabbing a familiar
donor.** A first pass at four natural terrain materials (ice, lava, forest
floor, pebbles) cloned one donor, `dry_earth`'s voronoi-plate crack network,
for all four and recolored it. They all looked like siblings, the exact
"everything looks similar" trap the noise-vocabulary section above
quantifies. The fix was to pick the base by surface TOPOLOGY instead. Three
topologies come up repeatedly:

- Connected crack network (ice, lava): `dry_earth`'s voronoi-plate chain is
  correct, these surfaces genuinely crack into a joined network.
- Discrete packed cells (pebbles): voronoi cells are right, but the joints
  must read as recessed CONTACT shadow, not warped crack lines, so drop
  `warp_0` to around 0.02. That one change separates packed pebbles from
  cracked plates.
- Scattered overlapping pieces (forest floor, leaf litter): there is no
  connected network at all. Leave `dry_earth` entirely and re-base onto
  `fbm` with noise set to Cellular 4, the scattered clumpy-blob base from
  the noise gallery, not a cracked-plate look.

**Masonry diagnostics: `warp_0.amount` cuts both ways.** Across the
`dry_earth`-derived masonry materials, the single biggest lever is
`warp_0.amount`, and its effect is opposite depending on the target: on
paving (cobblestone, fieldstone, flagstone) it is haze to suppress, typically
dropped to around 0.12 for clean mortar with a little organic wobble; on
marble it is raised to around 0.5 and IS the intended look, the soft cloudy
veining. When a broad gray haze inside plates looks like it might be the
color gradient rather than the warp, use this diagnostic: re-render once
with a maximally high-contrast test gradient on the per-cell colorize. If
each plate goes a distinct flat color and the haze remains, the haze is the
warp, not the ramp.

Coursed, quarried masonry (ashlar) needs a different donor entirely: `Bricks`
port 1 gives per-brick random, the brick-node analogue of voronoi port 2, and
voronoi cannot produce coursed rectangles. Whenever the target is
quarried/coursed masonry rather than random rubble, reach for a `Bricks`
donor instead of a voronoi one.

**A `blend`'s opacity is `amount` times its port-2 mask.** In Material
Maker, `blend` shows its port-1 input where the port-2 mask is 0, and its
port-0 input where the mask is 1, so put the majority layer on port-1 and
drive the minority coverage through the mask. The opacity itself is
`amount * mask`, so never feed a mid-value albedo colorize into port 2 as
the opacity mask: a mid-value mask makes the top layer partly transparent no
matter what `amount` is, letting the layer underneath bleed through. Always
use a hard 0/1 mask for opacity, and keep a separate colorize driving color
if color and opacity need different shapes.

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
  generator: the switch cares about what the buffer actually renders, not the
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

Per-material recipes now live as cards beside their graphs: see cookbook/<category>/<id>.md (and cookbook/README.md).
