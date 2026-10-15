"""Generate record-level failure cases from stored, held-out predictions."""

from __future__ import annotations

import json

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.metrics import evaluate


def main() -> None:
    source = RESEARCH_ROOT / "experiments" / "baseline_results.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    records: dict[str, list[dict]] = {}
    for fold in payload["leave_one_family_out"]["fold_records"]:
        truth = np.asarray(fold["truth"]["outcomes"])
        ids = fold["truth"]["ids"]
        for model, matrix in fold["predictions"].items():
            scores = np.asarray(matrix)
            for i, record_id in enumerate(ids):
                row = evaluate(truth[i : i + 1], scores[i : i + 1])
                records.setdefault(model, []).append({
                    "record_id": record_id,
                    "held_out_family": fold["held_out_family"],
                    "weighted_jaccard": row["weighted_jaccard"],
                    "recall_at_6": row["recall_at_6"],
                    "union_ratio_mae": row["union_ratio_mae"],
                })

    report = {
        "protocol": "Record-level errors from leave-one-style-family-out predictions.",
        "worst_five_by_weighted_jaccard": {
            model: sorted(rows, key=lambda row: row["weighted_jaccard"])[:5]
            for model, rows in records.items()
        },
        "best_five_by_weighted_jaccard": {
            model: sorted(rows, key=lambda row: row["weighted_jaccard"], reverse=True)[:5]
            for model, rows in records.items()
        },
    }
    output = RESEARCH_ROOT / "reports" / "cycle1_error_analysis.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["worst_five_by_weighted_jaccard"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
