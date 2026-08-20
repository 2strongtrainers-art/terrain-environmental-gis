(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const STORE = 'terrainEnvironmentalGIS.v2';
  const state = { base: null, selected: null, agency: {}, terrainAbort: null };
  const EMPTY = { type: 'FeatureCollection', features: [] };

  const basemaps = {
    osm: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png', 19, '&copy; OpenStreetMap contributors'],
    usgsTopo: ['https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}', 16, 'USGS The National Map'],
    usgsImagery: ['https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}', 16, 'USGS The National Map'],
    usgsImageryTopo: ['https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}', 16, 'USGS The National Map'],
    usgsRelief: ['https://basemap.nationalmap.gov/arcgis/rest/services/USGSShadedReliefOnly/MapServer/tile/{z}/{y}/{x}', 16, 'USGS The National Map']
  };

  const presets = {
    placer: [[39.09, -120.79], 9, 'Placer County, CA'],
    plymouth: [[38.4819, -120.8488], 12, 'Plymouth / Amador County, CA']
  };

  const services = {
    fire: {
      url: 'https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/ArcGIS/rest/services/California_Historic_Fire_Perimeters/FeatureServer/0',
      label: 'CAL FIRE historical perimeters · Firep25_1 (Apr 2026)', minZoom: 7,
      style: { color:'#ef4444', weight:1.3, fillColor:'#ef4444', fillOpacity:.12 }
    },
    fhz: {
      url: 'https://services8.arcgis.com/Xr1lDrwMv89PhjD9/ArcGIS/rest/services/FHSZALL_v25_1_vcp/FeatureServer/0',
      label: 'CAL FIRE / OSFM FHSZ · SRA 2024 + LRA 2025', minZoom: 8,
      style: { color:'#f59e0b', weight:1.2, fillColor:'#f59e0b', fillOpacity:.18 }
    },
    sra: {
      url: 'https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/ArcGIS/rest/services/State_Responsibility_Area/FeatureServer/0',
      label: 'CAL FIRE responsibility areas · SRA26_1', minZoom: 7,
      style: { color:'#a855f7', weight:1.2, fillColor:'#a855f7', fillOpacity:.10 }
    },
    watershed: {
      url: 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/5',
      label: 'USGS 10-digit watersheds · HUC10', minZoom: 7,
      style: { color:'#22d3ee', weight:1.4, fillColor:'#22d3ee', fillOpacity:.04 }
    }
  };

  const map = L.map('map', { zoomControl:true, preferCanvas:true }).setView([38.75,-121],8);
  const project = L.featureGroup().addTo(map);
  setBasemap('usgsImageryTopo');

  map.pm.addControls({ position:'topleft', drawMarker:true, drawCircleMarker:false, drawPolyline:true, drawRectangle:true, drawPolygon:true, drawCircle:false, editMode:true, dragMode:false, cutPolygon:false, removalMode:true, rotateMode:false });

  function status(msg, ms=3500) {
    $('statusBadge').textContent = msg;
    if (ms) setTimeout(() => { if ($('statusBadge').textContent === msg) $('statusBadge').textContent='Ready'; }, ms);
  }

  function setBasemap(key) {
    if (state.base) map.removeLayer(state.base);
    const b = basemaps[key] || basemaps.osm;
    state.base = L.tileLayer(b[0], { maxZoom:b[1], attribution:b[2] }).addTo(map);
    state.base.bringToBack();
  }

  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const xml = v => String(v ?? '').replace(/[<>&'"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;',"'":'&apos;','"':'&quot;'}[c]));

  function normalized(f) {
    f.properties ||= {};
    f.properties.name ||= f.properties.Name || f.properties.NAME || f.properties.title || 'Untitled feature';
    f.properties.description ||= f.properties.Description || f.properties.DESCRIPTION || f.properties.desc || '';
    return f;
  }

  function drawStyle(f) {
    const t=f?.geometry?.type || '';
    if (t.includes('Polygon')) return {color:'#f97316',weight:2,fillColor:'#fb923c',fillOpacity:.18};
    if (t.includes('Line')) return {color:'#38bdf8',weight:4,opacity:.9};
    return {color:'#22c55e',weight:2};
  }

  const pointStyle = (_f,ll) => L.circleMarker(ll,{radius:7,color:'#052e16',weight:2,fillColor:'#22c55e',fillOpacity:.95});

  function syncLayer(layer) {
    const gj=layer.toGeoJSON();
    gj.properties=Object.assign({},layer.feature?.properties||{},gj.properties||{});
    layer.feature=gj;
  }

  function bindProjectLayer(layer) {
    layer.on('click', e => { if (map.pm.globalDrawModeEnabled?.()) return; L.DomEvent.stopPropagation(e); selectFeature(layer); });
    layer.on('pm:edit', () => { syncLayer(layer); updateSummary(); save(); });
  }

  function addGeoJSON(gj, source='Imported') {
    const fc=gj?.type==='FeatureCollection'?gj:gj?.type==='Feature'?{type:'FeatureCollection',features:[gj]}:null;
    if (!fc) throw new Error('No supported GeoJSON features found.');
    fc.features.forEach(normalized);
    L.geoJSON(fc,{style:drawStyle,pointToLayer:pointStyle,onEachFeature:(f,l)=>{l.feature=f;l._sourceName=source;bindProjectLayer(l);}}).eachLayer(l=>project.addLayer(l));
    if(project.getLayers().length) map.fitBounds(project.getBounds(),{padding:[24,24],maxZoom:16});
    updateSummary(); save(); status(`Added ${fc.features.length} feature${fc.features.length===1?'':'s'} from ${source}`);
  }

  function collect() {
    const features=[];
    project.eachLayer(l=>{if(!l.toGeoJSON)return;syncLayer(l);const f=l.feature||l.toGeoJSON();f.type==='FeatureCollection'?features.push(...f.features):features.push(f);});
    return {type:'FeatureCollection',features};
  }

  function metrics(f) {
    const t=f?.geometry?.type||'';
    try {
      if(t.includes('Polygon')){const m2=turf.area(f);return `${(m2/4046.8564224).toFixed(2)} acres · ${(m2/1e6).toFixed(3)} km²`;}
      if(t.includes('Line')){const km=turf.length(f,{units:'kilometers'});return `${(km*.621371).toFixed(2)} miles · ${km.toFixed(2)} km`;}
      if(t==='Point'){const [x,y]=f.geometry.coordinates;return `${y.toFixed(6)}, ${x.toFixed(6)}`;}
    } catch(_){}
    return t;
  }

  function selectFeature(l) {
    state.selected=l;syncLayer(l);$('featureEmpty').classList.add('hidden');$('featureEditor').classList.remove('hidden');
    $('featureName').value=l.feature.properties?.name||'';$('featureDescription').value=l.feature.properties?.description||'';$('featureMetrics').textContent=metrics(l.feature);
  }
  function clearSelected(){state.selected=null;$('featureEmpty').classList.remove('hidden');$('featureEditor').classList.add('hidden');}

  function updateSummary(){const fc=collect();let acres=0,miles=0,points=0;fc.features.forEach(f=>{const t=f.geometry?.type||'';try{if(t.includes('Polygon'))acres+=turf.area(f)/4046.8564224;else if(t.includes('Line'))miles+=turf.length(f,{units:'miles'});else if(t.includes('Point'))points++;}catch(_){}});$('summary').innerHTML=[['Features',fc.features.length],['Mapped acres',acres.toFixed(1)],['Line miles',miles.toFixed(2)],['Points',points]].map(([a,b])=>`<div class="summary-item"><b>${b}</b><span>${a}</span></div>`).join('');}

  function save(){try{localStorage.setItem(STORE,JSON.stringify({name:$('projectName').value,geojson:collect(),center:map.getCenter(),zoom:map.getZoom(),basemap:$('basemapSelect').value}));}catch(e){console.warn(e);}}
  function restore(){try{const raw=localStorage.getItem(STORE);if(!raw)return;const s=JSON.parse(raw);$('projectName').value=s.name||'Untitled Project';if(s.basemap&&basemaps[s.basemap]){$('basemapSelect').value=s.basemap;setBasemap(s.basemap);}if(s.geojson?.features?.length)addGeoJSON(s.geojson,'Autosaved project');if(s.center&&s.zoom)map.setView([s.center.lat,s.center.lng],s.zoom);status('Restored autosaved project');}catch(e){console.warn(e);}}

  async function parseFile(file){
    const ext=file.name.split('.').pop().toLowerCase();
    if(['geojson','json'].includes(ext))return JSON.parse(await file.text());
    if(ext==='kml')return toGeoJSON.kml(new DOMParser().parseFromString(await file.text(),'text/xml'));
    if(ext==='gpx')return toGeoJSON.gpx(new DOMParser().parseFromString(await file.text(),'text/xml'));
    if(ext==='kmz'){const z=await JSZip.loadAsync(await file.arrayBuffer());const n=Object.keys(z.files).find(x=>x.toLowerCase().endsWith('.kml'));if(!n)throw new Error('KMZ contains no KML.');return toGeoJSON.kml(new DOMParser().parseFromString(await z.file(n).async('text'),'text/xml'));}
    if(ext==='zip'){const p=await shp(await file.arrayBuffer());return Array.isArray(p)?{type:'FeatureCollection',features:p.flatMap(x=>x.features||[])}:p;}
    if(ext==='csv'){const r=Papa.parse(await file.text(),{header:true,dynamicTyping:true,skipEmptyLines:true});const fs=[];for(const row of r.data){const ks=Object.keys(row),la=ks.find(k=>/^(lat|latitude|y)$/i.test(k)),lo=ks.find(k=>/^(lon|lng|long|longitude|x)$/i.test(k));if(la&&lo&&Number.isFinite(Number(row[la]))&&Number.isFinite(Number(row[lo])))fs.push({type:'Feature',geometry:{type:'Point',coordinates:[Number(row[lo]),Number(row[la])]},properties:row});}if(!fs.length)throw new Error('CSV needs latitude/longitude columns.');return {type:'FeatureCollection',features:fs};}
    throw new Error(`Unsupported file type: .${ext}`);
  }

  const safeName=()=>($('projectName').value||'terrain-project').trim().replace(/[^a-z0-9-_]+/gi,'-').replace(/^-|-$/g,'')||'terrain-project';
  function download(name,text,type='application/octet-stream'){const u=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1500);}
  function toGPX(fc){const w=[],t=[];fc.features.forEach((f,i)=>{const g=f.geometry,n=xml(f.properties?.name||`Feature ${i+1}`),d=xml(f.properties?.description||'');if(!g)return;if(g.type==='Point')w.push(`<wpt lat="${g.coordinates[1]}" lon="${g.coordinates[0]}"><name>${n}</name><desc>${d}</desc></wpt>`);if(g.type==='LineString')t.push(`<trk><name>${n}</name><trkseg>${g.coordinates.map(c=>`<trkpt lat="${c[1]}" lon="${c[0]}"></trkpt>`).join('')}</trkseg></trk>`);});return `<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Terrain Environmental GIS" xmlns="http://www.topografix.com/GPX/1/1">${w.join('')}${t.join('')}</gpx>`;}

  async function searchLocation(){const q=$('searchInput').value.trim();if(!q)return;status('Searching…',0);try{const r=await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(q)}`,{headers:{Accept:'application/json'}});if(!r.ok)throw Error('Search unavailable');const d=await r.json();if(!d.length)throw Error('No matching place found');map.setView([+d[0].lat,+d[0].lon],13);status(d[0].display_name,5000);}catch(e){status(e.message||'Search failed',5000);}}

  async function elevation(lat,lng,signal){const u=`https://epqs.nationalmap.gov/v1/json?x=${encodeURIComponent(lng)}&y=${encodeURIComponent(lat)}&units=Meters&wkid=4326&includeDate=false`;const r=await fetch(u,{signal});if(!r.ok)throw Error('USGS elevation unavailable');const d=await r.json();const v=Number(d.value??d.USGS_Elevation_Point_Query_Service?.Elevation_Query?.Elevation);if(!Number.isFinite(v))throw Error('No elevation value');return v;}
  const aspectName=a=>['N','NE','E','SE','S','SW','W','NW'][Math.round(a/45)%8];
  async function terrainAt(ll){if(state.terrainAbort)state.terrainAbort.abort();state.terrainAbort=new AbortController();const card=$('elevationCard');card.classList.remove('hidden');card.textContent='USGS terrain: loading…';try{const m=30,dLat=m/111320,dLng=m/(111320*Math.max(.2,Math.cos(ll.lat*Math.PI/180))),s=state.terrainAbort.signal;const [c,n,so,e,w]=await Promise.all([elevation(ll.lat,ll.lng,s),elevation(ll.lat+dLat,ll.lng,s),elevation(ll.lat-dLat,ll.lng,s),elevation(ll.lat,ll.lng+dLng,s),elevation(ll.lat,ll.lng-dLng,s)]);const dx=(e-w)/(2*m),dy=(n-so)/(2*m),slope=Math.atan(Math.hypot(dx,dy))*180/Math.PI,aspect=(Math.atan2(-dx,-dy)*180/Math.PI+360)%360;card.innerHTML=`<strong>Terrain screening</strong><br>Elevation: ${(c*3.28084).toFixed(0)} ft · ${c.toFixed(0)} m<br>Slope: ${slope.toFixed(1)}° · ${(Math.tan(slope*Math.PI/180)*100).toFixed(0)}%<br>Aspect: ${aspectName(aspect)} · ${aspect.toFixed(0)}°<br><span style="color:#9ca3af">USGS sample · ~30 m neighborhood</span>`;}catch(e){if(e.name!=='AbortError')card.textContent='USGS terrain analysis unavailable at this point.';}}

  function agencyGroup(cfg){const g=L.layerGroup().addTo(map);g._cfg=cfg;return g;}
  async function refreshAgency(g){const c=g._cfg;g.clearLayers();if(map.getZoom()<c.minZoom){status(`${c.label}: zoom in to load`,3500);return;}const b=map.getBounds(),geom=`${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`,u=`${c.url}/query?where=1%3D1&geometry=${encodeURIComponent(geom)}&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&outSR=4326&f=geojson&resultRecordCount=2000`;try{const r=await fetch(u);if(!r.ok)throw Error();const gj=await r.json();if(gj.error)throw Error(gj.error.message);L.geoJSON(gj,{style:c.style,pointToLayer:pointStyle,onEachFeature:(f,l)=>{const p=f.properties||{},keys=['FIRE_NAME','YEAR_','GIS_ACRES','FHSZ_Description','FHSZ_Descr','FHSZ','SRA','NAME','name','HUC10','huc10','areaacres'];const rows=keys.filter(k=>p[k]!==undefined&&p[k]!==null&&p[k]!=='').slice(0,6).map(k=>`<div><strong>${esc(k.replaceAll('_',' '))}:</strong> ${esc(p[k])}</div>`).join('');if(rows)l.bindPopup(`<div class="agency-popup"><strong>${esc(c.label)}</strong>${rows}</div>`);}}).addTo(g);status(`${c.label}: ${gj.features?.length||0} visible features`);}catch(_){status(`${c.label} could not load from its public GIS service`,5500);}}
  async function toggleAgency(key,on){if(!on){if(state.agency[key])map.removeLayer(state.agency[key]);delete state.agency[key];return;}const g=agencyGroup(services[key]);state.agency[key]=g;await refreshAgency(g);}

  map.on('pm:create',e=>{const l=e.layer;project.addLayer(l);l.feature=l.toGeoJSON();l.feature.properties={name:'New feature',description:'',source:'Drawn in Terrain Environmental GIS'};bindProjectLayer(l);selectFeature(l);updateSummary();save();});
  map.on('pm:remove',()=>{clearSelected();updateSummary();save();});
  map.on('moveend',()=>{Object.values(state.agency).forEach(refreshAgency);save();});
  map.on('click',e=>{if(!map.pm.globalDrawModeEnabled?.()){clearSelected();terrainAt(e.latlng);}});

  $('importBtn').addEventListener('click',()=>$('fileInput').click());
  $('fileInput').addEventListener('change',async e=>{for(const f of e.target.files){status(`Importing ${f.name}…`,0);try{addGeoJSON(await parseFile(f),f.name);}catch(x){status(`${f.name}: ${x.message}`,6500);}}e.target.value='';});
  $('basemapSelect').addEventListener('change',e=>{setBasemap(e.target.value);save();});
  document.querySelectorAll('.preset').forEach(b=>b.addEventListener('click',()=>{const p=presets[b.dataset.preset];map.setView(p[0],p[1]);status(p[2]);if(innerWidth<=720)$('leftPanel').classList.remove('open');}));
  $('searchBtn').addEventListener('click',searchLocation);$('searchInput').addEventListener('keydown',e=>{if(e.key==='Enter')searchLocation();});
  $('locateBtn').addEventListener('click',()=>{map.locate({setView:true,maxZoom:16,enableHighAccuracy:true});status('Locating…',0);});
  map.on('locationfound',e=>{L.circleMarker(e.latlng,{radius:8,color:'#fff',weight:2,fillColor:'#0ea5e9',fillOpacity:1}).addTo(map).bindPopup('Current location').openPopup();status(`Located within ~${Math.round(e.accuracy)} m`);});map.on('locationerror',()=>status('Location permission denied or unavailable',5000));
  $('projectName').addEventListener('input',save);
  $('saveFeatureBtn').addEventListener('click',()=>{if(!state.selected)return;syncLayer(state.selected);state.selected.feature.properties.name=$('featureName').value.trim()||'Untitled feature';state.selected.feature.properties.description=$('featureDescription').value.trim();save();status('Feature saved');});
  $('deleteFeatureBtn').addEventListener('click',()=>{if(!state.selected)return;project.removeLayer(state.selected);clearSelected();updateSummary();save();status('Feature deleted');});
  [['firePerimetersToggle','fire'],['fhzToggle','fhz'],['sraToggle','sra'],['watershedToggle','watershed']].forEach(([id,k])=>$(id).addEventListener('change',e=>toggleAgency(k,e.target.checked)));
  document.querySelectorAll('[data-export]').forEach(b=>b.addEventListener('click',()=>{const fc=collect();if(!fc.features.length)return status('Nothing to export',4000);const n=safeName(),t=b.dataset.export;if(t==='geojson')download(`${n}.geojson`,JSON.stringify(fc,null,2),'application/geo+json');if(t==='kml')download(`${n}.kml`,tokml(fc),'application/vnd.google-earth.kml+xml');if(t==='gpx')download(`${n}.gpx`,toGPX(fc),'application/gpx+xml');}));
  $('summaryBtn').addEventListener('click',()=>{const fc=collect();let a=0,m=0,p=0,poly=0,line=0;fc.features.forEach(f=>{const t=f.geometry?.type||'';try{if(t.includes('Polygon')){poly++;a+=turf.area(f)/4046.8564224}else if(t.includes('Line')){line++;m+=turf.length(f,{units:'miles'})}else if(t.includes('Point'))p++;}catch(_){}});download(`${safeName()}-summary.txt`,`Terrain Environmental GIS Project Summary\nProject: ${$('projectName').value}\nGenerated: ${new Date().toLocaleString()}\n\nFeatures: ${fc.features.length}\nPoints: ${p}\nLines: ${line}\nPolygons: ${poly}\nTotal mapped acres: ${a.toFixed(2)}\nTotal line miles: ${m.toFixed(2)}\nBasemap: ${$('basemapSelect').selectedOptions[0].text}\nActive environmental layers: ${Object.values(state.agency).map(g=>g._cfg.label).join('; ')||'None'}\n\nProject data is processed locally in the browser. Public terrain and environmental services remain subject to their source metadata and availability.`,'text/plain');});
  $('clearBtn').addEventListener('click',()=>{if(!confirm('Clear all mapped project features and the local autosave on this device?'))return;project.clearLayers();clearSelected();localStorage.removeItem(STORE);$('projectName').value='Untitled Project';updateSummary();status('Project cleared');});
  $('helpBtn').addEventListener('click',()=>$('helpDialog').showModal());$('closeHelpBtn').addEventListener('click',()=>$('helpDialog').close());$('panelToggle').addEventListener('click',()=>$('leftPanel').classList.toggle('open'));
  window.addEventListener('pagehide',save);

  updateSummary();restore();
})();
