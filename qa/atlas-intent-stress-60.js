const { chromium } = require('playwright-core');
const fs=require('fs');
const URL=process.env.ATLAS_URL||'https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/';
const groups=[
 [['free ai image maker','generate an image with ai for free','text to image generator'],['image','photo','art','generator']],
 [['make me a tiktok video','create a short reel','video tool for instagram'],['video','reel','clip','media']],
 [['logo maker','create a brand logo','design my company logo'],['logo','brand','design']],
 [['resume builder','make my cv','help with a job resume'],['resume','cv','career','job']],
 [['pdf editor','convert a pdf file','merge and edit pdf documents'],['pdf','document','edit','convert']],
 [['summarize an academic paper','research paper summary','help me understand a scientific study'],['research','paper','academic','science','study','summary']],
 [['apa citation maker','bibliography generator','cite my sources'],['citation','cite','bibliography','reference']],
 [['python tutorial','free python course','teach me python programming'],['python','programming','coding','course','learn']],
 [['online calculator','solve a math equation','calculate this formula'],['calculator','math','calculate','equation']],
 [['qr generator','create a qr code','turn a link into a qr code'],['qr','code','generator']],
 [['weather radar','forecast map','interactive weather map'],['weather','forecast','radar','map']],
 [['background remover','make photo background transparent','erase image background'],['background','image','photo','transparent']],
 [['audio transcription','turn voice recording into text','speech to text tool'],['transcribe','transcription','speech','voice','audio','text']],
 [['text to speech ai','generate an ai voice','voiceover generator'],['voice','speech','audio','tts','text to speech']],
 [['no code website builder','make a site without coding','build a web page visually'],['website','site','web','builder','no code']],
 [['make a slide deck','powerpoint generator','create presentation slides'],['presentation','slides','powerpoint','deck']],
 [['grammar checker','proofread my writing','fix spelling and grammar'],['grammar','writing','spell','proofread','editor']],
 [['language translator','translate english to spanish','translate this paragraph'],['translate','translation','translator','language']],
 [['royalty free stock images','free stock photography','find stock pictures'],['stock','photo','image','picture']],
 [['free no login tool','tool without signing up','website I can use without an account'],['free','no login','no-login','optional login']]
];
const intents=[];for(const [qs,expect] of groups)for(const q of qs)intents.push({q,expect});
function num(t=''){const m=t.match(/[\d,]+/);return m?Number(m[0].replace(/,/g,'')):0}
async function home(p){if(await p.locator('#view-home').evaluate(e=>e.classList.contains('active')))return;await p.locator('#menuBtn').click();await p.locator('#mobileNav button[data-view="home"]').click();await p.waitForTimeout(60)}
(async()=>{const report={url:URL,tests:[]};const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox']});try{const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});const p=await ctx.newPage();const errors=[];p.on('pageerror',e=>errors.push(String(e)));await p.goto(URL,{waitUntil:'networkidle',timeout:60000});await p.waitForFunction(()=>document.querySelector('#statIndexed')?.textContent?.includes('1,838'));for(let i=0;i<intents.length;i++){const x=intents[i];await home(p);await p.locator('#commandInput').fill(x.q);await p.locator('#routeBtn').click();await p.waitForTimeout(90);const b=p.locator('#routeSuggestions button').first();let count=0,names=[],blob='';if(await b.count()){await b.click();await p.waitForTimeout(100);const active=await p.locator('.view.active').getAttribute('id');const grid=active==='view-free'?'#freeGrid':'#toolGrid';const countSel=active==='view-free'?null:'#resultCount';count=countSel?num(await p.locator(countSel).innerText()):await p.locator(`${grid} .tool`).count();const cards=p.locator(`${grid} .tool`);const n=Math.min(5,await cards.count());for(let k=0;k<n;k++){names.push((await cards.nth(k).locator('h3').innerText()).trim());blob+=' '+(await cards.nth(k).innerText()).toLowerCase()}}const matches=x.expect.filter(k=>blob.includes(k));const structural=count>0&&names.length>0,relevant=matches.length>0;report.tests.push({q:x.q,count,names,matches,structural,relevant});console.log(`${relevant?'RELEVANT':'REVIEW'} #${i+1} | ${x.q} | results=${count} | top=${names.join(' / ')} | match=${matches.join(',')||'NONE'}`)}report.summary={total:intents.length,structural:report.tests.filter(x=>x.structural).length,relevant:report.tests.filter(x=>x.relevant).length,jsErrors:errors.length};fs.mkdirSync('intent-qa',{recursive:true});fs.writeFileSync('intent-qa/atlas-intent-stress-60.json',JSON.stringify(report,null,2));console.log('STRESS_SUMMARY '+JSON.stringify(report.summary));if(report.summary.structural<60||errors.length)process.exitCode=2;await ctx.close()}finally{await browser.close()}})();