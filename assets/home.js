const cards = [...document.querySelectorAll('.entry')];
const search = document.querySelector('#search');
const filters = [...document.querySelectorAll('[data-filter]')];
const routes = {
 space: {title:'翠湖：电影身体的现象学漫游', href:'cuihu-phenomenology.html', type:'影评 / 从观看出发', description:'把“空间如何改变感知”放回电影，看看镜面、漫游与身体如何相遇。', query:'影评', category:'理论', next:'继续探索影评 →'},
 body: {title:'梅洛庞蒂的空间现象学核心概念', href:'merleau-ponty-space.html', type:'概念 / 从身体出发', description:'空间不只是坐标。跟着梅洛庞蒂，从身体的行动与知觉理解我们所处的世界。', query:'', category:'理论', next:'继续探索理论 →'},
 writing: {title:'“她”组诗', href:'ta-zuoshi.html', type:'文本 / 从创作出发', description:'把阅读的目光交给诗句，看看感受如何在文字、停顿与留白中形成。', query:'', category:'文本', next:'继续探索文本 →'}
};
let category='全部', selected='space', opened=false;
let pocket=[], insight=false;
try {
 const saved=JSON.parse(localStorage.getItem('tzz-reading-pocket')||'{}');
 const allowed=Object.values(routes);
 pocket=Array.isArray(saved.articles)?saved.articles.filter(x=>allowed.some(r=>r.href===x)).slice(0,3):[];
 insight=saved.insight===true;
} catch {}
function persist(){
 try {localStorage.setItem('tzz-reading-pocket',JSON.stringify({articles:pocket,insight}));return true;} catch {return false;}
}
function updateArchive(){
 const query=search.value.trim().toLocaleLowerCase();let count=0;
 cards.forEach(card=>{
  card.hidden=!(category==='全部'||card.dataset.category===category)||!card.dataset.title.toLocaleLowerCase().includes(query);
  if(!card.hidden)count++;
 });
 document.querySelector('.result-count').textContent=`${count} 篇内容 / 共 ${cards.length} 篇`;
 document.querySelector('.empty').hidden=count!==0;
 filters.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.filter===category)));
}
function renderPocket(){
 const list=document.querySelector('#pocket-list');list.replaceChildren();
 pocket.forEach(href=>{
  const item=Object.values(routes).find(r=>r.href===href);
  const li=document.createElement('li'),a=document.createElement('a'),button=document.createElement('button');
  a.href=item.href;a.textContent=item.title+' ↗';
  button.type='button';button.textContent='移除';button.className='text-button';button.setAttribute('aria-label','移除 '+item.title);
  button.addEventListener('click',()=>{pocket=pocket.filter(x=>x!==href);persist();renderPocket();});
  li.append(a,button);list.append(li);
 });
 if(insight){const li=document.createElement('li');li.className='saved-insight';li.textContent='留下的发现：空间，也在讲故事。';list.prepend(li);}
 document.querySelector('.reading-pocket').hidden=pocket.length===0&&!insight;
 document.querySelector('#keep-insight').setAttribute('aria-pressed',String(insight));
 document.querySelector('#keep-insight').textContent=insight?'✓ 已留下发现':'＋ 留下这个发现';
 const saved=pocket.includes(routes[selected].href);
 document.querySelector('#save-recommendation').setAttribute('aria-pressed',String(saved));
 document.querySelector('#save-recommendation').textContent=saved?'✓ 已放入阅读口袋':'＋ 稍后阅读';
 document.querySelector('#journey-feedback').textContent=pocket.length||insight?'你已经留下了自己的线索。接下来，沿着它继续阅读，或在目录里发现新的方向。':'文章目录随时开放。沿着刚才的方向继续，或重新选一个问题。';
}
function chooseRoute(key){
 selected=key;const route=routes[key];
 document.querySelectorAll('[data-route]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.route===key)));
 document.querySelector('#recommendation-title').textContent=route.title;
 document.querySelector('#recommendation-type').textContent=route.type;
 document.querySelector('#recommendation-desc').textContent=route.description;
 document.querySelector('#read-recommendation').href=route.href;
 document.querySelector('#continue-route').textContent=route.next;
 document.querySelector('#route-feedback').textContent='';renderPocket();
}
const discover=document.querySelector('#discover');
discover.addEventListener('click',()=>{
 opened=!opened;discover.setAttribute('aria-expanded',String(opened));
 document.querySelector('#discovery').hidden=!opened;
 discover.querySelector('.card-action').innerHTML=opened?'发现了另一种视角 <b>✓</b>':'点开，换个角度 <b>↗</b>';
 document.querySelector('.first-encounter').classList.toggle('opened',opened);
});
document.querySelector('#keep-insight').addEventListener('click',()=>{
 insight=!insight;const retained=persist();renderPocket();
 document.querySelector('#insight-status').textContent=insight?(retained?'已留下。下次回来，这个发现还在阅读口袋里。':'已留在本次页面；浏览器无法保存，下次回来可能需要重新添加。'):'已从阅读口袋移除。';
});
document.querySelectorAll('[data-route]').forEach(button=>button.addEventListener('click',()=>chooseRoute(button.dataset.route)));
document.querySelector('#save-recommendation').addEventListener('click',()=>{
 const href=routes[selected].href,exists=pocket.includes(href);
 pocket=exists?pocket.filter(x=>x!==href):[...pocket,href];const retained=persist();renderPocket();
 document.querySelector('#route-feedback').textContent=exists?'已从阅读口袋移除。':retained?'已放入阅读口袋，可以稍后再读。':'已留在本次页面；浏览器无法保存，下次回来可能需要重新添加。';
});
document.querySelector('#clear-pocket').addEventListener('click',()=>{pocket=[];insight=false;persist();renderPocket();document.querySelector('#show-all').focus();});
document.querySelector('#continue-route').addEventListener('click',()=>{category=routes[selected].category;search.value=routes[selected].query;updateArchive();});
document.querySelector('#show-all').addEventListener('click',()=>{category='全部';search.value='';updateArchive();});
filters.forEach(button=>button.addEventListener('click',()=>{category=button.dataset.filter;updateArchive();}));
search.addEventListener('input',updateArchive);
document.querySelector('#clear-search').addEventListener('click',()=>{category='全部';search.value='';updateArchive();search.focus();});
document.addEventListener('keydown',event=>{
 if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!['INPUT','TEXTAREA','BUTTON'].includes(document.activeElement.tagName)&&!document.activeElement.isContentEditable){event.preventDefault();search.focus();}
});
if('IntersectionObserver' in window){
 const observer=new IntersectionObserver(entries=>{
  entries.forEach(entry=>{if(entry.isIntersecting){document.querySelectorAll('[data-stop]').forEach(a=>{if(a.dataset.stop===entry.target.id)a.setAttribute('aria-current','step');else a.removeAttribute('aria-current');});}});
 },{rootMargin:'-10% 0px -45% 0px',threshold:0});
 ['start','routes','destination'].forEach(id=>observer.observe(document.getElementById(id)));
}
chooseRoute(selected);updateArchive();
