# /// script
# dependencies = ["numpy", "scipy", "scikit-learn>=1.7"]
# ///
"""v2: supervised inverse formulation + perceptual fit + co-occurrence graph."""

import hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RESEARCH_ROOT=Path(__file__).resolve().parents[2]
ROOT=RESEARCH_ROOT/"data"/"raw"
load=lambda n: json.loads((ROOT/n).read_text(encoding="utf-8"))
mat_data=load("materials.json"); recipe_data=load("known_recipes_v2.json")
targets=load("targets.json"); profiles=load("target_profiles.json")["profiles"]
dims=mat_data["dimensions"]; materials=mat_data["materials"]; ids=[m["id"] for m in materials]
id_index={x:i for i,x in enumerate(ids)}; A=np.array([m["vector"] for m in materials],float).T
families=["plum","orchid","osmanthus","spring","quiet"]

def norm(d):
 t=sum(d.values()); return {k:v/t for k,v in d.items() if v>0}

def features(r):
 return np.array(r["target"]+[1.0 if r["family"]==f else 0.0 for f in families],float)

def outcome(r):
 y=np.zeros(len(ids));
 for k,v in norm(r["ingredients"]).items():
  if k in id_index:y[id_index[k]]=v
 return y

recipes=recipe_data["recipes"]
is_test=lambda r:int(hashlib.sha256(r["id"].encode()).hexdigest()[:8],16)%5==4
train=[r for r in recipes if not is_test(r)]; test=[r for r in recipes if is_test(r)]
X=np.array([features(r) for r in train]); Y=np.array([outcome(r) for r in train])

def make_family_priors(rows):
 out={}
 for family in families:
  subset=[outcome(r) for r in rows if r["family"]==family]
  out[family]=np.mean(subset,axis=0) if subset else np.zeros(len(ids))
  if out[family].sum():out[family]/=out[family].sum()
 return out
family_priors=make_family_priors(train)
global_prior=Y.mean(axis=0);global_prior/=global_prior.sum()

# Co-occurrence graph learned only from the v2 training split.
present=(Y>0).astype(float); counts=present.sum(axis=0); pair=present.T@present
co=np.zeros_like(pair)
for i in range(len(ids)):
 for j in range(len(ids)):
  if i!=j: co[i,j]=(pair[i,j]+0.5)/(min(counts[i],counts[j])+1.0)

def role_for(m):
 v=np.array(m["vector"]); top=v[6]+.45*v[4]+.25*v[10]-.35*v[11]
 heart=v[3]+.55*v[2]+.45*v[5]
 base=v[11]+.45*v[0]+.45*v[1]+.25*v[7]+.2*v[9]
 return ["top","heart","base"][int(np.argmax([top,heart,base]))]
roles={m["id"]:role_for(m) for m in materials}

def pipeline(alpha): return Pipeline([("scale",StandardScaler()),("ridge",Ridge(alpha=alpha))])
def knn_pipeline(k): return Pipeline([("scale",StandardScaler()),("knn",KNeighborsRegressor(n_neighbors=k,weights="distance",p=2))])

# Nested choice: alpha is selected with shuffled K-fold CV inside training only.
alphas=[0.1,0.5,1.0,2.0,5.0,10.0]; cv=KFold(n_splits=5,shuffle=True,random_state=42)
alpha_rows=[]
for alpha in alphas:
 losses=[]
 for a,b in cv.split(X):
  p=pipeline(alpha);p.fit(X[a],Y[a]);pred=np.clip(p.predict(X[b]),0,None)
  pred=pred/np.maximum(pred.sum(axis=1,keepdims=True),1e-9)
  losses.append(float(np.mean(np.abs(pred-Y[b]))))
 alpha_rows.append({"alpha":alpha,"cv_mae":sum(losses)/len(losses)})
best_alpha=min(alpha_rows,key=lambda z:z["cv_mae"])["alpha"]
reg=pipeline(best_alpha);reg.fit(X,Y)

knn_rows=[]
for k in [2,3,4,5,6,7]:
 losses=[]
 for a,b in cv.split(X):
  p=knn_pipeline(k);p.fit(X[a],Y[a]);pred=np.clip(p.predict(X[b]),0,None)
  pred=pred/np.maximum(pred.sum(axis=1,keepdims=True),1e-9)
  losses.append(float(np.mean(np.abs(pred-Y[b]))))
 knn_rows.append({"k":k,"cv_mae":sum(losses)/len(losses)})
best_k=min(knn_rows,key=lambda z:z["cv_mae"])["k"]
knn=knn_pipeline(best_k);knn.fit(X,Y)

blend_rows=[]
for beta in [0.0,.25,.5,.75,1.0]:
 losses=[]
 for a,b in cv.split(X):
  rp=pipeline(best_alpha);kp=knn_pipeline(best_k);rp.fit(X[a],Y[a]);kp.fit(X[a],Y[a])
  pred=beta*np.clip(kp.predict(X[b]),0,None)+(1-beta)*np.clip(rp.predict(X[b]),0,None)
  pred=pred/np.maximum(pred.sum(axis=1,keepdims=True),1e-9)
  losses.append(float(np.mean(np.abs(pred-Y[b]))))
 blend_rows.append({"knn_weight":beta,"cv_mae":sum(losses)/len(losses)})
