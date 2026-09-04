# pm02_automotive_enamel - Automotive enamel, deep red

_Category: painted-metal. Open the graph: `cookbook/painted-metal/pm02_automotive_enamel.ptex`._

A near-mirror deep red clearcoat with a faint metallic-flake sparkle, distinct from pm01's matte pebbling and pm04's dimpled hammertone.

## Recipe

Clones `rock`. Albedo is driven off `voronoi_0`'s per-cell random (port 2, rand3) at a very fine scale (60) so each tiny cell is a slightly different red, giving the faint metallic-flake sparkle. Very low roughness (0.07 to 0.11) produces the near-mirror clearcoat with a sharp specular highlight on the preview sphere, near-flat normal (`param1` 0.04) for the glassy coat, and metallic stays 0 since the dielectric clearcoat, not a metal surface, dominates the visible response.

Pitfall: the flake speckle reads a touch sandy on the matte faces of the preview geometry. If a cleaner enamel is wanted, drop the albedo spread or the fleck scale.

## See also

The invariant guide (`guide://authoring` resource, or `docs/AUTHORING.md`) for
the rubric, the authoring workflow, the noise vocabulary, and the `param4=0`
flat-normal fix.
