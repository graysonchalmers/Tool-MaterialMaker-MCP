# North Star — Tool-MaterialMaker-MCP

Why this project exists, in one place, so it doesn't drift as features get
added. Read this before proposing new scope; if a change doesn't serve the
loop below, it probably belongs in a different project.

## The problem this is solving

[Material Maker](https://github.com/RodZill4/material-maker) is a genuinely
capable, free, open-source procedural texturing tool, on par in spirit with
paid node-graph authoring software, and it is underused relative to what it
can actually do. Its node graph is powerful but has real learning cost: an
empty canvas and ~400 node types is not an inviting place to start. This
project exists to lower that barrier by giving Material Maker a
natural-language front door.

## The loop this is built around

This is not a one-shot "type a prompt, get a texture" generator. The point is
a round trip:

1. You describe a material in a sentence.
2. The assistant drafts a node graph, validates and renders it, and hands
   back the maps plus an editable `.ptex`.
3. **You open that `.ptex` in Material Maker and look at the actual graph the
   assistant built** — the node types it chose, how they connect, which
   parameters it tuned. You tweak it, save a new version.
4. That new version can go back to the assistant to keep iterating, or stand
   on its own.

Step 3 is the part that makes this a learning tool, not just a productivity
one. Grayson is learning Material Maker's node vocabulary *by watching and
editing what gets authored for him*, not by reading docs cold. Every
generated graph is a worked example of "how would you build this in MM,"
sitting right there in the app, editable. That's deliberate, not a side
effect: an assistant that only handed back flattened PNGs with no graph would
not serve this goal, even if the images looked better.

Phase 5 (live-control, speced but not built — see
`docs/superpowers/specs/2026-08-26-live-control-addon-design.md`) deepens the
same loop rather than replacing it: watching nodes appear in the live app as
the assistant builds them, instead of via file hand-off, is the same
"watch and learn the graph" idea in real time.

## Who this is for

Primarily Grayson, right now — this is a "me-first" tool per the project's
own conventions, built for one person's actual workflow before anyone else's.
Secondarily, anyone who finds the public repo and wants a lower-friction way
into Material Maker than an empty node graph. It is explicitly not built for
an audience that just wants finished textures with no interest in the
underlying tool.

## Non-goals

- **Not chasing photoreal quality.** The bar is "gets you most of the way
  there, you finish it in the app," not production-grade. See the `quality/`
  scorecard for the honest current hit rate.
- **Not replacing Material Maker's own UI.** This automates the parts that
  are tedious to start from scratch (blank-canvas node selection), not the
  parts where hands-on tweaking is the point.
- **Not a fully autonomous pipeline.** The human finishing and owning the
  graph in step 3 above is load-bearing, not a placeholder for "eventually
  we'll skip this step."
