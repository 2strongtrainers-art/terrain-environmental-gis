/* ATLAS-NAVIGATION-V6: one route, complete topic indexes, reusable search results. */
const V6_VIEWS = new Set(['home','library','categories','watch','free','archive','quality','do','learn','stacks','playbooks','explore']);
const V6_CONTROLS = {query:'searchInput',source:'sourceFilter',topic:'topicFilter',pricing:'pricingFilter',verification:'verificationFilter',priority:'priorityFilter',sort:'sortFilter'};
const V6_PARAMS = {query:'q',source:'source',topic:'topic',pricing:'price',verification:'verified',priority:'priority',sort:'sort'};
const V6_DEFAULTS = {query:'',source:'',topic:'',pricing:'',verification:'',priority:'',sort:'relevance',page:1,favoritesOnly:false};
const v6ScoreCache = new Map();
let v6ResultCache = {key:null,rows:[]};
let v6Restoring = false;
let v6LastFocus = null;
state.topic = '';
const topicName = t => t.section || 'General tools';
const V6_TOPICS = [...new Set(TOOLS.map(topicName))].sort((a,b)=>a.localeCompare(b));

function v6WriteURL(push=false) {
 if(v6Restoring)return;
 const url=new URL(location.href);
 for(const param of Object.values(V6_PARAMS))url.searchParams.delete(param);
 url.searchParams.delete('page');
 if(state.view==='library'){
  for(const [key,param] of Object.entries(V6_PARAMS))if(state[key]&&state[key]!==V6_DEFAULTS[key])url.searchParams.set(param,state[key]);
  if(state.page>1)url.searchParams.set('page',state.page);
 }
 url.hash=state.view;
 const next=url.pathname+url.search+url.hash;
 if(next!==location.pathname+location.search+location.hash)history[push?'pushState':'replaceState']({atlas:true},'',next);
}
function v6SyncControls(){
 v6TopicOptions();
 for(const [key,id] of Object.entries(V6_CONTROLS))$('#'+id).value=state[key]||'';
 $('#favOnly').classList.toggle('active',state.favoritesOnly);
 $('#favOnly').setAttribute('aria-pressed',String(state.favoritesOnly));
}
function showView(view,options={}){
 if(!V6_VIEWS.has(view)||!$('#view-'+view))return;
 clearTimeout(searchTimer);
 state.view=view;
 $$('.view').forEach(x=>x.classList.toggle('active',x.id==='view-'+view));
 $$('.navbtn').forEach(x=>{const active=(x.dataset.view||x.dataset.plusView)===view;x.classList.toggle('active',active);if(active)x.setAttribute('aria-current','page');else x.removeAttribute('aria-current')});
 $('#mobileNav').classList.remove('open');$('#menuBtn').setAttribute('aria-expanded','false');
 v6WriteURL(options.push!==false);
 if(view==='library'){v6SyncControls();renderLibrary()}
 if(view==='categories')renderCategories();
 if(view==='free')renderFree();
 if(view==='archive')renderArchive();
 if(options.scroll!==false)window.scrollTo({top:0,behavior:'instant'});
 trackAtlas('atlas_view',{view});
}
function v6RestoreRoute(){
 const params=new URLSearchParams(location.search),hash=location.hash.slice(1);
 const view=V6_VIEWS.has(hash)?hash:(params.has('q')?'library':'home');
 if(!$('#view-'+view))return; // The workflow views mount after core initialization.
 v6Restoring=true;
 state={...state,...V6_DEFAULTS};
 for(const [key,param] of Object.entries(V6_PARAMS)){
  const value=params.get(param);
  if(value===null)continue;
  if(key==='query')state.query=value.slice(0,500);
  else if(key==='topic'){if(V6_TOPICS.includes(value))state.topic=value}
  else if([...$('#'+V6_CONTROLS[key]).options].some(o=>o.value===value))state[key]=value;
 }
 state.page=Math.max(1,Math.min(Math.ceil(TOOLS.length/PAGE_SIZE),Number.parseInt(params.get('page'),10)||1));
 showView(view,{push:false});
 v6Restoring=false;
}
function v6StartSearch(query){
 clearTimeout(searchTimer);
 state={...state,...V6_DEFAULTS,query:String(query||'').trim().slice(0,500)};
 showView('library');
}
function syncStateFromControls(){
 const previousSource=state.source;
 for(const [key,id] of Object.entries(V6_CONTROLS))state[key]=$('#'+id).value.trim();
 if(previousSource!==state.source)state.topic='';
 state.page=1;
 v6SyncControls();renderLibrary();
}
function getFiltered(){
 const key=JSON.stringify([state.query,state.source,state.topic,state.pricing,state.verification,state.priority,state.sort,state.favoritesOnly,state.favoritesOnly?[...favorites]:null]);
 if(v6ResultCache.key===key)return v6ResultCache.rows;
 const norm=normalizeText(state.query);
 let parsed=null,scores=null;
 if(norm){
  let cached=v6ScoreCache.get(norm);
  if(!cached){const p=parseSmartQuery(state.query);cached={parsed:p,scores:new Map(TOOLS.map(t=>[t.id,scoreTool(t,p)]))};v6ScoreCache.set(norm,cached);if(v6ScoreCache.size>8)v6ScoreCache.delete(v6ScoreCache.keys().next().value)}
  parsed=cached.parsed;scores=cached.scores;
 }
 let arr=TOOLS.filter(t=>{
  if(state.source&&t.sourceCategory!==state.source&&!t.sourceCategories?.includes(state.source))return false;
  if(state.topic&&topicName(t)!==state.topic)return false;
  if(state.pricing&&t.pricing!==state.pricing)return false;
  if(state.verification==='not-live'&&t.verification==='Live verified')return false;
  if(state.verification&&state.verification!=='not-live'&&t.verification!==state.verification)return false;
  if(state.priority&&t.priority!==state.priority)return false;
  if(parsed?.explicitNoLogin&&!/Free - (no login|optional login)/i.test(t.accessType||''))return false;
  if(state.favoritesOnly&&!favorites.has(t.id))return false;
  return true;
 });
 if(parsed&&arr.length){
  const max=Math.max(...arr.map(t=>scores.get(t.id)));
  const floor=parsed.intent?Math.max(14,max*.16):5;
  let kept=arr.filter(t=>scores.get(t.id)>=floor);
  // A short relevant list is useful; filling it with unrelated sites is not.
  if(!kept.length&&!parsed.intent)kept=arr.filter(t=>scores.get(t.id)>3);
  kept.sort((a,b)=>scores.get(b.id)-scores.get(a.id)||a.name.localeCompare(b.name));
  arr=parsed.intent?kept.slice(0,30):kept;
 }
 if(state.sort==='az')arr.sort((a,b)=>a.name.localeCompare(b.name));
 else if(state.sort==='verified')arr.sort((a,b)=>(b.verification==='Live verified')-(a.verification==='Live verified')||a.name.localeCompare(b.name));
 else if(state.sort==='priority'){const p={High:3,Medium:2,Low:1};arr.sort((a,b)=>(p[b.priority]||0)-(p[a.priority]||0)||a.name.localeCompare(b.name))}
 v6ResultCache={key,rows:arr};
 return arr;
}
function v6TopicOptions(){
 const select=$('#topicFilter');
 if(select.dataset.source===state.source)return;
 select.dataset.source=state.source;
 const counts=new Map();TOOLS.filter(t=>!state.source||t.sourceCategory===state.source).forEach(t=>counts.set(topicName(t),(counts.get(topicName(t))||0)+1));
 select.innerHTML='<option value="">All topics</option>'+[...counts].sort((a,b)=>a[0].localeCompare(b[0])).map(([name,count])=>`<option value="${esc(name)}">${esc(name)} (${count})</option>`).join('');
}
function v6AfterRender(total){
 v6WriteURL();
 const active=Object.keys(V6_PARAMS).filter(k=>k!=='query'&&state[k]&&state[k]!==V6_DEFAULTS[k]);
 $('#activeFilters').innerHTML=active.map(k=>`<button class="chip" data-remove-filter="${k}" aria-label="Remove ${esc(k==='topic'?'topic: '+state[k]:state[k])} filter">${esc(state[k])} <span aria-hidden="true">×</span></button>`).join('');
 $('#filtersSummary').textContent=active.length?`Filters · ${active.length} active`:'Filters';
 $('#resultStatus').textContent=fmt(total)+(state.query?' matching tools':' tools')+(state.topic?' in '+state.topic:'');
 $('#favOnly').setAttribute('aria-pressed',String(state.favoritesOnly));
 if(!total){
  $('#toolGrid .empty p').textContent=state.favoritesOnly?'Save a tool with its star, then find it here. Favorites stay on this browser.':(active.length?'No tools match this search with these filters. Remove a filter or try a broader phrase.':'Try a tool name or a shorter task, or explore the topic index.');
 }
}
function v6OpenTopic(name){
 state={...state,...V6_DEFAULTS,topic:name};showView('library');
}
function renderCategories(){
 const groups={};TOOLS.forEach(t=>{groups[t.sourceCategory||'Other']=(groups[t.sourceCategory||'Other']||0)+1});
 $('#categoryGrid').innerHTML=Object.entries(groups).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`<button type="button" class="category" data-cat="${esc(k)}"><span class="count">${fmt(n)}</span><strong>${esc(k)}</strong><p>Browse this collection →</p></button>`).join('');
 $$('#categoryGrid [data-cat]').forEach(b=>b.onclick=()=>{state={...state,...V6_DEFAULTS,source:b.dataset.cat};showView('library')});
 const term=normalizeText($('#topicIndexSearch').value);
 const counts=new Map();TOOLS.forEach(t=>counts.set(topicName(t),(counts.get(topicName(t))||0)+1));
 const topics=[...counts].sort((a,b)=>a[0].localeCompare(b[0])).filter(([name])=>normalizeText(name).includes(term));
 $('#topicIndexCount').textContent=`${topics.length} of ${counts.size} topics`;
 $('#topicIndexGrid').innerHTML=topics.length?topics.map(([name,count])=>`<button class="topic-card" data-topic="${esc(name)}"><strong>${esc(name)}</strong><span>${fmt(count)} tools <span aria-hidden="true">↗</span></span></button>`).join(''):'<p>No topic matches that name. Try a broader word.</p>';
 $$('#topicIndexGrid [data-topic]').forEach(b=>b.onclick=()=>v6OpenTopic(b.dataset.topic));
}
function v6OpenGuide(){
 $('#atlasGuide').open=true;
 $('#newHere').scrollIntoView({behavior:'smooth',block:'center'});
 $('#commandInput').focus({preventScroll:true});
}
$('#jumpCommand').onclick=v6OpenGuide;
$('#friendMode').onclick=()=>{showView('home');v6OpenGuide()};
$('#heroSearchForm').addEventListener('submit',e=>{e.preventDefault();v6StartSearch($('#homeSearch').value)});
$('#topicIndexSearch').addEventListener('input',renderCategories);
$('#topicFilter').addEventListener('change',syncStateFromControls);
$('#searchInput').addEventListener('keydown',e=>{if(e.key==='Enter'){clearTimeout(searchTimer);syncStateFromControls();$('#searchInput').blur()}});
$('#activeFilters').addEventListener('click',e=>{const b=e.target.closest('[data-remove-filter]');if(!b)return;const key=b.dataset.removeFilter;state[key]=V6_DEFAULTS[key];if(key==='source')state.topic='';state.page=1;v6SyncControls();renderLibrary()});
$('#clearFilters').onclick=()=>{clearTimeout(searchTimer);state={...state,...V6_DEFAULTS};v6SyncControls();renderLibrary()};
$('#copyResults').onclick=async()=>{
 const b=$('#copyResults');v6WriteURL();
 try{await navigator.clipboard.writeText(location.href);b.textContent='Link copied';$('#resultStatus').textContent='Search link copied. Filters are included; personal favorites are not.';setTimeout(()=>b.textContent='Copy search link',2200)}catch{b.textContent='Use your browser’s share button'}
};
$('#homeTopics').onclick=()=>showView('categories');
$('#savedTools').onclick=()=>{state={...state,...V6_DEFAULTS,favoritesOnly:true};showView('library')};
document.addEventListener('click',e=>{
 const trigger=e.target.closest('button[onclick^="openDetail"]');if(trigger)v6LastFocus=trigger;
 if(!e.target.closest('.topbar')){$('#mobileNav').classList.remove('open');$('#menuBtn').setAttribute('aria-expanded','false')}
});
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'&&$('#mobileNav').classList.contains('open')){$('#mobileNav').classList.remove('open');$('#menuBtn').setAttribute('aria-expanded','false');$('#menuBtn').focus()}
 if(e.key!=='Tab'||!$('#detailModal').classList.contains('open'))return;
 const focusables=$$('#detailModal button,#detailModal a[href]');const first=focusables[0],last=focusables[focusables.length-1];
 if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
});
function closeModal(){
 const wasOpen=$('#detailModal').classList.contains('open');$('#detailModal').classList.remove('open');
 if(wasOpen&&v6LastFocus?.isConnected)v6LastFocus.focus();
}
window.browseSource=k=>{state={...state,...V6_DEFAULTS,source:k};showView('library')};
$('#browseRaw').onclick=()=>{state={...state,...V6_DEFAULTS,verification:'not-live'};showView('library')};
window.recoverVerified=()=>{state={...state,...V6_DEFAULTS,verification:'Live verified'};v6SyncControls();renderLibrary()};
window.showView=showView;
window.addEventListener('popstate',v6RestoreRoute);
window.addEventListener('hashchange',v6RestoreRoute);
window.Atlas={navigate:showView,search:v6StartSearch,restoreRoute:v6RestoreRoute};
v6TopicOptions();
v6RestoreRoute();
document.dispatchEvent(new Event('atlas:ready'));
