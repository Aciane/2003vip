(() => {
 document.body.classList.add('reader-page');
 const content = document.querySelector('.article-body, .main-content, main, .main-container, .container') || document.body;
 const headings = [...content.querySelectorAll('h2, h3')].filter(h => h.textContent.trim());
 const bar = document.createElement('div'); bar.className='reader-bar'; bar.setAttribute('aria-hidden','true');
 const tools = document.createElement('nav'); tools.className='reader-tools'; tools.setAttribute('aria-label','文章阅读工具');
 const home = document.createElement('a'); home.href='index.html#archive'; home.textContent='← 文章目录'; tools.append(home);
 if (headings.length) {
  const details = document.createElement('details');
  const summary = document.createElement('summary'); summary.textContent='章节目录'; details.append(summary);
  const toc = document.createElement('div'); toc.className='reader-toc';
  const title = document.createElement('strong'); title.textContent='本篇目录'; toc.append(title);
  headings.forEach((heading,index) => {
   if (!heading.id) { let id=`reader-section-${index}`; while(document.getElementById(id)) id+='-'; heading.id=id; }
   heading.style.scrollMarginTop='85px';
   const link=document.createElement('a');link.href=`#${heading.id}`;link.textContent=heading.textContent.trim();
   link.addEventListener('click',()=>{details.open=false;});toc.append(link);
  });
  details.append(toc);tools.append(details);
  document.addEventListener('keydown',event=>{if(event.key==='Escape')details.open=false;});
  document.addEventListener('click',event=>{if(!details.contains(event.target))details.open=false;});
 }
 const percent=document.createElement('span'); percent.className='reader-progress';percent.setAttribute('aria-label','阅读进度');tools.append(percent);
 const top=document.createElement('button');top.type='button';top.textContent='↑ 顶部';
 const scroller=content.classList.contains('main-content') && getComputedStyle(content).overflowY.match(/auto|scroll/) ? content : document.scrollingElement;
 top.addEventListener('click',()=>scroller.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));tools.append(top);
 document.body.append(bar,tools);
 function update(){const extent=scroller.scrollHeight-scroller.clientHeight;const value=extent>0?Math.min(100,Math.round(scroller.scrollTop/extent*100)):100;bar.style.width=value+'%';percent.textContent=value+'%';}
 (scroller===document.scrollingElement?window:scroller).addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);update();
})();
