"""Leakage-controlled weak supervision for the Xiangji V2.5 benchmark."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.v2_benchmark import (
    aggregate_records,
    evaluate_record,
    observed_materials,
    paired_work_comparison,
    parameter_grids,
)
from xiangji.evaluation.v2_nested_cross_work import load_all_records
from xiangji.models.data import FormulaRecord
from xiangji.models.source_stable_graph import (
    SourceStableGraphCompletion,
    SourceStableParameters,
)


SEEDS = (17, 29, 43, 71, 101)
WEAK_LABEL_WEIGHTS = (0.0, 0.10, 0.25, 0.50, 1.0)


@dataclass(frozen=True)
class WeakFormula:
    record: FormulaRecord
    candidate_id: str
    collection: str
    family_size: int


def _candidate_family_map() -> dict[str, str]:
    payload = json.loads(
        (
            RESEARCH_ROOT
            / "data"
            / "interim"
            / "formula_genealogy_candidates_v0.1.json"
        ).read_text(encoding="utf-8")
    )
    mapping = {}
    for family in payload["families"]:
        for candidate_id in family["member_candidate_ids"]:
            mapping[candidate_id] = family["formula_family_candidate_id"]
    return mapping


def load_weak_pool() -> tuple[WeakFormula, ...]:
    """Load ratio-ready records after removing gold records and gold-linked families."""
    reference = json.loads(
        (
            RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
        ).read_text(encoding="utf-8")
    )
    candidates = json.loads(
        (
            RESEARCH_ROOT
            / "data"
            / "interim"
            / "structured_formula_candidates_v0.1.json"
        ).read_text(encoding="utf-8")
    )["records"]
    family_map = _candidate_family_map()

    def family_id(candidate_id: str) -> str:
        return family_map.get(candidate_id, f"singleton-{candidate_id}")

    gold_candidate_ids = {row["candidate_id"] for row in reference["records"]}
    gold_family_ids = {family_id(value) for value in gold_candidate_ids}
    eligible = [
        row
        for row in candidates
        if row["ratio_ready_automatic"]
        and row["candidate_id"] not in gold_candidate_ids
        and family_id(row["candidate_id"]) not in gold_family_ids
        and len(row["composition_aromatic_only"]) >= 2
    ]
    family_sizes = Counter(family_id(row["candidate_id"]) for row in eligible)
    weak = []
    for row in eligible:
        composition = {
            key: float(value)
            for key, value in row["composition_aromatic_only"].items()
        }
        total = sum(composition.values())
        if not np.isfinite(total) or total <= 0:
            continue
        composition = {key: value / total for key, value in composition.items()}
        family = family_id(row["candidate_id"])
        weak.append(
            WeakFormula(
                record=FormulaRecord(
                    reference_id=f"weak-{row['candidate_id']}",
                    family_id=family,
                    work_id=f"weak_{row['collection']}",
                    title=row["formula_title_candidate"],
                    composition=composition,
                ),
                candidate_id=row["candidate_id"],
                collection=row["collection"],
                family_size=family_sizes[family],
            )
        )
    return tuple(weak)


def work_collection_map() -> dict[str, str]:
    payload = json.loads(
        (
            RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
        ).read_text(encoding="utf-8")
    )
    mapping = {}
    for row in payload["records"]:
        work = row["work_id"]
        collection = row["collection"]
        if work in mapping and mapping[work] != collection:
            raise ValueError(f"Work {work} maps to multiple collections")
        mapping[work] = collection
    return mapping


def assemble_training(
    gold: list[FormulaRecord],
    weak: tuple[WeakFormula, ...],
    weak_label_weight: float,
    forbidden_collections: set[str],
) -> tuple[list[FormulaRecord], np.ndarray, dict]:
    selected = [row for row in weak if row.collection not in forbidden_collections]
    records = list(gold)
    weights = [1.0] * len(gold)
    if weak_label_weight > 0:
        records.extend(row.record for row in selected)
        weights.extend(weak_label_weight / row.family_size for row in selected)
    return records, np.asarray(weights, dtype=float), {
        "gold_formula_count": len(gold),
        "eligible_weak_record_count": len(selected),
        "eligible_weak_family_count": len({row.record.family_id for row in selected}),
        "active_weak_record_count": len(selected) if weak_label_weight > 0 else 0,
        "effective_weak_weight": float(
            sum(weak_label_weight / row.family_size for row in selected)
        )
        if weak_label_weight > 0
        else 0.0,
        "forbidden_collections": sorted(forbidden_collections),
    }


def evaluate_split(
    parameters: SourceStableParameters,
    gold_training: list[FormulaRecord],
    test: list[FormulaRecord],
    weak: tuple[WeakFormula, ...],
    weak_label_weight: float,
    forbidden_collections: set[str],
) -> tuple[list[dict], dict]:
    training, weights, exposure = assemble_training(
        gold_training, weak, weak_label_weight, forbidden_collections
    )
    model = SourceStableGraphCompletion(parameters).fit(training, weights)
    rows = []
    for seed in SEEDS:
        for record in test:
            if sum(material in model.index for material in record.composition) < 2:
                continue
            observed = observed_materials(record, model.vocabulary, seed, 0.5, "uniform")
            prediction = model.predict(observed, observation_fraction=0.5)
            rows.append(
                {
                    "seed": seed,
                    "reference_id": record.reference_id,
                    "work_id": record.work_id,
                    "metrics": evaluate_record(record, observed, prediction),
                }
            )
    return rows, exposure


def select_inside_outer_fold(
    grid: list[SourceStableParameters],
    gold_training: list[FormulaRecord],
    weak: tuple[WeakFormula, ...],
    outer_forbidden_collection: str,
    collection_by_work: dict[str, str],
) -> tuple[SourceStableParameters, float, list[dict]]:
    candidates = []
    works = sorted({record.work_id for record in gold_training})
    for parameters in grid:
        for weak_label_weight in WEAK_LABEL_WEIGHTS:
            rows = []
            exposures = []
            for inner_work in works:
                inner_training = [
                    record for record in gold_training if record.work_id != inner_work
                ]
                inner_test = [
                    record for record in gold_training if record.work_id == inner_work
                ]
                fold_rows, exposure = evaluate_split(
                    parameters,
                    inner_training,
                    inner_test,
                    weak,
                    weak_label_weight,
                    {
                        outer_forbidden_collection,
                        collection_by_work[inner_work],
                    },
                )
                rows.extend(fold_rows)
                exposures.append(exposure)
            _, _, macro = aggregate_records(rows)
            candidates.append(
                {
                    "configuration": asdict(parameters),
                    "weak_label_weight": weak_label_weight,
                    "source_macro_metrics": macro,
                    "inner_exposures": exposures,
                }
            )
    candidates.sort(
        key=lambda row: (
            row["source_macro_metrics"]["hidden_f1"],
            row["source_macro_metrics"]["weighted_jaccard"],
            -row["weak_label_weight"],
        ),
        reverse=True,
    )
    selected = candidates[0]
    return (
        SourceStableParameters(**selected["configuration"]),
        float(selected["weak_label_weight"]),
        candidates,
    )


def run() -> dict:
    gold = list(load_all_records())
    weak = load_weak_pool()
    collection_by_work = work_collection_map()
    works = sorted({record.work_id for record in gold})
    grids = parameter_grids()
    families = ("directed_graph", "sscl")
    model_rows = {family: [] for family in families}
    outer_details = []
    for outer_work in works:
        gold_training = [record for record in gold if record.work_id != outer_work]
        test = [record for record in gold if record.work_id == outer_work]
        outer_collection = collection_by_work[outer_work]
        selections = {}
        for family in families:
            parameters, weak_label_weight, candidates = select_inside_outer_fold(
                grids[family],
                gold_training,
                weak,
                outer_collection,
                collection_by_work,
            )
            fold_rows, exposure = evaluate_split(
                parameters,
                gold_training,
                test,
                weak,
                weak_label_weight,
                {outer_collection},
            )
            model_rows[family].extend(fold_rows)
            selections[family] = {
                "configuration": asdict(parameters),
                "weak_label_weight": weak_label_weight,
                "outer_training_exposure": exposure,
                "top_five_inner_configurations": candidates[:5],
            }
        outer_details.append(
            {
                "outer_test_work": outer_work,
                "outer_test_collection": outer_collection,
                "gold_training_formula_count": len(gold_training),
                "gold_test_formula_count": len(test),
                "selected_models": selections,
            }
        )

    models = {}
    for family, rows in model_rows.items():
        formula, work, macro = aggregate_records(rows)
        models[family] = {
            "evaluated_formula_count": len(formula),
            "work_metrics": work,
            "source_macro_metrics": macro,
        }

    gold_only = json.loads(
        (
            RESEARCH_ROOT / "experiments" / "v2_nested_cross_work.json"
        ).read_text(encoding="utf-8")
    )
    comparisons = {
        family: paired_work_comparison(
            models[family]["work_metrics"],
            gold_only["models"][family]["work_metrics"],
        )
        for family in families
    }
    return {
        "schema_version": "0.1",
        "design": "nested_leave_one_work_out_with_collection_blocked_weak_supervision",
        "discovery_candidate_count": 592,
        "ratio_ready_candidate_count": 296,
        "gold_formula_count": len(gold),
        "eligible_weak_record_count": len(weak),
        "eligible_weak_family_count": len({row.record.family_id for row in weak}),
        "weak_label_weight_grid": list(WEAK_LABEL_WEIGHTS),
        "models": models,
        "comparisons_vs_gold_only_same_model": comparisons,
        "outer_details": outer_details,
    }


def main() -> None:
    result = run()
    path = RESEARCH_ROOT / "experiments" / "v2_5_weak_supervision.json"
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(path),
                "data": {
                    key: result[key]
                    for key in (
                        "discovery_candidate_count",
                        "ratio_ready_candidate_count",
                        "gold_formula_count",
                        "eligible_weak_record_count",
                        "eligible_weak_family_count",
                    )
                },
                "models": {
                    name: row["source_macro_metrics"]
                    for name, row in result["models"].items()
                },
                "comparisons": result["comparisons_vs_gold_only_same_model"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
