from pathlib import Path

p=Path('alan-fishing-escape/index.html')
s=p.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    if new in s:
        print(label,'already present'); return
    if old not in s:
        raise SystemExit('Missing signature for '+label)
    s=s.replace(old,new,1); print('patched',label)

# 1) Natural shoreline: replace mathematically perfect rings with deterministic irregular geometry.
anchor="function angleLerp(a,b,t){let d=((b-a+Math.PI)%(Math.PI*2))-Math.PI;return a+d*t;}"
helper="""function makeIrregularRing(inner,outer,segments=128,phase=0){
  const v=[],uv=[],idx=[];
  for(let i=0;i<segments;i++){
    const a=i/segments*Math.PI*2;
    const n1=Math.sin(a*3.0+phase)*.42+Math.sin(a*7.0-phase*.7)*.18+Math.sin(a*13.0+phase*.4)*.08;
    const n2=Math.sin(a*2.0+phase*.6)*.68+Math.sin(a*5.0-phase)*.24+Math.sin(a*11.0+phase)*.10;
    const ri=inner+n1,ro=outer+n2;
    v.push(Math.cos(a)*ri,Math.sin(a)*ri,0,Math.cos(a)*ro,Math.sin(a)*ro,0);
    uv.push(0,i/segments,1,i/segments);
  }
  for(let i=0;i<segments;i++){const n=(i+1)%segments,a=i*2,b=a+1,c=n*2,d=c+1;idx.push(a,c,b,b,c,d);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(idx);g.computeVertexNormals();return g;
}
function angleLerp(a,b,t){let d=((b-a+Math.PI)%(Math.PI*2))-Math.PI;return a+d*t;}"""
once(anchor,helper,'irregular shoreline helper')
once("new THREE.RingGeometry(39.4,41.6,144)","makeIrregularRing(39.25,41.75,state.mobile?112:160,.7)",'wet shoreline shape')
once("new THREE.RingGeometry(41.4,45.5,144)","makeIrregularRing(41.35,45.9,state.mobile?112:160,1.9)",'dry shoreline shape')

# 2) Continuous layered ridgelines soften the old isolated mountain-cone silhouette.
ridge_anchor="""  const mistShader=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,fog:false,"""
ridge_block="""  function addRidge(z,baseY,amp,step,color,phase){
    const verts=[],idx=[],count=Math.floor(320/step)+1;
    for(let i=0;i<count;i++){
      const x=-160+i*step;
      const y=baseY+Math.sin(i*.48+phase)*amp*.34+Math.sin(i*.19-phase)*amp*.42+Math.abs(Math.sin(i*.11+phase))*amp*.55;
      const zz=z+Math.sin(i*.23+phase)*2.8;
      verts.push(x,-6,zz,x,y,zz);
    }
    for(let i=0;i<count-1;i++){const a=i*2,b=a+1,c=a+2,d=a+3;idx.push(a,c,b,b,c,d);}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));g.setIndex(idx);g.computeVertexNormals();
    const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color,roughness:1,metalness:0,side:THREE.DoubleSide}));m.name='natural-ridgeline';visualExtras.add(m);
  }
  addRidge(-104,12,22,state.mobile?11:8,0x4d6259,.8);
  addRidge(-142,17,28,state.mobile?13:9,0x66776f,2.1);

  const mistShader=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,fog:false,"""
once(ridge_anchor,ridge_block,'natural layered ridgelines')

# 3) Boat hull: use tapered multi-section geometry rather than a rectangular box as the main silhouette.
boat_anchor="function buildBoat(){"
boat_helper="""function makeBoatHullGeometry(){
  const sections=[[-3.95,.12],[-3.15,.86],[-1.45,1.34],[1.45,1.38],[3.05,1.18]],verts=[],idx=[];
  for(const [z,w] of sections){verts.push(-w,.34,z,w,.34,z,-w*.82,-.34,z,w*.82,-.34,z);}
  for(let i=0;i<sections.length-1;i++){
    const a=i*4,b=a+4;
    idx.push(a,b,a+1,a+1,b,b+1);          // deck
    idx.push(a+2,a+3,b+2,a+3,b+3,b+2);    // keel
    idx.push(a,a+2,b,a+2,b+2,b);          // port
    idx.push(a+1,b+1,a+3,a+3,b+1,b+3);    // starboard
  }
  idx.push(0,1,2,1,3,2);const e=(sections.length-1)*4;idx.push(e,e+2,e+1,e+1,e+2,e+3);
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));g.setIndex(idx);g.computeVertexNormals();return g;
}
function buildBoat(){"""
once(boat_anchor,boat_helper,'tapered boat hull helper')
once("boatBody=new THREE.Mesh(new THREE.BoxGeometry(2.8,.48,5.8),hullMat);boatBody.position.y=.22;boat.add(boatBody);const lower=new THREE.Mesh(new THREE.BoxGeometry(2.42,.38,5.55),lowerMat);lower.position.y=-.08;boat.add(lower);","boatBody=new THREE.Mesh(makeBoatHullGeometry(),hullMat);boatBody.position.y=.28;boat.add(boatBody);const lower=new THREE.Mesh(makeBoatHullGeometry(),lowerMat);lower.scale.set(.91,.72,.96);lower.position.y=-.17;boat.add(lower);boatBody.name='tapered-fishing-hull';",'boat silhouette')
once("bow.position.set(0,.19,-4.1);boat.add(bow);","bow.position.set(0,.19,-4.1);bow.visible=false;boat.add(bow);",'hide obsolete cone bow')

