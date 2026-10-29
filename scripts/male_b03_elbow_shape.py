"""One bounded B03 elbow-only corrective shape trial; no new rig or topology.
Construct a fixed posed-space local relaxation at the B02 run25% reference,
then invert the existing linear skin matrix into two ordinary relative keys.
"""
import math,hashlib,json,struct
from pathlib import Path
from mathutils import Matrix,Vector


def _hash_body(obj):
 h=hashlib.sha256()
 for v in obj.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in obj.data.polygons:
  for i in p.vertices:h.update(struct.pack('<I',i))
 return h.hexdigest()

def _smooth(t):
 t=max(0.0,min(1.0,t));return t*t*(3-2*t)

def measure_elbow_bend(rig,side):
 upper=rig.pose.bones['UpperArm.'+side];lower=rig.pose.bones['LowerArm.'+side]
 a=(upper.tail-upper.head).normalized();b=(lower.tail-lower.head).normalized()
 ru=rig.data.bones[upper.name];rl=rig.data.bones[lower.name];ra=(ru.tail_local-ru.head_local).normalized();rb=(rl.tail_local-rl.head_local).normalized()
 neutral=math.acos(max(-1,min(1,ra.dot(rb))));current=math.acos(max(-1,min(1,a.dot(b))))
 return {'angleDegrees':math.degrees(current),'neutralAngleDegrees':math.degrees(neutral),'bendDegrees':max(0.0,math.degrees(current-neutral))}

def activation(bend_degrees,full_degrees,config):
 start=config['activationStartDegrees']
 if bend_degrees<=start:return 0.0
 return _smooth((bend_degrees-start)/max(1e-6,full_degrees-start))

def apply_activation(rig,body,metadata,config):
 values={}
 for side in ['L','R']:
  angle=measure_elbow_bend(rig,side);value=activation(angle['bendDegrees'],metadata['sides'][side]['referenceBend']['bendDegrees'],config);body.data.shape_keys.key_blocks[metadata['sides'][side]['key']].value=value;values[side]={'weight':value,**angle}
 return values

