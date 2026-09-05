
async function openGuide(page){const g=page.locator('#atlasGuide');if(await g.count()&&!(await g.evaluate(e=>e.open)))await g.locator(':scope > summary').click();}
async function openFilters(page){const f=page.locator('#libraryFilters');if(await f.count()&&!(await f.evaluate(e=>e.open)))await f.locator('summary').click();}
async function navView(page,view){const b=page.locator(`.navlinks button[data-view="${view}"]`);if(await b.isVisible())await b.click();else{await page.locator('#menuBtn').click();await page.locator(`#mobileNav button[data-view="${view}"]`).click();}}
const { chromium } = require('playwright-core');
const fs=require('fs');
const URL=process.env.ATLAS_URL||'https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/';
const EXPECTED_TOTAL=1850;
const checks=[
 {q:'free movie',expect:['tubi','pluto tv','plex','roku']},
 {q:'free live tv and news',expect:['pluto tv','roku','plex','tubi']},
 {q:'free documentary',expect:['nasa+','pbs','tubi','hoopla','kanopy']},
 {q:'live animal nature cams',expect:['explore.org']},
 {q:'NASA space documentary live mission',expect:['nasa+']},
 {q:'movies with my library card',expect:['hoopla','kanopy']},
 {q:'free tv shows',expect:['tubi','pluto tv','plex','roku']},
 {q:'show me something interesting to watch for free',expect:['tubi','pluto tv','plex','roku','nasa+','pbs','explore.org']}
];
function assert(x,m){if(!x)throw new Error(m)}
function num(t=''){const m=t.match(/[\d,]+/);return m?Number(m[0].replace(/,/g,'')):0}
(async()=>{
 const report={url:URL,tests:[],queries:[],errors:[]};
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox']});
 try{
  const ctx=await browser.newContext({viewport:{width:1440,height:1050}});
  const p=await ctx.newPage();p.on('pageerror',e=>report.errors.push(String(e)));
  await p.goto(URL,{waitUntil:'networkidle',timeout:60000});
  await p.waitForFunction(n=>Number((document.querySelector('#statIndexed')?.textContent||'').replace(/,/g,''))===n,EXPECTED_TOTAL,{timeout:30000});
  report.tests.push({name:'Atlas initializes at multimedia count',ok:true,detail:await p.locator('#statIndexed').innerText()});
  assert(await p.locator('.navlinks button[data-view="watch"]').count()===1,'Desktop Watch nav missing');
  await navView(p,"watch");
  assert(await p.locator('#view-watch').evaluate(e=>e.classList.contains('active')),'Watch view did not activate');
  report.tests.push({name:'Watch navigation opens dedicated view',ok:true});
  const services=p.locator('#view-watch [data-watch-link]');
  const count=await services.count();assert(count===9,`Expected 9 watch services, got ${count}`);
  const bad=[];for(let i=0;i<count;i++){const a=services.nth(i),href=await a.getAttribute('href'),target=await a.getAttribute('target');if(!/^https:\/\//.test(href||'')||target!=='_blank')bad.push({i,href,target})}
  assert(!bad.length,'Bad watch links: '+JSON.stringify(bad));report.tests.push({name:'Nine official service launch cards have safe external links',ok:true,detail:String(count)});
  const watchText=(await p.locator('#view-watch').innerText()).toLowerCase();assert(watchText.includes('free does not always mean no account'),'Access distinction missing');assert(watchText.includes('availability'),'Availability caveat missing');report.tests.push({name:'Free/login/availability caveats are visible',ok:true});
  await p.screenshot({path:'watch-qa/atlas-watch-desktop.png',fullPage:true});

  for(const c of checks){
    await navView(p,"home");await openGuide(p);await p.locator('#commandInput').fill(c.q);await p.locator('#routeBtn').click();await p.waitForTimeout(60);
    const best=p.locator('#routeSuggestions button[data-smart-query]').first();assert(await best.count()===1,`No best-match route for ${c.q}`);await best.click();await p.waitForTimeout(90);
    const n=num(await p.locator('#resultCount').innerText());assert(n>0,`Zero results for ${c.q}`);
    const cards=p.locator('#toolGrid .tool');const top=[];const lim=Math.min(5,await cards.count());for(let i=0;i<lim;i++)top.push((await cards.nth(i).locator('h3').innerText()).trim());
    const blob=top.join(' | ').toLowerCase();const hits=c.expect.filter(x=>blob.includes(x));const ok=hits.length>0;report.queries.push({q:c.q,count:n,top,hits,ok});console.log(`${ok?'PASS':'FAIL'} WATCH | ${c.q} | top=${top.join(' / ')} | hit=${hits.join(',')||'NONE'}`);assert(ok,`Irrelevant watch ranking for ${c.q}: ${top.join(' / ')}`);
  }
  report.tests.push({name:'Eight watch-intent ranking checks',ok:true,detail:'8/8'});
  await ctx.close();

  const mctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:2});const m=await mctx.newPage();m.on('pageerror',e=>report.errors.push('MOBILE '+String(e)));await m.goto(URL,{waitUntil:'networkidle',timeout:60000});await m.waitForFunction(n=>Number((document.querySelector('#statIndexed')?.textContent||'').replace(/,/g,''))===n,EXPECTED_TOTAL,{timeout:30000});await m.locator('#menuBtn').click();await m.locator('#mobileNav button[data-view="watch"]').click();assert(await m.locator('#view-watch').evaluate(e=>e.classList.contains('active')),'Mobile Watch view did not activate');const dims=await m.evaluate(()=>({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth}));assert(dims.sw<=dims.cw+1,`Mobile overflow ${JSON.stringify(dims)}`);assert(await m.locator('#view-watch [data-watch-link]').count()===9,'Mobile service cards missing');await m.screenshot({path:'watch-qa/atlas-watch-mobile.png',fullPage:true});report.tests.push({name:'Mobile Watch view',ok:true,detail:`${dims.sw}px/${dims.cw}px`});await mctx.close();

  assert(report.errors.length===0,'JS errors: '+report.errors.join(' | '));report.tests.push({name:'No production JavaScript errors',ok:true,detail:'0'});
  fs.mkdirSync('watch-qa',{recursive:true});fs.writeFileSync('watch-qa/atlas-watch-report.json',JSON.stringify(report,null,2));console.log(`WATCH_QA_SUMMARY tests=${report.tests.length} queries=${report.queries.length} queryPass=${report.queries.filter(x=>x.ok).length} jsErrors=${report.errors.length}`);
 }catch(e){fs.mkdirSync('watch-qa',{recursive:true});report.failure=String(e?.stack||e);fs.writeFileSync('watch-qa/atlas-watch-report.json',JSON.stringify(report,null,2));console.error(e);process.exitCode=2}finally{await browser.close()}
})();