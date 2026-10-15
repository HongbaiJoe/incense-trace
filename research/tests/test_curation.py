import pytest

from xiangji.normalization.curation import preflight_record, validate_decision


def test_preflight_flags_do_not_become_adjudication():
    record = {
        "curation_order": 1,
        "candidate_id": "x",
        "formula_family_candidate_id": "f",
        "formula_title_candidate": "測試香",
        "formula_scope_provisional": "burned_incense",
        "raw_wikitext": "測試香\n沉香一兩　麝香一字\n右為末",
        "material_mentions": [
            {"role": "aromatic_material", "entity_id": "agarwood", "identity_status": "family_level", "source_zone": "ingredient_list"},
        ],
        "composition_aromatic_only": {"agarwood": 1.0},
    }
    result = preflight_record(record, 1)
    assert "count_volume_or_qualitative_quantity_present" in result["flags"]
    assert result["automatic_status"] == "preflight_only_not_an_adjudication"


def test_included_decision_requires_all_gates():
    decision = {
        "candidate_id": "x", "boundary_ok": True, "title_ok": True, "materials_ok": True,
        "quantities_ok": True, "roles_ok": True, "scope_ok": True,
        "family_assignment_ok": False, "decision": "included_reference",
        "reviewer": "test", "review_notes": "", "reason_codes": [],
    }
    with pytest.raises(ValueError):
        validate_decision(decision)
