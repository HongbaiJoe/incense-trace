"""Post-freeze competitive baselines and source-shift stress tests."""

from __future__ import annotations

import gzip
import json
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.evaluation.partial_completion import composition_metrics, f1_sets, observed_from_mask, run_development
from xiangji.evaluation.primary import paired_source_comparison
from xiangji.models.data import FormulaRecord, build_vocabulary, composition_matrix, load_development_corpus, load_folds


SEEDS = (17, 29, 43, 71, 101)
OBSERVED_FRACTION = 0.5


def _mask_count(total: int, fraction: float = OBSERVED_FRACTION) -> int:
    return min(total - 1, max(1, round(total * fraction)))


def _count_summary(records: list[FormulaRecord], observed_count: int) -> tuple[int, int, int]:
    counts = np.asarray([len(record.composition) for record in records], dtype=int)
    eligible = counts[np.asarray([_mask_count(int(value)) == observed_count for value in counts])]
    if not len(eligible):
        distance = np.abs(np.asarray([_mask_count(int(value)) for value in counts]) - observed_count)
        eligible = counts[distance == distance.min()]
    low, median, high = np.quantile(eligible, [0.1, 0.5, 0.9], method="nearest").astype(int)
    minimum = observed_count + 1
    return max(minimum, int(low)), max(minimum, int(median)), max(minimum, int(high))


def _interval_from_posterior(posterior: dict[int | str, float]) -> tuple[int, int]:
    items = sorted((int(value), float(mass)) for value, mass in posterior.items())
    support = np.asarray([value for value, _ in items], dtype=int)
    cumulative = np.cumsum([mass for _, mass in items])
    low, high = support[np.searchsorted(cumulative, [0.1, 0.9])]
    return int(low), int(high)


