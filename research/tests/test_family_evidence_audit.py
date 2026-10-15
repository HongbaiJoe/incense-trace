from xiangji.normalization.build_family_evidence_audit import connected


def test_connected_accepts_transitive_leakage_group():
    assert connected(["a", "b", "c"], {frozenset(("a", "b")), frozenset(("b", "c"))})


def test_connected_rejects_disconnected_family():
    assert not connected(["a", "b", "c"], {frozenset(("a", "b"))})
