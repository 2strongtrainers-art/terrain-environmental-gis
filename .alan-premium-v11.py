from pathlib import Path

p=Path('alan-fishing-escape/index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    if new in s:
        print(label,'already present'); return
    if old not in s:
        raise SystemExit('Missing signature: '+label)
    s=s.replace(old,new,1); print('patched',label)

rep(
"import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.185.1/build/three.module.min.js';",
"import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.185.1/build/three.module.min.js';\nimport { GLTFLoader } from 'https://esm.sh/three@0.185.1/examples/jsm/loaders/GLTFLoader.js';",
'GLTF loader')

rep(
"let avatar=null, avatarTorso=null, avatarHead=null, avatarLeftArm=null, avatarRightArm=null, avatarLeftLeg=null, avatarRightLeg=null, avatarRodAnchor=null;",
"let avatar=null, avatarTorso=null, avatarHead=null, avatarLeftArm=null, avatarRightArm=null, avatarLeftLeg=null, avatarRightLeg=null, avatarRodAnchor=null;\nlet premiumAvatar=null,premiumMixer=null,premiumActions={},premiumAction='';",
'premium avatar globals')

rep(
"buildLights(); buildWorld(); buildDock(); buildBoat(); buildAvatar(); buildRod(); buildRipples(); buildParty();",
"buildLights(); buildWorld(); buildDock(); buildBoat(); buildAvatar(); buildRod(); loadPremiumAvatar(); buildRipples(); buildParty();",
'premium avatar load')

old_api="window.__ALAN_GAME__={release:RELEASE_ID,audit:()=>({release:RELEASE_ID,avatar:!!avatar,rodAttached:rodGroup?.parent===avatarRodAnchor,thirdPerson:camera.position.z>2,lure:state.lure,zone:state.lastZone,score:state.score,catches:state.catches.length,quality:state.quality,fps:state.fps}),forceLanding:()=>{if(state.fishing==='LANDING')return false;state.hookedFish={...fishSpecies[0],name:'Rainbow Trout',weight:3.2,power:.62,seed:1.1,zone:'SHORE',lure:state.lure};bobber.position.set(0,.1,30);landFish();return true;}};"
new_api="window.__ALAN_GAME__={release:RELEASE_ID,audit:()=>({release:RELEASE_ID,avatar:!!avatar,premiumAvatar:!!premiumAvatar,rodAttached:rodGroup?.parent===avatarRodAnchor,thirdPerson:camera.position.z>2,lure:state.lure,zone:state.lastZone,score:state.score,catches:state.catches.length,quality:state.quality,fps:state.fps}),forceLanding:()=>{if(state.fishing==='LANDING')return true;state.hookedFish={...fishSpecies[0],name:'Rainbow Trout',weight:3.2,power:.62,seed:1.1,zone:'SHORE',lure:state.lure};bobber.position.set(0,.1,30);landFish();return true;}};"
if "premiumAvatar:!!premiumAvatar" in s:
    print('QA landing contract already present')
else:
    rep(old_api,new_api,'QA landing contract')

premium_fn=r'''function setPremiumAction(name){
  if(!premiumMixer||premiumAction===name||!premiumActions[name])return;
  const next=premiumActions[name],prev=premiumActions[premiumAction];
  next.reset().fadeIn(.18).play();if(prev)prev.fadeOut(.18);premiumAction=name;
}
function loadPremiumAvatar(){
  try{
    const loader=new GLTFLoader();
    loader.load('https://cdn.jsdelivr.net/gh/mrdoob/three.js@r185/examples/models/gltf/Soldier.glb',gltf=>{
      const model=gltf.scene;premiumAvatar=model;model.name='alan-premium-avatar';model.scale.setScalar(1.04);model.position.set(0,.02,0);
      model.traverse(o=>{if(o.isMesh){o.castShadow=!state.mobile;o.receiveShadow=true;if(o.material){o.material=o.material.clone();o.material.roughness=Math.max(.52,o.material.roughness??.7);o.material.metalness=Math.min(.08,o.material.metalness??0);}}});
      const isRodMesh=o=>{let q=o;while(q){if(q===rodGroup)return true;q=q.parent;}return false;};
      avatar.traverse(o=>{if(o.isMesh&&!isRodMesh(o))o.visible=false;});avatar.add(model);
      premiumMixer=new THREE.AnimationMixer(model);for(const clip of gltf.animations){premiumActions[clip.name]=premiumMixer.clipAction(clip);}setPremiumAction(premiumActions.Idle?'Idle':Object.keys(premiumActions)[0]);
      if(avatarRodAnchor){avatarRodAnchor.position.set(.39,1.26,-.32);avatarRodAnchor.rotation.set(-.22,.08,-.13);}
    },undefined,()=>{premiumAvatar=null;});
  }catch{premiumAvatar=null;}
}

'''
if "function setPremiumAction(name){" in s and "function loadPremiumAvatar(){" in s:
    print('premium avatar functions already present')
else:
    rep("function buildRod(){",premium_fn+"function buildRod(){",'premium avatar functions')

rep(
"function updateAvatar(dt){\n  if(!avatar)return;const moving=playerVelocity.lengthSq()>.08||Math.abs(input.x)+Math.abs(input.y)>.08;const fishing=['WAIT','REEL','LANDING','CAUGHT'].includes(state.fishing);",
"function updateAvatar(dt){\n  if(!avatar)return;const moving=playerVelocity.lengthSq()>.08||Math.abs(input.x)+Math.abs(input.y)>.08;const fishing=['WAIT','REEL','LANDING','CAUGHT'].includes(state.fishing);if(premiumMixer){premiumMixer.update(dt);const desired=fishing?'Idle':(moving?(input.run?'Run':'Walk'):'Idle');setPremiumAction(premiumActions[desired]?desired:(premiumActions.Idle?'Idle':Object.keys(premiumActions)[0]));}",
'premium avatar animation')

rep("renderer.toneMappingExposure = 1.27;","renderer.toneMappingExposure = 1.32;",'tone exposure')
rep("const hemi = new THREE.HemisphereLight(0xd8e4e7, 0x17271f, 1.35);","const hemi = new THREE.HemisphereLight(0xe1edf0, 0x26372c, 1.62);",'hemisphere light')
rep("const ambient = new THREE.AmbientLight(0xb3c0b6, .46);","const ambient = new THREE.AmbientLight(0xb6c2b7, .52);",'ambient light')
rep("const fill = new THREE.DirectionalLight(0x9fc5d7,.62);","const fill = new THREE.DirectionalLight(0xa4cbe0,.68);",'fill light')
rep("scene.fog = new THREE.FogExp2(0xaeb9ad, state.mobile ? 0.0072 : 0.0054);","scene.fog = new THREE.FogExp2(0xb8c1b5, state.mobile ? 0.0065 : 0.0049);",'fog tuning')
rep("const groundTex=makeNoiseTexture('#43503c','#25322a',128,state.mobile?700:1200);","const groundTex=makeNoiseTexture('#536249','#303c32',128,state.mobile?700:1200);",'ground texture')
rep("const groundMat=new THREE.MeshStandardMaterial({color:0x76856c,roughness:.98,metalness:0,map:groundTex,bumpMap:groundTex,bumpScale:.08});","const groundMat=new THREE.MeshStandardMaterial({color:0x78866d,roughness:.96,metalness:0,map:groundTex,bumpMap:groundTex,bumpScale:.07});",'ground material')
rep("const count=layer?16:13;","const count=layer?12:10;",'mountain count')
rep("const a=Math.PI*.96+(i/(count-1))*Math.PI*1.03+rand(-.035,.035),r=layer?rand(124,154):rand(92,123),h=layer?rand(34,62):rand(25,51),rad=layer?rand(17,30):rand(13,25);","const a=Math.PI*.96+(i/(count-1))*Math.PI*1.03+rand(-.05,.05),r=layer?rand(132,164):rand(96,128),h=layer?rand(30,49):rand(23,40),rad=layer?rand(30,46):rand(24,38);",'broader mountains')

css=r'''
/* PREMIUM_RELEASE_V11 */
@media (max-width:900px){
  .objectives{min-width:154px;padding:8px 9px;background:rgba(8,22,19,.59)}
  .obj{font-size:10px;line-height:1.45}.hud-label{font-size:8px}
  .status{width:min(270px,32vw);padding:7px 10px;background:rgba(8,22,19,.56)}
  #status-title{font-size:12px}#status-sub{font-size:9px}
  .joystick-base{opacity:.56!important;width:100px!important;height:100px!important}
  .joystick-knob{left:29px!important;top:29px!important;width:42px!important;height:42px!important}
  .action{width:66px!important;height:66px!important}.run,.interact{width:50px!important;height:50px!important;font-size:10px}
  .icon-btn{width:38px;height:38px}.log-btn{top:calc(max(10px,env(safe-area-inset-top)) + 44px)}
}
'''
if css.strip() in s:
    print('premium mobile CSS already present')
else:
    rep("</style>",css+"\n</style>",'premium mobile CSS')
if "/* PREMIUM_RELEASE_V11 */" not in s:
    rep("/* 8PLUS_RELEASE_V10 */","/* 8PLUS_RELEASE_V10 */\n/* PREMIUM_RELEASE_V11 */",'v11 marker')
else:
    print('v11 marker already present')

p.write_text(s,encoding='utf-8')
module=s.split('<script type="module">',1)[1].split('</script>',1)[0]
Path('/tmp/alan-game.mjs').write_text(module,encoding='utf-8')
print('premium v11 patch complete',len(s))