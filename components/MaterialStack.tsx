'use client';
import {useState, type CSSProperties} from 'react';

const materialPhotos = [
  {src:'/media/frankincense.jpg',name:'乳香',alt:'乳香树脂颗粒',fit:'cover'},
  {src:'/media/benzoin-hd.jpg',name:'安息香',alt:'安息香树脂的颗粒与断面',fit:'cover'},
  {src:'/media/agarwood-hd.jpg',name:'沉香',alt:'沉香木的树脂纹理',fit:'cover'},
  {src:'/media/clove.jpg',name:'丁香',alt:'干燥丁香花蕾特写',fit:'cover'},
] as const;
const collections={
 materials:materialPhotos,
 manuscripts:[
  {src:'/media/chen-volume-3.jpg',name:'《陈氏香谱》卷三',alt:'陈氏香谱卷三扫描书页',fit:'contain'},
  {src:'/media/chen-volume-4.jpg',name:'《陈氏香谱》卷四',alt:'陈氏香谱卷四扫描书页',fit:'contain'},
  {src:'/media/wang-xiangpu.jpg',name:'王黼《香谱》',alt:'王黼香谱扫描书页',fit:'contain'},
 ],
 vessels:[
  {src:'/media/bronze-censer-hd.jpg',name:'铜香炉',alt:'大都会艺术博物馆藏铜香炉',fit:'contain'},
  {src:'/media/jade-censer-hd.jpg',name:'白玉盖炉',alt:'大都会艺术博物馆藏清代白玉盖炉',fit:'contain'},
  {src:'/media/jade-stand-hd.jpg',name:'玉香炉与座',alt:'大都会艺术博物馆藏玉香炉与底座',fit:'contain'},
 ],
 research:[
  {src:'/media/research-performance.svg',name:'跨书测试 · 论文图 4',alt:'六种方法的总体表现、分书表现及相对频率基线的差值',fit:'contain'},
  {src:'/media/research-protocol.svg',name:'任务与模型 · 论文图 3',alt:'残方补全、嵌套跨书验证和来源稳定关联模型的流程',fit:'contain'},
  {src:'/media/research-calibration.svg',name:'概率校准 · 论文图 7',alt:'论文中的概率校准实验图',fit:'contain'},
 ],
} as const;

/** An aligned photographic folio: the rear sheets become the next photographs. */
export default function MaterialStack({variant='materials',label='香材',className=''}:{variant?:keyof typeof collections;label?:string;className?:string}){
  const photographs=collections[variant];
  const [active,setActive]=useState(0);
  const step=(direction:number)=>setActive(i=>(i+direction+photographs.length)%photographs.length);
  return <figure className={`material-stack folio-${variant} ${className}`} aria-label={`${label}图片`}>
    <button className="material-folio" aria-label={`下一张${label}图片`} onClick={()=>step(1)}>
      {photographs.map((photo,i)=>{
        const depth=(i-active+photographs.length)%photographs.length;
        return <span key={photo.src} className="material-print" data-front={depth===0} aria-hidden={depth!==0}
          style={{'--depth':depth,zIndex:photographs.length-depth} as CSSProperties}>
          <img src={photo.src} alt={depth===0?photo.alt:''} loading="lazy" decoding="async" style={{objectFit:photo.fit}}/>
        </span>;
      })}
    </button>
    <figcaption className="material-caption"><span aria-live="polite">{photographs[active].name}</span><span className="material-controls">
      <button aria-label={`上一张${label}图片`} onClick={()=>step(-1)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg></button>
      <button aria-label={`切换${label}图片`} onClick={()=>step(1)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m10 6 6 6-6 6"/></svg></button>
    </span></figcaption>
    {variant==='research'&&<a className="figure-open" href={photographs[active].src} target="_blank" rel="noreferrer">放大查看</a>}
  </figure>;
}
