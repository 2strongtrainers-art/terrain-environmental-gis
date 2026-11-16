const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const CURRENT = 'terrainEnvironmentalGIS.market.v1';
const LEGACY = 'terrainEnvironmentalGIS.v2';
const clone = value => JSON.parse(JSON.stringify(value));
const feature = {type:'Feature', properties:{name:'Saved boundary', custom:'retained'},
  geometry:{type:'Polygon', coordinates:[[[-120.75,39],[-120.74,39],[-120.74,39.01],[-120.75,39]]]}};
const saved = {name:'Existing project', geojson:{type:'FeatureCollection',features:[feature]},
  center:{lat:39,lng:-120.75},zoom:12,basemap:'osm'};

function storageHarness(entries) {
  const storage = new Map(Object.entries(entries));
  const writes = [];
  const fields = {projectName:{value:'Untitled Project'},basemapSelect:{value:'usgsImageryTopo'}};
  let features = [];
  const context = {
    STORE:CURRENT, LEGACY_STORE:LEGACY,
    state:{readOnly:false,restoring:false,lastAnalysis:null},
    basemaps:{osm:[],usgsImageryTopo:[]},
    $:id=>fields[id],
    localStorage:{getItem:key=>storage.get(key)??null,
      setItem:(key,value)=>{writes.push({key,value});storage.set(key,value)}},
    collect:()=>({type:'FeatureCollection',features}),
    status:()=>{}, console:{warn:()=>{}}, renderAnalysis:()=>{}, setBasemap:()=>{},
    map:{getCenter:()=>saved.center,getZoom:()=>12,
      setView:()=>vm.runInContext('save()',context)},
    // Restoring features and map position fires the same save callbacks as the app.
    addGeoJSON:fc=>{features=clone(fc.features);context.state.lastAnalysis=null;
      vm.runInContext('save()',context)},
  };
  vm.createContext(context);
  const code = fs.readFileSync('app.js','utf8');
  vm.runInContext(code.slice(code.indexOf('  function save()'),code.indexOf('  async function parseFile')),context);
  return {storage,writes,context,restore:()=>vm.runInContext('restore()',context)};
}

test('old published projects migrate without modifying their backup or custom properties',()=>{
  const original=JSON.stringify(saved), h=storageHarness({[LEGACY]:original});
  h.restore();
  const restored=JSON.parse(h.storage.get(CURRENT));
  assert.equal(h.storage.get(LEGACY),original);
  assert.deepEqual(restored.geojson,saved.geojson);
  assert.equal(restored.name,saved.name);
  assert.equal(restored.basemap,'osm');
  assert.equal(h.writes.length,1,'Only the complete restored snapshot is persisted');
});

test('restoring feature and map events cannot erase saved screening results',()=>{
  const analysis={projectName:saved.name,generatedAt:'2026-11-16T00:00:00Z',areaAcres:20,services:{}};
  const h=storageHarness({[CURRENT]:JSON.stringify({...saved,analysis}),[LEGACY]:JSON.stringify(saved)});
  h.restore();h.restore();
  assert.deepEqual(JSON.parse(h.storage.get(CURRENT)).analysis,analysis);
  assert.equal(h.writes.length,2);
  assert(h.writes.every(write=>JSON.parse(write.value).analysis.areaAcres===20));
});

test('an intentionally cleared current project does not resurrect the old project',()=>{
  const empty={...saved,name:'Untitled Project',geojson:{type:'FeatureCollection',features:[]}};
  const h=storageHarness({[CURRENT]:JSON.stringify(empty),[LEGACY]:JSON.stringify(saved)});
  h.restore();
  assert.deepEqual(JSON.parse(h.storage.get(CURRENT)).geojson.features,[]);
});

test('an unreadable current save is left intact and the restore guard is released',()=>{
  const h=storageHarness({[CURRENT]:'not valid JSON',[LEGACY]:JSON.stringify(saved)});
  h.restore();
  assert.equal(h.storage.get(CURRENT),'not valid JSON');
  assert.equal(h.writes.length,0);
  assert.equal(h.context.state.restoring,false);
});

function workerHarness() {
  const handlers={}, deleted=[], added=[], written=[];
  const cache={addAll:async files=>added.push(...files),
    put:async (request,response)=>written.push({url:request.url,status:response.status}),
    match:async ()=>new Response('cached shell')};
  const context={URL,Response,Set,
    self:{registration:{scope:'https://example.test/terrain-environmental-gis/'},
      location:{origin:'https://example.test'},addEventListener:(event,handler)=>handlers[event]=handler},
    caches:{open:async()=>cache,
      keys:async()=>['terrain-gis-shell-v1','terrain-gis-shell-v2','alan-fishing-escape-v22','atlas-cache','other-app'],
      delete:async key=>deleted.push(key)},
    fetch:async()=>new Response('current shell')};
  vm.runInNewContext(fs.readFileSync('sw.js','utf8'),context);
  return {context,handlers,cache,deleted,added,written};
}

test('GIS shell activation preserves fishing, Atlas and unrelated caches',async()=>{
  const h=workerHarness();let pending;
  h.handlers.install({waitUntil:p=>pending=p});await pending;
  assert(h.added.includes('./share-fix.js')&&h.added.includes('./report-plus.js'));
  h.handlers.activate({waitUntil:p=>pending=p});await pending;
  assert.deepEqual(h.deleted,['terrain-gis-shell-v1']);
});

test('root GIS worker does not intercept Atlas, fishing, third-party or unrelated resources',()=>{
  const h=workerHarness();
  for(const path of ['https://example.test/terrain-environmental-gis/atlas/',
    'https://example.test/terrain-environmental-gis/alan-fishing-escape/index.html',
    'https://example.test/another-app/index.html','https://cdn.example.test/app.js']) {
    let intercepted=false;
    h.handlers.fetch({request:new Request(path),respondWith:()=>intercepted=true});
    assert.equal(intercepted,false,path);
  }
});

test('GIS shell uses the network, retains a good cache on server error, and has an offline fallback',async()=>{
  const h=workerHarness();let pending;
  const request=new Request('https://example.test/terrain-environmental-gis/report-plus.js');
  const get=async()=>{h.handlers.fetch({request,respondWith:p=>pending=p});return await pending};
  assert.equal(await (await get()).text(),'current shell');assert.equal(h.written.length,1);
  h.context.fetch=async()=>new Response('server error',{status:503});
  assert.equal((await get()).status,503);assert.equal(h.written.length,1);
  h.context.fetch=async()=>{throw Error('offline')};
  assert.equal(await (await get()).text(),'cached shell');
});

test('a rejected cache write never discards a successful network response',async()=>{
  const h=workerHarness();let pending;
  h.cache.put=async()=>{throw Error('QuotaExceededError')};
  h.handlers.fetch({request:new Request('https://example.test/terrain-environmental-gis/app.js'),
    respondWith:p=>pending=p});
  const response=await pending;
  assert.equal(response.status,200);
  assert.equal(await response.text(),'current shell');
});

test('unavailable cache storage leaves online responses usable and offline errors explicit',async()=>{
  const h=workerHarness();let pending;
  h.context.caches.open=async()=>{throw Error('Storage unavailable')};
  const request=new Request('https://example.test/terrain-environmental-gis/app.js');
  const get=async()=>{h.handlers.fetch({request,respondWith:p=>pending=p});return await pending};
  assert.equal(await (await get()).text(),'current shell');
  h.context.fetch=async()=>{throw Error('offline')};
  assert.equal((await get()).type,'error');
});
