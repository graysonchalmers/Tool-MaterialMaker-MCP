"""The Phase-3 gate (15/15 on the frozen 15-case set, 2026-08-26) is closed.
Its apparatus is archived under docs/evidence/phase3/ as a record, not as a
live harness: the runner is retired and quality/ no longer carries it."""
import hashlib
import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EVIDENCE = os.path.join(_ROOT, "docs", "evidence", "phase3")

TEST_SET_SHA256 = "482f25424a1e8427797f9d00c941c234991004471ba11f9c54faa67f0d323ddd"


def test_frozen_test_set_is_archived_unchanged():
    with open(os.path.join(_EVIDENCE, "test_set.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["_meta"]["frozen"] is True
    assert data["_meta"]["frozen_date"] == "2026-08-26"
    assert data["_meta"]["case_count"] == 15
    assert len(data["cases"]) == 15


def test_frozen_test_set_bytes_are_pinned():
    """freeze-rule.md forbids editing any case or the rubric; the metadata
    checks above cannot see a changed must_have line, a hash can."""
    path = os.path.join(_EVIDENCE, "test_set.json")
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    assert digest == TEST_SET_SHA256, "docs/evidence/phase3/test_set.json changed; the Phase-3 set is frozen"


def test_scorecards_and_freeze_rule_are_archived():
    for name in ("2026-08-26-baseline.md", "2026-08-26-iter1.md", "freeze-rule.md", "README.md"):
        assert os.path.isfile(os.path.join(_EVIDENCE, name)), name


def test_phase3_runner_is_retired_from_quality():
    for name in ("run_case.py", "score_baseline.py", "verify_hero_fold.py", "test_set.json"):
        assert not os.path.exists(os.path.join(_ROOT, "quality", name)), f"quality/{name} should be gone"
    assert not os.path.isdir(os.path.join(_ROOT, "quality", "scorecards"))
