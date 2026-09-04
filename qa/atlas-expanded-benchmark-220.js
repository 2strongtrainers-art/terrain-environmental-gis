const { chromium } = require('playwright');
const fs = require('fs');
const URL = process.env.ATLAS_URL || 'https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/';

// 22 task families x 10 deliberately varied requests = 220 queries.
// Acceptance terms are task-specific. A generic word such as "tool", "AI", "web", "free",
// "app", "site", "learn", or "business" never earns a relevance pass by itself.
const families = [
 {id:'image', base:'AI image generator', expect:['image generator','ideogram','midjourney','firefly','imagen','stable diffusion','leonardo','flux'], avoid:['stock photo only']},
 {id:'video', base:'short social video editor', expect:['capcut','clipchamp','opus clip','video editor','short video','runway','pika','descript']},
 {id:'voice', base:'AI voice generator text to speech', expect:['elevenlabs','speechify','murf','play.ht','text to speech','voice generator','tts']},
 {id:'website', base:'no code website builder', expect:['wix','framer','webflow','squarespace','carrd','wordpress','website builder','no code']},
 {id:'automation', base:'AI automation workflow agent', expect:['automation','workflow','agent','zapier','make.com','n8n','pipedream']},
 {id:'coding', base:'learn Python coding', expect:['python','freecodecamp','codecademy','kaggle learn','real python','coding','programming']},
 {id:'research', base:'research papers academic evidence', expect:['research','academic','paper','scholar','elicit','consensus','scispace','semantic scholar']},
 {id:'pdf', base:'edit PDF document', expect:['pdf','smallpdf','ilovepdf','acrobat','pdfescape','simplepdf']},
 {id:'ocr', base:'OCR extract text from image', expect:['ocr','image to text','extract text','tesseract','scan text']},
 {id:'design', base:'design logo and brand graphics', expect:['logo','design','canva','looka','brandmark','designevo','graphic']},
 {id:'marketing', base:'marketing sales lead generation', expect:['marketing','sales','lead generation','crm','hubspot','mailchimp','seo']},
 {id:'fitness', base:'fitness coaching workout programming', expect:['fitness','workout','training','trainer','exercise','strength','coach']},
 {id:'grants', base:'grant research funding opportunities', expect:['grant','funding','grants.gov','sam.gov','foundation','proposal']},
 {id:'gis', base:'GIS mapping geospatial data', expect:['gis','geospatial','mapping','arcgis','qgis','map','earth']},
 {id:'markets', base:'trading charts market screener risk', expect:['trading','market','chart','screener','tradingview','finance','stock','crypto']},
 {id:'local', base:'local government public data maps', expect:['local','government','public data','county','city','map','census']},
 {id:'watch', base:'free legal movies documentaries streaming', expect:['kanopy','hoopla','tubi','pluto','pbs','documentary','movie','streaming','internet archive']},
 {id:'livecams', base:'live nature animal cams', expect:['live cam','webcam','nature','wildlife','animal','explore.org']},
 {id:'space', base:'NASA space science streams', expect:['nasa','space','science','mission','astronomy']},
 {id:'games', base:'free browser games', expect:['game','games','itch.io','poki','crazygames','browser game']},
 {id:'maps', base:'interactive maps something cool', expect:['map','earth','terrain','geographic','geospatial','3d']},
 {id:'no-login', base:'free tool without creating an account', expect:['no login','optional login','free - no login','free - optional login'], strictNoLogin:true}
];

const variants = [
 b=>`I need ${b}`,
 b=>`Can you find me ${b}?`,
 b=>`best option for ${b}`,
 b=>`beginner friendly ${b}`,
 b=>`mobile friendly ${b}`,
 b=>`show me a useful ${b}`,
 b=>`im looking for ${b} and dont know where to start`,
 b=>`please help me find ${b} that is simple to use`,
 b=>`i need something for ${b} today`,
 b=>`find ${b} with good task fit rather than a random keyword match`
];

const tests=[];
for (const f of families) for (let i=0;i<variants.length;i++) tests.push({...f,q:variants[i](f.base),variant:i+1});
if(tests.length!==220) throw new Error(`benchmark construction error: ${tests.length}`);

