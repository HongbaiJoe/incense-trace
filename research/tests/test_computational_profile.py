from xiangji.evaluation.computational_profile import run


def test_computational_profile_reports_positive_times() -> None:
    result = run(repetitions=3)
    assert result["formula_count"] == 85
    assert result["material_vocabulary_size"] == 80
    assert result["fit_wall_time"]["median_seconds"] > 0
    assert result["single_prediction_wall_time"]["median_seconds"] > 0
