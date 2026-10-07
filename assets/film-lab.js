// Illustrative spatial inference, not a model of viewers' measured responses.
(() => {
 const $=id=>document.getElementById(id);
 const reduce=matchMedia('(prefers-reduced-motion: reduce)');
 const svg=(body,label)=>`<svg viewBox="0 0 640 340" role="img" aria-label="${label}">${body}</svg>`;
 const text=(x,y,value,size=14,fill='#f4efdf')=>`<text x="${x}" y="${y}" text-anchor="middle" font-family="sans-serif" font-size="${size}" fill="${fill}">${value}</text>`;
 const person=(x,y,color='#bca16d',direction=1)=>`<g transform="translate(${x} ${y})"><circle cx="0" cy="-69" r="17" fill="${color}"/><path d="M-18-45q18-12 36 0l6 55h-48z" fill="${color}"/><path d="M-10 10v37m20-37v37" stroke="${color}" stroke-width="10"/>${text(direction*30,-65,direction>0?'→':'←',22)}</g>`;
 const shell=`<rect width="640" height="340" fill="#274b3d"/><path d="M0 275h640v65H0z" fill="#a68a5a"/><path d="M0 275h640" stroke="#d2b983"/>`;
 let shot=0,timer=null;
 function stopGeo(){if(timer){clearInterval(timer);timer=null;} $('geo-play').textContent='▶ 播放两镜头';$('geo-play').setAttribute('aria-pressed','false');}
 function geoState(){return {match:document.querySelector('input[name=entry]:checked').value==='match',location:$('geo-location').checked,distance:Number($('geo-distance').value)};}
 function renderGeo(){
  const state=geoState(),isA=shot===0;
  const direction=isA||state.match?1:-1;
  const start=isA?170:state.match?50:590,end=isA?515:state.match?310:330;
  const doorX=isA?515:state.match?20:535;
  const door=`<rect x="${doorX}" y="64" width="85" height="211" fill="#122e26" stroke="#cfb985" stroke-width="5"/>`;
  const set=isA?`<path d="M0 85h450M0 150h450M0 215h450" stroke="#476c55"/>`:`<rect x="225" y="65" width="155" height="115" fill="#809776" stroke="#b6bd97" stroke-width="6"/><path d="M303 65v115" stroke="#b6bd97"/><path d="M410 263v-55h135v55" fill="#536e50"/>`;
  const animation=timer&&!reduce.matches?`<animateTransform attributeName="transform" type="translate" values="0 0;${end-start} 0" dur="1.5s" fill="freeze"/>`:'';
  const fade=timer&&!reduce.matches?`<animate attributeName="opacity" values="${isA?'1;1;0':'0;1;1'}" keyTimes="0;0.15;1" dur="1.5s" fill="freeze"/>`:'';
  const figure=`<g>${animation}${fade}${person(timer&&!reduce.matches?start:(start+end)/2,221,'#dbc281',direction)}</g>`;
  const caption=state.location&&!isA?`<rect x="155" y="15" width="330" height="33" fill="#102b25"/>${text(320,37,`地点 B · 与 A 相距 ${state.distance} km`,13)}`:'';
  $('geo-screen').innerHTML=svg(shell+set+door+figure+caption+text(320,320,isA?'镜头 A：向右走出走廊':state.match?'镜头 B：从左边进入房间，继续向右':'镜头 B：从右边进入房间，改向左走',14),isA?'人物向右离开走廊':'人物进入另一拍摄地点');
  $('shot-counter').textContent=`镜头 ${isA?'A':'B'} / 2`;
  $('geo-shot-desc').textContent=isA?'走廊的右侧出口，为下一个镜头留下动作线索。':state.match?'运动方向与上一镜头一致；两个门口可能被理解为同一通路。':'运动方向改变；可能被理解为转身、改道或一次空间跳转。';
  document.querySelectorAll('[data-shot]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.shot)===shot)));
  $('distance-output').textContent=state.distance+' km';
  let title,desc,link;
  if(state.location){title='地点分离的信息变得明确。';desc=`第二地点被标注为距 A ${state.distance} km。即使动作匹配，观众也可能把剪辑理解为省略旅程或跨地点转场，而非隔壁房间。`;link='地点分离<br>转场／旅程省略';}
  else if(state.match){title='远距离拍摄，仍可能形成邻接感。';desc=`地点真实相距 ${state.distance} km，但出口、入口与运动方向构成连续线索。剪辑可以让它们被理解为一个可穿行的空间；该推断仍取决于前后文。`;link='推断的通路 →<br>动作衔接';}
  else{title='连接线索减弱，不等于空间断开。';desc='方向反转削弱直线行动的连续感，但人物也可能转了弯或转身。仅凭这个切镜，不能断言两个地点是否相邻。';link='关系待定 ···<br>需更多线索';}
  $('geo-graph').innerHTML=`<span class="graph-node">走廊 A</span><span class="graph-link">${link}</span><span class="graph-node">房间 B</span>`;
  $('geo-feedback').innerHTML=`<strong>${title}</strong>${desc}`;
 }
 $('geo-play').onclick=()=>{if(timer){stopGeo();renderGeo();return;}shot=0;timer=setInterval(()=>{shot=(shot+1)%2;renderGeo();},1600);$('geo-play').textContent='Ⅱ 暂停播放';$('geo-play').setAttribute('aria-pressed','true');renderGeo();};
 $('geo-next').onclick=()=>{stopGeo();shot=(shot+1)%2;renderGeo();};
 document.querySelectorAll('[data-shot]').forEach(b=>b.onclick=()=>{stopGeo();shot=Number(b.dataset.shot);renderGeo();});
 $('geo-distance').oninput=renderGeo;$('geo-location').onchange=renderGeo;
 document.querySelectorAll('[name=entry]').forEach(r=>r.onchange=renderGeo);
 document.addEventListener('visibilitychange',()=>{if(document.hidden){stopGeo();renderGeo();}});
 window.addEventListener('pagehide',stopGeo);
 // Parallel projection of fixed world coordinates onto the camera's horizontal basis.
 function projectedFrame(target,angle){
  const sin=Math.sin(angle*Math.PI/180),positions=[50-27*sin,50+27*sin];
  target.replaceChildren();const floor=document.createElement('div');floor.className='frame-floor';target.append(floor);
  positions.forEach((x,i)=>{const figure=document.createElement('div');figure.className='projected-person person-'+(i?'b':'a');figure.style.left=x+'%';figure.style.zIndex=String(i+1);const other=positions[1-i];figure.innerHTML=`<div class="face-arrow">${Math.abs(other-x)<5?'·':other>x?'→':'←'}</div><div class="head"></div><div class="torso"></div><div class="name">${i?'B':'A'}</div>`;target.append(figure);});
 }
 function renderAxis(){
  const angle=Number($('axis-angle').value),rad=angle*Math.PI/180,sin=Math.sin(rad),x=250+190*Math.cos(rad),y=150+90*sin;
  $('angle-output').textContent=angle+'°';$('camera-point').setAttribute('cx',x);$('camera-point').setAttribute('cy',y);$('camera-sight').setAttribute('x1',x);$('camera-sight').setAttribute('y1',y);$('camera-label').setAttribute('x',x);$('camera-label').setAttribute('y',Math.max(25,y-20));
  projectedFrame($('axis-reference'),90);projectedFrame($('axis-current'),angle);
  if(Math.abs(sin)<.15){$('axis-feedback').innerHTML='<strong>机位接近轴线：左右线索变弱。</strong>两个人的银幕横向位置接近，可能出现遮挡或前后叠置。这个中性位置不能像轴线两侧那样提供清晰的左右参照。';}
  else if(sin>0){$('axis-feedback').innerHTML='<strong>与参考机位同侧：左右关系保持。</strong>A 在银幕左侧，面向右；B 在右侧，面向左。固定人物关系在两镜头间得到较稳定的方向提示。';}
  else{$('axis-feedback').innerHTML='<strong>机位越过轴线：左右关系反转。</strong>A 现在在银幕右侧，B 在左侧，但人物在场景中的位置始终没有交换。越轴是方向线索的改变，不是空间连通性的改变。';}
 }
 $('axis-angle').oninput=renderAxis;
 const regions={
  left:{name:'左侧画外',cue:'人物注视画框左边',inference:'视线建立朝向左侧的关系，但单凭视线不能确定看的是谁，也不能确定距离。',reveal:'反打：左侧站着另一位人物',object:person(180,220,'#bca16d',1)},
  right:{name:'右侧画外',cue:'人物沿右边缘走出画面',inference:'出画动作提示人物继续进入右侧不可见区域；下一镜头才补充他去了哪里。',reveal:'下一镜头：人物走入外面的走廊',object:person(400,220,'#dbc281',1)},
  top:{name:'上侧画外',cue:'绳子从画框上边进入',inference:'绳子越过画框上边界，提示上方存在延续区域；它并未独自说明绳子的来源。',reveal:'抬高机位：梯子上的人握着绳子',object:'<path d="M235 90v180m80-180v180m-80-155h80m-80 40h80m-80 40h80m-80 40h80" stroke="#bca16d" stroke-width="8"/>'+person(275,165,'#dbc281',1)+'<path d="M290 145v135" stroke="#e7d4a5" stroke-width="4"/>'},
  bottom:{name:'下侧画外',cue:'一只手从画框下边伸入',inference:'身体的一部分跨越下边界，使我们推断其余部分位于画框下方，而非凭空消失。',reveal:'向下取景：一位蹲下的人正伸手',object:person(320,210,'#bca16d',1)+'<path d="M338 180l38-55" stroke="#bca16d" stroke-width="10"/>'},
  set:{name:'布景后方',cue:'字幕声效：门后传来敲门声',inference:'门遮挡视线，敲门声把不可见声源定位到布景后方。声源还未出现，因此仍需后续镜头确认。',reveal:'切到门的另一侧：一位访客正在敲门',object:'<rect x="380" y="50" width="90" height="225" fill="#142f26" stroke="#bca16d" stroke-width="5"/>'+person(320,225,'#bca16d',1)},
  camera:{name:'摄影机后方',cue:'人物看向摄影机附近，画外传来问话',inference:'视线与问话可提示摄影机这一侧有对话者。也可能是对观众的直接讲话；本实验的反打会提供新的判断依据。',reveal:'反打：原先机位这一侧的对话者进入画内',object:person(320,225,'#bca16d',1)}
 };
 let revealed=false;
 function renderOff(){
  const key=document.querySelector('[name=region]:checked').value,r=regions[key];
  const door='<rect x="470" y="50" width="100" height="225" fill="#122e26" stroke="#bca16d" stroke-width="5"/>';
  let cue='';
  if(key==='top')cue='<path d="M270 0v140" stroke="#e7d4a5" stroke-width="5"/>';
  if(key==='bottom')cue='<path d="M325 340v-70l30-28" stroke="#c9b180" stroke-width="14" fill="none"/>';
  if(key==='set')cue=text(520,170,'叩 · 叩',18,'#e7d4a5');
  if(key==='camera')cue=text(320,100,'“你在等谁？”',18,'#e7d4a5');
  const actorX=key==='right'?607:320;
  const actor=person(actorX,225,'#dbc281',key==='left'?-1:1);
  const first=shell+door+(key==='camera'?actor.replace(text(30,-65,'→',22),''):actor)+cue;
  const second=shell+(key==='set'?'':door)+r.object;
  $('off-screen').innerHTML=svg((revealed?second:first)+`<rect x="0" y="294" width="640" height="46" fill="#102b25"/>`+text(320,322,revealed?r.reveal:r.cue,14),revealed?r.reveal:r.cue);
  $('off-mode').textContent=revealed?'镜头 2 / 揭示':'镜头 1 / 线索';
  $('off-feedback').innerHTML=`<strong>${revealed?'刚才的画外，现在成为画内。':r.name+'：线索指向不可见区域。'}</strong>${revealed?'下一镜头补充了声源或动作延续的位置。画内／画外的边界随镜头改变；原先画面的一部分此时不再可见。':r.inference}`;
  $('off-reveal').disabled=revealed;$('off-reset').disabled=!revealed;
 }
 document.querySelectorAll('[name=region]').forEach(r=>r.onchange=()=>{revealed=false;renderOff();});
 $('off-reveal').onclick=()=>{revealed=true;renderOff();};$('off-reset').onclick=()=>{revealed=false;renderOff();};
 renderGeo();renderAxis();renderOff();
})();
