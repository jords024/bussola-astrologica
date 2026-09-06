/* Componente isolado. Conteúdo e casa selecionada vêm do fluxo existente. */
window.montarPortas = (() => {
  let life, active=0, previousHouse=null;
  const opened=new Set();
  const icons=[
    'M8 20v-3a4 4 0 0 1 8 0v3 M12 11a3 3 0 1 0 0-6a3 3 0 0 0 0 6',
    'M12 3v18 M16 6H10a3 3 0 0 0 0 6h4a3 3 0 0 1 0 6H7',
    'M20 11a8 8 0 0 1-8 8H5l-3 3V11a9 9 0 0 1 18 0',
    'M3 10l9-7 9 7v11H3z M9 21v-8h6v8',
    'M12 21S2 15 2 8a5 5 0 0 1 10-1a5 5 0 0 1 10 1c0 7-10 13-10 13',
    'M12 22V10 M12 16C3 17 2 9 3 5c8 0 10 5 9 11 M12 20c9 0 11-8 9-12-7 1-9 6-9 12',
    'M8 12a4 4 0 1 0 0-8a4 4 0 0 0 0 8 M16 12a4 4 0 1 0 0-8 M1 22v-3a7 7 0 0 1 14 0v3 M18 15a5 5 0 0 1 5 5v2',
    'M20 8a8 8 0 1 0 0 9 M20 2v6h-6 M4 16v6h6',
    'M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3z',
    'M3 8h18v13H3z M8 8V4h8v4 M3 13h18 M10 13v3h4v-3',
    'M12 3v6 M4 18l5-5 M20 18l-5-5 M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0-6 0 M12 1h.1 M2 21h.1 M22 21h.1',
    'M20 16A9 9 0 0 1 8 4a9 9 0 1 0 12 12'
  ];
  return function(root, portas, house, onOpen){
    life?.abort();life=new AbortController();const signal=life.signal;
    if(house!==previousHouse){active=house?house-1:0;previousHouse=house;opened.clear();}
    // A exploração começa por outra área; a porta da carta segue identificada.
    active=house?house%12:0;
    root.replaceChildren();
    const track=document.createElement('div');track.className='portas-track';track.setAttribute('role','region');track.setAttribute('aria-label','As 12 portas do seu mapa');track.setAttribute('aria-roledescription','carrossel');
    const cards=[];
    portas.forEach(([name,description],i)=>{
      const card=document.createElement('article');card.className='porta-card'+(i+1===house?' sua':'');card.setAttribute('aria-label',`${i+1} de 12: ${name}`);
      const prefix=['de ','do ','da ','da ','do ','da ','dos ','da ','da ','da ','do ','do '][i];
      const title=document.createElement('h3');title.textContent='A porta '+prefix+name;
      const badge=document.createElement('span');badge.className='porta-selo';badge.textContent=i+1===house?'✦ você conheceu na sua carta':' ';
      const button=document.createElement('button');button.type='button';button.className='porta-button';
      button.setAttribute('aria-expanded',String(opened.has(i)));button.setAttribute('aria-label',(opened.has(i)?'Fechar':'Abrir')+' a porta: '+name);
      const reveal=document.createElement('span');reveal.className='porta-revelacao';reveal.id='porta-conteudo-'+i;button.setAttribute('aria-controls',reveal.id);
      const number=document.createElement('span');number.className='porta-num';number.textContent='PORTA '+String(i+1).padStart(2,'0');
      const heading=document.createElement('strong');heading.textContent=name;
      const desc=document.createElement('span');desc.className='porta-desc';desc.textContent=description;
      reveal.append(number,heading,desc);reveal.setAttribute('aria-hidden',String(!opened.has(i)));
      const leaf=document.createElement('span');leaf.className='porta-folha';leaf.setAttribute('aria-hidden','true');
      leaf.innerHTML=`<svg viewBox="0 0 24 24"><path d="${icons[i]}" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
      const closedHint=i+1===house?'✦ descubra o que ela representa':'✦ toque para conhecer esta porta';
      const hint=document.createElement('span');hint.className='porta-hint';hint.textContent=opened.has(i)?'Toque para fechar':closedHint;
      button.append(reveal,leaf);button.addEventListener('click',()=>{
        if(dragged)return;
        const open=button.getAttribute('aria-expanded')!=='true';
        if(open)opened.add(i);else opened.delete(i);
        button.setAttribute('aria-expanded',String(open));button.setAttribute('aria-label',(open?'Fechar':'Abrir')+' a porta: '+name);
        reveal.setAttribute('aria-hidden',String(!open));hint.textContent=open?'Toque para fechar':closedHint;
        onOpen?.(i+1,open);
      },{signal});
      card.append(title,badge,button,hint);track.append(card);cards.push(card);
    });
    const controls=document.createElement('div');controls.className='portas-controls';
    const prev=document.createElement('button'),next=document.createElement('button');
    for(const b of [prev,next]){b.type='button';b.className='portas-arrow';}
    prev.textContent='←';next.textContent='→';prev.setAttribute('aria-label','Porta anterior');next.setAttribute('aria-label','Próxima porta');
    const status=document.createElement('span');status.className='portas-status';status.setAttribute('aria-live','polite');status.setAttribute('aria-atomic','true');
    controls.append(prev,status,next);
    const dots=document.createElement('div');dots.className='portas-dots';dots.setAttribute('aria-label','Escolher uma porta');
    const reduced=()=>matchMedia('(prefers-reduced-motion:reduce)').matches;
    function move(n,smooth=true){active=Math.max(0,Math.min(11,n));track.scrollTo({left:cards[active].offsetLeft-track.offsetLeft-(track.clientWidth-cards[active].clientWidth)/2,behavior:smooth&&!reduced()?'smooth':'instant'});update();}
    function update(){status.textContent=String(active+1).padStart(2,'0')+' / 12';prev.disabled=active===0;next.disabled=active===11;[...dots.children].forEach((b,i)=>b.setAttribute('aria-current',String(i===active)));}
    portas.forEach(([name],i)=>{const b=document.createElement('button');b.type='button';b.setAttribute('aria-label',`Ir para porta ${i+1}: ${name}`);b.addEventListener('click',()=>move(i),{signal});dots.append(b);});
    prev.addEventListener('click',()=>move(active-1),{signal});next.addEventListener('click',()=>move(active+1),{signal});
    track.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();move(active+(e.key==='ArrowRight'?1:-1));cards[active].querySelector('button').focus({preventScroll:true});}},{signal});
    let frame=0;
    track.addEventListener('scroll',()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{const center=track.getBoundingClientRect().left+track.clientWidth/2;let distance=Infinity;cards.forEach((c,i)=>{const r=c.getBoundingClientRect();const d=Math.abs(r.left+r.width/2-center);if(d<distance){distance=d;active=i;}});update();});},{signal});
    let pointer=null,startX=0,startScroll=0,dragged=false;
    track.addEventListener('pointerdown',e=>{dragged=false;if(e.pointerType!=='mouse')return;pointer=e.pointerId;startX=e.clientX;startScroll=track.scrollLeft;},{signal});
    track.addEventListener('pointermove',e=>{if(pointer!==e.pointerId)return;const delta=e.clientX-startX;if(Math.abs(delta)>7){dragged=true;track.classList.add('dragging');track.setPointerCapture(e.pointerId);track.scrollLeft=startScroll-delta;}},{signal});
    function release(e){if(pointer!==e.pointerId)return;pointer=null;track.classList.remove('dragging');if(track.hasPointerCapture(e.pointerId))track.releasePointerCapture(e.pointerId);if(dragged)requestAnimationFrame(()=>{if(!signal.aborted)move(active);});setTimeout(()=>{dragged=false;},0);}
    track.addEventListener('pointerup',release,{signal});track.addEventListener('pointercancel',release,{signal});
    root.append(track,controls,dots);update();if(house&&opened.has(house-1))onOpen?.(house,true);requestAnimationFrame(()=>{if(!signal.aborted)move(active,false);});
  };
})();
