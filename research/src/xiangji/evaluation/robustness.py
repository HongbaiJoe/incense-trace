"""Locked-model sensitivity and error analysis for Cycle 4."""

from __future__ import annotations

import itertools
import json
import gzip
from collections import Counter, defaultdict

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.partial_completion import run_development
from xiangji.evaluation.primary import paired_source_comparison, slim_model_result, source_level_metrics
from xiangji.models.data import load_development_corpus, load_folds


def frequency_stratum(count: int) -> str:
    if count == 0:
        return "out_of_vocabulary"
    if count == 1:
        return "singleton"
    if count <= 4:
        return "rare_2_to_4"
    return "common_5_plus"


def count_stratum(count: int) -> str:
    if count <= 4:
        return "2_to_4"
    if count <= 7:
        return "5_to_7"
    return "8_plus"


def mean_seed_macro(runs: list[dict]) -> dict:
    keys = runs[0]["source_pair_macro_metrics"]
    return {
        key: float(np.mean([run["source_pair_macro_metrics"][key] for run in runs]))
        for key in keys
    }


def source_macro(source_metrics: dict) -> dict:
    """Average formula-aggregated work metrics with equal work weight."""
    metric_names = sorted(set(next(iter(source_metrics.values()))) - {"record_count"})
    return {
        metric: float(np.mean([row[metric] for row in source_metrics.values()]))
        for metric in metric_names
    }


def sensitivity(primary: dict, selection: dict, corpus) -> dict:
    names = ("frequency", selection["strongest_baseline"]["model"], primary["selected_model"])
    results = {}
    for fraction in (0.25, 0.75):
        model_runs = {}
        source_metrics = {}
        for name in names:
            configuration = selection["best_by_model"][name]
            stored = []
            for seed in selection["seeds"]:
                result = run_development(
                    seed=seed, observed_fraction=fraction,
                    C=configuration["C"],
                    group_dro_iterations=configuration["group_dro_iterations"],
                    graph_reducer=(
                        "weighted_mean" if configuration["graph_reducer"] == "not_applicable"
                        else configuration["graph_reducer"]
                    ),
                    posterior_samples=20, model_names=(name,), fold_kind="primary",
                )
                stored.append({"seed": seed, **slim_model_result(result["models"][name], False)})
            model_runs[name] = mean_seed_macro(stored)
            source_metrics[name] = source_level_metrics(stored, corpus)
        results[str(fraction)] = {
            "aggregation": "formula first, then historical work, then equal-weight work macro",
            "model_metrics": {name: source_macro(source_metrics[name]) for name in names},
            "selected_vs_graph": paired_source_comparison(
                source_metrics[primary["selected_model"]],
                source_metrics[selection["strongest_baseline"]["model"]],
            ),
            "selected_vs_frequency": paired_source_comparison(
                source_metrics[primary["selected_model"]], source_metrics["frequency"]
            ),
        }
    half_source_metrics = {name: primary["source_level_metrics"][name] for name in names}
    results["0.5"] = {
        "aggregation": "formula first, then historical work, then equal-weight work macro",
        "model_metrics": {name: source_macro(half_source_metrics[name]) for name in names},
        "selected_vs_graph": primary["primary_comparison"],
        "selected_vs_frequency": primary["frequency_comparison"],
    }
    return results


