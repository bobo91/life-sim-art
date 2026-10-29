"""Read-only historical B02 GLB contract audit, not a B04 integration approval.

B04 was rejected at its Blender gate and has no GLB. This audit intentionally
reads the preserved B02 bytes; copy status metadata separately for review.
"""
import argparse,json,struct,hashlib,io,math,uuid
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--input',default='build/male-neutral-b02/delivery-001/chr_player_male_poc_001.glb');p.add_argument('--out',default='build/male-neutral-b04/contract-audit001');a=p.parse_args();r=Path(__file__).resolve().parents[1];src=r/a.input;out=r/a.out;out.mkdir(parents=True,exist_ok=False);raw=src.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);bo=20+n;binary=raw[bo+8:];assert raw[bo+4:bo+8]==b'BIN\x00'
formats={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)};widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def acc(i):
 x=g['accessors'][i];assert 'sparse' not in x;v=g['bufferViews'][x['bufferView']];fmt,size=formats[x['componentType']];width=widths[x['type']];stride=v.get('byteStride',size*width);start=v.get('byteOffset',0)+x.get('byteOffset',0);return [struct.unpack_from('<'+fmt*width,binary,start+j*stride) for j in range(x['count'])]
parents={c:i for i,node in enumerate(g['nodes']) for c in node.get('children',[])}
def path(i):
 return (path(parents[i])+'/' if i in parents else '')+g['nodes'][i].get('name',str(i))
joints=g['skins'][0]['joints'];jointset=set(joints);bones=[{'name':g['nodes'][i]['name'],'parent':g['nodes'][parents[i]]['name'] if parents.get(i) in jointset else None,'path':path(i),'node':i} for i in joints];support=[b for b in bones if b['name'].startswith('B02_')];clips=[]
for anim in g.get('animations',[]):
 channels={};dur=0;diffs=[]
 for ch in anim['channels']:
  sampler=anim['samplers'][ch['sampler']];times=acc(sampler['input']);values=acc(sampler['output']);node=ch['target']['node'];prop=ch['target']['path'];dur=max(dur,max(t[0] for t in times));channels.setdefault(g['nodes'][node].get('name',str(node)),[]).append(prop);err=max(abs(a-b) for a,b in zip(values[0],values[-1]));
  if prop=='rotation':err=min(err,max(abs(a+b) for a,b in zip(values[0],values[-1])))
  diffs.append(err)
 clips.append({'name':anim['name'],'durationSeconds':dur,'channels':len(anim['channels']),'maxEndpointTRSComponentError':max(diffs),'endpointsMatchWithin1e_6':max(diffs)<1e-6,'allSixSupportsHaveTRS':all(set(channels.get(s['name'],[]))=={'translation','rotation','scale'} for s in support),'supportChannels':{s['name']:channels.get(s['name'],[]) for s in support},'animatedNonJointNodes':[name for name in channels if name not in {b['name'] for b in bones}]})
