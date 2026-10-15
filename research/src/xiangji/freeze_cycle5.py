"""Freeze Cycle 5 manuscript, figures, tables and evidence registries."""

from __future__ import annotations

import hashlib
import json

from xiangji.data import RESEARCH_ROOT
from xiangji.manuscript_audit import audit


FILES = (
    "pyproject.toml",
    "uv.lock",
    "literature/references.bib",
    "reports/cycle2_release_manifest.json",
    "experiments/cycle5_computational_profile.json",
    "src/xiangji/evaluation/computational_profile.py",
    "src/xiangji/manuscript_assets.py",
    "src/xiangji/manuscript_audit.py",
    "manuscript/venue_target.md",
    "manuscript/manuscript_v1.md",
    "manuscript/supplementary_v1.md",
    "manuscript/registries/source_manifest.json",
    "manuscript/registries/claims.csv",
    "manuscript/registries/consistency_manifest.json",
    "manuscript/tables/table1_corpus_by_source.csv",
    "manuscript/tables/table2_primary_models.csv",
    "manuscript/tables/table3_source_metrics.csv",
    "manuscript/tables/table4_context_sensitivity.csv",
    "manuscript/tables/table5_rarity_recall.csv",
    "manuscript/tables/table6_reliability_bins.csv",
    "manuscript/tables/table7_hong_confirmation.csv",
    "figures/figure_manifest.json",
    "figures/fig1_workflow.pdf",
    "figures/fig1_workflow.png",
    "figures/fig1_workflow.svg",
    "figures/fig2_corpus.pdf",
    "figures/fig2_corpus.png",
    "figures/fig2_corpus.svg",
    "figures/fig3_primary_performance.pdf",
    "figures/fig3_primary_performance.png",
    "figures/fig3_primary_performance.svg",
    "figures/fig4_robustness.pdf",
    "figures/fig4_robustness.png",
    "figures/fig4_robustness.svg",
    "figures/fig5_uncertainty_confirmation.pdf",
    "figures/fig5_uncertainty_confirmation.png",
    "figures/fig5_uncertainty_confirmation.svg",
    "tests/test_computational_profile.py",
    "tests/test_manuscript_assets.py",
    "tests/test_manuscript_audit.py",
    "reports/cycle5_completion.md",
)


def build_manifest() -> dict:
    manuscript = audit()
    if manuscript["reference_count"] != 38 or manuscript["cited_reference_count"] != 38:
        raise ValueError("Manuscript bibliography is incomplete")
    if manuscript["missing_numeric_anchors"] or manuscript["missing_sections"]:
        raise ValueError("Manuscript audit is incomplete")
    missing = [name for name in FILES if not (RESEARCH_ROOT / name).exists()]
    if missing:
        raise FileNotFoundError(f"Cycle 5 files missing: {missing}")
    rows = []
    for name in FILES:
        payload = (RESEARCH_ROOT / name).read_bytes()
        rows.append({
            "path": name,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        })
    return {
        "schema_version": "0.1",
        "checkpoint": "cycle5_manuscript_and_figures",
        "model_parameters_changed": False,
        "primary_results_changed": False,
        "bibliography_metadata_enriched": True,
        "test_count": 99,
        "manuscript_audit": manuscript,
        "artifact_count": len(rows),
        "artifacts": rows,
    }


def main() -> None:
    result = build_manifest()
    target = RESEARCH_ROOT / "reports" / "cycle5_release_manifest.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), "artifact_count": result["artifact_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
