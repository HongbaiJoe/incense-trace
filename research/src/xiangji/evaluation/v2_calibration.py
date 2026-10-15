"""Nested work-level calibration analysis for the selected SSCL model."""

from __future__ import annotations

import json
from collections import defaultdict

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit, logit

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.v2_nested_cross_work import evaluate_split, load_all_records
from xiangji.models.source_stable_graph import SourceStableParameters


def adaptive_calibration_error(probability: np.ndarray, label: np.ndarray, bins: int = 10) -> float:
    if not len(probability):
        return float("nan")
    order = np.argsort(probability)
    groups = [group for group in np.array_split(order, min(bins, len(order))) if len(group)]
    return float(sum(
        len(group) / len(order)
        * abs(float(probability[group].mean()) - float(label[group].mean()))
        for group in groups
    ))


def temperature_scale(probability: np.ndarray, temperature: float) -> np.ndarray:
    return expit(logit(np.clip(probability, 1e-6, 1 - 1e-6)) / temperature)


def logit_calibrate(probability: np.ndarray, slope: float, intercept: float) -> np.ndarray:
    return expit(slope * logit(np.clip(probability, 1e-6, 1 - 1e-6)) + intercept)


def candidate_rows(split_rows: list[dict], by_id: dict[str, object]) -> list[dict]:
    output = []
    for record in split_rows:
        truth = set(by_id[record["reference_id"]].composition)
        observed = set(record["observed_materials"])
        for material, probability in record["all_inclusion_probabilities"].items():
            if material in observed:
                continue
            output.append({
                "reference_id": record["reference_id"],
                "work_id": record["work_id"],
                "probability": float(probability),
                "label": int(material in truth),
            })
    return output


def fit_temperature(rows: list[dict]) -> float:
    probability = np.asarray([row["probability"] for row in rows])
    label = np.asarray([row["label"] for row in rows])

    def objective(log_temperature: float) -> float:
        calibrated = temperature_scale(probability, float(np.exp(log_temperature)))
        return float(-np.mean(
            label * np.log(np.clip(calibrated, 1e-9, 1.0))
            + (1 - label) * np.log(np.clip(1 - calibrated, 1e-9, 1.0))
        ))

    optimum = minimize_scalar(objective, bounds=(-3.0, 3.0), method="bounded")
    return float(np.exp(optimum.x))


def fit_logit_calibrator(rows: list[dict]) -> tuple[float, float]:
    probability = np.asarray([row["probability"] for row in rows])
    label = np.asarray([row["label"] for row in rows])
    raw_logit = logit(np.clip(probability, 1e-6, 1 - 1e-6))

    def objective(parameters: np.ndarray) -> float:
        calibrated = expit(np.exp(parameters[0]) * raw_logit + parameters[1])
        return float(-np.mean(
            label * np.log(np.clip(calibrated, 1e-9, 1.0))
            + (1 - label) * np.log(np.clip(1 - calibrated, 1e-9, 1.0))
        ))

    optimum = minimize(objective, np.asarray([0.0, 0.0]), method="BFGS")
    return float(np.exp(optimum.x[0])), float(optimum.x[1])


