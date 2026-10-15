"""Leakage-safe data structures for Cycle 3 models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from xiangji.data import RESEARCH_ROOT


@dataclass(frozen=True)
class FormulaRecord:
    reference_id: str
    family_id: str
    work_id: str
    title: str
    composition: dict[str, float]


@dataclass(frozen=True)
class DevelopmentCorpus:
    records: tuple[FormulaRecord, ...]
    sealed_reference_ids: frozenset[str]
    sealed_work_id: str
    reference_sha256: str
    split_sha256: str

    def by_id(self) -> dict[str, FormulaRecord]:
        return {record.reference_id: record for record in self.records}


def load_development_corpus(
    reference_path: Path | None = None,
    split_path: Path | None = None,
) -> DevelopmentCorpus:
    reference_path = reference_path or RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
    split_path = split_path or RESEARCH_ROOT / "data" / "curated" / "source_blocked_splits_v0.1.json"
    reference_bytes = reference_path.read_bytes()
    split_bytes = split_path.read_bytes()
    reference = json.loads(reference_bytes)
    split = json.loads(split_bytes)
    sealed_ids = frozenset(split["sealed_evaluation"]["reference_ids"])
    sealed_work = split["sealed_evaluation"]["work_id"]
    # Filter before constructing any model-facing record or corpus statistic.
    public_development_rows = [
        row for row in reference["records"] if row["reference_id"] not in sealed_ids
    ]
    records = tuple(
        FormulaRecord(
            reference_id=row["reference_id"],
            family_id=row["formula_family_id"],
            work_id=row["work_id"],
            title=row["formula_title_verbatim"],
            composition={key: float(value) for key, value in row["composition_aromatic_only"].items()},
        )
        for row in public_development_rows
    )
    if any(record.reference_id in sealed_ids or record.work_id == sealed_work for record in records):
        raise ValueError("Sealed source leaked into the development corpus")
    return DevelopmentCorpus(
        records=records,
        sealed_reference_ids=sealed_ids,
        sealed_work_id=sealed_work,
        reference_sha256=hashlib.sha256(reference_bytes).hexdigest(),
        split_sha256=hashlib.sha256(split_bytes).hexdigest(),
    )


def build_vocabulary(records: list[FormulaRecord] | tuple[FormulaRecord, ...]) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    for record in records:
        for material in record.composition:
            counts[material] = counts.get(material, 0) + 1
    return tuple(sorted(counts, key=lambda material: (-counts[material], material)))


def composition_matrix(records: list[FormulaRecord] | tuple[FormulaRecord, ...], vocabulary: tuple[str, ...]) -> np.ndarray:
    index = {material: position for position, material in enumerate(vocabulary)}
    matrix = np.zeros((len(records), len(vocabulary)), dtype=float)
    for row_index, record in enumerate(records):
        for material, value in record.composition.items():
            if material in index:
                matrix[row_index, index[material]] = value
    return matrix


def deterministic_observation_mask(
    record: FormulaRecord,
    vocabulary: tuple[str, ...],
    observed_fraction: float,
    seed: int,
) -> np.ndarray:
    if not 0 < observed_fraction < 1:
        raise ValueError("observed_fraction must be between zero and one")
    present = [index for index, material in enumerate(vocabulary) if material in record.composition]
    if len(present) < 2:
        raise ValueError("Masking requires at least two in-vocabulary formula components")
    count = min(len(present) - 1, max(1, round(len(present) * observed_fraction)))
    key = f"{record.reference_id}|{observed_fraction:.6f}|{seed}".encode()
    local_seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
    generator = np.random.default_rng(local_seed)
    observed = generator.choice(present, size=count, replace=False)
    mask = np.zeros(len(vocabulary), dtype=bool)
    mask[observed] = True
    return mask


def load_folds(split_path: Path | None = None, kind: str = "primary") -> list[dict]:
    split_path = split_path or RESEARCH_ROOT / "data" / "curated" / "source_blocked_splits_v0.1.json"
    split = json.loads(split_path.read_text(encoding="utf-8"))
    sealed_ids = set(split["sealed_evaluation"]["reference_ids"])
    if kind == "primary":
        folds = split["primary_two_unseen_work_folds"]
    elif kind == "development":
        folds = split["development_leave_one_work_out_folds"]
    else:
        raise ValueError("kind must be 'primary' or 'development'")
    for fold in folds:
        if sealed_ids & (set(fold["train_reference_ids"]) | set(fold["test_reference_ids"])):
            raise ValueError(f"Sealed source leaked into fold {fold['fold_id']}")
    return folds
