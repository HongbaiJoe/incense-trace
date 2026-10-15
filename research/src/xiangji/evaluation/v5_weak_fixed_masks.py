"""Full nested weak-supervision rerun with masks fixed by gold training only."""
import json
import numpy as np
from xiangji.data import RESEARCH_ROOT as R
from xiangji.evaluation import v2_5_weak_supervision as old
from xiangji.evaluation.v2_benchmark import observed_materials,evaluate_record
from xiangji.models.data import build_vocabulary
from xiangji.models.source_stable_graph import SourceStableGraphCompletion

def evaluate_split(parameters,gold_training,test,weak,weak_label_weight,forbidden_collections):
    training,weights,exposure=old.assemble_training(gold_training,weak,weak_label_weight,forbidden_collections)
    model=SourceStableGraphCompletion(parameters).fit(training,weights)
    common=build_vocabulary(gold_training)
    rows=[]
    for seed in old.SEEDS:
        for record in test:
            if sum(k in common for k in record.composition)<2:continue
            obs=observed_materials(record,common,seed,.5)
            pred=model.predict(obs,observation_fraction=.5)
            rows.append({'seed':seed,'reference_id':record.reference_id,'work_id':record.work_id,'metrics':evaluate_record(record,obs,pred)})
    return rows,exposure

if __name__=='__main__':
    old.evaluate_split=evaluate_split
    original=old.select_inside_outer_fold
    def progress(*args,**kwargs):
        answer=original(*args,**kwargs);print('selected',args[0][0].method,'outer collection',args[3],flush=True);return answer
    old.select_inside_outer_fold=progress
    result=old.run();result['design']='nested_leave_one_work_out_collection_blocked_weak_supervision_common_gold_vocabulary_masks'
    (R/'experiments/v5_weak_fixed_masks.json').write_text(json.dumps(result,indent=2))
    print({k:v['source_macro_metrics'] for k,v in result['models'].items()},flush=True)
