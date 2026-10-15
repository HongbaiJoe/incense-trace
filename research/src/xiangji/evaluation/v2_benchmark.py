"""Development selection and source-blocked evaluation for Xiangji V2."""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from dataclasses import asdict

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.partial_completion import composition_metrics, f1_sets
from xiangji.models.data import FormulaRecord, load_development_corpus, load_folds
from xiangji.models.source_stable_graph import (
    SourceStableGraphCompletion,
    SourceStableParameters,
)


SEEDS = (17, 29, 43, 71, 101)
PRIMARY_FRACTION = 0.5


def observed_materials(
    record: FormulaRecord,
    vocabulary: tuple[str, ...],
    seed: int,
    fraction: float,
    mechanism: str = "uniform",
) -> dict[str, float]:
    present = [i for i, material in enumerate(vocabulary) if material in record.composition]
    if len(present) < 2:
        raise ValueError("At least two in-vocabulary materials are required")
    count = min(len(present) - 1, max(1, round(len(present) * fraction)))
    key = f"{record.reference_id}|{fraction:.6f}|{seed}"
    if mechanism != "uniform":
        key += f"|{mechanism}"
    digest = hashlib.sha256(key.encode()).digest()
    generator = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    if mechanism == "uniform":
        selected = generator.choice(present, size=count, replace=False)
    elif mechanism == "abundance":
        mass = np.asarray([record.composition[vocabulary[i]] for i in present])
        key = np.log(np.clip(mass, 1e-12, None)) + generator.gumbel(size=len(present))
        selected = np.asarray(present)[np.argsort(-key)[:count]]
    elif mechanism == "prefix":
        order = {material: i for i, material in enumerate(record.composition)}
        selected = sorted(present, key=lambda i: order[vocabulary[i]])[:count]
    else:
        raise ValueError("Unknown observation mechanism")
    selected_set = {int(i) for i in selected}
    return {
        material: record.composition[material]
        for i, material in enumerate(vocabulary)
        if i in selected_set
    }


def evaluate_record(record: FormulaRecord, observed: dict[str, float], prediction: dict) -> dict[str, float]:
    truth = set(record.composition)
    known = set(observed)
    predicted = set(prediction["selected_materials"])
    precision, recall, f1 = f1_sets(truth - known, predicted - known)
    return {
        "hidden_precision": precision,
        "hidden_recall": recall,
        "hidden_f1": f1,
        "weighted_jaccard": composition_metrics(
            record.composition, prediction["composition"]
        )["weighted_jaccard"],
        "count_absolute_error": float(abs(len(truth) - len(predicted))),
        "hidden_reference_count": float(len(truth - known)),
    }


def aggregate_records(records: list[dict]) -> tuple[dict, dict, dict]:
    by_formula: dict[str, list[dict]] = defaultdict(list)
    formula_work = {}
    for row in records:
        by_formula[row["reference_id"]].append(row["metrics"])
        formula_work[row["reference_id"]] = row["work_id"]
    formula_metrics = {}
    by_work: dict[str, list[dict]] = defaultdict(list)
    for reference_id, values in by_formula.items():
        metrics = {
            key: float(np.mean([row[key] for row in values])) for key in values[0]
        }
        formula_metrics[reference_id] = metrics
        by_work[formula_work[reference_id]].append(metrics)
    work_metrics = {
        work: {
            "record_count": len(values),
            **{
                key: float(np.mean([row[key] for row in values]))
                for key in values[0]
            },
        }
        for work, values in sorted(by_work.items())
    }
    keys = [key for key in next(iter(work_metrics.values())) if key != "record_count"]
    macro = {
        key: float(np.mean([row[key] for row in work_metrics.values()])) for key in keys
    }
    return formula_metrics, work_metrics, macro


def exact_sign_flip_pvalue(differences: list[float] | np.ndarray) -> float:
    values = np.asarray(differences, dtype=float)
    observed = abs(float(values.mean()))
    null = [
        abs(float(np.mean(values * np.asarray(signs))))
        for signs in itertools.product((-1.0, 1.0), repeat=len(values))
    ]
    return float(np.mean(np.asarray(null) >= observed - 1e-12))


def paired_work_comparison(selected: dict, baseline: dict) -> dict:
    works = sorted(set(selected) & set(baseline))
    differences = [
        selected[work]["hidden_f1"] - baseline[work]["hidden_f1"] for work in works
    ]
    return {
        "unit": "historical_work_group",
        "work_count": len(works),
        "per_work_difference": dict(zip(works, differences)),
        "mean_difference": float(np.mean(differences)),
        "positive_work_count": int(np.sum(np.asarray(differences) > 0)),
        "exact_two_sided_sign_flip_pvalue": exact_sign_flip_pvalue(differences),
    }


