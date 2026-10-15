"""Build compact, publication-facing tables from frozen experiment artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from xiangji.data import RESEARCH_ROOT


OUTPUT_DIR = RESEARCH_ROOT / "manuscript" / "main_tables"


def _load(path: str) -> dict:
    return json.loads((RESEARCH_ROOT / path).read_text(encoding="utf-8"))


def _write(name: str, fieldnames: list[str], rows: list[dict]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _f(value: float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def build() -> list[Path]:
    outputs: list[Path] = []
    outputs.append(_write(
        "table1_notation.csv",
        ["Symbol", "Meaning"],
        [
            {"Symbol": "i, j, d", "Meaning": "Formula, material and historical-work indices"},
            {"Symbol": "S_i, O_i, H_i", "Meaning": "Complete, observed and hidden material sets for formula i"},
            {"Symbol": "q_ij, w_ij", "Meaning": "Converted aromatic mass and closed mass fraction"},
            {"Symbol": "pi_j, pi_j|d", "Meaning": "Global and source-conditioned material prevalence"},
            {"Symbol": "G_ab", "Meaning": "Directed posterior-predictive affinity from material a to b"},
            {"Symbol": "g_ij, u_ij", "Meaning": "Source-deviation feature and observed-material indicator"},
            {"Symbol": "phi_ij, x_ij, z_ij", "Meaning": "Core, complete and standardized candidate-feature vectors"},
            {"Symbol": "theta, Sigma", "Meaning": "Inclusion coefficients and Laplace covariance"},
            {"Symbol": "p_ij", "Meaning": "Posterior-approximated inclusion probability"},
            {"Symbol": "K_i, K-hat_i", "Meaning": "True and predicted total ingredient count"},
            {"Symbol": "mu_ij, W_i", "Meaning": "Predicted mean composition and composition random vector"},
            {"Symbol": "L_tr, L_r, B", "Meaning": "Candidate rows, positive ratio rows and chemical-profile bins"},
            {"Symbol": "D, I_d, A_i", "Meaning": "Number of works, formulas in work d and repeated evaluations of formula i"},
        ],
    ))
    with (RESEARCH_ROOT / "manuscript/tables/table1_corpus_by_source.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        corpus = list(csv.DictReader(handle))
    outputs.append(_write(
        "table2_corpus.csv",
        ["Historical work", "Formulas", "Unique materials", "Median size", "Evaluation role"],
        [{
            "Historical work": row["work"],
            "Formulas": row["formula_count"],
            "Unique materials": row["unique_materials"],
            "Median size": row["median_formula_size"],
            "Evaluation role": (
                "Confirmation" if row["role"] == "confirmation" else "Development and primary"
            ),
        } for row in corpus],
    ))

    stress = _load("experiments/cycle6_stress_tests.json")
    primary = _load("experiments/cycle4_primary_evaluation.json")
    baseline_rows = {
        row["model"]: row
        for row in csv.DictReader(
            (RESEARCH_ROOT / "manuscript/tables/table10_competitive_baselines.csv").open(
                encoding="utf-8", newline=""
            )
        )
    }
    outputs.append(_write(
        "table3_primary_results.csv",
        ["Model", "Hidden F1 higher is better", "Weighted Jaccard higher is better"],
        [{
            "Model": name,
            "Hidden F1 higher is better": _f(baseline_rows[name]["hidden_f1"]),
            "Weighted Jaccard higher is better": _f(baseline_rows[name]["weighted_jaccard"]),
        } for name in ("Frequency", "Formula kNN", "PureSVD", "Directed graph", "Full decoder")],
    ))

    selection = _load("experiments/cycle3_model_selection.json")
    labels = {
        "frequency": "Frequency only",
        "source_prior": "Frequency plus source",
        "title_only": "Frequency plus title",
        "graph_only": "Frequency plus directed graph",
        "full_no_chemistry": "Full decoder without chemistry",
        "xiangji_cgir_v1": "Full decoder with chemistry",
    }
    outputs.append(_write(
        "table4_development_ablation.csv",
        ["Development model", "Hidden F1 higher is better", "Weighted Jaccard higher is better", "Normalized Aitchison lower is better"],
        [{
            "Development model": labels[key],
            "Hidden F1 higher is better": _f(value["mean_metrics"]["hidden_f1"]),
            "Weighted Jaccard higher is better": _f(value["mean_metrics"]["weighted_jaccard"]),
            "Normalized Aitchison lower is better": _f(value["mean_metrics"]["aitchison_distance"]),
        } for key, value in selection["best_by_model"].items()],
    ))

    source = primary["source_level_metrics"]
    outputs.append(_write(
        "table5_work_level_results.csv",
        ["Held-out work", "Formulas", "Frequency F1", "Directed graph F1", "Full decoder F1"],
        [{
            "Held-out work": {
                "chen_xiangpu_compilation": "Chen Xiangpu",
                "huizhai_xiangpu": "Huizhai Xiangpu",
                "liexiang_xinpu": "Liexiang Xinpu",
                "moe_xiaolu_xiangpu": "Xiaolu Xiangpu",
                "xiangcheng_compilation_unresolved_source": "Xiangcheng compilation",
            }[work],
            "Formulas": source["full_no_chemistry"][work]["record_count"],
            "Frequency F1": _f(source["frequency"][work]["hidden_f1"]),
            "Directed graph F1": _f(source["graph_only"][work]["hidden_f1"]),
            "Full decoder F1": _f(source["full_no_chemistry"][work]["hidden_f1"]),
        } for work in sorted(source["full_no_chemistry"])],
    ))

    robustness = _load("experiments/cycle4_robustness.json")["observation_fraction_sensitivity"]
    context_rows = []
    for fraction in ("0.25", "0.5", "0.75"):
        for model, label in (
            ("frequency", "Frequency"), ("graph_only", "Directed graph"),
            ("full_no_chemistry", "Full decoder"),
        ):
            metrics = robustness[fraction]["model_metrics"][model]
            context_rows.append({
                "Observed fraction": fraction,
                "Model": label,
                "Hidden F1 higher is better": _f(metrics["hidden_f1"]),
                "Weighted Jaccard higher is better": _f(metrics["weighted_jaccard"]),
            })
    outputs.append(_write(
        "table6_context_sensitivity.csv",
        ["Observed fraction", "Model", "Hidden F1 higher is better", "Weighted Jaccard higher is better"],
        context_rows,
    ))

    calibration = primary["selected_model_calibration"]
    count = stress["count_interval_recalibration"]
    outputs.append(_write(
        "table7_uncertainty.csv",
        ["Diagnostic", "Estimate", "Interpretation"],
        [
            {"Diagnostic": "Hidden-candidate Brier score", "Estimate": _f(calibration["hidden_candidate_brier"], 4), "Interpretation": "Lower is better"},
            {"Diagnostic": "Hidden-candidate ECE", "Estimate": _f(calibration["hidden_candidate_ece"], 4), "Interpretation": "Ten equal-width bins"},
            {"Diagnostic": "Base count interval coverage", "Estimate": _f(count["base_coverage"]), "Interpretation": "Nominal level 0.80"},
            {"Diagnostic": "Calibrated count interval coverage", "Estimate": _f(count["expanded_coverage"]), "Interpretation": "Development radius equals one"},
            {"Diagnostic": "Calibrated count interval mean width", "Estimate": _f(count["expanded_mean_width"]), "Interpretation": "Materials"},
            {"Diagnostic": "Conditional ratio interval coverage", "Estimate": _f(calibration["ratio_conditional_80_interval_coverage"]), "Interpretation": "Conditional on correct selection"},
        ],
    ))

    case = _load("experiments/cycle6_case_study.json")
    outputs.append(_write(
        "table8_case_study.csv",
        ["Material", "Outcome", "Reference ratio", "Predicted ratio", "Inclusion probability"],
        [{
            "Material": row["material_id"].replace("_", " "),
            "Outcome": row["outcome"],
            "Reference ratio": _f(row["reference_ratio"]),
            "Predicted ratio": "" if row["predicted_ratio"] is None else _f(row["predicted_ratio"]),
            "Inclusion probability": "" if row["inclusion_probability"] is None else _f(row["inclusion_probability"]),
        } for row in case["material_rows"]],
    ))
    return outputs


def main() -> None:
    for path in build():
        print(path)


if __name__ == "__main__":
    main()
