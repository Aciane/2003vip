const cards=[...document.querySelectorAll('.entry')],search=document.querySelector('#search'),filters=[...document.querySelectorAll('[data-filter]')];
let category='全部',pocket=[],insight=false;
const notes=[...document.querySelectorAll('.save-note')];
try{const saved=JSON.parse(localStorage.getItem('tzz-reading-pocket')||'{}');pocket=Array.isArray(saved.articles)?saved.articles.filter(href=>notes.some(n=>n.dataset.href===href)):[];insight=saved.insight===true;}catch{}
function persist(){try{localStorage.setItem('tzz-reading-pocket',JSON.stringify({articles:pocket,insight}));return true;}catch{return false;}}
function renderPocket(){
 const list=document.querySelector('#pocket-list');list.replaceChildren();
 if(insight){const li=document.createElement('li');li.textContent='留下的观察：距离改变，关系也在改变。';list.append(li);}
 pocket.forEach(href=>{const note=notes.find(n=>n.dataset.href===href);const li=document.createElement('li'),a=document.createElement('a'),remove=document.createElement('button');a.href=href;a.textContent=note.dataset.title+' ↗';remove.className='text-button';remove.textContent='移除';remove.setAttribute('aria-label','移除 '+note.dataset.title);remove.onclick=()=>{pocket=pocket.filter(x=>x!==href);persist();renderPocket();};li.append(a,remove);list.append(li);});
 document.querySelector('.reading-pocket').hidden=!pocket.length&&!insight;
 notes.forEach(n=>{const saved=pocket.includes(n.dataset.href);n.setAttribute('aria-pressed',String(saved));n.textContent=saved?'✓ 已放入阅读口袋':'＋ 稍后阅读';});
 document.querySelector('#keep-insight').setAttribute('aria-pressed',String(insight));document.querySelector('#keep-insight').textContent=insight?'✓ 已留下观察':'＋ 留下这个观察';
}
notes.forEach(n=>n.onclick=()=>{pocket=pocket.includes(n.dataset.href)?pocket.filter(x=>x!==n.dataset.href):[...pocket,n.dataset.href];const saved=persist();renderPocket();document.querySelector('#journey-feedback').textContent=saved?'阅读口袋已更新，随时可以继续。':'已留在本次页面；浏览器未允许持久保存。';});
document.querySelector('#keep-insight').onclick=()=>{insight=!insight;const saved=persist();renderPocket();document.querySelector('#insight-status').textContent=insight?(saved?'观察已留下。':'已留在本次页面；浏览器未允许持久保存。'):'观察已移除。';};
document.querySelector('#clear-pocket').onclick=()=>{pocket=[];insight=false;persist();renderPocket();document.querySelector('#show-all').focus();};
function updateArchive(){const query=search.value.trim().toLocaleLowerCase();let count=0;cards.forEach(c=>{c.hidden=!(category==='全部'||c.dataset.category===category)||!c.dataset.title.toLocaleLowerCase().includes(query);if(!c.hidden)count++;});document.querySelector('.result-count').textContent=`${count} 篇内容 / 共 ${cards.length} 篇`;document.querySelector('.empty').hidden=count!==0;filters.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===category)));}
filters.forEach(b=>b.onclick=()=>{category=b.dataset.filter;updateArchive();});search.oninput=updateArchive;
function reset(){category='全部';search.value='';updateArchive();}
document.querySelector('#clear-search').onclick=()=>{reset();search.focus();};document.querySelector('#show-all').onclick=reset;
const distance=document.querySelector('#view-distance'),position=document.querySelector('#view-position'),surface=document.querySelector('.viewfinder'),art=document.querySelector('.scene-art'),frame=document.querySelector('.crop-frame');
function compose(){const d=Number(distance.value)/100,x=Number(position.value)/100;art.style.transform=`scale(${1+d*.85}) translateX(${-x*10}%)`;frame.style.inset=`${26+d*22}px ${26+d*40}px`;document.querySelector('.frame-label').textContent=`距离 ${Math.round(d*100)} / 视点 ${Math.round(x*100)}`;surface.classList.add('explored');}
distance.oninput=compose;position.oninput=compose;
let dragging=false;
surface.style.touchAction='pan-y';
surface.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse'||e.pointerType==='pen'){dragging=true;surface.setPointerCapture(e.pointerId);surface.classList.add('dragging');}});
surface.addEventListener('pointermove',e=>{if(!dragging)return;const r=surface.getBoundingClientRect();position.value=Math.max(-100,Math.min(100,((e.clientX-r.left)/r.width-.5)*200));compose();});
function end(){dragging=false;surface.classList.remove('dragging');}
surface.addEventListener('pointerup',end);surface.addEventListener('pointercancel',end);
renderPocket();updateArchive();
