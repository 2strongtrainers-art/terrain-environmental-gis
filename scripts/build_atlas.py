"""Build Atlas deterministically from its existing sources, without rewriting them.

The isolated legacy transforms preserve the current production data and search
taxonomy. V6 is applied once to their assembled output. Only dist is published.
"""
from pathlib import Path
import argparse
import base64
import collections
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STEPS = ['apply_atlas_intent_v32.py', 'apply_atlas_multimedia_v4.py',
         'apply_atlas_multimedia_v41.py', 'apply_atlas_discovery_v5_search.py',
         'apply_atlas_discovery_v51.py']


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Expected one build anchor ({text.count(old)} found): {old[:90]}')
    return text.replace(old, new, 1)


def build(out):
    with tempfile.TemporaryDirectory(prefix='atlas-build-') as temp:
        stage = Path(temp)
        shutil.copytree(ROOT / 'atlas-src', stage / 'atlas-src')
        shutil.copytree(ROOT / 'qa', stage / 'qa')
        shutil.copy(ROOT / 'atlas-build-report.json', stage)
        for step in STEPS:
            subprocess.run([sys.executable, str(ROOT / 'scripts' / step)], cwd=stage,
                           check=True, stdout=subprocess.DEVNULL)
        html = (stage / 'atlas-bundle.html').read_text()
        report = json.loads((stage / 'atlas-build-report.json').read_text())

    encoded = re.search(r'const DATA_B64="([^"]+)"', html)[1]
    rows = json.loads(gzip.decompress(base64.b64decode(encoded)))
    assert len({str(r[0]) for r in rows}) == len(rows), 'Duplicate tool IDs'
    assert all(len(r) == 13 and r[2].startswith(('https://', 'http://')) for r in rows)
    packed = base64.b64encode(gzip.compress(json.dumps(rows, ensure_ascii=False,
                 separators=(',', ':')).encode(), mtime=0)).decode()
    html = html.replace(encoded, packed, 1)
    counts = collections.Counter(r[10] for r in rows)
    topics = len({r[6] or 'General tools' for r in rows})

    # Safe local preferences: blocked storage or malformed favorites cannot stop boot.
    storage = '''<script>window.atlasStorage={getItem(k){try{return localStorage.getItem(k)}catch{return null}},setItem(k,v){try{localStorage.setItem(k,v)}catch{}},removeItem(k){try{localStorage.removeItem(k)}catch{}}};</script>'''
    html = re.sub(r'localStorage\.(getItem|setItem|removeItem)', r'window.atlasStorage.\1', html)
    html = html.replace('<script id="atlasAnalytics">', storage+'\n<script id="atlasAnalytics">', 1)
    html = replace_once(html, 'let favorites=new Set(JSON.parse(window.atlasStorage.getItem("atlasFavorites")||"[]"));',
        'let favorites=new Set();try{const saved=JSON.parse(window.atlasStorage.getItem("atlasFavorites")||"[]");if(Array.isArray(saved))favorites=new Set(saved.filter(id=>TOOLS.some(t=>t.id===id)))}catch{}')

    # Quote IDs at the HTML/JavaScript boundary; new curated IDs are strings.
    for old, new in [('openDetail(${t.id})','openDetail(${esc(JSON.stringify(t.id))})'),
                     ('toggleFav(${t.id},this)','toggleFav(${esc(JSON.stringify(t.id))},this)'),
                     ('toggleModalFav(${t.id},this)','toggleModalFav(${esc(JSON.stringify(t.id))},this)')]:
        html = html.replace(old, new)
    html = html.replace('tool_id:Number(a.dataset.toolId)', 'tool_id:a.dataset.toolId')
    # Do not give an unrelated tool a search match solely for being verified.
    html = replace_once(html, 'if(t.verification==="Live verified")s+=5;if(t.priority==="High")s+=2;',
                             'if(s<=0)return 0;\n if(t.verification==="Live verified")s+=5;if(t.priority==="High")s+=2;')
    html = replace_once(html, 'state.query=q;state.source="";', 'state.query=q;state.topic="";state.source="";')
    # Replace old core functions with their V6 implementations, not competing handlers.
    for name, after in [('showView','$("[data-view]")'), ('syncStateFromControls','let searchTimer;'),
                        ('getFiltered','function toolCard'), ('renderCategories','function renderFree')]:
        start = html.index('function '+name+'(')
        if name == 'showView':
            end = html.index('$$("[data-view]")', start)
        else:
            end = html.index(after, start)
        html = html[:start]+html[end:]
    html = replace_once(html, 'function closeModal(){$("#detailModal").classList.remove("open")}', '')
    html = replace_once(html, '\n}\nwindow.goPage=p=>', '\n v6AfterRender(total);\n}\nwindow.goPage=p=>')
    html = re.sub(r'const initial=location.hash.replace\("#",""\);[^\n]+',
                  lambda _: (ROOT/'atlas-src/atlas-v6.js').read_text(), html, count=1)
    html = re.sub(r'\$\("#qReview"\)\.textContent=fmt\([^;]+\);',
        f'$("#qReview").textContent=fmt({len(rows)-sum(counts[k] for k in ["Live verified","Automation blocked","Dead / unavailable","Parked / for sale"])});', html, count=1)
    html = html.replace('<div class="modal" id="detailModal"', '<div class="modal" id="detailModal" role="dialog" aria-modal="true" aria-labelledby="detailTitle"') if 'id="detailModal" role=' not in html else html

    # A compact home: immediate search, six existing beginner routes, topic index,
    # and the complete original guide available in one expandable section.
    html = replace_once(html, '<h1>Find the right tool or useful website for what you want to do.</h1>', '<h1>Find your next useful tool.</h1>')
    home_p = f'<p>Browse {len(rows):,} resources by goal, category, price or verification status. {counts["Live verified"]:,} destinations were live-checked on September 3, 2026.</p>'
    home_search = '''<p>Search by name, describe a task, or explore a topic. Find something useful in a few taps.</p>
 <form class="hero-search" id="heroSearchForm" role="search"><label for="homeSearch">What would you like to do?</label><div class="hero-search-row"><input id="homeSearch" type="search" placeholder="Try video, maps, Python…" aria-label="Search Atlas" autocomplete="off" maxlength="500"><button class="btn blue" type="submit">Search</button></div></form>'''
    html = replace_once(html, home_p, home_search)
    home_start = html.index('id="view-home"')
    stats = html.index(' <div class="stats">', home_start)
    home_end = html.index('</section>', stats)
    intro = f'''<section class="home-index" aria-label="Browse the indexes"><div><h2>A topic for every kind of curious.</h2><p>{topics} topic groups · {len(rows):,} indexed resources · no Atlas account needed.</p></div><div class="actions"><button class="btn blue" id="homeTopics">Explore topics</button><button class="btn outline" id="savedTools">★ My saved tools</button></div></section>
 <details id="atlasGuide"><summary>About Atlas &amp; more ways to find tools</summary>'''
    html = html[:stats]+intro+html[stats:home_end]+'</details>\n'+html[home_end:]

    # Secondary filters stay available without occupying most of a phone screen.
    begin = html.index('  <div class="searchrow">')
    end = html.index('  <div class="quicksearch"', begin)
    old_row = html[begin:end]
    selects = re.findall(r'<select[^>]+id="([^"]+)"[^>]*>.*?</select>', old_row, re.S)
    labels = {'sourceFilter':'Collection','pricingFilter':'Pricing','verificationFilter':'Verification','priorityFilter':'Priority','sortFilter':'Sort'}
    controls = []
    for id in selects:
        select = re.search(r'<select[^>]+id="'+id+r'"[^>]*>.*?</select>', old_row, re.S)[0]
        controls.append(f'<label for="{id}">{labels[id]}{select}</label>')
    controls.insert(1, '<label for="topicFilter">Topic<select class="control" id="topicFilter" aria-label="Topic"><option value="">All topics</option></select></label>')
    new_row = '''  <div class="searchrow"><input type="search" class="control query" id="searchInput" placeholder="Search tools, tasks or websites…" aria-label="Search library" autocomplete="off" maxlength="500" enterkeyhint="search">
 <details class="filter-disclosure" id="libraryFilters"><summary id="filtersSummary">Filters</summary><div class="filter-grid">'''+''.join(controls)+'''</div></details></div>
 <div class="chiprow" id="activeFilters" aria-label="Active filters"></div>
'''
    html = html[:begin]+new_row+html[end:]
    html = html.replace('<button class="chip" id="clearFilters">Clear filters</button>', '<button class="chip" id="clearFilters">Clear filters</button><button class="chip" id="copyResults">Copy search link</button>', 1)
    html = html.replace('<div class="tools" id="toolGrid">', '<p class="sr-only" id="resultStatus" role="status" aria-live="polite"></p><div class="tools" id="toolGrid">', 1)
    html = html.replace('<p>Search naturally by task. Atlas prioritizes exact capability matches, trusted task-specific candidates and modifiers like free/no-login before broad categories.</p>', '<p>Search by name or task. Open Filters to narrow by topic, price, or verification.</p>', 1)

    html = replace_once(html, '<h1>Categories</h1><p>Start broad, then narrow with search and filters.</p>', '<h1>Explore the indexes.</h1><p>Choose a collection, or find a topic below. Counts include every indexed resource.</p>')
    html = replace_once(html, '<div class="categorygrid" id="categoryGrid"></div>', '''<div class="categorygrid" id="categoryGrid"></div>
 <div class="index-search"><h2>Browse by topic</h2><label for="topicIndexSearch" class="sr-only">Find a topic</label><input class="control" id="topicIndexSearch" type="search" placeholder="Find a topic: science, design, Minecraft…"><span id="topicIndexCount" role="status"></span></div><div class="topic-index" id="topicIndexGrid"></div>''')
    html = html.replace('data-view="categories">Categories</button>', 'data-view="categories">Topics</button>')
    html = html.replace('data-view="library">Master Library</button>', 'data-view="library">Library</button>')
    html = html.replace('aria-controls="mobileNav">Menu</button>', 'aria-controls="mobileNav">More</button>')
    html = html.replace('"target":"https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/#library"', '"target":"https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/?q={search_term_string}#library"')
    html = html.replace('</style>', '\n'+(ROOT/'atlas-src/atlas-v6.css').read_text()+'\n</style>', 1)

    # The existing discovery layer delegates to the same router instead of
    # delayed clicks that can inherit stale filters or race a search.
    upgrade = (ROOT/'atlas-upgrade.js').read_text()
    a = upgrade.index('function openPlus('); b = upgrade.index('const BEHAVIOR_POLICY', a)
    upgrade = upgrade[:a]+"function openPlus(id){window.Atlas.navigate(id)}\n"+upgrade[b:]
    a = upgrade.index('function search('); b = upgrade.index('function style()', a)
    upgrade = upgrade[:a]+"function search(q,meta={}){window.Atlas.search(q);capture('atlas_discovery_search',{task_family:meta.task_family||familyFrom(q),source:meta.source||'discovery',query_length:q.length})}\n"+upgrade[b:]
    upgrade = upgrade.replace("const hash=location.hash.slice(1);if(['do','learn','stacks','playbooks','explore'].includes(hash))openPlus(hash);", 'window.Atlas.restoreRoute();')
    upgrade = upgrade.replace("if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',inject,{once:true});else inject();", "if(window.Atlas)inject();else document.addEventListener('atlas:ready',inject,{once:true});")
    # Infrastructure diagnostics belong in Data Quality rather than a workflow.
    upgrade = upgrade.replace('${evidence}<div class="atlas-plus-grid two">', '<div class="atlas-plus-grid two">')
    beginner = (ROOT/'atlas-mobile-beginner.js').read_text()
    a = beginner.index('function quickSearch('); b = beginner.index('function mount()', a)
    beginner = beginner[:a]+"function quickSearch(q,label){window.Atlas.search(q);capture('atlas_beginner_choice',{choice:label,query:q})}\n"+beginner[b:]
    beginner = beginner.replace("if(b.dataset.q)return quickSearch(b.dataset.q,b.textContent.trim());", "if(b.dataset.q){e.stopPropagation();return quickSearch(b.dataset.q,b.textContent.trim())}")
    beginner = beginner.replace("styles();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(mount,120));else setTimeout(mount,120);", "styles();if(window.Atlas)mount();else document.addEventListener('atlas:ready',mount,{once:true});")
    for name, content in [('atlas-upgrade.js', upgrade), ('atlas-mobile-beginner.js', beginner)]:
        content = re.sub(r'localStorage\.(getItem|setItem|removeItem)', r'window.atlasStorage.\1', content)
        digest = hashlib.sha256(content.encode()).hexdigest()[:12]
        out.mkdir(parents=True, exist_ok=True)
        (out/name).write_text(content)
        html = html.replace('</body>', f'<script src="../{name}?v={digest}" defer></script>\n</body>', 1)
    (out/'atlas').mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT/'atlas-static', out/'atlas', dirs_exist_ok=True)
    (out/'atlas/index.html').write_text(html)
    report.update(tool_count=len(rows),live_verified=counts['Live verified'],bundle_bytes=len(html.encode()),
                  sha256=hashlib.sha256(html.encode()).hexdigest(),release='atlas-v6',topic_count=topics,
                  data_sha256=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),
                  navigation_v6={'shareable_search':True,'topic_index':True,'cached_scoring':True,'string_ids':True,'safe_favorites':True})
    (out/'atlas/build-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['release','tool_count','topic_count','bundle_bytes','sha256']}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=ROOT/'dist')
    build(parser.parse_args().out.resolve())
