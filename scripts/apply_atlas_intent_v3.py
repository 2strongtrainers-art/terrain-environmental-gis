from pathlib import Path
import base64, gzip, hashlib, json

ROOT=Path('.')
SHELL_FILES=[ROOT/f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA_FILES=[ROOT/f'atlas-src/data-{i:03d}.txt' for i in range(9)]
shell=''.join(p.read_text() for p in SHELL_FILES)
data_b64=''.join(p.read_text().strip() for p in DATA_FILES)
records=json.loads(gzip.decompress(base64.b64decode(data_b64)))
assert len(records)==1834
assert '__DATA_B64__' in shell

if 'ATLAS-INTENT-V3' not in shell:
    start=shell.index('const SEARCH_ALIASES={')
    end=shell.index('\nfunction saveFav()', start)
    engine=r'''/* ATLAS-INTENT-V3 — task-first ranking, modifiers, synonyms, fuzzy matching */
const SEARCH_ALIASES={
 photo:["image","picture"],photos:["image","picture","stock"],picture:["image","photo"],pictures:["image","photo"],
 movie:["video"],film:["video"],reel:["video","clip"],reels:["video","clip"],shorts:["video","clip"],
 website:["site","web"],site:["website","web"],webpage:["website","site"],nocode:["no code","website builder"],
 automate:["automation","workflow"],automation:["workflow","agent"],study:["research","learn"],researching:["research"],
 cv:["resume"],mapping:["map","gis"],gis:["map","mapping"],voice:["audio","speech","tts"],audio:["voice","sound"],
 logo:["branding","design"],slides:["presentation","slideshow","deck"],presentation:["slides","slideshow","deck"],
 write:["writing","writer"],writer:["writing"],proofread:["grammar","writing"],proofreading:["grammar","writing"],
 translate:["translation","translator","language"],translator:["translate","translation"],transcribe:["transcription","speech to text"],
 transcription:["transcribe","speech to text"],citation:["cite","bibliography","reference"],citations:["citation","bibliography","reference"],
 qr:["qr code"],math:["calculator","calculate"],calculate:["calculator"],python:["programming","coding"],pdf:["document"],
 background:["remove background","background remover","transparent"],stock:["stock photo","stock image","royalty free"],
 weather:["forecast","radar"],resume:["cv","career"],grammar:["proofread","writing"],spreadsheet:["excel","sheets"],
 speech:["voice","audio"],tts:["text to speech","voice"],ocr:["image to text","scan"],diagram:["flowchart","visualize"]
};
const QUERY_STOP=new Set("i me my we our us you your a an the this that these those is are am be been being to for of on in at by with from into and or but if then than as it its do does did can could would should please help need want find give show make create use using get tool tools useful something thing online today right now".split(/\s+/));
const QUERY_MODIFIERS=new Set(["best","easy","easiest","simple","quick","fast","good","great","ai","free"]);
const INTENT_RULES=[
 {id:"image-generator",route:"design",patterns:["image generator","ai image","generate image","generate images","text to image","make an image","create image"],anchors:["image generator","text to image","image","art"],terms:["generator","photo","picture","design"]},
 {id:"short-video",route:"video",patterns:["short video","social media video","make a video","create a video","video for social","reel","shorts"],anchors:["video","reel","clip"],terms:["editor","generator","social media","media"]},
 {id:"logo",route:"design",patterns:["design a logo","make a logo","create a logo","logo"],anchors:["logo","branding","brand"],terms:["design","graphic"]},
 {id:"resume",route:"business",patterns:["resume","cv","curriculum vitae"],anchors:["resume","cv"],terms:["career","job","application","builder"]},
 {id:"pdf",route:"research",patterns:["pdf","edit pdf","work with a pdf","pdf editor","pdf converter"],anchors:["pdf"],terms:["document","editor","edit","convert","merge","compress","annotate"]},
 {id:"research-summary",route:"research",patterns:["summarize a research paper","summarize research","research paper","academic paper","paper summary"],anchors:["research","paper","academic","scholar"],terms:["summary","summarize","study","science"]},
 {id:"citation",route:"research",patterns:["citation","citation generator","bibliography","cite source","apa citation","mla citation"],anchors:["citation","bibliography","cite"],terms:["reference","apa","mla","academic"]},
 {id:"python-learning",route:"research",patterns:["learn python","python course","python tutorial","python programming"],anchors:["python"],terms:["learn","course","tutorial","programming","coding"]},
 {id:"calculator",route:"research",patterns:["calculator","calculate","math problem","equation solver"],anchors:["calculator","calculate"],terms:["math","equation","solver","formula"]},
 {id:"qr-code",route:"automation",patterns:["qr code","make a qr","create a qr","qr generator"],anchors:["qr","qr code"],terms:["generator","barcode","code"]},
 {id:"weather-map",route:"maps",patterns:["weather","forecast","weather map","weather or map","radar map"],anchors:["weather","forecast","radar"],terms:["map","earth","geo","gis"]},
 {id:"background-removal",route:"design",patterns:["remove the background","remove background","background remover","transparent background"],anchors:["background","background remover","remove background"],terms:["image","photo","transparent","cutout"]},
 {id:"transcription",route:"video",patterns:["transcribe","transcription","audio to text","speech to text","voice recording to text"],anchors:["transcribe","transcription","speech to text"],terms:["audio","voice","recording","text"]},
 {id:"voice-generator",route:"video",patterns:["voice generator","ai voice","text to speech","tts","generate voice"],anchors:["voice","text to speech","tts"],terms:["speech","audio","generator","narration"]},
 {id:"website-builder",route:"automation",patterns:["build a website","website builder","make a website","create a website","without coding","no code website","nocode website"],anchors:["website","website builder","site builder","no code"],terms:["web","builder","site","design","hosting"]},
 {id:"presentation",route:"design",patterns:["presentation","slideshow","slide deck","powerpoint","create slides","make slides"],anchors:["presentation","slides","slideshow","powerpoint","deck"],terms:["design","pitch"]},
 {id:"grammar",route:"research",patterns:["grammar","check my writing","grammar checker","proofread","spell check"],anchors:["grammar","proofread","spell"],terms:["writing","editor","rewrite"]},
 {id:"translation",route:"research",patterns:["translate","translation","translator","another language"],anchors:["translate","translation","translator"],terms:["language","text"]},
 {id:"stock-photos",route:"design",patterns:["stock photos","stock photo","free photos","royalty free photos","stock images"],anchors:["stock photo","stock image","photo","image"],terms:["royalty free","pictures"]},
 {id:"spreadsheet",route:"business",patterns:["spreadsheet","excel","google sheets"],anchors:["spreadsheet","excel","sheets"],terms:["data","table","csv"]},
 {id:"ocr",route:"research",patterns:["ocr","image to text","scan text","extract text from image"],anchors:["ocr","image to text"],terms:["scan","text","document"]},
 {id:"diagram",route:"design",patterns:["diagram","flowchart","mind map","mindmap"],anchors:["diagram","flowchart","mind map"],terms:["visual","chart"]},
 {id:"automation",route:"automation",patterns:["automate","automation","workflow","agent"],anchors:["automation","workflow","agent"],terms:["ai","assistant"]},
 {id:"coding",route:"automation",patterns:["coding","programming","write code","developer"],anchors:["code","coding","programming","developer"],terms:["ai","assistant"]},
 {id:"image-editing",route:"design",patterns:["edit image","edit photo","photo editor","image editor"],anchors:["image","photo"],terms:["editor","edit","design"]},
 {id:"video",route:"video",patterns:["video"],anchors:["video"],terms:["editor","generator","media"]},
 {id:"research",route:"research",patterns:["research","study","science"],anchors:["research","study","science"],terms:["learn","academic"]},
 {id:"maps",route:"maps",patterns:["map","mapping","gis","terrain"],anchors:["map","mapping","gis","terrain"],terms:["geo","earth"]},
 {id:"writing",route:"research",patterns:["writing","write","rewrite"],anchors:["writing","writer","rewrite"],terms:["editor","text"]}
];
function normalizeText(s){return String(s??"").normalize("NFKD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
function oneEditAway(a,b){if(a===b)return true;if(Math.abs(a.length-b.length)>1)return false;let i=0,j=0,e=0;while(i<a.length&&j<b.length){if(a[i]===b[j]){i++;j++;continue}if(++e>1)return false;if(a.length>b.length)i++;else if(b.length>a.length)j++;else{i++;j++;}}return e+(i<a.length||j<b.length?1:0)<=1}
const SEARCH_INDEX=new Map(TOOLS.map(t=>{const name=normalizeText(t.name),desc=normalizeText(t.description),tax=normalizeText([t.sourceCategory,t.section,t.subsection,t.curatedCategory].join(" ")),pricing=normalizeText(t.pricing),access=normalizeText(t.accessType);return [t.id,{name,desc,tax,pricing,access,all:[name,desc,tax,pricing,access].join(" "),tokens:[...new Set([name,desc,tax].join(" ").split(/\s+/).filter(Boolean))]}]}));
function parseSmartQuery(q){
 const norm=normalizeText(q),raw=norm.split(/\s+/).filter(Boolean);
 const explicitNoLogin=/(no login|no account|without an account|without account|without creating an account|without signing up|without sign up|no signup|no sign up)/.test(norm);
 const wantsFree=/\bfree\b/.test(norm);
 let intent=null,best=0;
 for(const rule of INTENT_RULES){let s=0;for(const p of rule.patterns){if(norm.includes(p))s=Math.max(s,p.split(" ").length*10+p.length/20)}if(s>best){best=s;intent=rule}}
 const rawTokens=raw.filter(x=>!QUERY_STOP.has(x)&&!QUERY_MODIFIERS.has(x)&&x.length>1);
 const anchors=intent?intent.anchors:[];
 const extras=intent?intent.terms:[];
 const tokenSet=new Set(rawTokens);
 for(const a of anchors)for(const x of normalizeText(a).split(" "))if(x.length>1)tokenSet.add(x);
 for(const x of extras)for(const t of normalizeText(x).split(" "))if(t.length>2)tokenSet.add(t);
 return {norm,rawTokens,tokens:[...tokenSet],intent,anchors,extras,wantsFree,explicitNoLogin};
}
function phraseScore(idx,p){p=normalizeText(p);if(!p)return 0;let s=0;if(idx.name===p)s+=130;else if(idx.name.includes(p))s+=80;if(idx.desc.includes(p))s+=34;if(idx.tax.includes(p))s+=10;return s}
function tokenScore(idx,t){let s=0;if(!t||t.length<2)return 0;if(idx.name.split(" ").includes(t))s+=28;else if(idx.name.includes(t))s+=16;if(idx.desc.split(" ").includes(t))s+=10;else if(idx.desc.includes(t))s+=6;if(idx.tax.split(" ").includes(t))s+=3;const al=SEARCH_ALIASES[t]||[];for(const a of al){const n=normalizeText(a);if(idx.name.includes(n))s+=12;if(idx.desc.includes(n))s+=5;if(idx.tax.includes(n))s+=2}if(t.length>=5&&s===0&&idx.tokens.some(tok=>Math.abs(tok.length-t.length)<=1&&oneEditAway(t,tok)))s+=4;return s}
function scoreTool(t,q){
 const p=typeof q==="string"?parseSmartQuery(q):q,idx=SEARCH_INDEX.get(t.id);if(!p.norm)return 1;
 let s=0,anchorHit=0;
 if(p.intent){for(const a of p.anchors){const ps=phraseScore(idx,a);if(ps>0)anchorHit++;s+=ps}for(const e of p.extras)s+=phraseScore(idx,e)*0.32}
 for(const tok of p.rawTokens)s+=tokenScore(idx,tok)*1.35;
 for(const tok of p.tokens)s+=tokenScore(idx,tok)*0.45;
 if(p.intent&&anchorHit===0)s*=0.16;
 if(p.wantsFree){if(idx.pricing.includes("free"))s+=26;else if(idx.pricing.includes("paid"))s-=8}
 if(p.explicitNoLogin){if(idx.access.includes("no login")||idx.access.includes("optional login"))s+=70;else s-=12}
 if(t.verification==="Live verified")s+=4;if(t.priority==="High")s+=2;
 if(/^(Dead \/ unavailable|Parked \/ for sale)$/.test(t.verification||""))s-=60;
 return s;
}
function matchesQuery(t,q){return scoreTool(t,q)>3}
'''
    shell=shell[:start]+engine+shell[end:]

    # Replace the generic category-first command router with task-first matching.
    start=shell.index('function routeCommand(){')
    end=shell.index('$("#routeBtn").onclick=routeCommand;', start)
    router=r'''function applyIntentSearch(q){
 const p=parseSmartQuery(q);state.query=q;state.source="";state.pricing="";state.verification="";state.priority="";state.sort="relevance";state.page=1;state.favoritesOnly=false;
 showView("library");$("#searchInput").value=q;$("#sourceFilter").value="";$("#pricingFilter").value="";$("#verificationFilter").value="";$("#priorityFilter").value="";$("#sortFilter").value="relevance";$("#favOnly").classList.remove("active");renderLibrary();
 trackAtlas("atlas_intent_search",{intent:p.intent?.id||"general",query_length:p.norm.length,result_count:getFiltered().length,wants_free:p.wantsFree,no_login:p.explicitNoLogin});
}
function routeCommand(){
 const raw=$("#commandInput").value.trim();const p=parseSmartQuery(raw);
 if(!p.norm){$("#routeSuggestions").innerHTML='<div class="suggestion"><b>Tell me the outcome.</b><span>For example: make a video, edit a PDF, create a logo, learn Python, or find a no-login tool.</span></div>';return}
 const genericNoLogin=p.explicitNoLogin&&!p.intent;
 let html="";
 if(genericNoLogin)html+='<button class="suggestion" data-route="no-login" style="text-align:left;cursor:pointer"><b>Free • No Login</b><span>Only explicitly audited no-account tools →</span></button>';
 else html+=`<button class="suggestion" data-smart-query="${esc(raw)}" style="text-align:left;cursor:pointer"><b>Best matches for this task</b><span>Rank all 1,834 tools by task relevance →</span></button>`;
 const route=p.intent?.route;
 if(route&&route!=="no-login")html+=`<button class="suggestion" data-route="${route}" style="text-align:left;cursor:pointer"><b>${esc(ROUTES[route].label)}</b><span>Browse the broader category →</span></button>`;
 if(p.explicitNoLogin&&!genericNoLogin)html+='<button class="suggestion" data-route="no-login" style="text-align:left;cursor:pointer"><b>Strict no-login collection</b><span>Only explicitly audited no-account tools →</span></button>';
 $("#routeSuggestions").innerHTML=html;
 $$("[data-smart-query]").forEach(x=>x.onclick=()=>applyIntentSearch(raw));
 $$("[data-route]").forEach(x=>x.onclick=()=>applyGoal(x.dataset.route));
 trackAtlas("atlas_command_submit",{query_length:p.norm.length,intent:p.intent?.id||"general",wants_free:p.wantsFree,no_login:p.explicitNoLogin});
}
'''
    shell=shell[:start]+router+shell[end:]

    # Replace library filtering/ranking with weighted relevance rather than all-terms AND matching.
    start=shell.index('function tokenize(q)')
    end=shell.index('function toolCard(t){', start)
    filtering=r'''function tokenize(q){return normalizeText(q).split(/\s+/).filter(Boolean)}
function getFiltered(){
 const hasQuery=!!normalizeText(state.query);const parsed=hasQuery?parseSmartQuery(state.query):null;
 let arr=TOOLS.filter(t=>{
  if(state.source&&t.sourceCategory!==state.source&&!t.sourceCategories?.includes(state.source))return false;
  if(state.pricing&&t.pricing!==state.pricing)return false;
  if(state.verification==="Live verified"&&t.verification!=="Live verified")return false;
  if(state.verification==="not-live"&&t.verification==="Live verified")return false;
  if(state.verification&&state.verification!=="Live verified"&&state.verification!=="not-live"&&t.verification!==state.verification)return false;
  if(state.priority&&t.priority!==state.priority)return false;
  if(state.favoritesOnly&&!favorites.has(t.id))return false;
  if(hasQuery&&scoreTool(t,parsed)<=3)return false;
  return true;
 });
 if(state.sort==="az")arr.sort((a,b)=>a.name.localeCompare(b.name));
 else if(state.sort==="verified")arr.sort((a,b)=>(b.verification==="Live verified")-(a.verification==="Live verified")||a.name.localeCompare(b.name));
 else if(state.sort==="priority"){const p={High:3,Medium:2,Low:1};arr.sort((a,b)=>(p[b.priority]||0)-(p[a.priority]||0)||a.name.localeCompare(b.name))}
 else if(hasQuery)arr.sort((a,b)=>scoreTool(b,parsed)-scoreTool(a,parsed)||a.name.localeCompare(b.name));
 return arr;
}
'''
    shell=shell[:start]+filtering+shell[end:]

    # Improve copy around the smart finder and search.
    shell=shell.replace('Describe the outcome—not the software. The Atlas will show matching tools and categories.','Describe the outcome—not the software. The Atlas ranks all 1,834 tools for your task, then offers broader categories when useful.',1)
    shell=shell.replace('Search names, descriptions, categories and subcategories. Filters operate locally and instantly.','Search naturally by task. Atlas weights exact capability matches above broad categories, with typo tolerance, synonyms and transparent filters.',1)

    # Marker and tiny visual cue for relevance mode.
    shell=shell.replace('</style>','/* ATLAS-INTENT-V3 */\n.suggestion[data-smart-query]{border-color:#8ddbd5;background:#f2fbfa}.suggestion[data-smart-query] b{color:#0a6667}\n</style>',1)

# Split source, rebuild bundle.
def split_n(text,n):
    q,r=divmod(len(text),n);out=[];pos=0
    for i in range(n):
        size=q+(1 if i<r else 0);out.append(text[pos:pos+size]);pos+=size
    assert ''.join(out)==text
    return out
for i,part in enumerate(split_n(shell,3)):SHELL_FILES[i].write_text(part)
bundle=shell.replace('__DATA_B64__',data_b64)
(ROOT/'atlas-bundle.html').write_text(bundle)
report=json.loads((ROOT/'atlas-build-report.json').read_text())
report['bundle_bytes']=len(bundle.encode())
report['sha256']=hashlib.sha256(bundle.encode()).hexdigest()
report['intent_v3']={'task_first_router':True,'weighted_field_ranking':True,'intent_taxonomy':len(29*[0]),'free_vs_no_login_separated':True,'query_preserved_after_route':True,'fuzzy_synonyms':True}
(ROOT/'atlas-build-report.json').write_text(json.dumps(report,indent=2)+'\n')
assert 'ATLAS-INTENT-V3' in bundle
assert 'Best matches for this task' in bundle
assert 'scoreTool(t,parsed)' in bundle
assert 'genericNoLogin' in bundle
print(json.dumps(report,indent=2))