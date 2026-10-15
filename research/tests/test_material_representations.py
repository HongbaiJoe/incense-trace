import json

import pytest

from xiangji.data import RESEARCH_ROOT
from xiangji.representations.build_material_representations import conditional_weights


def test_conditional_weights_normalize_numeric_midpoints():
    components = [
        {"compound_id": "a", "measurement": {"unit": "percent_peak_area", "min": 10, "max": 20}},
        {"compound_id": "b", "measurement": {"unit": "percent_peak_area", "min": 20, "max": 40}},
    ]
    weights, basis = conditional_weights(components)
    assert weights == pytest.approx({"a": 1 / 3, "b": 2 / 3})
    assert basis == "midpoint_normalized_within_reported_percent_peak_area"


def test_presence_only_weights_are_uniform_and_explicit():
    components = [
        {"compound_id": "a", "measurement": None},
        {"compound_id": "b", "measurement": None},
    ]
    weights, basis = conditional_weights(components)
    assert weights == {"a": 0.5, "b": 0.5}
    assert basis == "uniform_over_presence_only_compounds"


def test_incompatible_assays_are_not_silently_pooled():
    components = [
        {"compound_id": "a", "measurement": {"unit": "percent_peak_area", "min": 10, "max": 10}},
        {"compound_id": "b", "measurement": {"unit": "concentration_ng_g", "min": 10, "max": 10}},
    ]
    with pytest.raises(ValueError, match="cannot mix"):
        conditional_weights(components)


def test_generated_material_views_preserve_profile_context():
    path = RESEARCH_ROOT / "data" / "processed" / "material_representations_v0.1.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["profile_count"] == 18
    assert set(payload["views"]) == {"odor_tag_view", "compound_set_molecular_view", "physicochemical_view"}
    assert all(row["context"]["source_locator"] for row in payload["profiles"])