textures=[]
for i,im in enumerate(g['images']):
 v=g['bufferViews'][im['bufferView']];b=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];pic=Image.open(io.BytesIO(b));textures.append({'image':i,'name':im.get('name'),'mimeType':im.get('mimeType'),'width':pic.width,'height':pic.height,'mode':pic.mode,'encodedBytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
def texture_ref(t,role):
 if not t:return None
 ti=t['index'];img=g['textures'][ti]['source'];return {'textureIndex':ti,'image':textures[img],'texCoord':t.get('texCoord',0),'scale':t.get('scale',1),'colorSpace':'sRGB RGB (alpha linear)' if role=='baseColor' else 'Linear/data','channels':'RGB tangent-space normal' if role=='normal' else 'G roughness, B metallic' if role=='metallicRoughness' else 'RGB base color / A alpha','sampler':g['samplers'][g['textures'][ti]['sampler']] if 'sampler' in g['textures'][ti] else None}
materials=[]
for i,m in enumerate(g['materials']):
 pbr=m['pbrMetallicRoughness'];materials.append({'index':i,'name':m['name'],'alphaMode':m.get('alphaMode','OPAQUE'),'alphaCutoff':m.get('alphaCutoff',.5),'doubleSided':m.get('doubleSided',False),'baseColorFactorLinear':pbr.get('baseColorFactor',[1,1,1,1]),'metallicFactor':pbr.get('metallicFactor',1),'roughnessFactor':pbr.get('roughnessFactor',1),'baseColor':texture_ref(pbr.get('baseColorTexture'),'baseColor'),'metallicRoughness':texture_ref(pbr.get('metallicRoughnessTexture'),'metallicRoughness'),'normal':texture_ref(m.get('normalTexture'),'normal'),'occlusion':texture_ref(m.get('occlusionTexture'),'occlusion'),'emissiveFactor':m.get('emissiveFactor',[0,0,0]),'extensions':m.get('extensions',{}),'meshUsers':[me.get('name') for me in g['meshes'] if any(p.get('material')==i for p in me['primitives'])]})
roots=[{'node':i,'name':g['nodes'][i].get('name'),'children':[g['nodes'][c].get('name') for c in g['nodes'][i].get('children',[])],'translation':g['nodes'][i].get('translation',[0,0,0]),'rotation':g['nodes'][i].get('rotation',[0,0,0,1]),'scale':g['nodes'][i].get('scale',[1,1,1])} for i in g['scenes'][g.get('scene',0)]['nodes']]
res={'schema':'male-b04-integration-readonly-audit-1','basis':'B02 baseline; B04 final values pending visual gate','sourceGlb':src.relative_to(r).as_posix(),'glbSha256':hashlib.sha256(raw).hexdigest(),'assetId':'chr_player_male_poc_001','units':'meters','rootNodes':roots,'skins':len(g['skins']),'bones':bones,'boneCount':len(bones),'supportBones':support,'clips':clips,'materials':materials,'textures':textures,'extensionsUsed':g.get('extensionsUsed',[]),'extensionsRequired':g.get('extensionsRequired',[]),'sourceJsonAsset':g.get('asset'),'gait':{'actualRootTranslationMps':0,'walk':{'stanceTravelMeters':.32,'stanceSeconds':.58,'cycleSeconds':1,'inferredDesignMps':.32/.58,'effectiveSameFootStrideMeters':.32/.58,'effectiveStepMeters':.32/.58/2,'stepsPerMinute':120,'requiredPlaybackRateAt4Mps':4/(.32/.58)},'run':{'stanceTravelMeters':.46,'stanceSeconds':.4*.75,'cycleSeconds':.75,'inferredDesignMps':.46/(.4*.75),'effectiveSameFootStrideMeters':.46/.4,'effectiveStepMeters':.46/.4/2,'stepsPerMinute':160,'requiredPlaybackRateAt4Mps':4/(.46/(.4*.75))},'phase':'Left lands at normalized0, right at.5 by recipe, different duty factors (.58 walk/.40 run); no pop-free blend guarantee','safePlaybackRange':'Unknown; no fixed4m/s controller test or certified range'},'proposedStableGuid':uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/bobo91/life-sim-art/assets/chr_player_male_poc_001').hex}
# Actual bind bounds: mesh nodes are identityTRS in the pinned input.
for node in g['nodes']:
 if 'mesh' in node:assert 'matrix' not in node and node.get('translation',[0,0,0])==[0,0,0] and node.get('rotation',[0,0,0,1])==[0,0,0,1] and node.get('scale',[1,1,1])==[1,1,1]
limits=[g['accessors'][p['attributes']['POSITION']] for m in g['meshes'] for p in m['primitives']];low=[min(x['min'][k] for x in limits) for k in range(3)];high=[max(x['max'][k] for x in limits) for k in range(3)];res['neutralBoundsGlTF']={'min':low,'max':high};res['neutralBoundsUnity']={'min':[-high[0],low[1],low[2]],'max':[-low[0],high[1],high[2]],'dimensions':[high[k]-low[k] for k in range(3)],'method':'ActualPOSITIONaccessorextrema, identitymeshTRS, glTFastmirrorX'}
(out/'contract-audit.json').write_bytes((json.dumps(res,indent=2)+'\n').encode());(out/'skeleton.json').write_bytes((json.dumps({'bones':bones,'rootNodes':roots},indent=2)+'\n').encode());(out/'material-spec.json').write_bytes((json.dumps({'materials':materials,'textures':textures,'extensionsUsed':res['extensionsUsed'],'extensionsRequired':res['extensionsRequired']},indent=2)+'\n').encode());print(json.dumps({'bones':len(bones),'supports':len(support),'clips':[(c['name'],c['durationSeconds'],c['maxEndpointTRSComponentError'],c['allSixSupportsHaveTRS']) for c in clips],'materials':len(materials),'images':len(textures),'rootNodes':roots,'guidProposal':res['proposedStableGuid']},indent=2))
