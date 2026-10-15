"""Canonical loaders and leakage-aware split definitions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

RESEARCH_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = RESEARCH_ROOT / "data" / "raw"


def load_json(name: str) -> dict | list:
    return json.loads((RAW_DIR / name).read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Corpus:
    recipes: list[dict]
    materials: list[dict]
    dimensions: list[str]

    @property
    def material_ids(self) -> list[str]:
        return [m["id"] for m in self.materials]

    @property
    def material_matrix(self) -> np.ndarray:
        """Odor dimensions x materials."""
        return np.asarray([m["vector"] for m in self.materials], dtype=float).T

    def outcome(self, recipe: dict) -> np.ndarray:
        index = {material_id: i for i, material_id in enumerate(self.material_ids)}
        y = np.zeros(len(index), dtype=float)
        total = sum(max(float(v), 0.0) for v in recipe["ingredients"].values())
        if total <= 0:
            return y
        for material_id, amount in recipe["ingredients"].items():
            if material_id in index and amount > 0:
                y[index[material_id]] = float(amount) / total
        return y


def load_corpus() -> Corpus:
    recipe_data = load_json("known_recipes_v2.json")
    material_data = load_json("materials.json")
    if recipe_data["dimensions"] != material_data["dimensions"]:
        raise ValueError("Recipe and material odor dimensions are inconsistent")
    return Corpus(
        recipes=recipe_data["recipes"],
        materials=material_data["materials"],
        dimensions=material_data["dimensions"],
    )


def historical_hash_split(recipes: Iterable[dict]) -> tuple[list[int], list[int]]:
    """Exact v2.4 split, retained only for reproducibility comparisons."""
    train, test = [], []
    for i, recipe in enumerate(recipes):
        digest = int(hashlib.sha256(recipe["id"].encode()).hexdigest()[:8], 16)
        (test if digest % 5 == 4 else train).append(i)
    return train, test


def leave_one_family_out(recipes: Iterable[dict]) -> list[tuple[str, list[int], list[int]]]:
    """Harder style-family extrapolation; this is not a source split."""
    rows = list(recipes)
    folds = []
    for family in sorted({row["family"] for row in rows}):
        test = [i for i, row in enumerate(rows) if row["family"] == family]
        train = [i for i in range(len(rows)) if i not in test]
        folds.append((family, train, test))
    return folds