# 4) Angler detail: add visible straps, tackle pouches, net handle and warmer outdoor material treatment.
mat_old="o.material=o.material.clone();o.material.roughness=Math.max(.52,o.material.roughness??.7);o.material.metalness=Math.min(.08,o.material.metalness??0);"
mat_new="o.material=o.material.clone();o.material.roughness=Math.max(.58,o.material.roughness??.7);o.material.metalness=Math.min(.05,o.material.metalness??0);if(o.material.color)o.material.color.lerp(new THREE.Color(0x50604d),.16);"
once(mat_old,mat_new,'angler outdoor material treatment')
gear_anchor="""      const packFlap=new THREE.Mesh(new THREE.BoxGeometry(.43,.18,.055),gearDark);packFlap.position.set(0,1.31,.35);model.add(packFlap);"""
gear_block="""      const packFlap=new THREE.Mesh(new THREE.BoxGeometry(.43,.18,.055),gearDark);packFlap.position.set(0,1.31,.35);model.add(packFlap);
      const strapMat=new THREE.MeshStandardMaterial({color:0x223a31,roughness:.94});
      for(const x of [-.17,.17]){const strap=new THREE.Mesh(new THREE.BoxGeometry(.065,.72,.035),strapMat);strap.position.set(x,1.30,.29);strap.rotation.z=x<0?-.08:.08;model.add(strap);}
      for(const x of [-.29,.29]){const pouch=new THREE.Mesh(new THREE.BoxGeometry(.19,.23,.13),gearMat);pouch.position.set(x,1.02,.27);pouch.rotation.z=x<0?.08:-.08;model.add(pouch);}
      const netHandle=new THREE.Mesh(new THREE.CylinderGeometry(.018,.024,.78,7),gearDark);netHandle.position.set(.31,.72,.33);netHandle.rotation.z=-.18;model.add(netHandle);
      const vestPanel=new THREE.Mesh(new THREE.BoxGeometry(.48,.44,.055),new THREE.MeshStandardMaterial({color:0x55664a,roughness:.95}));vestPanel.name='angler-detail';vestPanel.position.set(0,1.34,-.19);model.add(vestPanel);"""
once(gear_anchor,gear_block,'premium angler gear detail')

# 5) Heavy-action performance: lower normal mobile DPR slightly and temporarily drop resolution during reel/landing.
once("renderer.setPixelRatio(Math.min(devicePixelRatio, state.mobile ? 1.45 : 1.8));","renderer.setPixelRatio(Math.min(devicePixelRatio, state.mobile ? 1.25 : 1.8));",'mobile base DPR')
once("let toastTimer = 0, saveTimer = 0;","let toastTimer = 0, saveTimer = 0, renderScaleMode = 'normal';",'render scale state')
update_game_anchor="""function updateGame(dt){
  const k=input.keys;"""
update_game_new="""function updateDynamicResolution(){
  if(!renderer||!state.mobile)return;
  const mode=(state.fishing==='REEL'||state.fishing==='LANDING')?'action':'normal';if(mode===renderScaleMode)return;renderScaleMode=mode;
  const cap=mode==='action'?.85:1.25;renderer.setPixelRatio(Math.min(devicePixelRatio,cap));renderer.setSize(innerWidth,innerHeight,false);
}
function updateGame(dt){
  updateDynamicResolution();
  const k=input.keys;"""
once(update_game_anchor,update_game_new,'dynamic heavy-action resolution')

# 6) Audit hooks for the new release qualities.
audit_old="fishVisible:!!catchFishVisual?.visible})"
audit_new="fishVisible:!!catchFishVisual?.visible,pixelRatio:renderer?.getPixelRatio?.()||0,anglerDetail:!!premiumAvatar?.getObjectByName('angler-detail'),taperedHull:!!boat?.getObjectByName('tapered-fishing-hull'),naturalRidge:!!visualExtras?.getObjectByName('natural-ridgeline')})"
once(audit_old,audit_new,'v17 runtime audit hooks')

if '/* VISUAL_PERF_V17 */' not in s:
    s=s.replace('/* TACKLE_HUD_V13 */','/* TACKLE_HUD_V13 */\n/* VISUAL_PERF_V17 */',1)

p.write_text(s,encoding='utf-8')
print('visual/performance v17 patch complete',len(s))
