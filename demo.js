(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const status = (msg, tone='') => {
    const el = $('status');
    el.textContent = msg;
    el.dataset.tone = tone;
  };

  const SERVICE = {
    fire: {
      label: 'CAL FIRE historical fire perimeters',
      url: 'https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/ArcGIS/rest/services/California_Historic_Fire_Perimeters/FeatureServer/0',
      style: { color:'#ef4444', weight:2, fillColor:'#ef4444', fillOpacity:.10 }
    },
    fhz: {
      label: 'CAL FIRE / OSFM Fire Hazard Severity Zones',
      url: 'https://services8.arcgis.com/Xr1lDrwMv89PhjD9/ArcGIS/rest/services/FHSZALL_v25_1_vcp/FeatureServer/0',
      style: { color:'#f59e0b', weight:2, fillColor:'#f59e0b', fillOpacity:.12 }
    },
    sra: {
      label: 'CAL FIRE State Responsibility Area',
      url: 'https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/ArcGIS/rest/services/State_Responsibility_Area/FeatureServer/0',
      style: { color:'#a855f7', weight:2, fillColor:'#a855f7', fillOpacity:.08 }
    },
    watershed: {
      label: 'USGS HUC10 watersheds',
      url: 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/5',
      style: { color:'#22d3ee', weight:2, fillColor:'#22d3ee', fillOpacity:.04 }
    }
  };

  const SAMPLE = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: {
          name: 'Demo Area of Interest',
          description: 'Sample screening polygon near the CAL FIRE-listed Mosquito Fire incident location east of Foresthill. This is a demonstration AOI, not an official incident or property boundary.'
        },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [-120.7560, 38.9965],
            [-120.7325, 38.9965],
            [-120.7325, 39.0155],
            [-120.7560, 39.0155],
            [-120.7560, 38.9965]
          ]]
        }
      },
      {
        type: 'Feature',
        properties: { name: 'Illustrative treatment corridor', description: 'Example line feature used to prove automatic distance calculations.' },
        geometry: { type: 'LineString', coordinates: [[-120.7540,39.0000],[-120.7460,39.0055],[-120.7350,39.0120]] }
      },
      {
        type: 'Feature',
        properties: { name: 'CAL FIRE-listed Mosquito Fire incident location', description: 'CAL FIRE incident page location: 39.00591, -120.7447.' },
        geometry: { type: 'Point', coordinates: [-120.7447,39.00591] }
      }
    ]
  };

  const map = L.map('demoMap', { preferCanvas:true }).setView([39.006,-120.7447],14);
  L.tileLayer('https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}', {
    maxZoom:16,
    attribution:'USGS The National Map'
  }).addTo(map);

  const project = L.featureGroup().addTo(map);
  const overlays = L.layerGroup().addTo(map);
  let lastAnalysis = null;

  map.pm.addControls({
    position:'topleft', drawMarker:false, drawCircleMarker:false, drawPolyline:false,
    drawRectangle:true, drawPolygon:true, drawCircle:false, editMode:true,
    dragMode:false, cutPolygon:false, removalMode:true, rotateMode:false
  });

  function projectStyle(feature) {
    const t = feature?.geometry?.type || '';
    if (t.includes('Polygon')) return { color:'#fb923c', weight:3, fillColor:'#fb923c', fillOpacity:.18 };
    if (t.includes('Line')) return { color:'#38bdf8', weight:5, opacity:.95 };
    return { color:'#22c55e', radius:8, weight:2, fillOpacity:1 };
  }

  function pointLayer(_feature, latlng) {
    return L.circleMarker(latlng, { radius:8, color:'#052e16', weight:2, fillColor:'#22c55e', fillOpacity:1 });
  }

  function loadSample() {
    project.clearLayers();
    overlays.clearLayers();
    L.geoJSON(SAMPLE, {
      style:projectStyle,
      pointToLayer:pointLayer,
      onEachFeature:(f,l) => l.bindPopup(`<strong>${escapeHtml(f.properties?.name || 'Feature')}</strong><br>${escapeHtml(f.properties?.description || '')}`)
    }).eachLayer(l => project.addLayer(l));
    map.fitBounds(project.getBounds(), { padding:[24,24] });
    lastAnalysis = null;
    $('exportBtn').disabled=true;
    $('results').innerHTML = '<div class="placeholder">Demo loaded. Press <strong>Analyze live data</strong>.</div>';
    status('Demo AOI loaded. Ready for live analysis.', 'ok');
    updateQuickMetrics();
  }

  function collect() {
    const features=[];
    project.eachLayer(l => {
      if (!l.toGeoJSON) return;
      const f=l.toGeoJSON();
      if (f.type==='FeatureCollection') features.push(...f.features); else features.push(f);
    });
    return { type:'FeatureCollection', features };
  }

  function areaPolygon() {
    const polygons = collect().features.filter(f => /Polygon/.test(f.geometry?.type || ''));
    if (!polygons.length) return null;
    return polygons.sort((a,b) => turf.area(b)-turf.area(a))[0];
  }

  function updateQuickMetrics() {
    const fc = collect();
    let acres=0, miles=0;
    fc.features.forEach(f => {
      try {
        if (/Polygon/.test(f.geometry?.type||'')) acres += turf.area(f)/4046.8564224;
        if (/Line/.test(f.geometry?.type||'')) miles += turf.length(f,{units:'miles'});
      } catch (_) {}
    });
    $('quickMetrics').innerHTML = `<div><b>${acres.toFixed(1)}</b><span>mapped acres</span></div><div><b>${miles.toFixed(2)}</b><span>line miles</span></div><div><b>${fc.features.length}</b><span>features</span></div>`;
  }

  function escapeHtml(v='') {
    return String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  async function elevation(lat,lng) {
    const u=`https://epqs.nationalmap.gov/v1/json?x=${encodeURIComponent(lng)}&y=${encodeURIComponent(lat)}&units=Meters&wkid=4326&includeDate=false`;
    const r=await fetch(u);
    if(!r.ok) throw new Error('USGS elevation unavailable');
    const d=await r.json();
    const v=Number(d.value ?? d.USGS_Elevation_Point_Query_Service?.Elevation_Query?.Elevation);
    if(!Number.isFinite(v)) throw new Error('No elevation value');
    return v;
  }

  function aspectName(a) {
    return ['N','NE','E','SE','S','SW','W','NW'][Math.round(a/45)%8];
  }

  async function terrainSummary(poly) {
    const center=turf.centroid(poly).geometry.coordinates;
    const lng=center[0], lat=center[1];
    const m=30, dLat=m/111320, dLng=m/(111320*Math.max(.2,Math.cos(lat*Math.PI/180)));
    const [c,n,s,e,w]=await Promise.all([
      elevation(lat,lng), elevation(lat+dLat,lng), elevation(lat-dLat,lng), elevation(lat,lng+dLng), elevation(lat,lng-dLng)
    ]);
    const dx=(e-w)/(2*m), dy=(n-s)/(2*m);
    const slope=Math.atan(Math.hypot(dx,dy))*180/Math.PI;
    const aspect=(Math.atan2(-dx,-dy)*180/Math.PI+360)%360;
    return { elevationM:c, elevationFt:c*3.28084, slopeDeg:slope, slopePct:Math.tan(slope*Math.PI/180)*100, aspectDeg:aspect, aspect:aspectName(aspect) };
  }

  function envelope(poly) {
    const b=turf.bbox(poly);
    return `${b[0]},${b[1]},${b[2]},${b[3]}`;
  }

  async function queryService(key, poly) {
    const cfg=SERVICE[key];
    const u=`${cfg.url}/query?where=1%3D1&geometry=${encodeURIComponent(envelope(poly))}&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&outSR=4326&f=geojson&resultRecordCount=2000`;
    const r=await fetch(u);
    if(!r.ok) throw new Error(`${cfg.label} unavailable`);
    const gj=await r.json();
    if(gj.error) throw new Error(gj.error.message || `${cfg.label} error`);
    const features=(gj.features||[]).filter(f => {
      try { return turf.booleanIntersects(poly,f); } catch (_) { return true; }
    });
    return { key, cfg, features };
  }

  function firstProp(props, keys) {
    for (const k of keys) if (props?.[k] !== undefined && props?.[k] !== null && String(props[k]).trim() !== '') return props[k];
    return null;
  }

  function unique(values) {
    return [...new Set(values.filter(v => v !== null && v !== undefined && String(v).trim() !== '').map(v => String(v)))];
  }

  function overlayResult(result) {
    if (!result?.features?.length) return;
    L.geoJSON({type:'FeatureCollection',features:result.features}, { style:result.cfg.style }).addTo(overlays);
  }

  function summarizeService(result) {
    if (!result) return 'Unavailable';
    const f=result.features;
    if (result.key==='fire') {
      const items=unique(f.map(x => {
        const p=x.properties||{};
        const name=firstProp(p,['FIRE_NAME','FIRENAME','INCIDENT','NAME','name']) || 'Unnamed perimeter';
        const year=firstProp(p,['YEAR_','FIRE_YEAR','YEAR','year']);
        return year ? `${name} (${year})` : name;
      }));
      return f.length ? `${f.length} intersecting perimeter${f.length===1?'':'s'}${items.length?`: ${items.slice(0,4).join(', ')}`:''}` : 'No intersecting historical perimeter returned';
    }
    if (result.key==='fhz') {
      const vals=unique(f.flatMap(x => {
        const p=x.properties||{};
        return [firstProp(p,['FHSZ_Description','FHSZ_Descr','FHSZ','HAZ_CLASS','HAZARD','CLASS','ZONE'])];
      }));
      return f.length ? `${f.length} intersecting zone feature${f.length===1?'':'s'}${vals.length?`: ${vals.slice(0,5).join(', ')}`:''}` : 'No intersecting zone returned';
    }
    if (result.key==='sra') return f.length ? `Yes — ${f.length} SRA feature${f.length===1?'':'s'} intersect the AOI` : 'No SRA intersection returned';
    if (result.key==='watershed') {
      const vals=unique(f.map(x => {
        const p=x.properties||{};
        const name=firstProp(p,['NAME','Name','name','GNIS_NAME']);
        const huc=firstProp(p,['HUC10','huc10','HUC_10']);
        return [name,huc].filter(Boolean).join(' · ');
      }));
      return f.length ? `${f.length} watershed${f.length===1?'':'s'}${vals.length?`: ${vals.slice(0,4).join(', ')}`:''}` : 'No HUC10 watershed returned';
    }
    return `${f.length} intersecting features`;
  }

  async function analyze() {
    const poly=areaPolygon();
    if(!poly){ status('Draw or load a polygon first.', 'bad'); return; }
    $('analyzeBtn').disabled=true;
    overlays.clearLayers();
    $('results').innerHTML='<div class="placeholder">Running live USGS and environmental queries…</div>';
    status('Analyzing AOI against live public GIS services…');

    const acres=turf.area(poly)/4046.8564224;
    const perimeter=turf.length(turf.polygonToLine(poly),{units:'miles'});
    const terrainPromise=terrainSummary(poly).catch(e => ({error:e.message}));
    const serviceResults=await Promise.all(Object.keys(SERVICE).map(async key => {
      try { return await queryService(key,poly); } catch (e) { return {key,cfg:SERVICE[key],features:[],error:e.message}; }
    }));
    const terrain=await terrainPromise;
    serviceResults.forEach(r => { if(!r.error) overlayResult(r); });

    const byKey=Object.fromEntries(serviceResults.map(r => [r.key,r]));
    const rows=[
      ['Project area', `${acres.toFixed(1)} acres`],
      ['Project perimeter', `${perimeter.toFixed(2)} miles`],
      ['Terrain at AOI center', terrain.error ? `Unavailable: ${terrain.error}` : `${terrain.elevationFt.toFixed(0)} ft elevation · ${terrain.slopeDeg.toFixed(1)}° (${terrain.slopePct.toFixed(0)}%) slope · ${terrain.aspect} (${terrain.aspectDeg.toFixed(0)}°) aspect`],
      ['Historical fire', byKey.fire.error ? `Unavailable: ${byKey.fire.error}` : summarizeService(byKey.fire)],
      ['Fire hazard zones', byKey.fhz.error ? `Unavailable: ${byKey.fhz.error}` : summarizeService(byKey.fhz)],
      ['State responsibility', byKey.sra.error ? `Unavailable: ${byKey.sra.error}` : summarizeService(byKey.sra)],
      ['Watersheds', byKey.watershed.error ? `Unavailable: ${byKey.watershed.error}` : summarizeService(byKey.watershed)]
    ];

    $('results').innerHTML = rows.map(([k,v]) => `<div class="result-row"><span>${escapeHtml(k)}</span><strong>${escapeHtml(v)}</strong></div>`).join('') +
      '<div class="proof-note">All values above were calculated in your browser or requested live from the listed public agencies. Failed services are shown as unavailable rather than replaced with invented data.</div>';

    lastAnalysis={ generated:new Date().toISOString(), acres, perimeter, terrain, services:Object.fromEntries(serviceResults.map(r => [r.key,{label:r.cfg.label,summary:r.error?`Unavailable: ${r.error}`:summarizeService(r)}])) };
    $('exportBtn').disabled=false;
    status('Live analysis complete. Environmental intersections are highlighted on the map.', 'ok');
    $('analyzeBtn').disabled=false;
  }

  function exportReport() {
    if(!lastAnalysis) return;
    const lines=[
      'Terrain Environmental GIS — Proof Demo',
      `Generated: ${new Date(lastAnalysis.generated).toLocaleString()}`,
      '',
      `Area: ${lastAnalysis.acres.toFixed(2)} acres`,
      `Perimeter: ${lastAnalysis.perimeter.toFixed(2)} miles`,
      lastAnalysis.terrain.error ? `Terrain: Unavailable (${lastAnalysis.terrain.error})` : `Terrain: ${lastAnalysis.terrain.elevationFt.toFixed(0)} ft elevation; ${lastAnalysis.terrain.slopeDeg.toFixed(1)}° / ${lastAnalysis.terrain.slopePct.toFixed(0)}% slope; ${lastAnalysis.terrain.aspect} ${lastAnalysis.terrain.aspectDeg.toFixed(0)}° aspect`,
      '',
      ...Object.values(lastAnalysis.services).map(x => `${x.label}: ${x.summary}`),
      '',
      'Sources: USGS The National Map / Elevation Point Query Service; CAL FIRE / OSFM public GIS services.',
      'Demo AOI is illustrative and is not an official property or incident boundary.'
    ];
    const blob=new Blob([lines.join('\n')],{type:'text/plain'});
    const a=document.createElement('a');
    a.href=URL.createObjectURL(blob);a.download='terrain-gis-proof-demo.txt';a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  }

  map.on('pm:create',e => {
    project.addLayer(e.layer);
    updateQuickMetrics();
    status('Custom polygon added. Press Analyze live data to prove the workflow on it.', 'ok');
  });
  map.on('pm:edit',updateQuickMetrics);
  map.on('pm:remove',updateQuickMetrics);

  $('loadBtn').addEventListener('click',loadSample);
  $('analyzeBtn').addEventListener('click',analyze);
  $('exportBtn').addEventListener('click',exportReport);
  $('backBtn').addEventListener('click',() => { window.location.href='./'; });

  loadSample();
})();
