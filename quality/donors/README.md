# quality/donors/

Vendored copies of 9 Material Maker bundled example graphs, copied
byte-for-byte from `<MM_PROJECT_PATH>/material_maker/examples/*.ptex`
(the external Material Maker checkout, not part of this repo).

These are upstream Material Maker content, not first-party recipes. They
have no recipe cards and are not part of `cookbook/`. They exist because
`quality/author.py`'s Phase 3 case builders and `quality/cookbook_<category>.py`
use them as starting graphs (`author_helpers.load_example(name)`), and
vendoring them removes the authoring pipeline's dependency on the external
checkout being present at a specific path.

Files: `beehive.ptex`, `crocodile_skin.ptex`, `dry_earth.ptex`,
`metal_pattern_2.ptex`, `rock.ptex`, `rusted_metal.ptex`, `stone_wall.ptex`,
`wood.ptex`, `wooden_floor.ptex`.

Browsing Material Maker's full bundled example library (all 43, not just
these 9) is unaffected by this folder: `list_examples(source="material_maker")`
and the Phase 1 gate test (`tests/test_examples_gate.py`) still read live from
the external checkout's `cfg.examples_dir`, unchanged.
