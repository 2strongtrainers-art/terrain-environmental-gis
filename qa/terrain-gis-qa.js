// Isolated synthetic acceptance. Agency responses below are explicit fixtures;
// this verifies the UI/data flow, not current agency availability or a real site.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const BASE = process.env.TERRAIN_URL || 'http://127.0.0.1:8766/';
const OUT = process.env.TERRAIN_QA_OUTPUT || 'terrain-qa';
const CURRENT = 'terrainEnvironmentalGIS.market.v1';
const LEGACY = 'terrainEnvironmentalGIS.v2';
const project = {name:'Synthetic release QA',center:{lat:39.005,lng:-120.745},zoom:12,basemap:'osm',
  geojson:{type:'FeatureCollection',features:[{type:'Feature',
    properties:{name:'Synthetic boundary',description:'Disposable acceptance fixture',custom:'retained'},
    geometry:{type:'Polygon',coordinates:[[[-120.75,39],[-120.74,39],[-120.74,39.01],[-120.75,39.01],[-120.75,39]]]}}]}};
const report={url:BASE,mode:'synthetic_agency_responses',checks:[],pageErrors:[]};
function pass(name){report.checks.push({name,passed:true});console.log('PASS '+name)}
async function fixtures(context){
  await context.route('https://epqs.nationalmap.gov/v1/json?**',route=>route.fulfill({
    contentType:'application/json',body:JSON.stringify({value:500})}));
  await context.route(/^https:\/\/(services\d+\.arcgis\.com|hydro\.nationalmap\.gov)\/.*\/query\?/,route=>route.fulfill({
    contentType:'application/json',body:JSON.stringify({type:'FeatureCollection',features:[]})}));
}
async function boot(page){
  page.on('pageerror',error=>report.pageErrors.push(String(error)));
  page.on('dialog',dialog=>dialog.accept());
  const response=await page.goto(BASE,{waitUntil:'domcontentloaded',timeout:60000});
  assert.equal(response.status(),200);
  await page.waitForFunction(()=>window.L&&window.turf&&document.querySelector('#summary .summary-item'));
  assert.equal(await page.getByText('Market Preview',{exact:true}).count(),1);
}
(async()=>{
  fs.mkdirSync(OUT,{recursive:true});
  const browser=await chromium.launch({headless:true,
    ...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),args:['--no-sandbox']});
  try{
    const context=await browser.newContext({viewport:{width:1440,height:1000},permissions:['clipboard-read','clipboard-write']});
    await fixtures(context);
    await context.addInitScript(({project,key})=>{
      if(!localStorage.getItem(key))localStorage.setItem(key,JSON.stringify(project));
      Object.defineProperty(navigator,'share',{value:undefined,configurable:true});
    },{project,key:LEGACY});
    const page=await context.newPage();await boot(page);
    assert.equal(await page.locator('#projectName').inputValue(),project.name);
    assert.equal(await page.locator('#summary .summary-item b').first().innerText(),'1');
    let snapshot=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),CURRENT);
    assert.deepEqual(snapshot.geojson,project.geojson);
    pass('Previously published local project restores with custom properties intact');

    const point={type:'FeatureCollection',features:[{type:'Feature',properties:{name:'Imported QA point'},
      geometry:{type:'Point',coordinates:[-120.745,39.005]}}]};
    await page.locator('#fileInput').setInputFiles({name:'synthetic-qa.geojson',mimeType:'application/geo+json',buffer:Buffer.from(JSON.stringify(point))});
    await page.waitForFunction(()=>document.querySelector('#summary .summary-item b')?.textContent==='2');
    await page.locator('#analyzeProjectBtn').click();
    await page.waitForFunction(()=>document.querySelector('#analysisState')?.textContent==='Screened');
    assert(await page.locator('#reportBtn').isEnabled());
    snapshot=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),CURRENT);
    assert(snapshot.analysis.areaAcres>0);
    assert.equal(snapshot.geojson.features.length,2);
    await page.reload({waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>document.querySelector('#analysisState')?.textContent==='Screened');
    assert.deepEqual(await page.evaluate(key=>JSON.parse(localStorage.getItem(key)).analysis,CURRENT),snapshot.analysis);
    pass('Import, synthetic screening, autosave and full analysis survive reload');

    const downloadEvent=page.waitForEvent('download');
    await page.locator('[data-export="geojson"]').click();
    const download=await downloadEvent;
    await download.saveAs(OUT+'/synthetic-export.geojson');
    const exported=JSON.parse(fs.readFileSync(OUT+'/synthetic-export.geojson','utf8'));
    assert.equal(exported.features.length,2);
    assert.equal(exported.features[0].properties.custom,'retained');
    pass('GeoJSON export retains all features and properties');

    const popupEvent=page.waitForEvent('popup');
    await page.locator('#reportBtn').click();
    const popup=await popupEvent;await popup.waitForLoadState('domcontentloaded');
    assert(await popup.locator('svg[aria-label="Project boundary schematic"]').isVisible());
    assert((await popup.locator('body').innerText()).includes('Data provenance'));
    await popup.close();
    await page.locator('#shareBtn').click();
    const shared=await page.evaluate(()=>navigator.clipboard.readText());
    assert(shared.includes('viewer.html#p='));
    const viewer=await context.newPage();
    viewer.on('pageerror',error=>report.pageErrors.push(String(error)));
    await viewer.goto(shared,{waitUntil:'domcontentloaded'});
    await viewer.waitForFunction(()=>document.querySelector('#name')?.textContent==='Synthetic release QA');
    assert((await viewer.locator('#findings').innerText()).includes('Project area'));
    await viewer.close();
    pass('Printable report and compact read-only share viewer load the screening snapshot');

    await page.screenshot({path:OUT+'/gis-desktop.png',fullPage:true});
    await page.locator('#clearBtn').click();await page.reload({waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>document.querySelector('#summary .summary-item b')?.textContent==='0');
    assert.deepEqual(await page.evaluate(key=>JSON.parse(localStorage.getItem(key)),LEGACY),project);
    pass('Clear remains cleared after reload; previous-version backup remains intact');
    await context.close();

    for(const width of [390,820]){
    const mobile=await browser.newContext({viewport:{width,height:844},isMobile:true,hasTouch:true});
    await fixtures(mobile);
    const phone=await mobile.newPage();await boot(phone);
    assert(await phone.locator('#panelToggle').isVisible());
    await phone.locator('#panelToggle').click();assert(await phone.locator('#leftPanel').evaluate(el=>el.classList.contains('open')));
    await phone.locator('#resultsToggle').click();assert(await phone.locator('#rightPanel').evaluate(el=>el.classList.contains('open')));
    assert(!(await phone.locator('#leftPanel').evaluate(el=>el.classList.contains('open'))));
    const overflow=await phone.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
    assert(overflow<=1,`Mobile horizontal overflow ${overflow}px`);
    await phone.screenshot({path:OUT+`/gis-mobile-${width}.png`,fullPage:true});
    pass(`Mobile project/findings panels and layout work at ${width}px`);
    await mobile.close();
    }
    assert.deepEqual(report.pageErrors,[]);pass('No application JavaScript errors');
  }catch(error){report.failure=String(error.stack||error);process.exitCode=1;console.error(error)}
  finally{fs.writeFileSync(OUT+'/gis-report.json',JSON.stringify(report,null,2));await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
