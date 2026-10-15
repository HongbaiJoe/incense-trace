"""Small-sample Bayesian logistic regression with a Laplace posterior."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


class LaplaceLogisticRegression:
    """Gaussian-prior logistic model with analytic gradient and Hessian.

    ``C`` is the coefficient prior variance. The intercept receives a weak
    fixed prior. Posterior predictive probabilities use the standard
    logistic-normal moment approximation rather than a plug-in MAP estimate.
    """

    def __init__(self, *, C: float = 1.0, max_iter: int = 2000):
        if C <= 0:
            raise ValueError("C must be positive")
        self.C = C
        self.max_iter = max_iter

    def fit(
        self, features: np.ndarray, labels: np.ndarray,
        sample_weight: np.ndarray | None = None,
    ) -> "LaplaceLogisticRegression":
        x = np.asarray(features, dtype=float)
        y = np.asarray(labels, dtype=float)
        if x.ndim != 2 or y.shape != (len(x),):
            raise ValueError("features and labels have incompatible shapes")
        design = np.column_stack([np.ones(len(x)), x])
        weights = np.ones(len(x)) if sample_weight is None else np.asarray(sample_weight, dtype=float).copy()
        positives = max(float(y.sum()), 1.0)
        negatives = max(float((1 - y).sum()), 1.0)
        self.class_balance_logit_offset_ = float(np.log(positives / negatives))
        weights *= np.where(y > 0, len(y) / (2 * positives), len(y) / (2 * negatives))
        precision = np.concatenate([[1e-6], np.full(x.shape[1], 1.0 / self.C)])

        def objective(theta: np.ndarray) -> tuple[float, np.ndarray]:
            linear = design @ theta
            value = np.sum(weights * (np.logaddexp(0.0, linear) - y * linear))
            value += 0.5 * np.dot(precision * theta, theta)
            gradient = design.T @ (weights * (expit(linear) - y)) + precision * theta
            return float(value), gradient

        def hessian(theta: np.ndarray) -> np.ndarray:
            probability = expit(design @ theta)
            curvature = weights * probability * (1 - probability)
            return design.T @ (curvature[:, None] * design) + np.diag(precision)

        result = minimize(
            objective, np.zeros(design.shape[1]), jac=True, method="L-BFGS-B",
            options={"maxiter": self.max_iter, "maxls": 50, "ftol": 1e-11, "gtol": 1e-7},
        )
        if not result.success:
            result = minimize(
                lambda theta: objective(theta)[0], result.x,
                jac=lambda theta: objective(theta)[1], hess=hessian,
                method="trust-exact",
                options={"maxiter": self.max_iter, "gtol": 1e-7},
            )
        gradient_norm = float(np.linalg.norm(objective(result.x)[1], ord=np.inf))
        if not result.success and gradient_norm > 1e-5:
            raise RuntimeError(
                f"Bayesian logistic MAP failed: {result.message}; gradient_inf={gradient_norm:.3g}"
            )
        theta = result.x
        probabilities = expit(design @ theta)
        curvature = weights * probabilities * (1 - probabilities)
        local_hessian = design.T @ (curvature[:, None] * design) + np.diag(precision)
        self.posterior_covariance_ = np.linalg.pinv(local_hessian, hermitian=True)
        self.posterior_mean_ = theta
        self.intercept_ = np.array([theta[0]])
        self.coef_ = theta[1:][None, :]
        self.optimization_result_ = result
        self.gradient_inf_norm_ = gradient_norm
        self.design_dimension_ = design.shape[1]
        return self

    def latent_moments(self, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        design = np.column_stack([np.ones(len(features)), np.asarray(features, dtype=float)])
        mean = design @ self.posterior_mean_ + self.class_balance_logit_offset_
        variance = np.einsum("ij,jk,ik->i", design, self.posterior_covariance_, design)
        return mean, np.clip(variance, 0.0, None)

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        mean, variance = self.latent_moments(features)
        probability = expit(mean / np.sqrt(1.0 + np.pi * variance / 8.0))
        return np.column_stack([1 - probability, probability])

    def sample_parameters(self, count: int, random_seed: int = 17) -> np.ndarray:
        generator = np.random.default_rng(random_seed)
        return generator.multivariate_normal(
            self.posterior_mean_, self.posterior_covariance_, size=count,
            check_valid="raise",
        )

    def log_posterior(
        self, theta: np.ndarray, features: np.ndarray, labels: np.ndarray,
        sample_weight: np.ndarray | None = None,
    ) -> float:
        x = np.asarray(features, dtype=float)
        y = np.asarray(labels, dtype=float)
        design = np.column_stack([np.ones(len(x)), x])
        weights = np.ones(len(x)) if sample_weight is None else np.asarray(sample_weight, dtype=float)
        positives = max(float(y.sum()), 1.0)
        negatives = max(float((1 - y).sum()), 1.0)
        weights = weights * np.where(y > 0, len(y) / (2 * positives), len(y) / (2 * negatives))
        precision = np.concatenate([[1e-6], np.full(x.shape[1], 1.0 / self.C)])
        linear = design @ theta
        return float(
            -np.sum(weights * (np.logaddexp(0.0, linear) - y * linear))
            -0.5 * np.dot(precision * theta, theta)
        )
