import numpy as np

from xiangji.representations.kernels import affinity_from_observed, build_chemical_kernel, hypergraph_kernel


def test_hypergraph_kernel_is_conditional_and_training_only_shape():
    compositions = np.array([[0.5, 0.5, 0.0], [0.4, 0.0, 0.6]])
    kernel = hypergraph_kernel(compositions)
    assert kernel.shape == (3, 3)
    assert np.allclose(np.diag(kernel), 1.0)
    assert np.all((kernel >= 0) & (kernel <= 1))


def test_affinity_is_weighted_by_observed_composition():
    kernel = np.eye(3)
    affinity = affinity_from_observed(kernel, np.array([3.0, 1.0, 0.0]))
    assert np.allclose(affinity, [0.75, 0.25, 0.0])


def test_affinity_reducers_are_explicit():
    kernel = np.array([[1.0, 0.2, 0.4], [0.1, 1.0, 0.8], [0.0, 0.0, 1.0]])
    observed = np.array([3.0, 1.0, 0.0])
    assert np.allclose(affinity_from_observed(kernel, observed, "mean"), [0.55, 0.6, 0.6])
    assert np.allclose(affinity_from_observed(kernel, observed, "max"), [1.0, 1.0, 0.8])


def test_chemical_kernel_marks_evidence_and_explicit_grade_proxies():
    vocabulary = ("agarwood", "agarwood_zhan_grade", "musk", "unknown")
    kernel, available, proxies = build_chemical_kernel(
        vocabulary, proxy_map={"agarwood_zhan_grade": "agarwood"}
    )
    assert available.tolist() == [True, True, True, False]
    assert proxies == {"agarwood_zhan_grade": "agarwood"}
    assert kernel[0, 1] == 1.0
    assert np.all(kernel[3] == 0.0)
