# pm03_chipped_paint - Paint chipped to bare metal

_Category: painted-metal. Open the graph: `cookbook/painted-metal/pm03_chipped_paint.ptex`._

Flat green paint over bare steel, chipped through to exposed metal in scattered worn spots. Distinct from the frozen `combo01_rusted_painted_steel` on purpose: that recipe chips paint to rust, this one chips to bare metal, so the two should never be read as duplicates.

## Recipe

Clones `rusted_metal` for its ready-made two-layer metal base, recolors that base to bare steel, then composites a flat green paint coat over it through one hard chip mask (perlin thresholded at roughly less than 0.30 for the minority worn spots). The green paint is wired as the majority coverage, with the chip mask driving bare metal only in the sparse worn spots. The same hard mask also drives metallic (Material port 1: metal chips = 1, paint = 0) and a chip-edge normal step so the paint sits physically proud of the chips.

Pitfall specific to this material: getting the mask wiring right took two passes. The first attempt was inverted, with metal as the majority and green paint only in the pits, which read as corroded metal rather than chipped paint. A second pass over-corrected to nearly all-metal before the wiring that puts paint as the dominant layer and metal only in the masked minority spots was pinned down. Metallic being masked per-pixel rather than a single global value is what makes the exposed chips read as real bright steel rather than dull painted metal.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
