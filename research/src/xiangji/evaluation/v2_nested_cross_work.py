"""Nested leave-one-work-out evaluation across all six Xiangji work groups."""

from __future__ import annotations

import json
from dataclasses import asdict

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.v2_benchmark import (
    SEEDS,
    aggregate_records,
    evaluate_record,
    observed_materials,
    paired_work_comparison,
    parameter_grids,
)
from xiangji.models.data import FormulaRecord
from xiangji.models.source_stable_graph import (
    SourceStableGraphCompletion,
    SourceStableParameters,
)


def load_all_records() -> tuple[FormulaRecord, ...]:
    payload = json.loads(
        (RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json").read_text()
    )
    return tuple(
        FormulaRecord(
            reference_id=row["reference_id"],
            family_id=row["formula_family_id"],
            work_id=row["work_id"],
            title=row["formula_title_verbatim"],
            composition={
                key: float(value)
                for key, value in row["composition_aromatic_only"].items()
            },
        )
        for row in payload["records"]
    )


def evaluate_split(
    parameters: SourceStableParameters,
    training: list[FormulaRecord],
    test: list[FormulaRecord],
    *,
    fraction: float = 0.5,
    mechanism: str = "uniform",
    decoder_fraction: float | None = 0.5,
    keep_probabilities: bool = False,
) -> list[dict]:
    model = SourceStableGraphCompletion(parameters).fit(training)
    rows = []
    mask_mechanism = "uniform" if mechanism == "uniform_unknown_fraction" else mechanism
    for seed in SEEDS:
        for record in test:
            if sum(material in model.index for material in record.composition) < 2:
                continue
            observed = observed_materials(
                record, model.vocabulary, seed, fraction, mask_mechanism
            )
            prediction = model.predict(observed, observation_fraction=decoder_fraction)
            row = {
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
    return rows


def select_inside_outer_fold(
    family: str,
    grid: list[SourceStableParameters],
    training: list[FormulaRecord],
) -> tuple[SourceStableParameters, list[dict]]:
    works = sorted({record.work_id for record in training})
    candidates = []
    for parameters in grid:
        rows = []
        for work in works:
            inner_training = [record for record in training if record.work_id != work]
            inner_test = [record for record in training if record.work_id == work]
            rows.extend(evaluate_split(parameters, inner_training, inner_test))
        _, _, macro = aggregate_records(rows)
        candidates.append({
            "configuration": asdict(parameters),
            "source_macro_metrics": macro,
        })
    candidates.sort(
        key=lambda row: (
            row["source_macro_metrics"]["hidden_f1"],
            row["source_macro_metrics"]["weighted_jaccard"],
        ),
        reverse=True,
    )
    return SourceStableParameters(**candidates[0]["configuration"]), candidates


def run() -> dict:
    records = list(load_all_records())
    works = sorted({record.work_id for record in records})
    grids = parameter_grids()
    families = ("frequency", "directed_graph", "sscl", "ease", "slim", "ppr")
    model_rows = {family: [] for family in families}
    outer_details = []
    for outer_work in works:
        training = [record for record in records if record.work_id != outer_work]
        test = [record for record in records if record.work_id == outer_work]
        selections = {}
        inner_summaries = {}
        for family in families:
            selected, candidates = select_inside_outer_fold(family, grids[family], training)
            selections[family] = asdict(selected)
            inner_summaries[family] = candidates[:5]
            model_rows[family].extend(evaluate_split(selected, training, test))
        outer_details.append({
            "outer_test_work": outer_work,
            "training_work_count": len(works) - 1,
            "training_formula_count": len(training),
            "test_formula_count": len(test),
            "selected_configurations": selections,
            "top_five_inner_configurations": inner_summaries,
        })
    models = {}
    for family, rows in model_rows.items():
        formula, work, macro = aggregate_records(rows)
        models[family] = {
            "evaluated_formula_count": len(formula),
            "work_metrics": work,
            "source_macro_metrics": macro,
        }
    frequency = models["frequency"]["work_metrics"]
    comparisons = {
        family: paired_work_comparison(row["work_metrics"], frequency)
        for family, row in models.items()
        if family != "frequency"
    }
    strongest = max(
        models,
        key=lambda family: models[family]["source_macro_metrics"]["hidden_f1"],
    )
    return {
        "schema_version": "0.2",
        "design": "nested_leave_one_work_out_across_six_work_groups",
        "outer_work_count": len(works),
        "hyperparameter_selection": "inner_leave_one_work_out_within_each_outer_training_set",
        "mask_seeds": list(SEEDS),
        "observed_fraction": 0.5,
        "models": models,
        "comparisons_vs_frequency": comparisons,
        "strongest_model": strongest,
        "strongest_metrics": models[strongest]["source_macro_metrics"],
        "outer_details": outer_details,
    }


def main() -> None:
    result = run()
    path = RESEARCH_ROOT / "experiments" / "v2_nested_cross_work.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "output": str(path),
        "metrics": {
            name: row["source_macro_metrics"] for name, row in result["models"].items()
        },
        "comparisons": result["comparisons_vs_frequency"],
        "strongest": result["strongest_model"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
