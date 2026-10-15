"""Audit mathematical completeness across manuscript, code, Word and LaTeX.

The audit is deliberately structural: every displayed equation must have a
unique label, a concrete implementation locus, and a numbered rendering in
both delivery formats.  It does not treat document export as proof that an
equation is scientifically implemented.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from xiangji.complete_manuscript import build as build_complete_manuscript
from xiangji.data import RESEARCH_ROOT
from xiangji.export_latex import export as export_latex
from xiangji.export_submission import export as export_word


REPORT = RESEARCH_ROOT / "reports" / "mathematical_audit_v1.md"
WORD = RESEARCH_ROOT / "submission" / "xiangji_cgir_complete_paper.docx"
TEX = RESEARCH_ROOT / "submission" / "latex" / "xiangji_cgir_complete_paper.tex"
MANUSCRIPT = RESEARCH_ROOT / "manuscript" / "manuscript_complete.md"


@dataclass(frozen=True)
class Implementation:
    file: str
    symbol: str
    keyword: str


IMPLEMENTATIONS = {
    "composition-closure": Implementation("src/xiangji/normalization/build_curated_reference.py", "close_composition", "value / total"),
    "mask-cardinality": Implementation("src/xiangji/models/data.py", "deterministic_observation_mask", "round"),
    "prevalence-priors": Implementation("src/xiangji/models/cgir.py", "XiangjiCGIR._fit_priors", "source_prior_strength"),
    "directed-graph": Implementation("src/xiangji/representations/kernels.py", "hypergraph_kernel", "cooccurrence"),
    "graph-affinity": Implementation("src/xiangji/representations/kernels.py", "affinity_from_observed", "reducer"),
    "title-affinity": Implementation("src/xiangji/models/cgir.py", "TitleMaterialEncoder", "centroids"),
    "candidate-features": Implementation("src/xiangji/models/cgir.py", "XiangjiCGIR._feature_matrix", "clipped_logit"),
    "logistic-model": Implementation("src/xiangji/models/bayesian_logistic.py", "LaplaceLogisticRegression", "expit"),
    "map-objective": Implementation("src/xiangji/models/bayesian_logistic.py", "LaplaceLogisticRegression.fit", "objective"),
    "laplace-posterior": Implementation("src/xiangji/models/bayesian_logistic.py", "LaplaceLogisticRegression.fit", "posterior_covariance_"),
    "predictive-probability": Implementation("src/xiangji/models/bayesian_logistic.py", "LaplaceLogisticRegression.predict_proba", "np.pi"),
    "count-priors": Implementation("src/xiangji/models/cgir.py", "XiangjiCGIR._fit_priors", "global_count_distribution_"),
    "count-posterior": Implementation("src/xiangji/models/cgir.py", "XiangjiCGIR.count_posterior", "likelihood"),
    "count-decision": Implementation("src/xiangji/models/cgir.py", "XiangjiCGIR.predict", "searchsorted"),
    "ratio-ridge": Implementation("src/xiangji/models/cgir.py", "XiangjiCGIR.fit", "Ridge"),
    "ratio-closure": Implementation("src/xiangji/models/cgir.py", "XiangjiCGIR.predict", "ratio_positive"),
    "dirichlet-composition": Implementation("src/xiangji/models/cgir.py", "XiangjiCGIR.predict", "dirichlet"),
    "mass-constraint": Implementation("src/xiangji/evaluation/cycle6_stress_tests.py", "mass_constrained_composition", "remaining"),
    "profile-similarities": Implementation("src/xiangji/representations/kernels.py", "build_chemical_kernel", "safe_cosine"),
    "chemical-kernel": Implementation("src/xiangji/representations/kernels.py", "build_chemical_kernel", "weights[0]"),
    "knn-similarity": Implementation("src/xiangji/evaluation/cycle6_stress_tests.py", "CompletionBaseline._scores", "cosine"),
    "svd-baseline": Implementation("src/xiangji/evaluation/cycle6_stress_tests.py", "CompletionBaseline.fit", "np.linalg.svd"),
    "set-metrics": Implementation("src/xiangji/evaluation/partial_completion.py", "f1_sets", "precision"),
    "composition-metrics": Implementation("src/xiangji/evaluation/partial_completion.py", "composition_metrics", "weighted_jaccard"),
    "aitchison-distance": Implementation("src/xiangji/evaluation/partial_completion.py", "composition_metrics", "true_clr"),
    "calibration-metrics": Implementation("src/xiangji/evaluation/primary.py", "selected_calibration", "brier"),
    "source-macro": Implementation("src/xiangji/evaluation/primary.py", "source_level_metrics", "reference_id"),
    "sign-flip-test": Implementation("src/xiangji/evaluation/primary.py", "exact_sign_flip_pvalue", "itertools.product"),
    "count-conformal": Implementation("src/xiangji/evaluation/cycle6_stress_tests.py", "recalibrated_count_intervals", "method=\"higher\""),
}


def _equations(text: str) -> list[str]:
    return re.findall(r"^\$\$\[([a-z0-9-]+)\]", text, flags=re.MULTILINE)


def audit(*, write_report: bool = True) -> dict[str, int | bool]:
    build_complete_manuscript()
    export_word()
    export_latex()
    text = MANUSCRIPT.read_text(encoding="utf-8")
    labels = _equations(text)
    if labels != list(IMPLEMENTATIONS):
        raise ValueError("Equation order and implementation registry differ")
    table_markers = [int(value) for value in re.findall(r"^\[\[TABLE:(\d+)\]\]$", text, flags=re.MULTILINE)]
    figure_markers = [int(value) for value in re.findall(r"^\[\[FIGURE:(\d+)\]\]$", text, flags=re.MULTILINE)]
    if table_markers != list(range(1, 9)) or figure_markers != list(range(1, 7)):
        raise ValueError(f"Non-sequential body assets: tables={table_markers}, figures={figure_markers}")

    for label, location in IMPLEMENTATIONS.items():
        source = (RESEARCH_ROOT / location.file).read_text(encoding="utf-8")
        if location.keyword not in source:
            raise ValueError(f"Implementation evidence missing for {label}: {location.keyword}")

    tex = TEX.read_text(encoding="utf-8")
    tex_labels = re.findall(r"\\label\{eq:([a-z0-9-]+)\}", tex)
    if tex_labels != labels or tex.count(r"\begin{equation}") != len(labels):
        raise ValueError("LaTeX equation labels or count differ from the manuscript")
    if tex.count(r"\begin{figure}[htbp]") != 6 or tex.count(r"\begin{table}[htbp]") != 8:
        raise ValueError("LaTeX does not contain six figures and eight main tables")

    with zipfile.ZipFile(WORD) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
        styles_xml = archive.read("word/styles.xml").decode("utf-8")
    visible_text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", document_xml))
    missing_numbers = [number for number in range(1, len(labels) + 1) if f"({number})" not in visible_text]
    if missing_numbers:
        raise ValueError(f"Word equation numbers missing: {missing_numbers}")
    if document_xml.count("<m:oMath") < len(labels):
        raise ValueError("Word export has fewer native math objects than equations")
    if "4F81BD" in document_xml + styles_xml or "w:highlight" in document_xml:
        raise ValueError("Word export contains forbidden blue or highlight styling")
    if "Times New Roman" not in styles_xml:
        raise ValueError("Word style sheet does not declare Times New Roman")
    if any(f"Table {number}." not in visible_text for number in range(1, 9)):
        raise ValueError("Word table captions are incomplete")
    if any(f"Figure {number}." not in visible_text for number in range(1, 7)):
        raise ValueError("Word figure captions are incomplete")

    rows = []
    for number, label in enumerate(labels, start=1):
        location = IMPLEMENTATIONS[label]
        rows.append(f"| {number} | `{label}` | `{location.file}` | `{location.symbol}` | verified |")
    report = "\n".join([
        "# Mathematical completeness audit",
        "",
        "Status: **PASS**",
        "",
        f"- Main-text numbered equations: {len(labels)}",
        "- Main-text figures: 6",
        "- Main-text tables: 8",
        "- Word equations: native OMML with all equation numbers present",
        "- LaTeX equations: numbered environments with matching labels",
        "- Styling checks: Times New Roman declared; no blue title styling or highlights",
        "",
        "## Equation-to-code traceability",
        "",
        "| Eq. | Manuscript label | Implementation file | Symbol or function | Audit |",
        "|---:|---|---|---|---|",
        *rows,
        "",
        "## Scope of this audit",
        "",
        "The check establishes structural parity and an implementation locus for every equation. Numerical correctness remains covered by the unit and release test suites; empirical claims remain covered by the manuscript evidence audit.",
        "",
    ])
    if write_report:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(report, encoding="utf-8")
    return {
        "equation_count": len(labels),
        "figure_count": 6,
        "table_count": 8,
        "word_native_math_minimum_met": True,
        "latex_equation_parity": True,
    }


def main() -> None:
    result = audit()
    print(REPORT)
    print(result)


if __name__ == "__main__":
    main()
