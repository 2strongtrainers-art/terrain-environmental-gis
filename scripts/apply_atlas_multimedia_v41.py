from pathlib import Path
import base64,gzip,hashlib,json
ROOT=Path('.')
SHELL=[ROOT/f'atlas-src/shell-{i:03d}.txt' for i in range(3)]
DATA=[ROOT/f'atlas-src/data-{i:03d}.txt' for i in range(9)]
shell=''.join(p.read_text() for p in SHELL)
data_b64=''.join(p.read_text().strip() for p in DATA)
records=json.loads(gzip.decompress(base64.b64decode(data_b64)))
assert len(records)==1846
assert 'ATLAS-MULTIMEDIA-V4' in shell
assert '__DATA_B64__' in shell
if 'ATLAS-MULTIMEDIA-V41' not in shell:
    old='{id:"nature-livecam",route:"watch",patterns:["live animal cam","live animal cams","live nature cam","live nature cams","wildlife cam","wildlife cams","animal webcam","nature webcam"],anchors:["live cam","nature","wildlife","animal"],terms:["webcam","camera","stream","explore"]}'
    new='{id:"nature-livecam",route:"watch",patterns:["live animal cam","live animal cams","live animal nature cams","animal cam","animal cams","nature cam","nature cams","live cam","live cams","live nature cam","live nature cams","wildlife cam","wildlife cams","wildlife webcam","animal webcam","nature webcam","live webcam","live webcams"],anchors:["live cam","nature","wildlife","animal"],terms:["webcam","camera","stream","explore"]}'
    assert old in shell
    shell=shell.replace(old,new,1)
    old2='{id:"watch-free",route:"watch",patterns:["watch free","watch something free","free movie","free movies","free tv","free streaming","stream free","live tv","live news","watch a movie","watch movie","watch tv","free documentary","watch documentary","something to watch","im bored","i m bored"],anchors:["movie","movies","tv","streaming","watch","documentary","live"],terms:["free","shows","channels","on demand","entertainment"]}'
    new2='{id:"watch-free",route:"watch",patterns:["watch free","watch for free","watch something free","something to watch","something interesting to watch","show me something to watch","show me something interesting","free movie","free movies","free tv","free tv shows","free shows","free streaming","stream free","streaming free","live tv","free live tv","live news","watch a movie","watch movie","watch tv","free documentary","watch documentary","im bored","i m bored","bored show me"],anchors:["movie","movies","tv","streaming","watch","documentary","live"],terms:["free","shows","channels","on demand","entertainment"]}'
    assert old2 in shell
    shell=shell.replace(old2,new2,1)
    shell=shell.replace('/* ATLAS-MULTIMEDIA-V4 */','/* ATLAS-MULTIMEDIA-V4 */\n/* ATLAS-MULTIMEDIA-V41 — live-cam + browse-intent precision */',1)

def split_n(text,n):
    q,r=divmod(len(text),n);out=[];p=0
    for i in range(n):
        z=q+(1 if i<r else 0);out.append(text[p:p+z]);p+=z
    assert ''.join(out)==text
    return out
for p,x in zip(SHELL,split_n(shell,3)):p.write_text(x)
bundle=shell.replace('__DATA_B64__',data_b64)
(ROOT/'atlas-bundle.html').write_text(bundle)
rep=json.loads((ROOT/'atlas-build-report.json').read_text())
rep['bundle_bytes']=len(bundle.encode());rep['sha256']=hashlib.sha256(bundle.encode()).hexdigest();rep['multimedia_v41']={'live_cam_phrase_expansion':True,'browse_free_watch_phrase_expansion':True}
(ROOT/'atlas-build-report.json').write_text(json.dumps(rep,indent=2)+'\n')
assert 'ATLAS-MULTIMEDIA-V41' in bundle
print(json.dumps(rep['multimedia_v41'],indent=2))