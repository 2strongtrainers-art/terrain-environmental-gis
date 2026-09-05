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

# Dedicated heavy-action renderer benchmark. It exercises the actual LANDING render path,
# fish mesh, chase camera, rod line, action culling and mobile pixel ratio without screenshots.
anchor="""function canWebGL() {
  try {"""
bench="""async function benchmarkActionRender(ms=1200){
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
}
function canWebGL() {
  try {"""
once(anchor,bench,'action render benchmark')

old="""window.__ALAN_GAME__={release:RELEASE_ID,audit:()=>({release:RELEASE_ID,avatar:!!avatar,premiumAvatar:!!premiumAvatar,fisherGear:!!premiumAvatar?.getObjectByName('fisher-pack'),rodAttached:rodGroup?.parent===avatarRodAnchor,thirdPerson:camera.position.z>2,lure:state.lure,zone:state.lastZone,score:state.score,catches:state.catches.length,quality:state.quality,fps:state.fps,fishing:state.fishing,landingT:catchAnim?.t||0,fishVisible:!!catchFishVisual?.visible,pixelRatio:renderer?.getPixelRatio?.()||0,anglerDetail:!!premiumAvatar?.getObjectByName('angler-detail'),taperedHull:!!boat?.getObjectByName('tapered-fishing-hull'),naturalRidge:!!visualExtras?.getObjectByName('natural-ridgeline')}),forceLanding:()=>{if(state.fishing==='LANDING')return true;state.hookedFish={...fishSpecies[0],name:'Rainbow Trout',weight:3.2,power:.62,seed:1.1,zone:'SHORE',lure:state.lure};bobber.position.set(0,.1,42);landFish();return true;}};"""
new="""window.__ALAN_GAME__={release:RELEASE_ID,audit:()=>({release:RELEASE_ID,avatar:!!avatar,premiumAvatar:!!premiumAvatar,fisherGear:!!premiumAvatar?.getObjectByName('fisher-pack'),rodAttached:rodGroup?.parent===avatarRodAnchor,thirdPerson:camera.position.z>2,lure:state.lure,zone:state.lastZone,score:state.score,catches:state.catches.length,quality:state.quality,fps:state.fps,fishing:state.fishing,landingT:catchAnim?.t||0,fishVisible:!!catchFishVisual?.visible,pixelRatio:renderer?.getPixelRatio?.()||0,anglerDetail:!!premiumAvatar?.getObjectByName('angler-detail'),taperedHull:!!boat?.getObjectByName('tapered-fishing-hull'),naturalRidge:!!visualExtras?.getObjectByName('natural-ridgeline')}),benchmarkAction:benchmarkActionRender,forceLanding:()=>{if(state.fishing==='LANDING')return true;state.hookedFish={...fishSpecies[0],name:'Rainbow Trout',weight:3.2,power:.62,seed:1.1,zone:'SHORE',lure:state.lure};bobber.position.set(0,.1,42);landFish();return true;}};"""
once(old,new,'benchmark API exposure')

if '/* ACTION_BENCHMARK_V19 */' not in s:
    s=s.replace('/* FINAL_ALL8_V18 */','/* FINAL_ALL8_V18 */\n/* ACTION_BENCHMARK_V19 */',1)

p.write_text(s,encoding='utf-8')
print('action benchmark v19 patch complete',len(s))
