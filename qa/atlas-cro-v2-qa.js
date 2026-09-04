const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
const fs = require('fs');
const URL = process.env.ATLAS_URL || 'https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/';
const CHROME = process.env.CHROME_PATH || '/usr/bin/google-chrome';
const report = {url:URL,started_at:new Date().toISOString(),checks:[],posthog_requests:[],page_errors:[],console_errors:[]};
function ok(name, condition, detail=''){if(!condition)throw new Error(`${name}: ${detail||'failed'}`);report.checks.push({name,detail});console.log(`PASS | ${name}${detail?' | '+detail:''}`)}
async function countFrom(page, sel){const t=await page.locator(sel).innerText();return Number((t.match(/[\d,]+/)||['0'])[0].replace(/,/g,''));}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:CHROME,args:['--no-sandbox']});
 try{
  const context=await browser.newContext({viewport:{width:390,height:844}});
  await context.addInitScript(()=>localStorage.clear());
  const page=await context.newPage();
  page.on('pageerror',e=>report.page_errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')report.console_errors.push(m.text())});
  page.on('request',r=>{if(r.url().includes('posthog.com'))report.posthog_requests.push({method:r.method(),url:r.url(),body:(r.postData()||'').slice(0,5000)})});
  let r=await page.goto(URL,{waitUntil:'networkidle',timeout:60000});
  ok('HTTP 200',r&&r.status()===200,String(r&&r.status()));
  ok('specific hero',(await page.locator('#view-home h1').innerText())==='Find the right tool or useful website for what you want to do.');
  ok('specific primary CTA',(await page.locator('#heroBrowse').innerText())==='Browse all 1,834 tools');
  ok('unsupported best claim removed',await page.getByText('Your map to the best AI tools & resources.').count()===0);
  ok('double question mark removed',await page.getByText('What is the Digital Atlas??').count()===0);
  ok('discovery is above explanation',await page.locator('.discovery-first').evaluate(el=>el.getBoundingClientRect().top) < await page.getByText('What is the Digital Atlas?').evaluate(el=>el.getBoundingClientRect().top));
  ok('8 goal buttons are semantic',await page.locator('#goalGrid button[data-goal]').count()===8);
  const firstGoal=page.locator('#goalGrid button[data-goal]').first();await firstGoal.focus();ok('goal keyboard focus',await firstGoal.evaluate(el=>document.activeElement===el));
  ok('partner CTA present',await page.locator('#partnerCta').count()===1);
  ok('share control present',await page.locator('#shareAtlas').count()===1);
  ok('canonical',await page.locator('link[rel="canonical"]').count()===1);
  ok('Open Graph',await page.locator('meta[property="og:title"]').count()===1);
  ok('JSON-LD',await page.locator('script[type="application/ld+json"]').count()===1);
  ok('sitemap link',await page.locator('link[rel="sitemap"]').count()===1);
  ok('analytics privacy control',await page.locator('#analyticsOptOut').count()===1);
  await page.waitForTimeout(2200);
  ok('PostHog initialized',await page.evaluate(()=>!!window.posthog&&typeof window.posthog.capture==='function'));

  // Accessibility basics on the home product surface.
  const axeHome=await new AxeBuilder({page}).analyze();
  const serious=axeHome.violations.filter(v=>['critical','serious'].includes(v.impact));
  ok('no critical/serious axe violations on home',serious.length===0,JSON.stringify(serious.map(v=>v.id)));
  const minTargets=await page.locator('button,a.btn').evaluateAll(els=>els.map(el=>{const r=el.getBoundingClientRect();return {text:(el.innerText||el.getAttribute('aria-label')||'').trim(),h:r.height,w:r.width,visible:r.width>0&&r.height>0}}).filter(x=>x.visible&&x.h<43.5));
  ok('primary interactive heights >=44px',minTargets.length===0,JSON.stringify(minTargets.slice(0,10)));
  const dims=await page.evaluate(()=>({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth}));
  ok('mobile no horizontal overflow',dims.sw<=dims.cw,`${dims.sw}/${dims.cw}`);
  await page.screenshot({path:'cro-v2-qa/mobile-home.png',fullPage:true});

  // Search UX: typo tolerance, synonyms, quick routes, zero recovery.
  await page.locator('#heroBrowse').click();await page.waitForTimeout(150);
  ok('library opens from hero',await page.locator('#view-library').evaluate(el=>el.classList.contains('active')));
  ok('result count live region',(await page.locator('#resultCount').getAttribute('aria-live'))==='polite');
  ok('quick search chips',await page.locator('[data-quick-search]').count()>=6);
  await page.locator('#searchInput').fill('reserch');await page.waitForTimeout(250);
  const typoCount=await countFrom(page,'#resultCount');ok('one-edit typo tolerance',typoCount>0,String(typoCount));
  await page.locator('#searchInput').fill('cv');await page.waitForTimeout(250);
  const aliasCount=await countFrom(page,'#resultCount');ok('search synonym alias',aliasCount>0,String(aliasCount));
  const privateQuery='sensitive-test-string-xyz-48392';
  await page.locator('#searchInput').fill(privateQuery);await page.waitForTimeout(500);
  ok('zero-result recovery UI',(await page.locator('#toolGrid').innerText()).includes('No matches yet.')&&await page.locator('#toolGrid button').count()>=3);
  await page.locator('#toolGrid button:has-text("Browse live-verified")').click();await page.waitForTimeout(120);
  ok('zero-result verified recovery',await countFrom(page,'#resultCount')===1529,await page.locator('#resultCount').innerText());

  // Dead/parked records must not offer outbound actions.
  await page.locator('#verificationFilter').selectOption('Dead / unavailable');await page.waitForTimeout(150);
  const deadCount=await countFrom(page,'#resultCount');ok('dead records exist for guard test',deadCount===32,String(deadCount));
  ok('dead cards have no Visit links',await page.locator('#toolGrid .tool a:has-text("Visit")').count()===0);
  ok('dead cards show unavailable state',await page.locator('#toolGrid .tool:has-text("Unavailable")').count()>0);
  await page.locator('#toolGrid .tool button:has-text("Details")').first().click();
  ok('dead detail has no Open website CTA',await page.locator('#detailModal a:has-text("Open website")').count()===0);
  await page.locator('#modalClose').click();

  // Outbound analytics: use a live destination and assert no raw search text leaks into PostHog request payloads.
  await page.locator('#clearFilters').click();await page.locator('#searchInput').fill('Genspark');await page.waitForTimeout(220);
  const liveLink=page.locator('#toolGrid a[data-tool-visit]').first();ok('tracked outbound link exists',await liveLink.count()===1);
  const href=await liveLink.getAttribute('href');ok('outbound link is absolute',/^https?:\/\//.test(href||''),href||'');
  await page.evaluate(()=>trackAtlas('atlas_qa_event',{purpose:'deployment_verification'}));await page.waitForTimeout(1500);
  ok('PostHog network traffic observed',report.posthog_requests.length>0,String(report.posthog_requests.length));
  ok('raw search text not sent to PostHog',!report.posthog_requests.some(x=>(x.body||'').includes(privateQuery)));

  // Analytics opt-out works locally.
  await page.locator('.navlinks button[data-view="quality"]').evaluate(el=>el.click());await page.waitForTimeout(100);
  await page.locator('#analyticsOptOut').click();
  ok('analytics opt-out persisted',await page.evaluate(()=>localStorage.getItem('atlasAnalyticsOptOut')==='1'));
  ok('analytics opt-out status visible',(await page.locator('#analyticsStatus').innerText()).includes('disabled'));

  // Crawlable commercial and acquisition pages are truly deployed.
  for(const path of ['collections/ai-tools/','collections/design-tools/','collections/education-tools/','collections/gaming-tools/','collections/live-verified-tools/','collections/free-no-login/','partners/']){
    const p=await context.newPage();const rr=await p.goto(URL+path,{waitUntil:'domcontentloaded',timeout:30000});ok(`static page ${path}`,rr&&rr.status()===200&&await p.locator('h1').count()===1,String(rr&&rr.status()));await p.close();
  }
  const sitemap=await context.request.get(URL+'sitemap.xml');ok('Atlas sitemap deployed',sitemap.status()===200&&(await sitemap.text()).includes('<urlset'),String(sitemap.status()));

  ok('no page errors',report.page_errors.length===0,JSON.stringify(report.page_errors));
  // Console errors from third-party destinations are irrelevant; only current Atlas page is inspected here.
  fs.writeFileSync('cro-v2-qa/report.json',JSON.stringify(report,null,2));
  console.log('CRO_V2_QA_COMPLETE '+JSON.stringify({checks:report.checks.length,posthog_requests:report.posthog_requests.length}));
 } finally { await browser.close(); }
})().catch(e=>{report.failure=String(e&&e.stack||e);try{fs.mkdirSync('cro-v2-qa',{recursive:true});fs.writeFileSync('cro-v2-qa/report.json',JSON.stringify(report,null,2));}catch{}console.error(e);process.exit(1)});
