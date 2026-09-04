from pathlib import Path
import base64, gzip, hashlib, json

ROOT = Path('.')
SHELL_FILES = [ROOT / f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA_FILES = [ROOT / f'atlas-src/data-{i:03d}.txt' for i in range(9)]
shell = ''.join(p.read_text() for p in SHELL_FILES)
data_b64 = ''.join(p.read_text().strip() for p in DATA_FILES)
records = json.loads(gzip.decompress(base64.b64decode(data_b64)))
assert len(records) == 1834
assert '__DATA_B64__' in shell

marker = 'ATLAS-CRO-A11Y-V21'
if marker not in shell:
    favicon = "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect rx='16' width='64' height='64' fill='%23087f80'/%3E%3Cpath d='M32 10l9 22-9 22-9-22z' fill='white'/%3E%3C/svg%3E\">\n"
    if '<link rel="icon"' not in shell:
        shell = shell.replace('<link rel="canonical"', favicon + '<link rel="canonical"', 1)

    # WCAG AA repairs. The prior brand teal button was ~3.99:1 against white and
    # one muted section subtitle was ~4.21:1 against the page background.
    # These replacements preserve the Atlas palette while clearing 4.5:1 for normal text.
    css = '''
/* ATLAS-CRO-A11Y-V21 — WCAG AA contrast repair */
.btn.blue{background:#087f80;color:#fff}
.sectionhead p{color:#53696b}
.stat span{color:#586b6d}
.note{color:#53696b}
'''
    shell = shell.replace('</style>', css + '\n</style>', 1)

# Re-split source deterministically.
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

report_path = ROOT / 'atlas-build-report.json'
report = json.loads(report_path.read_text()) if report_path.exists() else {}
report['bundle_bytes'] = len(bundle.encode())
report['data_b64_bytes'] = len(data_b64.encode())
report['sha256'] = hashlib.sha256(bundle.encode()).hexdigest()
report['visual_theme'] = 'Atlas Brand V2 + CRO V2.1'
report.setdefault('cro_v2', {})['wcag_aa_contrast_repair'] = True
report['cro_v2']['inline_favicon'] = True
report_path.write_text(json.dumps(report, indent=2) + '\n')

assert marker in bundle
assert '.btn.blue{background:#087f80;color:#fff}' in bundle
assert '.sectionhead p{color:#53696b}' in bundle
assert '<link rel="icon" href="data:image/svg+xml' in bundle
print(json.dumps({'bundle_bytes': report['bundle_bytes'], 'sha256': report['sha256'], 'a11y_v21': True}, indent=2))