function norm(s=''){return String(s).toLowerCase().replace(/\s+/g,' ').trim()}
function num(text=''){const m=String(text).match(/[\d,]+/);return m?Number(m[0].replace(/,/g,'')):0}
async function openLibrary(page){
 const active=await page.locator('#view-library').evaluate(el=>el.classList.contains('active')).catch(()=>false);
 if(active)return;
 const desktop=page.locator('.navlinks [data-view="library"]');
 if(await desktop.isVisible().catch(()=>false)) await desktop.click();
 else {await page.locator('#menuBtn').click();await page.locator('#mobileNav [data-view="library"]').click();}
 await page.waitForTimeout(80);
}
async function runViewport(browser,viewport,label,runQueries){
 const context=await browser.newContext({viewport,isMobile:viewport.width<700,hasTouch:viewport.width<700});
 const page=await context.newPage();
 const jsErrors=[], sameOriginFailures=[];
 page.on('pageerror',e=>jsErrors.push(String(e)));
 page.on('requestfailed',req=>{try{const u=new URL(req.url());if(u.origin===new URL(URL).origin)sameOriginFailures.push({url:req.url(),failure:req.failure()?.errorText||'failed'})}catch(_){}});
 const response=await page.goto(URL,{waitUntil:'networkidle',timeout:60000});
 if(!response||response.status()!==200) throw new Error(`${label} HTTP ${response&&response.status()}`);
 await page.waitForFunction(()=>document.querySelector('#statIndexed')?.textContent?.includes('1,846'),null,{timeout:30000});
 await page.waitForFunction(()=>document.querySelector('#view-stacks')&&document.querySelector('#view-playbooks'),null,{timeout:15000});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+2);
 const touchIssues=await page.evaluate(()=>[...document.querySelectorAll('button,a.btn,input,select')].filter(el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0&&(r.width<40||r.height<40)}).slice(0,20).map(el=>({tag:el.tagName,text:(el.textContent||el.getAttribute('aria-label')||'').trim().slice(0,40),w:Math.round(el.getBoundingClientRect().width),h:Math.round(el.getBoundingClientRect().height)})));
 const rows=[];
 if(runQueries){
   for(let i=0;i<tests.length;i++){
     const t=tests[i];
     await openLibrary(page);
     const input=page.locator('#searchInput');
     await input.fill(t.q);
     await input.dispatchEvent('input');
     await page.waitForTimeout(180);
     const resultCount=num(await page.locator('#resultCount').innerText().catch(()=>''));
     const cards=page.locator('#toolGrid .tool');
     const n=Math.min(5,await cards.count());
     const top=[];
     for(let k=0;k<n;k++) top.push(norm(await cards.nth(k).innerText()));
     const blob=top.join(' || ');
     const matches=t.expect.filter(x=>blob.includes(norm(x)));
     const avoidHits=(t.avoid||[]).filter(x=>blob.includes(norm(x)));
     const strictAccess=t.strictNoLogin?top.some(x=>/no login|optional login/.test(x)):true;
     const structural=resultCount>0&&n>0;
     const relevant=structural&&matches.length>0&&avoidHits.length===0&&strictAccess;
     rows.push({id:i+1,family:t.id,query:t.q,resultCount,top:top.map(x=>x.slice(0,180)),matches,avoidHits,structural,relevant});
     if(!relevant) console.log(`REVIEW ${i+1}/220 ${t.id}: ${t.q} | top=${top.slice(0,3).join(' / ')}`);
   }
 }
 await context.close();
 return {label,viewport,overflow,touchIssues,jsErrors,sameOriginFailures,rows};
}

(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={url:URL,started_at:new Date().toISOString(),runs:[],summary:{}};
 try{
   // Full benchmark on the middle target viewport; structural/mobile smoke on all three target sizes.
   report.runs.push(await runViewport(browser,{width:390,height:844},'390x844',true));
   report.runs.push(await runViewport(browser,{width:375,height:812},'375x812',false));
   report.runs.push(await runViewport(browser,{width:430,height:932},'430x932',false));
   const rows=report.runs[0].rows;
   const structural=rows.filter(x=>x.structural).length,relevant=rows.filter(x=>x.relevant).length;
   const jsErrors=report.runs.flatMap(x=>x.jsErrors), sameOriginFailures=report.runs.flatMap(x=>x.sameOriginFailures);
   const overflowRuns=report.runs.filter(x=>x.overflow).map(x=>x.label);
   const touchIssueCount=report.runs.reduce((n,x)=>n+x.touchIssues.length,0);
   const relevanceRate=relevant/rows.length;
   report.summary={total:rows.length,structural,relevant,relevanceRate:Number(relevanceRate.toFixed(4)),jsErrors:jsErrors.length,sameOriginFailures:sameOriginFailures.length,overflowRuns,touchIssueCount,viewports:report.runs.map(x=>x.label),finished_at:new Date().toISOString()};
   fs.mkdirSync('expanded-qa',{recursive:true});
   fs.writeFileSync('expanded-qa/atlas-expanded-benchmark-220.json',JSON.stringify(report,null,2));
   const misses=rows.filter(x=>!x.relevant);
   fs.writeFileSync('expanded-qa/atlas-expanded-benchmark-220.md',[
     '# Atlas Expanded 220-Query Benchmark','',
     `Structural: ${structural}/${rows.length}`,
     `Strict top-5 relevance: ${relevant}/${rows.length} (${(relevanceRate*100).toFixed(2)}%)`,
     `JS errors: ${jsErrors.length}`,
     `Critical same-origin request failures: ${sameOriginFailures.length}`,
     `Horizontal overflow viewports: ${overflowRuns.join(', ')||'none'}`,
     `Touch-target observations under 40px: ${touchIssueCount}`,'',
     '## Queries requiring review','',
     ...(misses.length?misses.map(x=>`- **${x.family}** — ${x.query} — top: ${x.top.slice(0,3).join(' / ')}`):['- none'])
   ].join('\n'));
   console.log(`EXPANDED_SUMMARY structural=${structural}/220 relevant=${relevant}/220 rate=${(relevanceRate*100).toFixed(2)}% jsErrors=${jsErrors.length} sameOriginFailures=${sameOriginFailures.length} overflow=${overflowRuns.length}`);
   if(structural!==220||relevanceRate<0.97||jsErrors.length||sameOriginFailures.length||overflowRuns.length) process.exitCode=2;
 } finally {await browser.close();}
})();