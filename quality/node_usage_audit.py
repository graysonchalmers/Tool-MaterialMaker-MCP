"""Audit which Material Maker generator nodes the cookbook actually uses,
recursing into the subgraph wrappers every cookbook material is grouped
into (quality.author_helpers.group_into_subgraph), so role-named nodes one
level down are counted correctly -- the same descent src/mm_mcp/validator.py
uses to check subgraph internals.

Why this exists: the 2026-09-01 "everything looks similar" histogram (see
docs/AUTHORING.md's Noise vocabulary section) was a one-time manual grep
against 38 builders. By the 2026-09-13 pickup session it was already stale
(59 materials existed by then, then 65 after this round) and had to be
re-derived by hand from a live recursive walk. This script makes that
number live: run it any time to see exactly which noise/pattern generators
the CURRENT cookbook uses and which are still untouched.

_NOISE_PATTERN_NODES is a curated list of Material Maker's scalar-field
noise/pattern GENERATOR node type names, matching the scope of
AUTHORING.md's "Noise vocabulary" section. It deliberately excludes:
distortion/warp nodes (AUTHORING.md's separate "Distortion vocabulary"
section covers those), the SDF family (ruled out of scope entirely, see
AUTHORING.md), and symbolic/glyph generators (roman_numerals, seven_segment,
sixteen_segment, runes, iching, japanese_glyphs, cairo -- decorative
tile-text nodes, not noise). Material Maker's .mmg node files carry no
machine-readable category field (verified against the pinned MM checkout),
so this list is maintained by hand here, the same way the SDF-family count
in AUTHORING.md is a manual tally. Update it if the MM node set changes.

Test-enforcement is one-directional: `tests/test_node_usage_audit.py` asserts
every name in `_NOISE_PATTERN_NODES` is a real node type in the current
Material Maker catalog (catches typos, deletions, stale names), but it does
NOT assert the set is complete -- whether some other real generator node
(e.g. `arc_pavement`, `pixels`, `pixels_smooth`) belongs in scope stays a
manual judgment call, not something a test can decide.

Run: python -m quality.node_usage_audit
"""
import json
from collections import Counter, defaultdict

from mm_mcp.config import load_config
from mm_mcp.cookbook import list_cookbook

_NOISE_PATTERN_NODES = frozenset({
    "beehive", "beehive2",
    "bricks", "bricks_nontileable", "bricks_uneven", "bricks_uneven2",
    "bricks_uneven2_2", "bricks_uneven3", "bricks_uneven3_2", "bricks_uneven4",
    "bricks2", "bricks3",
    "circle_splatter", "circle_splatter_color",
    "clouds_noise", "color_noise", "crystal", "custom_tiles",
    "diagonal_weave", "dirt", "directional_noise",
    "fbm", "fbm_variations", "fbm2", "fbm3", "fbm4",
    "noise", "noise_anisotropic", "noise_color", "noise_white", "noise2",
    "pattern",
    "perlin", "perlin_color",
    "scratches", "scratches2",
    "shard_fbm", "sine_wave",
    "skewed_bricks", "skewed_uneven_bricks",
    "spiral_gradient",
    "splatter", "splatter_color",
    "truchet", "truchet_generic",
    "voronoi", "voronoi_triangle", "voronoi2",
    "wavelet_noise", "wavelet_noise2",
    "weave", "weave2", "weave_random",
})


def _walk(nodes: list, counts: Counter) -> None:
    for n in nodes:
        t = n.get("type")
        if t:
            counts[t] += 1
        if t == "graph" and "nodes" in n:
            _walk(n["nodes"], counts)


def audit(cookbook_dir: str | None = None) -> dict:
    cookbook_dir = cookbook_dir or load_config().cookbook_dir
    counts: Counter = Counter()
    materials_by_type: "defaultdict[str, list]" = defaultdict(list)
    for entry in list_cookbook(cookbook_dir):
        with open(entry.path, encoding="utf-8") as fh:
            graph = json.load(fh)
        per_material: Counter = Counter()
        _walk(graph.get("nodes", []), per_material)
        for t, n in per_material.items():
            counts[t] += n
            materials_by_type[t].append(entry.name)
    for t in materials_by_type:
        materials_by_type[t].sort()
    used = {t for t in counts if t in _NOISE_PATTERN_NODES}
    return {
        "counts": counts,
        "materials_by_type": dict(materials_by_type),
        "noise_used": sorted(used),
        "noise_unused": sorted(_NOISE_PATTERN_NODES - used),
    }


def main() -> int:
    report = audit()
    used = report["noise_used"]
    print(f"Noise/pattern generators in use: {len(used)} of {len(_NOISE_PATTERN_NODES)}")
    for t in used:
        mats = report["materials_by_type"][t]
        print(f"  {t}: {report['counts'][t]} instance(s) across {len(mats)} material(s) ({', '.join(mats)})")
    print(f"\nStill unused ({len(report['noise_unused'])}):")
    for t in report["noise_unused"]:
        print(f"  {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
