(() => {
 'use strict';
 const $ = id => document.getElementById(id);
 const canvas = $('nebula'), stage = $('stage'), ctx = canvas.getContext('2d');
 const reduced = matchMedia('(prefers-reduced-motion: reduce)');
 const settings = {detail:55, diffusion:35, light:60};
 const palettes = {ice:[119,205,237], amber:[240,184,111], silver:[214,226,237]};
 let color = 'ice', source, points = [], links = [], width = 1, height = 1, ratio = 1;
 let paused = reduced.matches, phase = 0, lastTime = 0, frame = 0, generation = 0, detailTimer;
 let zoom = 1, panX = 0, panY = 0;
 const pointers = new Map();
 const rand = n => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
 const stars = Array.from({length:170}, (_, i) => [rand(i+1), rand(i+900), rand(i+500)]);
 function setStatus(message) { $('status').textContent = message; }
 function fit() { zoom=1; panX=0; panY=0; requestDraw(); }
 function size() {
  const box=stage.getBoundingClientRect(); width=box.width; height=box.height;
  ratio=Math.min(devicePixelRatio || 1,2); canvas.width=Math.round(width*ratio); canvas.height=Math.round(height*ratio); requestDraw();
 }
 function fieldFromCanvas(surface) {
  const w=surface.width,h=surface.height, pixels=surface.getContext('2d',{willReadFrequently:true}).getImageData(0,0,w,h).data;
  const gray=new Float32Array(w*h), blur=new Float32Array(w*h);
  for(let i=0;i<gray.length;i++) { const k=i*4, a=pixels[k+3]/255; gray[i]=(pixels[k]*.2126+pixels[k+1]*.7152+pixels[k+2]*.0722)*a; }
  for(let y=1;y<h-1;y++) for(let x=1;x<w-1;x++) {
   const i=y*w+x; blur[i]=(gray[i-w-1]+2*gray[i-w]+gray[i-w+1]+2*gray[i-1]+4*gray[i]+2*gray[i+1]+gray[i+w-1]+2*gray[i+w]+gray[i+w+1])/16;
  }
  const magnitude=new Float32Array(w*h), angle=new Float32Array(w*h);
  for(let y=2;y<h-2;y++) for(let x=2;x<w-2;x++) {
   const i=y*w+x;
   const gx=-blur[i-w-1]+blur[i-w+1]-2*blur[i-1]+2*blur[i+1]-blur[i+w-1]+blur[i+w+1];
   const gy=-blur[i-w-1]-2*blur[i-w]-blur[i-w+1]+blur[i+w-1]+2*blur[i+w]+blur[i+w+1];
   magnitude[i]=Math.hypot(gx,gy)/4; angle[i]=Math.atan2(gy,gx);
  }
  surface.width=1; surface.height=1;
  return {w,h,magnitude,angle};
 }
 function extract() {
  const {w,h,magnitude,angle}=source, threshold=5+Math.pow(1-settings.detail/100,1.7)*83;
  const candidates=[];
  for(let y=3;y<h-3;y++) for(let x=3;x<w-3;x++) {
   const i=y*w+x,m=magnitude[i]; if(m<threshold)continue;
   const a=angle[i],dx=Math.round(Math.cos(a)),dy=Math.round(Math.sin(a));
   if(m<magnitude[i+dy*w+dx] || m<magnitude[i-dy*w-dx])continue;
   candidates.push({x:x-w/2,y:y-h/2,a:a+Math.PI/2,strength:Math.min(m/100,1),seed:rand(i)});
  }
  // Keep a spatially distributed, deterministic sample at a bounded rendering cost.
  const stride=Math.max(1,candidates.length/4800);
  points=[]; for(let i=0;i<candidates.length;i+=stride)points.push(candidates[Math.floor(i)]);
  const cells=new Map(),cell=9;
  points.forEach((p,i)=>{const key=`${Math.floor(p.x/cell)},${Math.floor(p.y/cell)}`;if(!cells.has(key))cells.set(key,[]);cells.get(key).push(i);});
  links=[];
  points.forEach((p,i)=>{
   const cx=Math.floor(p.x/cell),cy=Math.floor(p.y/cell),near=[];
   for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++)for(const j of cells.get(`${cx+ox},${cy+oy}`)||[]) {
    if(j<=i)continue;const q=points[j],dx=q.x-p.x,dy=q.y-p.y,d=Math.hypot(dx,dy);
    // Follow the edge tangent rather than joining unrelated nearby contours.
    if(d<1 || d>9)continue;
    if(Math.abs(Math.cos(Math.atan2(dy,dx)-p.a))<.68 || Math.abs(Math.cos(q.a-p.a))<.6)continue;
    near.push({j,d});
   }
   near.sort((a,b)=>a.d-b.d); near.slice(0,2).forEach(q=>links.push([i,q.j]));
  });
  $('point-count').textContent=`${points.length.toLocaleString('zh-CN')} 个光点 / ${links.length.toLocaleString('zh-CN')} 段线迹`;
  requestDraw(); return points.length;
 }
 function demo() {
  generation++; $('photo').value='';
  const s=document.createElement('canvas');s.width=600;s.height=460;const c=s.getContext('2d');
  c.fillStyle='#07090b';c.fillRect(0,0,600,460);
  c.lineWidth=1.6;
  for(let k=0;k<19;k++) {
   c.beginPath();c.strokeStyle=`rgb(${125+k*5},${125+k*5},${125+k*5})`;
   for(let j=0;j<=400;j++) {
    const a=j/400*Math.PI*2,r=30+k*8+Math.sin(a*3+k*.12)*13+Math.cos(a*5-k*.18)*7;
    const x=300+Math.cos(a)*r*1.24,y=230+Math.sin(a)*r*.85;
    if(j===0)c.moveTo(x,y);else c.lineTo(x,y);
   } c.closePath();c.stroke();
  }
  source=fieldFromCanvas(s);extract();fit();$('source-label').textContent='初始习作 · 等高线';
  setStatus('试试人像、树枝或建筑，让清晰的明暗边界成为线条。');
 }
 async function loadPhoto(file) {
  if(!file)return;
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)){setStatus('请选择 JPG、PNG 或 WebP 格式的照片。');return;}
  if(file.size>20*1024*1024){setStatus('照片超过 20 MB，请缩小后再选择。');return;}
  const token=++generation;setStatus('正在提取明暗边界…');
  let image;
  try {
   if(typeof createImageBitmap==='function')image=await createImageBitmap(file);
   else image=await new Promise((resolve,reject)=>{const img=new Image(),url=URL.createObjectURL(file);img.onload=()=>{URL.revokeObjectURL(url);resolve(img);};img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('decode'));};img.src=url;});
   if(token!==generation)return;
   const iw=image.width,ih=image.height;
   if(!iw||!ih||iw*ih>60000000)throw new Error('dimensions');
   const scale=Math.min(1,650/Math.max(iw,ih)),s=document.createElement('canvas');
   s.width=Math.max(8,Math.round(iw*scale));s.height=Math.max(8,Math.round(ih*scale));s.getContext('2d').drawImage(image,0,0,s.width,s.height);
   source=fieldFromCanvas(s); const count=extract();fit();
   $('source-label').textContent='照片线场 · '+iw+' × '+ih;
   setStatus(count ? '线场已生成。调整细节与弥散，寻找你想留下的轮廓。' : '这张照片的明暗边界较少。提高“轮廓细节”，或换一张对比更清晰的照片。');
  } catch(error) {
   if(token===generation)setStatus(error.message==='dimensions'?'图片像素过大，请缩小后重试。':'这张照片未能解码，请重新保存为 JPG、PNG 或 WebP 后再试。');
  } finally {if(image && image.close)image.close();$('photo').value='';}
 }
 function draw() {
  ctx.setTransform(ratio,0,0,ratio,0,0);ctx.globalCompositeOperation='source-over';ctx.fillStyle='#060a0f';ctx.fillRect(0,0,canvas.width/ratio,canvas.height/ratio);
  if(!source)return;
  const rgb=palettes[color].join(','), power=settings.light/60,diff=settings.diffusion/100;
  ctx.fillStyle=`rgba(${rgb},.16)`;
  for(const [x,y,s] of stars){ctx.globalAlpha=.25+s*.65;ctx.fillRect(x*width,y*height,s>.8?1.2:.6,s>.8?1.2:.6);}ctx.globalAlpha=1;
  const scale=Math.min((width-65)/source.w,(height-100)/source.h)*zoom;
  ctx.save();ctx.translate(width/2+panX,height/2+panY);ctx.scale(scale,scale);
  const pos=points.map(p=>{const sway=Math.sin(phase*.45+p.seed*32)*diff*3;return [p.x+Math.cos(p.a)*sway,p.y+Math.sin(p.a)*sway];});
  ctx.globalCompositeOperation='lighter';
  ctx.beginPath();for(const [a,b] of links){ctx.moveTo(...pos[a]);ctx.lineTo(...pos[b]);}
  ctx.strokeStyle=`rgba(${rgb},${Math.min(.65,.23*power)})`;ctx.lineWidth=.55/Math.sqrt(scale);ctx.stroke();
  ctx.beginPath();for(let i=0;i<points.length;i++){const p=points[i];if(p.seed>.6)continue;const [x,y]=pos[i];const r=(2+p.seed*5)*(1+diff);ctx.moveTo(x+r,y);ctx.arc(x,y,r,0,Math.PI*2);}
  ctx.fillStyle=`rgba(${rgb},${.016*power*(.3+diff)})`;ctx.fill();
  ctx.beginPath();for(let i=0;i<points.length;i++){const [x,y]=pos[i],p=points[i],r=(.35+p.strength*.55)*(1+.2*Math.sin(phase+p.seed*100));ctx.moveTo(x+r,y);ctx.arc(x,y,r,0,Math.PI*2);}
  ctx.fillStyle=`rgba(${rgb},${Math.min(.95,.58*power)})`;ctx.fill();
  if(diff>0){ctx.beginPath();for(let i=0;i<points.length;i+=3){const p=points[i],r=(5+p.seed*27)*diff,angle=p.seed*100+phase*.06,[x,y]=pos[i];ctx.moveTo(x+Math.cos(angle)*r+.4,y+Math.sin(angle)*r);ctx.arc(x+Math.cos(angle)*r,y+Math.sin(angle)*r,.4,0,Math.PI*2);}ctx.fillStyle=`rgba(${rgb},${.32*power})`;ctx.fill();}
  ctx.restore();ctx.globalCompositeOperation='source-over';
 }
 function tick(time) {frame=0;if(!paused&&!document.hidden){if(lastTime)phase+=Math.min((time-lastTime)/1000,.05);lastTime=time;draw();frame=requestAnimationFrame(tick);}else{lastTime=0;draw();}}
 function requestDraw(){if(!frame)frame=requestAnimationFrame(tick);}
 function pauseUI(){$('pause').textContent=paused?'继续流动':'暂停流动';$('pause').setAttribute('aria-pressed',String(paused));requestDraw();}
 $('photo').addEventListener('change',e=>loadPhoto(e.target.files[0]));
 let dragDepth=0;
 stage.addEventListener('dragenter',e=>{e.preventDefault();dragDepth++;stage.classList.add('dragging');});
 stage.addEventListener('dragover',e=>{e.preventDefault();e.dataTransfer.dropEffect='copy';});
 stage.addEventListener('dragleave',()=>{if(--dragDepth<=0){dragDepth=0;stage.classList.remove('dragging');}});
 stage.addEventListener('drop',e=>{e.preventDefault();dragDepth=0;stage.classList.remove('dragging');loadPhoto(e.dataTransfer.files[0]);});
 // Prevent a missed drop outside the stage from navigating away from the work.
 window.addEventListener('dragover',e=>e.preventDefault());window.addEventListener('drop',e=>e.preventDefault());
 ['detail','diffusion','light'].forEach(id=>$(id).addEventListener('input',()=>{settings[id]=Number($(id).value);$(id+'-value').value=settings[id];if(id==='detail'){clearTimeout(detailTimer);detailTimer=setTimeout(()=>{if(source){const count=extract();if(!count)setStatus('当前阈值下没有轮廓，请提高“轮廓细节”。');else setStatus('线场已更新。调整细节与弥散，寻找你想留下的轮廓。');}},100);}else requestDraw();}));
 document.querySelectorAll('[name=color]').forEach(r=>r.addEventListener('change',()=>{color=r.value;requestDraw();}));
 $('pause').onclick=()=>{paused=!paused;pauseUI();};$('fit').onclick=fit;$('demo').onclick=demo;
 $('reset').onclick=()=>{clearTimeout(detailTimer);Object.assign(settings,{detail:55,diffusion:35,light:60});for(const id of Object.keys(settings)){$(id).value=settings[id];$(id+'-value').value=settings[id];}color='ice';document.querySelector('[value=ice]').checked=true;extract();fit();setStatus('成像参数已复位，保留当前照片的线场。');};
 $('export').onclick=()=>{draw();$('export').disabled=true;canvas.toBlob(blob=>{$('export').disabled=false;if(!blob){setStatus('图像保存失败，请重试。');return;}const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='afterimage-nebula.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);},'image/png');};
 canvas.addEventListener('keydown',e=>{
  if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','Home'].includes(e.key))return;
  e.preventDefault();
  if(e.key==='Home'){fit();return;}
  if(e.key==='ArrowLeft')panX-=20;if(e.key==='ArrowRight')panX+=20;
  if(e.key==='ArrowUp')panY-=20;if(e.key==='ArrowDown')panY+=20;
  if(e.key==='+'||e.key==='=')zoom=Math.min(6,zoom*1.12);if(e.key==='-')zoom=Math.max(.4,zoom/1.12);
  panX=Math.max(-width*3,Math.min(width*3,panX));panY=Math.max(-height*3,Math.min(height*3,panY));requestDraw();
 });
 canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.4,Math.min(6,zoom*Math.exp(-e.deltaY*.001)));requestDraw();},{passive:false});
 canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});});
 canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;const old=pointers.get(e.pointerId),next={x:e.clientX,y:e.clientY};if(pointers.size===1){panX=Math.max(-width*3,Math.min(width*3,panX+next.x-old.x));panY=Math.max(-height*3,Math.min(height*3,panY+next.y-old.y));}else if(pointers.size===2){const other=[...pointers.entries()].find(([id])=>id!==e.pointerId)[1];const d0=Math.hypot(old.x-other.x,old.y-other.y),d1=Math.hypot(next.x-other.x,next.y-other.y);if(d0>5)zoom=Math.max(.4,Math.min(6,zoom*d1/d0));}pointers.set(e.pointerId,next);requestDraw();});
 ['pointerup','pointercancel','lostpointercapture'].forEach(type=>canvas.addEventListener(type,e=>pointers.delete(e.pointerId)));
 document.addEventListener('visibilitychange',()=>{lastTime=0;requestDraw();});
 reduced.addEventListener('change',e=>{paused=e.matches;pauseUI();});
 new ResizeObserver(size).observe(stage);demo();pauseUI();
})();
