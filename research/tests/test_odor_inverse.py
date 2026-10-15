import numpy as np

from xiangji.data import load_corpus
from xiangji.models.odor_inverse import ForwardConsistentInverse


def test_forward_consistent_inverse_is_nonnegative_and_closed():
    corpus = load_corpus()
    train = corpus.recipes[:20]
    y = np.asarray([corpus.outcome(row) for row in train])
    model = ForwardConsistentInverse(
        tuple(corpus.material_ids), corpus.material_matrix,
        forward_strength=1.0, chemistry_blend=0.5,
    ).fit(train, y)
    prediction = model.predict(corpus.recipes[20:23])
    assert prediction.shape == (3, len(corpus.material_ids))
    assert np.all(prediction >= 0)
    assert np.allclose(prediction.sum(axis=1), 1.0)


def test_zero_forward_strength_reduces_to_nonnegative_ridge_prior():
    corpus = load_corpus()
    train = corpus.recipes[:20]
    y = np.asarray([corpus.outcome(row) for row in train])
    model = ForwardConsistentInverse(
        tuple(corpus.material_ids), corpus.material_matrix,
        forward_strength=0.0, chemistry_blend=1.0,
    ).fit(train, y)
    prediction = model.predict(corpus.recipes[20:21])
    prior = model.prior_model_.predict(corpus.recipes[20:21])
    assert np.allclose(prediction, prior, atol=1e-7)


def test_knn_prior_is_supported():
    corpus = load_corpus()
    train = corpus.recipes[:20]
    y = np.asarray([corpus.outcome(row) for row in train])
    model = ForwardConsistentInverse(
        tuple(corpus.material_ids), corpus.material_matrix,
        forward_strength=0.1, chemistry_blend=0.25, prior_model="odor_knn",
    ).fit(train, y)
    assert np.isclose(model.predict(corpus.recipes[20:21]).sum(), 1.0)
