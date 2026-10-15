"""Run transparent baselines under reproducible and extrapolative splits."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from xiangji.baselines import BM25MaterialModel, ChemicalNNLS, FrequencyPrior, OdorKNN, RidgeComposition
from xiangji.data import RESEARCH_ROOT, historical_hash_split, leave_one_family_out, load_corpus
from xiangji.metrics import evaluate


def models(material_matrix: np.ndarray, train_size: int) -> dict:
    return {
        "frequency": FrequencyPrior(),
        "bm25_char": BM25MaterialModel(neighbors=min(5, train_size)),
        "odor_knn": OdorKNN(neighbors=min(5, train_size)),
        "ridge": RidgeComposition(alpha=2.0),
        "chemical_nnls": ChemicalNNLS(material_matrix),
    }


def run_fold(corpus, train_indices: list[int], test_indices: list[int]) -> tuple[dict, dict, dict]:
    train = [corpus.recipes[i] for i in train_indices]
    test = [corpus.recipes[i] for i in test_indices]
    y_train = np.asarray([corpus.outcome(r) for r in train])
    y_test = np.asarray([corpus.outcome(r) for r in test])
    fold_metrics, predictions = {}, {}
    for name, model in models(corpus.material_matrix, len(train)).items():
        model.fit(train, y_train)
        score = model.predict(test)
        fold_metrics[name] = evaluate(y_test, score)
        predictions[name] = score.tolist()
    truth = {"ids": [r["id"] for r in test], "outcomes": y_test.tolist()}
    return fold_metrics, predictions, truth


def pooled_metrics(truths: list[dict], predictions: list[dict]) -> dict:
    result = {}
    model_names = predictions[0].keys()
    y_true = np.concatenate([np.asarray(item["outcomes"]) for item in truths], axis=0)
    for name in model_names:
        y_score = np.concatenate([np.asarray(item[name]) for item in predictions], axis=0)
        result[name] = evaluate(y_true, y_score)
    return result


def load_legacy_v24_scores(corpus, test_indices: list[int]) -> np.ndarray | None:
    path = RESEARCH_ROOT / "experiments" / "frozen_results" / "reproduction_v24.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_id = {row["id"]: row["predicted"] for row in payload["test_detail"]}
    material_index = {material_id: i for i, material_id in enumerate(corpus.material_ids)}
    scores = np.zeros((len(test_indices), len(corpus.material_ids)), dtype=float)
    for row_index, recipe_index in enumerate(test_indices):
        for material_id, weight in by_id[corpus.recipes[recipe_index]["id"]].items():
            scores[row_index, material_index[material_id]] = weight
    return scores


def main() -> None:
    corpus = load_corpus()
    hash_train, hash_test = historical_hash_split(corpus.recipes)
    hash_metrics, hash_predictions, hash_truth = run_fold(corpus, hash_train, hash_test)
    legacy_scores = load_legacy_v24_scores(corpus, hash_test)
    if legacy_scores is not None:
        y_hash = np.asarray(hash_truth["outcomes"])
        hash_metrics["legacy_v24"] = evaluate(y_hash, legacy_scores)
        hash_predictions["legacy_v24"] = legacy_scores.tolist()

    family_folds, family_predictions, family_truths = [], [], []
    for family, train, test in leave_one_family_out(corpus.recipes):
        fold_metrics, predictions, truth = run_fold(corpus, train, test)
        family_folds.append({"held_out_family": family, "n_train": len(train), "n_test": len(test), "metrics": fold_metrics})
        family_predictions.append(predictions)
        family_truths.append(truth)

    report = {
        "protocol": {
            "historical_hash_split": "Exact split used by website model v2.4; retained for reproduction, not external validity.",
            "leave_one_family_out": "Each semantic style family is held out once. This is family extrapolation, not cross-document validation.",
            "prediction_cardinality": 6,
        },
        "historical_hash_split": {
            "train_ids": [corpus.recipes[i]["id"] for i in hash_train],
            "test_ids": [corpus.recipes[i]["id"] for i in hash_test],
            "metrics": hash_metrics,
            "truth": hash_truth,
            "predictions": hash_predictions,
        },
        "leave_one_family_out": {
            "folds": family_folds,
            "pooled_metrics": pooled_metrics(family_truths, family_predictions),
            "fold_records": [
                {
                    "held_out_family": fold["held_out_family"],
                    "truth": truth,
                    "predictions": prediction,
                }
                for fold, truth, prediction in zip(family_folds, family_truths, family_predictions)
            ],
        },
    }
    output = RESEARCH_ROOT / "experiments" / "baseline_results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "hash_split": hash_metrics,
        "leave_one_family_out": report["leave_one_family_out"]["pooled_metrics"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
