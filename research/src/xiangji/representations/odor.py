"""Transparent odor views for optional odor-conditioned inference."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from xiangji.data import RESEARCH_ROOT
from xiangji.representations.kernels import safe_cosine

ODOR_DIMENSIONS = (
    "woody", "resinous", "sweet", "floral", "spicy", "herbal",
    "fresh", "earthy", "smoky", "musky", "fruity", "tenacity",
)

LEGACY_TO_ONTOLOGY = {
    "agarwood": "agarwood",
    "sandalwood": "sandalwood_white",
    "frankincense": "frankincense",
    "benzoin": "benzoin",
    "borneol": "borneol_family",
    "clove": "clove_bud",
    "cassia": "cassia",
    "nard": "spikenard",
    "patchouli": "patchouli",
    "calamus": "calamus",
    "lingling": "linglingxiang",
    "cyperus": "cyperus",
    "angelica": "angelica_dahurica",
    "costus": "costus",
    "musk": "musk",
    "styrax": "storax",
    "jiangzhen": "jiangzhenxiang",
    "anise": "fennel",
    "chuanxiong": "chuanxiong",
}

TAG_TO_DIMENSIONS = {
    "woody": {"woody": 1.0}, "agarwood": {"woody": 0.8, "tenacity": 0.7},
    "sandalwood": {"woody": 0.9, "tenacity": 0.7}, "guaiacwood": {"woody": 1.0},
    "balsamic": {"resinous": 0.8, "sweet": 0.3, "tenacity": 0.5},
    "benzoin": {"resinous": 0.8}, "benzoin_like": {"resinous": 0.8},
    "storax": {"resinous": 0.8}, "frankincense": {"resinous": 0.8, "fresh": 0.3},
    "sweet": {"sweet": 1.0}, "vanilla": {"sweet": 1.0}, "tonka_like": {"sweet": 0.8},
    "floral": {"floral": 1.0}, "rose": {"floral": 1.0},
    "spicy": {"spicy": 1.0}, "warm_spicy": {"spicy": 1.0},
    "clove": {"spicy": 0.9}, "clove_like": {"spicy": 0.9}, "cinnamon_bark": {"spicy": 0.9},
    "anise": {"herbal": 0.7, "sweet": 0.4}, "fennel": {"herbal": 0.8},
    "pine": {"fresh": 0.8, "woody": 0.3}, "citrus": {"fresh": 0.8, "fruity": 0.5},
    "eucalyptus": {"fresh": 0.9}, "camphoraceous": {"fresh": 0.9}, "camphor": {"fresh": 0.9},
    "earthy": {"earthy": 1.0}, "patchouli": {"earthy": 0.8, "woody": 0.4},
    "musk": {"musky": 1.0, "tenacity": 0.8}, "animalic": {"musky": 0.9},
    "fruity": {"fruity": 1.0}, "fixative": {"tenacity": 1.0},
}


@dataclass
class OdorViews:
    vocabulary: tuple[str, ...]
    legacy_vectors: np.ndarray
    legacy_available: np.ndarray
    chemical_profile_vectors: tuple[tuple[np.ndarray, ...], ...]
    chemical_available: np.ndarray
    proxy_used: dict[str, str]

    def similarities(self, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        target = np.asarray(target, dtype=float)
        if target.shape != (len(ODOR_DIMENSIONS),):
            raise ValueError(f"Odor target must have {len(ODOR_DIMENSIONS)} dimensions")
        legacy = np.array([
            max(0.0, safe_cosine(target, row)) if available else 0.0
            for row, available in zip(self.legacy_vectors, self.legacy_available)
        ])
        chemical = np.array([
            max((max(0.0, safe_cosine(target, profile)) for profile in profiles), default=0.0)
            for profiles in self.chemical_profile_vectors
        ])
        return legacy, chemical


def _tag_vector(weights: dict[str, float]) -> np.ndarray:
    index = {name: position for position, name in enumerate(ODOR_DIMENSIONS)}
    vector = np.zeros(len(ODOR_DIMENSIONS), dtype=float)
    for tag, tag_weight in weights.items():
        for dimension, mapping_weight in TAG_TO_DIMENSIONS.get(tag, {}).items():
            vector[index[dimension]] += float(tag_weight) * mapping_weight
    maximum = vector.max()
    return vector / maximum if maximum > 0 else vector


def build_odor_views(
    vocabulary: tuple[str, ...],
    proxy_map: dict[str, str] | None = None,
    legacy_path: Path | None = None,
    representations_path: Path | None = None,
) -> OdorViews:
    legacy_path = legacy_path or RESEARCH_ROOT / "data" / "raw" / "materials.json"
    representations_path = representations_path or RESEARCH_ROOT / "data" / "processed" / "material_representations_v0.1.json"
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
    representations = json.loads(representations_path.read_text(encoding="utf-8"))
    if tuple(legacy["dimensions"]) != ODOR_DIMENSIONS:
        raise ValueError("Legacy odor dimensions differ from the frozen Cycle 3 order")
    proxy_map = proxy_map or {}
    legacy_by_material: dict[str, np.ndarray] = {}
    for row in legacy["materials"]:
        vector = np.asarray(row["vector"], dtype=float)
        legacy_by_material[row["id"]] = vector
        if row["id"] in LEGACY_TO_ONTOLOGY:
            legacy_by_material[LEGACY_TO_ONTOLOGY[row["id"]]] = vector
    profiles_by_material: dict[str, list[np.ndarray]] = {}
    for profile in representations["profiles"]:
        profiles_by_material.setdefault(profile["ontology_material_id"], []).append(
            _tag_vector(profile["odor_tag_view"]["weights"])
        )
    proxy_used = {}
    legacy_vectors, legacy_available, chemical_profiles, chemical_available = [], [], [], []
    for material in vocabulary:
        resolved = LEGACY_TO_ONTOLOGY.get(material, material)
        if material not in legacy_by_material and material not in profiles_by_material:
            resolved = proxy_map.get(material, resolved)
            if resolved != material and (resolved in legacy_by_material or resolved in profiles_by_material):
                proxy_used[material] = resolved
        legacy_key = material if material in legacy_by_material else resolved
        legacy_vectors.append(legacy_by_material.get(legacy_key, np.zeros(len(ODOR_DIMENSIONS))))
        legacy_available.append(legacy_key in legacy_by_material)
        profiles = tuple(profiles_by_material.get(resolved, []))
        chemical_profiles.append(profiles)
        chemical_available.append(bool(profiles))
    return OdorViews(
        vocabulary=vocabulary,
        legacy_vectors=np.vstack(legacy_vectors),
        legacy_available=np.asarray(legacy_available, dtype=bool),
        chemical_profile_vectors=tuple(chemical_profiles),
        chemical_available=np.asarray(chemical_available, dtype=bool),
        proxy_used=proxy_used,
    )
