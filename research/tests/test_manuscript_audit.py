from xiangji.manuscript_audit import audit


def test_manuscript_meets_target_structure_and_numeric_anchors() -> None:
    result = audit()
    assert result["title_word_count"] <= 15
    assert result["abstract_word_count"] <= 150
    assert result["reference_count"] == 38
    assert result["cited_reference_count"] == 38
    assert result["missing_references"] == []
    assert result["uncited_references"] == []
    assert result["duplicate_bib_keys"] == []
    assert result["unresolved_bib_field_count"] == 0
    assert result["missing_sections"] == []
    assert result["discussion_subheadings"] == []
    assert result["cjk_character_count"] == 0
    assert result["missing_numeric_anchors"] == []
