import numpy as np

from xiangji.evaluation.inference_diagnostics import metropolis_hastings
from xiangji.models.bayesian_logistic import LaplaceLogisticRegression


def test_metropolis_hastings_returns_finite_draws():
    generator = np.random.default_rng(5)
    features = generator.normal(size=(100, 2))
    labels = generator.binomial(1, 0.5, size=100)
    model = LaplaceLogisticRegression(C=2.0).fit(features, labels)
    samples, acceptance = metropolis_hastings(
        model, features, labels, draws=100, burn=50, thin=1, seed=7
    )
    assert samples.shape == (100, 3)
    assert np.all(np.isfinite(samples))
    assert 0 < acceptance < 1
