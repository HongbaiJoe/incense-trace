"""Final model-quarantined Hong-source confirmation after model freeze."""

from __future__ import annotations

import json
import gzip
from collections import defaultdict

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.partial_completion import ABLATIONS, evaluate_prediction, mean_metrics, observed_from_mask
from xiangji.evaluation.primary import exact_sign_flip_pvalue, source_bootstrap_interval
from xiangji.models.cgir import XiangjiCGIR
from xiangji.models.data import FormulaRecord, load_development_corpus


CHEMISTRY_PROXY_MAP = {
    "agarwood_raw_resin": "agarwood", "agarwood_soku_grade": "agarwood",
    "agarwood_yellow_grade": "agarwood", "agarwood_zhan_grade": "agarwood",
    "agarwood_zhala_grade": "agarwood", "agarwood_qinan_grade": "agarwood",
    "clove_bark": "clove_bud",
}


def load_hong_records(corpus) -> list[FormulaRecord]:
    reference = json.loads(
        (RESEARCH_ROOT / "data/curated/formula_reference_v0.1.json").read_text()
    )
    rows = [row for row in reference["records"] if row["reference_id"] in corpus.sealed_reference_ids]
    records = [FormulaRecord(
        reference_id=row["reference_id"], family_id=row["formula_family_id"],
        work_id=row["work_id"], title=row["formula_title_verbatim"],
        composition={key: float(value) for key, value in row["composition_aromatic_only"].items()},
    ) for row in rows]
    if len(records) != len(corpus.sealed_reference_ids):
        raise ValueError("Hong confirmation record count differs from the frozen registry")
    return records


def formula_paired_comparison(selected: dict, baseline: dict) -> dict:
    ids = sorted(set(selected) & set(baseline))
    differences = np.array([selected[row_id] - baseline[row_id] for row_id in ids])
    return {
        "unit": "formula within one historical work; exploratory",
        "formula_count": len(ids),
        "per_formula_difference": {row_id: float(value) for row_id, value in zip(ids, differences)},
        "mean_difference": float(differences.mean()),
        "formula_bootstrap_95_interval": source_bootstrap_interval(
            differences, seed=1901, draws=20000
        ),
        "exact_two_sided_sign_flip_pvalue": exact_sign_flip_pvalue(differences),
    }


def run_hong_confirmation(observed_fraction: float = 0.5) -> dict:
    corpus = load_development_corpus()
    test_records = load_hong_records(corpus)
    selection = json.loads((RESEARCH_ROOT / "experiments/cycle3_model_selection.json").read_text())
    model_names = tuple(selection["best_by_model"])
    results = {}
    formula_values = defaultdict(lambda: defaultdict(list))
    for model_name in model_names:
        configuration = selection["best_by_model"][model_name]
        seed_rows = []
        for seed in selection["seeds"]:
            model = XiangjiCGIR(
                random_seed=seed, C=configuration["C"],
                group_dro_iterations=configuration["group_dro_iterations"],
                graph_reducer=(
                    "weighted_mean" if configuration["graph_reducer"] == "not_applicable"
                    else configuration["graph_reducer"]
                ),
                chemistry_proxy_map=CHEMISTRY_PROXY_MAP,
                enabled_channels=ABLATIONS[model_name],
            ).fit(corpus.records)
            records = []
            for record in test_records:
                in_vocabulary = sum(material in model.material_index_ for material in record.composition)
                if in_vocabulary < 2:
                    records.append({
                        "reference_id": record.reference_id,
                        "status": "not_evaluable_fewer_than_two_in_vocabulary_components",
                        "true_material_count": len(record.composition),
                        "in_vocabulary_count": in_vocabulary,
                    })
                    continue
                observed = observed_from_mask(record, model.vocabulary_, seed, observed_fraction)
                prediction = model.predict(
                    title=record.title, work_id=record.work_id, observed=observed,
                    observation_fraction=observed_fraction, posterior_samples=200, random_seed=seed,
                )
                metrics = evaluate_prediction(record, observed, prediction)
                formula_values[model_name][record.reference_id].append(metrics["hidden_f1"])
                records.append({
                    "reference_id": record.reference_id,
                    "status": "evaluated",
                    "observed_materials": observed,
                    "metrics": metrics,
                    "selected_materials": prediction["materials"],
                    "count_posterior": prediction["count_posterior"],
                })
            evaluated = [row for row in records if row["status"] == "evaluated"]
            seed_rows.append({
                "seed": seed,
                "evaluated_formula_count": len(evaluated),
                "metrics": mean_metrics([row["metrics"] for row in evaluated]),
                "records": records,
            })
        results[model_name] = {
            "mean_across_seeds": {
                key: float(np.mean([row["metrics"][key] for row in seed_rows]))
                for key in seed_rows[0]["metrics"]
            },
            "sd_across_seeds": {
                key: float(np.std([row["metrics"][key] for row in seed_rows], ddof=1))
                for key in seed_rows[0]["metrics"]
            },
            "seed_runs": seed_rows,
        }
    formula_means = {
        model: {row_id: float(np.mean(values)) for row_id, values in rows.items()}
        for model, rows in formula_values.items()
    }
    selected = selection["selected_structured_model"]["model"]
    graph = selection["strongest_baseline"]["model"]
    return {
        "schema_version": "0.1",
        "task": "model-quarantined Hong-source confirmation",
        "investigator_blinded": False,
        "model_parameters_changed_after_primary_evaluation": False,
        "training_formula_count": len(corpus.records),
        "Hong_formula_count": len(test_records),
        "observed_fraction": observed_fraction,
        "results": results,
        "selected_vs_graph": formula_paired_comparison(formula_means[selected], formula_means[graph]),
        "selected_vs_frequency": formula_paired_comparison(formula_means[selected], formula_means["frequency"]),
    }


def main() -> None:
    result = run_hong_confirmation()
    raw = {"schema_version": result["schema_version"], "results": result["results"]}
    compact = {key: value for key, value in result.items() if key != "results"}
    compact["results"] = {
        name: {
            "mean_across_seeds": row["mean_across_seeds"],
            "sd_across_seeds": row["sd_across_seeds"],
            "seed_runs": [
                {key: seed_row[key] for key in ("seed", "evaluated_formula_count", "metrics")}
                for seed_row in row["seed_runs"]
            ],
        }
        for name, row in result["results"].items()
    }
    target = RESEARCH_ROOT / "experiments/cycle4_hong_confirmation.json"
    target.write_text(json.dumps(compact, ensure_ascii=False, indent=2), encoding="utf-8")
    raw_target = RESEARCH_ROOT / "experiments/cycle4_hong_records.json.gz"
    raw_target.write_bytes(gzip.compress(
        json.dumps(raw, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        compresslevel=9, mtime=0,
    ))
    print(json.dumps({
        "output": str(target),
        "raw_output": str(raw_target),
        "model_metrics": {name: row["mean_across_seeds"] for name, row in result["results"].items()},
        "selected_vs_graph": result["selected_vs_graph"],
        "selected_vs_frequency": result["selected_vs_frequency"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
