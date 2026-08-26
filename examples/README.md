# Example materials

> ⚠️ Super-alpha, artist-built with AI help. These are "good enough to finish in
> the app" at best, not photoreal. See the main README warning.

Each `<name>/<name>.ptex` is a real graph this server authored from a one-line
prompt. Open any of them in Material Maker to inspect or edit the node network,
or render it headlessly (see the repo README). The `images/` previews are the
downscaled albedo maps; rendering a `.ptex` produces full-resolution albedo,
normal, roughness/metallic (ORM), and height maps.

| Preview | Material | Prompt | How it was built |
|---|---|---|---|
| ![](images/s02_gray_granite.png) | Polished gray granite | "polished gray granite" | fine voronoi per-cell-random flecks (port 2) through a multi-tone gray ramp |
| ![](images/f01_woven_denim.png) | Woven denim | "blue denim fabric" | `diagonal_weave` grafted into a working normal chain; twill in the normal via the `normal_map` `param4=0` fix |
| ![](images/m01_weathered_copper.png) | Weathered copper | "weathered copper" | two-layer recolor: copper base + green verdigris patina masked in |
| ![](images/combo01_rusted_painted_steel.png) | Rusted painted steel | "rusted painted steel, paint peeling to bare metal" | flat paint coat blended over rust through an irregular peel mask |
| ![](images/man02_ceramic_hex_tiles.png) | Ceramic hex tiles | "white ceramic hexagon tiles" | `beehive` hex field driving white tile faces + thin dark grout |
| ![](images/m02_brushed_aluminum.png) | Brushed aluminum | "brushed aluminum" | straightened wood-grain clone: parallel directional streaks, forced metallic |
| ![](images/o01_mossy_forest_floor.png) | Mossy forest floor | "mossy forest floor" | cracked-ground clone recolored soil-to-moss |
| ![](images/s01_red_brick_wall.png) | Red brick wall | "red brick wall" | nearest bundled example, as-is |

These come from the Phase 3 quality test set (`quality/`), which currently passes
15/15 prompts by an artist's eyeball standard. The full scorecard lives in
`quality/scorecards/`.
