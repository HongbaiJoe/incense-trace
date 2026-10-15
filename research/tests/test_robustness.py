from xiangji.evaluation.robustness import count_stratum, frequency_stratum


def test_frequency_strata_cover_oov_singleton_rare_and_common():
    assert [frequency_stratum(value) for value in (0, 1, 2, 4, 5)] == [
        "out_of_vocabulary", "singleton", "rare_2_to_4", "rare_2_to_4", "common_5_plus"
    ]


def test_count_strata_are_disjoint():
    assert [count_stratum(value) for value in (2, 4, 5, 7, 8, 12)] == [
        "2_to_4", "2_to_4", "5_to_7", "5_to_7", "8_plus", "8_plus"
    ]
