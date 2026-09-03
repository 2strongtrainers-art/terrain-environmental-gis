const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ATLAS_URL = process.env.ATLAS_URL || 'https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/';
const OUT_DIR = path.join(process.cwd(), 'atlas-link-audit');
fs.mkdirSync(OUT_DIR, { recursive: true });

function cleanUrl(raw) {
  try {
    const u = new URL(raw);
    if (!/^https?:$/.test(u.protocol)) return null;
    u.hash = '';
    return u.toString();
  } catch { return null; }
}

async function collectAtlasRecords(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const response = await page.goto(ATLAS_URL, { waitUntil: 'networkidle', timeout: 60000 });
  if (!response || response.status() !== 200) throw new Error(`Atlas page HTTP ${response ? response.status() : 'no response'}`);
  await page.waitForFunction(() => document.querySelector('#statIndexed')?.textContent?.includes('1,834'), null, { timeout: 30000 });
  await page.locator('.navlinks button[data-view="library"]').click();
  await page.locator('#clearFilters').click();
  await page.waitForTimeout(120);

  const records = new Map();
  let lastPage = 0;
  while (true) {
    await page.waitForSelector('#toolGrid .tool');
    const pageItems = await page.locator('#toolGrid .tool').evaluateAll(cards => cards.map(card => {
      const link = [...card.querySelectorAll('a[href]')].find(a => /visit/i.test(a.textContent || ''));
      return {
        name: (card.querySelector('h3')?.textContent || '').trim(),
        url: link?.href || ''
      };
    }));

    for (const item of pageItems) {
      const url = cleanUrl(item.url);
      if (url && !records.has(url)) records.set(url, { name: item.name || new URL(url).hostname, url });
    }

    const paginationText = await page.locator('#pagination').innerText();
    const match = paginationText.match(/Page\s+(\d+)\s+of\s+(\d+)/i);
    const current = match ? Number(match[1]) : lastPage + 1;
    const totalPages = match ? Number(match[2]) : null;
    console.log(`Collected Atlas page ${current}${totalPages ? `/${totalPages}` : ''}; unique URLs=${records.size}`);
    if (current <= lastPage) throw new Error(`Pagination did not advance (still page ${current})`);
    lastPage = current;

    const next = page.locator('#pagination button:has-text("Next")');
    if (!(await next.count()) || !(await next.isEnabled())) break;
    await next.click();
    await page.waitForFunction(prev => {
      const text = document.querySelector('#pagination')?.textContent || '';
      const m = text.match(/Page\s+(\d+)\s+of\s+(\d+)/i);
      return m && Number(m[1]) > prev;
    }, current, { timeout: 5000 });
  }

  await context.close();
  const out = [...records.values()];
  if (out.length !== 1834) throw new Error(`Expected exactly 1,834 Atlas URLs, collected ${out.length}`);
  return out;
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
  const browser = await chromium.launch({ headless: true });
  try {
    const records = await collectAtlasRecords(browser);
    console.log(`Atlas records collected from live UI: ${records.length}`);

    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36 AtlasLinkAudit/1.1',
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
    let completed = 0;
    const concurrency = 16;
    async function worker() {
      while (true) {
        const i = cursor++;
        if (i >= records.length) return;
        results[i] = await auditOne(context, records[i]);
        completed++;
        if (completed % 50 === 0 || completed === records.length) console.log(`Checked ${completed}/${records.length}`);
      }
    }
    await Promise.all(Array.from({ length: concurrency }, () => worker()));
    await context.close();

    const counts = {};
    for (const r of results) counts[r.verdict] = (counts[r.verdict] || 0) + 1;
    const live = counts.live || 0;
    const report = {
      generatedAt: new Date().toISOString(),
      auditMethod: 'Live Atlas UI inventory + Chromium render audit; images/media/fonts blocked; 12s navigation timeout; redirects followed; 16 concurrent pages',
      total: results.length,
      liveVerified: live,
      counts,
      results
    };
    fs.writeFileSync(path.join(OUT_DIR, 'atlas-link-audit.json'), JSON.stringify(report, null, 2));
    fs.writeFileSync(path.join(OUT_DIR, 'summary.json'), JSON.stringify({ generatedAt: report.generatedAt, total: report.total, liveVerified: live, counts }, null, 2));
    fs.writeFileSync(path.join(OUT_DIR, 'needs-review.json'), JSON.stringify(results.filter(r => r.verdict !== 'live'), null, 2));
    console.log('AUDIT_SUMMARY ' + JSON.stringify({ total: report.total, liveVerified: live, counts }));
  } finally {
    await browser.close().catch(() => {});
  }
}

main().catch(err => { console.error(err); process.exit(1); });
