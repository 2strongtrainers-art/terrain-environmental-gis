from pathlib import Path
import base64, gzip, hashlib, html, json, re

ROOT = Path('.')
SHELL_FILES = [ROOT / f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA_FILES = [ROOT / f'atlas-src/data-{i:03d}.txt' for i in range(9)]
POSTHOG_TOKEN = 'phc_pBipv2roqvT6HULpBA5Z4H2N63cwaUkRqgYmguFk3Zbm'
ATLAS_URL = 'https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/'
CONTACT_EMAIL = '2strongtrainers@gmail.com'

shell = ''.join(p.read_text() for p in SHELL_FILES)
data_b64 = ''.join(p.read_text().strip() for p in DATA_FILES)
records = json.loads(gzip.decompress(base64.b64decode(data_b64)))
assert len(records) == 1834, len(records)
assert sum(1 for r in records if r[10] == 'Live verified') == 1529
assert '__DATA_B64__' in shell


def once(old, new, label):
    global shell
    n = shell.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly 1 occurrence, found {n}')
    shell = shell.replace(old, new, 1)


def regex_once(pattern, replacement, label, flags=0):
    global shell
    shell2, n = re.subn(pattern, replacement, shell, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly 1 regex match, found {n}')
    shell = shell2


if 'ATLAS-CRO-V2' not in shell:
    # --- Search/social metadata ---
    once(
        '<title>Nick’s Digital Atlas — AI, Tools & Useful Websites</title>\n<meta name="description" content="A searchable digital atlas of AI tools, websites, research resources, design tools, gaming tools, and learning resources.">',
        f'''<title>Nick’s Digital Atlas — 1,834 AI Tools & Useful Websites</title>
<meta name="description" content="Browse 1,834 AI tools and useful websites by goal, category, price and verification status. 1,529 destinations were live-checked on September 3, 2026.">
<link rel="canonical" href="{ATLAS_URL}">
<link rel="sitemap" type="application/xml" href="{ATLAS_URL}sitemap.xml">
<meta property="og:type" content="website">
<meta property="og:title" content="Nick’s Digital Atlas — 1,834 AI Tools & Useful Websites">
<meta property="og:description" content="Find the right tool or useful website by goal, category, price or verification status.">
<meta property="og:url" content="{ATLAS_URL}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Nick’s Digital Atlas — 1,834 AI Tools & Useful Websites">
<meta name="twitter:description" content="Find the right tool or useful website by goal, category, price or verification status.">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"Nick’s Digital Atlas","url":"{ATLAS_URL}","description":"A searchable directory of AI tools and useful websites organized by goal, category, price and verification status.","potentialAction":{{"@type":"SearchAction","target":"{ATLAS_URL}#library","query-input":"required name=search_term_string"}}}}</script>''',
        'head metadata'
    )

    # --- Hero and first-impression clarity ---
    once(
        '<div class="eyebrow">Verified discovery • 1,834 useful resources</div>\n  <h1>Your map to the best AI tools & resources.</h1>\n  <p>A curated, searchable atlas built to get you from an idea to the right tool faster. Explore by goal, category, verification status, or simply tell the Atlas what you want to accomplish.</p>\n  <div class="actions"><button class="btn primary" data-view="library">Search the library</button><button class="btn ghost" id="jumpCommand">New here? Start here</button></div>',
        '<div class="eyebrow">1,834 tools & useful websites • 1,529 live verified</div>\n  <h1>Find the right tool or useful website for what you want to do.</h1>\n  <p>Browse 1,834 resources by goal, category, price or verification status. 1,529 destinations were live-checked on September 3, 2026.</p>\n  <div class="actions"><button class="btn primary" data-view="library" id="heroBrowse">Browse all 1,834 tools</button><button class="btn ghost" id="jumpCommand">Help me choose</button></div>',
        'hero copy'
    )
    once('<div class="stat"><b>4</b><span>connected Web Surfers source libraries</span></div>',
         '<div class="stat"><b>4</b><span>explicitly audited Free • No Login tools</span></div>', 'fourth stat')

    # --- Accurate beginner-router framing ---
    once(
        '<strong>🧭 New here? This is the best place to start.</strong>\n  <p>Tell the guide what you want in ordinary language—“Help me make a video,” “Research this topic,” or “Find me a free tool.”</p>\n  <div class="command">\n   <label for="commandInput"><b>Family AI Command Center</b></label>\n   <div class="commandbox"><input id="commandInput" placeholder="What do you want to accomplish?" autocomplete="off"><button class="btn blue" id="routeBtn">Find my route</button></div>',
        '<strong>🧭 New here? Start here.</strong>\n  <p>Describe the outcome—not the software. The Atlas will show matching tools and categories.</p>\n  <div class="command">\n   <label for="commandInput"><b>Tell the Atlas what you want to do</b></label>\n   <div class="commandbox"><input id="commandInput" placeholder="Example: make a short video from five photos" autocomplete="off"><button class="btn blue" id="routeBtn">Show matching tools</button></div>',
        'beginner router copy'
    )

    # --- Move discovery before explanatory content ---
    old_goal = ''' <div class="section">
  <div class="sectionhead"><div><h2>Try something right now</h2><p>Goal-first routes mirror the Notion Atlas.</p></div></div>
  <div class="grid" id="goalGrid"></div>
 </div>
'''
    if shell.count(old_goal) != 1:
        raise SystemExit('goal block mismatch')
    shell = shell.replace(old_goal, '', 1)
    anchor = '''  </div>
 </div>
 <div class="section">
  <div class="sectionhead"><div><h2>What is the Digital Atlas??</h2><p>Think of it as a well-organized digital toolbox.</p></div></div>'''
    moved = '''  </div>
 </div>
 <div class="section discovery-first">
  <div class="sectionhead"><div><h2>Start with what you want to do</h2><p>Not sure what to search? Pick an outcome and explore matching tools.</p></div></div>
  <div class="grid" id="goalGrid"></div>
 </div>
 <div class="section">
  <div class="sectionhead"><div><h2>What is the Digital Atlas?</h2><p>Think of it as a well-organized digital toolbox.</p></div></div>'''
    once(anchor, moved, 'move discovery')

    # --- Experience cards become keyboard-native buttons ---
    replacements = [
        ('<div class="card click" id="friendMode"><div class="icon">🌱</div><h3>Friend Mode</h3><p>Best if you do not know where to start. Describe your goal in normal language.</p></div>',
         '<button type="button" class="card click" id="friendMode"><div class="icon">🌱</div><h3>Friend Mode</h3><p>Best if you do not know where to start. Describe your goal in normal language.</p></button>', 'friend card'),
        ('<div class="card click" data-view="categories"><div class="icon">🧩</div><h3>Browse by goal</h3><p>Best if you know the kind of task you want to complete.</p></div>',
         '<button type="button" class="card click" data-view="categories"><div class="icon">🧩</div><h3>Browse by goal</h3><p>Best if you know the kind of task you want to complete.</p></button>', 'browse card'),
        ('<div class="card click" data-view="archive"><div class="icon">⚡</div><h3>Power User Mode</h3><p>Best when you want the broadest coverage and the raw source layers.</p></div>',
         '<button type="button" class="card click" data-view="archive"><div class="icon">⚡</div><h3>Source Archive</h3><p>Best when you want the broadest coverage and the original source layers.</p></button>', 'archive card'),
        ('<div class="card click" data-view="library"><div class="icon">🔎</div><h3>Master Library</h3><p>Search every indexed launchable URL in one fast interface.</p></div>',
         '<button type="button" class="card click" data-view="library"><div class="icon">🔎</div><h3>All Tools</h3><p>Search every indexed launchable URL in one fast interface.</p></button>', 'library card'),
    ]
    for old, new, label in replacements:
        once(old, new, label)

    # --- Add transparent revenue path without selling verification/ranking ---
    partner_block = f'''
 <div class="section">
  <div class="callout purple partner-callout">
   <div><strong>Building a useful tool?</strong><p>Atlas accepts partnership and sponsorship inquiries. Paid placements are clearly labeled and never change verification status or editorial ranking.</p></div>
   <a class="btn outline" id="partnerCta" href="mailto:{CONTACT_EMAIL}?subject=Digital%20Atlas%20partnership%20inquiry">Partner with Atlas</a>
  </div>
 </div>
'''
    once(' <div class="section">\n   <div class="sectionhead"><div><h2>Prompts that make the guide more useful</h2></div></div>',
         partner_block + ' <div class="section">\n   <div class="sectionhead"><div><h2>Prompts that make the guide more useful</h2></div></div>', 'partner block')

    # --- Search/discovery UI improvements ---
    once('<input class="control query" id="searchInput" placeholder="Search tools, descriptions, categories…" aria-label="Search library">',
         '<input class="control query" id="searchInput" placeholder="Search tools, tasks or websites…" aria-label="Search library" autocomplete="off">', 'search placeholder')
    once(' </div>\n </div>\n <div class="filtermeta"><div><b id="resultCount"></b> <span id="filterSummary"></span></div>',
         ' </div>\n  <div class="quicksearch" aria-label="Suggested searches"><span>Try:</span><button type="button" data-quick-search="video">video</button><button type="button" data-quick-search="research">research</button><button type="button" data-quick-search="website">website</button><button type="button" data-quick-search="mapping">mapping</button><button type="button" data-quick-search="resume">resume</button><button type="button" data-quick-search="image">image</button></div>\n </div>\n <div class="filtermeta"><div><b id="resultCount" aria-live="polite" aria-atomic="true"></b> <span id="filterSummary"></span></div>', 'quick searches and result live region')

    # --- Data Quality trust + analytics privacy controls ---
    trust_add = '''
 <div class="section trust-grid">
  <div class="callout green"><strong>What “Live verified” means</strong><p>A live-verified destination successfully rendered during the latest automated browser audit. This verifies availability—not every feature, claim, price, privacy policy or security practice of the third-party service.</p></div>
  <div class="callout gray"><strong>Editorial & commercial policy</strong><p>Verification status cannot be purchased. Sponsorships or affiliate relationships, when present, are labeled and do not change verification status or organic editorial ranking.</p></div>
 </div>
 <div class="section"><div class="callout gray"><strong>Anonymous product analytics</strong><p>Atlas uses lightweight PostHog product analytics to measure actions such as searches, filters and outbound tool visits. Search text itself is not sent. Session recording is disabled.</p><div class="actions"><button type="button" class="btn outline" id="analyticsOptOut">Disable analytics on this device</button><span class="note" id="analyticsStatus" aria-live="polite"></span></div></div></div>
'''
    once(' <div class="section">\n  <div class="callout gray"><b>Build provenance:</b>', trust_add + ' <div class="section">\n  <div class="callout gray"><b>Build provenance:</b>', 'trust blocks')

    # --- Footer: sharing, crawlable collection links, partnership route ---
    once('<footer class="footer"><b>Nick’s Digital Atlas</b> · Built from connected source libraries and curated verification data. External websites are third-party services. Data snapshot: <span id="footerDate"></span>.</footer>',
         '<footer class="footer"><div><b>Nick’s Digital Atlas</b> · Built from connected source libraries and curated verification data. External websites are third-party services. Data snapshot: <span id="footerDate"></span>.</div><div class="footerlinks"><a href="collections/ai-tools/">AI tools</a><a href="collections/design-tools/">Design tools</a><a href="collections/education-tools/">Education tools</a><a href="collections/gaming-tools/">Gaming tools</a><a href="collections/live-verified-tools/">Live verified</a><a href="collections/free-no-login/">Free • No Login</a><a href="partners/">Partner policy</a><button type="button" class="linkbutton" id="shareAtlas">Share Atlas</button></div></footer>', 'footer links')

    # --- Analytics bootstrap: lazy-load SDK after first paint; no session replay ---
    analytics = f'''
<script id="atlasAnalytics">
/* ATLAS-CRO-V2 analytics: custom events only, session replay disabled */
window.__atlasAnalyticsQueue=[];
window.trackAtlas=function(name,props){{
  if(localStorage.getItem('atlasAnalyticsOptOut')==='1') return;
  const payload=Object.assign({{atlas_version:'cro-v2',path:location.pathname,view:(location.hash||'#home').slice(1)}},props||{{}});
  if(window.posthog&&typeof window.posthog.capture==='function') window.posthog.capture(name,payload);
  else window.__atlasAnalyticsQueue.push([name,payload]);
}};
(function(t,e){{var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){{function g(t,e){{var o=e.split('.');2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}}(p=t.createElement('script')).type='text/javascript',p.crossOrigin='anonymous',p.async=!0,p.src=s.api_host.replace('.i.posthog.com','-assets.i.posthog.com')+'/static/array.js',(r=t.getElementsByTagName('script')[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a='posthog',u.people=u.people||[],o='capture opt_out_capturing has_opted_out_capturing opt_in_capturing'.split(' '),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])}},e.__SV=1)}})(document,window.posthog||[]);
function initAtlasAnalytics(){{
 if(localStorage.getItem('atlasAnalyticsOptOut')==='1') return;
 posthog.init('{POSTHOG_TOKEN}',{{api_host:'https://us.i.posthog.com',person_profiles:'identified_only',autocapture:false,capture_pageview:false,capture_pageleave:true,disable_session_recording:true,persistence:'localStorage'}});
 const queued=window.__atlasAnalyticsQueue.splice(0); queued.forEach(x=>posthog.capture(x[0],x[1]));
 trackAtlas('atlas_page_loaded',{{referrer_host:(()=>{{try{{return new URL(document.referrer).hostname}}catch{{return ''}}}})()}});
}}
if('requestIdleCallback' in window)requestIdleCallback(initAtlasAnalytics,{{timeout:1800}});else setTimeout(initAtlasAnalytics,900);
</script>
'''
    once('\n<script>\nconst DATA_B64="__DATA_B64__";', '\n' + analytics + '<script>\nconst DATA_B64="__DATA_B64__";', 'analytics bootstrap')

    # --- Goal and category semantics + analytics ---
    once('$("#goalGrid").innerHTML=goals.map(g=>`<div class="card click" data-goal="${g[3]}"><div class="icon">${g[0]}</div><h3>${g[1]}</h3><p>${g[2]}</p></div>`).join("");\n$$("[data-goal]").forEach(x=>x.onclick=()=>applyGoal(x.dataset.goal));',
         '$("#goalGrid").innerHTML=goals.map(g=>`<button type="button" class="card click" data-goal="${g[3]}"><div class="icon">${g[0]}</div><h3>${g[1]}</h3><p>${g[2]}</p></button>`).join("");\n$$("[data-goal]").forEach(x=>x.onclick=()=>{trackAtlas("atlas_goal_select",{goal:x.dataset.goal});applyGoal(x.dataset.goal)});', 'goal buttons')

    old_cat = '$("#categoryGrid").innerHTML=Object.entries(groups).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`<div class="category" data-cat="${esc(k)}"><span class="count">${fmt(n)}</span><strong>${esc(k)}</strong><p style="color:#667085;margin:5px 0 0">Browse ${fmt(n)} indexed entries →</p></div>`).join("");'
    new_cat = '$("#categoryGrid").innerHTML=Object.entries(groups).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`<button type="button" class="category" data-cat="${esc(k)}"><span class="count">${fmt(n)}</span><strong>${esc(k)}</strong><p style="color:#667085;margin:5px 0 0">Browse ${fmt(n)} indexed entries →</p></button>`).join("");'
    once(old_cat, new_cat, 'category buttons')

    # --- Navigation and high-value event instrumentation ---
    once('function showView(view){\n state.view=view;', 'function showView(view){\n state.view=view;\n trackAtlas("atlas_view",{view});', 'view tracking')
    once('$("#jumpCommand").onclick=()=>{$("#newHere").scrollIntoView({behavior:"smooth",block:"center"});setTimeout(()=>$("#commandInput").focus(),350)};',
         '$("#jumpCommand").onclick=()=>{trackAtlas("atlas_help_me_choose",{});$("#newHere").scrollIntoView({behavior:"smooth",block:"center"});setTimeout(()=>$("#commandInput").focus(),350)};\n$("#heroBrowse").addEventListener("click",()=>trackAtlas("atlas_hero_cta",{cta:"browse_all"}));', 'hero tracking')

    # Route command: preserve privacy by logging length/routes, not text.
    once(' const picks=top.length?top:[["research",ROUTES.research,1],["design",ROUTES.design,1],["automation",ROUTES.automation,1]];\n $("#routeSuggestions").innerHTML=',
         ' const picks=top.length?top:[["research",ROUTES.research,1],["design",ROUTES.design,1],["automation",ROUTES.automation,1]];\n trackAtlas("atlas_command_submit",{query_length:q.length,matched_routes:picks.map(x=>x[0]).join(",")});\n $("#routeSuggestions").innerHTML=', 'command tracking')

    # --- Search: normalization, aliases and one-edit typo tolerance ---
    search_helpers = r'''
const SEARCH_ALIASES={
  photo:["image","picture"],photos:["image","picture"],picture:["image","photo"],
  movie:["video"],film:["video"],website:["site","web"],site:["website","web"],
  automate:["automation","workflow"],automation:["workflow","agent"],study:["research","learn"],
  researching:["research"],cv:["resume"],mapping:["map","gis"],gis:["map","mapping"],
  voice:["audio","speech"],audio:["voice","sound"],logo:["branding","design"],
  slides:["presentation"],presentation:["slides"],write:["writing","writer"],writer:["writing"]
};
function normalizeText(s){return String(s??"").normalize("NFKD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
function oneEditAway(a,b){
 if(a===b)return true;if(Math.abs(a.length-b.length)>1)return false;
 let i=0,j=0,edits=0;
 while(i<a.length&&j<b.length){if(a[i]===b[j]){i++;j++;continue}if(++edits>1)return false;if(a.length>b.length)i++;else if(b.length>a.length)j++;else{i++;j++;}}
 return edits+(i<a.length||j<b.length?1:0)<=1;
}
const SEARCH_INDEX=new Map(TOOLS.map(t=>{const text=normalizeText([t.name,t.description,t.sourceCategory,t.section,t.subsection,t.curatedCategory,t.pricing].join(" "));return [t.id,{text,tokens:[...new Set(text.split(/\s+/).filter(Boolean))]}]}));
function matchesQuery(t,q){
 const terms=normalizeText(q).split(/\s+/).filter(Boolean),idx=SEARCH_INDEX.get(t.id);if(!terms.length)return true;
 return terms.every(term=>{
   const candidates=[term,...(SEARCH_ALIASES[term]||[])];
   return candidates.some(c=>idx.text.includes(c)||(c.length>=5&&idx.tokens.some(tok=>Math.abs(tok.length-c.length)<=1&&oneEditAway(c,tok))));
 });
}
'''
    once('const fmt=n=>new Intl.NumberFormat().format(n);\nfunction saveFav()', 'const fmt=n=>new Intl.NumberFormat().format(n);\n' + search_helpers + '\nfunction saveFav()', 'search helpers')
    once('  if(terms.length){\n    const hay=[t.name,t.description,t.sourceCategory,t.section,t.subsection,t.curatedCategory,t.pricing].join(" ").toLowerCase();\n    if(!terms.every(term=>hay.includes(term)))return false;\n  }',
         '  if(terms.length&&!matchesQuery(t,state.query))return false;', 'search matcher')

    # Debounce search; track result success without sending raw query text.
    old_listeners='["searchInput","sourceFilter","pricingFilter","verificationFilter","priorityFilter","sortFilter"].forEach(id=>$("#"+id).addEventListener(id==="searchInput"?"input":"change",syncStateFromControls));'
    new_listeners='''let searchTimer;
$("#searchInput").addEventListener("input",()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{syncStateFromControls();const n=getFiltered().length;trackAtlas("atlas_search",{query_length:$("#searchInput").value.trim().length,result_count:n,zero_results:n===0});if(n===0)trackAtlas("atlas_zero_result",{query_length:$("#searchInput").value.trim().length})},110)});
["sourceFilter","pricingFilter","verificationFilter","priorityFilter","sortFilter"].forEach(id=>$("#"+id).addEventListener("change",()=>{syncStateFromControls();trackAtlas("atlas_filter_change",{filter:id,value:$("#"+id).value,result_count:getFiltered().length})}));
$$("[data-quick-search]").forEach(b=>b.addEventListener("click",()=>{$("#searchInput").value=b.dataset.quickSearch;syncStateFromControls();trackAtlas("atlas_quick_search",{term:b.dataset.quickSearch,result_count:getFiltered().length})}));'''
    once(old_listeners, new_listeners, 'search/filter listeners')

    # --- Dead / parked destinations are not clickable ---
    once(' const statusClass=live?"live":(/^(Dead|Parked|Server error)/.test(t.verification||"")?"bad":(t.verification==="Automation blocked"?"blocked":"pending"));',
         ' const statusClass=live?"live":(/^(Dead|Parked|Server error)/.test(t.verification||"")?"bad":(t.verification==="Automation blocked"?"blocked":"pending"));\n const unavailable=/^(Dead \/ unavailable|Parked \/ for sale)$/.test(t.verification||"");', 'unavailable flag')
    once('<div class="toolactions"><button class="btn outline" onclick="openDetail(${t.id})">Details</button><a class="btn blue" href="${esc(t.url)}" target="_blank" rel="noopener noreferrer">Visit ↗</a><button class="btn outline fav" aria-label="Favorite ${esc(t.name)}" onclick="toggleFav(${t.id},this)">${favorites.has(t.id)?"★":"☆"}</button></div>',
         '<div class="toolactions"><button class="btn outline" onclick="openDetail(${t.id})">Details</button>${unavailable?`<span class="btn outline" aria-disabled="true">Unavailable</span>`:`<a class="btn blue" data-tool-visit data-tool-id="${t.id}" data-tool-name="${esc(t.name)}" data-tool-domain="${esc(domain(t.url))}" data-tool-source="${esc(t.sourceCategory)}" data-tool-verification="${esc(t.verification||"")}" href="${esc(t.url)}" target="_blank" rel="noopener noreferrer">Visit ↗</a>`}<button class="btn outline fav" aria-label="Favorite ${esc(t.name)}" onclick="toggleFav(${t.id},this)">${favorites.has(t.id)?"★":"☆"}</button></div>', 'tool card visit guard')

    once('function openDetail(id){\n const t=TOOLS.find(x=>x.id===id);if(!t)return;',
         'function openDetail(id){\n const t=TOOLS.find(x=>x.id===id);if(!t)return;\n const unavailable=/^(Dead \/ unavailable|Parked \/ for sale)$/.test(t.verification||"");\n trackAtlas("atlas_tool_detail",{tool_id:t.id,tool_name:t.name,domain:domain(t.url),source:t.sourceCategory,verification:t.verification});', 'detail tracking')
    once('<dl class="detailgrid"><dt>Website</dt><dd><a href="${esc(t.url)}" target="_blank" rel="noopener noreferrer" style="color:#175cd3">${esc(t.url)}</a></dd>',
         '<dl class="detailgrid"><dt>Website</dt><dd>${unavailable?`<span>${esc(t.url)}</span>`:`<a data-tool-visit data-tool-id="${t.id}" data-tool-name="${esc(t.name)}" data-tool-domain="${esc(domain(t.url))}" data-tool-source="${esc(t.sourceCategory)}" data-tool-verification="${esc(t.verification||"")}" href="${esc(t.url)}" target="_blank" rel="noopener noreferrer" style="color:#175cd3">${esc(t.url)}</a>`}</dd>', 'detail URL guard')
    once('<div class="actions"><a class="btn blue" href="${esc(t.url)}" target="_blank" rel="noopener noreferrer">Open website ↗</a><button class="btn outline" onclick="toggleModalFav(${t.id},this)">${favorites.has(t.id)?"★ Favorited":"☆ Add favorite"}</button></div>`;',
         '<div class="actions">${unavailable?`<span class="btn outline" aria-disabled="true">Website unavailable</span>`:`<a class="btn blue" data-tool-visit data-tool-id="${t.id}" data-tool-name="${esc(t.name)}" data-tool-domain="${esc(domain(t.url))}" data-tool-source="${esc(t.sourceCategory)}" data-tool-verification="${esc(t.verification||"")}" href="${esc(t.url)}" target="_blank" rel="noopener noreferrer">Open website ↗</a>`}<button class="btn outline" onclick="toggleModalFav(${t.id},this)">${favorites.has(t.id)?"★ Favorited":"☆ Add favorite"}</button></div>`;', 'detail visit button guard')

    # --- Favorites and outbound clicks become measurable ---
    once('window.toggleFav=(id,btn)=>{favorites.has(id)?favorites.delete(id):favorites.add(id);saveFav();btn.textContent=favorites.has(id)?"★":"☆";if(state.favoritesOnly)renderLibrary()};',
         'window.toggleFav=(id,btn)=>{favorites.has(id)?favorites.delete(id):favorites.add(id);saveFav();const added=favorites.has(id);btn.textContent=added?"★":"☆";trackAtlas("atlas_favorite_toggle",{tool_id:id,added});if(state.favoritesOnly)renderLibrary()};', 'favorite tracking')
    once('window.toggleModalFav=(id,b)=>{favorites.has(id)?favorites.delete(id):favorites.add(id);saveFav();b.textContent=favorites.has(id)?"★ Favorited":"☆ Add favorite"};',
         'window.toggleModalFav=(id,b)=>{favorites.has(id)?favorites.delete(id):favorites.add(id);saveFav();const added=favorites.has(id);b.textContent=added?"★ Favorited":"☆ Add favorite";trackAtlas("atlas_favorite_toggle",{tool_id:id,added})};', 'modal favorite tracking')

    # --- Zero-result recovery ---
    old_empty='$("#toolGrid").innerHTML=slice.length?slice.map(toolCard).join(""):`<div class="empty" style="grid-column:1/-1"><h3>No matching tools</h3><p>Try clearing a filter or using a broader search.</p></div>`;'
    new_empty='$("#toolGrid").innerHTML=slice.length?slice.map(toolCard).join(""):`<div class="empty" style="grid-column:1/-1"><h3>No matches yet.</h3><p>Try a broader phrase, clear filters, or browse verified destinations.</p><div class="actions" style="justify-content:center"><button class="btn blue" onclick="recoverClear()">Clear filters</button><button class="btn outline" onclick="recoverVerified()">Browse live-verified</button><button class="btn outline" onclick="showView(\'categories\')">Browse categories</button></div></div>`;'
    once(old_empty, new_empty, 'zero-result recovery')
    recovery = '''
window.recoverClear=()=>{$("#clearFilters").click();trackAtlas("atlas_zero_recovery",{action:"clear"})};
window.recoverVerified=()=>{state.query="";state.source="";state.pricing="";state.verification="Live verified";state.priority="";state.page=1;state.favoritesOnly=false;$("#searchInput").value="";$("#sourceFilter").value="";$("#pricingFilter").value="";$("#verificationFilter").value="Live verified";$("#priorityFilter").value="";$("#favOnly").classList.remove("active");renderLibrary();trackAtlas("atlas_zero_recovery",{action:"verified"})};
'''
    once('window.goPage=p=>{state.page=p;renderLibrary();$("#view-library").scrollIntoView({behavior:"smooth"})};',
         'window.goPage=p=>{state.page=p;renderLibrary();$("#view-library").scrollIntoView({behavior:"smooth"})};' + recovery, 'recovery helpers')

    # --- Share + analytics opt-out + delegated outbound/partner tracking ---
    misc = '''
async function shareAtlas(){
 const data={title:"Nick’s Digital Atlas",text:"Browse 1,834 AI tools and useful websites.",url:location.origin+location.pathname};
 try{if(navigator.share)await navigator.share(data);else{await navigator.clipboard.writeText(data.url);alert("Atlas link copied.")}trackAtlas("atlas_share",{method:navigator.share?"native":"clipboard"})}catch(e){}
}
$("#shareAtlas").addEventListener("click",shareAtlas);
$("#partnerCta").addEventListener("click",()=>trackAtlas("atlas_partner_click",{placement:"home"}));
document.addEventListener("click",e=>{const a=e.target.closest("[data-tool-visit]");if(a)trackAtlas("atlas_tool_visit",{tool_id:Number(a.dataset.toolId),tool_name:a.dataset.toolName,domain:a.dataset.toolDomain,source:a.dataset.toolSource,verification:a.dataset.toolVerification})});
function updateAnalyticsStatus(){const off=localStorage.getItem("atlasAnalyticsOptOut")==="1";$("#analyticsStatus").textContent=off?"Analytics disabled on this device.":"Analytics enabled; session recording is off.";$("#analyticsOptOut").textContent=off?"Enable analytics on this device":"Disable analytics on this device"}
$("#analyticsOptOut").addEventListener("click",()=>{const off=localStorage.getItem("atlasAnalyticsOptOut")==="1";if(off){localStorage.removeItem("atlasAnalyticsOptOut");if(window.posthog&&posthog.opt_in_capturing)posthog.opt_in_capturing()}else{localStorage.setItem("atlasAnalyticsOptOut","1");if(window.posthog&&posthog.opt_out_capturing)posthog.opt_out_capturing()}updateAnalyticsStatus()});
updateAnalyticsStatus();
'''
    once('$("#menuBtn").onclick=()=>{let o=$("#mobileNav").classList.toggle("open");$("#menuBtn").setAttribute("aria-expanded",String(o))};',
         '$("#menuBtn").onclick=()=>{let o=$("#mobileNav").classList.toggle("open");$("#menuBtn").setAttribute("aria-expanded",String(o))};\n' + misc, 'misc controls')

    # --- Mobile performance: do not build 60 hidden library cards on initial Home load ---
    once('const initial=location.hash.replace("#","");if(["home","library","categories","free","archive","quality"].includes(initial))showView(initial);else renderLibrary();',
         'const initial=location.hash.replace("#","");if(["home","library","categories","free","archive","quality"].includes(initial))showView(initial);else{trackAtlas("atlas_view",{view:"home"})}', 'home startup render')

    # --- CSS for accessible controls and new blocks ---
    cro_css = '''
/* ATLAS-CRO-V2 — clarity, discovery, accessibility, monetization and measurement */
.card,.category{font:inherit;text-align:left;color:inherit;width:100%}
button.card,button.category{appearance:none;-webkit-appearance:none}
.btn,.navbtn,.menu,.chip,.pagination button,.quicksearch button{min-height:44px}
.modalclose{width:44px;height:44px}.fav{width:44px}
.discovery-first{margin-top:28px}
.quicksearch{display:flex;align-items:center;gap:7px;flex-wrap:wrap;padding:4px 0 2px;color:var(--muted);font-size:12px}
.quicksearch button{border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 11px;color:#35595b;cursor:pointer;font:inherit}
.quicksearch button:hover,.quicksearch button:focus-visible{border-color:#78cfc8;background:#f2fbfa}
.empty .actions{margin-top:16px}.partner-callout{display:flex;align-items:center;justify-content:space-between;gap:20px}.partner-callout p{margin:5px 0 0;max-width:760px}
.trust-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.trust-grid .callout{height:100%}
.footerlinks{display:flex;flex-wrap:wrap;gap:12px;margin-top:12px}.footerlinks a,.linkbutton{color:#246b6d;text-decoration:underline;text-underline-offset:3px}.linkbutton{border:0;background:none;padding:0;font:inherit;cursor:pointer}
@media(max-width:680px){.discovery-first{margin-top:24px}.discovery-first .sectionhead h2{font-size:27px}.partner-callout{align-items:flex-start;flex-direction:column}.trust-grid{grid-template-columns:1fr}.quicksearch{padding-top:8px}}
'''
    once('</style>', cro_css + '\n</style>', 'CRO CSS')

    # --- Keep current regression QA aligned and use installed system Chrome in CI ---
    qa_path = ROOT / 'qa/atlas-live-qa.js'
    qa = qa_path.read_text()
    if 'button:has-text("Search the library")' in qa:
        qa = qa.replace('button:has-text("Search the library")', 'button:has-text("Browse all 1,834 tools")', 1)
    if 'const browser=await chromium.launch({headless:true});' in qa:
        qa = qa.replace('const browser=await chromium.launch({headless:true});', 'const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||"/usr/bin/google-chrome",args:["--no-sandbox"]});', 1)
    qa_path.write_text(qa)

# Always rebuild production bundle and derived static acquisition pages from the source of truth.
def split_n(text, n):
    q, r = divmod(len(text), n)
    out, pos = [], 0
    for i in range(n):
        size = q + (1 if i < r else 0)
        out.append(text[pos:pos+size]); pos += size
    assert ''.join(out) == text
    return out

for i, part in enumerate(split_n(shell, 3)):
    SHELL_FILES[i].write_text(part)

bundle = shell.replace('__DATA_B64__', data_b64)
(ROOT / 'atlas-bundle.html').write_text(bundle)

# Static, crawlable collection pages: real intent pages, not 1,834 thin doorway pages.
static_root = ROOT / 'atlas-static'
collections_root = static_root / 'collections'
collections_root.mkdir(parents=True, exist_ok=True)


def priority_score(r):
    return {'High': 3, 'Medium': 2, 'Low': 1}.get(r[9] or '', 0)


def select_records(predicate, limit=120):
    arr = [r for r in records if predicate(r)]
    arr.sort(key=lambda r: (r[10] != 'Live verified', -priority_score(r), (r[1] or '').lower()))
    return arr[:limit], len(arr)


def render_collection(slug, title, intro, predicate):
    chosen, total = select_records(predicate)
    cards = []
    for r in chosen:
        name, url, desc, pricing, verification = r[1], r[2], r[3] or 'No description available.', r[4] or 'Unknown', r[10] or 'Source listed'
        status = 'Live verified' if verification == 'Live verified' else verification
        cards.append(f'''<article class="item"><h2>{html.escape(name)}</h2><p>{html.escape(desc[:320])}</p><div class="meta"><span>{html.escape(pricing)}</span><span>{html.escape(status)}</span></div><a href="{html.escape(url, quote=True)}" rel="noopener noreferrer">Open {html.escape(name)} ↗</a></article>''')
    page_url = f'{ATLAS_URL}collections/{slug}/'
    body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} — Nick’s Digital Atlas</title><meta name="description" content="{html.escape(intro[:155], quote=True)}"><link rel="canonical" href="{page_url}"><meta property="og:type" content="website"><meta property="og:title" content="{html.escape(title, quote=True)} — Nick’s Digital Atlas"><meta property="og:url" content="{page_url}"><style>body{{margin:0;background:#f4f8f7;color:#102b2d;font:16px/1.55 Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}}main{{max-width:1060px;margin:auto;padding:28px 18px 64px}}a{{color:#087f80}}.top{{padding:34px;border-radius:26px;background:#071b1d;color:white}}.top p{{color:#cde9e6;max-width:760px}}.nav{{display:flex;gap:14px;flex-wrap:wrap;margin:20px 0}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}.item{{background:white;border:1px solid rgba(7,73,76,.12);border-radius:18px;padding:20px}}.item h2{{font-size:19px;margin:0 0 8px}}.item p{{color:#617274}}.meta{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}}.meta span{{font-size:12px;background:#eef7f6;border-radius:999px;padding:5px 8px}}footer{{margin-top:34px;color:#617274}}@media(max-width:680px){{.grid{{grid-template-columns:1fr}}.top{{padding:26px}}}}</style></head><body><main><section class="top"><div>Nick’s Digital Atlas</div><h1>{html.escape(title)}</h1><p>{html.escape(intro)}</p><p><strong>{total:,}</strong> matching records in the current Atlas; this page shows up to {len(chosen)} strong starting points, prioritizing live-verified entries.</p></section><nav class="nav"><a href="{ATLAS_URL}">Open the interactive Atlas</a><a href="{ATLAS_URL}#library">Search all 1,834 tools</a><a href="{ATLAS_URL}#quality">Verification methodology</a></nav><section class="grid">{''.join(cards)}</section><footer>Availability verification confirms that a destination rendered during the latest audit; it does not independently validate every product claim, price, privacy policy or security practice.</footer></main></body></html>'''
    out = collections_root / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / 'index.html').write_text(body)

render_collection('ai-tools', 'AI Tools & Automation Resources', 'Browse AI tools for creation, automation, coding, media and productivity from the Atlas source library.', lambda r: r[5] == 'AI')
render_collection('design-tools', 'Design & Creative Tools', 'Browse design, image, video, branding and creative resources from the Atlas source library.', lambda r: r[5] == 'Design & Creative')
render_collection('education-tools', 'Education & Learning Tools', 'Browse research, education and learning resources from the Atlas source library.', lambda r: r[5] == 'Education & Learning')
render_collection('gaming-tools', 'Gaming, Mapping & Interactive Tools', 'Browse gaming, mapping, 3D and interactive resources from the Atlas source library.', lambda r: r[5] == 'Gaming')
render_collection('live-verified-tools', 'Live-Verified Tools & Websites', 'Start with destinations that successfully rendered during the latest Atlas browser audit.', lambda r: r[10] == 'Live verified')
render_collection('free-no-login', 'Free Tools With No Required Login', 'A deliberately strict collection of resources explicitly audited as usable without a required account or with optional login.', lambda r: bool(r[11]) and ('no login' in r[11].lower() or 'optional login' in r[11].lower()))

# Honest partner/sponsorship landing page.
partners = static_root / 'partners'
partners.mkdir(parents=True, exist_ok=True)
partner_url = ATLAS_URL + 'partners/'
(partners / 'index.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Partner With Nick’s Digital Atlas</title><meta name="description" content="Transparent sponsorship and partnership policy for Nick’s Digital Atlas."><link rel="canonical" href="{partner_url}"><style>body{{margin:0;background:#f4f8f7;color:#102b2d;font:16px/1.6 Inter,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}}main{{max-width:850px;margin:auto;padding:36px 18px 70px}}.hero,.card{{background:white;border:1px solid rgba(7,73,76,.12);border-radius:22px;padding:28px;margin-bottom:16px}}.hero{{background:#071b1d;color:#fff}}.hero p{{color:#cae7e5}}a.button{{display:inline-block;background:#0f9d9a;color:white;padding:12px 16px;border-radius:12px;text-decoration:none;font-weight:700}}h2{{margin-bottom:6px}}</style></head><body><main><section class="hero"><div>Nick’s Digital Atlas</div><h1>Partner with the Atlas</h1><p>Reach people who are actively choosing tools without compromising the Atlas verification system.</p><a class="button" href="mailto:{CONTACT_EMAIL}?subject=Digital%20Atlas%20partnership%20inquiry">Start a partnership inquiry</a></section><section class="card"><h2>What can be sponsored</h2><p>Clearly labeled featured placements, category sponsorships and other disclosed promotional inventory can be considered. Exact packages are quoted based on fit and measured audience activity.</p></section><section class="card"><h2>What cannot be bought</h2><p><strong>Verification status, organic ranking and editorial conclusions are not for sale.</strong> Paid relationships are labeled so users can distinguish commercial placement from organic discovery.</p></section><section class="card"><h2>Affiliate policy</h2><p>If an outbound link later uses an affiliate relationship, the relationship will be disclosed. Affiliate economics will not change whether a destination is marked live, dead, blocked or review-needed.</p></section><p><a href="{ATLAS_URL}">← Back to the Atlas</a></p></main></body></html>''')

# Atlas-scoped sitemap for the main app and useful acquisition pages.
urls = [ATLAS_URL,
        ATLAS_URL+'collections/ai-tools/', ATLAS_URL+'collections/design-tools/', ATLAS_URL+'collections/education-tools/',
        ATLAS_URL+'collections/gaming-tools/', ATLAS_URL+'collections/live-verified-tools/', ATLAS_URL+'collections/free-no-login/',
        partner_url]
(static_root / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{html.escape(u)}</loc><lastmod>2026-09-04</lastmod></url>\n' for u in urls) + '</urlset>\n')

report = {
    'tool_count': 1834,
    'live_verified': 1529,
    'source_entries': 1802,
    'bundle_bytes': len(bundle.encode()),
    'data_b64_bytes': len(data_b64.encode()),
    'sha256': hashlib.sha256(bundle.encode()).hexdigest(),
    'visual_theme': 'Atlas Brand V2 + CRO V2',
    'cro_v2': {
        'clarity': True, 'discovery_first': True, 'semantic_buttons': True, 'min_touch_target_px': 44,
        'zero_result_recovery': True, 'dead_parked_visit_guards': True, 'fuzzy_search': True,
        'posthog_custom_events': True, 'session_recording': False, 'analytics_opt_out': True,
        'partner_conversion_path': True, 'sponsorship_independence_policy': True,
        'canonical_social_schema': True, 'crawlable_collection_pages': 6, 'sitemap': True,
        'hidden_home_library_render_removed': True
    }
}
(ROOT / 'atlas-build-report.json').write_text(json.dumps(report, indent=2) + '\n')

# Strong pre-deploy integrity assertions.
assert 'ATLAS-CRO-V2' in bundle
assert 'What is the Digital Atlas??' not in bundle
assert 'Browse all 1,834 tools' in bundle
assert '<link rel="canonical"' in bundle and 'application/ld+json' in bundle
assert '<button type="button" class="card click" data-goal=' in bundle
assert 'No matches yet.' in bundle
assert 'Family AI Command Center' not in bundle
assert 'Your map to the best AI tools' not in bundle
assert 'else renderLibrary();' not in bundle
assert 'atlas_tool_visit' in bundle and 'atlas_search' in bundle and 'atlas_partner_click' in bundle
assert 'disable_session_recording:true' in bundle
assert (static_root / 'collections/ai-tools/index.html').exists()
assert (static_root / 'partners/index.html').exists()
assert (static_root / 'sitemap.xml').exists()
print(json.dumps(report, indent=2))
