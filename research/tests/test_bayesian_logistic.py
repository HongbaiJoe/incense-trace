import numpy as np

from xiangji.models.bayesian_logistic import LaplaceLogisticRegression


def test_laplace_logistic_returns_valid_posterior_and_predictions():
    generator = np.random.default_rng(17)
    x = generator.normal(size=(200, 3))
    probability = 1 / (1 + np.exp(-(x @ np.array([1.0, -0.7, 0.4]))))
    y = generator.binomial(1, probability)
    model = LaplaceLogisticRegression(C=3.0).fit(x, y)
    predicted = model.predict_proba(x[:10])
    assert predicted.shape == (10, 2)
    assert np.all((predicted >= 0) & (predicted <= 1))
    assert np.allclose(predicted.sum(axis=1), 1.0)
    assert model.posterior_covariance_.shape == (4, 4)
    assert np.all(np.linalg.eigvalsh(model.posterior_covariance_) > -1e-10)
    assert np.isfinite(model.class_balance_logit_offset_)
