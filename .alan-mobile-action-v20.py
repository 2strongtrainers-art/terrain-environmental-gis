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

# Cull every individually drawn shoreline rock during the two-second REEL/LANDING action window.
once("if(o.name==='action-cull-rock'||o.name==='bird')o.visible=!action;","if(o.name==='action-cull-rock'||o.name==='shore-rock'||o.name==='bird')o.visible=!action;",'full shoreline rock action cull')

# Mobile landing fish: keep silhouette, belly, tail and eyes; drop small fins/highlights/spots that add draw calls.
old_loop="""  for(const side of [-1,1]){const pectoral=new THREE.Mesh(new THREE.ConeGeometry(.13,.48,8),finMat);pectoral.rotation.z=-Math.PI/2;pectoral.rotation.x=side*.55;pectoral.position.set(.1,-.05,.36*side);g.add(pectoral);const eye=new THREE.Mesh(new THREE.SphereGeometry(.06,10,8),new THREE.MeshBasicMaterial({color:0x080909}));eye.position.set(.5,.17,.245*side);g.add(eye);const shine=new THREE.Mesh(new THREE.SphereGeometry(.018,6,4),new THREE.MeshBasicMaterial({color:0xffffff}));shine.position.set(.525,.19,.287*side);g.add(shine);}
  const dorsal=new THREE.Mesh(new THREE.ConeGeometry(.16,.62,8),finMat);dorsal.rotation.z=-Math.PI/2;dorsal.position.set(-.12,.36,0);g.add(dorsal);const mouth=new THREE.Mesh(new THREE.TorusGeometry(.07,.012,5,12,Math.PI),new THREE.MeshBasicMaterial({color:0x4d3934}));mouth.position.set(.61,-.02,0);mouth.rotation.y=Math.PI/2;g.add(mouth);
  const spotMat=new THREE.MeshBasicMaterial({color:0x343d34,transparent:true,opacity:.5});for(let i=0;i<(state.mobile?4:8);i++){for(const side of [-1,1]){const sp=new THREE.Mesh(new THREE.SphereGeometry(.025+Math.random()*.018,6,4),spotMat);sp.position.set(rand(-.48,.28),rand(-.04,.24),.27*side);g.add(sp);}}"""
new_loop="""  for(const side of [-1,1]){if(!state.mobile){const pectoral=new THREE.Mesh(new THREE.ConeGeometry(.13,.48,8),finMat);pectoral.rotation.z=-Math.PI/2;pectoral.rotation.x=side*.55;pectoral.position.set(.1,-.05,.36*side);g.add(pectoral);}const eye=new THREE.Mesh(new THREE.SphereGeometry(.055,state.mobile?6:10,state.mobile?4:8),new THREE.MeshBasicMaterial({color:0x080909}));eye.position.set(.5,.17,.245*side);g.add(eye);if(!state.mobile){const shine=new THREE.Mesh(new THREE.SphereGeometry(.018,6,4),new THREE.MeshBasicMaterial({color:0xffffff}));shine.position.set(.525,.19,.287*side);g.add(shine);}}
  if(!state.mobile){const dorsal=new THREE.Mesh(new THREE.ConeGeometry(.16,.62,8),finMat);dorsal.rotation.z=-Math.PI/2;dorsal.position.set(-.12,.36,0);g.add(dorsal);const mouth=new THREE.Mesh(new THREE.TorusGeometry(.07,.012,5,12,Math.PI),new THREE.MeshBasicMaterial({color:0x4d3934}));mouth.position.set(.61,-.02,0);mouth.rotation.y=Math.PI/2;g.add(mouth);const spotMat=new THREE.MeshBasicMaterial({color:0x343d34,transparent:true,opacity:.5});for(let i=0;i<8;i++){for(const side of [-1,1]){const sp=new THREE.Mesh(new THREE.SphereGeometry(.025+Math.random()*.018,6,4),spotMat);sp.position.set(rand(-.48,.28),rand(-.04,.24),.27*side);g.add(sp);}}}"""
once(old_loop,new_loop,'mobile fish draw-call reduction')
once("new THREE.SphereGeometry(.62,state.mobile?16:22,state.mobile?10:14)","new THREE.SphereGeometry(.62,state.mobile?12:22,state.mobile?8:14)",'mobile fish body segments')
once("new THREE.SphereGeometry(.55,state.mobile?14:18,state.mobile?8:10)","new THREE.SphereGeometry(.55,state.mobile?10:18,state.mobile?6:10)",'mobile fish belly segments')

