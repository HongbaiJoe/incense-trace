"""Transparent baselines covering frequency, text, perception and chemistry."""

from __future__ import annotations

import math
from collections import Counter

import numpy as np
from scipy.optimize import nnls
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from xiangji.metrics import normalize_rows


def text_of(recipe: dict) -> str:
    return f'{recipe.get("name", "")} {recipe.get("description", "")}'.strip()


def char_ngrams(text: str) -> list[str]:
    chars = [c for c in text if not c.isspace()]
    return chars + ["".join(chars[i : i + 2]) for i in range(max(len(chars) - 1, 0))]


class FrequencyPrior:
    def fit(self, recipes: list[dict], y: np.ndarray) -> "FrequencyPrior":
        self.prior = normalize_rows(np.mean(y, axis=0))
        return self

    def predict(self, recipes: list[dict]) -> np.ndarray:
        return np.tile(self.prior, (len(recipes), 1))


class BM25MaterialModel:
    """Retrieval baseline: BM25 recipe similarity followed by outcome averaging."""

    def __init__(self, k1: float = 1.5, b: float = 0.75, neighbors: int = 5):
        self.k1, self.b, self.neighbors = k1, b, neighbors

    def fit(self, recipes: list[dict], y: np.ndarray) -> "BM25MaterialModel":
        self.documents = [Counter(char_ngrams(text_of(r))) for r in recipes]
        self.y = y
        self.lengths = np.asarray([sum(d.values()) for d in self.documents], dtype=float)
        self.avg_length = float(self.lengths.mean()) if len(self.lengths) else 1.0
        df = Counter(term for document in self.documents for term in document)
        n = len(self.documents)
        self.idf = {term: math.log(1.0 + (n - count + 0.5) / (count + 0.5)) for term, count in df.items()}
        return self

    def predict(self, recipes: list[dict]) -> np.ndarray:
        outputs = []
        for recipe in recipes:
            query = Counter(char_ngrams(text_of(recipe)))
            scores = np.zeros(len(self.documents))
            for i, document in enumerate(self.documents):
                norm = self.k1 * (1 - self.b + self.b * self.lengths[i] / max(self.avg_length, 1e-9))
                for term, qtf in query.items():
                    tf = document.get(term, 0)
                    if tf:
                        scores[i] += self.idf.get(term, 0.0) * (tf * (self.k1 + 1) / (tf + norm)) * qtf
            keep = np.argsort(scores)[::-1][: min(self.neighbors, len(scores))]
            weights = np.maximum(scores[keep], 0.0)
            weights = weights / weights.sum() if weights.sum() else np.full(len(keep), 1 / len(keep))
            outputs.append(weights @ self.y[keep])
        return normalize_rows(np.asarray(outputs))


class OdorKNN:
    def __init__(self, neighbors: int = 5):
        self.model = Pipeline([
            ("scale", StandardScaler()),
            ("knn", KNeighborsRegressor(n_neighbors=neighbors, weights="distance")),
        ])

    def fit(self, recipes: list[dict], y: np.ndarray) -> "OdorKNN":
        self.model.fit(np.asarray([r["target"] for r in recipes]), y)
        return self

    def predict(self, recipes: list[dict]) -> np.ndarray:
        x = np.asarray([r["target"] for r in recipes])
        return normalize_rows(np.clip(self.model.predict(x), 0.0, None))


class RidgeComposition:
    def __init__(self, alpha: float = 2.0):
        self.model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])

    def fit(self, recipes: list[dict], y: np.ndarray) -> "RidgeComposition":
        self.model.fit(np.asarray([r["target"] for r in recipes]), y)
        return self

    def predict(self, recipes: list[dict]) -> np.ndarray:
        x = np.asarray([r["target"] for r in recipes])
        return normalize_rows(np.clip(self.model.predict(x), 0.0, None))


class ChemicalNNLS:
    """Untrained inverse baseline using the material odor matrix only."""

    def __init__(self, material_matrix: np.ndarray):
        self.material_matrix = np.asarray(material_matrix, dtype=float)

    def fit(self, recipes: list[dict], y: np.ndarray) -> "ChemicalNNLS":
        return self

    def predict(self, recipes: list[dict]) -> np.ndarray:
        outputs = []
        for recipe in recipes:
            weights, _ = nnls(self.material_matrix, np.asarray(recipe["target"], dtype=float))
            outputs.append(weights)
        return normalize_rows(np.asarray(outputs))
