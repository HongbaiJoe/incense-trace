from xiangji.evaluation.v2_nested_cross_work import load_all_records


def test_all_six_work_groups_are_loaded_for_nested_evaluation():
    records = load_all_records()
    assert len(records) == 91
    assert len({record.work_id for record in records}) == 6


def test_every_outer_split_has_disjoint_work_groups():
    records = load_all_records()
    for work in {record.work_id for record in records}:
        training = [record for record in records if record.work_id != work]
        test = [record for record in records if record.work_id == work]
        assert {record.work_id for record in training}.isdisjoint(
            {record.work_id for record in test}
        )

