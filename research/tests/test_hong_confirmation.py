from xiangji.evaluation.hong_confirmation import load_hong_records
from xiangji.models.data import load_development_corpus


def test_hong_confirmation_uses_only_quarantined_registry_records():
    corpus = load_development_corpus()
    records = load_hong_records(corpus)
    assert len(records) == 6
    assert {record.reference_id for record in records} == corpus.sealed_reference_ids
    assert all(record.work_id == corpus.sealed_work_id for record in records)
