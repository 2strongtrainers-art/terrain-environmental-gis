from pathlib import Path
import base64,gzip,hashlib,json,re
ROOT=Path('.')
SHELL=[ROOT/f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA=[ROOT/f'atlas-src/data-{i:03d}.txt' for i in range(9)]
shell=''.join(p.read_text() for p in SHELL)
data_b64=''.join(p.read_text().strip() for p in DATA)
records=json.loads(gzip.decompress(base64.b64decode(data_b64)))
assert 'ATLAS-INTENT-V31' in shell
assert '__DATA_B64__' in shell
old_total=len(records)

# High-demand gaps found by live task testing. These are official destinations validated by current web research.
# Access type remains Unknown unless explicitly audited; verification remains Needs review until the full browser-link audit merges them.
essentials=[
 ['curated-qrcode-monkey','QRCode Monkey','https://www.qrcode-monkey.com/','Free QR code generator for creating custom QR codes with logos and high-resolution PNG, SVG, PDF, and EPS exports.','Free','Curated Library','Task Essentials','QR Codes','General Utility','High','Needs review','Unknown','Official-site capability validated 2026-09-04; access not audited.'],
 ['curated-otter-ai','Otter.ai','https://otter.ai/','AI transcription and meeting-notes tool that can import audio or video files and generate transcripts, summaries, action items, and outlines.','Free / Paid','Curated Library','Task Essentials','Transcription','AI & Automation','High','Needs review','Unknown','Official-site capability and free Basic tier validated 2026-09-04; access not audited.'],
 ['curated-deepl-translator','DeepL Translator','https://www.deepl.com/en/translate','Translation tool for text and files with support for multiple languages and document translation.','Not verified','Curated Library','Task Essentials','Translation','General Utility','High','Needs review','Unknown','Official-site translation capability validated 2026-09-04; pricing/access not audited.'],
 ['curated-wix-builder','Wix Website Builder','https://www.wix.com/','No-code website builder with drag-and-drop editing, templates, AI-assisted site creation, hosting, and business features.','Free / Paid','Curated Library','Task Essentials','Website Builders','Design & Creative','High','Needs review','Unknown','Official-site no-code builder and free option validated 2026-09-04; access not audited.']
]
existing_urls={str(r[2]).rstrip('/').lower() for r in records}
existing_names={str(r[1]).strip().lower() for r in records}
added=[]
for row in essentials:
    key=row[2].rstrip('/').lower()
    if key not in existing_urls and row[1].lower() not in existing_names:
        records.append(row);added.append(row[1]);existing_urls.add(key);existing_names.add(row[1].lower())
new_total=len(records)

if 'ATLAS-INTENT-V32' not in shell:
    # Expand phrase coverage surfaced by the 60-query stress test.
    repl={
      'patterns:["image generator","ai image","generate image","generate images","text to image","make an image","create image"]':'patterns:["image generator","ai image","generate image","generate images","generate an image","image maker","text to image","make an image","create image"]',
      'patterns:["short video","social media video","make a video","create a video","video for social","reel","shorts"]':'patterns:["short video","social media video","make a video","create a video","video for social","tiktok video","instagram video","video for instagram","reel","shorts"]',
      'patterns:["citation","citation generator","bibliography","cite source","apa citation","mla citation"]':'patterns:["citation","citation generator","bibliography","cite source","cite my source","cite my sources","apa citation","mla citation"]',
      'patterns:["calculator","calculate","math problem","equation solver"]':'patterns:["calculator","calculate","math problem","equation solver","math equation","solve an equation","solve a math equation","solve math equation"]',
      'patterns:["transcribe","transcription","audio to text","speech to text","voice recording to text"]':'patterns:["transcribe","transcription","audio transcription","audio to text","speech to text","speech to text tool","voice recording to text","voice recording into text","turn voice recording into text"]'
    }
    for old,new in repl.items():
        if old not in shell: raise SystemExit('missing pattern '+old)
        shell=shell.replace(old,new,1)

    # Add the newly validated exact candidates and hard-exclude known false-positive titles for task-specific intents.
    old=''' "qr-code":["qrcode monkey","qr code monkey","qr code generator","qrstuff","goqr","canva qr"],'''
    new=''' "qr-code":["qrcode monkey","qr code monkey","qr code generator","qrstuff","goqr","canva qr"],'''
    assert old in shell
    # Existing list already names QRCode Monkey; the new curated row makes the preference actionable.

    shell=shell.replace(''' transcription:["tabletop audio","voice models","mmaudio","voicemod tuna"],''',''' transcription:["tabletop audio","voice models","mmaudio","voicemod tuna","complex function plotter","surface plotter","direction field plotter","musicfx"],''',1)
    shell=shell.replace(''' "website-builder":["3 websites for","work from home websites","mdn web docs","the useless web","animal diversity web"],''',''' "website-builder":["3 websites for","work from home websites","mdn web docs","the useless web","animal diversity web","wix logo maker"],''',1)
    shell=shell.replace(''' translation:["cdromance","learnalanguage"],''',''' translation:["cdromance","learnalanguage","deeplearning ai","languagetool","textcraft","chemlibretexts"],''',1)

    old='''for(const n0 of avoid){const n=normalizeText(n0);if(idx.name.includes(n))s-=180}'''
    new='''for(const n0 of avoid){const n=normalizeText(n0);if(idx.name.includes(n))return -999}'''
    assert old in shell
    shell=shell.replace(old,new,1)

    # Keep task-mode results focused. Generic library searches remain broad.
    old='''if(kept.length<5)kept=scored.sort((a,b)=>b[1]-a[1]).slice(0,Math.min(20,scored.length)).filter(x=>x[1]>3);arr=kept.map(x=>x[0])}'''
    new='''if(kept.length<5)kept=scored.sort((a,b)=>b[1]-a[1]).slice(0,Math.min(20,scored.length)).filter(x=>x[1]>3);kept.sort((a,b)=>b[1]-a[1]);if(parsed.intent)kept=kept.slice(0,30);arr=kept.map(x=>x[0])}'''
    assert old in shell
    shell=shell.replace(old,new,1)

    # Visible marker and trust copy: task ranking can say when exact matches are being prioritized without implying universal perfection.
    shell=shell.replace('/* ATLAS-INTENT-V3 */','/* ATLAS-INTENT-V3 */\n/* ATLAS-INTENT-V32 — high-demand coverage + false-positive suppression */',1)
    shell=shell.replace('Describe the outcome—not the software. The Atlas ranks all 1,834 tools for your task, then offers broader categories when useful.','Describe the outcome—not the software. Atlas ranks the strongest task matches first, then offers broader categories when useful.',1)

# Update dataset and every user-facing total from the previous count to the current count.
old_fmt=f'{old_total:,}'; new_fmt=f'{new_total:,}'
shell=shell.replace(old_fmt,new_fmt)
shell=re.sub(r'"indexedTools":\s*'+str(old_total), '"indexedTools":'+str(new_total), shell, count=1)
# The replacement above may already have updated numeric text if it appeared comma-formatted only; enforce exact META.
shell=re.sub(r'"indexedTools":\s*\d+', '"indexedTools":'+str(new_total), shell, count=1)

# Encode the augmented dataset and re-split source/data chunks.
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

# Keep QA harnesses synchronized with the current dataset count.
for path in [ROOT/'qa/atlas-live-qa.js',ROOT/'qa/atlas-common-intents-20.js',ROOT/'qa/atlas-intent-stress-60.js']:
    txt=path.read_text()
    txt=txt.replace(old_fmt,new_fmt).replace(f'===%d'%old_total,f'===%d'%new_total).replace(f'=== {old_total}',f'=== {new_total}')
    path.write_text(txt)

rep=json.loads((ROOT/'atlas-build-report.json').read_text())
rep['tool_count']=new_total;rep['bundle_bytes']=len(bundle.encode());rep['data_b64_bytes']=len(encoded);rep['sha256']=hashlib.sha256(bundle.encode()).hexdigest()
rep['intent_v32']={'high_demand_gap_fill':added,'total_tools':new_total,'phrase_coverage_expanded':True,'hard_false_positive_exclusion':True,'task_results_capped':30,'strict_free_vs_no_login_preserved':True}
(ROOT/'atlas-build-report.json').write_text(json.dumps(rep,indent=2)+'\n')
assert 'ATLAS-INTENT-V32' in bundle
assert f'indexedTools":{new_total}' in bundle
assert any(r[1]=='QRCode Monkey' for r in records)
print(json.dumps({'old_total':old_total,'new_total':new_total,'added':added,'sha256':rep['sha256']},indent=2))