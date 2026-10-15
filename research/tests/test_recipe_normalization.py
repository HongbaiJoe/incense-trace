from xiangji.normalization.recipes import (
    assign_quantities,
    chinese_number,
    find_materials,
    ingredient_body,
    load_ontology,
    make_parser_text,
    method_tail,
    note_quantity_projection,
    normalize_quantity,
    structure_candidate,
)


def test_chinese_number_and_mass_conversion():
    assert chinese_number("十") == 10
    assert chinese_number("十二") == 12
    assert chinese_number("廿") == 20
    assert normalize_quantity("半觔")["value_qian"] == 80
    assert normalize_quantity("一兩半")["value_qian"] == 15
    assert normalize_quantity("七錢五分")["value_qian"] == 7.5
    assert normalize_quantity("十餘粒")["basis"] == "non_mass"
    assert normalize_quantity("十餘兩")["basis"] == "approximate_mass"


def test_group_quantity_assignment_and_longest_alias():
    entities, aliases = load_ontology()
    text = "白檀香　零陵香　藿香葉已上各一兩　麝香五分"
    mentions = find_materials(text, aliases)
    assign_quantities(text, mentions)
    by_id = {mention["entity_id"]: mention for mention in mentions}
    assert set(by_id) == {"sandalwood_white", "linglingxiang", "patchouli", "musk"}
    assert by_id["sandalwood_white"]["quantity"]["value_qian"] == 10
    assert by_id["linglingxiang"]["quantity"]["value_qian"] == 10
    assert by_id["patchouli"]["quantity"]["value_qian"] == 10
    assert by_id["musk"]["quantity"]["value_qian"] == 0.5


def test_compound_mention_expands_to_two_entities():
    _, aliases = load_ontology()
    mentions = find_materials("龍麝各一錢", aliases)
    assign_quantities("龍麝各一錢", mentions)
    assert {mention["entity_id"] for mention in mentions} == {"borneol_family", "musk"}
    assert all(mention["quantity"]["value_qian"] == 1 for mention in mentions)


def test_process_material_inside_note_is_not_parsed_as_component():
    _, aliases = load_ontology()
    raw = "{{SK anchor|白檀}}{{SK notes|五兩細剉以臘茶清浸半月後用蜜炒}}沉香{{SK notes|四兩}}"
    parser_text = make_parser_text(raw)
    mentions = find_materials(parser_text, aliases)
    assert {mention["entity_id"] for mention in mentions} == {"sandalwood_white", "agarwood"}
    assert "蜜炒" not in parser_text


def test_note_projection_does_not_steal_processing_reagent_quantity():
    _, aliases = load_ontology()
    parser_text = make_parser_text("丁香{{SK notes|臘茶半錢同煑半日}}　麝香一錢")
    mentions = find_materials(parser_text, aliases)
    assign_quantities(parser_text, mentions)
    by_id = {row["entity_id"]: row for row in mentions}
    assert by_id["clove_bud"]["quantity"] is None
    assert by_id["musk"]["quantity"]["value_qian"] == 1


def test_note_projection_retains_group_quantity_backreference():
    assert note_quantity_projection("細研同麝香入上三味各二錢") == "各二錢"


def test_note_material_addition_is_parsed_separately():
    entities, aliases = load_ontology()
    record = {
        "candidate_id": "synthetic-note-addition",
        "raw_wikitext": "測試香\n箋香{{SK notes|二十兩加速香三兩}}　麝香一錢\n右為末",
    }
    structured = structure_candidate(record, entities, aliases)
    additions = [
        row for row in structured["material_mentions"]
        if row["source_zone"] == "note_quantified_addition"
    ]
    assert [(row["entity_id"], row["quantity"]["value_qian"]) for row in additions] == [
        ("agarwood_soku_grade", 30.0)
    ]


