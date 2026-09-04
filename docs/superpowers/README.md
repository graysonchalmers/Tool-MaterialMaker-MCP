# docs/superpowers/ - execution history (not current guidance)

This directory holds the specs and phased plans that drove past build
sessions, one file per feature under `specs/` and `plans/`. They are kept as
a record of how the project was built and why, not as living documentation.

For current guidance, read these instead:

- `CLAUDE.md` (repo root): standing instructions for a session.
- `HANDOFF.md`: the session baton (current state, next step).
- `STATUS.md`: the gate ledger.
- `docs/PLAN.md`: the phase plan and exit gates.
- `docs/AUTHORING.md`: the invariant authoring guide (also served as the
  `guide://authoring` MCP resource); per-material recipes live in each
  graph's card at `cookbook/<category>/<id>.md`.

A file here is frozen at the state it described when its session ended. Where
it disagrees with the code, the code is the truth. Treat these as archaeology,
useful for understanding a decision's original argument, not as a spec to
implement against today.
