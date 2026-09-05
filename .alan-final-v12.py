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

# Make the premium humanoid read as a lake angler rather than a generic character.
old_add="avatar.traverse(o=>{if(o.isMesh&&!isRodMesh(o))o.visible=false;});avatar.add(model);\n      premiumMixer=new THREE.AnimationMixer(model);"
new_add="""avatar.traverse(o=>{if(o.isMesh&&!isRodMesh(o))o.visible=false;});avatar.add(model);
      const gearMat=new THREE.MeshStandardMaterial({color:0x776043,roughness:.9,metalness:0});
      const gearDark=new THREE.MeshStandardMaterial({color:0x30463a,roughness:.92,metalness:0});
      const fisherPack=new THREE.Mesh(new THREE.BoxGeometry(.52,.58,.16),gearMat);fisherPack.name='fisher-pack';fisherPack.position.set(0,1.14,.25);fisherPack.rotation.x=-.03;model.add(fisherPack);
      const packFlap=new THREE.Mesh(new THREE.BoxGeometry(.43,.18,.055),gearDark);packFlap.position.set(0,1.31,.35);model.add(packFlap);
      const netRing=new THREE.Mesh(new THREE.TorusGeometry(.18,.022,7,22),gearDark);netRing.position.set(.31,1.05,.35);netRing.rotation.y=.24;model.add(netRing);
      const capTop=new THREE.Mesh(new THREE.CylinderGeometry(.19,.23,.14,16),gearDark);capTop.position.set(0,1.79,0);model.add(capTop);
      const capBrim=new THREE.Mesh(new THREE.BoxGeometry(.34,.025,.18),gearDark);capBrim.position.set(0,1.75,-.16);model.add(capBrim);
      premiumMixer=new THREE.AnimationMixer(model);"""
once(old_add,new_add,'angler gear')

# Expose the angler gear in the runtime QA audit.
old_audit="premiumAvatar:!!premiumAvatar,rodAttached:rodGroup?.parent===avatarRodAnchor"
new_audit="premiumAvatar:!!premiumAvatar,fisherGear:!!premiumAvatar?.getObjectByName('fisher-pack'),rodAttached:rodGroup?.parent===avatarRodAnchor"
once(old_audit,new_audit,'angler gear audit')

# Expose the actual visible fish mesh, not just animation timing, for the final public QA.
if 'fishVisible:!!catchFishVisual?.visible' not in s:
    if 'landingT:catchAnim?.t||0})' in s:
        s=s.replace('landingT:catchAnim?.t||0})','landingT:catchAnim?.t||0,fishVisible:!!catchFishVisual?.visible})',1)
    elif 'quality:state.quality,fps:state.fps})' in s:
        s=s.replace('quality:state.quality,fps:state.fps})','quality:state.quality,fps:state.fps,fishVisible:!!catchFishVisual?.visible})',1)
    else:
        raise SystemExit('Missing runtime audit signature for fish visibility')
    print('patched fish visibility audit')

# Hard completion fallback in addition to the wall-clock animation timing.
old_anim="catchAnim={t:0,duration:1.75,start:fish.position.clone(),fish:f,recorded:false,startedAt:performance.now()};\n  showToast(`${f.name} coming out of the water!`,1500);updateActionLabel();"
new_anim="catchAnim={t:0,duration:1.75,start:fish.position.clone(),fish:f,recorded:false,startedAt:performance.now()};const landingRef=catchAnim;setTimeout(()=>{if(catchAnim===landingRef&&state.fishing==='LANDING')finishCatchLanding();},2100);\n  showToast(`${f.name} coming out of the water!`,1500);updateActionLabel();"
once(old_anim,new_anim,'landing completion safeguard')

# Lift lake color separation without adding expensive post-processing.
old_water="vec3 deep=vec3(.025,.145,.155); vec3 mid=vec3(.055,.235,.235); vec3 sky=vec3(.42,.58,.59);"
new_water="vec3 deep=vec3(.022,.16,.18); vec3 mid=vec3(.07,.285,.30); vec3 sky=vec3(.48,.66,.68);"
once(old_water,new_water,'water tonal lift')

# Keep HUD buttons above the transparent mobile look layer so real iPhone taps reach them.
if '/* HUD_TOUCH_PRIORITY_V15 */' not in s:
    s=s.replace('</style>',"\n/* HUD_TOUCH_PRIORITY_V15 */\n#hud{z-index:16!important}\n.icon-btn,.tackle-btn{pointer-events:auto!important}\n</style>",1)

if '/* FISH_VISUAL_GATE_V16 */' not in s:
    s=s.replace('/* HUD_TOUCH_PRIORITY_V15 */','/* HUD_TOUCH_PRIORITY_V15 */\n/* FISH_VISUAL_GATE_V16 */',1)

if 'FINAL_8PLUS_V12' not in s:
    s=s.replace('/* PREMIUM_RELEASE_V11 */','/* PREMIUM_RELEASE_V11 */\n/* FINAL_8PLUS_V12 */',1)

p.write_text(s,encoding='utf-8')
module=s.split('<script type="module">',1)[1].split('</script>',1)[0]
Path('/tmp/alan-game.mjs').write_text(module,encoding='utf-8')
print('final v12 patch complete',len(s))
