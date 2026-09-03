const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const { chromium } = require('playwright');

const DATA_DIR = path.join(process.cwd(), 'atlas-src');
const OUT_DIR = path.join(process.cwd(), 'atlas-link-audit');
fs.mkdirSync(OUT_DIR, { recursive: true });

function loadAtlasData() {
  const files = fs.readdirSync(DATA_DIR)
    .filter(n => /^data-\d{3}\.txt$/.test(n))
    .sort();
  if (!files.length) throw new Error('No Atlas data chunks found');
  const b64 = files.map(n => fs.readFileSync(path.join(DATA_DIR, n), 'utf8').trim()).join('');
  const json = zlib.gunzipSync(Buffer.from(b64, 'base64')).toString('utf8');
  return JSON.parse(json);
}

function urlFromRecord(r) {
  if (!r || typeof r !== 'object') return null;
  for (const key of ['url', 'URL', 'href', 'link', 'website', 'Website URL', 'websiteUrl']) {
    if (typeof r[key] === 'string' && /^https?:\/\//i.test(r[key].trim())) return r[key].trim();
  }
  return null;
}

function nameFromRecord(r, url) {
  for (const key of ['name', 'Name', 'Website Name', 'title', 'Title', 'tool']) {
    if (typeof r?.[key] === 'string' && r[key].trim()) return r[key].trim();
  }
  try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return url; }
}

function findRecordArray(root) {
  const seen = new Set();
  const candidates = [];
  function walk(v, depth = 0) {
    if (!v || typeof v !== 'object' || seen.has(v) || depth > 8) return;
    seen.add(v);
    if (Array.isArray(v)) {
      const sample = v.slice(0, 25);
      const withUrls = sample.filter(x => urlFromRecord(x)).length;
      if (v.length >= 100 && withUrls > 0) candidates.push({ v, score: v.length * 100 + withUrls });
      for (const x of sample) walk(x, depth + 1);
    } else {
      for (const x of Object.values(v)) walk(x, depth + 1);
    }
  }
  walk(root);
  candidates.sort((a, b) => b.score - a.score);
  if (!candidates.length) throw new Error('Could not locate Atlas record array');
  return candidates[0].v;
}

function normalizeRecords(root) {
  const arr = findRecordArray(root);
  const map = new Map();
  for (const r of arr) {
    const url = urlFromRecord(r);
    if (!url) continue;
    let key;
    try {
      const u = new URL(url);
      u.hash = '';
      key = u.toString();
    } catch { continue; }
    if (!map.has(key)) map.set(key, { name: nameFromRecord(r, url), url: key });
  }
  return [...map.values()];
}

const PARKED_PATTERNS = [
  /domain (?:name )?(?:is )?for sale/i,
  /buy this domain/i,
  /this domain may be for sale/i,
  /sedo domain parking/i,
  /afternic/i,
  /hugedomains/i,
  /parked free/i,
  /domain parking/i
];
const NOT_FOUND_PATTERNS = [
  /^404\b/i,
  /404\s*[-–—:]?\s*(?:page )?not found/i,
  /the page you (?:are looking for|requested) (?:does not exist|could not be found)/i
];

