from pathlib import Path
import json,re

ROOT=Path('.')
report=json.loads((ROOT/'atlas-build-report.json').read_text())
total=int(report['tool_count'])
verified=int(report.get('verified_count', report.get('live_verified', 1529)))
# The V5.1 build report records the non-live total after adding new Needs review destinations.
non_live=int(report.get('discovery_v51',{}).get('non_live_total', total-verified))
fmt=f'{total:,}'

# Stress benchmark: initialization should follow the generated build, not a historical count.
p=ROOT/'qa/atlas-intent-stress-60.js'
s=p.read_text()
s=re.sub(r"await p\.waitForFunction\(\(\)=>document\.querySelector\('#statIndexed'\)\?\.textContent\?\.includes\('[\d,]+'\)\);",
         f"await p.waitForFunction(()=>Number((document.querySelector('#statIndexed')?.textContent||'').replace(/,/g,''))==={total});",s)
p.write_text(s)

# Watch QA already centralizes its expected total.
p=ROOT/'qa/atlas-watch-multimedia.js'
s=p.read_text()
s=re.sub(r'const EXPECTED_TOTAL=\d+;',f'const EXPECTED_TOTAL={total};',s)
p.write_text(s)

# Full regression: synchronize only factual build-count expectations; leave feature assertions strict.
p=ROOT/'qa/atlas-live-qa.js'
s=p.read_text()
s=re.sub(r"textContent\?\.includes\('[\d,]+'\)",f"textContent?.includes('{fmt}')",s)
s=re.sub(r"assert\(a==='[\d,]+'",f"assert(a==='{fmt}'",s)
s=re.sub(r'button:has-text\(\\"Browse all [\d,]+ tools\\"\)',f'button:has-text(\\"Browse all {fmt} tools\\")',s)
s=s.replace('===1846',f'==={total}').replace('1,846 results',f'{fmt} results').replace('1,846-result',f'{fmt}-result')
s=s.replace('===317',f'==={non_live}').replace('317 non-live-verified records',f'{non_live} non-live-verified records')
s=s.replace("not-live=317",f"not-live={non_live}")
# Keep verified count synchronized if the audit count changes in a later build.
s=re.sub(r'===1529',f'==={verified}',s).replace('Live verified=1,529',f'Live verified={verified:,}')
p.write_text(s)

print(json.dumps({'tool_count':total,'verified':verified,'non_live':non_live,'qa_counts_synchronized':True},indent=2))
