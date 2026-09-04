from pathlib import Path
import base64,gzip,hashlib,json
ROOT=Path('.')
SHELL=[ROOT/f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA=[ROOT/f'atlas-src/data-{i:03d}.txt' for i in range(9)]
shell=''.join(p.read_text() for p in SHELL)
data_b64=''.join(p.read_text().strip() for p in DATA)
records=json.loads(gzip.decompress(base64.b64decode(data_b64)))
assert len(records)==1834
assert 'ATLAS-INTENT-V3' in shell
assert '__DATA_B64__' in shell

if 'ATLAS-INTENT-V31' not in shell:
    marker='const QUERY_MODIFIERS=new Set(["best","easy","easiest","simple","quick","fast","good","great","ai","free"]);'
    assert shell.count(marker)==1
    extra=r'''const QUERY_MODIFIERS=new Set(["best","easy","easiest","simple","quick","fast","good","great","ai","free"]);
/* ATLAS-INTENT-V31 — precision reranking over V3 */
const INTENT_PREFERRED={
 "image-generator":["qwen image","reve image","chatgpt image","google imagen","adobe firefly","midjourney","ideogram","leonardo"],
 "short-video":["pika","runway","capcut","opus clip","clipchamp","descript","synthesia","heygen"],
 logo:["wix logo maker","brandmark","tailor brands","designevo","looka","placeit","canva"],
 resume:["kickresume","flowcv","resume.io","teal","rezi","enhancv"],
 pdf:["ilovepdf","pdfescape","simplepdf","smallpdf","adobe acrobat","pdfgear"],
 "research-summary":["elicit","consensus","scholarcy","scispace","humata","semantic scholar","paperme"],
 citation:["cite this for me","zotero","mybib","scribbr","citation machine"],
 "python-learning":["freecodecamp","kaggle learn","codecademy","microsoft learn","real python","python.org"],
 calculator:["omni calculator","wolfram","symbolab","mathway","desmos"],
 "qr-code":["qrcode monkey","qr code monkey","qr code generator","qrstuff","goqr","canva qr"],
 "weather-map":["zoom earth","windy","ventusky","weather underground","weather.com","meteoblue","rainviewer"],
 "background-removal":["remove.bg","adobe express","iloveimg","unscreen","bg bye","pfpmaker"],
 transcription:["otter","descript","turboscribe","notta","happy scribe","whisper","sonix","trint"],
 "voice-generator":["elevenlabs","speechify","murf","play.ht","tts online","kokoro tts","fish audio"],
 "website-builder":["wix","framer","webflow","squarespace","carrd","wordpress.com","bubble","weebly","dorik"],
 presentation:["gamma","beautiful.ai","decktopus","pitch","canva","slidesgo","slidescarnival"],
 grammar:["grammarly","languagetool","prowritingaid","hemingway","quillbot"],
 translation:["deepl","google translate","reverso","linguee","microsoft translator"],
 "stock-photos":["pexels","unsplash","pixabay","stocksnap","gratisography","freeimages","burst"],
 spreadsheet:["google sheets","microsoft excel","airtable","rows"],
 ocr:["online ocr","ocr.space","adobe scan","google lens"],
 diagram:["lucidchart","draw.io","diagrams.net","whimsical","miro"],
 automation:["zapier","make","n8n","ifttt"],
 coding:["github copilot","cursor","replit","claude code","codex"],
 "image-editing":["photopea","pixlr","adobe express","canva","gimp"]
};
const INTENT_AVOID={
 "qr-code":["papers with code","claude code","codecademy","codepen","100-days-of-ml-code"],
 "website-builder":["3 websites for","work from home websites","mdn web docs","the useless web","animal diversity web"],
 transcription:["tabletop audio","voice models","mmaudio","voicemod tuna"],
 "weather-map":["pantone","wgsn","minecraft"],
 translation:["cdromance","learnalanguage"],
 calculator:["damage calculator"],
 "stock-photos":["getty images","shutterstock","istock","adobe stock"]
};'''
    shell=shell.replace(marker,extra,1)

    replacements={
      '{id:"background-removal",route:"design",patterns:["remove the background","remove background","background remover","transparent background"]':'{id:"background-removal",route:"design",patterns:["remove the background","remove background","background remover","transparent background","erase background","erase image background","image background","photo background","background transparent"]',
      '{id:"voice-generator",route:"video",patterns:["voice generator","ai voice","text to speech","tts","generate voice"]':'{id:"voice-generator",route:"video",patterns:["voice generator","ai voice","text to speech","tts","generate voice","voiceover","voice over","voiceover generator"]',
      '{id:"website-builder",route:"automation",patterns:["build a website","website builder","make a website","create a website","without coding","no code website","nocode website"]':'{id:"website-builder",route:"automation",patterns:["build a website","website builder","make a website","create a website","without coding","no code website","nocode website","build a web page","web page visually","visual website builder"]'
    }
    for old,new in replacements.items():
        assert shell.count(old)==1,old
        shell=shell.replace(old,new,1)

    old=''' if(p.intent&&anchorHit===0)s*=0.16;\n if(p.wantsFree){if(idx.pricing.includes("free"))s+=26;else if(idx.pricing.includes("paid"))s-=8}\n if(p.explicitNoLogin){if(idx.access.includes("no login")||idx.access.includes("optional login"))s+=70;else s-=12}\n if(t.verification==="Live verified")s+=4;if(t.priority==="High")s+=2;'''
    new=''' if(p.intent&&anchorHit===0)s*=0.08;\n if(p.intent){const pref=INTENT_PREFERRED[p.intent.id]||[];for(let i=0;i<pref.length;i++){const n=normalizeText(pref[i]);if(idx.name===n)s+=260-i*5;else if(idx.name.includes(n)||n.includes(idx.name))s+=175-i*3;else if(idx.desc.includes(n))s+=55-i}const avoid=INTENT_AVOID[p.intent.id]||[];for(const n0 of avoid){const n=normalizeText(n0);if(idx.name.includes(n))s-=180}}\n if(p.wantsFree){if(idx.pricing.includes("free"))s+=34;else if(idx.pricing.includes("paid"))s-=18;if(/getty|shutterstock|istock|adobe stock/.test(idx.name))s-=160}\n if(p.explicitNoLogin){if(idx.access.includes("no login")||idx.access.includes("optional login"))s+=90;else s-=18}\n if(t.verification==="Live verified")s+=5;if(t.priority==="High")s+=2;'''
    assert shell.count(old)==1
    shell=shell.replace(old,new,1)

    old=''' let arr=TOOLS.filter(t=>{\n  if(state.source&&t.sourceCategory!==state.source&&!t.sourceCategories?.includes(state.source))return false;\n  if(state.pricing&&t.pricing!==state.pricing)return false;\n  if(state.verification==="Live verified"&&t.verification!=="Live verified")return false;\n  if(state.verification==="not-live"&&t.verification==="Live verified")return false;\n  if(state.verification&&state.verification!=="Live verified"&&state.verification!=="not-live"&&t.verification!==state.verification)return false;\n  if(state.priority&&t.priority!==state.priority)return false;\n  if(state.favoritesOnly&&!favorites.has(t.id))return false;\n  if(hasQuery&&scoreTool(t,parsed)<=3)return false;\n  return true;\n });'''
    new=''' let arr=TOOLS.filter(t=>{\n  if(state.source&&t.sourceCategory!==state.source&&!t.sourceCategories?.includes(state.source))return false;\n  if(state.pricing&&t.pricing!==state.pricing)return false;\n  if(state.verification==="Live verified"&&t.verification!=="Live verified")return false;\n  if(state.verification==="not-live"&&t.verification==="Live verified")return false;\n  if(state.verification&&state.verification!=="Live verified"&&state.verification!=="not-live"&&t.verification!==state.verification)return false;\n  if(state.priority&&t.priority!==state.priority)return false;\n  if(state.favoritesOnly&&!favorites.has(t.id))return false;\n  return true;\n });\n if(hasQuery&&arr.length){const scored=arr.map(t=>[t,scoreTool(t,parsed)]);const max=Math.max(...scored.map(x=>x[1]));let floor=parsed.intent?Math.max(14,max*0.16):5;let kept=scored.filter(x=>x[1]>=floor);if(kept.length<5)kept=scored.sort((a,b)=>b[1]-a[1]).slice(0,Math.min(20,scored.length)).filter(x=>x[1]>3);arr=kept.map(x=>x[0])}'''
    assert shell.count(old)==1
    shell=shell.replace(old,new,1)

    # Score-aware sorting already works; improve user-facing explanation.
    shell=shell.replace('Rank all 1,834 tools by task relevance →','Rank the strongest task matches across all 1,834 tools →',1)
    shell=shell.replace('Search naturally by task. Atlas weights exact capability matches above broad categories, with typo tolerance, synonyms and transparent filters.','Search naturally by task. Atlas prioritizes exact capability matches, trusted task-specific candidates and modifiers like free/no-login before broad categories.',1)

# rewrite source and bundle
def split_n(text,n):
    q,r=divmod(len(text),n);out=[];p=0
    for i in range(n):
        z=q+(1 if i<r else 0);out.append(text[p:p+z]);p+=z
    return out
parts=split_n(shell,3)
assert ''.join(parts)==shell
for p,x in zip(SHELL,parts):p.write_text(x)
bundle=shell.replace('__DATA_B64__',data_b64)
(ROOT/'atlas-bundle.html').write_text(bundle)
rep=json.loads((ROOT/'atlas-build-report.json').read_text())
rep['bundle_bytes']=len(bundle.encode());rep['sha256']=hashlib.sha256(bundle.encode()).hexdigest()
rep['intent_v31']={'precision_reranking':True,'preferred_task_candidates':True,'intent_avoid_lists':True,'dynamic_relevance_floor':True,'free_paid_penalty':True,'voiceover_background_webpage_expansion':True}
(ROOT/'atlas-build-report.json').write_text(json.dumps(rep,indent=2)+'\n')
assert 'ATLAS-INTENT-V31' in bundle
print(json.dumps(rep,indent=2))