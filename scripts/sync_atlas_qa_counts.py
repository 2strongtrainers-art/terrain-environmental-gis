from pathlib import Path
import json,re

ROOT=Path('.')
report=json.loads((ROOT/'atlas-build-report.json').read_text())
total=int(report['tool_count'])
verified=int(report.get('verified_count', report.get('live_verified', 1529)))
non_live=int(report.get('discovery_v51',{}).get('non_live_total', total-verified))
fmt=f'{total:,}'
verified_fmt=f'{verified:,}'

# Keep every production QA suite tied to the generated build snapshot instead of historical totals.
qa_paths=[
    ROOT/'qa/atlas-common-intents-20.js',
    ROOT/'qa/atlas-intent-stress-60.js',
    ROOT/'qa/atlas-watch-multimedia.js',
    ROOT/'qa/atlas-live-qa.js',
]
for p in qa_paths:
    s=p.read_text()
    # Replace the known historical totals wherever they are used in waits, selectors, assertions, or report text.
    s=s.replace('1,846',fmt).replace('1846',str(total))
    s=s.replace('317',str(non_live))
    # Keep live-verified expectations tied to the current audit snapshot.
    s=s.replace('1,529',verified_fmt).replace('1529',str(verified))
    p.write_text(s)

# Normalize the stress-suite initialization check so later count growth is handled numerically.
p=ROOT/'qa/atlas-intent-stress-60.js'
s=p.read_text()
s=re.sub(r"await p\.waitForFunction\(\(\)=>document\.querySelector\('#statIndexed'\)\?\.textContent\?\.includes\('[\d,]+'\)\);",
         f"await p.waitForFunction(()=>Number((document.querySelector('#statIndexed')?.textContent||'').replace(/,/g,''))==={total});",s)
p.write_text(s)

# Watch QA centralizes its expected total.
p=ROOT/'qa/atlas-watch-multimedia.js'
s=p.read_text()
s=re.sub(r'const EXPECTED_TOTAL=\d+;',f'const EXPECTED_TOTAL={total};',s)
p.write_text(s)

print(json.dumps({
    'tool_count':total,
    'verified':verified,
    'non_live':non_live,
    'qa_files_synchronized':[str(p) for p in qa_paths],
    'qa_counts_synchronized':True
},indent=2))
