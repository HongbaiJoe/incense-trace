"""Training-fold hypergraph and source-backed chemical similarity kernels."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from xiangji.data import RESEARCH_ROOT


def safe_cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    return float(np.dot(left, right) / denominator) if denominator else 0.0


def hypergraph_kernel(compositions: np.ndarray, smoothing: float = 2.0) -> np.ndarray:
    binary = (compositions > 0).astype(float)
    frequency = binary.sum(axis=0)
    cooccurrence = binary.T @ binary
    global_prevalence = (frequency + 0.5) / (len(binary) + 1.0)
    # Directed posterior-predictive P(candidate j | observed i), shrunk to
    # global prevalence. Rows are observed materials; columns are candidates.
    kernel = (cooccurrence + smoothing * global_prevalence[None, :]) / (frequency[:, None] + smoothing)
    np.fill_diagonal(kernel, 1.0)
    return np.clip(kernel, 0.0, 1.0)


def _dense_sparse(mapping: dict[str, float], keys: tuple[str, ...]) -> np.ndarray:
    return np.array([float(mapping.get(key, 0.0)) for key in keys], dtype=float)


def _profile_views(payload: dict) -> tuple[dict[str, list[dict]], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    by_material: defaultdict[str, list[dict]] = defaultdict(list)
    bit_keys, physicochemical_keys, tag_keys = set(), set(), set()
    for profile in payload["profiles"]:
        by_material[profile["ontology_material_id"]].append(profile)
        bit_keys.update(profile["compound_set_molecular_view"]["weighted_morgan_bits"])
        physicochemical_keys.update(profile["physicochemical_view"])
        tag_keys.update(profile["odor_tag_view"]["weights"])
    return by_material, tuple(sorted(bit_keys)), tuple(sorted(physicochemical_keys)), tuple(sorted(tag_keys))


def build_chemical_kernel(
    vocabulary: tuple[str, ...],
    representations_path: Path | None = None,
    proxy_map: dict[str, str] | None = None,
    weights: tuple[float, float, float] = (0.5, 0.25, 0.25),
) -> tuple[np.ndarray, np.ndarray, dict[str, str]]:
    representations_path = representations_path or RESEARCH_ROOT / "data" / "processed" / "material_representations_v0.1.json"
    payload = json.loads(representations_path.read_text(encoding="utf-8"))
    by_material, bit_keys, phys_keys, tag_keys = _profile_views(payload)
    proxy_map = proxy_map or {}
    resolved = {
        material: material if material in by_material else proxy_map.get(material, material)
        for material in vocabulary
    }
    proxy_used = {
        material: target for material, target in resolved.items()
        if material != target and target in by_material
    }
    available = np.array([resolved[material] in by_material for material in vocabulary], dtype=bool)
    kernel = np.zeros((len(vocabulary), len(vocabulary)), dtype=float)

    phys_rows = []
    for profiles in by_material.values():
        for profile in profiles:
            phys_rows.append(_dense_sparse(profile["physicochemical_view"], phys_keys))
    phys_matrix = np.vstack(phys_rows)
    phys_mean = phys_matrix.mean(axis=0)
    phys_std = phys_matrix.std(axis=0)
    phys_std[phys_std == 0] = 1.0

    def similarity(left: dict, right: dict) -> float:
        left_bits = _dense_sparse(left["compound_set_molecular_view"]["weighted_morgan_bits"], bit_keys)
        right_bits = _dense_sparse(right["compound_set_molecular_view"]["weighted_morgan_bits"], bit_keys)
        intersection = np.minimum(left_bits, right_bits).sum()
        union = np.maximum(left_bits, right_bits).sum()
        tanimoto = float(intersection / union) if union else 0.0
        left_phys = (_dense_sparse(left["physicochemical_view"], phys_keys) - phys_mean) / phys_std
        right_phys = (_dense_sparse(right["physicochemical_view"], phys_keys) - phys_mean) / phys_std
        phys = max(0.0, safe_cosine(left_phys, right_phys))
        tags = max(0.0, safe_cosine(
            _dense_sparse(left["odor_tag_view"]["weights"], tag_keys),
            _dense_sparse(right["odor_tag_view"]["weights"], tag_keys),
        ))
        return weights[0] * tanimoto + weights[1] * phys + weights[2] * tags

    for left_index, left_material in enumerate(vocabulary):
        if not available[left_index]:
            continue
        for right_index in range(left_index, len(vocabulary)):
            if not available[right_index]:
                continue
            right_material = vocabulary[right_index]
            scores = [
                similarity(left, right)
                for left in by_material[resolved[left_material]]
                for right in by_material[resolved[right_material]]
            ]
            value = max(scores)
            kernel[left_index, right_index] = value
            kernel[right_index, left_index] = value
    for index, is_available in enumerate(available):
        if is_available:
            kernel[index, index] = 1.0
    return kernel, available, proxy_used


def affinity_from_observed(
    kernel: np.ndarray,
    observed_weights: np.ndarray,
    reducer: str = "weighted_mean",
) -> np.ndarray:
    if observed_weights.ndim != 1 or kernel.shape[0] != observed_weights.shape[0]:
        raise ValueError("Kernel and observation vector dimensions differ")
    total = observed_weights.sum()
    if total <= 0:
        return np.zeros(kernel.shape[0], dtype=float)
    observed_rows = kernel[observed_weights > 0]
    if reducer == "weighted_mean":
        normalized = observed_weights / total
        return normalized @ kernel
    if reducer == "mean":
        return observed_rows.mean(axis=0)
    if reducer == "max":
        return observed_rows.max(axis=0)
    raise ValueError("reducer must be 'weighted_mean', 'mean', or 'max'")
