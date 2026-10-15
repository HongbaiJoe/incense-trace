import json

from xiangji.data import RESEARCH_ROOT


def test_generated_curation_batch_is_family_unique_and_pending():
    path = RESEARCH_ROOT / "data" / "interim" / "formula_curation_batch_v0.1.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text())
    records = payload["records"]
    assert len(records) == payload["target_size"] == 120
    assert len({record["formula_family_candidate_id"] for record in records}) == 120
    assert all(record["review"]["adjudication_status"] == "pending" for record in records)
