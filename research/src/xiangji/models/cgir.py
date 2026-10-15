"""Low-parameter chemistry-guided structured probabilistic decoder v1."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.special import expit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from xiangji.models.data import FormulaRecord, build_vocabulary, composition_matrix, deterministic_observation_mask
from xiangji.models.bayesian_logistic import LaplaceLogisticRegression
from xiangji.representations.kernels import affinity_from_observed, build_chemical_kernel, hypergraph_kernel
from xiangji.representations.odor import OdorViews, build_odor_views

FEATURE_NAMES = (
    "global_prevalence_logit",
    "source_prevalence_logit",
    "title_material_similarity",
    "hypergraph_affinity",
    "chemical_affinity",
    "chemical_evidence_available",
    "legacy_odor_similarity",
    "chemical_odor_similarity",
    "observed_material",
    "observed_log_weight",
)


def clipped_logit(probability: np.ndarray | float, epsilon: float = 1e-5) -> np.ndarray:
    probability = np.clip(probability, epsilon, 1 - epsilon)
    return np.log(probability / (1 - probability))


@dataclass
class TitleMaterialEncoder:
    vectorizer: TfidfVectorizer
    centroids: np.ndarray
    title_matrix: object
    presence: np.ndarray
    centroid_sums: np.ndarray
    centroid_counts: np.ndarray

    @classmethod
    def fit(cls, titles: list[str], presence: np.ndarray) -> "TitleMaterialEncoder":
        vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(1, 2), sublinear_tf=True, norm="l2")
        title_matrix = vectorizer.fit_transform(titles)
        centroid_sums = np.zeros((presence.shape[1], title_matrix.shape[1]), dtype=float)
        centroid_counts = presence.sum(axis=0).astype(float)
        for material_index in range(presence.shape[1]):
            rows = np.flatnonzero(presence[:, material_index])
            if len(rows):
                centroid_sums[material_index] = np.asarray(title_matrix[rows].sum(axis=0)).ravel()
        centroids = np.divide(
            centroid_sums,
            centroid_counts[:, None],
            out=np.zeros_like(centroid_sums),
            where=centroid_counts[:, None] > 0,
        )
        norms = np.linalg.norm(centroids, axis=1)
        nonzero = norms > 0
        centroids[nonzero] /= norms[nonzero, None]
        return cls(
            vectorizer=vectorizer,
            centroids=centroids,
            title_matrix=title_matrix,
            presence=presence,
            centroid_sums=centroid_sums,
            centroid_counts=centroid_counts,
        )

    def transform(self, title: str) -> np.ndarray:
        vector = self.vectorizer.transform([title])
        return np.asarray(vector @ self.centroids.T).ravel()

    def transform_training_index(self, record_index: int) -> np.ndarray:
        vector = np.asarray(self.title_matrix[record_index].toarray()).ravel()
        sums = self.centroid_sums - self.presence[record_index, :, None] * vector[None, :]
        counts = self.centroid_counts - self.presence[record_index].astype(float)
        centroids = np.divide(
            sums,
            counts[:, None],
            out=np.zeros_like(sums),
            where=counts[:, None] > 0,
        )
        norms = np.linalg.norm(centroids, axis=1)
        nonzero = norms > 0
        centroids[nonzero] /= norms[nonzero, None]
        return centroids @ vector


class XiangjiCGIR:
    def __init__(
        self,
        *,
        random_seed: int = 17,
        C: float = 0.3,
        ratio_alpha: float = 1.0,
        mask_fractions: tuple[float, ...] = (0.25, 0.5, 0.75),
        source_prior_strength: float = 5.0,
        count_prior_strength: float = 3.0,
        group_dro_iterations: int = 8,
        group_dro_eta: float = 0.2,
        chemistry_proxy_map: dict[str, str] | None = None,
        graph_reducer: str = "weighted_mean",
        enabled_channels: set[str] | None = None,
    ):
        self.random_seed = random_seed
        self.C = C
        self.ratio_alpha = ratio_alpha
        self.mask_fractions = mask_fractions
        self.source_prior_strength = source_prior_strength
        self.count_prior_strength = count_prior_strength
        self.group_dro_iterations = group_dro_iterations
        self.group_dro_eta = group_dro_eta
        self.chemistry_proxy_map = chemistry_proxy_map or {}
        self.graph_reducer = graph_reducer
        self.enabled_channels = enabled_channels or set(FEATURE_NAMES)

    def fit(self, records: list[FormulaRecord] | tuple[FormulaRecord, ...]) -> "XiangjiCGIR":
        self.records_ = tuple(records)
        if len(self.records_) < 3:
            raise ValueError("At least three training formulas are required")
        self.vocabulary_ = build_vocabulary(self.records_)
        self.material_index_ = {material: index for index, material in enumerate(self.vocabulary_)}
        self.compositions_ = composition_matrix(self.records_, self.vocabulary_)
        self.presence_ = self.compositions_ > 0
        self.title_encoder_ = TitleMaterialEncoder.fit(
            [record.title for record in self.records_], self.presence_
        )
        self.hypergraph_kernel_ = hypergraph_kernel(self.compositions_)
        self.chemical_kernel_, self.chemical_available_, self.chemical_proxy_used_ = build_chemical_kernel(
            self.vocabulary_, proxy_map=self.chemistry_proxy_map
        )
        self.odor_views_: OdorViews = build_odor_views(
            self.vocabulary_, proxy_map=self.chemistry_proxy_map
        )
        self._fit_priors()
        features, labels, groups, ratio_rows, ratio_targets = self._training_rows()
        self.feature_scaler_ = StandardScaler().fit(features)
        scaled = self.feature_scaler_.transform(features)
        self.inclusion_model_ = LaplaceLogisticRegression(
            C=self.C,
            max_iter=2000,
        )
        self.group_weights_ = self._fit_group_dro(scaled, labels, groups)
        training_probabilities = np.clip(
            self.inclusion_model_.predict_proba(scaled)[:, 1], 1e-8, 1 - 1e-8
        )
        self.training_source_log_loss_ = {}
        for group in sorted(set(groups.tolist())):
            group_mask = groups == group
            self.training_source_log_loss_[group] = float(np.mean(
                -(labels[group_mask] * np.log(training_probabilities[group_mask])
                  + (1 - labels[group_mask]) * np.log(1 - training_probabilities[group_mask]))
            ))

        self.ratio_scaler_ = StandardScaler().fit(ratio_rows)
        ratio_scaled = self.ratio_scaler_.transform(ratio_rows)
        self.ratio_model_ = Ridge(alpha=self.ratio_alpha).fit(ratio_scaled, ratio_targets)
        residuals = ratio_targets - self.ratio_model_.predict(ratio_scaled)
        self.ratio_residual_sd_ = float(np.sqrt(np.mean(residuals ** 2)))
        self.dirichlet_concentration_ = float(np.clip(1.0 / max(self.ratio_residual_sd_ ** 2, 0.01), 2.0, 100.0))
        return self

    def _fit_priors(self) -> None:
        count = self.presence_.sum(axis=0)
        self.global_presence_count_ = count.copy()
        total = len(self.records_)
        self.global_prevalence_ = (count + 0.5) / (total + 1.0)
        self.source_prevalence_ = {}
        self.source_count_distribution_ = {}
        self.source_presence_count_ = {}
        self.source_record_count_ = {}
        works = sorted({record.work_id for record in self.records_})
        formula_counts = self.presence_.sum(axis=1).astype(int)
        self.maximum_count_ = int(formula_counts.max())
        support = np.arange(1, self.maximum_count_ + 1)
        global_hist = np.array([(formula_counts == value).sum() for value in support], dtype=float)
        self.global_count_distribution_ = (global_hist + 0.5) / (global_hist.sum() + 0.5 * len(support))
        for work in works:
            rows = np.array([record.work_id == work for record in self.records_])
            source_count = self.presence_[rows].sum(axis=0)
            self.source_presence_count_[work] = source_count.copy()
            self.source_record_count_[work] = int(rows.sum())
            self.source_prevalence_[work] = (
                source_count + self.source_prior_strength * self.global_prevalence_
            ) / (rows.sum() + self.source_prior_strength)
            source_formula_counts = formula_counts[rows]
            hist = np.array([(source_formula_counts == value).sum() for value in support], dtype=float)
            self.source_count_distribution_[work] = (
                hist + self.count_prior_strength * self.global_count_distribution_
            ) / (len(source_formula_counts) + self.count_prior_strength)

    def _feature_matrix(
        self,
        *,
        title: str,
        work_id: str | None,
        observed_weights: np.ndarray,
        odor_target: np.ndarray | None = None,
        global_prevalence: np.ndarray | None = None,
        source_prevalence: np.ndarray | None = None,
        title_score: np.ndarray | None = None,
        graph_kernel: np.ndarray | None = None,
    ) -> np.ndarray:
        global_prevalence = self.global_prevalence_ if global_prevalence is None else global_prevalence
        source = (
            self.source_prevalence_.get(work_id, global_prevalence)
            if source_prevalence is None else source_prevalence
        )
        title_score = self.title_encoder_.transform(title) if title_score is None else title_score
        graph = affinity_from_observed(
            self.hypergraph_kernel_ if graph_kernel is None else graph_kernel,
            observed_weights,
            reducer=self.graph_reducer,
        )
        chemistry = affinity_from_observed(self.chemical_kernel_, observed_weights)
        chemical_context_available = bool(
            np.any((observed_weights > 0) & self.chemical_available_)
        )
        if odor_target is None:
            legacy_odor = np.zeros(len(self.vocabulary_))
            chemical_odor = np.zeros(len(self.vocabulary_))
        else:
            legacy_odor, chemical_odor = self.odor_views_.similarities(odor_target)
        observed = observed_weights > 0
        observed_log = np.where(observed, np.log(np.clip(observed_weights, 1e-8, None)), 0.0)
        matrix = np.column_stack([
            clipped_logit(global_prevalence),
            clipped_logit(source) - clipped_logit(global_prevalence),
            title_score,
            graph,
            chemistry,
            self.chemical_available_.astype(float) * float(chemical_context_available),
            legacy_odor,
            chemical_odor,
            observed.astype(float),
            observed_log,
        ])
        channel_mask = np.array([name in self.enabled_channels for name in FEATURE_NAMES], dtype=float)
        return matrix * channel_mask

    def _training_rows(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        feature_blocks, label_blocks, group_blocks = [], [], []
        ratio_rows, ratio_targets = [], []
        for record_index, record in enumerate(self.records_):
            true_composition = self.compositions_[record_index]
            labels = (true_composition > 0).astype(int)
            global_loo = (
                self.global_presence_count_ - labels + 0.5
            ) / (len(self.records_) - 1 + 1.0)
            source_count = self.source_presence_count_[record.work_id] - labels
            source_n = self.source_record_count_[record.work_id] - 1
            source_loo = (
                source_count + self.source_prior_strength * global_loo
            ) / (source_n + self.source_prior_strength)
            title_loo = self.title_encoder_.transform_training_index(record_index)
            graph_loo = hypergraph_kernel(np.delete(self.compositions_, record_index, axis=0))
            for mask_index, fraction in enumerate(self.mask_fractions):
                mask = deterministic_observation_mask(
                    record, self.vocabulary_, fraction, self.random_seed + mask_index
                )
                observed_weights = true_composition * mask
                features = self._feature_matrix(
                    title=record.title,
                    work_id=record.work_id,
                    observed_weights=observed_weights,
                    global_prevalence=global_loo,
                    source_prevalence=source_loo,
                    title_score=title_loo,
                    graph_kernel=graph_loo,
                )
                feature_blocks.append(features)
                label_blocks.append(labels)
                group_blocks.extend([record.work_id] * len(self.vocabulary_))
                present = np.flatnonzero(labels)
                ratio_rows.append(features[present])
                ratio_targets.append(np.log(np.clip(true_composition[present], 1e-8, None)))
        return (
            np.vstack(feature_blocks),
            np.concatenate(label_blocks),
            np.asarray(group_blocks),
            np.vstack(ratio_rows),
            np.concatenate(ratio_targets),
        )

    def _fit_group_dro(self, features: np.ndarray, labels: np.ndarray, groups: np.ndarray) -> dict[str, float]:
        unique_groups = sorted(set(groups.tolist()))
        weights = {group: 1.0 / len(unique_groups) for group in unique_groups}
        group_sizes = {group: int((groups == group).sum()) for group in unique_groups}
        if self.group_dro_iterations <= 0:
            self.inclusion_model_.fit(features, labels)
            return weights
        for _ in range(self.group_dro_iterations):
            sample_weight = np.array([
                weights[group] / group_sizes[group] for group in groups
            ])
            sample_weight *= len(sample_weight) / sample_weight.sum()
            self.inclusion_model_.fit(features, labels, sample_weight=sample_weight)
            probabilities = np.clip(self.inclusion_model_.predict_proba(features)[:, 1], 1e-7, 1 - 1e-7)
            losses = {}
            for group in unique_groups:
                mask = groups == group
                losses[group] = float(np.mean(
                    -(labels[mask] * np.log(probabilities[mask]) + (1 - labels[mask]) * np.log(1 - probabilities[mask]))
                ))
            updated = {
                group: weights[group] * math.exp(self.group_dro_eta * losses[group])
                for group in unique_groups
            }
            normalizer = sum(updated.values())
            weights = {group: value / normalizer for group, value in updated.items()}
        return weights

    def _observed_vector(self, observed: dict[str, float] | None) -> tuple[np.ndarray, list[str]]:
        vector = np.zeros(len(self.vocabulary_), dtype=float)
        out_of_vocabulary = []
        for material, value in (observed or {}).items():
            if material not in self.material_index_:
                out_of_vocabulary.append(material)
                continue
            if value <= 0:
                raise ValueError("Observed material weights must be positive")
            vector[self.material_index_[material]] = float(value)
        return vector, sorted(out_of_vocabulary)

    def count_posterior(
        self,
        work_id: str | None,
        observed_count: int = 0,
        observation_fraction: float | None = None,
    ) -> np.ndarray:
        posterior = self.source_count_distribution_.get(work_id, self.global_count_distribution_).copy()
        support = np.arange(1, self.maximum_count_ + 1)
        posterior[support < max(1, observed_count)] = 0.0
        if observed_count and observation_fraction is not None:
            if not 0 < observation_fraction < 1:
                raise ValueError("observation_fraction must be between zero and one")
            # Evaluation masks retain exactly round(K * fraction), capped to
            # leave at least one hidden component. Condition on that registered
            # observation mechanism rather than pretending masks are Bernoulli.
            likelihood = np.array([
                float(
                    min(int(total_count) - 1, max(1, round(int(total_count) * observation_fraction)))
                    == observed_count
                )
                for total_count in support
            ])
            posterior *= likelihood
        if posterior.sum() == 0:
            posterior[-1] = 1.0
        return posterior / posterior.sum()

    def predict(
        self,
        *,
        title: str,
        work_id: str | None = None,
        observed: dict[str, float] | None = None,
        odor_target: np.ndarray | list[float] | None = None,
        posterior_samples: int = 1000,
        random_seed: int | None = None,
        observation_fraction: float | None = None,
    ) -> dict:
        observed_weights, out_of_vocabulary = self._observed_vector(observed)
        odor_array = None if odor_target is None else np.asarray(odor_target, dtype=float)
        features = self._feature_matrix(
            title=title, work_id=work_id, observed_weights=observed_weights, odor_target=odor_array
        )
        scaled_features = self.feature_scaler_.transform(features)
        probabilities = self.inclusion_model_.predict_proba(scaled_features)[:, 1]
        parameter_samples = self.inclusion_model_.sample_parameters(
            posterior_samples,
            self.random_seed if random_seed is None else random_seed,
        )
        inclusion_design = np.column_stack([np.ones(len(scaled_features)), scaled_features])
        inclusion_samples = expit(
            inclusion_design @ parameter_samples.T
            + self.inclusion_model_.class_balance_logit_offset_
        )
        inclusion_lower, inclusion_upper = np.quantile(inclusion_samples, [0.1, 0.9], axis=1)
        probabilities[observed_weights > 0] = 1.0
        inclusion_lower[observed_weights > 0] = 1.0
        inclusion_upper[observed_weights > 0] = 1.0
        count_probabilities = self.count_posterior(
            work_id,
            int((observed_weights > 0).sum()),
            observation_fraction=observation_fraction,
        )
        count_support = np.arange(1, self.maximum_count_ + 1)
        # Posterior median is the Bayes action under the registered absolute
        # cardinality-error loss.
        selected_count = int(count_support[np.searchsorted(np.cumsum(count_probabilities), 0.5)])
        selected_count = max(selected_count, int((observed_weights > 0).sum()), 1)
        selected_indices = np.argsort(-probabilities, kind="stable")[:selected_count]

        ratio_log = self.ratio_model_.predict(self.ratio_scaler_.transform(features[selected_indices]))
        ratio_positive = np.exp(ratio_log - ratio_log.max())
        ratio_mean = ratio_positive / ratio_positive.sum()
        alpha = np.clip(ratio_mean * self.dirichlet_concentration_, 1e-3, None)
        generator = np.random.default_rng(self.random_seed if random_seed is None else random_seed)
        samples = generator.dirichlet(alpha, size=posterior_samples)
        lower, upper = np.quantile(samples, [0.1, 0.9], axis=0)

        selected = []
        for local_index, material_index in enumerate(selected_indices):
            selected.append({
                "material_id": self.vocabulary_[material_index],
                "inclusion_probability": float(probabilities[material_index]),
                "inclusion_interval_80": [
                    float(inclusion_lower[material_index]),
                    float(inclusion_upper[material_index]),
                ],
                "posterior_mean_ratio": float(ratio_mean[local_index]),
                "ratio_interval_80": [float(lower[local_index]), float(upper[local_index])],
                "chemical_evidence_available": bool(self.chemical_available_[material_index]),
                "chemical_proxy": self.chemical_proxy_used_.get(self.vocabulary_[material_index]),
                "observed": bool(observed_weights[material_index] > 0),
            })
        return {
            "model": "xiangji-cgir-v1",
            "title": title,
            "work_id": work_id,
            "vocabulary_size": len(self.vocabulary_),
            "selected_count": selected_count,
            "count_posterior": {
                str(value): float(probability) for value, probability in zip(count_support, count_probabilities)
            },
            "materials": selected,
            "all_inclusion_probabilities": {
                material: float(probabilities[index]) for index, material in enumerate(self.vocabulary_)
            },
            "all_inclusion_intervals_80": {
                material: [float(inclusion_lower[index]), float(inclusion_upper[index])]
                for index, material in enumerate(self.vocabulary_)
            },
            "out_of_vocabulary_observations": out_of_vocabulary,
            "dirichlet_concentration": self.dirichlet_concentration_,
            "posterior_samples": samples.tolist(),
        }

    def diagnostics(self) -> dict:
        return {
            "model": "xiangji-cgir-v1",
            "training_formula_count": len(self.records_),
            "vocabulary_size": len(self.vocabulary_),
            "feature_names": list(FEATURE_NAMES),
            "enabled_channels": sorted(self.enabled_channels),
            "inclusion_coefficients": {
                name: float(value) for name, value in zip(FEATURE_NAMES, self.inclusion_model_.coef_[0])
            },
            "inclusion_coefficient_sd": {
                name: float(value) for name, value in zip(
                    FEATURE_NAMES,
                    np.sqrt(np.clip(np.diag(self.inclusion_model_.posterior_covariance_)[1:], 0.0, None)),
                )
            },
            "group_dro_weights": self.group_weights_,
            "training_source_log_loss": self.training_source_log_loss_,
            "inclusion_map_gradient_inf_norm": self.inclusion_model_.gradient_inf_norm_,
            "case_control_logit_offset": self.inclusion_model_.class_balance_logit_offset_,
            "chemical_material_count": int(self.chemical_available_.sum()),
            "chemical_proxies": self.chemical_proxy_used_,
            "ratio_residual_sd_log_scale": self.ratio_residual_sd_,
            "dirichlet_concentration": self.dirichlet_concentration_,
            "maximum_training_component_count": self.maximum_count_,
            "graph_reducer": self.graph_reducer,
        }
