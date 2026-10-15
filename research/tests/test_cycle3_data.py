import numpy as np

from xiangji.models.data import (
    FormulaRecord,
    build_vocabulary,
    composition_matrix,
    deterministic_observation_mask,
    load_development_corpus,
    load_folds,
)


def test_development_loader_removes_sealed_source_before_model_view():
    corpus = load_development_corpus()
    assert len(corpus.records) == 85
    assert all(record.work_id != corpus.sealed_work_id for record in corpus.records)
    assert all(record.reference_id not in corpus.sealed_reference_ids for record in corpus.records)
    assert len(load_folds()) == 10


def test_vocabulary_and_composition_matrix_are_training_record_derived():
    records = [
        FormulaRecord("a", "fa", "wa", "甲", {"x": 0.75, "y": 0.25}),
        FormulaRecord("b", "fb", "wb", "乙", {"y": 1.0}),
    ]
    vocabulary = build_vocabulary(records)
    assert vocabulary == ("y", "x")
    matrix = composition_matrix(records, vocabulary)
    assert np.allclose(matrix.sum(axis=1), 1.0)


def test_mask_is_deterministic_nonempty_and_hides_at_least_one_component():
    record = FormulaRecord("a", "fa", "wa", "甲", {"x": 0.5, "y": 0.3, "z": 0.2})
    vocabulary = ("x", "y", "z", "q")
    left = deterministic_observation_mask(record, vocabulary, 0.5, 17)
    right = deterministic_observation_mask(record, vocabulary, 0.5, 17)
    assert np.array_equal(left, right)
    assert 1 <= left.sum() < 3
    assert not left[3]
