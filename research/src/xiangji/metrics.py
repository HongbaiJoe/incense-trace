"""Metrics for sparse set-and-composition prediction."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, f1_score


def normalize_rows(values: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(values, dtype=float), 0.0, None)
    if values.ndim == 1:
        total = values.sum()
        return values / total if total > 0 else values
    totals = values.sum(axis=1, keepdims=True)
    return np.divide(values, totals, out=np.zeros_like(values), where=totals > 0)


def sparsify(values: np.ndarray, k: int = 6) -> np.ndarray:
    values = normalize_rows(values)
    was_1d = values.ndim == 1
    rows = values[None, :] if was_1d else values.copy()
    result = np.zeros_like(rows)
    for i, row in enumerate(rows):
        keep = np.argsort(row)[::-1][: min(k, len(row))]
        result[i, keep] = row[keep]
    result = normalize_rows(result)
    return result[0] if was_1d else result


def evaluate(y_true: np.ndarray, y_score: np.ndarray, k: int = 6) -> dict[str, float]:
    y_true = normalize_rows(y_true)
    y_score = normalize_rows(y_score)
    y_pred = sparsify(y_score, k=k)
    truth = y_true > 0
    predicted = y_pred > 0
    n = len(y_true)

    top1 = np.mean(np.argmax(y_true, axis=1) == np.argmax(y_score, axis=1))
    recalls = []
    jaccards = []
    union_maes = []
    for i in range(n):
        order = set(np.argsort(y_score[i])[::-1][: min(k, y_score.shape[1])])
        true_set = set(np.flatnonzero(truth[i]))
        recalls.append(len(order & true_set) / max(len(true_set), 1))
        union = truth[i] | predicted[i]
        numerator = np.minimum(y_true[i], y_pred[i])[union].sum()
        denominator = np.maximum(y_true[i], y_pred[i])[union].sum()
        jaccards.append(numerator / denominator if denominator else 0.0)
        union_maes.append(np.abs(y_true[i] - y_pred[i])[union].mean() if union.any() else 0.0)

    per_label_ap = []
    for j in range(truth.shape[1]):
        if truth[:, j].any():
            per_label_ap.append(average_precision_score(truth[:, j], y_score[:, j]))

    return {
        "n": int(n),
        "top1": float(top1),
        "recall_at_6": float(np.mean(recalls)),
        "weighted_jaccard": float(np.mean(jaccards)),
        "union_ratio_mae": float(np.mean(union_maes)),
        "micro_f1_at_6": float(f1_score(truth.ravel(), predicted.ravel(), zero_division=0)),
        "macro_f1_at_6": float(f1_score(truth, predicted, average="macro", zero_division=0)),
        "macro_average_precision": float(np.mean(per_label_ap)) if per_label_ap else 0.0,
    }
