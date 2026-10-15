from xiangji.freeze_cycle3 import FILES, build_manifest


def test_cycle3_release_is_locked_before_primary_evaluation():
    manifest = build_manifest()
    assert len(manifest["files"]) == len(FILES)
    assert manifest["development_gate_passed"] is True
    assert manifest["primary_two_work_folds_accessed"] is False
    assert manifest["quarantined_source_accessed_by_model"] is False
    assert manifest["investigator_blinded"] is False
    assert all(len(row["sha256"]) == 64 for row in manifest["files"])
