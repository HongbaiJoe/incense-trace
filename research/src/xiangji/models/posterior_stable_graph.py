"""Posterior log-odds pooling and non-oracle formula completion.

All source statistics are fitted on supplied training records only. Exact Beta
logit moments are conditional on the empirical-Bayes prevalence estimates.
"""
from __future__ import annotations

import numpy as np
from scipy.special import betaln, digamma, expit, gammaln, logit, polygamma

from xiangji.models.source_stable_graph import SourceStableGraphCompletion


def beta_logit_moments(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if np.any(a <= 0) or np.any(b <= 0):
        raise ValueError("Beta shapes must be positive")
    return digamma(a) - digamma(b), polygamma(1, a) + polygamma(1, b)


def decompose_variation(means, variances, weights):
    """Method-of-moments random-source variance, with unequal fixed weights.

    E[sum q_d (Y_d-Ybar)^2] = (1-sum q_d^2) tau^2
                                + sum q_d(1-q_d) V_d.
    A single exposed source has no estimable between-source variance.
    """
    weights = np.broadcast_to(weights, means.shape)
    total = weights.sum(axis=0)
    q = np.divide(weights, total, out=np.zeros_like(weights), where=total > 0)
    mu = (q * means).sum(axis=0)
    dispersion = (q * (means - mu) ** 2).sum(axis=0)
    noise = (q * (1 - q) * variances).sum(axis=0)
    df = 1 - (q * q).sum(axis=0)
    tau2 = np.divide(dispersion - noise, df, out=np.zeros_like(mu), where=df > 1e-12)
    tau2 = np.maximum(tau2, 0)
    mean_variance = (q * q * (variances + tau2)).sum(axis=0)
    return mu, tau2, mean_variance


def project_composition(reference, known_relative, known_mass):
    """Unique KL projection onto fixed known ratios and a known total mass."""
    if not 0 < known_mass < 1:
        raise ValueError("Known mass must be strictly between zero and one")
    if not known_relative or any(not np.isfinite(x) or x <= 0 for x in known_relative.values()):
        raise ValueError("Known ratios must be positive and finite")
    hidden = {k: max(float(v), 1e-12) for k, v in reference.items() if k not in known_relative}
    if not hidden:
        raise ValueError("At least one hidden material is required")
    total = sum(known_relative.values())
    out = {k: known_mass * v / total for k, v in known_relative.items()}
    hidden_total = sum(hidden.values())
    out.update({k: (1 - known_mass) * v / hidden_total for k, v in hidden.items()})
    return out


class PosteriorStableGraphCompletion(SourceStableGraphCompletion):
    def _fit_source_stable_edges(self):
        means, variances, weights = [], [], []
        alpha = self.parameters.smoothing
        kappa = self.parameters.source_prior_strength
        for work in sorted({r.work_id for r in self.records}):
            rows = np.array([r.work_id == work for r in self.records])
            x, w = self.presence[rows], self.sample_weight[rows]
            counts = (x * w[:, None]).sum(axis=0)
            pairs = x.T @ (x * w[:, None])
            pi = (counts + kappa * self.prevalence) / (w.sum() + kappa)
            a = pairs + alpha * pi[None, :]
            b = counts[:, None] - pairs + alpha * (1 - pi[None, :])
            mean, variance = beta_logit_moments(a, b)
            means.append(mean - logit(pi)[None, :])
            variances.append(variance)
            weights.append((counts / (counts + alpha))[:, None])
        mu, tau2, mean_var = decompose_variation(np.stack(means), np.stack(variances), np.stack(weights))
        self.source_lift_mean = mu
        self.source_between_variance = tau2
        self.source_mean_variance = mean_var
        self.source_lift_sd = np.sqrt(tau2 + mean_var)
        stable = expit(logit(self.prevalence)[None, :] + mu - self.parameters.heterogeneity_penalty * self.source_lift_sd)
        blend = self.parameters.stable_blend
        self.source_stable_graph = (1 - blend) * self.directed_graph + blend * stable
        np.fill_diagonal(self.source_stable_graph, 1.)

    def unknown_count_distribution(self, observed_count, retention_a=1., retention_b=1.):
        if retention_a <= 0 or retention_b <= 0:
            raise ValueError("Retention-prior parameters must be positive")
        k = np.arange(max(2, observed_count + 1), max(int(self.formula_counts.max()), observed_count + 1) + 1)
        prior = np.array([self.sample_weight[self.formula_counts == n].sum() + .5 for n in k])
        m = observed_count
        loglike = gammaln(k + 1) - gammaln(m + 1) - gammaln(k - m + 1)
        loglike += betaln(m + retention_a, k - m + retention_b) - betaln(retention_a, retention_b)
        logp = np.log(prior) + loglike
        p = np.exp(logp - logp.max())
        return k, p / p.sum()

    def predict_partial(self, observed, *, known_mass=None, total_count=None):
        if not observed or any(k not in self.index for k in observed):
            raise ValueError("Supply known materials from the model vocabulary")
        if any(not np.isfinite(v) or v <= 0 for v in observed.values()):
            raise ValueError("Ratios must be finite and positive")
        binary, _ = self._observed_vector(observed)
        support, p = self.unknown_count_distribution(len(observed))
        total = int(support[np.searchsorted(np.cumsum(p), .5)]) if total_count is None else int(total_count)
        if not len(observed) < total <= len(self.vocabulary):
            raise ValueError("Total count must exceed known count and fit the vocabulary")
        scores = self.score(observed)
        ranking = scores.copy()
        ranking[binary > 0] = np.inf
        selected = np.argsort(-ranking, kind="stable")[:total]
        ratio = np.maximum(self._ratio_scores(binary), 1e-9)
        if known_mass is None:
            # Training-only reference mass, never the hidden query composition.
            known_mass = float(ratio[binary > 0].sum() / ratio[selected].sum())
            known_mass = float(np.clip(known_mass, 1e-6, 1 - 1e-6))
            mass_source = "training_neighbours"
        else:
            mass_source = "user_supplied"
        reference = {self.vocabulary[j]: float(ratio[j]) for j in selected}
        composition = project_composition(reference, observed, known_mass)
        return {"model": "posterior_stable", "selected_materials": list(composition),
                "selected_count": total, "composition": composition,
                "known_mass": known_mass, "known_mass_source": mass_source,
                "count_posterior": dict(zip(map(str, support), map(float, p)))}


class OperationalGraphCompletion(PosteriorStableGraphCompletion):
    """Validated V4 graph with the V5 unknown-retention/composition decoder."""
    _fit_source_stable_edges = SourceStableGraphCompletion._fit_source_stable_edges
