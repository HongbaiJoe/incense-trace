import numpy as np

from xiangji.evaluation.primary import compact_result, exact_sign_flip_pvalue, source_bootstrap_interval


def test_exact_sign_flip_is_bounded_and_detects_consistent_direction():
    assert exact_sign_flip_pvalue(np.ones(5)) == 0.0625
    assert 0 <= exact_sign_flip_pvalue(np.array([1, -1, 1, -1, 0.1])) <= 1


def test_source_bootstrap_interval_is_deterministic():
    values = np.array([0.1, 0.2, -0.1, 0.0, 0.3])
    assert source_bootstrap_interval(values, draws=1000) == source_bootstrap_interval(values, draws=1000)


def test_compact_result_separates_record_payload():
    result = {
        "schema_version": "0.1", "selected_model": "m",
        "model_runs": {"m": [{
            "seed": 1, "source_pair_macro_metrics": {"hidden_f1": 0.5},
            "folds": [{"fold_id": "f", "test_work_ids": ["a", "b"], "metrics": {}, "records": [{"id": 1}]}],
        }]},
    }
    compact, raw = compact_result(result)
    assert "records" not in compact["model_runs"]["m"][0]["folds"][0]
    assert raw["model_runs"]["m"][0]["folds"][0]["records"] == [{"id": 1}]
