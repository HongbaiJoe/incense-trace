from xiangji.evaluation.model_selection import selection_key


def test_selection_key_uses_registered_lexicographic_order():
    left = {"mean_metrics": {
        "hidden_f1": 0.5, "weighted_jaccard": 0.4, "aitchison_distance": 3.0,
    }}
    right = {"mean_metrics": {
        "hidden_f1": 0.5, "weighted_jaccard": 0.4, "aitchison_distance": 4.0,
    }}
    assert selection_key(left) > selection_key(right)
