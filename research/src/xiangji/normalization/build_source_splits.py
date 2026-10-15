"""Freeze family-safe, source-blocked evaluation indices for Formula Reference v0.1."""

from __future__ import annotations

import hashlib
import itertools
import json

from xiangji.data import RESEARCH_ROOT

SEALED_WORK = "hong_xiangpu_attributed"


def ids_for_works(records: list[dict], works: set[str]) -> list[str]:
    return sorted(row["reference_id"] for row in records if row["work_id"] in works)


def assert_partition(records: list[dict], train_ids: list[str], test_ids: list[str], test_works: set[str]) -> None:
    by_id = {row["reference_id"]: row for row in records}
    if set(train_ids) & set(test_ids):
        raise ValueError("Train/test reference IDs overlap")
    train_families = {by_id[row_id]["formula_family_id"] for row_id in train_ids}
    test_families = {by_id[row_id]["formula_family_id"] for row_id in test_ids}
    if train_families & test_families:
        raise ValueError("Train/test formula families overlap")
    if {by_id[row_id]["work_id"] for row_id in test_ids} != test_works:
        raise ValueError("Test work IDs do not match the declared source block")
    if {by_id[row_id]["work_id"] for row_id in train_ids} & test_works:
        raise ValueError("A held-out work appears in training")


def build_splits(reference: dict) -> dict:
    records = reference["records"]
    works = sorted({row["work_id"] for row in records})
    if SEALED_WORK not in works:
        raise ValueError(f"Sealed work {SEALED_WORK} is absent")
    development_works = [work for work in works if work != SEALED_WORK]
    sealed_ids = ids_for_works(records, {SEALED_WORK})

    development_folds = []
    for test_work in development_works:
        test_works = {test_work}
        train_works = set(development_works) - test_works
        train_ids = ids_for_works(records, train_works)
        test_ids = ids_for_works(records, test_works)
        assert_partition(records, train_ids, test_ids, test_works)
        development_folds.append({
            "fold_id": f"dev_lowo_{len(development_folds) + 1:02d}",
            "train_work_ids": sorted(train_works),
            "test_work_ids": sorted(test_works),
            "train_reference_ids": train_ids,
            "test_reference_ids": test_ids,
        })

    primary_folds = []
    for test_pair in itertools.combinations(development_works, 2):
        test_works = set(test_pair)
        train_works = set(development_works) - test_works
        train_ids = ids_for_works(records, train_works)
        test_ids = ids_for_works(records, test_works)
        assert_partition(records, train_ids, test_ids, test_works)
        primary_folds.append({
            "fold_id": f"primary_two_source_{len(primary_folds) + 1:02d}",
            "train_work_ids": sorted(train_works),
            "test_work_ids": sorted(test_works),
            "train_reference_ids": train_ids,
            "test_reference_ids": test_ids,
        })

    return {
        "schema_version": "0.1",
        "reference_record_count": len(records),
        "family_blocking": "one curated representative per formula family; family IDs are asserted disjoint",
        "source_blocking": "entire work IDs are held out; no record-level random split is provided",
        "sealed_evaluation": {
            "work_id": SEALED_WORK,
            "reference_ids": sealed_ids,
            "record_count": len(sealed_ids),
            "access_rule": "Do not evaluate or tune on this source until the model, thresholds and analysis code are frozen after Cycle 4.",
        },
        "development_leave_one_work_out_folds": development_folds,
        "primary_two_unseen_work_folds": primary_folds,
        "notes": "The two-record Moe Xiaolu group is retained and reported transparently; macro source summaries must accompany pooled metrics.",
    }


def main() -> None:
    reference_path = RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    output = build_splits(reference)
    output["reference_sha256"] = hashlib.sha256(reference_path.read_bytes()).hexdigest()
    target = RESEARCH_ROOT / "data" / "curated" / "source_blocked_splits_v0.1.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "sealed_records": output["sealed_evaluation"]["record_count"],
        "development_folds": len(output["development_leave_one_work_out_folds"]),
        "primary_folds": len(output["primary_two_unseen_work_folds"]),
        "output": str(target),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
