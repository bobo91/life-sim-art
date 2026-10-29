"""B01 bounded data-only Snow skin adapter and four original locomotion clips.
Preserves approved A03 mesh positions/topology/materials. No CloudRig execution.
"""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from mathutils.geometry import barycentric_transform
P=argparse.ArgumentParser();P.add_argument('--out',required=True);P.add_argument('--views',action='store_true');a=P.parse_args(sys.argv[sys.argv.index('--')+1:]);R=Path.cwd();out=R/a.out
assert not out.exists(),'Preserve previous proof';out.mkdir(parents=True);(out/'renders').mkdir()
def dump(p,v):p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def geom(o):
 m=o.data;m.calc_loop_triangles();h=hashlib.sha256()
 for v in m.vertices:h.update(struct.pack('<3f',*(o.matrix_world@v.co)))
 for t in m.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
 return h.hexdigest()
config=json.loads((R/'configs/male-neutral-b01-skeleton.json').read_text());src=R/'build/source-audit/original/Snow/snow_v4.2.blend';approved=R/'build/male-neutral-a03/delivery-003/character.blend';high=approved.with_name('character_high.blend');a01=R/'build/male-neutral-a01/delivery-002/character.blend';srcsha=sha(src);ash=sha(approved)
assert srcsha=='80fd0a81bca90f0efdcdcb98422df0e198ae57f4a1c239e13fb795922779b1fc';assert ash=='dcd7681255f49fa704844492b0ffc6964e434ccb4ae59aaba7788b0af56ffd90'
aff=config['a01Affine'];print('AFFINE',aff,flush=True)
scale=aff['scale'];offset=Vector(aff['offsetBeforeScale']);spec=config['bones'];groupmap=config['weightGroupMap'];face=set(config['remainingDeformGroupsCollapsedToHead']);sources={}
bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False);scene=bpy.context.scene;scene.frame_set(1)
head=bpy.data.objects['GEO-snow-head'];head.data.shape_keys.animation_data_clear()
for s in ['L','R']:
 head.data.shape_keys.key_blocks['Smile.'+s].value=.12
 for bone,dz in [('MSTR-Eyelid_Upper.'+s,-.006),('ACT-Lips_Corner.'+s,.0025)]:
  pb=bpy.data.objects['RIG-Snow'].pose.bones[bone];pb.matrix=Matrix.Translation(Vector((0,0,dz)))@pb.matrix
for o in scene.objects:
 if o.type=='MESH':
  for m in o.modifiers:
   if m.type=='SUBSURF':m.levels=m.render_levels=0
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();unknown=set();deform_names={b.name for b in bpy.data.objects['RIG-Snow'].data.bones if b.use_deform};ignored_stale=set()
for part in ['body','head','shirt','pants','shoes_base','shoes_bottom','shoes_parts']:
 o=bpy.data.objects['GEO-snow-'+part];me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);used=sorted({i for p in me.polygons for i in p.vertices});pts=[];weights=[]
 for i in used:
  v=me.vertices[i];pts.append((o.matrix_world@v.co-offset)*scale);w={}
  for g in v.groups:
   n=o.vertex_groups[g.group].name
   if n not in deform_names:
    if n.startswith('DEF-') and g.weight>1e-7:ignored_stale.add(n)
    continue
   dest=groupmap.get(n)
   if dest is None and n in face:dest='Head'
   if dest is None and g.weight>1e-7:unknown.add(n);continue
   if dest:w[dest]=w.get(dest,0)+g.weight
  assert sum(w.values())>1e-6,(part,i);s=sum(w.values());weights.append({n:x/s for n,x in w.items() if x>1e-8})
 sources[part]={'pts':pts,'weights':weights}
assert not unknown,unknown
# Match weights to the exact approved ancestor coordinates, never original vertex indices.
bpy.ops.wm.open_mainfile(filepath=str(a01),load_ui=False,use_scripts=False);mapping={}
for part,d in sources.items():
 o=bpy.data.objects['M01_'+part];kd=KDTree(len(d['pts']))
 for i,p in enumerate(d['pts']):kd.insert(p,i)
 kd.balance();d['a01weights']=[];dist=[]
 for v in o.data.vertices:
  _,i,error=kd.find(o.matrix_world@v.co);dist.append(error);d['a01weights'].append(d['weights'][i])
 assert max(dist)<1e-6,(part,max(dist));mapping[part]={'ancestorMatchMaxMeters':max(dist),'ancestorVertices':len(dist)}
