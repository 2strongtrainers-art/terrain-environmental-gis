from pathlib import Path
import base64,gzip,hashlib,json,re

ROOT=Path('.')
SHELL=[ROOT/f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA=[ROOT/f'atlas-src/data-{i:03d}.txt' for i in range(9)]
shell=''.join(p.read_text() for p in SHELL)
data_b64=''.join(p.read_text().strip() for p in DATA)
records=json.loads(gzip.decompress(base64.b64decode(data_b64)))
assert 'ATLAS-INTENT-V32' in shell
assert '__DATA_B64__' in shell
old_total=len(records)

# Official/free or library-supported viewing services validated from current official sources.
# Verification remains Needs review until the Atlas link-audit classifies them; access remains Unknown
# unless the existing strict access audit has explicitly classified it.
media_rows=[
 ['curated-tubi','Tubi','https://tubitv.com/','Free, legal, ad-supported movies and TV shows with no subscription fee.','Free','Curated Library','Watch & Multimedia','Free Movies & TV','Entertainment','High','Needs review','Unknown','Official Tubi free/legal streaming capability validated 2026-09-04; Atlas access audit pending.'],
 ['curated-pluto-tv','Pluto TV','https://pluto.tv/','Free streaming service with live TV channels plus on-demand movies and shows.','Free','Curated Library','Watch & Multimedia','Free Movies & Live TV','Entertainment','High','Needs review','Unknown','Official Pluto TV free movies/live-TV capability validated 2026-09-04; Atlas access audit pending.'],
 ['curated-plex-watch','Plex Free Movies & TV','https://watch.plex.tv/','Free ad-supported on-demand movies, TV shows, and live TV channels from Plex.','Free','Curated Library','Watch & Multimedia','Free Movies & Live TV','Entertainment','High','Needs review','Unknown','Official Plex free ad-supported streaming capability validated 2026-09-04; Atlas access audit pending.'],
 ['curated-roku-channel','The Roku Channel','https://therokuchannel.roku.com/','Free movies, TV shows, Roku Originals, live news, kids programming, and live channels; optional premium subscriptions also exist.','Free / Paid','Curated Library','Watch & Multimedia','Free Movies & Live TV','Entertainment','High','Needs review','Unknown','Official Roku free streaming capability validated 2026-09-04; Atlas access audit pending.'],
 ['curated-nasa-plus','NASA+','https://plus.nasa.gov/','NASA’s free, ad-free streaming service with live mission coverage, documentaries, original series, and science programming.','Free','Curated Library','Watch & Multimedia','Science & Documentaries','Education & Learning','High','Needs review','Unknown','Official NASA+ free/ad-free/no-subscription capability validated 2026-09-04; Atlas access audit pending.'],
 ['curated-pbs-watch','PBS','https://www.pbs.org/','Watch many PBS episodes, documentaries, news, science, nature, and educational programs free; some content requires PBS Passport.','Free / Paid','Curated Library','Watch & Multimedia','Documentaries & Education','Education & Learning','High','Needs review','Unknown','Official PBS free streaming/no-account availability for many videos validated 2026-09-04; Atlas access audit pending.'],
 ['curated-hoopla-movies','Hoopla Movies','https://www.hoopladigital.com/movie','Stream movies free with a participating library card; Hoopla also offers TV, music, audiobooks, ebooks, and comics.','Free','Curated Library','Watch & Multimedia','Library Streaming','Entertainment','Medium','Needs review','Unknown','Official Hoopla free-with-library-card movie capability validated 2026-09-04; account/library-card access required.'],
 ['curated-kanopy','Kanopy','https://www.kanopy.com/','Stream classic cinema, indie films, documentaries, and educational video free through participating public libraries and universities.','Free','Curated Library','Watch & Multimedia','Library Streaming','Entertainment','Medium','Needs review','Unknown','Official Kanopy library-card streaming capability validated 2026-09-04; account/library-card access required.']
]
existing_urls={str(r[2]).rstrip('/').lower() for r in records}
existing_names={str(r[1]).strip().lower() for r in records}
added=[]
for row in media_rows:
    u=row[2].rstrip('/').lower()
    if u not in existing_urls and row[1].lower() not in existing_names:
        records.append(row);added.append(row[1]);existing_urls.add(u);existing_names.add(row[1].lower())
new_total=len(records)
new_fmt=f'{new_total:,}'
old_fmt=f'{old_total:,}'

if 'ATLAS-MULTIMEDIA-V4' not in shell:
    # 1) Navigation: dedicated Watch section on desktop and mobile.
    desktop='''   <button class="navbtn" data-view="categories">Categories</button>\n   <button class="navbtn" data-view="free">Free / No Login</button>'''
    desktop_new='''   <button class="navbtn" data-view="categories">Categories</button>\n   <button class="navbtn" data-view="watch">Watch</button>\n   <button class="navbtn" data-view="free">Free / No Login</button>'''
    assert desktop in shell
    shell=shell.replace(desktop,desktop_new,1)
    mobile='''<button class="navbtn" data-view="categories">Categories</button><button class="navbtn" data-view="free">Free / No Login</button>'''
    mobile_new='''<button class="navbtn" data-view="categories">Categories</button><button class="navbtn" data-view="watch">Watch</button><button class="navbtn" data-view="free">Free / No Login</button>'''
    assert mobile in shell
    shell=shell.replace(mobile,mobile_new,1)

    # 2) Polished Watch & Multimedia view. All destinations are official services; availability can vary by region/catalog.
    watch_view=r'''
<section class="view" id="view-watch">
 <div class="watchHero">
  <div class="eyebrow">Watch & Multimedia</div>
  <h1>Watch something free.</h1>
  <p>Legal, official streaming destinations for movies, TV, documentaries, live channels, nature cams, science and library-supported viewing.</p>
  <div class="actions"><button type="button" class="btn primary" data-watch-query="free movies and tv">Find free movies & TV</button><button type="button" class="btn ghost" data-watch-query="show me something interesting to watch for free">Surprise me</button></div>
 </div>
 <div class="callout green watch-note"><strong>Free does not always mean no account.</strong><p>Some services are ad-supported, some have optional paid tiers, and Hoopla/Kanopy require participating library access. Use the separate Free • No Login collection when account-free access is mandatory.</p></div>
 <div class="section">
  <div class="sectionhead"><div><h2>Start watching</h2><p>Official services with free viewing options. Catalogs and regional availability change over time.</p></div></div>
  <div class="grid watch-services">
   <a class="card click watch-card" data-watch-link="Tubi" href="https://tubitv.com/" target="_blank" rel="noopener noreferrer"><div class="icon">🍿</div><h3>Tubi</h3><p>Free, legal movies and TV with ads.</p><span class="watch-tag">Free • ad-supported</span></a>
   <a class="card click watch-card" data-watch-link="Pluto TV" href="https://pluto.tv/" target="_blank" rel="noopener noreferrer"><div class="icon">📺</div><h3>Pluto TV</h3><p>Free live channels plus on-demand movies and shows.</p><span class="watch-tag">Free • live + on-demand</span></a>
   <a class="card click watch-card" data-watch-link="Plex" href="https://watch.plex.tv/" target="_blank" rel="noopener noreferrer"><div class="icon">▶️</div><h3>Plex</h3><p>Free ad-supported movies, TV and live channels.</p><span class="watch-tag">Free • ad-supported</span></a>
   <a class="card click watch-card" data-watch-link="The Roku Channel" href="https://therokuchannel.roku.com/" target="_blank" rel="noopener noreferrer"><div class="icon">📡</div><h3>The Roku Channel</h3><p>Free shows, movies, live news and Roku Originals.</p><span class="watch-tag">Free + optional premium</span></a>
   <a class="card click watch-card" data-watch-link="NASA+" href="https://plus.nasa.gov/" target="_blank" rel="noopener noreferrer"><div class="icon">🚀</div><h3>NASA+</h3><p>Free, ad-free missions, documentaries and science series.</p><span class="watch-tag">Free • ad-free</span></a>
   <a class="card click watch-card" data-watch-link="PBS" href="https://www.pbs.org/" target="_blank" rel="noopener noreferrer"><div class="icon">🎓</div><h3>PBS</h3><p>News, NOVA, Nature, documentaries and educational programs.</p><span class="watch-tag">Many programs free</span></a>
   <a class="card click watch-card" data-watch-link="Explore.org" href="https://explore.org/livecams" target="_blank" rel="noopener noreferrer"><div class="icon">🐻</div><h3>Explore.org</h3><p>Live nature cams, wildlife and documentary programming.</p><span class="watch-tag">Free live cams</span></a>
   <a class="card click watch-card" data-watch-link="Hoopla" href="https://www.hoopladigital.com/movie" target="_blank" rel="noopener noreferrer"><div class="icon">📚</div><h3>Hoopla</h3><p>Movies and media free through participating libraries.</p><span class="watch-tag">Library card required</span></a>
   <a class="card click watch-card" data-watch-link="Kanopy" href="https://www.kanopy.com/" target="_blank" rel="noopener noreferrer"><div class="icon">🎞️</div><h3>Kanopy</h3><p>Classic cinema, indie films and documentaries via libraries.</p><span class="watch-tag">Participating library required</span></a>
  </div>
 </div>
 <div class="section">
  <div class="sectionhead"><div><h2>Browse by mood</h2><p>Use Atlas intent ranking instead of hunting through streaming sites one at a time.</p></div></div>
  <div class="grid watch-moods">
   <button type="button" class="card click" data-watch-query="free movie"><div class="icon">🎬</div><h3>Movie night</h3><p>Find free movie-streaming options.</p></button>
   <button type="button" class="card click" data-watch-query="free live tv and news"><div class="icon">📺</div><h3>Live TV & news</h3><p>Browse live channels and current programming.</p></button>
   <button type="button" class="card click" data-watch-query="free documentary"><div class="icon">🧠</div><h3>Documentaries</h3><p>Science, history, nature and educational viewing.</p></button>
   <button type="button" class="card click" data-watch-query="live animal nature cams"><div class="icon">🦅</div><h3>Relaxing live cams</h3><p>Wildlife, oceans, bears, birds and nature.</p></button>
   <button type="button" class="card click" data-watch-query="NASA space documentary live mission"><div class="icon">🛰️</div><h3>Space & science</h3><p>NASA missions, documentaries and science.</p></button>
   <button type="button" class="card click" data-watch-query="movies with my library card"><div class="icon">🏛️</div><h3>Library streaming</h3><p>Hoopla, Kanopy and library-supported viewing.</p></button>
   <button type="button" class="card click" data-watch-query="free tv shows"><div class="icon">📼</div><h3>Binge a show</h3><p>Free series and television catalogs.</p></button>
   <button type="button" class="card click" data-watch-query="show me something interesting to watch for free"><div class="icon">🎲</div><h3>I’m bored</h3><p>Let Atlas surface something worth exploring.</p></button>
  </div>
 </div>
 <div class="callout gray"><strong>Availability note</strong><p>Streaming catalogs, geographic availability and account requirements can change. Atlas treats link verification separately from pricing and login/access verification.</p><div class="actions"><button type="button" class="btn outline" data-view="free">Browse audited Free • No Login</button><button type="button" class="btn outline" data-watch-query="free streaming">Search all free streaming</button></div></div>
</section>

'''
    marker='<section class="view" id="view-library">'
    assert marker in shell
    shell=shell.replace(marker,watch_view+marker,1)

    # 3) Styling that uses the existing Atlas visual language.
    css=r'''
/* ATLAS-MULTIMEDIA-V4 */
.watchHero{margin:26px 0 18px;position:relative;overflow:hidden;border-radius:28px;background:linear-gradient(135deg,#071b1d 0%,#0f4c5c 52%,#0d9488 125%);color:#fff;padding:48px 46px;box-shadow:var(--shadow)}
.watchHero:after{content:"";position:absolute;width:320px;height:320px;border-radius:50%;right:-80px;top:-150px;background:radial-gradient(circle,rgba(94,234,212,.26),transparent 68%)}
.watchHero h1{font-size:clamp(38px,6vw,64px);line-height:1.02;margin:10px 0 14px;letter-spacing:-.05em}.watchHero p{font-size:17px;max-width:760px;color:#d5fffb;margin:0 0 22px}.watchHero .eyebrow{color:#99f6e4}
.watch-card{text-decoration:none;min-height:210px;display:flex;flex-direction:column}.watch-card .watch-tag{margin-top:auto;padding-top:13px;color:#0f766e;font-size:12px;font-weight:800}.watch-note{margin:18px 0 30px}.watch-services .card{border-color:#d0ece9}.watch-moods .card{text-align:left}.watch-moods button.card{font:inherit;color:inherit}
@media(max-width:680px){.watchHero{padding:34px 24px;margin-top:14px;border-radius:22px}.watchHero h1{font-size:40px}.watchHero p{font-size:15px}}
'''
    assert '</style>' in shell
    shell=shell.replace('</style>',css+'\n</style>',1)

    # 4) Add Watch to discovery goals and route architecture.
    needle=''' ["🆓","Use something free without an account","Only explicitly audited no-login tools.","no-login"],'''
    insert=''' ["🍿","Watch something free","Movies, TV, documentaries, live channels and nature cams.","watch"],\n ["🆓","Use something free without an account","Only explicitly audited no-login tools.","no-login"],'''
    assert needle in shell
    shell=shell.replace(needle,insert,1)
    route_needle=''' maps:{label:"Games, maps & 3D",terms:["map","3d","world","terrain","game","minecraft"],source:"Gaming"},\n "no-login":{label:"Free • No Login",terms:[],source:""},'''
    route_new=''' maps:{label:"Games, maps & 3D",terms:["map","3d","world","terrain","game","minecraft"],source:"Gaming"},\n watch:{label:"Watch & Multimedia",terms:["free movies","streaming","live tv","documentary","nature cams"],source:"Curated Library"},\n "no-login":{label:"Free • No Login",terms:[],source:""},'''
    assert route_needle in shell
    shell=shell.replace(route_needle,route_new,1)
    apply_needle='''function applyGoal(g){\n if(g==="no-login"){showView("free");return}'''
    apply_new='''function applyGoal(g){\n if(g==="watch"){showView("watch");return}\n if(g==="no-login"){showView("free");return}'''
    assert apply_needle in shell
    shell=shell.replace(apply_needle,apply_new,1)

    # 5) Task intelligence: distinguish watching media from creating media.
    pref_needle=''' "stock-photos":["pexels","unsplash","pixabay","stocksnap","gratisography","freeimages","burst"],\n spreadsheet:'''
    pref_new=''' "stock-photos":["pexels","unsplash","pixabay","stocksnap","gratisography","freeimages","burst"],\n "watch-free":["tubi","pluto tv","plex free movies","the roku channel","nasa+","pbs","explore.org","hoopla","kanopy"],\n "library-streaming":["hoopla","kanopy"],\n "nature-livecam":["explore.org"],\n "space-streaming":["nasa+","pbs"],\n spreadsheet:'''
    assert pref_needle in shell
    shell=shell.replace(pref_needle,pref_new,1)
    avoid_needle=''' "stock-photos":["getty images","shutterstock","istock","adobe stock"]\n};'''
    avoid_new=''' "stock-photos":["getty images","shutterstock","istock","adobe stock"],\n "watch-free":["pika","runway","topaz video ai","bing video","video-tutor","aifreevideo","1a auto videos","synthesia","heygen"],\n "library-streaming":["library genesis"],\n "nature-livecam":["minecraft","map generator"],\n "space-streaming":["spacehey"]\n};'''
    assert avoid_needle in shell
    shell=shell.replace(avoid_needle,avoid_new,1)

    video_rule=''' {id:"video",route:"video",patterns:["video"],anchors:["video"],terms:["editor","generator","media"]},'''
    watch_rules=''' {id:"library-streaming",route:"watch",patterns:["library card movies","movies with my library card","watch with library card","library streaming","hoopla","kanopy"],anchors:["library","library card","movies"],terms:["streaming","hoopla","kanopy","film"]},\n {id:"nature-livecam",route:"watch",patterns:["live animal cam","live animal cams","live nature cam","live nature cams","wildlife cam","wildlife cams","animal webcam","nature webcam"],anchors:["live cam","nature","wildlife","animal"],terms:["webcam","camera","stream","explore"]},\n {id:"space-streaming",route:"watch",patterns:["nasa plus","nasa+","space documentary","space documentaries","live mission","nasa mission"],anchors:["nasa","space","mission"],terms:["documentary","science","streaming","live"]},\n {id:"watch-free",route:"watch",patterns:["watch free","watch something free","free movie","free movies","free tv","free streaming","stream free","live tv","live news","watch a movie","watch movie","watch tv","free documentary","watch documentary","something to watch","im bored","i m bored"],anchors:["movie","movies","tv","streaming","watch","documentary","live"],terms:["free","shows","channels","on demand","entertainment"]},\n {id:"video",route:"video",patterns:["video"],anchors:["video"],terms:["editor","generator","media"]},'''
    assert video_rule in shell
    shell=shell.replace(video_rule,watch_rules,1)

    # Close the final V3.2 stress-test weakness: "video tool for Instagram" should be creation intent.
    short_old='''"video for social","tiktok video","instagram video","video for instagram","reel","shorts"]'''
    short_new='''"video for social","tiktok video","instagram video","video for instagram","video tool for instagram","instagram video tool","reel","shorts"]'''
    assert short_old in shell
    shell=shell.replace(short_old,short_new,1)

    # 6) Watch interactions and analytics.
    event_marker='''$("#routeBtn").onclick=routeCommand;'''
    event_extra='''$("#routeBtn").onclick=routeCommand;\n$$('[data-watch-query]').forEach(b=>b.addEventListener('click',()=>{trackAtlas('atlas_watch_browse',{query_type:b.dataset.watchQuery.slice(0,60)});applyIntentSearch(b.dataset.watchQuery)}));\ndocument.addEventListener('click',e=>{const a=e.target.closest('[data-watch-link]');if(a)trackAtlas('atlas_watch_launch',{service:a.dataset.watchLink})});'''
    assert event_marker in shell
    shell=shell.replace(event_marker,event_extra,1)

    # Better empty-input guidance now that Watch is a primary use case.
    shell=shell.replace('For example: make a video, edit a PDF, create a logo, learn Python, or find a no-login tool.','For example: make a video, watch something free, edit a PDF, create a logo, learn Python, or find a no-login tool.',1)

    # Add watch shortcut to library suggestions and footer.
    qs='''<button type="button" data-quick-search="image">image</button></div>'''
    qs_new='''<button type="button" data-quick-search="image">image</button><button type="button" data-quick-search="free movies">watch free</button></div>'''
    assert qs in shell
    shell=shell.replace(qs,qs_new,1)
    footer='''<a href="partners/">Partner policy</a><button type="button" class="linkbutton" id="shareAtlas">Share Atlas</button>'''
    footer_new='''<a href="partners/">Partner policy</a><button type="button" class="linkbutton" data-view="watch">Watch & Multimedia</button><button type="button" class="linkbutton" id="shareAtlas">Share Atlas</button>'''
    assert footer in shell
    shell=shell.replace(footer,footer_new,1)

# Counts, trust metadata, and newly-curated review state.
shell=shell.replace(old_fmt,new_fmt)
shell=re.sub(r'"indexedTools":\s*\d+', '"indexedTools":'+str(new_total), shell, count=1)
# Original 305 non-live records + post-audit curated additions (V3.2 and V4) remain unverified until the next full audit.
task_ids={
 'curated-qrcode-monkey','curated-otter-ai','curated-deepl-translator','curated-wix-builder',
 'curated-tubi','curated-pluto-tv','curated-plex-watch','curated-roku-channel','curated-nasa-plus','curated-pbs-watch','curated-hoopla-movies','curated-kanopy'
}
task_pending=sum(1 for r in records if r[0] in task_ids and r[10] != 'Live verified')
not_live=new_total-1529
shell=re.sub(r'"serverError":5(?:,"taskEssentialNeedsReview":\d+)?', '"serverError":5,"taskEssentialNeedsReview":'+str(task_pending), shell, count=1)
review_old='META.auditBreakdown.error+META.auditBreakdown.timeout+META.auditBreakdown.uncertain+META.auditBreakdown.serverError'
review_new='META.auditBreakdown.error+META.auditBreakdown.timeout+META.auditBreakdown.uncertain+META.auditBreakdown.serverError+(META.auditBreakdown.taskEssentialNeedsReview||0)'
if review_old in shell:shell=shell.replace(review_old,review_new,1)
shell=re.sub(r'Review \d+ non-live-verified records',f'Review {not_live:,} non-live-verified records',shell)
quality_note='<p><b>New task essentials</b> added after the September 3 audit remain marked <b>Needs review</b> until a subsequent link audit verifies them. Official-site capability research is kept separate from Atlas link/access verification.</p>'
if quality_note not in shell:
    qmarker='<p><b>Access type</b> is only shown when the curated Notion database explicitly classified it. A free price does not automatically mean no account is required.</p>'
    assert qmarker in shell
    shell=shell.replace(qmarker,qmarker+'\n    '+quality_note,1)

# Encode augmented dataset and rebuild bundle.
encoded=base64.b64encode(gzip.compress(json.dumps(records,separators=(',',':')).encode(),compresslevel=9)).decode()
def split_n(text,n):
    q,r=divmod(len(text),n);out=[];p=0
    for i in range(n):
        z=q+(1 if i<r else 0);out.append(text[p:p+z]);p+=z
    assert ''.join(out)==text
    return out
for p,x in zip(SHELL,split_n(shell,3)):p.write_text(x)
for p,x in zip(DATA,split_n(encoded,9)):p.write_text(x)
bundle=shell.replace('__DATA_B64__',encoded)
(ROOT/'atlas-bundle.html').write_text(bundle)

# Synchronize the regression/intent harnesses with the current counts and new navigation.
qa=ROOT/'qa/atlas-live-qa.js'
txt=qa.read_text()
txt=txt.replace(old_fmt,new_fmt).replace(f'===%d'%old_total,f'===%d'%new_total).replace(f'=== {old_total}',f'=== {new_total}')
txt=txt.replace("Desktop primary navigation: all six views","Desktop primary navigation: all seven views")
txt=txt.replace("['home','library','categories','free','archive','quality']","['home','library','categories','watch','free','archive','quality']")
txt=txt.replace("Home, Library, Categories, Free, Power User, Data Quality","Home, Library, Categories, Watch, Free, Power User, Data Quality")
txt=txt.replace("Goal-first cards: all eight routes click through","Goal-first cards: all nine routes click through")
txt=txt.replace("['video','research','design','business','automation','maps','no-login','recommended']","['video','research','design','business','automation','maps','watch','no-login','recommended']")
txt=txt.replace("video, research, design, business, automation, maps, no-login, recommended","video, research, design, business, automation, maps, watch, no-login, recommended")
txt=txt.replace("Mobile menu opens and all six nav controls work","Mobile menu opens and all seven nav controls work")
txt=txt.replace("menu + six mobile navigation controls","menu + seven mobile navigation controls")
txt=txt.replace("===305",f"==={not_live}").replace("not-live=305",f"not-live={not_live:,}").replace("305 non-live-verified source-indexed records",f"{not_live:,} non-live-verified records")
# Watch goal opens the watch view instead of the library; teach the existing goal test about that branch.
old_goal="""if(g==='no-login'){assert(await activeView(page,'free'),`${g} did not open free view`);assert(await page.locator('#freeGrid .tool').count()>0,'Free view empty')}else{assert(await activeView(page,'library'),`${g} did not open library`);assert(await countFrom(page,'#resultCount')>0,`${g} produced zero results`)}"""
new_goal="""if(g==='no-login'){assert(await activeView(page,'free'),`${g} did not open free view`);assert(await page.locator('#freeGrid .tool').count()>0,'Free view empty')}else if(g==='watch'){assert(await activeView(page,'watch'),'watch did not open Watch view');assert(await page.locator('#view-watch [data-watch-link]').count()>=8,'Watch view missing services')}else{assert(await activeView(page,'library'),`${g} did not open library`);assert(await countFrom(page,'#resultCount')>0,`${g} produced zero results`)}"""
if old_goal in txt:txt=txt.replace(old_goal,new_goal,1)
qa.write_text(txt)

for path in [ROOT/'qa/atlas-common-intents-20.js',ROOT/'qa/atlas-intent-stress-60.js']:
    t=path.read_text().replace(old_fmt,new_fmt).replace(f'===%d'%old_total,f'===%d'%new_total).replace(f'=== {old_total}',f'=== {new_total}')
    path.write_text(t)

rep=json.loads((ROOT/'atlas-build-report.json').read_text())
rep['tool_count']=new_total
rep['bundle_bytes']=len(bundle.encode())
rep['data_b64_bytes']=len(encoded)
rep['sha256']=hashlib.sha256(bundle.encode()).hexdigest()
rep['multimedia_v4']={
 'watch_view':True,
 'official_free_streaming_services':9,
 'new_records':added,
 'watch_intents':['watch-free','library-streaming','nature-livecam','space-streaming'],
 'legal_official_only':True,
 'access_verification_kept_separate':True,
 'post_audit_needs_review':task_pending,
 'non_live_total':not_live,
 'instagram_video_intent_repair':True
}
(ROOT/'atlas-build-report.json').write_text(json.dumps(rep,indent=2)+'\n')

assert 'ATLAS-MULTIMEDIA-V4' in bundle
assert 'id="view-watch"' in bundle
assert 'data-view="watch"' in bundle
assert 'Tubi' in bundle and 'NASA+' in bundle and 'Hoopla' in bundle
assert f'indexedTools":{new_total}' in bundle
print(json.dumps({'old_total':old_total,'new_total':new_total,'added':added,'task_pending':task_pending,'not_live':not_live,'sha256':rep['sha256']},indent=2))