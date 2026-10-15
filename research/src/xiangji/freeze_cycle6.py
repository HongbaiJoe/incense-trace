"""Freeze the reviewed Cycle 6 submission package."""

from __future__ import annotations

import hashlib
import json

from xiangji.data import RESEARCH_ROOT
from xiangji.manuscript_audit import audit


FILES = (
    "pyproject.toml", "uv.lock", "Makefile", "literature/references.bib",
    "manuscript/manuscript_v1.md", "manuscript/supplementary_v1.md",
    "manuscript/registries/source_manifest.json", "manuscript/registries/claims.csv",
    "manuscript/registries/consistency_manifest.json",
    "experiments/cycle6_stress_tests.json", "experiments/cycle6_case_study.json",
    "figures/fig6_stress_tests.pdf", "figures/fig6_stress_tests.png", "figures/fig6_stress_tests.svg",
    "figures/cycle6_figure_manifest.json",
    "manuscript/tables/table8_case_study.csv", "manuscript/tables/table9_source_mapping.csv",
    "manuscript/tables/table10_competitive_baselines.csv",
    "manuscript/tables/table11_near_duplicate_sensitivity.csv",
    "manuscript/tables/table12_count_recalibration.csv",
    "src/xiangji/evaluation/cycle6_stress_tests.py", "src/xiangji/evaluation/case_study.py",
    "src/xiangji/cycle6_assets.py", "src/xiangji/reference_verification_cycle6.py",
    "src/xiangji/clean_reproduction.py", "src/xiangji/export_submission.py",
    "src/xiangji/export_latex.py", "src/xiangji/freeze_cycle6.py", "src/xiangji/manuscript_assets.py",
    "src/xiangji/manuscript_audit.py", "src/xiangji/figure_submission_audit.py",
    "src/xiangji/ingest/build_literature_assets.py",
    "tests/test_cycle6_stress_tests.py", "tests/test_case_study.py",
    "tests/test_cycle6_assets.py", "tests/test_reference_verification_cycle6.py",
    "tests/test_clean_reproduction.py", "tests/test_export_submission.py",
    "tests/test_manuscript_audit.py", "tests/test_cycle6_release.py",
    "data/sources/literature/manuscript_reference_verification_2026-09-08.json",
    "reports/reference_verification_cycle6.md", "reports/clean_reproduction_cycle6.json",
    "reports/clean_reproduction_cycle6.md", "reports/mock_peer_review_v1.md",
    "reports/response_to_mock_review_v1.md", "reports/prepublish_audit_v1.md",
    "reports/prepublish_audit_v2.md", "reports/figure_submission_audit.json",
    "reports/figure_submission_audit.md", "reports/cycle6_completion.md",
    "reports/cycle2_release_manifest.json", "reports/cycle5_release_manifest.json",
    "submission/xiangji_cgir_manuscript.docx", "submission/xiangji_cgir_manuscript.pdf",
    "submission/xiangji_cgir_supplementary.docx", "submission/xiangji_cgir_supplementary.pdf",
    "submission/latex/xiangji_cgir_manuscript.tex",
    "submission/latex/xiangji_cgir_manuscript.pdf",
    "submission/latex/xiangji_cgir_supplementary.tex",
    "submission/latex/xiangji_cgir_supplementary.pdf",
    "submission/latex/xiangji_cgir_references.bib",
    "submission/latex/README.md",
    "submission/latex/figures/fig1_workflow.pdf",
    "submission/latex/figures/fig2_corpus.pdf",
    "submission/latex/figures/fig3_primary_performance.pdf",
    "submission/latex/figures/fig4_robustness.pdf",
    "submission/latex/figures/fig5_uncertainty_confirmation.pdf",
    "submission/latex/figures/fig6_stress_tests.pdf",
)


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest() -> dict:
    manuscript = audit()
    if manuscript["reference_count"] != 38 or manuscript["cited_reference_count"] != 38:
        raise ValueError("Numbered bibliography is incomplete")
    reference_check = json.loads((RESEARCH_ROOT / "data/sources/literature/manuscript_reference_verification_2026-09-08.json").read_text())
    if reference_check["verified_count"] != 38 or reference_check["failed_count"]:
        raise ValueError("Live reference verification is incomplete")
    reproduction = json.loads((RESEARCH_ROOT / "reports/clean_reproduction_cycle6.json").read_text())
    if reproduction["tests_passed"] != 112 or reproduction["matching_output_count"] != 14:
        raise ValueError("Clean-environment reproduction did not pass")
    stress = json.loads((RESEARCH_ROOT / "experiments/cycle6_stress_tests.json").read_text())
    if stress["count_interval_recalibration"]["expanded_coverage"] < 0.8:
        raise ValueError("Count calibration target failed")
    missing = [name for name in FILES if not (RESEARCH_ROOT / name).exists()]
    if missing:
        raise FileNotFoundError(f"Cycle 6 files missing: {missing}")
    rows = []
    for name in FILES:
        path = RESEARCH_ROOT / name
        rows.append({"path": name, "bytes": path.stat().st_size, "sha256": _sha256(path)})
    return {
        "schema_version": "0.1", "checkpoint": "cycle6_reviewed_submission_package",
        "model_parameters_changed": False, "primary_results_changed": False,
        "local_release_test_count": 112, "clean_environment_test_count": 112,
        "manuscript_audit": manuscript, "reference_verification": "38/38",
        "clean_reproduction_outputs": 14, "artifact_count": len(rows), "artifacts": rows,
    }


def main() -> None:
    payload = build_manifest()
    path = RESEARCH_ROOT / "reports/cycle6_release_manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(path), "artifact_count": payload["artifact_count"]}, indent=2))


if __name__ == "__main__":
    main()
