import model from './data/research-model.json';

export const vocabulary = model.vocabulary;
export const names = model.names as Record<string,string>;
export const modelVersion = model.version;
export type Reconstruction = {composition:Record<string,number>; knownMass:number; total:number; countPosterior:Record<string,number>; evidence:{id:string;title:string;similarity:number}[]; version:string};

export function reconstruct(observed:Record<string,number>, totalCount?:number, knownMass?:number):Reconstruction {
  const entries=Object.entries(observed);
  if(!entries.length || entries.some(([k,v])=>!vocabulary.includes(k)||!Number.isFinite(v)||v<=0)) throw new Error('请选择香材并填写正数份量。');
  const known=new Set(entries.map(([k])=>vocabulary.indexOf(k)));
  if(known.size>=vocabulary.length) throw new Error('请至少留出一种待复原香材。');
  const hist=model.count_histogram as Record<string,number>;
  const maximum=Math.max(...Object.keys(hist).map(Number),known.size+1);
  const countPosterior:Record<string,number>={}; let norm=0;
  for(let k=known.size+1;k<=maximum;k++){countPosterior[k]=((hist[k]||0)+.5)/(k+1);norm+=countPosterior[k];}
  let cumulative=0,median=maximum;
  for(const [k,p] of Object.entries(countPosterior)){countPosterior[k]=p/norm;cumulative+=p/norm;if(cumulative>=.5&&median===maximum)median=Number(k);}
  const total=totalCount??median;
  if(!Number.isInteger(total)||total<=known.size||total>vocabulary.length) throw new Error('总香材数应为大于已知香材数的整数。');
  const score=vocabulary.map((_,j)=>{
    const edges=[...known].map(i=>model.graph[i][j]);
    if(model.parameters.reducer==='max')return Math.max(...edges);
    if(model.parameters.reducer==='top2'){edges.sort((a,b)=>b-a);return edges.slice(0,2).reduce((a,b)=>a+b,0)/Math.min(2,edges.length);}
    return edges.reduce((a,b)=>a+b,0)/edges.length;
  });
  const selected=vocabulary.map((_,i)=>i).sort((a,b)=>(known.has(b)?Infinity:score[b])-(known.has(a)?Infinity:score[a])||a-b).slice(0,total);
  const neighbors=model.compositions.map((row,i)=>({i,similarity:[...known].filter(j=>row[j]>0).length/Math.sqrt(row.filter(v=>v>0).length*known.size)})).sort((a,b)=>b.similarity-a.similarity||a.i-b.i).slice(0,model.parameters.ratio_neighbors);
  const weight=neighbors.reduce((s,n)=>s+n.similarity,0);
  const ratio=vocabulary.map((_,j)=>Math.max(1e-9,neighbors.reduce((s,n)=>s+model.compositions[n.i][j]*(weight?n.similarity:1),0)/(weight||neighbors.length)));
  const mass=knownMass??Math.max(1e-6,Math.min(1-1e-6,[...known].reduce((s,j)=>s+ratio[j],0)/selected.reduce((s,j)=>s+ratio[j],0)));
  if(!Number.isFinite(mass)||mass<=0||mass>=1)throw new Error('已知部分占比须大于 0、小于 100%。');
  const observedSum=entries.reduce((s,[,v])=>s+v,0);
  const composition:Record<string,number>=Object.fromEntries(entries.map(([k,v])=>[k,mass*v/observedSum]));
  const hidden=selected.filter(i=>!known.has(i));const hiddenSum=hidden.reduce((s,j)=>s+ratio[j],0);
  hidden.forEach(j=>composition[vocabulary[j]]=(1-mass)*ratio[j]/hiddenSum);
  return {composition,knownMass:mass,total,countPosterior,version:modelVersion,evidence:neighbors.filter(n=>n.similarity>0).slice(0,3).map(n=>({id:model.records[n.i].id,title:model.records[n.i].title,similarity:n.similarity}))};
}
