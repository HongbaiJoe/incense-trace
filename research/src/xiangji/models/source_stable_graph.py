"""Small-data set-completion models for the Xiangji V2 benchmark."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import expit, logit
from sklearn.linear_model import ElasticNet

from xiangji.models.data import FormulaRecord, build_vocabulary, composition_matrix


def _clip_probability(values: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(values, dtype=float), 1e-6, 1.0 - 1e-6)


def _mask_count(total: int, fraction: float) -> int:
    return min(total - 1, max(1, round(total * fraction)))


def _reduce_edges(edges: np.ndarray, reducer: str) -> np.ndarray:
    if reducer == "mean":
        return edges.mean(axis=0)
    if reducer == "max":
        return edges.max(axis=0)
    if reducer == "top2":
        return np.sort(edges, axis=0)[-min(2, len(edges)) :].mean(axis=0)
    raise ValueError("reducer must be 'mean', 'max', or 'top2'")


@dataclass(frozen=True)
class SourceStableParameters:
    method: str = "sscl"
    smoothing: float = 2.0
    source_prior_strength: float = 5.0
    heterogeneity_penalty: float = 0.25
    stable_blend: float = 0.5
    prior_weight: float = 1.0
    reducer: str = "max"
    ease_ridge: float = 100.0
    slim_alpha: float = 0.01
    slim_l1_ratio: float = 0.2
    diffusion: float = 0.2
    ratio_neighbors: int = 10


class SourceStableGraphCompletion:
    """Complete a partial formula with source-aware or comparator scores."""

    def __init__(self, parameters: SourceStableParameters | None = None):
        self.parameters = parameters or SourceStableParameters()

    def fit(
        self,
        records: list[FormulaRecord] | tuple[FormulaRecord, ...],
        sample_weight: np.ndarray | list[float] | tuple[float, ...] | None = None,
    ) -> "SourceStableGraphCompletion":
        if len(records) < 3:
            raise ValueError("At least three training formulas are required")
        self.records = tuple(records)
        if sample_weight is None:
            self.sample_weight = np.ones(len(self.records), dtype=float)
        else:
            self.sample_weight = np.asarray(sample_weight, dtype=float)
            if self.sample_weight.shape != (len(self.records),):
                raise ValueError("sample_weight must have one value per formula")
            if np.any(~np.isfinite(self.sample_weight)) or np.any(self.sample_weight <= 0):
                raise ValueError("sample_weight values must be finite and positive")
        self.effective_sample_size = float(self.sample_weight.sum())
        self.vocabulary = build_vocabulary(self.records)
        self.index = {material: i for i, material in enumerate(self.vocabulary)}
        self.compositions = composition_matrix(self.records, self.vocabulary)
        self.presence = (self.compositions > 0).astype(float)
        self.formula_counts = self.presence.sum(axis=1).astype(int)
        weighted_presence = self.presence * self.sample_weight[:, None]
        count = weighted_presence.sum(axis=0)
        self.prevalence = (count + 0.5) / (self.effective_sample_size + 1.0)
        cooccurrence = self.presence.T @ weighted_presence
        alpha = self.parameters.smoothing
        self.directed_graph = (
            cooccurrence + alpha * self.prevalence[None, :]
        ) / (count[:, None] + alpha)
        np.fill_diagonal(self.directed_graph, 1.0)
        self._fit_source_stable_edges()
        self._fit_comparator()
        return self

    def _fit_source_stable_edges(self) -> None:
        source_lifts = []
        source_weights = []
        for work in sorted({record.work_id for record in self.records}):
            rows = np.asarray([record.work_id == work for record in self.records])
            block = self.presence[rows]
            block_weight = self.sample_weight[rows]
            weighted_block = block * block_weight[:, None]
            count = weighted_block.sum(axis=0)
            cooccurrence = block.T @ weighted_block
            source_size = float(block_weight.sum())
            source_prevalence = (
                count + self.parameters.source_prior_strength * self.prevalence
            ) / (source_size + self.parameters.source_prior_strength)
            conditional = (
                cooccurrence + self.parameters.smoothing * source_prevalence[None, :]
            ) / (count[:, None] + self.parameters.smoothing)
            lift = logit(_clip_probability(conditional)) - logit(
                _clip_probability(source_prevalence)
            )[None, :]
            source_lifts.append(lift)
            source_weights.append(count / (count + self.parameters.smoothing))
        lifts = np.stack(source_lifts)
        weights = np.stack(source_weights)[:, :, None]
        denominator = weights.sum(axis=0)
        mean = np.divide(
            (lifts * weights).sum(axis=0),
            denominator,
            out=np.zeros_like(self.directed_graph),
            where=denominator > 0,
        )
        variance = np.divide(
            (((lifts - mean[None, :, :]) ** 2) * weights).sum(axis=0),
            denominator,
            out=np.zeros_like(self.directed_graph),
            where=denominator > 0,
        )
        self.source_lift_mean = mean
        self.source_lift_sd = np.sqrt(np.maximum(variance, 0.0))
        stable_logit = (
            self.parameters.prior_weight * logit(_clip_probability(self.prevalence))[None, :]
            + self.source_lift_mean
            - self.parameters.heterogeneity_penalty * self.source_lift_sd
        )
        stable = expit(stable_logit)
        blend = self.parameters.stable_blend
        self.source_stable_graph = (1.0 - blend) * self.directed_graph + blend * stable
        np.fill_diagonal(self.source_stable_graph, 1.0)

    def _fit_comparator(self) -> None:
        method = self.parameters.method
        self.comparator_matrix = None
        if method == "ease":
            gram = self.presence.T @ (self.presence * self.sample_weight[:, None])
            precision = np.linalg.inv(
                gram + self.parameters.ease_ridge * np.eye(gram.shape[0])
            )
            weights = precision / (-np.diag(precision)[None, :])
            np.fill_diagonal(weights, 0.0)
            self.comparator_matrix = weights
        elif method == "slim":
            matrix = np.zeros((len(self.vocabulary), len(self.vocabulary)))
            for target in range(len(self.vocabulary)):
                columns = [j for j in range(len(self.vocabulary)) if j != target]
                model = ElasticNet(
                    alpha=self.parameters.slim_alpha,
                    l1_ratio=self.parameters.slim_l1_ratio,
                    positive=True,
                    fit_intercept=False,
                    max_iter=10000,
                    tol=1e-7,
                    selection="cyclic",
                ).fit(
                    self.presence[:, columns],
                    self.presence[:, target],
                    sample_weight=self.sample_weight,
                )
                matrix[columns, target] = model.coef_
            self.comparator_matrix = matrix
        elif method == "ppr":
            transition = self.directed_graph.copy()
            np.fill_diagonal(transition, 0.0)
            row_sum = transition.sum(axis=1, keepdims=True)
            self.comparator_matrix = np.divide(
                transition,
                row_sum,
                out=np.zeros_like(transition),
                where=row_sum > 0,
            )

    def count_distribution(
        self, observed_count: int, observation_fraction: float | None
    ) -> tuple[np.ndarray, np.ndarray]:
        maximum = int(self.formula_counts.max())
        support = np.arange(1, maximum + 1)
        histogram = np.asarray(
            [self.sample_weight[self.formula_counts == k].sum() for k in support],
            dtype=float,
        )
        posterior = (histogram + 0.5) / (
            self.effective_sample_size + 0.5 * maximum
        )
        posterior[support < max(1, observed_count + 1)] = 0.0
        if observation_fraction is not None:
            posterior *= np.asarray(
                [_mask_count(int(k), observation_fraction) == observed_count for k in support],
                dtype=float,
            )
        if posterior.sum() == 0:
            distance = np.abs(
                np.asarray([
                    _mask_count(int(k), observation_fraction or 0.5) for k in support
                ])
                - observed_count
            )
            posterior[distance == distance.min()] = 1.0
            posterior[support < max(1, observed_count + 1)] = 0.0
        if posterior.sum() == 0:
            posterior[-1] = 1.0
        return support, posterior / posterior.sum()

    def _observed_vector(self, observed: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
        binary = np.zeros(len(self.vocabulary), dtype=float)
        weights = np.zeros(len(self.vocabulary), dtype=float)
        for material, value in observed.items():
            if material in self.index:
                binary[self.index[material]] = 1.0
                weights[self.index[material]] = float(value)
        return binary, weights

    def score(self, observed: dict[str, float]) -> np.ndarray:
        binary, _ = self._observed_vector(observed)
        observed_index = np.flatnonzero(binary)
        if not len(observed_index):
            return self.prevalence.copy()
        method = self.parameters.method
        if method == "frequency":
            score = self.prevalence.copy()
        elif method == "directed_graph":
            score = _reduce_edges(
                self.directed_graph[observed_index], self.parameters.reducer
            )
        elif method == "sscl":
            score = _reduce_edges(
                self.source_stable_graph[observed_index], self.parameters.reducer
            )
        elif method in {"ease", "slim"}:
            score = binary @ self.comparator_matrix
            score = score + 0.05 * self.prevalence
        elif method == "ppr":
            state = binary / binary.sum()
            restart = state.copy()
            for _ in range(50):
                state = (
                    (1.0 - self.parameters.diffusion) * restart
                    + self.parameters.diffusion * state @ self.comparator_matrix
                )
            score = state
        else:
            raise ValueError(f"Unknown method: {method}")
        score = np.asarray(score, dtype=float)
        finite = score[np.isfinite(score)]
        if len(finite) and (finite.min() < 0.0 or finite.max() > 1.0):
            score = expit(score)
        return np.clip(score, 1e-6, 1.0 - 1e-6)

    def _ratio_scores(self, observed_binary: np.ndarray) -> np.ndarray:
        overlap = self.presence @ observed_binary
        denominator = np.sqrt(self.presence.sum(axis=1) * observed_binary.sum())
        similarity = np.divide(
            overlap, denominator, out=np.zeros_like(overlap), where=denominator > 0
        )
        order = np.argsort(-similarity, kind="stable")[: self.parameters.ratio_neighbors]
        weights = similarity[order] * self.sample_weight[order]
        if weights.sum() <= 0:
            weights = np.ones(len(order))
        ratio = np.average(self.compositions[order], axis=0, weights=weights)
        if ratio.sum() <= 0:
            ratio = self.prevalence.copy()
        return ratio

    def predict(
        self,
        observed: dict[str, float],
        *,
        observation_fraction: float | None = 0.5,
    ) -> dict:
        binary, _ = self._observed_vector(observed)
        probabilities = self.score(observed)
        ranking = probabilities.copy()
        ranking[binary > 0] = np.inf
        support, count_probability = self.count_distribution(
            int(binary.sum()), observation_fraction
        )
        total = int(support[np.searchsorted(np.cumsum(count_probability), 0.5)])
        total = min(max(total, int(binary.sum()) + 1), len(self.vocabulary))
        selected = np.argsort(-ranking, kind="stable")[:total]
        selected_materials = [self.vocabulary[j] for j in selected]

        ratio_score = self._ratio_scores(binary)
        hidden = [j for j in selected if binary[j] == 0]
        hidden_score = np.maximum(ratio_score[hidden], 0.0)
        if len(hidden) and hidden_score.sum() <= 0:
            hidden_score = self.prevalence[hidden]
        remaining = max(0.0, 1.0 - float(sum(observed.values())))
        composition = dict(observed)
        if len(hidden):
            hidden_score /= hidden_score.sum()
            composition.update(
                {
                    self.vocabulary[j]: remaining * float(value)
                    for j, value in zip(hidden, hidden_score)
                }
            )
        denominator = sum(composition.values()) or 1.0
        composition = {key: value / denominator for key, value in composition.items()}
        return {
            "model": self.parameters.method,
            "selected_count": total,
            "selected_materials": selected_materials,
            "composition": composition,
            "all_inclusion_probabilities": {
                material: float(probabilities[j])
                for j, material in enumerate(self.vocabulary)
            },
            "count_posterior": {
                str(k): float(p) for k, p in zip(support, count_probability)
            },
        }
