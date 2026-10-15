import numpy as np

from xiangji.representations.odor import ODOR_DIMENSIONS, build_odor_views


def test_odor_views_keep_legacy_and_chemical_channels_separate():
    views = build_odor_views(
        ("agarwood", "agarwood_zhan_grade", "musk", "unknown"),
        proxy_map={"agarwood_zhan_grade": "agarwood"},
    )
    assert views.legacy_available.tolist() == [True, True, True, False]
    assert views.chemical_available.tolist() == [True, True, True, False]
    assert views.proxy_used == {"agarwood_zhan_grade": "agarwood"}
    legacy, chemical = views.similarities(np.ones(len(ODOR_DIMENSIONS)))
    assert legacy.shape == chemical.shape == (4,)
    assert legacy[-1] == chemical[-1] == 0.0


def test_legacy_identifier_vocabulary_maps_without_losing_vectors():
    views = build_odor_views(("sandalwood", "clove", "rose"))
    assert views.legacy_available.tolist() == [True, True, True]
    assert np.all(views.legacy_vectors.sum(axis=1) > 0)
