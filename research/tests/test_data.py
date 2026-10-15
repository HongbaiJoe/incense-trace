from xiangji.data import historical_hash_split, leave_one_family_out, load_corpus


def test_corpus_shape_and_normalization():
    corpus = load_corpus()
    assert len(corpus.recipes) == 44
    assert len(corpus.materials) == 25
    assert len(corpus.dimensions) == 12
    for recipe in corpus.recipes:
        assert abs(corpus.outcome(recipe).sum() - 1.0) < 1e-10


def test_legacy_hash_split_is_frozen():
    corpus = load_corpus()
    train, test = historical_hash_split(corpus.recipes)
    assert len(train) == 33
    assert len(test) == 11
    assert not set(train) & set(test)


def test_family_folds_cover_every_recipe_once():
    corpus = load_corpus()
    folds = leave_one_family_out(corpus.recipes)
    assert len(folds) == 5
    held_out = [index for _, _, test in folds for index in test]
    assert sorted(held_out) == list(range(44))
    for family, train, test in folds:
        assert all(corpus.recipes[i]["family"] == family for i in test)
        assert all(corpus.recipes[i]["family"] != family for i in train)