def build_corrective(rig,body,config):
 import bpy
 assert body.name=='M01_body' and len(rig.data.bones)==58
 assert body.data.shape_keys is None,'Run only on the preserved B02 independent copy'
 before=_hash_body(body);body.data.calc_loop_triangles();topology=[tuple(t.vertices) for t in body.data.loop_triangles]
 for m in body.modifiers:assert m.type=='ARMATURE' and not m.use_deform_preserve_volume
 basis=[v.co.copy() for v in body.data.vertices];adj=[set() for v in basis]
 for edge in body.data.edges:
  a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mesh=ev.to_mesh();posed=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear();groupnames={g.index:g.name for g in body.vertex_groups};transforms={}
 object_from_arm=body.matrix_world.inverted()@rig.matrix_world;arm_from_object=rig.matrix_world.inverted()@body.matrix_world
 for pb in rig.pose.bones:transforms[pb.name]=object_from_arm@pb.matrix@pb.bone.matrix_local.inverted()@arm_from_object
 blended=[];skin_errors=[]
 for v,reference in zip(body.data.vertices,posed):
  m=Matrix(((0,0,0,0),)*4);s=0
  for g in v.groups:
   n=groupnames[g.group]
   if n not in transforms:continue
   weight=g.weight;s+=weight;m=m+transforms[n]*weight
  assert abs(s-1)<1e-5
  m=m*(1/s);blended.append(m.to_3x3());skin_errors.append((m@v.co-reference).length)
 assert max(skin_errors)<1e-5,max(skin_errors)
 body.shape_key_add(name='Basis',from_mix=False);meta={'method':'One tightly masked posed-space Taubin relaxation, inverse existing blendedLBS into two local relative keys','basisHash':before,'sourceRunFrame':config['sourceRunFrame'],'maxForwardSkinPredictionErrorMeters':max(skin_errors),'sides':{}}
 for side in ['L','R']:
  upper='UpperArm.'+side;lower='LowerArm.'+side;center=rig.data.bones[lower].head_local;axis=(center-rig.data.bones[upper].head_local).normalized();factors=[]
  influence_names={upper,lower,'B02_Elbow.'+side}
  for v in body.data.vertices:
   d=v.co-center;along=abs(d.dot(axis));radius=(d-axis*d.dot(axis)).length;mass=sum(g.weight for g in v.groups if groupnames[g.group] in influence_names)
   factor=(1-_smooth((along-config['fullStrengthHalfWidthMeters'])/(config['halfWidthMeters']-config['fullStrengthHalfWidthMeters']))) if along<config['halfWidthMeters'] and radius<config['radiusMeters'] and mass>.8 else 0
   factors.append(factor)
  target=[v.copy() for v in posed]
  for cycle in range(config['taubinCycles']):
   for amount in [config['lambda'],config['mu']]:
    old=[v.copy() for v in target]
    for i,weight in enumerate(factors):
     if not weight or not adj[i]:continue
     average=sum((old[j] for j in adj[i]),Vector())/len(adj[i]);target[i]=old[i]+(average-old[i])*amount*weight
  keyname='B03_ElbowCorrective.'+side;key=body.shape_key_add(name=keyname,from_mix=False);moved=[];posed_deltas=[];rest_deltas=[];ids=[]
  for i,(raw,p,desired,weight) in enumerate(zip(basis,posed,target,factors)):
   delta=(desired-p)*weight
   if delta.length>config['maximumPosedDeltaMeters']:delta*=config['maximumPosedDeltaMeters']/delta.length
   if delta.length<1e-8:continue
   correction=blended[i].inverted()@delta;key.data[i].co=raw+correction;moved.append(i);posed_deltas.append(delta.length);rest_deltas.append(correction.length);ids.append(i)
  key.value=0;meta['sides'][side]={'key':keyname,'referenceBend':measure_elbow_bend(rig,side),'verticesChanged':len(moved),'vertexIds':ids,'maxPosedCorrectionMeters':max(posed_deltas,default=0),'maxRestKeyDeltaMeters':max(rest_deltas,default=0),'longitudinalMaskHalfWidthMeters':config['halfWidthMeters'],'radialMaskMeters':config['radiusMeters']}
 assert _hash_body(body)==before,'Raw approved neutral mesh changed'
 assert all((a.co-b).length<1e-9 for a,b in zip(body.data.shape_keys.key_blocks['Basis'].data,basis))
 assert len(rig.data.bones)==58
 meta['topologyUnchanged']=topology==[tuple(t.vertices) for t in body.data.loop_triangles];meta['neutralBasisExact']=True;meta['rigWeightsMaterialsUnchanged']=True
 return meta


