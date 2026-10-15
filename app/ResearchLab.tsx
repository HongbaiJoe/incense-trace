'use client';
import {useEffect,useMemo,useState} from 'react';
import formulas from './data/research-formulas.json';
import {names,vocabulary,reconstruct,type Reconstruction} from './research-engine';
import './research.css';
import IncenseSmoke from './IncenseSmoke';
import ResearchMethod from '../components/ResearchMethod';
import {Dotm3x3_1} from '../components/ui/dotm-3x3-1';
import MaterialStack from '../components/MaterialStack';
const percent=(v:number):string=>v>0&&v<0.0001?'<0.01%':`${(v*100).toFixed(2)}%`;

const workNames:Record<string,string>={chen_xiangpu_compilation:'陈氏香谱',hong_xiangpu_attributed:'洪氏香谱',huizhai_xiangpu:'晦斋香谱',liexiang_xinpu:'列香新谱',moe_xiaolu_xiangpu:'墨娥小录',xiangcheng_compilation_unresolved_source:'香乘辑录'};
type Entry={id:string;title:string;source:string;notes:string;observed:string;result:string;published:number;created_at:string};
export default function ResearchLab(){
  const [section,setSection]=useState('home');const [search,setSearch]=useState('');
  const [known,setKnown]=useState<{id:string;amount:string}[]>([{id:'sandalwood_white',amount:'2'},{id:'agarwood',amount:'1'}]);
  const [count,setCount]=useState('');const [mass,setMass]=useState('');
  const [result,setResult]=useState<Reconstruction|null>(null);const [error,setError]=useState('');
  const [title,setTitle]=useState('');const [source,setSource]=useState('');const [notes,setNotes]=useState('');
  const [published,setPublished]=useState(false);const [saving,setSaving]=useState(false);const [saved,setSaved]=useState('');
  const [entries,setEntries]=useState<Entry[]>([]);const [signedIn,setSignedIn]=useState(false);const [dbError,setDbError]=useState('');
  const [paused,setPaused]=useState(false);
  const [expanded,setExpanded]=useState<string|null>(null);
  const filtered=useMemo(()=>formulas.filter(f=>(f.title+workNames[f.work]+Object.keys(f.composition).map(k=>names[k]).join('')).includes(search)),[search]);
  useEffect(()=>{const hash=location.hash.slice(1);if(['restore','archive','library','method'].includes(hash))setSection(hash);const listener=()=>setSection(location.hash.slice(1)||'home');window.addEventListener('hashchange',listener);return()=>window.removeEventListener('hashchange',listener);},[]);
  useEffect(()=>{if(section==='library')refresh();},[section]);
  useEffect(()=>{if(matchMedia('(prefers-reduced-motion: reduce)').matches)setPaused(true);try{const raw=sessionStorage.getItem('xiangji-draft');if(raw){const d=JSON.parse(raw);setKnown(d.known);setCount(d.count);setMass(d.mass);setTitle(d.title);setSource(d.source);setNotes(d.notes);setPublished(d.published);setResult(reconstruct(Object.fromEntries(d.known.map((r:{id:string;amount:string})=>[r.id,Number(r.amount)])),d.count?Number(d.count):undefined,d.mass?Number(d.mass)/100:undefined));sessionStorage.removeItem('xiangji-draft');}}catch{}},[]);
  function preserveDraft(){sessionStorage.setItem('xiangji-draft',JSON.stringify({known,count,mass,title,source,notes,published}));}
  function go(next:string){location.hash=next==='home'?'':next;setSection(next);setError('');window.scrollTo({top:0,behavior:'instant'});}
  function inputs(){const obs:Record<string,number>={};for(const row of known){if(obs[row.id])throw new Error('同一种香材只需填写一次。');obs[row.id]=Number(row.amount);}return obs;}
  function predict(){try{setResult(reconstruct(inputs(),count?Number(count):undefined,mass?Number(mass)/100:undefined));setError('');setSaved('');}catch(e){setError((e as Error).message);}}
  async function refresh(){try{const response=await fetch('/api/restorations');const data=await response.json() as {error?:string;records:Entry[];signedIn:boolean};if(!response.ok)throw new Error(data.error);setEntries(data.records);setSignedIn(data.signedIn);setDbError('');}catch(e){setDbError((e as Error).message);}}
  async function save(){setSaving(true);setError('');try{const response=await fetch('/api/restorations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,source,notes,observed:inputs(),totalCount:count?Number(count):undefined,knownMass:mass?Number(mass)/100:undefined,published})});const data=await response.json() as {error?:string};if(!response.ok)throw new Error(data.error);setSaved('已保存');}catch(e){setError((e as Error).message);}finally{setSaving(false);}}
  function download(){if(!result)return;const blob=new Blob([JSON.stringify({title,source,notes,observed:inputs(),result},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='xiangji-restoration.json';a.click();URL.revokeObjectURL(url);}
  function changeKnown(rows:typeof known){setKnown(rows);setResult(null);setSaved('');}
  function useFormula(f:typeof formulas[number]){const part=Object.entries(f.composition).slice(0,Math.max(1,Math.floor(Object.keys(f.composition).length/2)));changeKnown(part.map(([id,v])=>({id,amount:String(v)})));setTitle(f.title+' · 复原');setSource(f.source.stable_revision_url);setCount('');setMass('');go('restore');}
  return <div className="research-lab">
    {section!=='home'&&<nav className="lab-nav" aria-label="主导航"><button onClick={()=>go('home')} aria-label="首页" className="home-mark">香迹</button><div>{[['restore','复原'],['archive','已复原香方'],['library','资料库'],['method','方法']].map(([id,label])=><button key={id} aria-current={section===id?'page':undefined} onClick={()=>go(id)}>{label}</button>)}</div></nav>}
    {section==='home'?<main className="lab-cover">
      <div className="cover-left"><div className="cover-name"><h1>香迹<img className="vermilion-seal" src="/media/xiangji-seal.png" alt="" aria-hidden="true"/></h1><p>香方复原实验室</p></div><nav className="cover-menu" aria-label="主导航">{[['restore','复原香方'],['archive','已复原香方'],['library','资料库'],['method','公开方法']].map(([id,label])=><button key={id} onClick={()=>go(id)}>{label}<svg width="19" height="19" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4 10h12m-5-5 5 5-5 5" stroke="currentColor" strokeWidth="1"/></svg></button>)}</nav></div>
      <div className="cover-right"><div className="incense-stage"><img src="/media/incense-v5.png" alt="一支完整线香立在瓷座上，烟雾从燃烧端上升"/><IncenseSmoke paused={paused}/></div></div>
      <button className="motion-toggle" onClick={()=>setPaused(!paused)}>{paused?'播放烟雾':'暂停烟雾'}</button>
    </main>:<main className="lab-content" key={section}>
    {section==='restore'&&<><header className="lab-heading"><h1>复原</h1><p>填写残方中已有的香材与份量。</p></header><div className="restoration-desk"><div>
      <div className="ingredient-head"><span>已知香材</span><span>份量</span></div>
      {known.map((row,i)=><div className="ingredient-input" key={i}><select aria-label={`香材 ${i+1}`} value={row.id} onChange={e=>changeKnown(known.map((r,j)=>j===i?{...r,id:e.target.value}:r))}>{vocabulary.map(id=><option key={id} value={id}>{names[id]}</option>)}</select><input aria-label={`份量 ${i+1}`} type="number" min="0.001" step="any" value={row.amount} onChange={e=>changeKnown(known.map((r,j)=>j===i?{...r,amount:e.target.value}:r))}/><button aria-label={`移除 ${names[row.id]}`} onClick={()=>changeKnown(known.filter((_,j)=>i!==j))}>×</button></div>)}
      <button className="text-action" onClick={()=>changeKnown([...known,{id:vocabulary.find(k=>!known.some(r=>r.id===k))||vocabulary[0],amount:'1'}])}>添加香材</button>
      <details className="lab-details"><summary>已知总数或占比</summary><label>总香材数<input type="number" min={known.length+1} value={count} onChange={e=>{setCount(e.target.value);setResult(null);}} placeholder="由模型估计"/></label><label>已知部分占全方（%）<input type="number" min="0.01" max="99.99" step="any" value={mass} onChange={e=>{setMass(e.target.value);setResult(null);}} placeholder="由模型估计"/></label></details>
      <button className="ink-button" onClick={predict}>生成候选香方</button><p role="alert" className="lab-error">{error}</p>
      <MaterialStack className="desk-folio" label="复原页香材"/>
    </div><div className="result-sheet" aria-live="polite">{result?<><div className="result-title"><h2>候选香方</h2><button className="text-action" onClick={download}>导出</button></div><div className="composition-table">{Object.entries(result.composition).sort((a,b)=>b[1]-a[1]).map(([id,v],i)=><div className="composition-row" key={id} style={{animationDelay:`${i*35}ms`}}><span>{names[id]}{known.some(k=>k.id===id)&&<small>已知</small>}</span><span>{percent(v)}</span><div className="ratio-rule" style={{width:`${v*100}%`}}/></div>)}</div>
      <details className="lab-details"><summary>参照香方</summary>{result.evidence.map(e=><p key={e.id}><button className="text-action" onClick={()=>{setSearch(e.title);setExpanded(e.id);go('archive');}}>{e.title}</button></p>)}<p>比例按芳香材料干重归一，保留已知香材之间的份量关系。</p></details>
      <div className="save-form"><label>香名<input value={title} onChange={e=>setTitle(e.target.value)}/></label><label>出处<input value={source} onChange={e=>setSource(e.target.value)} placeholder="书名、卷页或原文链接"/></label><label>校订记录<textarea value={notes} onChange={e=>setNotes(e.target.value)} rows={3}/></label><label className="inline-check"><input type="checkbox" checked={published} onChange={e=>setPublished(e.target.checked)}/>公开此条候选记录</label><div className="save-actions"><button className="ink-button" onClick={save} disabled={saving||!title.trim()}>{saving?<><Dotm3x3_1 size={18} color="white" ariaLabel="保存中"/> 保存中…</>:'保存到资料库'}</button><a onClick={preserveDraft} href="/signin-with-chatgpt?return_to=%2F%23restore" target="_top">登录</a><span role="status">{saved}</span></div></div>
    </>:<div className="empty-sheet"><h2>待补之处</h2><p>候选香材、比例与参照出处将在这里展开。</p></div>}</div></div></>}
    {section==='archive'&&<><header className="lab-heading archive-heading"><h1>已复原香方</h1><input aria-label="搜索香方" type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="搜索香名、香材或书名"/></header><div className="archive-layout"><div className="formula-list">{filtered.length===0&&<p>没有找到对应香方。</p>}{filtered.map(f=><article key={f.id} className="formula-item"><button className="formula-summary" aria-expanded={expanded===f.id} onClick={()=>setExpanded(expanded===f.id?null:f.id)}><span>{f.title}</span><small>{workNames[f.work]}</small><span aria-hidden="true">{expanded===f.id?'−':'+'}</span></button>{expanded===f.id&&<div className="formula-body"><div className="formula-ingredients">{Object.entries(f.composition).map(([id,v])=><span key={id}>{names[id]} <b>{(v*100).toFixed(1)}%</b></span>)}</div><details><summary>原文</summary><p>{f.text.replace(/\{\{[^}]*\}\}/g,'')}</p></details><div className="formula-links"><a href={f.source.stable_revision_url} target="_blank" rel="noreferrer">查看底本</a><button onClick={()=>useFormula(f)}>遮盖一半，试着复原</button></div></div>}</article>)}</div><aside className="archive-image"><MaterialStack variant="manuscripts" label="古籍"/></aside></div></>}
    {section==='library'&&<><header className="lab-heading"><h1>资料库</h1><button className="text-action" onClick={refresh}>刷新</button></header><div className="library-layout"><div>{dbError?<p role="alert">{dbError}</p>:entries.length===0?<p>尚无公开复原记录。完成一份香方后，即可保存至此。</p>:entries.map(e=><article className="saved-entry" key={e.id}><h2>{e.title}</h2><p>{e.source}</p><div className="formula-ingredients">{Object.entries((JSON.parse(e.result) as Reconstruction).composition).map(([id,v])=><span key={id}>{names[id]} {percent(v)}</span>)}</div>{e.notes&&<p>{e.notes}</p>}<small>{e.published?'公开候选':'个人草稿'} · {e.created_at}</small></article>)}{!signedIn&&<a className="text-action" href="/signin-with-chatgpt?return_to=%2F%23library" target="_top">登录，查看个人草稿</a>}</div><MaterialStack variant="vessels" label="香具"/></div></>}
    {section==='method'&&<ResearchMethod/>}
    </main>}
  </div>;
}
