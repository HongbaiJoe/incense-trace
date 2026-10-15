import numpy as np

from xiangji.metrics import evaluate, normalize_rows, sparsify


def test_normalization_and_sparsity():
    x = np.array([[1.0, -1.0, 2.0, 0.5]])
    normalized = normalize_rows(x)
    assert np.isclose(normalized.sum(), 1.0)
    sparse = sparsify(normalized, k=2)
    assert np.count_nonzero(sparse) == 2
    assert np.isclose(sparse.sum(), 1.0)


def test_perfect_metrics_are_one_except_error():
    y = np.array([[0.6, 0.4, 0.0], [0.0, 0.2, 0.8]])
    result = evaluate(y, y, k=2)
    assert result["top1"] == 1.0
    assert result["recall_at_6"] == 1.0
    assert result["weighted_jaccard"] == 1.0
    assert result["union_ratio_mae"] == 0.0
    assert result["micro_f1_at_6"] == 1.0
