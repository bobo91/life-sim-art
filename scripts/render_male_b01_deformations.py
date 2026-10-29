"""Actual B01 close-up deformation proof; independent copies, never saves A03."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector,Matrix
r=Path.cwd();out=r/'build/male-neutral-b01/deformation-review-001';out.mkdir(exist_ok=False);bpy.ops.wm.open_mainfile(filepath=str(r/'build/male-neutral-b01/bind-005/character_b01.blend'),load_ui=False,use_scripts=False);sc=bpy.context.scene;rig=bpy.data.objects['A03_B01_Rig'];camera=sc.camera;sc.cycles.samples=12;sc.cycles.use_denoising=True;sc.render.resolution_x=sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.render.threads_mode='FIXED';sc.render.threads=6
views=[]
def capture(name,target,size,offset=Vector((.7,-1,.5))):
 camera.data.type='ORTHO';camera.data.ortho_scale=size;camera.location=target+offset;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);views.append({'name':name,'focus':list(target),'orthoScale':size})
# Actual selected locomotion pose, not a sculpted or edited mesh.
rig.animation_data.action=bpy.data.actions['run'];sc.frame_set(7);bpy.context.view_layer.update();capture('run_front',Vector((0,0,.85)),2.05,Vector((0,-3,.08)));capture('run_shoulder_elbow',rig.pose.bones['LowerArm.L'].matrix.translation,.48);capture('run_hand',(rig.pose.bones['Hand.L'].matrix.translation+rig.pose.bones['Middle2.L'].matrix.translation)*.5,.30);capture('run_knee',rig.pose.bones['LowerLeg.L'].matrix.translation,.48)
# One bounded bend stress pose: existing bones/weights, no corrective sculpt.
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
# 90-degree elbow bend with upper arm in original horizontal bind orientation.
pb=rig.pose.bones['LowerArm.L'];m=Matrix.Rotation(math.radians(-90),4,'Z')@rest[pb.name].to_3x3().to_4x4();m.translation=rest[pb.name].translation;pb.matrix=m;bpy.context.view_layer.update()
# 45-degree wrist and 60-degree finger curl stress are deliberately beyond idle.
pb=rig.pose.bones['Hand.L'];pb.rotation_mode='XYZ';pb.rotation_euler.x=math.radians(45)
for finger in ['Index','Middle','Ring','Pinky']:
 for j in range(1,4):
  pb=rig.pose.bones[finger+str(j)+'.L'];pb.rotation_mode='XYZ';pb.rotation_euler.x=math.radians(60)
bpy.context.view_layer.update();capture('stress_elbow90',rig.pose.bones['LowerArm.L'].matrix.translation,.48);capture('stress_wrist45_fingers60',(rig.pose.bones['Hand.L'].matrix.translation+rig.pose.bones['Middle2.L'].matrix.translation)*.5,.28)
# Left knee stress90deg; useful for trouser simplification collapse inspection.
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
pb=rig.pose.bones['LowerLeg.L'];m=Matrix.Rotation(math.radians(-90),4,'X')@rest[pb.name].to_3x3().to_4x4();m.translation=rest[pb.name].translation;pb.matrix=m;bpy.context.view_layer.update();capture('stress_knee90',rig.pose.bones['LowerLeg.L'].matrix.translation,.58)
(out/'metadata.json').write_bytes((json.dumps({'views':views,'engine':'Cycles CPU 12samples','source':'bind-005/character_b01.blend','stressPoseOnly':'Separate unsaved test pose, not shipped animation or edited mesh','faceAndSourceMeshesUnchanged':True},indent=2)+'\n').encode());print('DEFORMATION_REVIEW_RENDERED',len(views),flush=True)
