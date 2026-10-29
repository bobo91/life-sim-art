"""Bounded B02 on an independent B01 copy: local weights, baked supports, turn contact."""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
import bpy
from mathutils import Matrix
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'scripts'))
from male_b02_joint_weights import apply,update_support_matrices
from male_b02_turn import apply_turn
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--joint-config',default='configs/male-neutral-b02-joints.json');p.add_argument('--turn-config',default='configs/male-neutral-b02-turn.json');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=ROOT/a.out;assert not out.exists(),'Preserve previous variants';out.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
def geometry(o):
 h=hashlib.sha256();o.data.calc_loop_triangles()
 for v in o.data.vertices:h.update(struct.pack('<3f',*(o.matrix_world@v.co)))
 for t in o.data.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
 return h.hexdigest()
def appearance(o):
 h=hashlib.sha256()
 for layer in o.data.uv_layers:
  h.update(layer.name.encode())
  for v in layer.data:h.update(struct.pack('<2f',*v.uv))
 for m in o.data.materials:
  h.update(m.name.encode())
  if m.node_tree:
   for n in m.node_tree.nodes:
    if n.type=='BSDF_PRINCIPLED':
     for k in ['Base Color','Roughness','Metallic','Specular IOR Level']:
      v=n.inputs[k].default_value;h.update(str(tuple(v) if hasattr(v,'__iter__') else v).encode())
    elif n.type=='TEX_IMAGE' and n.image:
     h.update(n.image.name.encode())
     if n.image.packed_file:h.update(n.image.packed_file.data)
 return h.hexdigest()
source=ROOT/'build/male-neutral-b01/bind-005/character_b01.blend';sourcehash=sha(source);assert sourcehash=='a9fb4a469aeec6cf9b82cfb580bafe8d658055c29b8b297925983fda380e126e';base=json.loads((source.parent/'asset-report.json').read_text(encoding='utf-8'));jointcfg=json.loads((ROOT/a.joint_config).read_text(encoding='utf-8'));turncfg=json.loads((ROOT/a.turn_config).read_text(encoding='utf-8'))
bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False);scene=bpy.context.scene;rig=bpy.data.objects['A03_B01_Rig'];root=bpy.data.objects['CHR_PlayerMale_A01'];asset=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('M01_')];assert len(asset)==10
oldnames=[b.name for b in rig.data.bones];oldrest={b.name:b.matrix_local.copy() for b in rig.data.bones};geobefore={o.name:geometry(o) for o in asset};lookbefore={o.name:appearance(o) for o in asset};rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();correction=apply(rig,asset,jointcfg);supports=correction['supports'];rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
assert all(max(abs(rest[n][r][c]-oldrest[n][r][c]) for r in range(4) for c in range(4))<1e-7 for n in oldnames)
# Evaluate the preserved B01 animation, then alter only turn legs and support channels.
snapshots={};originals={n:bpy.data.actions[n] for n in ['idle','walk','run','turn']};originalRanges={}
for name,action in originals.items():
 rig.animation_data.action=action;lo,hi=map(int,action.frame_range);originalRanges[name]=[lo,hi];frames=[]
 for f in range(lo,hi+1):
  scene.frame_set(f);bpy.context.view_layer.update();mats={n:rig.pose.bones[n].matrix.copy() for n in oldnames}
  if name=='turn':mats=apply_turn(mats,(f-lo)/(hi-lo),rest,turncfg)
  update_support_matrices(mats,rest,supports);frames.append((f,mats))
 snapshots[name]=frames
rig.animation_data.action=None
for track in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(track)
for action in originals.values():bpy.data.actions.remove(action)
# Existing52parents precede new supportchildren; all runtime pose behavior is baked TRS.
boneorder=oldnames+[s['bone'] for s in supports];actions={}
for name,frames in snapshots.items():
 ac=bpy.data.actions.new(name);rig.animation_data.action=ac
 for frame,mats in frames:
  scene.frame_set(frame)
  for n in boneorder:
   pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.matrix=mats[n];bpy.context.view_layer.update()
   for path in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=path,frame=frame,group=n)
 for fc in ac.fcurves:
  for key in fc.keyframe_points:key.interpolation='LINEAR'
 ac.use_fake_user=True;actions[name]=ac
rig.animation_data.action=None
for ac in actions.values():
 track=rig.animation_data.nla_tracks.new();track.name=ac.name;strip=track.strips.new(ac.name,1,ac);strip.action_frame_start=ac.frame_range[0];strip.action_frame_end=ac.frame_range[1];track.mute=True
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
scene.frame_set(1);bpy.context.view_layer.update();assert geobefore=={o.name:geometry(o) for o in asset};assert lookbefore=={o.name:appearance(o) for o in asset};dg=bpy.context.evaluated_depsgraph_get();resterror={}
for o in asset:
 ev=o.evaluated_get(dg);me=ev.to_mesh();err=max((v.co-me.vertices[i].co).length for i,v in enumerate(o.data.vertices));resterror[o.name]=err;ev.to_mesh_clear();assert err<1e-5,(o.name,err)
root['phase']='B02 bounded local corrective pass';root['rigReuse']='B01 52-joint adapter plus limited baked support joints';rig['supportNote']='Half-angle supports baked in supplied clips; future animations must bake corresponding support channels. No runtime driver or Humanoid support automation.'
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);rig.select_set(True)
for o in asset:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(out/'chr_player_male_poc_001.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_slide_to_zero=True,export_nla_strips=True,export_force_sampling=True,export_frame_range=False,export_skins=True,export_def_bones=False,export_morph=False,export_cameras=False,export_lights=False,export_influence_nb=4)
rig.animation_data.action=actions['idle'];scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'character_b02.blend'))
report={'assetId':base['assetId'],'phase':'B02','sourceB01BlendSha256':sourcehash,'sourceB01GlbSha256':sha(source.parent/'chr_player_male_poc_001.glb'),'triangles':base['triangles'],'meshCount':10,'materialCount':9,'bones':len(rig.data.bones),'baseBones':52,'supportJoints':supports,'correction':correction,'jointConfig':jointcfg,'turnConfig':turncfg,'geometryHashes':geobefore,'appearanceHashes':lookbefore,'approvedA03RawGeometryAndAppearanceUnchanged':True,'baseRestBonesUnchanged':True,'restSkinningMaxErrorMeters':resterror,'clips':[{'name':n,'fps':24,'durationSeconds':(frames[-1][0]-frames[0][0])/24,'frames':len(frames)-1,'loop':n!='turn'} for n,frames in snapshots.items()],'sourceEmbeddedCodeExecutedOrDelivered':False,'license':'CC-BY-4.0','credit':'Snow Rig (CC) Blender Foundation | studio.blender.org','limitations':['No Humanoid/facial/wardrobe/game integration certification','Support poses are baked for supplied clips only; new clips/retargeting need correct support baking','Motion/visual approval depends on actual matched comparison and contact tests']};dump(out/'asset-report.json',report);assert sha(source)==sourcehash;print(json.dumps({'output':str(out),'bones':report['bones'],'triangles':report['triangles'],'clips':report['clips'],'geometryAndLookUnchanged':True}),flush=True)
