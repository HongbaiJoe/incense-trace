"""Freeze Cycle 4 cross-source results and analysis."""

from __future__ import annotations

import hashlib
import json

from xiangji.data import RESEARCH_ROOT


FILES = (
    "src/xiangji/evaluation/primary.py",
    "src/xiangji/evaluation/robustness.py",
    "src/xiangji/evaluation/hong_confirmation.py",
    "experiments/cycle4_primary_evaluation.json",
    "experiments/cycle4_primary_records.json.gz",
    "experiments/cycle4_robustness.json",
    "experiments/cycle4_hong_confirmation.json",
    "experiments/cycle4_hong_records.json.gz",
    "reports/cycle4_completion.md",
)


def build_manifest() -> dict:
    primary = json.loads((RESEARCH_ROOT / "experiments/cycle4_primary_evaluation.json").read_text())
    robustness = json.loads((RESEARCH_ROOT / "experiments/cycle4_robustness.json").read_text())
    hong = json.loads((RESEARCH_ROOT / "experiments/cycle4_hong_confirmation.json").read_text())
    if primary["primary_result_used_for_model_changes"] is not False:
        raise ValueError("Primary results changed the model")
    if robustness["model_parameters_changed_after_primary_result"] is not False:
        raise ValueError("Robustness results changed the model")
    if hong["model_parameters_changed_after_primary_evaluation"] is not False:
        raise ValueError("Hong confirmation changed the model")
    missing = [name for name in FILES if not (RESEARCH_ROOT / name).exists()]
    if missing:
        raise FileNotFoundError(f"Cycle 4 files missing: {missing}")
    return {
        "schema_version": "0.1",
        "checkpoint": "cycle4_cross_source_evaluation",
        "model_parameters_changed": False,
        "primary_two_work_folds_accessed": True,
        "Hong_source_accessed_for_confirmation": True,
        "investigator_blinded": False,
        "files": [
            {
                "path": name,
                "sha256": hashlib.sha256((RESEARCH_ROOT / name).read_bytes()).hexdigest(),
            }
            for name in FILES
        ],
    }


def main() -> None:
    result = build_manifest()
    target = RESEARCH_ROOT / "reports/cycle4_release_manifest.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), "file_count": len(result["files"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