def test_count_quantity_prevents_later_group_quantity_from_overwriting_material():
    _, aliases = load_ontology()
    text = "丁香十餘粒　龍腦麝香各一錢"
    mentions = find_materials(text, aliases)
    assign_quantities(text, mentions)
    by_id = {row["entity_id"]: row for row in mentions}
    assert by_id["clove_bud"]["quantity"]["basis"] == "non_mass"
    assert by_id["borneol_family"]["quantity"]["value_qian"] == 1
    assert by_id["musk"]["quantity"]["value_qian"] == 1


def test_contextually_resolved_skchar_is_available_to_material_parser():
    _, aliases = load_ontology()
    parser_text = make_parser_text("{{SKchar|202}}香一兩　白荳{{SKchar|3587}}仁二錢　{{SKchar|999999}}")
    assert parser_text == "箋香一兩　白荳蔻仁二錢　□"
    assert {row["entity_id"] for row in find_materials(parser_text, aliases)} == {
        "agarwood_zhan_grade", "cardamom"
    }


def test_longer_unresolved_term_blocks_false_musk_substring():
    _, aliases = load_ontology()
    mentions = find_materials("木麝二兩", aliases)
    assert [mention["entity_id"] for mention in mentions] == ["wood_musk_unresolved"]


def test_ingredients_before_inline_method_are_retained():
    lines = ["測試香", "沉香一兩", "甲香半兩　龍腦一錢　右為細末"]
    body = ingredient_body(lines)
    assert "甲香半兩" in body
    assert "龍腦一錢" in body
    assert "右為細末" not in body


def test_quantified_aromatics_in_method_tail_are_retained_with_zone_provenance():
    entities, aliases = load_ontology()
    record = {
        "candidate_id": "synthetic-method-addition",
        "raw_wikitext": "芬積香\n沉香一兩　箋香一兩\n右為細末入龍腦麝香各二錢拌勻",
    }
    structured = structure_candidate(record, entities, aliases)
    additions = [
        row for row in structured["material_mentions"]
        if row["source_zone"] == "method_quantified_addition"
    ]
    assert {row["entity_id"] for row in additions} == {"borneol_family", "musk"}
    assert all(row["quantity"]["value_qian"] == 2 for row in additions)
    assert structured["method_quantified_addition_count"] == 2
    assert structured["ratio_ready_automatic"] is True


def test_method_tail_excludes_unquantified_repeated_materials():
    entities, aliases = load_ontology()
    record = {
        "candidate_id": "synthetic-method-repeat",
        "raw_wikitext": "測試香\n沉香一兩　麝香一錢\n右除麝香另研，用炭末二十兩和勻",
    }
    structured = structure_candidate(record, entities, aliases)
    musk = [row for row in structured["material_mentions"] if row["entity_id"] == "musk"]
    assert len(musk) == 1
    assert musk[0]["source_zone"] == "ingredient_list"
    assert method_tail(record["raw_wikitext"].splitlines()).startswith("右除麝香")


def test_collective_compound_without_each_stays_ambiguous():
    _, aliases = load_ontology()
    text = "沉速五斤　檀香一斤"
    mentions = find_materials(text, aliases)
    assign_quantities(text, mentions)
    compound = [mention for mention in mentions if mention["start"] == 0]
    assert len(compound) == 2
    assert all(mention["quantity"]["basis"] == "collective_ambiguous" for mention in compound)
    sandalwood = [mention for mention in mentions if mention["entity_id"] == "sandalwood_white"][0]
    assert sandalwood["quantity"]["value_qian"] == 160


def test_ctext_method_paragraph_is_excluded_but_ingredient_prefix_is_kept():
    assert ingredient_body(["玉華香方", "沉香四兩", "上以香料為末，和入合油，燒用二分"]) == "沉香四兩"
    body = ingredient_body(["聚仙香方", "沉香四兩", "檀香二斤　排草八兩為末，作第二層"])
    assert "檀香二斤" in body
    assert "為末" not in body
