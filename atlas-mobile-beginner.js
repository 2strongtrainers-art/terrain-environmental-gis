(()=>{
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const capture=(event,props={})=>{try{if(localStorage.getItem('atlasAnalyticsOptOut')==='1')return;window.posthog?.capture?.(event,{atlas_discovery_version:'5.2-mobile-beginner',...props})}catch(_){}};
function clickNav(label){const target=$$('.navbtn,button').find(b=>(b.textContent||'').trim().toLowerCase()===label.toLowerCase());if(target){target.click();return true}return false}
function quickSearch(q,label){const library=$('[data-view="library"]');if(library)library.click();setTimeout(()=>{const i=$('#searchInput');if(!i)return;i.value=q;i.dispatchEvent(new Event('input',{bubbles:true}));capture('atlas_beginner_choice',{choice:label,query:q});window.scrollTo({top:0,behavior:'instant'});},70)}
function mount(){
 if($('#atlasBeginnerStart')||!$('#view-home'))return;
 const host=document.createElement('section');host.id='atlasBeginnerStart';host.className='atlas-beginner';host.setAttribute('aria-label','Start here');
 host.innerHTML=`<div class="beginner-kicker">NEW HERE?</div><h2>Not sure what to search?</h2><p class="beginner-sub">Pick what sounds closest. Atlas will take you somewhere useful.</p>
 <div class="beginner-grid">
  <button class="beginner-card" data-beginner="useful"><span>✓</span><b>Do something useful</b><small>Tools for work, life, business and everyday tasks</small></button>
  <button class="beginner-card" data-beginner="create"><span>✦</span><b>Make something</b><small>Video, images, websites, writing and creator tools</small></button>
  <button class="beginner-card" data-beginner="learn"><span>↗</span><b>Learn something</b><small>AI, Python, business, science and tutorials</small></button>
  <button class="beginner-card" data-beginner="watch"><span>▶</span><b>Watch or listen</b><small>Free legal video, live TV, documentaries and streams</small></button>
  <button class="beginner-card" data-beginner="bored"><span>?</span><b>I’m bored</b><small>Interesting, weird, visual and fun corners of the web</small></button>
  <button class="beginner-card surprise" data-beginner="surprise"><span>🎲</span><b>Surprise me</b><small>No decision needed — just show me something interesting</small></button>
 </div>
 <div class="beginner-quick"><strong>Quick starts</strong><div class="beginner-chips">
  <button data-q="short social video editor AI voice">Make a Reel</button><button data-q="website builder analytics payment">Build a Website</button><button data-q="free no login tool">Actually Free</button><button data-q="live nature animal cams">Live Cams</button><button data-q="learn Python coding course">Learn Python</button><button data-q="grant funding research GIS mapping">Research a Grant</button>
 </div></div>`;
 const home=$('#view-home');const anchor=home.querySelector('.hero,section,.card');if(anchor)anchor.insertAdjacentElement('afterend',host);else home.prepend(host);
 host.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.q)return quickSearch(b.dataset.q,b.textContent.trim());const c=b.dataset.beginner;capture('atlas_beginner_choice',{choice:c});if(c==='watch'){clickNav('Watch');return}if(c==='learn'){if(!clickNav('Learn'))quickSearch('tutorial course reference education','Learn something');return}if(c==='create'){if(!clickNav('Do'))quickSearch('video image website creator tools','Make something');return}if(c==='useful'){if(!clickNav('Do'))quickSearch('useful productivity business utility tools','Do something useful');return}if(c==='bored'){if(!clickNav('Explore'))quickSearch('interesting weird fun useful sites',"I'm bored");return}if(c==='surprise'){const s=$$('button').find(x=>/surprise me/i.test(x.textContent||'')&&x!==b);if(s)s.click();else quickSearch(['live nature animal cams','NASA space science streams','interactive map earth','browser games free','visual interactive experiment'][Math.floor(Math.random()*5)],'Surprise me')}});
 capture('atlas_beginner_impression',{viewport:innerWidth});
}
function styles(){if($('#atlasBeginnerStyles'))return;const s=document.createElement('style');s.id='atlasBeginnerStyles';s.textContent=`
.atlas-beginner{margin:18px 0 28px;padding:22px;border:1px solid var(--line,#e5e7eb);border-radius:22px;background:linear-gradient(180deg,#fff,#f8fafc)}.beginner-kicker{font-size:11px;font-weight:800;letter-spacing:.12em;color:#475467}.atlas-beginner h2{margin:4px 0 6px;font-size:clamp(24px,5vw,34px);letter-spacing:-.03em}.beginner-sub{margin:0 0 16px;color:var(--muted,#667085)}.beginner-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.beginner-card{appearance:none;text-align:left;border:1px solid #d0d5dd;background:#fff;border-radius:16px;padding:15px;min-height:116px;color:inherit;font:inherit;cursor:pointer}.beginner-card span{display:block;font-size:20px;margin-bottom:9px}.beginner-card b{display:block;font-size:15px;margin-bottom:4px}.beginner-card small{display:block;color:#667085;line-height:1.35}.beginner-card.surprise{background:#101828;color:#fff;border-color:#101828}.beginner-card.surprise small{color:#d0d5dd}.beginner-quick{margin-top:16px}.beginner-quick>strong{font-size:13px}.beginner-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:8px}.beginner-chips button{border:1px solid #d0d5dd;background:#fff;border-radius:999px;padding:9px 12px;min-height:40px;font:inherit;font-size:13px;cursor:pointer}
@media(max-width:680px){.atlas-beginner{margin:12px -2px 22px;padding:16px;border-radius:18px}.beginner-kicker{font-size:10px}.atlas-beginner h2{font-size:27px;line-height:1.05}.beginner-sub{font-size:14px}.beginner-grid{grid-template-columns:1fr 1fr;gap:8px}.beginner-card{min-height:132px;padding:13px;touch-action:manipulation}.beginner-card b{font-size:14px}.beginner-card small{font-size:12px}.beginner-chips{display:grid;grid-template-columns:1fr 1fr}.beginner-chips button{min-height:46px;border-radius:12px;padding:10px}.atlas-beginner button:focus-visible{outline:3px solid #84adff;outline-offset:2px}}
@media(max-width:370px){.beginner-grid{grid-template-columns:1fr}.beginner-card{min-height:106px}}
`;document.head.appendChild(s)}
styles();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(mount,120));else setTimeout(mount,120);
})();
