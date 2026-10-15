from xiangji.freeze_cycle4 import build_manifest


def test_cycle4_release_records_evaluation_without_model_change():
    manifest = build_manifest()
    assert manifest["model_parameters_changed"] is False
    assert manifest["primary_two_work_folds_accessed"] is True
    assert manifest["Hong_source_accessed_for_confirmation"] is True
    assert manifest["investigator_blinded"] is False
    assert all(len(row["sha256"]) == 64 for row in manifest["files"])
