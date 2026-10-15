"""Metrics and fold runner for leakage-safe partial-formula completion."""

from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.models.cgir import FEATURE_NAMES, XiangjiCGIR
from xiangji.models.data import FormulaRecord, deterministic_observation_mask, load_development_corpus, load_folds


ABLATIONS = {
    "frequency": {"global_prevalence_logit", "observed_material", "observed_log_weight"},
    "source_prior": {"global_prevalence_logit", "source_prevalence_logit", "observed_material", "observed_log_weight"},
    "title_only": {"global_prevalence_logit", "title_material_similarity", "observed_material", "observed_log_weight"},
    "graph_only": {"global_prevalence_logit", "hypergraph_affinity", "observed_material", "observed_log_weight"},
    "full_no_chemistry": set(FEATURE_NAMES) - {"chemical_affinity", "chemical_evidence_available", "chemical_odor_similarity"},
    # The chemistry affinity is active only when the observed material and
    # candidate both have external profiles. The standalone availability flag
    # is excluded from T1 because it otherwise becomes a material-identity
    # shortcut rather than a chemical relation.
    "xiangji_cgir_v1": set(FEATURE_NAMES) - {
        "chemical_evidence_available", "chemical_odor_similarity"
    },
}


def f1_sets(truth: set[str], prediction: set[str]) -> tuple[float, float, float]:
    tp = len(truth & prediction)
    precision = tp / len(prediction) if prediction else (1.0 if not truth else 0.0)
    recall = tp / len(truth) if truth else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def composition_metrics(truth: dict[str, float], prediction: dict[str, float]) -> dict[str, float]:
    union = sorted(set(truth) | set(prediction))
    true = np.array([truth.get(key, 0.0) for key in union], dtype=float)
    pred = np.array([prediction.get(key, 0.0) for key in union], dtype=float)
    weighted_jaccard = np.minimum(true, pred).sum() / np.maximum(true, pred).sum()
    union_mae = np.abs(true - pred).mean()
    epsilon = 1e-6
    true_closed = (true + epsilon) / (true + epsilon).sum()
    pred_closed = (pred + epsilon) / (pred + epsilon).sum()
    true_clr = np.log(true_closed) - np.log(true_closed).mean()
    pred_clr = np.log(pred_closed) - np.log(pred_closed).mean()
    aitchison = np.linalg.norm(true_clr - pred_clr) / np.sqrt(len(union))
    return {
        "weighted_jaccard": float(weighted_jaccard),
        "union_ratio_mae": float(union_mae),
        "aitchison_distance": float(aitchison),
    }


def evaluate_prediction(record: FormulaRecord, observed: dict[str, float], prediction: dict) -> dict:
    truth_set = set(record.composition)
    observed_set = set(observed)
    predicted_set = {row["material_id"] for row in prediction["materials"]}
    full_precision, full_recall, full_f1 = f1_sets(truth_set, predicted_set)
    hidden_precision, hidden_recall, hidden_f1 = f1_sets(
        truth_set - observed_set, predicted_set - observed_set
    )
    predicted_composition = {
        row["material_id"]: row["posterior_mean_ratio"] for row in prediction["materials"]
    }
    metrics = {
        "full_precision": full_precision,
        "full_recall": full_recall,
        "full_f1": full_f1,
        "hidden_precision": hidden_precision,
        "hidden_recall": hidden_recall,
        "hidden_f1": hidden_f1,
        "count_absolute_error": abs(len(truth_set) - len(predicted_set)),
        **composition_metrics(record.composition, predicted_composition),
    }
    vocabulary_probabilities = prediction["all_inclusion_probabilities"]
    metrics["inclusion_brier_in_vocabulary"] = float(np.mean([
        (probability - float(material in truth_set)) ** 2
        for material, probability in vocabulary_probabilities.items()
    ]))
    metrics["true_material_vocabulary_coverage"] = len(truth_set & set(vocabulary_probabilities)) / len(truth_set)
    return metrics


def mean_metrics(rows: list[dict]) -> dict[str, float]:
    keys = rows[0].keys()
    return {key: float(np.mean([row[key] for row in rows])) for key in keys}


def observed_from_mask(record: FormulaRecord, vocabulary: tuple[str, ...], seed: int, fraction: float) -> dict[str, float]:
    mask = deterministic_observation_mask(record, vocabulary, fraction, seed)
    return {
        material: record.composition[material]
        for material, keep in zip(vocabulary, mask)
        if keep
    }


