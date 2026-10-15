import json

from xiangji.data import RESEARCH_ROOT
from xiangji.normalization.build_source_splits import SEALED_WORK, build_splits


def mock_reference():
    records = []
    for work in [SEALED_WORK, "a", "b", "c", "d", "e"]:
        for index in range(2):
            records.append({
                "reference_id": f"{work}-{index}",
                "formula_family_id": f"family-{work}-{index}",
                "work_id": work,
            })
    return {"records": records}


def test_source_splits_hold_out_whole_works_and_keep_sealed_source_absent():
    payload = build_splits(mock_reference())
    sealed = set(payload["sealed_evaluation"]["reference_ids"])
    assert len(payload["development_leave_one_work_out_folds"]) == 5
    assert len(payload["primary_two_unseen_work_folds"]) == 10
    for fold in payload["primary_two_unseen_work_folds"]:
        assert len(fold["test_work_ids"]) == 2
        assert sealed.isdisjoint(fold["train_reference_ids"])
        assert sealed.isdisjoint(fold["test_reference_ids"])


def test_generated_splits_cover_reference_without_family_leakage():
    split_path = RESEARCH_ROOT / "data" / "curated" / "source_blocked_splits_v0.1.json"
    reference_path = RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
    if not split_path.exists() or not reference_path.exists():
        return
    split = json.loads(split_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    by_id = {row["reference_id"]: row for row in reference["records"]}
    sealed = set(split["sealed_evaluation"]["reference_ids"])
    assert split["sealed_evaluation"]["record_count"] == len(sealed) > 0
    for fold in split["primary_two_unseen_work_folds"]:
        train, test = set(fold["train_reference_ids"]), set(fold["test_reference_ids"])
        assert train.isdisjoint(test | sealed)
        assert {by_id[row_id]["formula_family_id"] for row_id in train}.isdisjoint(
            {by_id[row_id]["formula_family_id"] for row_id in test}
        )
        assert {by_id[row_id]["work_id"] for row_id in test} == set(fold["test_work_ids"])
