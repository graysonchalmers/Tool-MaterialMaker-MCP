# f07_herringbone_tweed - Herringbone tweed

_Category: fabrics. Open the graph: `cookbook/fabrics/f07_herringbone_tweed.ptex`._

A warm woven wool fabric with the classic herringbone chevron pattern:
diagonal ribbons that reverse direction band to band. This is the material
the wool-knit search found along the way, not a knit.

## Recipe

Retype the generator to `weave2` with `stitch=3` for the classic herringbone
chevron. `columns`/`rows` around 8, `width_x`/`width_y` around 0.8. Warm
brown Harris-tweed three-stop albedo (espresso, tan, cream) for a woven
two-tone heather look, very matte wool roughness (around 0.86 to 0.96), and a
soft `normal_map` `param1` around 0.35 with `param4=0` (directly-fed analytic
generator) so the chevron reads as pressed-tweed relief rather than sharp
thread crossings.

Honest limit: `weave2` emits one grayscale, so the tone comes from shading a
single ribbon shape, not two real thread colors, and it reads as a warm
one-tone weave. A true two-color tweed would need two colorizes blended
through the weave's own over/under mask.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
