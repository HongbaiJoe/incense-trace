import numpy as np

from xiangji.models.data import FormulaRecord
from xiangji.models.source_stable_graph import (
    SourceStableGraphCompletion,
    SourceStableParameters,
)


def _records():
    return [
        FormulaRecord("a1", "f1", "A", "one", {"x": 0.6, "y": 0.4}),
        FormulaRecord("a2", "f2", "A", "two", {"x": 0.5, "z": 0.5}),
        FormulaRecord("b1", "f3", "B", "three", {"x": 0.7, "y": 0.3}),
        FormulaRecord("b2", "f4", "B", "four", {"w": 0.5, "z": 0.5}),
    ]


def test_source_stable_edges_are_finite_asymmetric_and_bounded():
    model = SourceStableGraphCompletion().fit(_records())
    assert np.isfinite(model.source_stable_graph).all()
    assert ((model.source_stable_graph >= 0) & (model.source_stable_graph <= 1)).all()
    x, y = model.index["x"], model.index["y"]
    assert model.source_stable_graph[x, y] != model.source_stable_graph[y, x]


def test_prediction_forces_observed_material_and_closes_composition():
    model = SourceStableGraphCompletion().fit(_records())
    prediction = model.predict({"x": 0.6}, observation_fraction=0.5)
    assert "x" in prediction["selected_materials"]
    assert abs(sum(prediction["composition"].values()) - 1.0) < 1e-12
    assert prediction["composition"]["x"] == 0.6


def test_ease_has_zero_diagonal():
    parameters = SourceStableParameters(method="ease", ease_ridge=10.0)
    model = SourceStableGraphCompletion(parameters).fit(_records())
    assert np.allclose(np.diag(model.comparator_matrix), 0.0)


def test_unknown_fraction_count_distribution_is_valid():
    model = SourceStableGraphCompletion().fit(_records())
    support, probability = model.count_distribution(1, None)
    assert np.isclose(probability.sum(), 1.0)
    assert probability[support <= 1].sum() == 0.0


def test_heterogeneity_penalty_cannot_raise_a_stable_edge():
    unpenalized = SourceStableGraphCompletion(
        SourceStableParameters(heterogeneity_penalty=0.0, stable_blend=1.0)
    ).fit(_records())
    penalized = SourceStableGraphCompletion(
        SourceStableParameters(heterogeneity_penalty=1.0, stable_blend=1.0)
    ).fit(_records())
    assert np.all(
        penalized.source_stable_graph <= unpenalized.source_stable_graph + 1e-12
    )