bpy.ops.wm.open_mainfile(filepath=str(high),load_ui=False,use_scripts=False)
for part,d in sources.items():
 o=bpy.data.objects['M01_'+part];assert len(o.data.vertices)==len(d['a01weights']);o.data.calc_loop_triangles();d['highpoints']=[o.matrix_world@v.co for v in o.data.vertices];d['triangles']=[tuple(t.vertices) for t in o.data.loop_triangles]
bpy.ops.wm.open_mainfile(filepath=str(approved),load_ui=False,use_scripts=False);scene=bpy.context.scene;asset=[o for o in scene.objects if o.type=='MESH' and o.get('wc_asset_id')=='chr_player_male_poc_001'];before={o.name:geom(o) for o in asset};assert len(asset)==10
# The data-only runtime skeleton deliberately excludes constraints, drivers, Text and controls.
arm=bpy.data.armatures.new('A03_B01_Skeleton52');rig=bpy.data.objects.new('A03_B01_Rig',arm);scene.collection.objects.link(rig);root=bpy.data.objects['CHR_PlayerMale_A01'];rig.parent=root
bpy.context.view_layer.objects.active=rig;bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for b in spec:
 eb=arm.edit_bones.new(b['gameBone']);eb.head=(Vector(b['sourceHead'])-offset)*scale;eb.tail=(Vector(b['sourceTail'])-offset)*scale;eb.align_roll(Matrix(b['sourceRestMatrix']).col[2].to_3d());eb.use_deform=True
 if b['parent']:eb.parent=arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');assert len(arm.bones)==52
weightreport={}
for o in asset:
 part=o.name.removeprefix('M01_');weights=[];errors=[];dropped=[]
 if part in ['eyes','eyebrows','hair_base']:weights=[{'Head':1.0} for v in o.data.vertices];errors=[0]*len(weights)
 else:
  d=sources[part]
  if len(o.data.vertices)==len(d['highpoints']) and part=='head':weights=d['a01weights'];errors=[0]*len(weights)
  else:
   tree=BVHTree.FromPolygons(d['highpoints'],d['triangles'],all_triangles=True)
   for v in o.data.vertices:
    near,normal,ti,dist=tree.find_nearest(o.matrix_world@v.co);tri=d['triangles'][ti];p=[d['highpoints'][i] for i in tri];bc=barycentric_transform(near,*p,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));bc=[max(0,min(1,x)) for x in bc];s=sum(bc);w={}
    for t,blend in zip(tri,bc):
     for n,value in d['a01weights'][t].items():w[n]=w.get(n,0)+blend/s*value
    weights.append(w);errors.append(dist)
 for vg in list(o.vertex_groups):o.vertex_groups.remove(vg)
 groups={b.name:o.vertex_groups.new(name=b.name) for b in arm.bones}
 for i,w in enumerate(weights):
  order=sorted(w.items(),key=lambda x:(-x[1],x[0]));total=sum(x[1] for x in order);chosen=order[:4];retained=sum(x[1] for x in chosen);dropped.append(1-retained/total)
  assert retained>1e-8
  for n,value in chosen:groups[n].add([i],value/retained,'REPLACE')
 m=o.modifiers.new('B01_LBS4','ARMATURE');m.object=rig;m.use_deform_preserve_volume=False
 weightreport[o.name]={'vertices':len(weights),'maxSurfaceTransferDistanceMeters':max(errors),'maxDiscardedWeightFraction':max(dropped),'meanDiscardedWeightFraction':sum(dropped)/len(dropped),'maxInfluences':4,'normalized':True}
