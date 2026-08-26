"""One-off: write the 3B baseline verdicts into each case's _result.json, then
rebuild the scorecard. Verdicts are Claude-vision judgments against the frozen
rubric (Grayson audits). Kept in-repo so the baseline is reproducible/auditable.
"""
import json
import sys
from pathlib import Path

RUN = "2026-08-26-baseline"
ROOT = Path(__file__).resolve().parent.parent
RUNDIR = ROOT / "quality" / "runs" / RUN

# case_id -> (case_hit, variant1_usable, miss_category, notes)
# miss_category taxonomy (the 3C worklist):
#   wrong-example         nearest example depicts a different material
#   recolor-only          right structure, wrong color (cheap fix)
#   missing-composite     needs a multi-node pattern no single example gives
#   weak-attribute        criterion present but too weak to pass
#   render-broken         example emits too few maps / broken output
VERDICTS = {
    "m01_weathered_copper": (False, False, "missing-composite",
        "rusted_metal reads as rust: orange base, NO green/teal verdigris, base is not copper. Needs copper base color + verdigris patina ramp masked into recesses."),
    "m02_brushed_aluminum": (False, False, "wrong-example",
        "metal_pattern is diamond tread-plate, not brushed. No directional streaking; tone is brownish not neutral gray. Needs stretched/anisotropic noise for streaks + neutral colorize."),
    "m03_rusted_iron": (True, True, "",
        "rusted_metal IS rusted iron: orange-brown rust patches over darker metal, pitted/rough. Clean HIT."),
    "s01_red_brick_wall": (True, True, "",
        "bricks example: running-bond coursing, recessed gray mortar in normal+albedo, red/brown bricks. Clean HIT."),
    "s02_gray_granite": (False, False, "wrong-example",
        "marble example renders high-contrast black/white veining framed in gold tiles: veined + tiled + gold, not speckled gray granite. Needs fine multi-tone speckle noise, neutral gray, low roughness."),
    "s03_cracked_concrete": (False, False, "wrong-example",
        "stone_wall is a mortared block wall (tan blocks + gray mortar), a tile pattern (must_not). Needs a cracked-surface generator (voronoi cracks) over a gray rough base, no coursing."),
    "w01_oak_planks": (False, False, "weak-attribute",
        "wooden_floor: plank divisions + warm brown are good, but directional grain is too soft/absent. Closest near-hit. Note: the 'wood' example grain (see w02) is far stronger; combine plank layout + strong grain."),
    "w02_weathered_barn_wood": (False, False, "recolor-only",
        "wood example has excellent directional grain + knots, but color is vivid saturated orange (must_not), not faded weathered gray. Desaturate + shift toward gray-brown; raise roughness."),
    "f01_woven_denim": (False, False, "render-broken",
        "paper example emits ONLY albedo (no normal/height/orm) and shows no woven twill. Fails 'all four maps' + no weave. Needs a fabric weave pattern with a real normal."),
    "f02_brown_leather": (False, False, "recolor-only",
        "crocodile_skin cellular grain is a good leather structure, but renders green. Recolor ramp to warm brown; otherwise structurally close."),
    "o01_mossy_forest_floor": (False, False, "wrong-example",
        "clump_of_grass is a single centered grass tuft on flat green (a decal), not a tiling ground. Needs tiling moss+soil: green moss blobs over darker earth base with bumpy relief."),
    "o02_cracked_dry_mud": (True, True, "",
        "dry_earth: polygonal cracked plates, dark recessed cracks, tan/brown matte. Clean HIT."),
    "man01_metal_grating": (False, False, "missing-composite",
        "metal_pattern is diamond tread-plate studs, not hexagonal cells/holes. Needs a hex generator (shape/pattern hexagon) with recessed holes over metal."),
    "man02_ceramic_hex_tiles": (False, False, "wrong-example",
        "tiles example is an orange fish-scale scallop, not white hexagons with grout. Needs hexagon tile generator + white glazed faces (low roughness) + darker/rougher grout."),
    "combo01_rusted_painted_steel": (False, False, "missing-composite",
        "rusted_metal has rust+metal but NO paint layer, so no peel. Needs a flat colored paint coat blended over rust via an irregular peel mask, with roughness contrast."),
}


def main() -> int:
    missing = []
    for case_id, (hit, v1, cat, notes) in VERDICTS.items():
        rj = RUNDIR / case_id / "_result.json"
        if not rj.exists():
            missing.append(case_id)
            continue
        doc = json.loads(rj.read_text(encoding="utf-8"))
        doc["verdict"]["case_hit"] = hit
        # variant 1 is the only variant in the baseline
        doc["verdict"]["variant_verdicts"] = {"1": v1}
        doc["verdict"]["notes"] = (f"[{cat}] " if cat else "") + notes
        rj.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    if missing:
        print("MISSING result files:", missing)
        return 1
    hits = sum(1 for v in VERDICTS.values() if v[0])
    print(f"scored {len(VERDICTS)} cases; hits={hits}/{len(VERDICTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