async function auditOne(context, item) {
  const page = await context.newPage();
  const started = Date.now();
  let response = null;
  let title = '';
  let finalUrl = item.url;
  let body = '';
  let verdict = 'error';
  let detail = '';
  let status = null;
  try {
    response = await page.goto(item.url, { waitUntil: 'domcontentloaded', timeout: 12000 });
    finalUrl = page.url() || item.url;
    status = response?.status() ?? null;
    title = (await page.title().catch(() => '')).trim().slice(0, 180);
    body = (await page.locator('body').innerText({ timeout: 2500 }).catch(() => '')).replace(/\s+/g, ' ').trim().slice(0, 1500);
    const text = `${title} ${body}`;
    if (PARKED_PATTERNS.some(rx => rx.test(text))) {
      verdict = 'parked'; detail = 'Domain-sale/parking language detected';
    } else if ((status === 404 || status === 410) || NOT_FOUND_PATTERNS.some(rx => rx.test(text))) {
      verdict = 'dead'; detail = `Not-found response${status ? ` (${status})` : ''}`;
    } else if (status != null && status >= 200 && status < 400 && (title || body.length > 40)) {
      verdict = 'live'; detail = `Rendered successfully (${status})`;
    } else if ([401, 403, 429].includes(status)) {
      verdict = 'blocked'; detail = `Reached site but verification blocked (${status})`;
    } else if (status != null && status >= 500) {
      verdict = 'server_error'; detail = `Server returned ${status}`;
    } else if (status != null && status >= 400) {
      verdict = 'dead'; detail = `HTTP ${status}`;
    } else if (title || body.length > 40) {
      verdict = 'live'; detail = 'Rendered content without a usable HTTP status';
    } else {
      verdict = 'uncertain'; detail = status ? `HTTP ${status}, insufficient rendered content` : 'No usable response/content';
    }
  } catch (e) {
    const msg = String(e?.message || e).replace(/\s+/g, ' ').slice(0, 240);
    if (/timeout/i.test(msg)) { verdict = 'timeout'; detail = msg; }
    else { verdict = 'error'; detail = msg; }
    try {
      finalUrl = page.url() || item.url;
      title = (await page.title().catch(() => '')).trim().slice(0, 180);
      body = (await page.locator('body').innerText({ timeout: 1000 }).catch(() => '')).replace(/\s+/g, ' ').trim().slice(0, 500);
      if ((title || body.length > 40) && !/^chrome-error:\/\//.test(finalUrl)) {
        verdict = 'live'; detail = 'Page rendered content despite navigation exception';
      }
    } catch {}
  } finally {
    await page.close().catch(() => {});
  }
  return {
    name: item.name,
    url: item.url,
    finalUrl,
    status,
    verdict,
    detail,
    title,
    checkedAt: new Date().toISOString(),
    ms: Date.now() - started
  };
}

async function main() {
  const root = loadAtlasData();
  const records = normalizeRecords(root);
  console.log(`Atlas records located: ${records.length}`);
  if (records.length < 1700) throw new Error(`Expected ~1,834 URLs, found only ${records.length}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36 AtlasLinkAudit/1.0',
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 800 }
  });
  await context.route('**/*', route => {
    const t = route.request().resourceType();
    if (['image', 'media', 'font'].includes(t)) return route.abort();
    return route.continue();
  });

  const results = new Array(records.length);
  let cursor = 0;
  const concurrency = 10;
  async function worker(id) {
    while (true) {
      const i = cursor++;
      if (i >= records.length) return;
      results[i] = await auditOne(context, records[i]);
      if ((i + 1) % 50 === 0 || i + 1 === records.length) console.log(`Checked ${i + 1}/${records.length}`);
    }
  }
  await Promise.all(Array.from({ length: concurrency }, (_, i) => worker(i)));
  await browser.close();

  const counts = {};
  for (const r of results) counts[r.verdict] = (counts[r.verdict] || 0) + 1;
  const live = counts.live || 0;
  const report = {
    generatedAt: new Date().toISOString(),
    auditMethod: 'Chromium render audit; images/media/fonts blocked for speed; 12s navigation timeout; redirects followed',
    total: results.length,
    liveVerified: live,
    counts,
    results
  };
  fs.writeFileSync(path.join(OUT_DIR, 'atlas-link-audit.json'), JSON.stringify(report, null, 2));
  fs.writeFileSync(path.join(OUT_DIR, 'summary.json'), JSON.stringify({ generatedAt: report.generatedAt, total: report.total, liveVerified: live, counts }, null, 2));
  fs.writeFileSync(path.join(OUT_DIR, 'needs-review.json'), JSON.stringify(results.filter(r => r.verdict !== 'live'), null, 2));

  console.log('AUDIT_SUMMARY ' + JSON.stringify({ total: report.total, liveVerified: live, counts }));
}

main().catch(err => { console.error(err); process.exit(1); });
