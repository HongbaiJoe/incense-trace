"""Nested family-blocked evaluation for the auxiliary odor inverse task."""

from __future__ import annotations

import json

import numpy as np

from xiangji.baselines import ChemicalNNLS, FrequencyPrior, OdorKNN, RidgeComposition
from xiangji.data import RESEARCH_ROOT, load_corpus
from xiangji.metrics import evaluate
from xiangji.models.odor_inverse import ForwardConsistentInverse


FORWARD_STRENGTH_GRID = (0.0, 0.1, 0.3, 1.0, 3.0, 10.0)
CHEMISTRY_BLEND_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
PRIOR_MODEL_GRID = ("ridge", "odor_knn")


def family_indices(recipes: list[dict]) -> dict[str, list[int]]:
    return {
        family: [index for index, row in enumerate(recipes) if row["family"] == family]
        for family in sorted({row["family"] for row in recipes})
    }


def inner_score(
    corpus, outer_train: list[int], forward_strength: float,
    chemistry_blend: float, prior_model: str,
) -> float:
    recipes = corpus.recipes
    held_out_families = sorted({recipes[index]["family"] for index in outer_train})
    scores = []
    for family in held_out_families:
        validation = [index for index in outer_train if recipes[index]["family"] == family]
        training = [index for index in outer_train if recipes[index]["family"] != family]
        train_recipes = [recipes[index] for index in training]
        validation_recipes = [recipes[index] for index in validation]
        y_train = np.asarray([corpus.outcome(row) for row in train_recipes])
        y_validation = np.asarray([corpus.outcome(row) for row in validation_recipes])
        model = ForwardConsistentInverse(
            tuple(corpus.material_ids), corpus.material_matrix,
            forward_strength=forward_strength, chemistry_blend=chemistry_blend,
            prior_model=prior_model,
        ).fit(train_recipes, y_train)
        predictions = model.predict(validation_recipes)
        scores.append(evaluate(y_validation, predictions)["weighted_jaccard"])
    return float(np.mean(scores))


def select_inner(corpus, outer_train: list[int]) -> dict:
    rows = []
    for forward_strength in FORWARD_STRENGTH_GRID:
        for chemistry_blend in CHEMISTRY_BLEND_GRID:
            for prior_model in PRIOR_MODEL_GRID:
                rows.append({
                    "forward_strength": forward_strength,
                    "chemistry_blend": chemistry_blend,
                    "prior_model": prior_model,
                    "source_macro_weighted_jaccard": inner_score(
                        corpus, outer_train, forward_strength, chemistry_blend, prior_model
                    ),
                })
    # Prefer less chemical blending and weaker forward correction on exact ties.
    selected = max(rows, key=lambda row: (
        row["source_macro_weighted_jaccard"],
        -row["chemistry_blend"],
        -row["forward_strength"],
        row["prior_model"] == "odor_knn",
    ))
    return {"selected": selected, "grid": rows}


def baseline_models(corpus, train_size: int) -> dict:
    return {
        "frequency": FrequencyPrior(),
        "odor_knn": OdorKNN(neighbors=min(5, train_size)),
        "ridge": RidgeComposition(alpha=2.0),
        "legacy_forward_nnls": ChemicalNNLS(corpus.material_matrix),
    }


def run_nested_family_evaluation(seed: int = 17) -> dict:
    corpus = load_corpus()
    recipes = corpus.recipes
    by_family = family_indices(recipes)
    fold_rows = []
    pooled_truth, pooled_predictions = [], {}
    for fold_index, (family, test_indices) in enumerate(by_family.items()):
        train_indices = [index for index in range(len(recipes)) if index not in test_indices]
        train_recipes = [recipes[index] for index in train_indices]
        test_recipes = [recipes[index] for index in test_indices]
        y_train = np.asarray([corpus.outcome(row) for row in train_recipes])
        y_test = np.asarray([corpus.outcome(row) for row in test_recipes])
        selection = select_inner(corpus, train_indices)
        choice = selection["selected"]
        models = baseline_models(corpus, len(train_indices))
        models.update({
            "xiangji_forward_consistent": ForwardConsistentInverse(
                tuple(corpus.material_ids), corpus.material_matrix,
                forward_strength=choice["forward_strength"],
                chemistry_blend=choice["chemistry_blend"],
                prior_model=choice["prior_model"],
            ),
            "no_chemical_ablation": ForwardConsistentInverse(
                tuple(corpus.material_ids), corpus.material_matrix,
                forward_strength=choice["forward_strength"], chemistry_blend=0.0,
                prior_model=choice["prior_model"],
            ),
            "shuffled_chemical_control": ForwardConsistentInverse(
                tuple(corpus.material_ids), corpus.material_matrix,
                forward_strength=choice["forward_strength"],
                chemistry_blend=choice["chemistry_blend"],
                prior_model=choice["prior_model"],
                chemical_permutation_seed=seed + fold_index,
            ),
        })
        fold_predictions, fold_metrics = {}, {}
        for name, model in models.items():
            model.fit(train_recipes, y_train)
            prediction = model.predict(test_recipes)
            fold_predictions[name] = prediction
            fold_metrics[name] = evaluate(y_test, prediction)
            pooled_predictions.setdefault(name, []).append(prediction)
        pooled_truth.append(y_test)
        fold_rows.append({
            "held_out_family": family,
            "n_train": len(train_indices),
            "n_test": len(test_indices),
            "inner_selection": selection,
            "metrics": fold_metrics,
        })
    truth = np.concatenate(pooled_truth)
    pooled = {
        name: evaluate(truth, np.concatenate(blocks))
        for name, blocks in pooled_predictions.items()
    }
    return {
        "schema_version": "0.1",
        "task": "odor-conditioned inverse formulation",
        "scope": "auxiliary provenance-limited legacy corpus",
        "validation": "nested leave-one-family-out; inner family folds select hyperparameters",
        "selection_metric": "inner source-macro weighted Jaccard at top 6",
        "forward_strength_grid": list(FORWARD_STRENGTH_GRID),
        "chemistry_blend_grid": list(CHEMISTRY_BLEND_GRID),
        "prior_model_grid": list(PRIOR_MODEL_GRID),
        "seed": seed,
        "chemical_profile_coverage": 14 / 25,
        "folds": fold_rows,
        "pooled_metrics": pooled,
    }


def main() -> None:
    result = run_nested_family_evaluation()
    target = RESEARCH_ROOT / "experiments" / "cycle3_odor_inverse_nested.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), "pooled_metrics": result["pooled_metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
