import json

import pytest

from xiangji.data import RESEARCH_ROOT
from xiangji.normalization.build_curated_reference import (
    GATE_KEYS,
    aromatic_mass_vector,
    build_decisions,
    close_composition,
    materialize,
)


def minimal_record(candidate_id="a", family_id="f-a"):
    return {
        "curation_order": 1,
        "candidate_id": candidate_id,
        "formula_family_candidate_id": family_id,
        "work_id_provisional": "work-a",
        "collection": "test",
        "page_title": "page",
        "stable_revision_url": "https://example.test/revision",
        "locator_start": 1,
        "locator_end": 2,
        "formula_title_candidate": "測試香",
        "raw_wikitext": "沉香一兩 檀香二兩",
        "material_mentions": [
            {"surface": "沉香", "entity_id": "agarwood", "role": "aromatic_material", "quantity": {"basis": "mass_qian", "value_qian": 10.0}},
            {"surface": "檀香", "entity_id": "sandalwood", "role": "aromatic_material", "quantity": {"basis": "mass_qian", "value_qian": 20.0}},
            {"surface": "蜜", "entity_id": "honey", "role": "binder", "quantity": {"basis": "mass_qian", "value_qian": 4.0}},
        ],
        "composition_aromatic_only": {"agarwood": 1 / 3, "sandalwood": 2 / 3},
    }


def minimal_manifest():
    return {
        "batch_sha256": "test",
        "review_date": "2026-09-07",
        "reviewer": "test",
        "review_mode": "test",
        "default_review_notes": "checked",
        "exclusions": {},
    }


def test_aromatic_vector_excludes_non_aromatic_roles():
    masses = aromatic_mass_vector(minimal_record())
    assert masses == {"agarwood": 10.0, "sandalwood": 20.0}
    assert close_composition(masses) == pytest.approx({"agarwood": 1 / 3, "sandalwood": 2 / 3})


def test_manifest_exclusion_fails_named_gate_and_retains_reason():
    record = minimal_record()
    manifest = minimal_manifest()
    manifest["exclusions"] = {
        "a": {
            "curation_order": 1,
            "expected_title": "測試香",
            "failed_gates": ["quantities_ok"],
            "reason_codes": ["unquantified_aromatic"],
            "review_notes": "missing quantity",
        }
    }
    decision = build_decisions({"records": [record]}, manifest)[0]
    assert decision["decision"] == "excluded_reference"
    assert decision["quantities_ok"] is False
    assert decision["reason_codes"] == ["unquantified_aromatic"]


def test_release_hold_excludes_record_without_inventing_failed_scientific_gate():
    record = minimal_record()
    manifest = minimal_manifest()
    manifest["exclusions"] = {
        "a": {
            "curation_order": 1,
            "expected_title": "測試香",
            "failed_gates": [],
            "release_ok": False,
            "reason_codes": ["source_redistribution_hold"],
            "review_notes": "rights check pending",
        }
    }
    decision = build_decisions({"records": [record]}, manifest)[0]
    assert all(decision[key] is True for key in GATE_KEYS)
    assert decision["release_ok"] is False
    assert decision["decision"] == "excluded_reference"


def test_materialize_rejects_under_80_records():
    with pytest.raises(ValueError, match="minimum is 80"):
        materialize({"records": [minimal_record()]}, minimal_manifest())


def test_generated_reference_meets_release_invariants():
    path = RESEARCH_ROOT / "data" / "curated" / "formula_reference_v0.1.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload["records"]
    assert payload["record_count"] >= 80
    assert payload["work_count"] >= 5
    assert len({row["formula_family_id"] for row in records}) == len(records)
    assert all(abs(sum(row["composition_aromatic_only"].values()) - 1.0) < 1e-10 for row in records)
    assert all(all(row["curation"][key] is True for key in GATE_KEYS) for row in records)
    assert all(row["curation"]["release_ok"] is True for row in records)
