"""Development-only hyperparameter selection for Xiangji-CGIR T1."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.partial_completion import ABLATIONS, run_development


METRICS = (
    "hidden_f1",
    "weighted_jaccard",
    "aitchison_distance",
    "count_absolute_error",
)


def selection_key(row: dict) -> tuple[float, float, float]:
    metrics = row["mean_metrics"]
    return (
        metrics["hidden_f1"],
        metrics["weighted_jaccard"],
        -metrics["aitchison_distance"],
    )


def run_selection() -> dict:
    config_path = RESEARCH_ROOT / "configs" / "model" / "xiangji_cgir_v1.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    seeds = config["random_seeds"]
    c_grid = config["inclusion_decoder"]["C_grid"]
    dro_iterations = [0, config["group_dro"]["iterations"]]
    graph_reducers = config["selection"]["graph_reducer_grid"]
    non_graph_models = ("frequency", "source_prior", "title_only")
    graph_models = ("graph_only", "full_no_chemistry", "xiangji_cgir_v1")
    model_names = non_graph_models + graph_models
    rows: defaultdict[tuple[str, float, int, str], list[dict]] = defaultdict(list)

    for seed in seeds:
        for C in c_grid:
            for dro in dro_iterations:
                non_graph_result = run_development(
                    seed=seed,
                    C=C,
                    group_dro_iterations=dro,
                    posterior_samples=20,
                    model_names=non_graph_models,
                )
                for model_name in non_graph_models:
                    metrics = non_graph_result["models"][model_name]["source_macro_metrics"]
                    rows[(model_name, C, dro, "not_applicable")].append({
                        "seed": seed,
                        "metrics": {key: metrics[key] for key in METRICS},
                    })
                for reducer in graph_reducers:
                    graph_result = run_development(
                        seed=seed,
                        C=C,
                        group_dro_iterations=dro,
                        posterior_samples=20,
                        model_names=graph_models,
                        graph_reducer=reducer,
                    )
                    for model_name in graph_models:
                        metrics = graph_result["models"][model_name]["source_macro_metrics"]
                        rows[(model_name, C, dro, reducer)].append({
                            "seed": seed,
                            "metrics": {key: metrics[key] for key in METRICS},
                        })

    candidates = []
    for (model_name, C, dro, reducer), seed_rows in rows.items():
        summary = {
            key: float(np.mean([row["metrics"][key] for row in seed_rows]))
            for key in METRICS
        }
        spread = {
            key: float(np.std([row["metrics"][key] for row in seed_rows], ddof=1))
            for key in METRICS
        }
        candidates.append({
            "model": model_name,
            "C": C,
            "group_dro_iterations": dro,
            "graph_reducer": reducer,
            "mean_metrics": summary,
            "sd_across_seeds": spread,
            "seed_results": seed_rows,
        })

    best_by_model = {}
    for model_name in model_names:
        options = [row for row in candidates if row["model"] == model_name]
        best_by_model[model_name] = max(options, key=selection_key)

    baseline_names = ("frequency", "source_prior", "title_only", "graph_only")
    strongest_baseline = max(
        (best_by_model[name] for name in baseline_names), key=selection_key
    )
    structured_candidates = [
        best_by_model["full_no_chemistry"], best_by_model["xiangji_cgir_v1"]
    ]
    selected = max(structured_candidates, key=selection_key)
    advances = selection_key(selected) >= selection_key(strongest_baseline)

    return {
        "schema_version": "0.1",
        "scope": "development folds only; Hong records quarantined from model statistics",
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "selection_order": [
            "maximize mean source-macro hidden F1",
            "maximize mean source-macro weighted Jaccard",
            "minimize mean source-macro Aitchison distance",
        ],
        "seeds": seeds,
        "C_grid": c_grid,
        "group_dro_iterations_grid": dro_iterations,
        "graph_reducer_grid": graph_reducers,
        "best_by_model": best_by_model,
        "strongest_baseline": strongest_baseline,
        "selected_structured_model": selected,
        "advancement_gate_passed": advances,
        "all_candidates": candidates,
    }


def main() -> None:
    result = run_selection()
    target = RESEARCH_ROOT / "experiments" / "cycle3_model_selection.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(target),
        "strongest_baseline": result["strongest_baseline"],
        "selected_structured_model": result["selected_structured_model"],
        "advancement_gate_passed": result["advancement_gate_passed"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
