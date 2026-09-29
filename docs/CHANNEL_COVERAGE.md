# Material channel coverage

Which Material Maker material inputs the cookbook actually drives, and which the
preview rig can show. Counted over the 55 cookbook graphs on 2026-09-29
(`Material` node input ports, `material.mmg` order). Recount after any
cookbook change; these are a to-do list for "feature-rich", not a goal in
themselves (see `NORTH_STAR.md`, "depth over breadth").

| Input | Graphs | In preview rig | Notes |
|---|---|---|---|
| albedo | 55 | yes | |
| normal | 53 | yes | m01 and combo01 have none. |
| roughness | 52 | yes (ORM) | |
| metallic | 32 | yes (ORM) | |
| depth / height | 9 | opt-in (Deep Parallax on the sphere) | Only s09's polarity was ever checked. |
| ao | 1 (s09) | yes (ORM red) | The rest export flat AO (red channel 255). |
| emission | 1 (t06) | **no** | `preview.gd` only takes albedo, normal, ORM, heightmap. t06's glow never shows in a preview. |
| sss | 0 | **no** | Same rig gap. |
| opacity | 1 (sf04) | yes (cutout only) | Rides in the albedo PNG's alpha. See below. |

## Opacity

- `opacity_tex` is `Material` input port 7. Set the node's `flags_transparent`
  parameter to true or the `.tres` will not enable transparency; the alpha is
  in `_albedo.png` either way.
- Material Maker's export writes `transparency = 1` (alpha BLEND). The preview
  rig instead uses alpha SCISSOR (threshold 0.5): hard-edged holes that cast
  real shadows. Faces are single-sided, so the far half of each shape is
  culled and a hole shows what is really behind it. (Double-sided would show
  the inside of the far wall through every hole.) The rook's hand-built lathe
  winds inward, so it uses CULL_FRONT for cutouts. It only applies when the albedo image really
  has alpha, so opaque materials are untouched.
- For a cutout the rig also adds a lit neutral-grey sheet under the ground, so
  the grate's holes show a floor and its shadows land on something instead of
  the black void.
- Keep opacity a hard 0/1 threshold off the SAME field that drives the
  height/normal, so the cut edge and the chamfer register.
- True translucency (soft alpha blend, glass) is a separate job: gl01 rework in
  `teardowns/TEARDOWN-2026-09-27.md`.

## Not representable at all

- **Clearcoat**: Material Maker's material has no clearcoat channel. The rig's
  clearcoat is preview-only and does not round-trip.
- **Anisotropy, displacement mesh**: no channel; depth is parallax only.
