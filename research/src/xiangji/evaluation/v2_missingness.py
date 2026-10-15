"""Observation-mechanism stress tests for the selected V2 models."""

from __future__ import annotations

import json

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.v2_benchmark import aggregate_records
from xiangji.evaluation.v2_nested_cross_work import evaluate_split, load_all_records
from xiangji.models.source_stable_graph import SourceStableParameters


def run() -> dict:
    nested = json.loads(
        (RESEARCH_ROOT / "experiments" / "v2_nested_cross_work.json").read_text()
    )
    records = list(load_all_records())
    outer = {row["outer_test_work"]: row for row in nested["outer_details"]}
    selected_names = ("frequency", "directed_graph", "sscl", "ease")
    conditions = []
    for fraction in (0.25, 0.5, 0.75):
        for mechanism in ("uniform", "abundance", "prefix"):
            conditions.append((mechanism, fraction, fraction))
        conditions.append(("uniform_unknown_fraction", fraction, None))
    results = {}
    for mechanism, fraction, decoder_fraction in conditions:
        mask_mechanism = "uniform" if mechanism == "uniform_unknown_fraction" else mechanism
        key = f"{mechanism}_{fraction:.2f}"
        results[key] = {
            "mechanism": mechanism,
            "observed_fraction": fraction,
            "decoder_fraction": decoder_fraction,
            "models": {},
        }
        for name in selected_names:
            rows = []
            for work in sorted(outer):
                training = [record for record in records if record.work_id != work]
                test = [record for record in records if record.work_id == work]
                configuration = SourceStableParameters(
                    **outer[work]["selected_configurations"][name]
                )
                rows.extend(evaluate_split(
                    configuration,
                    training,
                    test,
                    fraction=fraction,
                    mechanism=mask_mechanism,
                    decoder_fraction=decoder_fraction,
                ))
            _, work_metrics, source_macro = aggregate_records(rows)
            results[key]["models"][name] = {
                "source_macro_metrics": source_macro,
                "work_metrics": work_metrics,
            }
    return {
        "schema_version": "0.2",
        "evaluation_unit": "historical_work_group",
        "design": "six_outer_works_with_configuration_selected_inside_each_outer_fold",
        "models": list(selected_names),
        "conditions": results,
    }


def main() -> None:
    result = run()
    path = RESEARCH_ROOT / "experiments" / "v2_missingness_stress.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "output": str(path),
        "conditions": {
            key: {
                name: row["source_macro_metrics"]["hidden_f1"]
                for name, row in condition["models"].items()
            }
            for key, condition in result["conditions"].items()
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
