"""B02 local LBS weights and at most six explicitly baked half-angle supports.
No geometry, UV, material, face or original animation edit is made by apply().
"""
import math,hashlib,struct
from mathutils import Matrix,Vector

def _geometry(obj):
 h=hashlib.sha256()
 for v in obj.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in obj.data.polygons:
  for i in p.vertices:h.update(struct.pack('<I',i))
 return h.hexdigest()

def _smooth(t):return t*t*(3-2*t)

def apply(rig,asset,config):
 """Return metadata and support specs; caller bakes support poses for every key."""
 import bpy
 assert len(rig.data.bones)==52,'B02 local correction requires the preserved52bone B01 input, not an already corrected copy'
 before={o.name:_geometry(o) for o in asset};rest={b.name:b.matrix_local.copy() for b in rig.data.bones};supports=[];specs=[]
 for joint in config['joints']:
  for side in ['L','R']:
   proximal=joint['proximal']+'.'+side;distal=joint['distal']+'.'+side;name='B02_'+joint['label'].capitalize()+'.'+side
   support={'bone':name,'parent':proximal,'proximal':proximal,'distal':distal,'label':joint['label']}
   use_support=config.get('enableSupportJoints',False) and joint.get('useSupport',True)
   if use_support:supports.append(support)
   specs.append({**joint,'proximalName':proximal,'distalName':distal,'supportName':name if use_support else None})
 if supports:
  previous_active=bpy.context.view_layer.objects.active;bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
  for support in supports:
   n=support['bone'];d=support['distal'];eb=rig.data.edit_bones.new(n);m=rest[d];eb.head=m.translation;eb.tail=eb.head+m.col[1].to_3d().normalized()*.04;eb.align_roll(m.col[2].to_3d());eb.parent=rig.data.edit_bones[support['parent']];eb.use_deform=True
  bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.objects.active=previous_active
 rest={b.name:b.matrix_local.copy() for b in rig.data.bones};report={}
 for obj in asset:
  if obj.name not in {'M01_body','M01_pants'}:continue
  names={g.index:g.name for g in obj.vertex_groups};weights=[{names[g.group]:g.weight for g in v.groups if g.weight>1e-8} for v in obj.data.vertices];original=[dict(w) for w in weights];changes={}
  for spec in specs:
   if obj.name not in spec['parts']:continue
   a=spec['proximalName'];b=spec['distalName'];center=rest[b].translation;axis=(center-rest[a].translation).normalized();width=spec['halfWidthMeters'];radius=spec['radiusMeters'];count=0
   for i,v in enumerate(obj.data.vertices):
    w=weights[i];mass=w.get(a,0)+w.get(b,0);d=v.co-center;long=d.dot(axis);radial=(d-axis*long).length
    if mass<.35 or abs(long)>=width or radial>radius:continue
    t=_smooth(max(0,min(1,(long/width+1)/2)));w[a]=mass*(1-t);w[b]=mass*t
    if spec['supportName']:
     # Central section follows the actual half-angle transform; neighboring
     # sections use at most45deg relative LBS blends instead of the full hinge.
     support=spec.get('supportStrength',1.0)*math.sin(math.pi*t)**2;w[a]*=1-support;w[b]*=1-support;w[spec['supportName']]=mass*support
    count+=1
   changes[spec['label']+':'+a[-1]]=count
  finger=config.get('fingerWeightPass',{})
  if obj.name=='M01_body' and finger.get('enabled'):
   for side in ['L','R']:
    for name in ['Thumb','Index','Middle','Ring','Pinky']:
     for joint in [1,2,3]:
      b=name+str(joint)+'.'+side;a='Hand.'+side if joint==1 else name+str(joint-1)+'.'+side;center=rest[b].translation;axis=rest[b].col[1].to_3d().normalized();count=0
      for i,v in enumerate(obj.data.vertices):
       w=weights[i];mass=w.get(a,0)+w.get(b,0);d=v.co-center;long=d.dot(axis);rad=(d-axis*long).length
       if mass<.55 or abs(long)>finger['halfWidthMeters'] or rad>finger['radiusMeters']:continue
       t=_smooth(max(0,min(1,(long/finger['halfWidthMeters']+1)/2)));w[a]=mass*(1-t);w[b]=mass*t;count+=1
      changes[b]=count
  for g in list(obj.vertex_groups):obj.vertex_groups.remove(g)
  groups={b.name:obj.vertex_groups.new(name=b.name) for b in rig.data.bones};discard=[];changed=0
  for i,w in enumerate(weights):
   order=sorted(((n,x) for n,x in w.items() if x>1e-8),key=lambda x:(-x[1],x[0]));total=sum(x for n,x in order);keep=order[:config.get('maxInfluences',4)];s=sum(x for n,x in keep);discard.append(1-s/total);assert s>1e-6
   new={n:x/s for n,x in keep}
   changed+=any(abs(new.get(n,0)-original[i].get(n,0))>1e-7 for n in set(new)|set(original[i]))
   for n,x in new.items():groups[n].add([i],x,'REPLACE')
  report[obj.name]={'verticesChanged':changed,'zoneAssignments':changes,'maxDiscardedMassFraction':max(discard),'meanDiscardedMassFraction':sum(discard)/len(discard),'maxInfluences':max(len(v.groups) for v in obj.data.vertices)}
 assert before=={o.name:_geometry(o) for o in asset},'Approved geometry changed'
 return {'supports':supports,'weights':report,'approvedRawGeometryUnchanged':True,'bonesBefore':len(rest)-len(supports),'bonesAfter':len(rig.data.bones),'mode':'local weights plus baked half-angle supports' if supports else 'local weights only'}

def update_support_matrices(mats,rest,supports):
 """Mutates global pose matrices after the52original poses have been evaluated.
 All runtime behavior is baked TRS: no constraint/driver/DQ/code dependency.
 """
 for spec in supports:
  upper=spec['proximal'];lower=spec['distal'];name=spec['bone'];straight=mats[upper]@rest[upper].inverted()@rest[lower];bent=mats[lower];q=straight.to_quaternion().slerp(bent.to_quaternion(),.5);m=q.to_matrix().to_4x4();m.translation=bent.translation;mats[name]=m
 return mats

def update_current_pose(rig,supports):
 """Convenience for independent unsaved test poses; bake callers use matrices."""
 import bpy
 bpy.context.view_layer.update();rest={b.name:b.matrix_local.copy() for b in rig.data.bones};mats={b.name:b.matrix.copy() for b in rig.pose.bones};update_support_matrices(mats,rest,supports)
 for spec in supports:rig.pose.bones[spec['bone']].matrix=mats[spec['bone']]
 bpy.context.view_layer.update()