best_beta=min(blend_rows,key=lambda z:z["cv_mae"])["knn_weight"]

def inverse_scores(target):
 target=np.array(target); den=np.linalg.norm(A,axis=0)*np.linalg.norm(target)
 return np.divide(target@A,den,out=np.zeros(len(ids)),where=den>0)

def select_six(target, learned, hints=None, anchors=None, family_prior=None, preferred=None):
 hints=hints or {}; anchors=anchors or []
 learned=np.clip(learned,0,None); learned=learned/(learned.sum()+1e-9)
 family_prior=np.zeros(len(ids)) if family_prior is None else family_prior
 inv=inverse_scores(target); inv=np.clip(inv,0,None); inv=inv/(inv.sum()+1e-9)
 score=.42*learned+.36*family_prior+.22*inv+np.array([.08*hints.get(i,0) for i in ids])
 selected=[]
 for a in anchors:
  if a in id_index and a not in selected:selected.append(a)
 if preferred in id_index and preferred not in selected:selected.append(preferred)
 while len(selected)<6:
  remaining=[i for i in ids if i not in selected]
  def utility(i):
   ii=id_index[i]; compat=np.mean([co[ii,id_index[j]] for j in selected]) if selected else 0
   return score[ii]+.10*compat
  selected.append(max(remaining,key=utility))
 return selected[:max(6,len(anchors))],score

def optimize(target, selected, prior):
 idx=np.array([id_index[i] for i in selected]); M=A[:,idx]; p=np.clip(prior[idx],1e-6,None);p=p/p.sum()
 def loss(x):
  percept=np.mean((M@x-target)**2)
  learned=np.mean((x-p)**2)
  compat=sum(x[i]*x[j]*co[idx[i],idx[j]] for i in range(len(x)) for j in range(i+1,len(x)))
  entropy=np.sum(x*np.log(np.clip(x,1e-9,None)))
  return 1.7*percept+.65*learned-.05*compat+.018*entropy
 n=len(selected);x0=np.full(n,1/n)
 result=minimize(loss,x0,method="SLSQP",bounds=[(.04,.52)]*n,constraints={"type":"eq","fun":lambda x:x.sum()-1},options={"maxiter":500,"ftol":1e-11})
 x=result.x if result.success else x0
 rounded=np.round(x*20)/20; rounded=np.maximum(rounded,.05); rounded[0]+=1-rounded.sum()
 if rounded[0]<.05:
  deficit=.05-rounded[0];rounded[0]=.05;rounded[np.argmax(rounded[1:])+1]-=deficit
 return rounded/rounded.sum()

def calibrate_dominant(x,selected,preferred):
 if preferred not in selected:return x
 p=selected.index(preferred);q=int(np.argmax(x))
 if p!=q and x[p]<=x[q]:
  delta=min(x[q]-.05,(x[q]+.05-x[p])/2)
  x[p]+=delta;x[q]-=delta
 return x/x.sum()

def quantize_five(x,selected,preferred):
 raw=x*20;units=np.maximum(1,np.floor(raw).astype(int))
 while units.sum()<20:
  i=int(np.argmax(raw-units));units[i]+=1
 while units.sum()>20:
  candidates=[i for i,u in enumerate(units) if u>1]
  i=min(candidates,key=lambda j:raw[j]-units[j]);units[i]-=1
 if preferred in selected:
  p=selected.index(preferred);q=int(np.argmax(units))
  while p!=q and units[p]<=units[q] and units[q]>1:
   units[p]+=1;units[q]-=1;q=int(np.argmax(units))
 return units/20

def metrics(y,p):
 true=set(np.where(y>0)[0]); order=list(np.argsort(p)[::-1]); pred=set(np.where(p>0)[0]); union=true|pred
 wj=sum(min(y[i],p[i]) for i in union)/max(1e-9,sum(max(y[i],p[i]) for i in union))
 return {"top1":float(np.argmax(y)==np.argmax(p)),"recall5":len(set(order[:5])&true)/len(true),"weighted_jaccard":wj,"ratio_mae":float(np.mean([abs(y[i]-p[i]) for i in union]))}

def v2_predict(r, fit=reg, near=knn):
 learned=(1-best_beta)*np.clip(fit.predict(features(r).reshape(1,-1))[0],0,None)+best_beta*np.clip(near.predict(features(r).reshape(1,-1))[0],0,None)
 fp=family_priors.get(r["family"],np.zeros(len(ids)))
 preferred=ids[int(np.argmax(.50*learned+.35*fp+.15*global_prior))]
 sel,score=select_six(np.array(r["target"]),learned,family_prior=fp,preferred=preferred)
 x=optimize(np.array(r["target"]),sel,learned+fp+.10*score)
 x=calibrate_dominant(x,sel,preferred)
 x=quantize_five(x,sel,preferred)
 p=np.zeros(len(ids));
 for i,w in zip(sel,x):p[id_index[i]]=w
 return p

