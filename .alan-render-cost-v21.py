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

old="""async function benchmarkActionRender(ms=900){
  if(!renderer||!state.mobile)return {baselineFps:state.fps,actionFps:state.fps,ratio:1,pixelRatio:renderer?.getPixelRatio?.()||0};
  const prevFishing=state.fishing,prevHooked=state.hookedFish,prevAction=state.actionHeld;
  const sample=async animate=>{const start=performance.now();let frames=0;await new Promise(resolve=>{const tick=t=>{frames++;if(animate&&catchFishVisual){catchFishVisual.rotation.y+=.018;catchFishVisual.rotation.z=.35+Math.sin(t*.006)*.18;}if(t-start>=ms)resolve();else requestAnimationFrame(tick);};requestAnimationFrame(tick);});const elapsed=Math.max(1,performance.now()-start);return {fps:frames/(elapsed/1000),frames,elapsed};};
  state.fishing='IDLE';state.actionHeld=false;updateDynamicResolution();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const normal=await sample(false);
  const benchFish={...fishSpecies[0],name:'Rainbow Trout',weight:3.2,power:.62,seed:1.1,zone:'SHORE',lure:state.lure};state.hookedFish=benchFish;state.fishing='LANDING';
  let created=false;if(!catchFishVisual){const f=createCatchFish(benchFish);f.position.set(0,1.15,34);f.rotation.set(.08,.2,.4);created=true;}updateDynamicResolution();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const actionPixelRatio=renderer.getPixelRatio(),action=await sample(true);
  if(created&&catchFishVisual){scene.remove(catchFishVisual);catchFishVisual=null;}state.fishing=prevFishing;state.hookedFish=prevHooked;state.actionHeld=prevAction;updateDynamicResolution();
  const rel=normal.fps>0?action.fps/normal.fps:0;return {baselineFps:+normal.fps.toFixed(1),actionFps:+action.fps.toFixed(1),ratio:+rel.toFixed(2),pixelRatio:+actionPixelRatio.toFixed(2),baselineFrames:normal.frames,actionFrames:action.frames};
}"""
new="""function benchmarkActionRender(iterations=10){
  if(!renderer||!state.mobile)return {baselineMs:0,actionMs:0,costRatio:1,pixelRatio:renderer?.getPixelRatio?.()||0};
  iterations=Math.max(4,Math.min(20,Math.round(iterations)||10));const gl=renderer.getContext();
  const prevFishing=state.fishing,prevHooked=state.hookedFish,prevAction=state.actionHeld;
  const sample=()=>{renderer.render(scene,camera);gl.finish();const start=performance.now();for(let i=0;i<iterations;i++){renderer.render(scene,camera);gl.finish();}const elapsed=Math.max(.01,performance.now()-start);return elapsed/iterations;};
  state.fishing='IDLE';state.actionHeld=false;updateDynamicResolution();const baselineMs=sample();
  const benchFish={...fishSpecies[0],name:'Rainbow Trout',weight:3.2,power:.62,seed:1.1,zone:'SHORE',lure:state.lure};state.hookedFish=benchFish;state.fishing='LANDING';let created=false;if(!catchFishVisual){const f=createCatchFish(benchFish);f.position.set(0,1.15,34);f.rotation.set(.08,.2,.4);created=true;}updateDynamicResolution();const actionPixelRatio=renderer.getPixelRatio(),actionMs=sample();
  if(created&&catchFishVisual){scene.remove(catchFishVisual);catchFishVisual=null;}state.fishing=prevFishing;state.hookedFish=prevHooked;state.actionHeld=prevAction;updateDynamicResolution();
  return {baselineMs:+baselineMs.toFixed(2),actionMs:+actionMs.toFixed(2),costRatio:+(actionMs/baselineMs).toFixed(2),pixelRatio:+actionPixelRatio.toFixed(2),baselineEquivalentFps:+(1000/baselineMs).toFixed(1),actionEquivalentFps:+(1000/actionMs).toFixed(1)};
}"""
once(old,new,'deterministic render-cost benchmark')

if '/* RENDER_COST_V21 */' not in s:
    s=s.replace('/* MOBILE_ACTION_V20 */','/* MOBILE_ACTION_V20 */\n/* RENDER_COST_V21 */',1)

p.write_text(s,encoding='utf-8')
print('render cost v21 patch complete',len(s))
