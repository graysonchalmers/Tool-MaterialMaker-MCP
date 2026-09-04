# o04_snake_scales - Snake scales

_Category: organics. Open the graph: `cookbook/organics/o04_snake_scales.ptex`._

An olive-to-khaki reptile scale surface with faceted per-cell relief that
reads as scales through the normal map rather than the albedo.

## Recipe

`crocodile_skin`'s own default voronoi cellular pattern IS already a
reptile-scale layout, that's what it was built to look like, so no retype is
needed: pure recolor lever (olive to khaki, lower roughness than leather for
a scale sheen). Proactively apply the `param4=0` fix even though it wasn't
strictly required for the reference leather HIT: `crocodile_skin`'s normal
chain (`voronoi_0` to `colorize_0` to `normal_map_0`) is directly-fed with no
buffer, the same shape as the classic denim blocker, so it renders flat by
default. The faceted per-cell relief this produces is a better tell for
"scales" than the albedo, which stays fairly soft and blurred by the donor's
own design, and for this material that's fine: the read comes through the
normal, not the color.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
