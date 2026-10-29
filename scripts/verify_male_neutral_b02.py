"""Actual saved Blender/GLB skin trajectory comparison for the bounded B02 proof."""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);p=Path.cwd()/args.input;out=Path.cwd()/args.out;out.mkdir(exist_ok=False)
def points():
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();res=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or (not o.name.startswith('M01_')):continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();res.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
 return res
expected=json.loads((p/'asset-report.json').read_text(encoding='utf-8'));bones_expected=expected['bones'];bpy.ops.wm.open_mainfile(filepath=str(p/'character_b02.blend'),load_ui=False,use_scripts=False);rig=bpy.data.objects['A03_B01_Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
base=points();ref={};ranges={};acts={a.name:a for a in bpy.data.actions}
for name in ['idle','walk','run','turn']:
 ac=acts[name];lo,hi=ac.frame_range;ranges[name]=[float(lo),float(hi)];rig.animation_data.action=ac;ref[name]=[]
 for u in [0,.25,.5,.75,1]:
  bpy.context.scene.frame_set(int(lo+(hi-lo)*u),subframe=(lo+(hi-lo)*u)%1);ref[name].append(points())
 rig.animation_data.action=None
assert len(bpy.data.texts)==0 and len(rig.data.bones)==bones_expected
weights={}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or not o.name.startswith('M01_'):continue
 sums=[sum(g.weight for g in v.groups) for v in o.data.vertices];count=max(len(v.groups) for v in o.data.vertices);assert max(abs(s-1) for s in sums)<1e-5 and count<=4;weights[o.name]={'maxInfluences':count,'maxWeightError':max(abs(s-1) for s in sums)}
# Fresh importer, not resampling the authoring file and calling it a roundtrip.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'chr_player_male_poc_001.glb'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');print('IMPORTED ACTIONS',[(a.name,list(a.frame_range)) for a in bpy.data.actions],flush=True)
assert len(rig.data.bones)==bones_expected
res={}
for name in ref:
 ac=next(a for a in bpy.data.actions if a.name.lower().startswith(name));rig.animation_data_create();rig.animation_data.action=ac
 if hasattr(ac,'slots') and len(ac.slots):rig.animation_data.action_slot=ac.slots[0]
 lo,hi=ac.frame_range;errors=[]
 for u,expected in zip([0,.25,.5,.75,1],ref[name]):
  f=lo+(hi-lo)*u;bpy.context.scene.frame_set(int(f),subframe=f%1);actual=points();assert len(actual)>0
  def error(a,b):
   kd=KDTree(len(b))
   for i,point in enumerate(b):kd.insert(point,i)
   kd.balance();return max(kd.find(point)[2] for point in a)
  err=max(error(expected,actual),error(actual,expected));errors.append(err)
 res[name]={'importedAction':ac.name,'sourceFrameRange':ranges[name],'importedFrameRange':[float(lo),float(hi)],'bidirectionalNearestSurfaceVertexMaxErrorsMeters':errors,'passed':max(errors)<.0001}
 rig.animation_data.action=None
result={'schema':'male-b02-blender-motion-roundtrip-1','sourceSavedReopened':True,'importedBones':len(rig.data.bones),'clips':res,'allMotionPosePointcloudsMatchWithin0_1mm':all(x['passed'] for x in res.values()),'weights':weights,'limitations':['Pointcloud comparison samples five poses per clip, not all animation times or full self intersection.','No Humanoid controller or facial keys tested.']}
(out/'report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2));assert result['allMotionPosePointcloudsMatchWithin0_1mm']
