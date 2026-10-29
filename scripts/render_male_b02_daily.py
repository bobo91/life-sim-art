"""Matched B01/B02 everyday reach/gesture and correctly directed knee-flex views."""
import bpy,argparse,json,math,sys
from pathlib import Path
from mathutils import Matrix,Vector
r=Path.cwd();sys.path.insert(0,str(r/'scripts'));from male_b02_joint_weights import update_support_matrices
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=r/a.out;assert not out.exists();out.mkdir(parents=True)
records={};reference={};report=json.loads((r/a.input/'asset-report.json').read_text(encoding='utf-8'));supports=report['supportJoints']
for label,file in [('B01',r/'build/male-neutral-b01/bind-005/character_b01.blend'),('B02',r/a.input/'character_b02.blend')]:
 (out/label).mkdir();bpy.ops.wm.open_mainfile(filepath=str(file),load_ui=False,use_scripts=False);sc=bpy.context.scene;rig=bpy.data.objects['A03_B01_Rig'];rest={b.name:b.matrix_local.copy() for b in rig.data.bones};base_names=[b.name for b in rig.data.bones if not b.name.startswith('B02_')];rig.animation_data.action=bpy.data.actions['idle'];sc.frame_set(1);bpy.context.view_layer.update();idle={n:rig.pose.bones[n].matrix.copy() for n in base_names};rig.animation_data.action=None;cam=sc.camera;sc.cycles.samples=12;sc.render.threads_mode='FIXED';sc.render.threads=6;sc.render.resolution_percentage=100;sc.render.resolution_x=sc.render.resolution_y=800
 def change(mats,name,rot):
  old=mats[name].copy();new=rot@old.to_3x3().to_4x4();new.translation=old.translation;d=new@old.inverted()
  for n in list(mats):
   b=rig.data.bones[n]
   if n==name or any(p.name==name for p in b.parent_recursive):mats[n]=d@mats[n]
 def capture(name,target,size,offset):
  cam.data.type='ORTHO';cam.data.ortho_scale=size;cam.location=target+offset;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/label/(name+'.png'));bpy.ops.render.render(write_still=True)
 records[label]={}
 for pose in ['reach','gesture','knee_flex90']:
  mats={n:m.copy() for n,m in (rest if pose=='knee_flex90' else idle).items() if n in base_names}
  if pose=='reach':
   change(mats,'UpperArm.L',Matrix.Rotation(math.radians(-45),4,'X'));change(mats,'LowerArm.L',Matrix.Rotation(math.radians(-35),4,'X'));axis=mats['Hand.L'].col[0].to_3d();change(mats,'Hand.L',Matrix.Rotation(math.radians(20),4,axis))
  elif pose=='gesture':
   change(mats,'UpperArm.L',Matrix.Rotation(math.radians(-50),4,'Y'));change(mats,'LowerArm.L',Matrix.Rotation(math.radians(-40),4,'X'))
   for finger in ['Index','Middle','Ring','Pinky']:
    for j in [1,2,3]:
     n=finger+str(j)+'.L';change(mats,n,Matrix.Rotation(math.radians(15),4,mats[n].col[0].to_3d()))
  else:change(mats,'LowerLeg.L',Matrix.Rotation(math.radians(90),4,'X'))
  if label=='B01':reference[pose]={n:m.copy() for n,m in mats.items()}
  delta=max(abs(mats[n][i][j]-reference[pose][n][i][j]) for n in mats for i in range(4) for j in range(4));assert delta<1e-5,(pose,delta)
  for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
  if label=='B02':update_support_matrices(mats,rest,supports)
  for n in base_names+[s['bone'] for s in supports if label=='B02']:
   rig.pose.bones[n].matrix=mats[n];bpy.context.view_layer.update()
  if label=='B01':reference[pose+'_focus']=(mats['Hand.L'].translation+mats['Middle2.L'].translation)*.5
  if pose=='knee_flex90':
   capture(pose,mats['LowerLeg.L'].translation,.58,Vector((.7,-1,.5)))
  else:
   capture(pose+'_full',Vector((0,0,.87)),2.10,Vector((1.2,-2,.15)));capture(pose+'_hand',reference[pose+'_focus'],.32,Vector((.7,-1,.5)))
  records[label][pose]={'majorBoneMatrixDifferenceFromBaselineMax':delta,'samePoseAndCamera':True,'supportsEvaluated':label=='B02','normalKneeFlexion':pose=='knee_flex90'}
(out/'report.json').write_bytes((json.dumps({'schema':'male-b02-everyday-render-1','poses':records,'engine':'Cycles CPU12samples','kneeDirectionCorrection':'Positive90worldX is physiologicalflexion; B01 oldnegative90stresswas hyperextension. Bothversionshereusecorrectpositive90.','noSourceSaved':True,'limits':'Unsaved diagnostic poses, not extra gameplayclips or fullmovementrange certification'},indent=2)+'\n').encode());print('MATCHED_EVERYDAY_RENDERED',flush=True)
