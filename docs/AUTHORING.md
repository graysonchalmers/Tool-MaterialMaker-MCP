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

_(Filled during 3C — mined from the ~100 bundled examples. Empty by design for
the 3B baseline.)_

### Base tones & color

### Surface pattern generators (brick, tile, hex, planks)

### Weathering & edge wear (rust, patina, peeling, dirt)

### Normal / height / roughness pairing

## Common pitfalls

_(Filled during 3C from the miss taxonomy.)_
