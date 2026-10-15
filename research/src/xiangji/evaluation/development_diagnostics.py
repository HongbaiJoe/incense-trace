"""Post-selection diagnostics without primary-fold or Hong-record model use."""

from __future__ import annotations

import json

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.partial_completion import run_development
from xiangji.models.data import load_development_corpus


def reliability_bins(probabilities: list[float], labels: list[int], count: int = 10) -> tuple[list[dict], float]:
    p = np.asarray(probabilities)
    y = np.asarray(labels)
    rows, ece = [], 0.0
    for index in range(count):
        lower, upper = index / count, (index + 1) / count
        mask = (p >= lower) & (p < upper if index < count - 1 else p <= upper)
        if not mask.any():
            continue
        mean_probability = float(p[mask].mean())
        empirical = float(y[mask].mean())
        ece += float(mask.mean()) * abs(mean_probability - empirical)
        rows.append({
            "lower": lower, "upper": upper, "n": int(mask.sum()),
            "mean_probability": mean_probability, "empirical_frequency": empirical,
        })
    return rows, ece


def run_diagnostics() -> dict:
    lock = json.loads((RESEARCH_ROOT / "configs" / "model" / "xiangji_cgir_v1_locked.json").read_text())
    selection = json.loads((RESEARCH_ROOT / "experiments" / "cycle3_model_selection.json").read_text())
    selected = selection["selected_structured_model"]
    if any(selected[key] != lock[key] for key in ("C", "group_dro_iterations", "graph_reducer")):
        raise ValueError("Locked model does not match development selection")
    corpus = load_development_corpus()
    by_id = corpus.by_id()
    seed_runs, probabilities, labels = [], [], []
    count_errors, count_biases, count_interval_hits = [], [], []
    ratio_hits, ratio_total = 0, 0
    selected_true, total_true = 0, 0
    for seed in selection["seeds"]:
        result = run_development(
            seed=seed, C=lock["C"], group_dro_iterations=lock["group_dro_iterations"],
            graph_reducer=lock["graph_reducer"], posterior_samples=500,
            model_names=(selected["model"],),
        )
        model_result = result["models"][selected["model"]]
        seed_runs.append({
            "seed": seed,
            "source_macro_metrics": model_result["source_macro_metrics"],
            "fold_diagnostics": [
                {"fold_id": fold["fold_id"], **fold["diagnostics"]}
                for fold in model_result["folds"]
            ],
        })
        for fold in model_result["folds"]:
            for row in fold["records"]:
                if row["status"] != "evaluated":
                    continue
                record = by_id[row["reference_id"]]
                prediction = row["prediction"]
                observed = set(row["observed_materials"])
                for material, probability in prediction["all_inclusion_probabilities"].items():
                    if material not in observed:
                        probabilities.append(probability)
                        labels.append(int(material in record.composition))
                true_count = len(record.composition)
                predicted_count = prediction["selected_count"]
                count_errors.append(abs(predicted_count - true_count))
                count_biases.append(predicted_count - true_count)
                support = np.array([int(value) for value in prediction["count_posterior"]])
                mass = np.array(list(prediction["count_posterior"].values()))
                cumulative = np.cumsum(mass)
                low = support[np.searchsorted(cumulative, 0.1)]
                high = support[np.searchsorted(cumulative, 0.9)]
                count_interval_hits.append(int(low <= true_count <= high))
                total_true += len(record.composition)
                predicted_by_material = {item["material_id"]: item for item in prediction["materials"]}
                selected_true += len(set(predicted_by_material) & set(record.composition))
                for material, truth in record.composition.items():
                    if material in predicted_by_material:
                        ratio_total += 1
                        low, high = predicted_by_material[material]["ratio_interval_80"]
                        ratio_hits += int(low <= truth <= high)
    bins, ece = reliability_bins(probabilities, labels)
    metric_keys = seed_runs[0]["source_macro_metrics"]
    return {
        "schema_version": "0.1",
        "scope": "development leave-one-work-out folds only; primary folds unused and Hong records model-quarantined",
        "locked_model": lock,
        "seed_macro_mean": {
            key: float(np.mean([run["source_macro_metrics"][key] for run in seed_runs]))
            for key in metric_keys
        },
        "seed_macro_sd": {
            key: float(np.std([run["source_macro_metrics"][key] for run in seed_runs], ddof=1))
            for key in metric_keys
        },
        "hidden_candidate_reliability": {
            "n": len(labels), "bins": bins, "expected_calibration_error": ece,
        },
        "count_posterior": {
            "mean_absolute_error": float(np.mean(count_errors)),
            "mean_signed_error": float(np.mean(count_biases)),
            "central_80_interval_coverage": float(np.mean(count_interval_hits)),
        },
        "ratio_posterior": {
            "conditional_on_true_component_selected_80_interval_coverage": ratio_hits / ratio_total,
            "true_component_selection_rate": selected_true / total_true,
            "evaluated_selected_true_components": ratio_total,
        },
        "seed_runs": seed_runs,
    }


def main() -> None:
    result = run_diagnostics()
    target = RESEARCH_ROOT / "experiments" / "cycle3_development_diagnostics.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(target),
        "seed_macro_mean": result["seed_macro_mean"],
        "hidden_candidate_reliability": result["hidden_candidate_reliability"],
        "count_posterior": result["count_posterior"],
        "ratio_posterior": result["ratio_posterior"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
