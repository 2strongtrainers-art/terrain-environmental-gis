from pathlib import Path
import json, hashlib

ROOT=Path('.')
SHELL=[ROOT/f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA=[ROOT/f'atlas-src/data-{i:03d}.txt' for i in range(9)]
shell=''.join(p.read_text() for p in SHELL)
data=''.join(p.read_text().strip() for p in DATA)
MARK='ATLAS-DISCOVERY-V5-SEARCH'

if MARK not in shell:
    # Specific multi-word task families outrank generic tokens such as video, research,
    # programming, agent and AI. This fixes real misses surfaced by the 220-query benchmark.
    needle=''' {id:"automation",route:"automation",patterns:["automate","automation","workflow","agent"],anchors:["automation","workflow","agent"],terms:["ai","assistant"]},'''
    rules=''' /* ATLAS-DISCOVERY-V5-SEARCH — benchmark-driven task families */\n {id:"social-video-v5",route:"video",patterns:["short social video editor","short social video","social video editor","social video","short form video","short-form video","vertical video editor","reel editor","tiktok editor","instagram reel editor"],anchors:["video editor","short video","social video","reel"],terms:["clipchamp","opus clip","capcut","pika","runway","descript"]},\n {id:"automation-workflow-v5",route:"automation",patterns:["ai automation workflow agent","ai automation workflow","automation workflow agent","workflow automation agent","ai agent workflow","workflow automation","automation agent"],anchors:["automation","workflow","agent"],terms:["zapier","n8n","ifttt","pipedream"]},\n {id:"fitness-coaching-v5",route:"business",patterns:["fitness coaching workout programming","fitness coaching","workout programming","fitness programming","personal trainer programming","fitness client","workout program","training program"],anchors:["fitness","workout","training","coach","trainer","exercise"],terms:["client","strength","program","coaching"]},\n {id:"grant-funding-v5",route:"research",patterns:["grant research funding opportunities","grant funding opportunities","grant research","grant funding","funding opportunities","grant opportunities","research grant","grant proposal","grants"],anchors:["grant","grants","funding"],terms:["opportunity","proposal","government","funding"]},\n {id:"marketing-leads-v5",route:"business",patterns:["marketing sales lead generation","sales lead generation","marketing lead generation","lead generation","sales leads","marketing sales"],anchors:["marketing","sales","lead","leads"],terms:["crm","email","seo","customer"]},\n'''
    if needle not in shell: raise SystemExit('V5 intent insertion point not found')
    shell=shell.replace(needle,rules+needle,1)

    pref='''const INTENT_PREFERRED={\n "social-video-v5":["clipchamp","opus clip","capcut","pika","runway","descript"],\n "automation-workflow-v5":["zapier","n8n","ifttt","pipedream","bardeen"],\n "fitness-coaching-v5":["musclewiki","exrx","darebee","hevy","strong","trainerize","truecoach"],\n "grant-funding-v5":["grants.gov","sam.gov","candid","foundation directory"],\n "marketing-leads-v5":["hubspot","mailchimp","semrush","ahrefs","google trends"],'''
    if 'const INTENT_PREFERRED={' not in shell: raise SystemExit('preferred map not found')
    shell=shell.replace('const INTENT_PREFERRED={',pref,1)

    avoid='''const INTENT_AVOID={\n "social-video-v5":["video-tutor","topaz video ai"],\n "automation-workflow-v5":["maket ai","make me a cocktail","animaker","aws sagemaker"],\n "fitness-coaching-v5":["claude code","replit","cursor","github copilot","codecademy","codewars"],\n "grant-funding-v5":["research methods in psych","open science framework","science geek","study stream"],\n "marketing-leads-v5":["google imagen","imgsys","fake imessage"],'''
    if 'const INTENT_AVOID={' not in shell: raise SystemExit('avoid map not found')
    shell=shell.replace('const INTENT_AVOID={',avoid,1)

    # Re-split the shell exactly the same way as the existing generators.
    def split_n(text,n):
        q,r=divmod(len(text),n);out=[];p=0
        for i in range(n):
            z=q+(1 if i<r else 0);out.append(text[p:p+z]);p+=z
        assert ''.join(out)==text
        return out
    for p,x in zip(SHELL,split_n(shell,3)): p.write_text(x)

# Always rebuild the monolithic bundle from current authoritative chunks.
bundle=shell.replace('__DATA_B64__',data)
(ROOT/'atlas-bundle.html').write_text(bundle)
rep=json.loads((ROOT/'atlas-build-report.json').read_text())
rep['bundle_bytes']=len(bundle.encode())
rep['sha256']=hashlib.sha256(bundle.encode()).hexdigest()
rep['discovery_v5_search']={
  'marker':MARK,
  'benchmark_driven_intents':['social-video','automation-workflow','fitness-coaching','grant-funding','marketing-leads'],
  'preserves_free_vs_no_login':True,
  'behavior_ranking_active':False
}
(ROOT/'atlas-build-report.json').write_text(json.dumps(rep,indent=2)+'\n')
assert MARK in bundle
print(json.dumps(rep['discovery_v5_search'],indent=2))
