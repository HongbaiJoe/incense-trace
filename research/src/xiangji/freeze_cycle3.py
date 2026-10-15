"""Freeze the Cycle 3 model checkpoint and its reproducibility-critical files."""

from __future__ import annotations

import hashlib
import json

from xiangji.data import RESEARCH_ROOT


FILES = (
    "configs/model/xiangji_cgir_v1.json",
    "configs/model/xiangji_cgir_v1_locked.json",
    "protocol/cycle3_model_protocol_v0.1.md",
    "src/xiangji/models/bayesian_logistic.py",
    "src/xiangji/models/cgir.py",
    "src/xiangji/models/data.py",
    "src/xiangji/models/odor_inverse.py",
    "src/xiangji/representations/kernels.py",
    "src/xiangji/representations/odor.py",
    "src/xiangji/evaluation/partial_completion.py",
    "src/xiangji/evaluation/model_selection.py",
    "src/xiangji/evaluation/development_diagnostics.py",
    "src/xiangji/evaluation/odor_inverse.py",
    "src/xiangji/evaluation/inference_diagnostics.py",
    "experiments/cycle3_model_selection.json",
    "experiments/cycle3_development_diagnostics.json",
    "experiments/cycle3_odor_inverse_nested.json",
    "experiments/cycle3_inference_diagnostics.json",
    "reports/model_card_xiangji_cgir_v1.md",
    "reports/cycle3_completion.md",
)


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest() -> dict:
    lock = json.loads((RESEARCH_ROOT / "configs/model/xiangji_cgir_v1_locked.json").read_text())
    selection = json.loads((RESEARCH_ROOT / "experiments/cycle3_model_selection.json").read_text())
    diagnostics = json.loads((RESEARCH_ROOT / "experiments/cycle3_development_diagnostics.json").read_text())
    if not selection["advancement_gate_passed"]:
        raise ValueError("Cycle 3 advancement gate did not pass")
    if lock["sealed_source_status"] != "quarantined_from_model_statistics_not_investigator_blinded":
        raise ValueError("Hong source quarantine status is not explicit")
    if "Hong records model-quarantined" not in diagnostics["scope"]:
        raise ValueError("Development diagnostic scope does not preserve the model quarantine")
    missing = [name for name in FILES if not (RESEARCH_ROOT / name).exists()]
    if missing:
        raise FileNotFoundError(f"Cycle 3 freeze files missing: {missing}")
    return {
        "schema_version": "0.1",
        "checkpoint": "cycle3_model_development_lock",
        "primary_model": lock["model"],
        "selected_configuration": {
            key: lock[key] for key in ("C", "group_dro_iterations", "graph_reducer")
        },
        "development_gate_passed": True,
        "primary_two_work_folds_accessed": False,
        "quarantined_source_accessed_by_model": False,
        "investigator_blinded": False,
        "files": [
            {"path": name, "sha256": sha256(RESEARCH_ROOT / name)} for name in FILES
        ],
    }


def main() -> None:
    manifest = build_manifest()
    target = RESEARCH_ROOT / "reports/cycle3_release_manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), "file_count": len(manifest["files"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