assert {o.name:geom(o) for o in asset}==before
for t in list(bpy.data.texts):bpy.data.texts.remove(t)
for ac in list(bpy.data.actions):bpy.data.actions.remove(ac)
rest={b.name:b.matrix_local.copy() for b in arm.bones};fps=24;scene.render.fps=fps;clipdefs=[('idle',48),('walk',24),('run',18),('turn',36)];actions=[];posedmetrics={}
def rot(axis,ang):return Matrix.Rotation(ang,4,axis)
def buildpose(kind,u):
 phase=2*math.pi*u;run=kind=='run';moving=kind in ['walk','run','turn'];bob=(.012 if run else .004)*math.cos(2*phase) if moving else .0015*math.sin(phase)
 lower=.038 if run else .022;delta=Vector((.004*math.sin(phase) if moving else 0,0,-lower+bob));yaw=(math.pi/2*(3*u*u-2*u*u*u)) if kind=='turn' else 0
 mats={}
 for b in spec:
  n=b['gameBone'];parent=b['parent'];m=(mats[parent]@rest[parent].inverted()@rest[n]) if parent else rest[n].copy();
  if not parent:m.translation+=delta
  if n=='Chest':m=m@rot('Z',.018*math.sin(phase) if moving else 0)
  if n=='UpperChest':m=m@rot('X',.04 if run else 0)
  mats[n]=m
 for side,sign in [('L',1),('R',-1)]:
  ph=(u+(0 if side=='L' else .5))%1;wave=math.sin(2*math.pi*ph);swing=(.45 if run else .22)*wave if moving else .015*math.sin(phase)
  n='UpperArm.'+side;p='Shoulder.'+side;m=mats[p]@rest[p].inverted()@rest[n];r=rot('X',swing)@rot('Y',sign*math.radians(76))@m.to_3x3().to_4x4();r.translation=m.translation;mats[n]=r
  n='LowerArm.'+side;p='UpperArm.'+side;m=mats[p]@rest[p].inverted()@rest[n];r=rot('X',-math.radians(65 if run else 18))@m.to_3x3().to_4x4();r.translation=m.translation;mats[n]=r
  n='Hand.'+side;mats[n]=mats['LowerArm.'+side]@rest['LowerArm.'+side].inverted()@rest[n]
  for finger in ['Thumb','Index','Middle','Ring','Pinky']:
   for j in range(1,4):
    n=finger+str(j)+'.'+side;p='Hand.'+side if j==1 else finger+str(j-1)+'.'+side;mats[n]=mats[p]@rest[p].inverted()@rest[n]@rot('X',math.radians(8 if finger=='Thumb' else 15))
  upper='UpperLeg.'+side;lowerleg='LowerLeg.'+side;foot='Foot.'+side;toe='Toes.'+side;hip=(mats['Hips']@rest['Hips'].inverted()@rest[upper]).translation;ankle=rest[foot].translation.copy();stride=.16 if kind=='walk' else .23 if run else .035 if kind=='turn' else 0;stance=.58 if not run else .40
  if moving:
   if ph<stance:ankle.y+=stride*(-1+2*ph/stance)
   else:
    t=(ph-stance)/(1-stance);ankle.y+=stride*math.cos(math.pi*t);ankle.z+=(.12 if run else .065)*math.sin(math.pi*t)
  l1=(rest[lowerleg].translation-rest[upper].translation).length;l2=(rest[foot].translation-rest[lowerleg].translation).length;v=ankle-hip;dist=min(v.length,l1+l2-1e-5);direction=v.normalized();center=(l1*l1-l2*l2+dist*dist)/(2*dist);height=math.sqrt(max(0,l1*l1-center*center));forward=Vector((0,-1,0));perp=(forward-direction*direction.dot(forward)).normalized();knee=hip+direction*center+perp*height
  for n,start,end,restend in [(upper,hip,knee,rest[lowerleg].translation),(lowerleg,knee,ankle,rest[foot].translation)]:
   q=(restend-rest[n].translation).rotation_difference(end-start);m=q.to_matrix().to_4x4()@rest[n].to_3x3().to_4x4();m.translation=start;mats[n]=m
  m=rest[foot].copy();m.translation=ankle;mats[foot]=m;mats[toe]=m@rest[foot].inverted()@rest[toe]
 yawmat=rot('Z',yaw)
 for n in mats:mats[n]=yawmat@mats[n]
 return mats
