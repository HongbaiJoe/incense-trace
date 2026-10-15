import numpy as np

from xiangji.evaluation.development_diagnostics import reliability_bins


def test_reliability_bins_account_for_every_probability():
    bins, ece = reliability_bins([0.05, 0.15, 0.85, 1.0], [0, 0, 1, 1])
    assert sum(row["n"] for row in bins) == 4
    assert 0 <= ece <= 1
