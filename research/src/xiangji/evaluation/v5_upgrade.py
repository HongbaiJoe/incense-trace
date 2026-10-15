"""Reproducible V5 extension; all tuning stays inside each training fold."""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
from collections import Counter
from dataclasses import asdict
import numpy as np
from xiangji.data import RESEARCH_ROOT as R
from xiangji.evaluation.v2_nested_cross_work import load_all_records
from xiangji.evaluation.v2_benchmark import SEEDS, observed_materials, evaluate_record, aggregate_records, paired_work_comparison
from xiangji.models.source_stable_graph import SourceStableGraphCompletion, SourceStableParameters
from xiangji.models.posterior_stable_graph import PosteriorStableGraphCompletion, OperationalGraphCompletion
from xiangji.models.data import load_development_corpus, load_folds


def evaluate(train, test, params, posterior, operational=False):
    cls = PosteriorStableGraphCompletion if posterior else OperationalGraphCompletion if operational else SourceStableGraphCompletion
    model = cls(params).fit(train)
    rows=[]
    for seed in SEEDS:
        for record in test:
            if sum(k in model.index for k in record.composition)<2: continue
            obs=observed_materials(record,model.vocabulary,seed,.5)
            if operational:
                # The input contains ratios among known materials only.
                rel={k:v/sum(obs.values()) for k,v in obs.items()}
                pred=model.predict_partial(rel)
            else:
                pred=model.predict(obs,observation_fraction=.5)
            metrics=evaluate_record(record,obs,pred)
            hidden=set(record.composition)-set(obs)
            predicted={k:v for k,v in pred['composition'].items() if k not in obs}
            true={k:record.composition[k] for k in hidden}
            true_mass=sum(true.values()); pred_mass=sum(predicted.values())
            union=set(true)|set(predicted)
            # Shape on the hidden simplex, separate from total missing mass.
            metrics['hidden_shape_tv']=.5*sum(abs(true.get(k,0)/true_mass-predicted.get(k,0)/pred_mass) for k in union)
            metrics['hidden_mass_absolute_error']=abs(true_mass-pred_mass)
            rows.append({'reference_id':record.reference_id,'work_id':record.work_id,'seed':seed,'metrics':metrics,
                         'observed':obs,'prediction':pred['composition']})
    return rows


def run():
    records=list(load_all_records()); works=sorted({r.work_id for r in records})
    old=json.loads((R/'experiments/v2_nested_cross_work.json').read_text())
    # Deliberately bounded grid; no outer-test performance enters selection.
    grid=[SourceStableParameters(smoothing=a,stable_blend=b,heterogeneity_penalty=g,reducer=r)
          for a in (.5,1.,2.,5.) for b in (0.,.5,1.) for g in (0.,.5) for r in ('mean','max','top2')]
    rows={k:[] for k in ('directed','sscl_v4','posterior','operational')}; selections=[]
    for work in works:
        train=[r for r in records if r.work_id!=work]; test=[r for r in records if r.work_id==work]
        candidates=[]
        for params in grid:
            inner=[]
            for iw in sorted({r.work_id for r in train}):
                inner.extend(evaluate([r for r in train if r.work_id!=iw],[r for r in train if r.work_id==iw],params,True))
            macro=aggregate_records(inner)[2]
            candidates.append((macro['hidden_f1'],macro['weighted_jaccard'],params,macro))
        best=max(candidates,key=lambda c:(c[0],c[1]))
        details=next(d for d in old['outer_details'] if d['outer_test_work']==work)
        for label,key in [('directed','directed_graph'),('sscl_v4','sscl')]:
            p=SourceStableParameters(**details['selected_configurations'][key])
            rows[label].extend(evaluate(train,test,p,False))
        rows['posterior'].extend(evaluate(train,test,best[2],True))
        deployment_params=SourceStableParameters(**details['selected_configurations']['sscl'])
        rows['operational'].extend(evaluate(train,test,deployment_params,False,True))
        selections.append({'work':work,'parameters':asdict(best[2]),'inner_macro':best[3],
                           'grid':[{'parameters':asdict(c[2]),'metrics':c[3]} for c in candidates]})
        print('completed',work,flush=True)
    models={}
    for name, rr in rows.items():
        formulas, wm, macro=aggregate_records(rr)
        models[name]={'evaluated_formulas':len(formulas),'work_metrics':wm,'source_macro_metrics':macro}
    result={'protocol':'nested six-work evaluation; extension exploratory after V4; operational model uses benchmark-selected parameters',
            'grid_size':len(grid),'seeds':list(SEEDS),'models':models,'selections':selections,
            'posterior_vs_directed':paired_work_comparison(models['posterior']['work_metrics'],models['directed']['work_metrics'])}
    (R/'experiments/v5_upgrade.json').write_text(json.dumps(result,indent=2))
    with gzip.open(R/'experiments/v5_predictions.json.gz','wt') as f: json.dump(rows,f)
    print(json.dumps(models,indent=2),flush=True)


def audit():
    corpus=load_development_corpus(); byid=corpus.by_id()
    compact=json.loads((R/'experiments/cycle4_primary_evaluation.json').read_text())
    raw=json.loads(gzip.decompress((R/'experiments/cycle4_primary_records.json.gz').read_bytes()))
    counts=Counter(); recovered=Counter(); instances=0
    folds={f['fold_id']:f for f in load_folds(kind='primary')}
    for run in raw['model_runs'][compact['selected_model']]:
        for fold in run['folds']:
            train=[byid[x] for x in folds[fold['fold_id']]['train_reference_ids']]
            freq=Counter(k for r in train for k in r.composition)
            for row in fold['records']:
                if row.get('status')!='evaluated': continue
                instances+=1
                hidden=set(byid[row['reference_id']].composition)-set(row['observed_materials'])
                pred={x['material_id'] for x in row['uncertainty']['materials']}-set(row['observed_materials'])
                for m in hidden:
                    group='0' if freq[m]==0 else '1' if freq[m]==1 else '2-4' if freq[m]<5 else '5+'
                    counts[group]+=1; recovered[group]+=int(m in pred)
    weak=json.loads((R/'experiments/v2_5_weak_supervision.json').read_text())
    weights=[]
    for fold in weak['outer_details']:
        weights.append({'work':fold['outer_test_work'],**{name:{k:v for k,v in model.items() if k not in ('top_five_inner_configurations','configuration')}
                                                       for name,model in fold['selected_models'].items()}})
    near=json.loads((R/'experiments/cycle6_stress_tests.json').read_text())['near_duplicate_sensitivity']
    full=compact['source_level_metrics']
    out={'development_work_counts':dict(Counter(r.work_id for r in corpus.records)),
         'family_size_definition':'Number of eligible non-gold ratio-ready witnesses in the family, counted before collection blocking; each retained witness has eta/family_size weight.',
         'weak_selections':weights,'rarity':{'evaluation_instances':instances,'opportunities':sum(counts.values()),
                                          'strata':{k:{'total':counts[k],'recovered':recovered[k]} for k in counts}},
         'near_duplicate_exact':near['source_macro_metrics'],
         'full_exact':{m:{metric:float(np.mean([v[metric] for v in works.values()])) for metric in next(iter(works.values())) if isinstance(next(iter(works.values()))[metric],(float,int))} for m,works in full.items()}}
    (R/'reports/v5_data_audit.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    import sys
    audit() if '--audit' in sys.argv else run()
