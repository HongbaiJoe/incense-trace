import numpy as np
import pytest

from xiangji.evaluation.v2_benchmark import (
    aggregate_records,
    exact_sign_flip_pvalue,
    observed_materials,
)
from xiangji.models.data import FormulaRecord


def test_aggregation_averages_repeats_before_work_macro():
    rows = [
        {"reference_id": "a", "work_id": "A", "metrics": {"hidden_f1": 0.2}},
        {"reference_id": "a", "work_id": "A", "metrics": {"hidden_f1": 0.4}},
        {"reference_id": "b", "work_id": "B", "metrics": {"hidden_f1": 0.8}},
    ]
    formula, work, macro = aggregate_records(rows)
    assert formula["a"]["hidden_f1"] == pytest.approx(0.3)
    assert work["A"]["hidden_f1"] == pytest.approx(0.3)
    assert macro["hidden_f1"] == pytest.approx(0.55)


def test_two_sided_sign_flip_has_five_block_floor():
    assert exact_sign_flip_pvalue(np.ones(5)) == 0.0625


def test_prefix_mask_uses_source_order():
    record = FormulaRecord(
        "r", "f", "w", "title", {"c": 0.4, "a": 0.3, "b": 0.2, "d": 0.1}
    )
    observed = observed_materials(record, ("a", "b", "c", "d"), 17, 0.5, "prefix")
    assert list(observed) == ["a", "c"]


def test_abundance_mask_is_deterministic():
    record = FormulaRecord(
        "r", "f", "w", "title", {"a": 0.7, "b": 0.2, "c": 0.1}
    )
    first = observed_materials(record, ("a", "b", "c"), 29, 0.5, "abundance")
    second = observed_materials(record, ("a", "b", "c"), 29, 0.5, "abundance")
    assert first == second
