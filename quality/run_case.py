"""Phase 3 quality harness: render authored variants for a test-set case and
(re)build the run scorecard.

Claude authors 2-3 variant .ptex graphs per prompt (that authoring is the thing
Phase 3 measures). This harness automates everything around it: validate + render
each variant at a fixed size, lay the outputs out under
quality/runs/<run>/<case_id>/variant_N/, and regenerate a Markdown scorecard from
the per-case result files so re-running a case never duplicates rows.

It reuses mm_mcp.validator + mm_mcp.render; it adds no render logic of its own.

Usage (PowerShell 5.1):
  # render one case's variants into a run, then rebuild that run's scorecard
  & "C:\\Program Files\\Python313\\python.exe" quality\\run_case.py `
      --run 2026-08-26-baseline --case m01_weathered_copper `
      --variants v1.ptex v2.ptex v3.ptex --size 512

  # just rebuild the scorecard from whatever cases have been rendered
  & "C:\\Program Files\\Python313\\python.exe" quality\\run_case.py `
      --run 2026-08-26-baseline --rebuild-scorecard
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from mm_mcp.config import load_config
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.validator import validate_graph
from mm_mcp.render import render

_QUALITY = _ROOT / "quality"
_RUNS = _QUALITY / "runs"
_TEST_SET = _QUALITY / "test_set.json"


def _load_test_set() -> dict:
    with open(_TEST_SET, encoding="utf-8") as fh:
        return json.load(fh)


def _find_case(test_set: dict, case_id: str) -> dict:
    for c in test_set["cases"]:
        if c["id"] == case_id:
            return c
    raise SystemExit(f"case '{case_id}' not found in test_set.json")


def _load_ptex(src: str) -> dict:
    """A variant source is a path to a .ptex/.json file OR inline JSON."""
    p = Path(src)
    if p.exists():
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return json.loads(src)


def render_variants(run_label: str, case_id: str, variant_srcs: list[str],
                    size: int = 512) -> dict:
    """Render every variant for one case; write outputs + a _result.json.

    Returns the result dict that also gets persisted to the case dir.
    """
    cfg = load_config()
    catalog = build_catalog(cfg.nodes_dir)
    test_set = _load_test_set()
    case = _find_case(test_set, case_id)

    case_dir = _RUNS / run_label / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    variants = []
    for i, src in enumerate(variant_srcs, start=1):
        vdir = case_dir / f"variant_{i}"
        vdir.mkdir(parents=True, exist_ok=True)
        try:
            ptex = _load_ptex(src)
        except (json.JSONDecodeError, OSError) as exc:
            variants.append({"n": i, "ok": False, "error": f"bad source: {exc}",
                             "images": [], "problems": []})
            continue

        problems = validate_graph(ptex, catalog)
        errors = [p for p in problems if p["severity"] == "error"]
        # persist the source graph next to its render for later inspection
        with open(vdir / "source.ptex", "w", encoding="utf-8") as fh:
            json.dump(ptex, fh, indent=1)

        if errors:
            variants.append({"n": i, "ok": False, "error": "validation failed",
                             "images": [], "problems": errors})
            continue

        result = render(ptex, size=size, outdir=str(vdir),
                        basename=case_id, cfg=cfg)
        # normalize image paths to be relative to the quality/ dir for the card
        rel_images = [str(Path(img).resolve().relative_to(_QUALITY.resolve()))
                      for img in result.images]
        variants.append({
            "n": i, "ok": result.ok,
            "error": result.error, "images": rel_images,
            "log_tail": result.log_tail if not result.ok else "",
            "problems": [p for p in problems if p["severity"] == "warning"],
        })

    result_doc = {
        "case_id": case_id,
        "prompt": case["prompt"],
        "category": case["category"],
        "must_have": case["must_have"],
        "must_not": case["must_not"],
        "size": size,
        "variants": variants,
        # verdict fields are filled by the judge (Claude vision), then audited.
        "verdict": {
            "case_hit": None,
            "variant_verdicts": {str(v["n"]): None for v in variants},
            "notes": "",
        },
    }
    with open(case_dir / "_result.json", "w", encoding="utf-8") as fh:
        json.dump(result_doc, fh, indent=2)
    return result_doc


def _case_results(run_dir: Path) -> list[dict]:
    docs = []
    for rj in sorted(run_dir.glob("*/_result.json")):
        with open(rj, encoding="utf-8") as fh:
            docs.append(json.load(fh))
    return docs


def write_scorecard(run_label: str) -> Path:
    """Regenerate scorecards/<run>.md from every case's _result.json."""
    run_dir = _RUNS / run_label
    docs = _case_results(run_dir)
    scorecards = _QUALITY / "scorecards"
    scorecards.mkdir(parents=True, exist_ok=True)
    out = scorecards / f"{run_label}.md"

    total = len(docs)
    scored = [d for d in docs if d["verdict"]["case_hit"] is not None]
    hits = [d for d in scored if d["verdict"]["case_hit"] is True]
    rate = f"{len(hits)}/{total}" if total else "0/0"
    pct = f"{100 * len(hits) / total:.0f}%" if total else "n/a"

    lines = [
        f"# Scorecard: {run_label}",
        "",
        f"_Auto-generated by run_case.py. Verdict fields come from the judge in "
        f"each case's `runs/{run_label}/<case>/_result.json` (edit there, then "
        f"rebuild)._",
        "",
        f"**Cases:** {total}  ·  **Scored:** {len(scored)}  ·  "
        f"**Hit-rate:** {rate} ({pct})  ·  **Gate:** >= 70% (>= 11/15)",
        "",
        "| Case | Prompt | Category | Variants rendered | Case verdict |",
        "|---|---|---|---|---|",
    ]
    for d in docs:
        v = d["verdict"]
        rendered = sum(1 for x in d["variants"] if x["ok"])
        vtotal = len(d["variants"])
        hit = v["case_hit"]
        verdict = "HIT" if hit is True else "MISS" if hit is False else "_unscored_"
        lines.append(
            f"| `{d['case_id']}` | {d['prompt']} | {d['category']} | "
            f"{rendered}/{vtotal} ok | {verdict} |"
        )

    # Per-case detail with evidence paths + miss-taxonomy prompt.
    lines += ["", "## Per-case detail", ""]
    for d in docs:
        v = d["verdict"]
        hit = v["case_hit"]
        verdict = "HIT" if hit is True else "MISS" if hit is False else "unscored"
        lines += [
            f"### `{d['case_id']}` — {d['prompt']}  ({verdict})",
            "",
            "must_have: " + "; ".join(d["must_have"]),
            "",
            "must_not: " + "; ".join(d["must_not"]),
            "",
        ]
        for x in d["variants"]:
            status = "ok" if x["ok"] else f"FAILED ({x['error']})"
            vv = v["variant_verdicts"].get(str(x["n"]))
            vvtxt = "usable" if vv is True else "not usable" if vv is False else "unscored"
            imgs = ", ".join(f"`{i}`" for i in x["images"]) or "(none)"
            lines.append(f"- variant {x['n']}: render {status}; judge: {vvtxt}")
            lines.append(f"  - maps: {imgs}")
            if x["problems"]:
                warns = "; ".join(p["message"] for p in x["problems"])
                lines.append(f"  - warnings: {warns}")
        if v["notes"]:
            lines += ["", f"miss/why: {v['notes']}"]
        lines.append("")

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 3 quality harness")
    ap.add_argument("--run", required=True, help="run label, e.g. 2026-08-26-baseline")
    ap.add_argument("--case", help="test-set case id to render")
    ap.add_argument("--variants", nargs="+", default=[],
                    help="2-3 variant .ptex paths (or inline JSON strings)")
    ap.add_argument("--size", type=int, default=512, help="render size (px)")
    ap.add_argument("--rebuild-scorecard", action="store_true",
                    help="skip rendering; just regenerate the scorecard")
    args = ap.parse_args()

    if not args.rebuild_scorecard:
        if not args.case or not args.variants:
            ap.error("--case and --variants are required unless --rebuild-scorecard")
        doc = render_variants(args.run, args.case, args.variants, size=args.size)
        ok = sum(1 for v in doc["variants"] if v["ok"])
        print(f"rendered case {args.case}: {ok}/{len(doc['variants'])} variants ok")

    card = write_scorecard(args.run)
    print(f"scorecard: {card}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
