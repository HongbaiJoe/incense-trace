"""Locked two-work-held-out primary evaluation and source-block inference."""

from __future__ import annotations

import itertools
import gzip
import json
from collections import defaultdict

import numpy as np
from scipy.stats import t

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.development_diagnostics import reliability_bins
from xiangji.evaluation.partial_completion import run_development
from xiangji.models.data import load_development_corpus


PRIMARY_METRIC = "hidden_f1"


def exact_sign_flip_pvalue(differences: np.ndarray) -> float:
    differences = np.asarray(differences, dtype=float)
    observed = abs(float(differences.mean()))
    statistics = [
        abs(float(np.mean(differences * np.asarray(signs))))
        for signs in itertools.product((-1.0, 1.0), repeat=len(differences))
    ]
    return sum(value >= observed - 1e-12 for value in statistics) / len(statistics)


def source_bootstrap_interval(
    differences: np.ndarray, *, seed: int = 1701, draws: int = 20000
) -> list[float]:
    differences = np.asarray(differences, dtype=float)
    generator = np.random.default_rng(seed)
    indices = generator.integers(0, len(differences), size=(draws, len(differences)))
    estimates = differences[indices].mean(axis=1)
    return [float(value) for value in np.quantile(estimates, [0.025, 0.975])]


def slim_model_result(model_result: dict, keep_uncertainty: bool) -> dict:
    folds = []
    for fold in model_result["folds"]:
        records = []
        for row in fold["records"]:
            slim = {key: row[key] for key in (
                "reference_id", "work_id", "status", "true_material_count", "in_vocabulary_count"
            ) if key in row}
            if row["status"] == "evaluated":
                slim["observed_materials"] = row["observed_materials"]
                slim["metrics"] = row["metrics"]
                if keep_uncertainty:
                    prediction = row["prediction"]
                    slim["uncertainty"] = {
                        "selected_count": prediction["selected_count"],
                        "count_posterior": prediction["count_posterior"],
                        "materials": prediction["materials"],
                    }
            records.append(slim)
        folds.append({
            "fold_id": fold["fold_id"],
            "test_work_ids": fold["test_work_ids"],
            "training_formula_count": fold["training_formula_count"],
            "test_formula_count": fold["test_formula_count"],
            "evaluated_formula_count": fold["evaluated_formula_count"],
            "not_evaluable_count": fold["not_evaluable_count"],
            "metrics": fold["metrics"],
            "diagnostics": fold["diagnostics"],
            "records": records,
        })
    return {"source_pair_macro_metrics": model_result["source_macro_metrics"], "folds": folds}


def source_level_metrics(model_runs: dict, corpus) -> dict:
    by_id = corpus.by_id()
    values = defaultdict(lambda: defaultdict(list))
    for seed_run in model_runs:
        for fold in seed_run["folds"]:
            for row in fold["records"]:
                if row["status"] == "evaluated":
                    values[row["reference_id"]][PRIMARY_METRIC].append(row["metrics"][PRIMARY_METRIC])
                    values[row["reference_id"]]["weighted_jaccard"].append(row["metrics"]["weighted_jaccard"])
                    values[row["reference_id"]]["aitchison_distance"].append(row["metrics"]["aitchison_distance"])
    source_records = defaultdict(list)
    for reference_id, metric_values in values.items():
        source_records[by_id[reference_id].work_id].append({
            metric: float(np.mean(items)) for metric, items in metric_values.items()
        })
    return {
        source: {
            "record_count": len(rows),
            **{metric: float(np.mean([row[metric] for row in rows])) for metric in rows[0]},
        }
        for source, rows in sorted(source_records.items())
    }


def paired_source_comparison(selected: dict, baseline: dict) -> dict:
    sources = sorted(set(selected) & set(baseline))
    differences = np.array([
        selected[source][PRIMARY_METRIC] - baseline[source][PRIMARY_METRIC]
        for source in sources
    ])
    mean = float(differences.mean())
    standard_error = float(differences.std(ddof=1) / np.sqrt(len(differences)))
    half_width = float(t.ppf(0.975, len(differences) - 1) * standard_error)
    return {
        "metric": PRIMARY_METRIC,
        "unit_of_inference": "historical work group",
        "source_count": len(sources),
        "per_source_difference": {
            source: float(value) for source, value in zip(sources, differences)
        },
        "mean_paired_difference": mean,
        "descriptive_t_95_interval": [mean - half_width, mean + half_width],
        "source_bootstrap_95_interval": source_bootstrap_interval(differences),
        "exact_two_sided_sign_flip_pvalue": exact_sign_flip_pvalue(differences),
    }