def run_configuration(
    parameters: SourceStableParameters,
    fold_kind: str,
    *,
    fraction: float = PRIMARY_FRACTION,
    mechanism: str = "uniform",
    decoder_fraction: float | None = PRIMARY_FRACTION,
    keep_probabilities: bool = False,
) -> dict:
    corpus = load_development_corpus()
    by_id = corpus.by_id()
    rows = []
    fold_summaries = []
    for fold in load_folds(kind=fold_kind):
        training = [by_id[value] for value in fold["train_reference_ids"]]
        test = [by_id[value] for value in fold["test_reference_ids"]]
        model = SourceStableGraphCompletion(parameters).fit(training)
        fold_rows = []
        for seed in SEEDS:
            for record in test:
                if sum(material in model.index for material in record.composition) < 2:
                    continue
                observed = observed_materials(
                    record, model.vocabulary, seed, fraction, mechanism
                )
                prediction = model.predict(
                    observed, observation_fraction=decoder_fraction
                )
                row = {
                    "fold_id": fold["fold_id"],
                    "seed": seed,
                    "reference_id": record.reference_id,
                    "work_id": record.work_id,
                    "observed_materials": observed,
                    "metrics": evaluate_record(record, observed, prediction),
                }
                if keep_probabilities:
                    row["all_inclusion_probabilities"] = prediction[
                        "all_inclusion_probabilities"
                    ]
                rows.append(row)
                fold_rows.append(row)
        _, work, macro = aggregate_records(fold_rows)
        fold_summaries.append(
            {
                "fold_id": fold["fold_id"],
                "training_formula_count": len(training),
                "test_formula_count": len(test),
                "work_metrics": work,
                "source_macro_metrics": macro,
            }
        )
    formula, work, macro = aggregate_records(rows)
    return {
        "configuration": asdict(parameters),
        "fold_kind": fold_kind,
        "fraction": fraction,
        "mechanism": mechanism,
        "decoder_fraction": decoder_fraction,
        "evaluated_formula_count": len(formula),
        "source_macro_metrics": macro,
        "work_metrics": work,
        "fold_summaries": fold_summaries,
        "records": rows if keep_probabilities else [],
    }


def parameter_grids() -> dict[str, list[SourceStableParameters]]:
    return {
        "frequency": [SourceStableParameters(method="frequency")],
        "directed_graph": [
            SourceStableParameters(method="directed_graph", smoothing=smoothing, reducer=reducer)
            for smoothing in (0.5, 1.0, 2.0, 5.0)
            for reducer in ("mean", "max", "top2")
        ],
        "sscl": [
            SourceStableParameters(
                method="sscl",
                smoothing=smoothing,
                heterogeneity_penalty=penalty,
                stable_blend=blend,
                reducer=reducer,
            )
            for smoothing in (1.0, 2.0, 5.0)
            for penalty in (0.0, 0.25, 0.5, 1.0)
            for blend in (0.25, 0.5, 0.75, 1.0)
            for reducer in ("mean", "max")
        ],
        "ease": [
            SourceStableParameters(method="ease", ease_ridge=value)
            for value in (1.0, 10.0, 30.0, 100.0, 300.0, 1000.0)
        ],
        "slim": [
            SourceStableParameters(method="slim", slim_alpha=alpha, slim_l1_ratio=ratio)
            for alpha in (0.001, 0.01, 0.05, 0.1)
            for ratio in (0.1, 0.5, 0.9)
        ],
        "ppr": [
            SourceStableParameters(method="ppr", diffusion=value)
            for value in (0.1, 0.2, 0.4, 0.6, 0.8)
        ],
    }


def select_models() -> dict:
    results = {}
    selected = {}
    for family, grid in parameter_grids().items():
        rows = []
        for parameters in grid:
            result = run_configuration(parameters, "development")
            rows.append(
                {
                    "configuration": result["configuration"],
                    "source_macro_metrics": result["source_macro_metrics"],
                }
            )
        rows.sort(
            key=lambda row: (
                row["source_macro_metrics"]["hidden_f1"],
                row["source_macro_metrics"]["weighted_jaccard"],
            ),
            reverse=True,
        )
        results[family] = rows
        selected[family] = rows[0]["configuration"]
    return {
        "selection_unit": "historical_work_group",
        "selection_folds": "five_leave_one_work_out",
        "primary_metric": "source_macro_hidden_f1",
        "tie_breaker": "source_macro_weighted_jaccard",
        "selected": selected,
        "grids": results,
    }


def evaluate_selected(selection: dict) -> dict:
    models = {}
    for family, configuration in selection["selected"].items():
        models[family] = run_configuration(
            SourceStableParameters(**configuration), "primary"
        )
    frequency = models["frequency"]["work_metrics"]
    comparisons = {
        name: paired_work_comparison(result["work_metrics"], frequency)
        for name, result in models.items()
        if name != "frequency"
    }
    strongest = max(
        models,
        key=lambda name: models[name]["source_macro_metrics"]["hidden_f1"],
    )
    v1 = json.loads(
        (RESEARCH_ROOT / "experiments" / "cycle6_stress_tests.json").read_text()
    )["competitive_baselines"]["primary_results"]
    legacy = {
        name: row["source_macro_metrics"] for name, row in v1.items()
    }
    return {
        "primary_unit": "historical_work_group",
        "models": models,
        "comparisons_vs_frequency": comparisons,
        "strongest_v2_model": strongest,
        "strongest_v2_metrics": models[strongest]["source_macro_metrics"],
        "legacy_primary_comparators": legacy,
    }


def main() -> None:
    selection = select_models()
    selection_path = RESEARCH_ROOT / "experiments" / "v2_model_selection.json"
    selection_path.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    primary = evaluate_selected(selection)
    primary_path = RESEARCH_ROOT / "experiments" / "v2_primary_evaluation.json"
    primary_path.write_text(
        json.dumps(primary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "selection": str(selection_path),
                "primary": str(primary_path),
                "selected": selection["selected"],
                "primary_metrics": {
                    name: result["source_macro_metrics"]
                    for name, result in primary["models"].items()
                },
                "strongest": primary["strongest_v2_model"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