def error_analysis(primary: dict, corpus) -> dict:
    selected_runs = primary["model_runs"][primary["selected_model"]]
    by_id = corpus.by_id()
    folds = {fold["fold_id"]: fold for fold in load_folds(kind="primary")}
    rarity = defaultdict(lambda: [0, 0])
    chemistry = defaultdict(lambda: [0, 0])
    formula_metrics = defaultdict(list)
    false_negative, false_positive = Counter(), Counter()
    prediction_sets = defaultdict(list)
    representations = json.loads(
        (RESEARCH_ROOT / "data/processed/material_representations_v0.1.json").read_text()
    )
    chemical_materials = {row["ontology_material_id"] for row in representations["profiles"]}
    proxy_map = {
        "agarwood_raw_resin": "agarwood", "agarwood_soku_grade": "agarwood",
        "agarwood_yellow_grade": "agarwood", "agarwood_zhan_grade": "agarwood",
        "agarwood_zhala_grade": "agarwood", "agarwood_qinan_grade": "agarwood",
        "clove_bark": "clove_bud",
    }
    for seed_run in selected_runs:
        for fold_result in seed_run["folds"]:
            fold = folds[fold_result["fold_id"]]
            training = [by_id[reference_id] for reference_id in fold["train_reference_ids"]]
            material_counts = Counter(
                material for record in training for material in record.composition
            )
            for row in fold_result["records"]:
                if row["status"] != "evaluated":
                    continue
                record = by_id[row["reference_id"]]
                truth = set(record.composition)
                observed = set(row["observed_materials"])
                predicted = {item["material_id"] for item in row["uncertainty"]["materials"]}
                hidden_truth = truth - observed
                hidden_prediction = predicted - observed
                prediction_sets[(fold_result["fold_id"], row["reference_id"])].append(predicted)
                formula_metrics[count_stratum(len(truth))].append(row["metrics"])
                false_negative.update(hidden_truth - hidden_prediction)
                false_positive.update(hidden_prediction - hidden_truth)
                for material in hidden_truth:
                    stratum = frequency_stratum(material_counts[material])
                    rarity[stratum][1] += 1
                    rarity[stratum][0] += int(material in hidden_prediction)
                    resolved = proxy_map.get(material, material)
                    chemical_key = "profile_available" if resolved in chemical_materials else "profile_unavailable"
                    chemistry[chemical_key][1] += 1
                    chemistry[chemical_key][0] += int(material in hidden_prediction)
    stability = []
    for sets in prediction_sets.values():
        for left, right in itertools.combinations(sets, 2):
            stability.append(len(left & right) / len(left | right))
    metric_names = ("hidden_f1", "weighted_jaccard", "count_absolute_error")
    return {
        "pooling_note": "recall opportunities and errors repeat formulas across four pair folds and five mask seeds",
        "hidden_recall_by_training_frequency": {
            name: {"recovered": value[0], "total": value[1], "recall": value[0] / value[1]}
            for name, value in sorted(rarity.items())
        },
        "hidden_recall_by_chemical_profile_availability": {
            name: {"recovered": value[0], "total": value[1], "recall": value[0] / value[1]}
            for name, value in sorted(chemistry.items())
        },
        "metrics_by_true_formula_size": {
            stratum: {
                "evaluation_instances": len(rows),
                **{metric: float(np.mean([row[metric] for row in rows])) for metric in metric_names},
            }
            for stratum, rows in sorted(formula_metrics.items())
        },
        "mean_pairwise_prediction_jaccard_across_mask_seeds": float(np.mean(stability)),
        "top_false_negative_materials": false_negative.most_common(15),
        "top_false_positive_materials": false_positive.most_common(15),
    }


def run_robustness() -> dict:
    primary = json.loads((RESEARCH_ROOT / "experiments/cycle4_primary_evaluation.json").read_text())
    raw = json.loads(gzip.decompress(
        (RESEARCH_ROOT / "experiments/cycle4_primary_records.json.gz").read_bytes()
    ))
    primary_with_records = dict(primary)
    primary_with_records["model_runs"] = {
        model_name: [
            {
                "seed": compact_run["seed"],
                "source_pair_macro_metrics": compact_run["source_pair_macro_metrics"],
                "folds": [
                    {**compact_fold, "records": raw_fold["records"]}
                    for compact_fold, raw_fold in zip(compact_run["folds"], raw_run["folds"])
                ],
            }
            for compact_run, raw_run in zip(primary["model_runs"][model_name], raw["model_runs"][model_name])
        ]
        for model_name in primary["model_runs"]
    }
    selection = json.loads((RESEARCH_ROOT / "experiments/cycle3_model_selection.json").read_text())
    corpus = load_development_corpus()
    return {
        "schema_version": "0.1",
        "model_parameters_changed_after_primary_result": False,
        "observation_fraction_sensitivity": sensitivity(primary, selection, corpus),
        "locked_model_error_analysis": error_analysis(primary_with_records, corpus),
    }


def main() -> None:
    result = run_robustness()
    target = RESEARCH_ROOT / "experiments/cycle4_robustness.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
