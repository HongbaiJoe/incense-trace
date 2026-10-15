import numpy as np

from xiangji.models.cgir import FEATURE_NAMES, XiangjiCGIR
from xiangji.models.data import FormulaRecord


def synthetic_records():
    records = []
    for index in range(12):
        if index % 2 == 0:
            title = "梅花清香"
            composition = {"agarwood": 0.5, "clove_bud": 0.3, "borneol_family": 0.2}
        else:
            title = "木犀暖香"
            composition = {"sandalwood_white": 0.55, "spikenard": 0.25, "musk": 0.2}
        records.append(FormulaRecord(
            reference_id=f"r-{index}", family_id=f"f-{index}",
            work_id=f"work-{index % 3}", title=title, composition=composition,
        ))
    return records


def test_cgir_returns_probabilities_variable_count_and_simplex_posterior():
    model = XiangjiCGIR(random_seed=17, group_dro_iterations=2).fit(synthetic_records())
    prediction = model.predict(
        title="梅花清香", work_id="unseen-work", observed={"agarwood": 0.5}, posterior_samples=100
    )
    assert prediction["selected_count"] >= 1
    assert prediction["all_inclusion_probabilities"]["agarwood"] == 1.0
    assert prediction["all_inclusion_intervals_80"]["agarwood"] == [1.0, 1.0]
    assert np.isclose(sum(row["posterior_mean_ratio"] for row in prediction["materials"]), 1.0)
    samples = np.asarray(prediction["posterior_samples"])
    assert np.all(samples >= 0)
    assert np.allclose(samples.sum(axis=1), 1.0)
    assert len(model.count_posterior("unseen-work")) == model.maximum_count_


def test_chemistry_channel_is_present_in_fitted_model_and_group_dro_normalizes():
    model = XiangjiCGIR(random_seed=29, group_dro_iterations=2).fit(synthetic_records())
    diagnostics = model.diagnostics()
    assert "chemical_affinity" in diagnostics["enabled_channels"]
    assert set(diagnostics["inclusion_coefficients"]) == set(FEATURE_NAMES)
    assert np.isclose(sum(diagnostics["group_dro_weights"].values()), 1.0)
    assert diagnostics["chemical_material_count"] > 0


def test_zero_group_dro_iterations_fits_erm_model():
    model = XiangjiCGIR(random_seed=37, group_dro_iterations=0).fit(synthetic_records())
    prediction = model.predict(title="梅花清香", observed={"agarwood": 0.5}, posterior_samples=10)
    assert prediction["materials"]


def test_channel_ablation_zeroes_feature_before_scaling():
    enabled = set(FEATURE_NAMES) - {"chemical_affinity", "chemical_odor_similarity"}
    model = XiangjiCGIR(random_seed=43, group_dro_iterations=1, enabled_channels=enabled).fit(synthetic_records())
    assert "chemical_affinity" not in model.diagnostics()["enabled_channels"]


def test_count_posterior_conditions_on_masking_process():
    model = XiangjiCGIR(random_seed=31, group_dro_iterations=1).fit(synthetic_records())
    conditioned = model.count_posterior(
        "unseen-work", observed_count=1, observation_fraction=0.5
    )
    support = np.arange(1, model.maximum_count_ + 1)
    likelihood = np.array([
        float(min(total_count - 1, max(1, round(total_count * 0.5))) == 1)
        for total_count in support
    ])
    expected = model.global_count_distribution_ * likelihood
    expected /= expected.sum()
    assert np.isclose(conditioned.sum(), 1.0)
    assert np.allclose(conditioned, expected)
