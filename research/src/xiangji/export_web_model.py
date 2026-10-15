"""Export fitted graph and test fixtures; the browser performs inference only."""
import json
import hashlib
import sys
from pathlib import Path
from dataclasses import asdict
from collections import Counter
from xiangji.data import RESEARCH_ROOT as R
from xiangji.evaluation.v2_nested_cross_work import load_all_records, select_inside_outer_fold
from xiangji.evaluation.v2_benchmark import parameter_grids
from xiangji.models.posterior_stable_graph import OperationalGraphCompletion

def run(destination):
    records=list(load_all_records())
    p,candidates=select_inside_outer_fold('sscl',parameter_grids()['sscl'],records)
    model=OperationalGraphCompletion(p).fit(records)
    source=json.loads((R/'data/curated/formula_reference_v0.1.json').read_text())
    names={}
    for row in source['records']:
        for mention in row.get('material_mentions',[]):
            names.setdefault(mention['entity_id'],mention['surface'])
    out={'version':'xiangji-v5-20260929','parameters':asdict(p),'vocabulary':model.vocabulary,
         'names':{k:names.get(k,k) for k in model.vocabulary},'graph':model.source_stable_graph.tolist(),
         'prevalence':model.prevalence.tolist(),'compositions':model.compositions.tolist(),
         'records':[{'id':r.reference_id,'title':r.title,'work':r.work_id,'composition':r.composition} for r in records],
         'count_histogram':dict(Counter(map(str,model.formula_counts))),
         'source_sha256':hashlib.sha256((R/'data/curated/formula_reference_v0.1.json').read_bytes()).hexdigest(),
         'training_selection':candidates[0]}
    fixtures=[]
    for r in records[:8]:
        obs=dict(list(r.composition.items())[:2]); total=sum(obs.values()); obs={k:v/total for k,v in obs.items()}
        fixtures.append({'observed':obs,'expected':model.predict_partial(obs)})
    dest=Path(destination); dest.mkdir(parents=True,exist_ok=True)
    (dest/'research-model.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
    (dest/'model-fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False))
    public=[]
    for row in source['records']:
        public.append({'id':row['reference_id'],'title':row['formula_title_verbatim'],'work':row['work_id'],
                       'composition':row['composition_aromatic_only'],'source':row['source'],'text':row['raw_wikitext']})
    (dest/'research-formulas.json').write_text(json.dumps(public,ensure_ascii=False,separators=(',',':')))
    (R/'experiments/v5_deployment_selection.json').write_text(json.dumps({'parameters':asdict(p),'inner_cv':candidates[0]},indent=2))
    print('Exported',len(model.vocabulary),'materials and',len(records),'formulas to',dest)

if __name__=='__main__': run(sys.argv[1])
