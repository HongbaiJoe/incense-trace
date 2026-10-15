'use client';
import {useEffect,useRef} from 'react';
export default function IncenseSmoke({paused}:{paused:boolean}){
  const canvas=useRef<HTMLCanvasElement>(null);
  useEffect(()=>{const element=canvas.current;if(!element)return;const context=element.getContext('2d');if(!context)return;
    const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
    let frame=0;let last=0;const start=performance.now();
    function draw(time:number){if(!element||!context)return;if(time-last<32){frame=requestAnimationFrame(draw);return;}last=time;
      const {width:w,height:h}=element.getBoundingClientRect();const dpr=Math.min(devicePixelRatio,2);
      if(element.width!==Math.round(w*dpr)||element.height!==Math.round(h*dpr)){element.width=Math.round(w*dpr);element.height=Math.round(h*dpr);}
      context.setTransform(dpr,0,0,dpr,0,0);context.clearRect(0,0,w,h);
      const phase=paused||reduce?0:(time-start)/1000;
      for(let strand=0;strand<5;strand++){
        context.beginPath();
        for(let j=0;j<=100;j++){
          const u=j/100;const y=h*(.43-.37*u);
          const envelope=Math.sin(u*Math.PI/2)*w*.045;
          const drift=Math.sin(u*9-phase*.8+strand*.18)*envelope+Math.sin(u*17-phase*1.1)*envelope*.28;
          const x=w*.5+drift+(strand-2)*w*.0017*u;
          if(j===0)context.moveTo(x,y);else context.lineTo(x,y);
        }
        const gradient=context.createLinearGradient(0,h*.43,0,h*.06);
        gradient.addColorStop(0,'rgba(99,104,96,0.035)');gradient.addColorStop(.3,'rgba(110,116,106,0.095)');gradient.addColorStop(1,'rgba(130,136,126,0)');
        context.strokeStyle=gradient;context.lineWidth=1.2+strand*.55;context.lineCap='round';context.shadowBlur=4;context.shadowColor='rgba(125,130,120,.1)';context.stroke();
      }
      if(!paused&&!reduce)frame=requestAnimationFrame(draw);
    }
    frame=requestAnimationFrame(draw);return()=>cancelAnimationFrame(frame);
  },[paused]);
  return <canvas ref={canvas} className="incense-smoke-canvas" aria-hidden="true"/>;
}
