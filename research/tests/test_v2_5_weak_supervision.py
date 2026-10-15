import numpy as np

from xiangji.evaluation.v2_5_weak_supervision import (
    assemble_training,
    load_weak_pool,
)
from xiangji.evaluation.v2_nested_cross_work import load_all_records
from xiangji.models.source_stable_graph import SourceStableGraphCompletion


def test_weak_pool_excludes_gold_and_gold_linked_families():
    gold = load_all_records()
    weak = load_weak_pool()
    assert len(weak) == 146
    assert len({row.record.family_id for row in weak}) == 100
    assert {row.record.reference_id for row in weak}.isdisjoint(
        {row.reference_id for row in gold}
    )
    assert {row.record.family_id for row in weak}.isdisjoint(
        {row.family_id for row in gold}
    )


def test_collection_block_and_inverse_family_weights():
    gold = list(load_all_records())[:10]
    weak = load_weak_pool()
    records, weights, exposure = assemble_training(
        gold, weak, 0.5, {"xiangcheng"}
    )
    assert len(records) == 10 + exposure["active_weak_record_count"]
    assert exposure["forbidden_collections"] == ["xiangcheng"]
    assert all(
        not record.work_id.endswith("xiangcheng") for record in records[len(gold) :]
    )
    assert np.isclose(weights[len(gold) :].sum(), exposure["effective_weak_weight"])


def test_weighted_fit_reduces_to_unweighted_fit_for_unit_weights():
    records = list(load_all_records())[:20]
    ordinary = SourceStableGraphCompletion().fit(records)
    weighted = SourceStableGraphCompletion().fit(records, np.ones(len(records)))
    assert np.allclose(ordinary.prevalence, weighted.prevalence)
    assert np.allclose(ordinary.directed_graph, weighted.directed_graph)
    assert np.allclose(ordinary.source_stable_graph, weighted.source_stable_graph)
