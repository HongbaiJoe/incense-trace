"""Replay locked V4 configurations with a common gold-vocabulary mask."""
import json
from collections import Counter
from xiangji.data import RESEARCH_ROOT as R
from xiangji.evaluation.v2_nested_cross_work import load_all_records
from xiangji.evaluation.v2_5_weak_supervision import load_weak_pool,assemble_training,work_collection_map
from xiangji.evaluation.v2_benchmark import SEEDS,observed_materials,evaluate_record,aggregate_records
from xiangji.models.source_stable_graph import SourceStableGraphCompletion,SourceStableParameters

def run():
    gold=list(load_all_records());weak=load_weak_pool();collections=work_collection_map()
    original=json.loads((R/'experiments/v2_5_weak_supervision.json').read_text())
    baseline=json.loads((R/'experiments/v2_nested_cross_work.json').read_text())
    rows={k:[] for k in ('directed_graph_gold','directed_graph_weak','sscl_gold','sscl_weak')}
    same=Counter();mask_changed=Counter()
    for fold in original['outer_details']:
        work=fold['outer_test_work'];train=[r for r in gold if r.work_id!=work];test=[r for r in gold if r.work_id==work]
        old=next(x for x in baseline['outer_details'] if x['outer_test_work']==work)
        common=SourceStableGraphCompletion().fit(train).vocabulary
        models={}
        for family in ('directed_graph','sscl'):
            selected=fold['selected_models'][family]
            full,weights,_=assemble_training(train,weak,selected['weak_label_weight'],{collections[work]})
            models[family+'_gold']=SourceStableGraphCompletion(SourceStableParameters(**old['selected_configurations'][family])).fit(train)
            models[family+'_weak']=SourceStableGraphCompletion(SourceStableParameters(**selected['configuration'])).fit(full,weights)
        for seed in SEEDS:
            for r in test:
                if sum(k in common for k in r.composition)<2:continue
                obs=observed_materials(r,common,seed,.5);counts={}
                for name,model in models.items():
                    legacy=observed_materials(r,model.vocabulary,seed,.5)
                    mask_changed[name]+=set(legacy)!=set(obs)
                    prediction=model.predict(obs,observation_fraction=.5);counts[name]=prediction['selected_count']
                    rows[name].append({'reference_id':r.reference_id,'work_id':work,'metrics':evaluate_record(r,obs,prediction)})
                same['queries']+=1;same['same_weak_count']+=counts['directed_graph_weak']==counts['sscl_weak']
    out={'design':'locked-configuration replay; common gold-training-vocabulary masks; no new tuning',
         'legacy_mask_changes':dict(mask_changed),'count_comparison':dict(same),
         'models':{k:aggregate_records(v)[2] for k,v in rows.items()}}
    (R/'experiments/v5_pairing_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':run()