for name,frames in clipdefs:
 action=bpy.data.actions.new(name);rig.animation_data_create();rig.animation_data.action=action
 for frame in range(1,frames+2):
  u=(frame-1)/frames;scene.frame_set(frame);mats=buildpose(name,u)
  for b in spec:
   n=b['gameBone'];pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.matrix=mats[n];bpy.context.view_layer.update();pb.keyframe_insert(data_path='location',frame=frame,group=n);pb.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=n);pb.keyframe_insert(data_path='scale',frame=frame,group=n)
 for fc in action.fcurves:
  for key in fc.keyframe_points:key.interpolation='LINEAR'
 action.use_fake_user=True;actions.append(action)
 rig.animation_data.action=None
# NLA tracks give exact named clips and explicit ranges; no source pose actions reused.
for action,(_,frames) in zip(actions,clipdefs):
 track=rig.animation_data.nla_tracks.new();track.name=action.name;strip=track.strips.new(action.name,1,action);strip.action_frame_start=1;strip.action_frame_end=frames+1;strip.frame_end=frames+1;track.mute=True
scene.frame_start=1;scene.frame_end=49
# Assert the approved bind geometry is unchanged and all modifiers are identity at rest.
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();resterrors={}
for o in asset:
 ev=o.evaluated_get(dg);me=ev.to_mesh();err=max((v.co-me.vertices[i].co).length for i,v in enumerate(o.data.vertices));resterrors[o.name]=err;ev.to_mesh_clear();assert err<1e-5,(o.name,err)
for ac,(_,frames) in zip(actions,clipdefs):
 rig.animation_data.action=ac;stats=[]
 for f in sorted({1,1+frames//4,1+frames//2,1+3*frames//4,frames+1}):
  scene.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pts=[]
  for o in asset:
   ev=o.evaluated_get(dg);me=ev.to_mesh();pts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
  assert all(math.isfinite(x) for p in pts for x in p);stats.append({'frame':f,'min':[min(p[k] for p in pts) for k in range(3)],'max':[max(p[k] for p in pts) for k in range(3)]})
 posedmetrics[ac.name]=stats
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
scene.frame_set(1);bpy.context.view_layer.update();assert {o.name:geom(o) for o in asset}==before
root['phase']='B01 limited skin/locomotion proof';root['rigReuse']='52 joint data-only adapter; not native CloudRig runtime';root['license']='CC-BY-4.0';rig['animations']='Original procedural B01 clips, not Snow pose-library actions'
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);rig.select_set(True)
for o in asset:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(out/'chr_player_male_poc_001.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_nla_strips=True,export_force_sampling=True,export_frame_range=False,export_skins=True,export_def_bones=False,export_morph=False,export_cameras=False,export_lights=False,export_influence_nb=4)
# Persist editable skin+clips in independent copy, with idle active for immediate review.
rig.animation_data.action=actions[0];scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'character_b01.blend'))
base=json.loads((approved.parent/'asset-report.json').read_text());report={'assetId':base['assetId'],'phase':'B01','triangles':base['triangles'],'materialCount':base['materialCount'],'meshCount':10,'bones':52,'sourceOriginalSha256':srcsha,'approvedA03BlendSha256':ash,'approvedA03GeometryHashesUnchanged':before,'restSkinningMaxErrorMeters':resterrors,'ancestorMapping':mapping,'ignoredStaleNonBoneGroups':sorted(ignored_stale),'weights':weightreport,'clips':[{'name':n,'frames':f,'fps':fps,'durationSeconds':f/fps,'loop':n!='turn','motion':'in-place except turn yaw90deg'} for n,f in clipdefs],'poseSamples':posedmetrics,'sourceEmbeddedScriptsExecutedOrIncluded':False,'nativeRigPreserved':False,'nativeFeaturesLost':['B-Bone segments','dual-quaternion skinning','pose-space correctives','facial rig/keys'],'license':'CC-BY-4.0','credit':'Snow Rig (CC) Blender Foundation | studio.blender.org','animationProvenance':'Original deterministic B01 clips authored in this repository; derivative skin/skeleton credit retained. No downloaded animation or paid service.','limitations':['Locomotion only, fixed approved facial expression','No Humanoid mapping/controller/transitions/game integration','No clothing variation certification','Bounded skin transfer; no extensive manual repair']}
dump(out/'asset-report.json',report);assert sha(src)==srcsha and sha(approved)==ash;print(json.dumps({'output':str(out),'bones':52,'triangles':report['triangles'],'clips':report['clips'],'restErrorMax':max(resterrors.values())}),flush=True)
