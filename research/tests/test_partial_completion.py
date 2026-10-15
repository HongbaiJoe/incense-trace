import numpy as np

from xiangji.evaluation.partial_completion import composition_metrics, f1_sets
from xiangji.models.data import load_folds


def test_set_metrics_are_exact_for_identical_sets():
    assert f1_sets({"a", "b"}, {"a", "b"}) == (1.0, 1.0, 1.0)


def test_composition_metrics_identical_simplex_is_zero_distance():
    metrics = composition_metrics({"a": 0.7, "b": 0.3}, {"a": 0.7, "b": 0.3})
    assert metrics["weighted_jaccard"] == 1.0
    assert metrics["union_ratio_mae"] == 0.0
    assert np.isclose(metrics["aitchison_distance"], 0.0)


def test_primary_fold_registry_contains_ten_two_work_folds():
    folds = load_folds(kind="primary")
    assert len(folds) == 10
    assert all(len(fold["test_work_ids"]) == 2 for fold in folds)
