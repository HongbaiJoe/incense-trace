from xiangji.normalization.genealogy import normalize_title, should_link


def test_title_normalization_handles_known_witness_variants():
    assert normalize_title("唐化度寺牙香法") == normalize_title("唐化度寺衙香")
    assert normalize_title("清逺香新方") == normalize_title("清遠香")
    assert normalize_title("撒䭱蘭香方") == normalize_title("撒馥兰香")


def test_generic_titles_need_stronger_text_match():
    left = {"formula_title_candidate": "又方", "witness_id": "a"}
    right = {"formula_title_candidate": "又方", "witness_id": "b"}
    assert should_link(left, right, 0.40) == (False, None)
    assert should_link(left, right, 0.60)[0]


def test_same_title_without_material_overlap_is_not_enough():
    left = {
        "formula_title_candidate": "宣和御製香", "witness_id": "a",
        "composition_aromatic_only": {"agarwood": 1.0},
    }
    right = {
        "formula_title_candidate": "宣和御製香", "witness_id": "b",
        "composition_aromatic_only": {"sandalwood_white": 1.0},
    }
    assert should_link(left, right, 0.35) == (False, None)


def test_cross_witness_composition_view_links_near_duplicate_formula():
    left = {
        "formula_title_candidate": "龍腦印香",
        "witness_id": "a",
        "composition_aromatic_only": {"agarwood": 0.4, "sandalwood_white": 0.3, "clove_bud": 0.2, "musk": 0.1},
    }
    right = {
        "formula_title_candidate": "龍麝印香",
        "witness_id": "b",
        "composition_aromatic_only": {"agarwood": 0.39, "sandalwood_white": 0.31, "clove_bud": 0.2, "musk": 0.1},
    }
    assert should_link(left, right, 0.20) == (True, "cross_witness_composition_similarity")
