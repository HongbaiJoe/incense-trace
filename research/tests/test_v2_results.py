import json

from xiangji.data import RESEARCH_ROOT


def test_nested_result_contains_six_work_level_estimates():
    payload = json.loads(
        (RESEARCH_ROOT / "experiments" / "v2_nested_cross_work.json").read_text()
    )
    assert payload["outer_work_count"] == 6
    assert len(payload["models"]["sscl"]["work_metrics"]) == 6
    assert payload["strongest_model"] == "sscl"


def test_sscl_gain_and_direct_graph_gap_are_reported_at_work_level():
    payload = json.loads(
        (RESEARCH_ROOT / "experiments" / "v2_nested_cross_work.json").read_text()
    )
    sscl = payload["models"]["sscl"]["source_macro_metrics"]["hidden_f1"]
    graph = payload["models"]["directed_graph"]["source_macro_metrics"]["hidden_f1"]
    frequency = payload["models"]["frequency"]["source_macro_metrics"]["hidden_f1"]
    assert sscl - frequency > 0.04
    assert abs(sscl - graph) < 0.001
    assert payload["comparisons_vs_frequency"]["sscl"]["work_count"] == 6


def test_missingness_results_cover_all_declared_conditions():
    payload = json.loads(
        (RESEARCH_ROOT / "experiments" / "v2_missingness_stress.json").read_text()
    )
    assert len(payload["conditions"]) == 12
    assert set(payload["models"]) == {"frequency", "directed_graph", "sscl", "ease"}


def test_nested_logit_calibration_reduces_all_three_errors():
    payload = json.loads(
        (RESEARCH_ROOT / "experiments" / "v2_calibration.json").read_text()
    )
    before = payload["uncalibrated"]["source_macro_metrics"]
    after = payload["logit_calibrated"]["source_macro_metrics"]
    for key in ("brier", "nll", "adaptive_calibration_error"):
        assert after[key] < before[key]
