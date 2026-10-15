import numpy as np

from xiangji.evaluation.v2_calibration import (
    adaptive_calibration_error,
    logit_calibrate,
    temperature_scale,
)


def test_adaptive_calibration_error_is_zero_for_exact_bins():
    probability = np.asarray([0.0, 0.0, 1.0, 1.0])
    label = np.asarray([0, 0, 1, 1])
    assert adaptive_calibration_error(probability, label, bins=2) == 0.0


def test_temperature_one_is_identity():
    probability = np.asarray([0.1, 0.5, 0.9])
    assert np.allclose(temperature_scale(probability, 1.0), probability)


def test_larger_temperature_moves_probabilities_toward_half():
    probability = np.asarray([0.1, 0.9])
    scaled = temperature_scale(probability, 2.0)
    assert scaled[0] > probability[0]
    assert scaled[1] < probability[1]


def test_identity_logit_calibrator_preserves_probabilities():
    probability = np.asarray([0.1, 0.5, 0.9])
    assert np.allclose(logit_calibrate(probability, 1.0, 0.0), probability)