def summarize(rows: list[dict], field: str) -> dict:
    by_formula: dict[str, list[tuple[float, int]]] = defaultdict(list)
    formula_work = {}
    for row in rows:
        by_formula[row["reference_id"]].append((row[field], row["label"]))
        formula_work[row["reference_id"]] = row["work_id"]
    work_formula: dict[str, list[dict]] = defaultdict(list)
    work_candidates: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for reference_id, values in by_formula.items():
        probability = np.asarray([value for value, _ in values])
        label = np.asarray([value for _, value in values])
        work = formula_work[reference_id]
        work_formula[work].append({
            "brier": float(np.mean((probability - label) ** 2)),
            "nll": float(-np.mean(
                label * np.log(np.clip(probability, 1e-9, 1.0))
                + (1 - label) * np.log(np.clip(1 - probability, 1e-9, 1.0))
            )),
        })
        work_candidates[work].extend(values)
    work_metrics = {}
    for work in sorted(work_formula):
        probability = np.asarray([value for value, _ in work_candidates[work]])
        label = np.asarray([value for _, value in work_candidates[work]])
        high = probability >= 0.8
        work_metrics[work] = {
            "formula_count": len(work_formula[work]),
            "candidate_count": len(probability),
            "brier": float(np.mean([row["brier"] for row in work_formula[work]])),
            "nll": float(np.mean([row["nll"] for row in work_formula[work]])),
            "adaptive_calibration_error": adaptive_calibration_error(probability, label),
            "high_probability_count": int(high.sum()),
            "high_probability_mean": float(probability[high].mean()) if high.any() else None,
            "high_probability_empirical_frequency": float(label[high].mean()) if high.any() else None,
        }
    keys = ("brier", "nll", "adaptive_calibration_error")
    all_probability = np.asarray([row[field] for row in rows])
    all_label = np.asarray([row["label"] for row in rows])
    reliability = []
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        mask = (all_probability >= lower) & (
            (all_probability <= upper) if upper >= 1.0 else (all_probability < upper)
        )
        if mask.any():
            reliability.append({
                "lower": float(lower),
                "upper": float(min(upper, 1.0)),
                "count": int(mask.sum()),
                "mean_probability": float(all_probability[mask].mean()),
                "empirical_frequency": float(all_label[mask].mean()),
            })
    return {
        "work_metrics": work_metrics,
        "source_macro_metrics": {
            key: float(np.mean([row[key] for row in work_metrics.values()])) for key in keys
        },
        "total_high_probability_count": int(sum(
            row["high_probability_count"] for row in work_metrics.values()
        )),
        "pooled_reliability_bins": reliability,
    }


def run() -> dict:
    nested = json.loads(
        (RESEARCH_ROOT / "experiments" / "v2_nested_cross_work.json").read_text()
    )
    records = list(load_all_records())
    by_id = {record.reference_id: record for record in records}
    all_candidates = []
    temperatures = {}
    logit_calibrators = {}
    calibration_counts = {}
    for outer in nested["outer_details"]:
        outer_work = outer["outer_test_work"]
        parameters = SourceStableParameters(
            **outer["selected_configurations"]["sscl"]
        )
        training = [record for record in records if record.work_id != outer_work]
        test = [record for record in records if record.work_id == outer_work]
        inner_rows = []
        for inner_work in sorted({record.work_id for record in training}):
            inner_training = [record for record in training if record.work_id != inner_work]
            inner_test = [record for record in training if record.work_id == inner_work]
            inner_rows.extend(evaluate_split(
                parameters, inner_training, inner_test, keep_probabilities=True
            ))
        inner_candidates = candidate_rows(inner_rows, by_id)
        temperature = fit_temperature(inner_candidates)
        slope, intercept = fit_logit_calibrator(inner_candidates)
        temperatures[outer_work] = temperature
        logit_calibrators[outer_work] = {"slope": slope, "intercept": intercept}
        calibration_counts[outer_work] = len(inner_candidates)
        outer_rows = evaluate_split(
            parameters, training, test, keep_probabilities=True
        )
        outer_candidates = candidate_rows(outer_rows, by_id)
        for row in outer_candidates:
            row["calibrated_probability"] = float(
                temperature_scale(np.asarray([row["probability"]]), temperature)[0]
            )
            row["logit_calibrated_probability"] = float(
                logit_calibrate(
                    np.asarray([row["probability"]]), slope, intercept
                )[0]
            )
        all_candidates.extend(outer_candidates)
    return {
        "schema_version": "0.2",
        "model": "nested_selected_sscl",
        "design": "one_temperature_fitted_inside_each_outer_work_fold",
        "outer_temperatures": temperatures,
        "outer_logit_calibrators": logit_calibrators,
        "inner_calibration_candidate_counts": calibration_counts,
        "primary_candidate_count": len(all_candidates),
        "uncalibrated": summarize(all_candidates, "probability"),
        "temperature_scaled": summarize(all_candidates, "calibrated_probability"),
        "logit_calibrated": summarize(all_candidates, "logit_calibrated_probability"),
    }


def main() -> None:
    result = run()
    path = RESEARCH_ROOT / "experiments" / "v2_calibration.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "output": str(path),
        "outer_temperatures": result["outer_temperatures"],
        "uncalibrated": result["uncalibrated"]["source_macro_metrics"],
        "temperature_scaled": result["temperature_scaled"]["source_macro_metrics"],
        "logit_calibrated": result["logit_calibrated"]["source_macro_metrics"],
        "high_probability_count": result["logit_calibrated"]["total_high_probability_count"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
