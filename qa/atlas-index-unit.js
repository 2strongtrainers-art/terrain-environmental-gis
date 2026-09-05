// Pure data/search tests; no browser, network, or third-party services involved.
const fs=require('node:fs');
const vm=require('node:vm');
const zlib=require('node:zlib');
const assert=require('node:assert/strict');
const html=fs.readFileSync('dist/atlas/index.html','utf8');
const rows=JSON.parse(zlib.gunzipSync(Buffer.from(html.match(/const DATA_B64="([^"]+)"/)[1],'base64')));
let code=html.slice(html.indexOf(' const RAW=JSON.parse(await decodeAtlasData());'),html.indexOf('function saveFav()'));
code=code.replace(' const RAW=JSON.parse(await decodeAtlasData());','const RAW='+JSON.stringify(rows)+';');
code=code.replace('function scoreTool(t,q){','function scoreTool(t,q){scoreCalls++;');
const runtime=fs.readFileSync('atlas-src/atlas-v6.js','utf8');
code+= '\nconst v6ScoreCache=new Map();let v6ResultCache={key:null};const topicName=t=>t.section||"General tools";';
code+=runtime.slice(runtime.indexOf('function getFiltered()'),runtime.indexOf('function v6TopicOptions()'));
code+='\nthis.find=(q,filters={})=>{state={view:"library",query:q,source:"",topic:"",pricing:"",verification:"",priority:"",sort:"relevance",favoritesOnly:false,...filters};return getFiltered()};';
const ctx={window:{atlasStorage:{getItem:()=>null}},document:{},scoreCalls:0};vm.createContext(ctx);vm.runInContext(code,ctx);
assert.equal(rows.length,1850);assert.equal(new Set(rows.map(r=>r[0])).size,1850);
const topicCounts=new Map();for(const r of rows){const t=r[6]||'General tools';topicCounts.set(t,(topicCounts.get(t)||0)+1)}
for(const [name,n] of topicCounts)assert.equal(ctx.find('',{topic:name}).length,n);
assert.equal(topicCounts.size,37);
assert.equal(ctx.find('grants').length,4);
assert.equal(ctx.find('zqxvnonexistent987654321').length,0);
assert.equal(ctx.find('free tool without creating an account').length,4);
const before=ctx.scoreCalls;ctx.find('make a reel');const first=ctx.scoreCalls-before;
for(let i=0;i<10;i++)ctx.find('make a reel');
assert.equal(first,1850);assert.equal(ctx.scoreCalls-before,1850);
const benchmark=fs.readFileSync('qa/atlas-expanded-benchmark-220.js','utf8');
const bctx={};vm.createContext(bctx);vm.runInContext(benchmark.slice(benchmark.indexOf('const families'),benchmark.indexOf('function norm'))+'\nthis.cases=tests;',bctx);
let relevant=0;const failed=[];
for(const test of bctx.cases){
 const top=ctx.find(test.q).slice(0,5);
 const content=top.map(t=>[t.name,t.description,t.accessType].join(' ')).join(' ').toLowerCase();
 const ok=top.length>0&&test.expect.some(x=>content.includes(x.toLowerCase()))&&!(test.avoid||[]).some(x=>content.includes(x.toLowerCase()));
 if(ok)relevant++;else failed.push({query:test.q,top:top.map(t=>t.name)});
}
assert(relevant/220>=.97,JSON.stringify(failed));
console.log(JSON.stringify({records:rows.length,topics:topicCounts.size,topicCountsReconciled:true,grantResults:4,noLoginResults:4,unknownQueryResults:0,repeatedSearches:11,scoreCalls:first,searchBenchmark:{relevant,total:220,failed}},null,2));