# Compare normal and action cadence with the same requestAnimationFrame sampling method.
old_bench="""async function benchmarkActionRender(ms=1200){
  if(!renderer||!state.mobile)return {fps:state.fps,pixelRatio:renderer?.getPixelRatio?.()||0,frames:0,elapsed:0};
  const prevFishing=state.fishing,prevHooked=state.hookedFish,prevAction=state.actionHeld,prevFish=catchFishVisual;
  const benchFish={...fishSpecies[0],name:'Rainbow Trout',weight:3.2,power:.62,seed:1.1,zone:'SHORE',lure:state.lure};
  state.hookedFish=benchFish;state.fishing='LANDING';state.actionHeld=false;
  let created=false;
  if(!catchFishVisual){const f=createCatchFish(benchFish);f.position.set(0,1.15,34);f.rotation.set(.08,.2,.4);created=true;}
  updateDynamicResolution();
  const start=performance.now();let frames=0;
  await new Promise(resolve=>{const tick=t=>{frames++;if(catchFishVisual){catchFishVisual.rotation.y+=.018;catchFishVisual.rotation.z=.35+Math.sin(t*.006)*.18;}if(t-start>=ms)resolve();else requestAnimationFrame(tick);};requestAnimationFrame(tick);});
  const elapsed=Math.max(1,performance.now()-start),ratio=renderer.getPixelRatio(),fps=frames/(elapsed/1000);
  if(created&&catchFishVisual){scene.remove(catchFishVisual);catchFishVisual=null;}
  state.fishing=prevFishing;state.hookedFish=prevHooked;state.actionHeld=prevAction;
  updateDynamicResolution();
  return {fps:+fps.toFixed(1),pixelRatio:+ratio.toFixed(2),frames,elapsed:Math.round(elapsed)};
}"""
new_bench="""async function benchmarkActionRender(ms=900){
  if(!renderer||!state.mobile)return {baselineFps:state.fps,actionFps:state.fps,ratio:1,pixelRatio:renderer?.getPixelRatio?.()||0};
  const prevFishing=state.fishing,prevHooked=state.hookedFish,prevAction=state.actionHeld;
  const sample=async animate=>{const start=performance.now();let frames=0;await new Promise(resolve=>{const tick=t=>{frames++;if(animate&&catchFishVisual){catchFishVisual.rotation.y+=.018;catchFishVisual.rotation.z=.35+Math.sin(t*.006)*.18;}if(t-start>=ms)resolve();else requestAnimationFrame(tick);};requestAnimationFrame(tick);});const elapsed=Math.max(1,performance.now()-start);return {fps:frames/(elapsed/1000),frames,elapsed};};
  state.fishing='IDLE';state.actionHeld=false;updateDynamicResolution();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const normal=await sample(false);
  const benchFish={...fishSpecies[0],name:'Rainbow Trout',weight:3.2,power:.62,seed:1.1,zone:'SHORE',lure:state.lure};state.hookedFish=benchFish;state.fishing='LANDING';
  let created=false;if(!catchFishVisual){const f=createCatchFish(benchFish);f.position.set(0,1.15,34);f.rotation.set(.08,.2,.4);created=true;}updateDynamicResolution();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const actionPixelRatio=renderer.getPixelRatio(),action=await sample(true);
  if(created&&catchFishVisual){scene.remove(catchFishVisual);catchFishVisual=null;}state.fishing=prevFishing;state.hookedFish=prevHooked;state.actionHeld=prevAction;updateDynamicResolution();
  const rel=normal.fps>0?action.fps/normal.fps:0;return {baselineFps:+normal.fps.toFixed(1),actionFps:+action.fps.toFixed(1),ratio:+rel.toFixed(2),pixelRatio:+actionPixelRatio.toFixed(2),baselineFrames:normal.frames,actionFrames:action.frames};
}"""
once(old_bench,new_bench,'relative action benchmark')

if '/* MOBILE_ACTION_V20 */' not in s:
    s=s.replace('/* ACTION_BENCHMARK_V19 */','/* ACTION_BENCHMARK_V19 */\n/* MOBILE_ACTION_V20 */',1)

p.write_text(s,encoding='utf-8')
print('mobile action v20 patch complete',len(s))
