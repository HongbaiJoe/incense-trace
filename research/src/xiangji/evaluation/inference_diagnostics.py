"""Synthetic recovery and reduced-model Laplace-versus-MH diagnostics."""

from __future__ import annotations

import json
import math

import numpy as np
from scipy.special import expit

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.partial_completion import evaluate_prediction, observed_from_mask
from xiangji.models.bayesian_logistic import LaplaceLogisticRegression
from xiangji.models.cgir import FEATURE_NAMES, XiangjiCGIR
from xiangji.models.data import FormulaRecord


def metropolis_hastings(
    model: LaplaceLogisticRegression,
    features: np.ndarray,
    labels: np.ndarray,
    *,
    draws: int = 20000,
    burn: int = 5000,
    thin: int = 5,
    seed: int = 17,
) -> tuple[np.ndarray, float]:
    generator = np.random.default_rng(seed)
    current = model.posterior_mean_.copy()
    current_logp = model.log_posterior(current, features, labels)
    dimension = len(current)
    covariance = model.posterior_covariance_ + np.eye(dimension) * 1e-10
    proposal_factor = np.linalg.cholesky(covariance)
    proposal_scale = 1.5 / math.sqrt(dimension)
    kept, accepted = [], 0
    total_steps = burn + draws * thin
    for step in range(total_steps):
        proposal = current + proposal_scale * (proposal_factor @ generator.normal(size=dimension))
        proposal_logp = model.log_posterior(proposal, features, labels)
        if math.log(generator.uniform()) < proposal_logp - current_logp:
            current, current_logp = proposal, proposal_logp
            accepted += 1
        if step >= burn and (step - burn) % thin == 0:
            kept.append(current.copy())
    return np.vstack(kept), accepted / total_steps


def reduced_logistic_check(seed: int = 17, draws: int = 20000) -> dict:
    generator = np.random.default_rng(seed)
    true_theta = np.array([0.0, 1.0, -0.8, 0.5])
    features = generator.normal(size=(600, 3))
    design = np.column_stack([np.ones(len(features)), features])
    labels = generator.binomial(1, expit(design @ true_theta))
    model = LaplaceLogisticRegression(C=10.0).fit(features, labels)
    samples, acceptance = metropolis_hastings(
        model, features, labels, draws=draws, seed=seed + 1
    )
    mh_mean = samples.mean(axis=0)
    mh_sd = samples.std(axis=0, ddof=1)
    laplace_sd = np.sqrt(np.diag(model.posterior_covariance_))
    test_features = generator.normal(size=(250, 3))
    test_design = np.column_stack([np.ones(len(test_features)), test_features])
    mh_predictive = expit(
        test_design @ samples[::20].T + model.class_balance_logit_offset_
    ).mean(axis=1)
    laplace_predictive = model.predict_proba(test_features)[:, 1]
    lower = model.posterior_mean_ - 1.96 * laplace_sd
    upper = model.posterior_mean_ + 1.96 * laplace_sd
    return {
        "sample_size": len(features),
        "true_parameters": true_theta.tolist(),
        "laplace_mean": model.posterior_mean_.tolist(),
        "laplace_sd": laplace_sd.tolist(),
        "mh_mean": mh_mean.tolist(),
        "mh_sd": mh_sd.tolist(),
        "mh_acceptance_rate": acceptance,
        "laplace_vs_mh_mean_rmse": float(np.sqrt(np.mean((model.posterior_mean_ - mh_mean) ** 2))),
        "laplace_vs_mh_sd_rmse": float(np.sqrt(np.mean((laplace_sd - mh_sd) ** 2))),
        "predictive_probability_mae": float(np.mean(np.abs(laplace_predictive - mh_predictive))),
        "true_parameter_rmse": float(np.sqrt(np.mean((model.posterior_mean_ - true_theta) ** 2))),
        "true_parameter_95_interval_coverage": float(np.mean((true_theta >= lower) & (true_theta <= upper))),
    }


def synthetic_formula_records(seed: int = 29, count: int = 120) -> list[FormulaRecord]:
    generator = np.random.default_rng(seed)
    archetypes = [
        ("梅花清韵", ("agarwood", "clove_bud", "borneol_family", "spikenard", "musk")),
        ("桂木暖韵", ("sandalwood_white", "cassia", "patchouli", "frankincense", "musk")),
    ]
    records = []
    for index in range(count):
        title, materials = archetypes[index % 2]
        keep = list(materials)
        if generator.uniform() < 0.35:
            keep.pop(int(generator.integers(0, len(keep) - 1)))
        weights = generator.dirichlet(np.linspace(3.0, 1.2, len(keep)))
        records.append(FormulaRecord(
            reference_id=f"synthetic-{index:03d}",
            family_id=f"synthetic-family-{index:03d}",
            work_id=f"synthetic-work-{index % 4}",
            title=title,
            composition={material: float(weight) for material, weight in zip(keep, weights)},
        ))
    return records


def composition_recovery_check(seed: int = 29) -> dict:
    records = synthetic_formula_records(seed)
    training, test = records[:96], records[96:]
    models = {
        "frequency": XiangjiCGIR(
            random_seed=seed, C=0.3, group_dro_iterations=0,
            enabled_channels={"global_prevalence_logit", "observed_material", "observed_log_weight"},
        ).fit(training),
        "structured": XiangjiCGIR(
            random_seed=seed, C=0.3, group_dro_iterations=0, graph_reducer="mean",
            enabled_channels=set(FEATURE_NAMES) - {
                "chemical_affinity", "chemical_evidence_available", "chemical_odor_similarity"
            },
        ).fit(training),
    }
    output = {}
    for model_name, model in models.items():
        rows, interval_hits, interval_total = [], 0, 0
        for record in test:
            observed = observed_from_mask(record, model.vocabulary_, seed, 0.5)
            prediction = model.predict(
                title=record.title, work_id="synthetic-unseen-work", observed=observed,
                observation_fraction=0.5, posterior_samples=500, random_seed=seed,
            )
            rows.append(evaluate_prediction(record, observed, prediction))
            for material in prediction["materials"]:
                if material["material_id"] in record.composition:
                    interval_total += 1
                    low, high = material["ratio_interval_80"]
                    interval_hits += int(low <= record.composition[material["material_id"]] <= high)
        output[model_name] = {
            key: float(np.mean([row[key] for row in rows])) for key in rows[0]
        }
        output[model_name]["conditional_ratio_interval_80_coverage"] = (
            interval_hits / interval_total if interval_total else 0.0
        )
    return {
        "training_formula_count": len(training),
        "test_formula_count": len(test),
        "held_out_work": "synthetic-unseen-work",
        "metrics": output,
    }


def run_diagnostics() -> dict:
    return {
        "schema_version": "0.1",
        "reduced_logistic_laplace_vs_mh": reduced_logistic_check(),
        "synthetic_formula_recovery": composition_recovery_check(),
    }


def main() -> None:
    result = run_diagnostics()
    target = RESEARCH_ROOT / "experiments" / "cycle3_inference_diagnostics.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
