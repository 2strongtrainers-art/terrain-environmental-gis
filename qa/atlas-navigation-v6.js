const {chromium}=require('playwright');
const fs=require('fs');
const assert=require('node:assert/strict');
const URL=process.env.ATLAS_URL||'http://127.0.0.1:8765/atlas/';
const output=process.env.QA_OUTPUT||'navigation-qa';
fs.mkdirSync(output,{recursive:true});
const report={url:URL,checks:[],errors:[],widths:[]};
const check=(name,detail)=>{report.checks.push({name,passed:true,detail});console.log('PASS '+name+(detail?' | '+detail:''))};
async function nav(p,view){const b=p.locator(`.navlinks [data-view="${view}"],.navlinks [data-plus-view="${view}"]`);if(await b.isVisible())await b.click();else{await p.locator('#menuBtn').click();await p.locator(`#mobileNav [data-view="${view}"],#mobileNav [data-plus-view="${view}"]`).click()}}
async function boot(p){await p.goto(URL);await p.waitForFunction(()=>window.Atlas&&document.querySelector('#atlasBeginnerStart'));}
async function search(p,q){await p.locator('#searchInput').fill(q);await p.locator('#searchInput').press('Enter');}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox']});
 try{
  const ctx=await browser.newContext({viewport:{width:1440,height:1000},permissions:['clipboard-read','clipboard-write']});
  const p=await ctx.newPage();p.on('pageerror',e=>report.errors.push(String(e)));
  await boot(p);
  assert(await p.locator('#homeSearch').isVisible());
  assert(!(await p.locator('#atlasGuide').getAttribute('open')));
  await p.locator('#homeSearch').fill('grants');await p.locator('#homeSearch').press('Enter');
  assert.equal(await p.locator('#searchInput').inputValue(),'grants');
  const grants=p.locator('#toolGrid .tool').filter({has:p.getByRole('heading',{name:'Grants.gov',exact:true})});
  assert(await grants.isVisible());
  assert.equal(await p.locator('#toolGrid .tool').count(),4,'Grant searches should show the four matching portals without unrelated padding');
  check('Home search opens four relevant grant results');
  await grants.getByRole('button',{name:'Details',exact:true}).click();
  assert(await p.locator('#detailModal').isVisible());assert.equal(await p.locator('#detailTitle').innerText(),'Grants.gov');
  await p.locator('#modalClose').press('Shift+Tab');
  assert.equal(await p.evaluate(()=>document.activeElement.textContent.trim()),'☆ Add favorite');
  await p.locator('#detailModal button').filter({hasText:'Add favorite'}).click();
  await p.keyboard.press('Escape');assert(!(await p.locator('#detailModal').isVisible()));
  await p.locator('#favOnly').click();assert.equal(await p.locator('#toolGrid .tool').count(),1);
  await p.reload();await p.waitForFunction(()=>window.Atlas);await p.locator('#favOnly').click();assert.equal(await p.locator('#toolGrid .tool').count(),1);
  check('String-ID details, modal keyboard focus, and saved favorites survive reload');
  await p.locator('#clearFilters').click();
  await p.locator('#libraryFilters summary').click();
  await p.locator('#sourceFilter').selectOption('Education & Learning');
  await p.locator('#topicFilter').selectOption('Science');
  const count=await p.locator('#resultCount').innerText();
  await p.locator('#copyResults').click();
  const shared=await p.evaluate(()=>navigator.clipboard.readText());
  assert(shared.includes('topic=Science')&&shared.includes('source=Education'));
  await p.reload();await p.waitForFunction(()=>window.Atlas);
  assert.equal(await p.locator('#topicFilter').inputValue(),'Science');assert.equal(await p.locator('#resultCount').innerText(),count);
  const second=await ctx.newPage();await second.goto(shared);await second.waitForFunction(()=>window.Atlas);
  assert.equal(await second.locator('#resultCount').innerText(),count);await second.close();
  check('Copied search link restores collection, topic, and result count in a fresh tab',count);
  await nav(p,'home');await p.goBack();await p.waitForSelector('#view-library.active');
  assert.equal(await p.locator('#topicFilter').inputValue(),'Science');
  await p.goForward();await p.waitForSelector('#view-home.active');
  check('Browser Back and Forward restore the selected view and filters');
  await nav(p,'categories');
  assert.equal(await p.locator('#topicIndexGrid button').count(),37);
  const topicCounts=await p.locator('#topicIndexGrid button>span').allTextContents();
  assert.equal(topicCounts.reduce((n,t)=>n+Number(t.match(/[\d,]+/)[0].replace(/,/g,'')),0),1850);
  await p.locator('#topicIndexSearch').fill('science');assert.equal(await p.locator('#topicIndexGrid button').count(),2);
  await p.locator('#topicIndexGrid [data-topic="Science"]').click();assert.equal(await p.locator('#topicFilter').inputValue(),'Science');
  assert.equal(await p.locator('#sourceFilter').inputValue(),'');
  check('All 37 topic counts reconcile to all 1,850 records; topic search and launch work');
  await p.locator('#clearFilters').click();await search(p,'zqxvnonexistent987654321');
  assert.equal(await p.locator('#toolGrid .tool').count(),0);
  assert(await p.getByText('No matches yet.',{exact:true}).isVisible());
  await p.locator('#toolGrid').getByRole('button',{name:'Clear filters',exact:true}).click();
  assert.equal(await p.locator('#resultCount').innerText(),'1,850 results');
  check('Unrelated search returns an honest empty state with working recovery');
  // Previously every string ID generated an invalid inline handler. Cover all 16.
  const html=fs.readFileSync('dist/atlas/index.html','utf8');
  const rows=JSON.parse(require('zlib').gunzipSync(Buffer.from(html.match(/const DATA_B64="([^"]+)"/)[1],'base64')));
  for(const row of rows.filter(r=>typeof r[0]==='string')){
   await search(p,row[1]);
   const card=p.locator('#toolGrid .tool').filter({has:p.getByRole('heading',{name:row[1],exact:true})}).first();
   await card.getByRole('button',{name:'Details',exact:true}).click();assert.equal(await p.locator('#detailTitle').innerText(),row[1]);await p.locator('#modalClose').click();
   const before=await card.locator('.fav').innerText();await card.locator('.fav').click();assert.equal(await card.locator('.fav').innerText(),before==='★'?'☆':'★');await card.locator('.fav').click();
  }
  check('All 16 newer resources open details and toggle favorites');
  await nav(p,'home');await p.screenshot({path:output+'/atlas-desktop.png',fullPage:false});
  await ctx.close();
  for(const width of [320,375,390,430]){
   const c=await browser.newContext({viewport:{width,height:844},isMobile:true,hasTouch:true});
   const m=await c.newPage();m.on('pageerror',e=>report.errors.push(`${width}: ${e}`));await boot(m);
   assert.equal(await m.locator('#atlasBeginnerStart button[data-beginner]').count(),6);
   const homeSearch=await m.locator('#homeSearch').boundingBox();assert(homeSearch.y+homeSearch.height<844,'Search must fit the opening screen');
   await m.locator('#homeSearch').fill('video');await m.locator('#homeSearch').press('Enter');
   assert((await m.locator('#toolGrid .tool').count())>0);
   assert(!(await m.locator('#sourceFilter').isVisible()));
   await m.locator('#libraryFilters summary').click();assert(await m.locator('#sourceFilter').isVisible());
   await m.locator('#sourceFilter').selectOption('AI');assert.equal(await m.locator('#sourceFilter').inputValue(),'AI');
   await nav(m,'home');await m.locator('#atlasBeginnerStart [data-q="live nature animal cams"]').click();
   assert.equal(await m.locator('#sourceFilter').inputValue(),'','Quick starts must clear old filters');
   assert((await m.locator('#toolGrid .tool').count())>0);
   for(const view of ['home','library','categories','do','learn','explore','stacks','playbooks','watch','free','archive','quality']){
    await nav(m,view);assert(await m.locator('#view-'+view).isVisible());
    const overflow=await m.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);assert(overflow<=1,`${view} overflows at ${width}: ${overflow}`);
   }
   report.widths.push({width,views:12,overflow:false,searchVisibleOnHome:true});
   if(width===390){await nav(m,'home');await m.screenshot({path:output+'/atlas-mobile.png',fullPage:false});await nav(m,'categories');await m.screenshot({path:output+'/atlas-topics.png',fullPage:false})}
   await c.close();
  }
  check('Search, filters, quick starts, and all 12 views work at 320/375/390/430px');
  const corrupt=await browser.newContext();await corrupt.addInitScript(()=>localStorage.setItem('atlasFavorites','not json'));
  const cp=await corrupt.newPage();cp.on('pageerror',e=>report.errors.push(String(e)));await boot(cp);assert(await cp.locator('#homeSearch').isVisible());await corrupt.close();
  check('Malformed saved favorites do not prevent startup');
  assert.deepEqual(report.errors,[]);check('Zero application JavaScript errors');
 }catch(e){report.failure=String(e.stack||e);process.exitCode=1;console.error(e)}
 finally{fs.writeFileSync(output+'/report.json',JSON.stringify(report,null,2));await browser.close()}
})();
