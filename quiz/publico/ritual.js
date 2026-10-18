/* Visual-only controller. Reading content still comes from the existing API. */
(()=>{
 'use strict';
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const portal=document.querySelector('.portal-screen');
 const canvas=document.getElementById('portalParticles');
 const ctx=canvas?.getContext('2d');
 let frame=0,active=false,last=0;
 const stars=Array.from({length:54},(_,n)=>({x:((n*71)%367)/367,y:((n*137)%311)/311,r:n%4===0?1.3:.7,s:.012+(n%5)*.006}));
 function draw(time){
  if(!active||!ctx)return;
  if(time-last>32){
   const dt=Math.min((time-last)/1000,.05);last=time;
   const w=canvas.clientWidth,h=canvas.clientHeight;
   ctx.clearRect(0,0,w,h);
   for(const p of stars){
    if(!reduced.matches)p.y=(p.y-p.s*dt+1)%1;
    ctx.beginPath();ctx.fillStyle=`rgba(227,197,137,${.2+.55*Math.abs(Math.sin(p.x*12+time/2300))})`;
    ctx.arc(p.x*w,p.y*h,p.r,0,Math.PI*2);ctx.fill();
   }
  }
  if(!reduced.matches)frame=requestAnimationFrame(draw);
 }
 function refresh(){
  cancelAnimationFrame(frame);active=portal?.classList.contains('on')&&!document.hidden;
  if(active&&ctx){const d=Math.min(devicePixelRatio||1,2);canvas.width=canvas.clientWidth*d;canvas.height=canvas.clientHeight*d;ctx.setTransform(d,0,0,d,0,0);last=0;draw(performance.now());}
 }
 if(portal)new MutationObserver(refresh).observe(portal,{attributes:true,attributeFilter:['class']});
 document.addEventListener('visibilitychange',refresh);window.addEventListener('resize',refresh);reduced.addEventListener('change',refresh);
 refresh();
})();
