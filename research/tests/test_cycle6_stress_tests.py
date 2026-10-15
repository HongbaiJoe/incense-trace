import json

import numpy as np

from xiangji.evaluation.cycle6_stress_tests import CompletionBaseline, _count_summary
from xiangji.data import RESEARCH_ROOT
from xiangji.models.data import FormulaRecord


def _records() -> list[FormulaRecord]:
    return [
        FormulaRecord("a", "fa", "w1", "a", {"x": 0.5, "y": 0.3, "z": 0.2}),
        FormulaRecord("b", "fb", "w1", "b", {"x": 0.6, "y": 0.4}),
        FormulaRecord("c", "fc", "w2", "c", {"x": 0.4, "z": 0.4, "q": 0.2}),
        FormulaRecord("d", "fd", "w2", "d", {"y": 0.5, "q": 0.5}),
    ]


def test_competitive_baselines_force_observed_and_close_composition() -> None:
    for model in (
        CompletionBaseline("formula_knn", 3, "jaccard"),
        CompletionBaseline("pure_svd", 2),
    ):
        fitted = model.fit(_records())
        prediction = fitted.predict({"x": 0.4})
        assert "x" in prediction["selected_materials"]
        assert len(prediction["selected_materials"]) == prediction["selected_count"]
        assert np.isclose(sum(prediction["composition"].values()), 1.0)
        assert all(value >= 0 for value in prediction["composition"].values())


def test_count_summary_leaves_a_hidden_component() -> None:
    low, median, high = _count_summary(_records(), observed_count=1)
    assert 2 <= low <= median <= high


def test_frozen_cycle6_stress_results_support_reported_claims() -> None:
    path = RESEARCH_ROOT / "experiments" / "cycle6_stress_tests.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    baselines = payload["competitive_baselines"]["primary_results"]
    graph_f1 = 0.3787
    assert graph_f1 > baselines["formula_knn"]["source_macro_metrics"]["hidden_f1"]
    assert graph_f1 > baselines["pure_svd"]["source_macro_metrics"]["hidden_f1"]
    sensitivity = payload["near_duplicate_sensitivity"]
    assert sensitivity["excluded_formula_count"] == 9
    assert sensitivity["source_macro_metrics"]["graph_only"]["hidden_f1"] > sensitivity["source_macro_metrics"]["frequency"]["hidden_f1"]
    count = payload["count_interval_recalibration"]
    assert count["base_coverage"] < 0.8 <= count["expanded_coverage"]
    assert payload["mass_constrained_composition"]["source_macro_weighted_jaccard"] > 0.42
