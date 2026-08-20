(() => {
  'use strict';
  const STORE='terrainEnvironmentalGIS.market.v1';
  const encode=obj=>{const bytes=new TextEncoder().encode(JSON.stringify(obj));let s='';bytes.forEach(b=>s+=String.fromCharCode(b));return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')};
  const compactGeometry=fc=>{const out={type:'FeatureCollection',features:(fc?.features||[]).map(f=>({type:'Feature',properties:{name:f.properties?.name||'',description:f.properties?.description||''},geometry:f.geometry}))};try{return turf.simplify(out,{tolerance:.00008,highQuality:false,mutate:false})}catch(_){return out}};
  const compactAnalysis=a=>{if(!a)return null;const svc={};['fire','fhz','sra','watershed'].forEach(k=>{const r=a.services?.[k]||{};svc[k]={error:r.error||null,count:r.features?.length||0}});return{generatedAt:a.generatedAt,projectName:a.projectName,areaAcres:a.areaAcres,perimeterMiles:a.perimeterMiles,terrain:a.terrain,priority:a.priority,services:svc}};
  const btn=document.getElementById('shareBtn');
  if(!btn)return;
  btn.addEventListener('click',async e=>{
    e.preventDefault();e.stopImmediatePropagation();
    let saved;try{saved=JSON.parse(localStorage.getItem(STORE)||'{}')}catch(_){saved={}};
    const fc=saved.geojson||{type:'FeatureCollection',features:[]};
    if(!fc.features.length){alert('Add project features before sharing.');return}
    const payload={v:2,name:saved.name||document.getElementById('projectName')?.value||'Shared project',geojson:compactGeometry(fc),analysis:compactAnalysis(saved.analysis),basemap:saved.basemap||'usgsImageryTopo'};
    const encoded=encode(payload);
    if(encoded.length>24000){alert('This project is too detailed for a no-backend share link. Export GeoJSON or simplify the project first.');return}
    const url=new URL('viewer.html',location.href);url.hash=`p=${encoded}`;
    const data={title:`${payload.name} — Terrain Environmental GIS`,text:'Read-only environmental project screening',url:url.toString()};
    try{if(navigator.share)await navigator.share(data);else{await navigator.clipboard.writeText(url.toString());alert('Read-only project link copied.')}}catch(err){if(err?.name!=='AbortError')window.prompt('Copy this read-only project link:',url.toString())}
  },true);
})();