def _run_probe():
 import argparse,sys,bpy
 from male_b02_joint_weights import update_support_matrices
 p=argparse.ArgumentParser();p.add_argument('--source',default='build/male-neutral-b02/delivery-001/character_b02.blend');p.add_argument('--config',default='configs/male-neutral-b03-elbow.json');p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=Path.cwd();out=r/a.out;assert not out.exists();out.mkdir(parents=True);(out/'B02').mkdir();(out/'B03').mkdir();cfg=json.loads((r/a.config).read_text(encoding='utf-8'));source=r/a.source;sourcehash=hashlib.sha256(source.read_bytes()).hexdigest();assert sourcehash==cfg['sourceBlendSha256'];bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False);sc=bpy.context.scene;rig=bpy.data.objects[cfg['rig']];body=bpy.data.objects[cfg['body']];basehashes={o.name:_hash_body(o) for o in sc.objects if o.type=='MESH' and o.name.startswith('M01_')};rig.animation_data.action=bpy.data.actions['run'];sc.frame_set(int(cfg['sourceRunFrame']),subframe=cfg['sourceRunFrame']%1);bpy.context.view_layer.update();meta=build_corrective(rig,body,cfg);rest={b.name:b.matrix_local.copy() for b in rig.data.bones};major=[n for n in rest if not n.startswith('B02_')];supports=json.loads((source.parent/'asset-report.json').read_text(encoding='utf-8'))['supportJoints'];reference_pose={n:rig.pose.bones[n].matrix.copy() for n in major};cam=sc.camera;sc.cycles.samples=12;sc.render.threads_mode='FIXED';sc.render.threads=6;sc.render.resolution_x=sc.render.resolution_y=800;sc.render.resolution_percentage=100;views=[];metrics={}
 def set_pose(name):
  if name=='run25':
   rig.animation_data.action=bpy.data.actions['run'];sc.frame_set(int(cfg['sourceRunFrame']),subframe=cfg['sourceRunFrame']%1);bpy.context.view_layer.update()
  else:
   rig.animation_data.action=None
   for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
   # Keep the actual run upperarm and intrinsic run hinge-plane. Changing
   # the old Tpose/worldZ diagnostic plane would add an unrelated twist test.
   mats={n:reference_pose[n].copy() for n in major};angle=90 if name=='elbow90' else 10
   for side in ['L','R']:
    n='LowerArm.'+side;u=mats['UpperArm.'+side].col[1].to_3d().normalized();v=mats[n].col[1].to_3d().normalized();axis=u.cross(v).normalized();desired=Matrix.Rotation(math.radians(angle),4,axis).to_3x3()@u;q=v.rotation_difference(desired);old=mats[n].copy();new=q.to_matrix().to_4x4()@old.to_3x3().to_4x4();new.translation=old.translation;d=new@old.inverted()
    for child in major:
     if child==n or any(b.name==n for b in rig.data.bones[child].parent_recursive):mats[child]=d@mats[child]
   update_support_matrices(mats,rest,supports)
   for n in major+[s['bone'] for s in supports]:rig.pose.bones[n].matrix=mats[n];bpy.context.view_layer.update()
  bpy.context.view_layer.update()
 for pose in ['run25','elbow90','near_straight10']:
  set_pose(pose);poses={s:measure_elbow_bend(rig,s) for s in ['L','R']};metrics[pose]={'bend':poses};foci={s:rig.pose.bones['LowerArm.'+s].matrix.translation.copy() for s in ['L','R']}
  for label in ['B02','B03']:
   if label=='B02':
    for s in ['L','R']:body.data.shape_keys.key_blocks[meta['sides'][s]['key']].value=0
    weights={s:0 for s in ['L','R']}
   else:weights=apply_activation(rig,body,meta,cfg)
   bpy.context.view_layer.update();metrics[pose][label]={'weights':weights}
   for side in ['L','R']:
    target=foci[side];cam.data.type='ORTHO';cam.data.ortho_scale=.31;cam.location=target+Vector((.55 if side=='L' else -.55,-1,.25));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/label/(pose+'_'+side+'.png'));bpy.ops.render.render(write_still=True);views.append({'label':label,'pose':pose,'side':side,'focus':list(target),'camera':list(cam.location),'orthoScale':.31})
 # Restore exact reference pose and the measured bend-driven weight for inspection.
 set_pose('run25');apply_activation(rig,body,meta,cfg);bpy.ops.wm.save_as_mainfile(filepath=str(out/'candidate.blend'))
 assert sourcehash==hashlib.sha256(source.read_bytes()).hexdigest();assert basehashes=={o.name:_hash_body(o) for o in sc.objects if o.type=='MESH' and o.name.startswith('M01_')}
 result={'schema':'male-b03-isolated-shape-proof-1','sourceSha256':sourcehash,'config':cfg,'corrective':meta,'poses':metrics,'views':views,'sourceAndAllRawMeshesUnchanged':True,'boneCount':len(rig.data.bones),'topologyChanged':False,'unityOrExportRun':False,'diagnosticPosePlane':'Physical90/10degree direction angles, actual run upperarm and run hinge-plane held fixed; not the historical Tpose/worldZ diagnostic.','render':'Actual CPU Cycles12samples on same scene/cameras/lights, no image retouch','gate':'Visual judgement required; technical preservation alone is not a GO'};(out/'report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({'output':str(out),'referenceBends':{s:meta['sides'][s]['referenceBend'] for s in meta['sides']},'correctedVertices':{s:meta['sides'][s]['verticesChanged'] for s in meta['sides']}}),flush=True)

if __name__=='__main__':
 import sys
 sys.path.insert(0,str(Path(__file__).resolve().parent))
 _run_probe()
