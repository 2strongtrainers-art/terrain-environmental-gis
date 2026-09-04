const { chromium } = require('playwright-core');
const fs = require('fs');
const URL = process.env.ATLAS_URL || 'https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/';

const intents = [
  {q:'I need a free AI image generator', expect:['image','photo','art','design','generator']},
  {q:'Help me make a short video for social media', expect:['video','clip','reel','media']},
  {q:'I need to design a logo', expect:['logo','design','brand','graphic']},
  {q:'Help me build a resume', expect:['resume','cv','career','job']},
  {q:'I need to edit or work with a PDF', expect:['pdf','document','edit','convert']},
  {q:'Summarize a research paper', expect:['research','paper','scholar','science','academic','summary']},
  {q:'Give me a citation generator', expect:['citation','cite','bibliography','reference']},
  {q:'I want to learn Python for free', expect:['python','learn','coding','programming','course']},
  {q:'I need a calculator for a math problem', expect:['calculator','math','calculate']},
  {q:'Make a QR code', expect:['qr','code','generator']},
  {q:'Show me a useful weather or map tool', expect:['weather','map','radar','earth','geo']},
  {q:'Remove the background from an image', expect:['background','image','photo','remove']},
  {q:'Transcribe audio or a voice recording', expect:['transcribe','audio','speech','voice','text']},
  {q:'I need an AI voice generator', expect:['voice','audio','speech','text to speech','tts']},
  {q:'Help me build a website without coding', expect:['website','site','web','builder','no-code','nocode']},
  {q:'Create a presentation or slideshow', expect:['presentation','slides','powerpoint','deck']},
  {q:'Check my writing and grammar', expect:['grammar','writing','spell','editor']},
  {q:'Translate text into another language', expect:['translate','translation','language']},
  {q:'Find free stock photos', expect:['stock','photo','image','pictures']},
  {q:'Find a free tool I can use without creating an account', expect:['free','no login','no-login','without login']}
];

function num(text=''){ const m=text.match(/[\d,]+/); return m?Number(m[0].replace(/,/g,'')):0; }
function norm(s=''){ return s.toLowerCase(); }
async function goHome(page){
  if(await page.locator('#view-home').evaluate(el=>el.classList.contains('active'))) return;
  await page.locator('#menuBtn').click();
  await page.locator('#mobileNav button[data-view="home"]').click();
  await page.waitForTimeout(100);
}

(async()=>{
  const report={url:URL,started_at:new Date().toISOString(),tests:[],summary:{}};
  const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox']});
  try{
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
    const page=await context.newPage();
    const jsErrors=[];
    page.on('pageerror',e=>jsErrors.push(String(e)));
    const r=await page.goto(URL,{waitUntil:'networkidle',timeout:60000});
    if(!r || r.status()!==200) throw new Error('Atlas HTTP status '+(r&&r.status()));
    await page.waitForFunction(()=>document.querySelector('#statIndexed')?.textContent?.includes('1,834'),null,{timeout:30000});

    for(let i=0;i<intents.length;i++){
      const intent=intents[i];
      await goHome(page);
      const input=page.locator('#commandInput');
      await input.fill(intent.q);
      await page.locator('#routeBtn').click();
      await page.waitForTimeout(180);
      const buttons=page.locator('#routeSuggestions button[data-route]');
      const suggestionCount=await buttons.count();
      const suggestionLabels=suggestionCount?await buttons.allInnerTexts():[];
      let activeView='home', resultCount=0, topCards=[], routeClicked='';
      if(suggestionCount){
        routeClicked=suggestionLabels[0]||'';
        await buttons.first().click();
        await page.waitForTimeout(180);
        activeView=await page.locator('.view.active').getAttribute('id')||'';
        if(activeView==='view-library'){
          resultCount=num(await page.locator('#resultCount').innerText());
          const cards=page.locator('#toolGrid .tool');
          const n=Math.min(5,await cards.count());
          for(let k=0;k<n;k++){
            const c=cards.nth(k);
            topCards.push({name:(await c.locator('h3').innerText()).trim(),text:(await c.innerText()).replace(/\s+/g,' ').trim().slice(0,450)});
          }
        } else if(activeView==='view-free'){
          const cards=page.locator('#freeGrid .tool');
          resultCount=await cards.count();
          const n=Math.min(5,resultCount);
          for(let k=0;k<n;k++){
            const c=cards.nth(k);
            topCards.push({name:(await c.locator('h3').innerText()).trim(),text:(await c.innerText()).replace(/\s+/g,' ').trim().slice(0,450)});
          }
        }
      }
      const blob=norm(topCards.map(x=>x.text).join(' '));
      const relevanceMatches=intent.expect.filter(k=>blob.includes(norm(k)));
      const structuralPass=suggestionCount>0 && resultCount>0 && topCards.length>0;
      const relevancePass=relevanceMatches.length>0;
      const row={id:i+1,query:intent.q,suggestionCount,suggestions:suggestionLabels.slice(0,4),routeClicked,activeView,resultCount,topResults:topCards.map(x=>x.name),relevanceMatches,structuralPass,relevancePass};
      report.tests.push(row);
      console.log(`${structuralPass?'PASS':'FAIL'} #${i+1} | ${intent.q} | route=${routeClicked} | results=${resultCount} | top=${row.topResults.join(' / ')} | relevance=${relevanceMatches.join(',')||'NONE'}`);
    }
    const structuralPassed=report.tests.filter(x=>x.structuralPass).length;
    const relevancePassed=report.tests.filter(x=>x.relevancePass).length;
    report.summary={total:report.tests.length,structuralPassed,relevancePassed,jsErrors,finished_at:new Date().toISOString()};
    fs.mkdirSync('intent-qa',{recursive:true});
    fs.writeFileSync('intent-qa/atlas-common-intents-20.json',JSON.stringify(report,null,2));
    fs.writeFileSync('intent-qa/atlas-common-intents-20.md',[
      '# Atlas 20 Common Intent Test','',
      `Structural passes: ${structuralPassed}/${report.tests.length}`,
      `Top-result keyword relevance passes: ${relevancePassed}/${report.tests.length}`,
      `JavaScript page errors: ${jsErrors.length}`,'',
      '| # | Request | Route | Results | Top results | Relevance |','|---:|---|---|---:|---|---|',
      ...report.tests.map(x=>`| ${x.id} | ${x.query.replace(/\|/g,'/')} | ${x.routeClicked.replace(/\|/g,'/')} | ${x.resultCount} | ${x.topResults.join('; ').replace(/\|/g,'/')} | ${x.relevancePass?'PASS':'REVIEW'} |`)
    ].join('\n'));
    console.log(`SUMMARY structural=${structuralPassed}/20 relevance=${relevancePassed}/20 jsErrors=${jsErrors.length}`);
    if(structuralPassed<20) process.exitCode=2;
  } finally { await browser.close(); }
})();