def baseline_predict():
 avg=Y.mean(axis=0);sel=np.argsort(avg)[::-1][:6];p=np.zeros(len(ids));p[sel]=avg[sel];return p/p.sum()

test_rows=[];base=baseline_predict()
for r in test:
 p=v2_predict(r);test_rows.append({"id":r["id"],"name":r["name"],"metrics":metrics(outcome(r),p),"predicted":{ids[i]:round(float(p[i]),4) for i in np.where(p>0)[0]}})
def avg(rows):return {k:sum(r["metrics"][k] for r in rows)/len(rows) for k in rows[0]["metrics"]}
v2_metrics=avg(test_rows)
base_rows=[{"metrics":metrics(outcome(r),base)} for r in test];base_metrics=avg(base_rows)

# Refit on all 44 recorded formulas for final 30 hypotheses after evaluation.
Xall=np.array([features(r) for r in recipes]);Yall=np.array([outcome(r) for r in recipes]);final_reg=pipeline(best_alpha);final_reg.fit(Xall,Yall);final_knn=knn_pipeline(best_k);final_knn.fit(Xall,Yall)
final_family_priors=make_family_priors(recipes)
final_global_prior=Yall.mean(axis=0);final_global_prior/=final_global_prior.sum()
target_by={t["id"]:t for t in targets}; outputs=[]
for pr in profiles:
 target=np.array([pr["labels"].get(d,0) for d in dims],float)
 family="osmanthus" if pr["id"] in {"juwutou","qubo"} else "quiet" if pr["id"] in {"fanhun","jinti","baizhuo","jibin"} else "spring" if pr["id"] in {"bihan","huaimeng"} else ""
 feat=np.array(list(target)+[1.0 if family==f else 0.0 for f in families])
 learned=(1-best_beta)*np.clip(final_reg.predict(feat.reshape(1,-1))[0],0,None)+best_beta*np.clip(final_knn.predict(feat.reshape(1,-1))[0],0,None)
 fp=final_family_priors.get(family,np.zeros(len(ids)))
 anchors=pr.get("anchors",[])
 preferred=anchors[0] if anchors else ids[int(np.argmax(.50*learned+.35*fp+.15*final_global_prior))]
 if len(anchors)>=5:
  sel=list(anchors);score=.42*learned+.36*fp+.22*inverse_scores(target)
 else:
  sel,score=select_six(target,learned,pr.get("hints"),anchors,fp,preferred)
 x=optimize(target,sel,learned+fp+.10*score)
 x=calibrate_dominant(x,sel,preferred)
 x=quantize_five(x,sel,preferred)
 formula=sorted([{"material_id":i,"material":materials[id_index[i]]["zh"],"percent":int(round(w*100)),"role":roles[i]} for i,w in zip(sel,x)],key=lambda z:z["percent"],reverse=True)
 outputs.append({**target_by[pr["id"]],"labels":pr["labels"],"formula":formula})

scale=final_reg.named_steps["scale"];ridge=final_reg.named_steps["ridge"]
report={"model_version":"v2.4-historical-graph","method":"Ridge全局先验 + 距离加权kNN历史类方 + 家族材料先验 + 感知平均逆问题 + 香材共现图 + SLSQP非负比例优化 + 主料校准；顶中基调仅作解释，不作硬约束", "recorded_recipe_count":len(recipes),"train_count":len(train),"unseen_test_count":len(test),"test_ids":[r["id"] for r in test],"alpha_search":alpha_rows,"selected_alpha":best_alpha,"knn_search":knn_rows,"selected_k":best_k,"blend_search":blend_rows,"knn_weight":best_beta,"metrics":v2_metrics,"baseline_metrics":base_metrics,"test_detail":test_rows,"dimensions":dims,"families":families,"roles":roles,"family_priors":{k:v.round(8).tolist() for k,v in final_family_priors.items()},"global_prior":final_global_prior.round(8).tolist(),"cooccurrence":co.round(5).tolist(),"ridge":{"mean":scale.mean_.round(8).tolist(),"scale":scale.scale_.round(8).tolist(),"coef":ridge.coef_.round(8).tolist(),"intercept":ridge.intercept_.round(8).tolist()},"knn_training":{"features":Xall.round(8).tolist(),"outcomes":Yall.round(8).tolist()},"targets":outputs}
output_path=RESEARCH_ROOT/"experiments"/"frozen_results"/"reproduction_v24.json"
output_path.parent.mkdir(parents=True,exist_ok=True)
output_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"recipes":len(recipes),"train":len(train),"test":len(test),"alpha":best_alpha,"metrics":v2_metrics,"baseline":base_metrics,"density":sorted(set(len(t["formula"]) for t in outputs))},ensure_ascii=False,indent=2))
