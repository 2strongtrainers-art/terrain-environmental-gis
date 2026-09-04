from pathlib import Path
import base64, gzip, hashlib, json

ROOT = Path('.')
SHELL = [ROOT / f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA = [ROOT / f'atlas-src/data-{i:03d}.txt' for i in range(9)]
shell = ''.join(p.read_text() for p in SHELL)
data_b64 = ''.join(p.read_text().strip() for p in DATA)
records = json.loads(gzip.decompress(base64.b64decode(data_b64)))
MARK = 'ATLAS-DISCOVERY-V51'
old_total = len(records)

# The expanded benchmark exposed one concentrated gap: all ten grant/funding
# paraphrases were being swallowed by the older generic research intent.  Put a
# high-specificity grant rule before generic intents, while preserving the
# existing V5 preferred/avoid maps and strict access semantics.
if MARK not in shell:
    anchor = 'const INTENTS=['
    if anchor not in shell:
        raise SystemExit('INTENTS anchor not found')
    grant_guard = '''const INTENTS=[\n /* ATLAS-DISCOVERY-V51 — grant/funding intent precedence repair */\n {id:"grant-funding-v5",route:"research",patterns:["grant research funding opportunities","grant funding opportunities","grant research","grant funding","funding opportunities","grant opportunities","research grant","grant proposal","government grants","find grants","grants"],anchors:["grant","grants","funding"],terms:["opportunity","proposal","government","funding","assistance"]},'''
    shell = shell.replace(anchor, grant_guard, 1)

# Add only authoritative grant-discovery destinations.  These are deliberately
# Needs review / Unknown for Atlas link/access auditing even though their
# official capabilities were validated independently on 2026-09-04.
grant_rows = [
    ['curated-grants-gov','Grants.gov','https://www.grants.gov/','Official U.S. government portal to search federal grant funding opportunities and learn the grant application lifecycle.','Free','Curated Library','Research & Intelligence','Grants & Funding','General Utility','High','Needs review','Unknown','Official federal grant-search capability validated 2026-09-04; Atlas link/access audit pending.'],
    ['curated-sam-assistance','SAM.gov Assistance Listings','https://sam.gov/assistance-listings','Official searchable catalog of federal assistance programs including grants, loans, cooperative agreements, scholarships, insurance, and other assistance.','Free','Curated Library','Research & Intelligence','Grants & Funding','General Utility','High','Needs review','Unknown','Official federal assistance-listing capability validated 2026-09-04; Atlas link/access audit pending.'],
    ['curated-ca-grants','California Grants Portal','https://www.grants.ca.gov/','Official California Grants Portal for finding grants and loans offered by California state agencies, searchable by applicant type, category, and deadline.','Free','Curated Library','Research & Intelligence','Grants & Funding','General Utility','High','Needs review','Unknown','Official California grant-search capability validated 2026-09-04; Atlas link/access audit pending.'],
    ['curated-fema-grants','FEMA Grants','https://www.fema.gov/grants','Official FEMA grants hub for preparedness, hazard mitigation, emergency management, fire, and related federal funding programs.','Free','Curated Library','Research & Intelligence','Grants & Funding','General Utility','High','Needs review','Unknown','Official FEMA grants capability validated 2026-09-04; Atlas link/access audit pending.']
]
existing_urls = {str(r[2]).rstrip('/').lower() for r in records}
existing_names = {str(r[1]).strip().lower() for r in records}
added = []
for row in grant_rows:
    url = row[2].rstrip('/').lower()
    name = row[1].strip().lower()
    if url not in existing_urls and name not in existing_names:
        records.append(row)
        added.append(row[1])
        existing_urls.add(url)
        existing_names.add(name)

new_total = len(records)
if new_total != old_total:
    shell = shell.replace(f'{old_total:,}', f'{new_total:,}')

# Re-encode and split authoritative source chunks deterministically enough for
# the current static build pipeline.
encoded = base64.b64encode(gzip.compress(json.dumps(records, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))).decode('ascii')

def split_n(text, n):
    q, r = divmod(len(text), n)
    out, pos = [], 0
    for i in range(n):
        size = q + (1 if i < r else 0)
        out.append(text[pos:pos + size])
        pos += size
    assert ''.join(out) == text
    return out

for p, chunk in zip(SHELL, split_n(shell, len(SHELL))):
    p.write_text(chunk)
for p, chunk in zip(DATA, split_n(encoded, len(DATA))):
    p.write_text(chunk)

bundle = shell.replace('__DATA_B64__', encoded)
(ROOT / 'atlas-bundle.html').write_text(bundle)
report = json.loads((ROOT / 'atlas-build-report.json').read_text())
report['tool_count'] = new_total
report['bundle_bytes'] = len(bundle.encode('utf-8'))
report['data_b64_bytes'] = len(encoded.encode('ascii'))
report['sha256'] = hashlib.sha256(bundle.encode('utf-8')).hexdigest()
report['discovery_v51'] = {
    'grant_intent_precedence_repair': True,
    'official_grant_destinations': 4,
    'new_records': added,
    'new_records_verification': 'Needs review',
    'new_records_access': 'Unknown',
    'total_tools': new_total,
    'preserves_free_vs_no_login': True
}
(ROOT / 'atlas-build-report.json').write_text(json.dumps(report, indent=2) + '\n')

assert MARK in bundle
assert '__DATA_B64__' not in bundle
assert len(records) == new_total
print(json.dumps(report['discovery_v51'], indent=2))