def selected_calibration(raw_seed_results: list[dict], corpus) -> dict:
    by_id = corpus.by_id()
    probabilities, labels = [], []
    count_error, count_bias, count_coverage = [], [], []
    ratio_hits = ratio_total = selected_true = total_true = 0
    for model_result in raw_seed_results:
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
                truth_count = len(record.composition)
                count_error.append(abs(prediction["selected_count"] - truth_count))
                count_bias.append(prediction["selected_count"] - truth_count)
                support = np.asarray([int(key) for key in prediction["count_posterior"]])
                mass = np.asarray(list(prediction["count_posterior"].values()))
                cumulative = np.cumsum(mass)
                low, high = support[np.searchsorted(cumulative, [0.1, 0.9])]
                count_coverage.append(int(low <= truth_count <= high))
                predicted = {item["material_id"]: item for item in prediction["materials"]}
                total_true += len(record.composition)
                selected_true += len(set(predicted) & set(record.composition))
                for material, truth in record.composition.items():
                    if material in predicted:
                        ratio_total += 1
                        low, high = predicted[material]["ratio_interval_80"]
                        ratio_hits += int(low <= truth <= high)
    bins, ece = reliability_bins(probabilities, labels)
    brier = float(np.mean((np.asarray(probabilities) - np.asarray(labels)) ** 2))
    return {
        "pooling_note": "evaluation instances repeat formulas across pair folds and seeds; calibration is descriptive",
        "hidden_candidate_count": len(labels),
        "hidden_candidate_brier": brier,
        "hidden_candidate_ece": ece,
        "reliability_bins": bins,
        "count_mae": float(np.mean(count_error)),
        "count_mean_signed_error": float(np.mean(count_bias)),
        "count_central_80_interval_coverage": float(np.mean(count_coverage)),
        "true_component_selection_rate": selected_true / total_true,
        "ratio_conditional_80_interval_coverage": ratio_hits / ratio_total,
    }


def run_primary() -> dict:
    lock = json.loads((RESEARCH_ROOT / "configs/model/xiangji_cgir_v1_locked.json").read_text())
    selection = json.loads((RESEARCH_ROOT / "experiments/cycle3_model_selection.json").read_text())
    manifest = json.loads((RESEARCH_ROOT / "reports/cycle3_release_manifest.json").read_text())
    if manifest["primary_two_work_folds_accessed"] is not False:
        raise ValueError("Cycle 3 manifest does not preserve the primary-fold lock")
    selected_name = selection["selected_structured_model"]["model"]
    if selected_name != "full_no_chemistry":
        raise ValueError("Unexpected locked primary model")
    corpus = load_development_corpus()
    model_names = tuple(selection["best_by_model"])
    raw_by_model = {name: [] for name in model_names}
    stored_by_model = {name: [] for name in model_names}
    for seed in selection["seeds"]:
        for model_name in model_names:
            configuration = selection["best_by_model"][model_name]
            result = run_development(
                seed=seed,
                C=configuration["C"],
                group_dro_iterations=configuration["group_dro_iterations"],
                graph_reducer=(
                    "weighted_mean" if configuration["graph_reducer"] == "not_applicable"
                    else configuration["graph_reducer"]
                ),
                posterior_samples=200,
                model_names=(model_name,),
                fold_kind="primary",
            )
            raw_model = result["models"][model_name]
            raw_by_model[model_name].append(raw_model)
            slim = slim_model_result(raw_model, keep_uncertainty=model_name == selected_name)
            stored_by_model[model_name].append({"seed": seed, **slim})
    source_metrics = {
        name: source_level_metrics(runs, corpus) for name, runs in stored_by_model.items()
    }
    strongest_baseline = selection["strongest_baseline"]["model"]
    return {
        "schema_version": "0.1",
        "task": "frozen two-work-held-out partial-formula completion",
        "model_lock": lock,
        "cycle3_manifest_sha256": __import__("hashlib").sha256(
            (RESEARCH_ROOT / "reports/cycle3_release_manifest.json").read_bytes()
        ).hexdigest(),
        "Hong_source_role": "model-quarantined and excluded; not investigator-blinded",
        "primary_result_used_for_model_changes": False,
        "seeds": selection["seeds"],
        "selected_model": selected_name,
        "strongest_development_baseline": strongest_baseline,
        "model_runs": stored_by_model,
        "source_level_metrics": source_metrics,
        "primary_comparison": paired_source_comparison(
            source_metrics[selected_name], source_metrics[strongest_baseline]
        ),
        "frequency_comparison": paired_source_comparison(
            source_metrics[selected_name], source_metrics["frequency"]
        ),
        "selected_model_calibration": selected_calibration(raw_by_model[selected_name], corpus),
    }


def compact_result(result: dict) -> tuple[dict, dict]:
    compact = {key: value for key, value in result.items() if key != "model_runs"}
    compact_runs, raw_runs = {}, {}
    for model_name, runs in result["model_runs"].items():
        compact_runs[model_name] = []
        raw_runs[model_name] = []
        for run in runs:
            compact_folds, raw_folds = [], []
            for fold in run["folds"]:
                compact_folds.append({key: value for key, value in fold.items() if key != "records"})
                raw_folds.append({
                    "fold_id": fold["fold_id"],
                    "test_work_ids": fold["test_work_ids"],
                    "records": fold["records"],
                })
            compact_runs[model_name].append({
                "seed": run["seed"],
                "source_pair_macro_metrics": run["source_pair_macro_metrics"],
                "folds": compact_folds,
            })
            raw_runs[model_name].append({"seed": run["seed"], "folds": raw_folds})
    compact["model_runs"] = compact_runs
    raw = {"schema_version": result["schema_version"], "model_runs": raw_runs}
    return compact, raw


def main() -> None:
    result = run_primary()
    compact, raw = compact_result(result)
    target = RESEARCH_ROOT / "experiments/cycle4_primary_evaluation.json"
    target.write_text(json.dumps(compact, ensure_ascii=False, indent=2), encoding="utf-8")
    raw_target = RESEARCH_ROOT / "experiments/cycle4_primary_records.json.gz"
    raw_target.write_bytes(gzip.compress(
        json.dumps(raw, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        compresslevel=9, mtime=0,
    ))
    print(json.dumps({
        "output": str(target),
        "raw_output": str(raw_target),
        "primary_comparison": result["primary_comparison"],
        "frequency_comparison": result["frequency_comparison"],
        "selected_model_calibration": result["selected_model_calibration"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