@dataclass
class CompletionBaseline:
    method: str
    parameter: int
    similarity: str = "cosine"

    def fit(self, records: list[FormulaRecord]) -> "CompletionBaseline":
        self.records = list(records)
        self.vocabulary = build_vocabulary(records)
        self.index = {material: i for i, material in enumerate(self.vocabulary)}
        self.compositions = composition_matrix(records, self.vocabulary)
        self.presence = (self.compositions > 0).astype(float)
        self.prevalence = (self.presence.sum(axis=0) + 0.5) / (len(records) + 1)
        if self.method == "pure_svd":
            _, _, vt = np.linalg.svd(self.presence, full_matrices=False)
            rank = min(self.parameter, len(vt))
            basis = vt[:rank]
            self.projector = basis.T @ basis
        return self

    def _scores(self, observed_vector: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self.method == "formula_knn":
            overlap = self.presence @ observed_vector
            if self.similarity == "jaccard":
                denominator = self.presence.sum(axis=1) + observed_vector.sum() - overlap
            else:
                denominator = np.sqrt(self.presence.sum(axis=1) * observed_vector.sum())
            similarity = np.divide(overlap, denominator, out=np.zeros_like(overlap), where=denominator > 0)
            order = np.argsort(-similarity, kind="stable")[: self.parameter]
            weights = similarity[order]
            if weights.sum() <= 0:
                weights = np.ones(len(order))
            inclusion = np.average(self.presence[order], axis=0, weights=weights)
            ratios = np.average(self.compositions[order], axis=0, weights=weights)
            return inclusion, ratios
        if self.method == "pure_svd":
            reconstructed = observed_vector @ self.projector
            shifted = reconstructed - reconstructed.min()
            inclusion = shifted + 0.05 * self.prevalence
            return inclusion, inclusion.copy()
        raise ValueError(f"Unknown method: {self.method}")

    def predict(self, observed: dict[str, float]) -> dict:
        vector = np.zeros(len(self.vocabulary), dtype=float)
        for material in observed:
            if material in self.index:
                vector[self.index[material]] = 1.0
        score, ratio_score = self._scores(vector)
        for material in observed:
            if material in self.index:
                score[self.index[material]] = np.inf
        _, selected_count, _ = _count_summary(self.records, len(observed))
        selected_count = min(selected_count, len(self.vocabulary))
        selected = np.argsort(-score, kind="stable")[:selected_count]
        selected_materials = [self.vocabulary[i] for i in selected]

        observed_mass = float(sum(observed.values()))
        remaining = max(0.0, 1.0 - observed_mass)
        hidden = [i for i in selected if self.vocabulary[i] not in observed]
        hidden_weights = np.maximum(ratio_score[hidden], 0.0)
        if len(hidden) and hidden_weights.sum() == 0:
            hidden_weights = self.prevalence[hidden]
        composition = dict(observed)
        if len(hidden):
            hidden_weights = hidden_weights / hidden_weights.sum()
            composition.update({self.vocabulary[i]: remaining * float(weight) for i, weight in zip(hidden, hidden_weights)})
        total = sum(composition.values())
        if total <= 0:
            total = 1.0
        return {
            "selected_count": selected_count,
            "composition": {key: value / total for key, value in composition.items()},
            "selected_materials": selected_materials,
        }


def _evaluate(record: FormulaRecord, observed: dict[str, float], prediction: dict) -> dict[str, float]:
    truth = set(record.composition)
    observed_set = set(observed)
    predicted = set(prediction["selected_materials"])
    precision, recall, f1 = f1_sets(truth - observed_set, predicted - observed_set)
    return {
        "hidden_precision": precision,
        "hidden_recall": recall,
        "hidden_f1": f1,
        "weighted_jaccard": composition_metrics(record.composition, prediction["composition"])["weighted_jaccard"],
        "count_absolute_error": float(abs(len(truth) - len(predicted))),
    }


def _run_configuration(configuration: dict, fold_kind: str) -> dict:
    corpus = load_development_corpus()
    by_id = corpus.by_id()
    runs = []
    for seed in SEEDS:
        folds_out = []
        for fold in load_folds(kind=fold_kind):
            train = [by_id[value] for value in fold["train_reference_ids"]]
            test = [by_id[value] for value in fold["test_reference_ids"]]
            model = CompletionBaseline(**configuration).fit(train)
            records = []
            for record in test:
                if sum(material in model.index for material in record.composition) < 2:
                    continue
                observed = observed_from_mask(record, model.vocabulary, seed, OBSERVED_FRACTION)
                metrics = _evaluate(record, observed, model.predict(observed))
                records.append({"reference_id": record.reference_id, "work_id": record.work_id, "metrics": metrics})
            folds_out.append({"fold_id": fold["fold_id"], "records": records})
        runs.append({"seed": seed, "folds": folds_out})
    return {"configuration": configuration, "runs": runs, "source_metrics": _source_metrics(runs)}


def _source_metrics(runs: list[dict], exclude_ids: set[str] | None = None) -> dict:
    exclude_ids = exclude_ids or set()
    by_formula: dict[str, list[dict]] = defaultdict(list)
    work_by_formula = {}
    for run in runs:
        for fold in run["folds"]:
            for row in fold["records"]:
                if row["reference_id"] not in exclude_ids:
                    by_formula[row["reference_id"]].append(row["metrics"])
                    work_by_formula[row["reference_id"]] = row["work_id"]
    by_work: dict[str, list[dict]] = defaultdict(list)
    for reference_id, rows in by_formula.items():
        keys = rows[0]
        by_work[work_by_formula[reference_id]].append({
            key: float(np.mean([row[key] for row in rows])) for key in keys
        })
    return {
        work: {
            "record_count": len(rows),
            **{key: float(np.mean([row[key] for row in rows])) for key in rows[0]},
        }
        for work, rows in sorted(by_work.items())
    }


def _macro(source_metrics: dict) -> dict:
    keys = sorted(set(next(iter(source_metrics.values()))) - {"record_count"})
    return {key: float(np.mean([row[key] for row in source_metrics.values()])) for key in keys}


def select_and_evaluate_baselines() -> dict:
    grids = {
        "formula_knn": [
            {"method": "formula_knn", "parameter": k, "similarity": similarity}
            for similarity in ("cosine", "jaccard") for k in (1, 3, 5, 10)
        ],
        "pure_svd": [
            {"method": "pure_svd", "parameter": rank, "similarity": "cosine"}
            for rank in (2, 4, 8, 16, 32)
        ],
    }
    selected = {}
    development_summary = {}
    primary = {}
    for family, configurations in grids.items():
        rows = []
        for configuration in configurations:
            result = _run_configuration(configuration, "development")
            rows.append({"configuration": configuration, "metrics": _macro(result["source_metrics"])})
        rows.sort(key=lambda row: (row["metrics"]["hidden_f1"], row["metrics"]["weighted_jaccard"]), reverse=True)
        development_summary[family] = rows
        selected[family] = rows[0]["configuration"]
        primary_result = _run_configuration(rows[0]["configuration"], "primary")
        primary[family] = {
            "configuration": rows[0]["configuration"],
            "source_metrics": primary_result["source_metrics"],
            "source_macro_metrics": _macro(primary_result["source_metrics"]),
        }
    frozen = json.loads((RESEARCH_ROOT / "experiments/cycle4_primary_evaluation.json").read_text())
    comparisons = {}
    for family in primary:
        comparisons[f"graph_only_minus_{family}"] = paired_source_comparison(
            frozen["source_level_metrics"]["graph_only"], primary[family]["source_metrics"]
        )
    return {
        "selection_data": "five development leave-one-work-out folds and five deterministic masks",
        "primary_data": "ten frozen two-work-held-out folds and five deterministic masks",
        "post_freeze_analysis": True,
        "development_grid": development_summary,
        "selected_configurations": selected,
        "primary_results": primary,
        "comparisons": comparisons,
    }


def near_duplicate_sensitivity() -> dict:
    corpus = load_development_corpus()
    records = list(corpus.records)
    high_similarity = {}
    for query in records:
        candidates = [record for record in records if record.work_id != query.work_id]
        scored = []
        for candidate in candidates:
            left, right = set(query.composition), set(candidate.composition)
            scored.append((len(left & right) / len(left | right), candidate.reference_id))
        maximum, match = max(scored)
        if maximum >= 0.8:
            high_similarity[query.reference_id] = {"maximum_material_jaccard": maximum, "matched_reference_id": match}

    compact = json.loads((RESEARCH_ROOT / "experiments/cycle4_primary_evaluation.json").read_text())
    raw = json.loads(gzip.decompress((RESEARCH_ROOT / "experiments/cycle4_primary_records.json.gz").read_bytes()))
    runs_by_model = {}
    for model_name, compact_runs in compact["model_runs"].items():
        runs = []
        for compact_run, raw_run in zip(compact_runs, raw["model_runs"][model_name]):
            folds = []
            for raw_fold in raw_run["folds"]:
                folds.append({
                    "fold_id": raw_fold["fold_id"],
                    "records": [row for row in raw_fold["records"] if row.get("status") == "evaluated"],
                })
            runs.append({"seed": compact_run["seed"], "folds": folds})
        runs_by_model[model_name] = runs
    excluded = set(high_similarity)
    source_metrics = {name: _source_metrics(runs, excluded) for name, runs in runs_by_model.items()}
    return {
        "threshold": 0.8,
        "rule": "exclude a formula if its aromatic material set has Jaccard >= 0.8 with any formula from another work group",
        "excluded_formula_count": len(excluded),
        "retained_formula_count": len(records) - len(excluded),
        "flagged_pairs": high_similarity,
        "source_level_metrics": source_metrics,
        "source_macro_metrics": {name: _macro(values) for name, values in source_metrics.items()},
        "full_minus_frequency": paired_source_comparison(source_metrics["full_no_chemistry"], source_metrics["frequency"]),
        "graph_minus_frequency": paired_source_comparison(source_metrics["graph_only"], source_metrics["frequency"]),
    }


def mass_constrained_composition() -> dict:
    """Preserve supplied ratios and allocate only the unobserved mass."""
    corpus = load_development_corpus()
    by_id = corpus.by_id()
    raw = json.loads(gzip.decompress((RESEARCH_ROOT / "experiments/cycle4_primary_records.json.gz").read_bytes()))
    runs = raw["model_runs"]["full_no_chemistry"]
    by_formula = defaultdict(list)
    for run in runs:
        for fold in run["folds"]:
            for row in fold["records"]:
                if row.get("status") != "evaluated":
                    continue
                observed = row["observed_materials"]
                predicted = {
                    item["material_id"]: item["posterior_mean_ratio"]
                    for item in row["uncertainty"]["materials"]
                }
                hidden = {material: value for material, value in predicted.items() if material not in observed}
                remaining = max(0.0, 1.0 - sum(observed.values()))
                denominator = sum(hidden.values())
                composition = dict(observed)
                if denominator > 0:
                    composition.update({material: remaining * value / denominator for material, value in hidden.items()})
                by_formula[row["reference_id"]].append(
                    composition_metrics(by_id[row["reference_id"]].composition, composition)
                )
    by_work = defaultdict(list)
    for reference_id, rows in by_formula.items():
        by_work[by_id[reference_id].work_id].append(float(np.mean([row["weighted_jaccard"] for row in rows])))
    source = {work: float(np.mean(values)) for work, values in sorted(by_work.items())}
    return {
        "rule": "hold observed ratios fixed and close predicted hidden ratios to the remaining mass",
        "selected_sets_changed": False,
        "source_weighted_jaccard": source,
        "source_macro_weighted_jaccard": float(np.mean(list(source.values()))),
    }


def recalibrated_count_intervals() -> dict:
    corpus = load_development_corpus()
    by_id = corpus.by_id()
    compact = json.loads((RESEARCH_ROOT / "experiments/cycle4_primary_evaluation.json").read_text())
    raw = json.loads(gzip.decompress((RESEARCH_ROOT / "experiments/cycle4_primary_records.json.gz").read_bytes()))
    selected = compact["selected_model"]
    stored_runs = raw["model_runs"][selected]
    selection = json.loads((RESEARCH_ROOT / "experiments/cycle3_model_selection.json").read_text())
    configuration = selection["best_by_model"][selected]
    development_nonconformity = []
    development_base_hits = []
    for seed in SEEDS:
        result = run_development(
            seed=seed,
            observed_fraction=OBSERVED_FRACTION,
            C=configuration["C"],
            group_dro_iterations=configuration["group_dro_iterations"],
            graph_reducer=configuration["graph_reducer"],
            posterior_samples=10,
            model_names=(selected,),
            fold_kind="development",
        )["models"][selected]
        for fold in result["folds"]:
            for row in fold["records"]:
                if row.get("status") != "evaluated":
                    continue
                truth = len(by_id[row["reference_id"]].composition)
                low, high = _interval_from_posterior(row["prediction"]["count_posterior"])
                development_base_hits.append(int(low <= truth <= high))
                development_nonconformity.append(max(low - truth, truth - high, 0))
    quantile_level = min(1.0, np.ceil((len(development_nonconformity) + 1) * 0.8) / len(development_nonconformity))
    calibration_radius = int(np.quantile(development_nonconformity, quantile_level, method="higher"))
    cover_base, cover_expanded, widths_base, widths_expanded = [], [], [], []
    fold_details = []
    for run in stored_runs:
        for fold in run["folds"]:
            fold_rows = []
            for row in fold["records"]:
                if row.get("status") != "evaluated":
                    continue
                truth = len(by_id[row["reference_id"]].composition)
                observed_count = len(row["observed_materials"])
                low, high = _interval_from_posterior(row["uncertainty"]["count_posterior"])
                expanded_low = max(observed_count + 1, low - calibration_radius)
                expanded_high = high + calibration_radius
                cover_base.append(int(low <= truth <= high))
                cover_expanded.append(int(expanded_low <= truth <= expanded_high))
                widths_base.append(high - low)
                widths_expanded.append(expanded_high - expanded_low)
                fold_rows.append({
                    "reference_id": row["reference_id"],
                    "truth": truth,
                    "base_interval": [low, high],
                    "expanded_interval": [expanded_low, expanded_high],
                })
            fold_details.append({"fold_id": fold["fold_id"], "seed": run["seed"], "records": fold_rows})
    return {
        "method": "development-work-held-out interval-nonconformity expansion",
        "nominal_level": 0.8,
        "development_calibration_instances": len(development_nonconformity),
        "development_base_coverage": float(np.mean(development_base_hits)),
        "finite_sample_quantile_level": float(quantile_level),
        "calibration_radius": calibration_radius,
        "base_coverage": float(np.mean(cover_base)),
        "expanded_coverage": float(np.mean(cover_expanded)),
        "base_mean_width": float(np.mean(widths_base)),
        "expanded_mean_width": float(np.mean(widths_expanded)),
        "evaluation_instances": len(cover_base),
        "folds": fold_details,
    }


def run() -> dict:
    return {
        "schema_version": "0.1",
        "model_parameters_changed": False,
        "competitive_baselines": select_and_evaluate_baselines(),
        "near_duplicate_sensitivity": near_duplicate_sensitivity(),
        "count_interval_recalibration": recalibrated_count_intervals(),
        "mass_constrained_composition": mass_constrained_composition(),
    }


def main() -> None:
    result = run()
    target = RESEARCH_ROOT / "experiments" / "cycle6_stress_tests.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "output": str(target),
        "selected_baselines": result["competitive_baselines"]["selected_configurations"],
        "primary_baselines": {
            name: row["source_macro_metrics"]
            for name, row in result["competitive_baselines"]["primary_results"].items()
        },
        "near_duplicate": result["near_duplicate_sensitivity"]["source_macro_metrics"],
        "count_recalibration": {
            key: result["count_interval_recalibration"][key]
            for key in ("base_coverage", "expanded_coverage", "base_mean_width", "expanded_mean_width")
        },
        "mass_constrained_weighted_jaccard": result["mass_constrained_composition"]["source_macro_weighted_jaccard"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
