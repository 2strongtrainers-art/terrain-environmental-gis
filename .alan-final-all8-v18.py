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

# More organic foreground terrain using vertex color variation instead of one flat green plane.
once("const groundMat=new THREE.MeshStandardMaterial({color:0x78866d,roughness:.96,metalness:0,map:groundTex,bumpMap:groundTex,bumpScale:.07});","const groundMat=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.96,metalness:0,map:groundTex,bumpMap:groundTex,bumpScale:.055,vertexColors:true});",'ground vertex-color material')
old_gp="const gp=groundGeo.attributes.position;for(let i=0;i<gp.count;i++){const x=gp.getX(i),z=gp.getZ(i);gp.setY(i,groundHeightAt(x,z)-.08);}groundGeo.computeVertexNormals();"
new_gp="""const gp=groundGeo.attributes.position,gc=[];const cShore=new THREE.Color(0x8d805b),cMeadow=new THREE.Color(0x667050),cForest=new THREE.Color(0x46553e);
  for(let i=0;i<gp.count;i++){const x=gp.getX(i),z=gp.getZ(i),r=Math.hypot(x,z);gp.setY(i,groundHeightAt(x,z)-.08);const n=.5+.5*Math.sin(x*.075+Math.sin(z*.047)*1.8);const c=(r<49?cShore.clone().lerp(cMeadow,THREE.MathUtils.clamp((r-43)/6,0,1)):cMeadow.clone().lerp(cForest,.22+n*.38));gc.push(c.r,c.g,c.b);}groundGeo.setAttribute('color',new THREE.Float32BufferAttribute(gc,3));groundGeo.computeVertexNormals();"""
once(old_gp,new_gp,'natural ground color variation')

# Broader, calmer mountain shoulders to remove the remaining pointed-cone look.
once("const seg=state.mobile?14:20,rings=6,verts=[],idx=[];\n    for(let j=0;j<=rings;j++){const t=j/rings,rr=rad*Math.pow(1-t,.72);const cy=-h*.5+t*h;for(let i=0;i<seg;i++){const a=i/seg*Math.PI*2;const wob=1+Math.sin(a*3.1+j*.7)*.11+Math.sin(a*7.3-j*.45)*.055;","const seg=state.mobile?14:20,rings=6,verts=[],idx=[];\n    for(let j=0;j<=rings;j++){const t=j/rings,rr=rad*Math.pow(1-t,.58);const cy=-h*.5+t*h;for(let i=0;i<seg;i++){const a=i/seg*Math.PI*2;const wob=1+Math.sin(a*3.1+j*.7)*.075+Math.sin(a*7.3-j*.45)*.035;",'broader mountain profile')

# Mark half of shoreline rocks as optional detail so they can be hidden only during heavy action.
old_rock="m.scale.set(rand(.35,1.55),rand(.25,1.08),rand(.38,1.65));m.position.set(Math.cos(a)*r,rand(-.06,.22),Math.sin(a)*r);m.rotation.set(rand(0,2.5),rand(0,6.28),rand(0,2.5));m.castShadow=!state.mobile&&i%3===0;scene.add(m);"
new_rock="m.scale.set(rand(.35,1.55),rand(.25,1.08),rand(.38,1.65));m.position.set(Math.cos(a)*r,rand(-.06,.22),Math.sin(a)*r);m.rotation.set(rand(0,2.5),rand(0,6.28),rand(0,2.5));m.castShadow=!state.mobile&&i%3===0;m.name=i%2?'action-cull-rock':'shore-rock';scene.add(m);"
once(old_rock,new_rock,'action-cull shoreline rocks')

# Make Alan read larger and cleaner in third person; reduce oversized landing-net ring.
once("const baseDistance=state.inBoat?6.7:(state.fishing==='LANDING'?4.4:5.45),height=state.inBoat?3.15:2.72;","const baseDistance=state.inBoat?6.45:(state.fishing==='LANDING'?4.05:4.82),height=state.inBoat?3.05:2.66;",'closer third-person framing')
once("const netRing=new THREE.Mesh(new THREE.TorusGeometry(.18,.022,7,22),gearDark);","const netRing=new THREE.Mesh(new THREE.TorusGeometry(.14,.018,7,20),gearDark);",'smaller fishing net')

# Correct the adaptive resolution race: action mode now owns the pixel ratio until the action ends.
old_dyn="""function updateDynamicResolution(){
  if(!renderer||!state.mobile)return;
  const mode=(state.fishing==='REEL'||state.fishing==='LANDING')?'action':'normal';if(mode===renderScaleMode)return;renderScaleMode=mode;
  const cap=mode==='action'?.85:1.25;renderer.setPixelRatio(Math.min(devicePixelRatio,cap));renderer.setSize(innerWidth,innerHeight,false);
}"""
new_dyn="""function updateDynamicResolution(){
  if(!renderer||!state.mobile)return;
  const mode=(state.fishing==='REEL'||state.fishing==='LANDING')?'action':'normal';const cap=mode==='action'?.72:1.18;const target=Math.min(devicePixelRatio,cap);
  const changed=mode!==renderScaleMode||Math.abs(renderer.getPixelRatio()-target)>.015;if(!changed)return;renderScaleMode=mode;renderer.setPixelRatio(target);renderer.setSize(innerWidth,innerHeight,false);
  const action=mode==='action';if(mistGroup)mistGroup.visible=!action&&state.quality!=='LOW';if(cloudGroup)cloudGroup.visible=!action;if(shoreGrass)shoreGrass.visible=!action;if(boatWake)boatWake.visible=!action;
  scene?.children.forEach(o=>{if(o.name==='action-cull-rock'||o.name==='bird')o.visible=!action;});
}"""
once(old_dyn,new_dyn,'stable action resolution and transient culling')

# Prevent AUTO quality from overriding the temporary action pixel ratio.
once("if(state.quality==='AUTO'&&state.frameTier==='low')applyQuality();","if(state.quality==='AUTO'&&state.frameTier==='low'&&state.fishing!=='REEL'&&state.fishing!=='LANDING')applyQuality();",'protect action render scale')

# Keep resize/quality coherent with the new normal mobile target.
once("else ratio=Math.min(devicePixelRatio,state.frameTier==='low'?1:state.frameTier==='medium'?(state.mobile?1.22:1.55):state.mobile?1.42:1.85);","else ratio=Math.min(devicePixelRatio,state.frameTier==='low'?.9:state.frameTier==='medium'?(state.mobile?1.08:1.55):state.mobile?1.18:1.85);",'auto quality mobile targets')

if '/* FINAL_ALL8_V18 */' not in s:
    s=s.replace('/* VISUAL_PERF_V17 */','/* VISUAL_PERF_V17 */\n/* FINAL_ALL8_V18 */',1)

p.write_text(s,encoding='utf-8')
print('final all-8 v18 patch complete',len(s))
