"""Convex odor-conditioned inverse formulation with an external chemistry bridge."""

from __future__ import annotations

import numpy as np
from scipy.optimize import nnls

from xiangji.baselines.models import OdorKNN, RidgeComposition
from xiangji.metrics import normalize_rows
from xiangji.representations.odor import build_odor_views


class ForwardConsistentInverse:
    """MAP-like inverse: learned composition prior plus forward odor agreement.

    The objective is quadratic under non-negativity:

        lambda_f ||A w - o||^2 + lambda_p ||w - p(o)||^2.

    ``A`` blends the frozen legacy material-odor view with source-backed
    chemical odor tags only where such external profiles exist.
    """

    def __init__(
        self,
        material_ids: tuple[str, ...],
        legacy_material_matrix: np.ndarray,
        *,
        forward_strength: float = 1.0,
        prior_strength: float = 1.0,
        chemistry_blend: float = 0.0,
        ridge_alpha: float = 2.0,
        prior_model: str = "ridge",
        chemical_permutation_seed: int | None = None,
    ):
        if forward_strength < 0 or prior_strength <= 0:
            raise ValueError("forward_strength must be non-negative and prior_strength positive")
        if not 0 <= chemistry_blend <= 1:
            raise ValueError("chemistry_blend must lie in [0, 1]")
        self.material_ids = material_ids
        self.legacy_material_matrix = np.asarray(legacy_material_matrix, dtype=float)
        self.forward_strength = forward_strength
        self.prior_strength = prior_strength
        self.chemistry_blend = chemistry_blend
        self.ridge_alpha = ridge_alpha
        self.prior_model = prior_model
        self.chemical_permutation_seed = chemical_permutation_seed

    def _forward_matrix(self) -> np.ndarray:
        views = build_odor_views(self.material_ids)
        chemical = np.zeros_like(self.legacy_material_matrix)
        for index, profiles in enumerate(views.chemical_profile_vectors):
            if profiles:
                chemical[:, index] = np.mean(np.vstack(profiles), axis=0)
        available = views.chemical_available.copy()
        if self.chemical_permutation_seed is not None and available.sum() > 1:
            indices = np.flatnonzero(available)
            permutation = np.random.default_rng(self.chemical_permutation_seed).permutation(indices)
            chemical[:, indices] = chemical[:, permutation]
        matrix = self.legacy_material_matrix.copy()
        matrix[:, available] = (
            (1 - self.chemistry_blend) * matrix[:, available]
            + self.chemistry_blend * chemical[:, available]
        )
        return matrix

    def fit(self, recipes: list[dict], y: np.ndarray) -> "ForwardConsistentInverse":
        if self.prior_model == "ridge":
            prior = RidgeComposition(alpha=self.ridge_alpha)
        elif self.prior_model == "odor_knn":
            prior = OdorKNN(neighbors=min(5, len(recipes)))
        else:
            raise ValueError("prior_model must be 'ridge' or 'odor_knn'")
        self.prior_model_ = prior.fit(recipes, y)
        self.forward_matrix_ = self._forward_matrix()
        return self

    def predict(self, recipes: list[dict]) -> np.ndarray:
        priors = self.prior_model_.predict(recipes)
        outputs = []
        identity = np.eye(len(self.material_ids))
        design = np.vstack([
            np.sqrt(self.forward_strength) * self.forward_matrix_,
            np.sqrt(self.prior_strength) * identity,
        ])
        for recipe, prior in zip(recipes, priors):
            target = np.asarray(recipe["target"], dtype=float)
            response = np.concatenate([
                np.sqrt(self.forward_strength) * target,
                np.sqrt(self.prior_strength) * prior,
            ])
            weights, _ = nnls(design, response)
            outputs.append(weights)
        return normalize_rows(np.asarray(outputs))

    def forward_reconstruction(self, compositions: np.ndarray) -> np.ndarray:
        return np.asarray(compositions) @ self.forward_matrix_.T
