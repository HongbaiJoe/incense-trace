"""Replace V4 weak-supervision results with the common-mask nested rerun."""
import json,re,itertools
import numpy as np
from pathlib import Path

def interval(d,alpha=.1):
    d=np.asarray(d); s=np.array(list(itertools.product((-1,1),repeat=len(d))))
    # Breakpoints of |s·(d-theta)| = |1·(d-theta)|.
    points=[]
    for row in s:
        for sign in (-1,1):
            a=row.sum()-sign*len(d)
            if a:points.append(float((row@d-sign*d.sum())/a))
    points=sorted(set(points)); accepted=[]
    def p(t):return np.mean(np.abs(s@(d-t))>=abs((d-t).sum())-1e-12)
    for a,b in zip(points,points[1:]):
        if p((a+b)/2)>alpha:accepted.extend((a,b))
    accepted.extend(t for t in points if p(t)>alpha)
    return [min(accepted),max(accepted)]

def reconcile(text,research):
    data=json.loads((research/'experiments/v5_weak_fixed_masks.json').read_text())
    comp=data['comparisons_vs_gold_only_same_model']['sscl'];ci=interval(list(comp['per_work_difference'].values()))
    text=text.replace('Weak records lowered count error from 1.145 to 1.089 without changing F1, and nested calibration cut', 'Weak-record augmentation left count error unchanged at 1.145 and reduced SSCL F1 to 0.407; nested calibration cut')
    text=text.replace('Weak records improve the prediction of formula size but not the identification of ingredients.', 'Weak-record augmentation leaves size error unchanged and reduces SSCL ingredient recovery on the matched queries.')
    text=text.replace('Weak Records Improve Size Prediction, Not Ingredient Identification','Weak Records under Matched Observation Masks')
    text=text.replace('The work-averaged change is $-0.0009$ (exact sign-flip $p=1.0$).','The work-averaged change is $-0.0197$ (exact sign-flip $p=0.5$); masks are identical across training-evidence conditions.')
    start=text.index('\\draw[clgray,line width=1pt] (axis cs:0.4199,6)');end=text.index('\\legend{Gold only,Gold + weak}',start)
    work=list(data['models']['sscl']['work_metrics']); gold=[];weak=[];segments=[]
    for w,y in zip(work,range(6,0,-1)):
        b=data['models']['sscl']['work_metrics'][w]['hidden_f1'];a=b-comp['per_work_difference'][w]
        gold.append(f'({a:.8f},{y})');weak.append(f'({b:.8f},{y})');segments.append(f'(axis cs:{a:.8f},{y})--(axis cs:{b:.8f},{y})')
    text=text[:start]+r'\draw[clgray,line width=1pt] '+' '.join(segments)+';\n'+r'\addplot[only marks,mark=o,mark size=2.2pt,draw=cochre,line width=0.9pt] coordinates {'+' '.join(gold)+'};\n'+r'\addplot[only marks,mark=*,mark size=1.5pt,color=cteal] coordinates {'+' '.join(weak)+'};\n'+text[end:]
    text=text.replace('xmin=0.25, xmax=0.62','xmin=0.15, xmax=0.62')
    text=re.sub(r'SSCL weak \$-\$ SSCL gold &[^\n]+',lambda _: f'SSCL weak $-$ SSCL gold & $-$0.020 & --- & 2/2/2 & 0.500 & [{ci[0]:.3f}, {ci[1]:.3f}] & --- '+r'\\',text)
    paragraph='Depending on which collection was blocked'
    start=text.index(paragraph);end=text.index('\n\n',start)
    text=text[:start]+r'Depending on which collection was blocked, an outer fold admitted 62 to 142 weak records (Table~\ref{tab:weakfolds}). Inner validation selected a positive SSCL weight in five of six folds. Effective weak mass ranged from zero in Liexiang to 98.67 formula units in Hong. The family denominator is fixed before collection blocking: it counts all eligible, ratio-ready weak witnesses in the family after gold families have been removed. A family with blocked witnesses therefore contributes only its admissible fraction of the budget.'+text[end:]
    start=text.index('Chen & 53 & 88');end=text.index('\\bottomrule',start)
    rows=[]
    for fold,name in zip(data['outer_details'],['Chen','Hong','Huizhai','Liexiang','Xiaolu','Xiangcheng']):
        m=fold['selected_models']['sscl'];e=m['outer_training_exposure'];rows.append(f"{name} & {e['gold_formula_count']} & {e['eligible_weak_record_count']} & {m['weak_label_weight']:.2f} & {e['effective_weak_weight']:.2f} "+r'\\')
    text=text[:start]+'\n'.join(rows)+'\n'+text[end:]
    start=text.index('Adding weak records left');end=text.index('\n\n',start)
    text=text[:start]+r'Under identical masks, weak-record augmentation changes directed-graph F1 from 0.4260 to 0.4258 and SSCL F1 from 0.4263 to 0.4065 (Table~\ref{tab:weak}). For SSCL, the largest decrease occurs in Huizhai ($-0.1013$), followed by Hong ($-0.0267$); Chen and Xiangcheng improve by about 0.005, while Liexiang and Xiaolu tie. The work-mean difference is $-0.0197$ with sign-flip $p=0.5$. Both systems retain count MAE 1.1447. Their selected weak weights differ, but the size posterior produces the same count decisions on these queries. A larger weighted sample can alter a histogram without changing its posterior mode.'+text[end:]
    for key,label in [('directed_graph','Directed graph'),('sscl','SSCL')]:
        m=data['models'][key]['source_macro_metrics'];row=label+', gold + weak & '+' & '.join(f'{m[k]:.3f}' for k in ('hidden_precision','hidden_recall','hidden_f1','weighted_jaccard','count_absolute_error'))+' '+r'\\'
        text=re.sub(re.escape(label)+r', gold \+ weak &[^\n]+',lambda _:row,text)
    text=text.replace('are evaluated on the same 90 gold formulas;', 'are evaluated on the same 90 gold formulas with identical observed ingredients;')
    key='The admissible pool~\\eqref{eq:pool-weak} is rebuilt for every inner and outer target, giving 62 to 142 admissible weak records per outer fold.'
    text=text.replace(key,key+' Query eligibility and observed masks are generated once from the gold training vocabulary at each split and reused across every weak weight and model configuration, including inner selection. Additional weak vocabulary can expand the prediction space but cannot change the test input.')
    start=text.index('Weak records helped the quantity');end=text.index('\n\n',start)
    text=text[:start]+r'The matched-mask experiment makes the role of source review concrete. Adding 146 unreviewed records supplies more observed pairs, yet leaves size decisions unchanged and lowers SSCL recovery, principally in Huizhai. Positive inner-selected weights describe what validation selected within the available training works; their outer-fold performance measures whether that choice transfers. Here it does not improve aggregate recovery. Review should prioritise families containing rare materials, families spanning collections and additional witnesses of unstable edges, because these records can add information that the present graph lacks.'+text[end:]
    text=text.replace('Unreviewed records improve size prediction but not ingredient identification,', 'Unreviewed-record augmentation does not improve the matched-mask benchmark,')
    text=text.replace('6450 hidden-material opportunities pooled over folds and masks', '6450 hidden-material opportunities across 1660 evaluated fold--mask--formula instances')
    text=text.replace('so the recall of any ranking model is bounded', 'so the recall of a closed-vocabulary ranking model is bounded')
    text=text.replace('which sets a hard ceiling that no ranking model can pass without new sources', 'which sets the recall ceiling for this closed-vocabulary task')
    (research/'reports/v5_common_mask_inference.json').write_text(json.dumps({'weak_sscl_difference':comp,'ninety_percent_interval':ci},indent=2))
    return text.replace('without changing its posterior mode.', 'without changing its posterior median.')