def run_development(
    *,
    seed: int = 17,
    observed_fraction: float = 0.5,
    C: float = 0.3,
    group_dro_iterations: int = 8,
    posterior_samples: int = 200,
    model_names: tuple[str, ...] | None = None,
    graph_reducer: str = "weighted_mean",
    fold_kind: str = "development",
) -> dict:
    corpus = load_development_corpus()
    by_id = corpus.by_id()
    folds = load_folds(kind=fold_kind)
    all_results = {}
    selected_models = ABLATIONS if model_names is None else {
        name: ABLATIONS[name] for name in model_names
    }
    for model_name, channels in selected_models.items():
        fold_results = []
        for fold in folds:
            train_records = [by_id[row_id] for row_id in fold["train_reference_ids"]]
            test_records = [by_id[row_id] for row_id in fold["test_reference_ids"]]
            model = XiangjiCGIR(
                random_seed=seed,
                C=C,
                group_dro_iterations=group_dro_iterations,
                chemistry_proxy_map={
                    "agarwood_raw_resin": "agarwood",
                    "agarwood_soku_grade": "agarwood",
                    "agarwood_yellow_grade": "agarwood",
                    "agarwood_zhan_grade": "agarwood",
                    "agarwood_zhala_grade": "agarwood",
                    "agarwood_qinan_grade": "agarwood",
                    "clove_bark": "clove_bud",
                },
                graph_reducer=graph_reducer,
                enabled_channels=channels,
            ).fit(train_records)
            record_results = []
            for record in test_records:
                in_vocabulary_count = sum(material in model.material_index_ for material in record.composition)
                if in_vocabulary_count < 2:
                    record_results.append({
                        "reference_id": record.reference_id,
                        "work_id": record.work_id,
                        "status": "not_evaluable_fewer_than_two_in_vocabulary_components",
                        "true_material_count": len(record.composition),
                        "in_vocabulary_count": in_vocabulary_count,
                    })
                    continue
                observed = observed_from_mask(record, model.vocabulary_, seed, observed_fraction)
                prediction = model.predict(
                    title=record.title,
                    work_id=record.work_id,
                    observed=observed,
                    posterior_samples=posterior_samples,
                    random_seed=seed,
                    observation_fraction=observed_fraction,
                )
                record_results.append({
                    "reference_id": record.reference_id,
                    "work_id": record.work_id,
                    "status": "evaluated",
                    "observed_materials": observed,
                    "metrics": evaluate_prediction(record, observed, prediction),
                    "prediction": {key: value for key, value in prediction.items() if key != "posterior_samples"},
                })
            evaluated = [row for row in record_results if row["status"] == "evaluated"]
            fold_results.append({
                "fold_id": fold["fold_id"],
                "test_work_ids": fold["test_work_ids"],
                "training_formula_count": len(train_records),
                "test_formula_count": len(test_records),
                "evaluated_formula_count": len(evaluated),
                "not_evaluable_count": len(test_records) - len(evaluated),
                "metrics": mean_metrics([row["metrics"] for row in evaluated]),
                "diagnostics": model.diagnostics(),
                "records": record_results,
            })
        all_results[model_name] = {
            "source_macro_metrics": mean_metrics([row["metrics"] for row in fold_results]),
            "folds": fold_results,
        }
    return {
        "schema_version": "0.1",
        "task": "source-shifted partial-formula completion",
        "split": (
            "five development leave-one-work-out folds; quarantined Hong source excluded"
            if fold_kind == "development"
            else "ten frozen two-work-held-out primary folds; quarantined Hong source excluded"
        ),
        "fold_kind": fold_kind,
        "seed": seed,
        "observed_fraction": observed_fraction,
        "C": C,
        "group_dro_iterations": group_dro_iterations,
        "graph_reducer": graph_reducer,
        "reference_sha256": corpus.reference_sha256,
        "split_sha256": corpus.split_sha256,
        "sealed_work_id": corpus.sealed_work_id,
        "sealed_record_count": len(corpus.sealed_reference_ids),
        "quarantined_records_accessed_by_model": False,
        "models": all_results,
    }


def main() -> None:
    output = run_development()
    target = RESEARCH_ROOT / "experiments" / "cycle3_v1_1_development.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        name: payload["source_macro_metrics"] for name, payload in output["models"].items()
    }
    print(json.dumps({"output": str(target), "source_macro_metrics": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
