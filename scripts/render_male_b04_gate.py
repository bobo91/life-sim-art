"""Mandatory B04 single-candidate gate: B02/B03/B04,6poses,2sides,2views,16m."""
import bpy,argparse,json,math,sys,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
r=Path.cwd();sys.path.insert(0,str(r/'scripts'))
from male_b02_joint_weights import update_support_matrices
from male_b03_elbow_shape import apply_activation,measure_elbow_bend
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);p.add_argument('--samples',type=int,default=12);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=r/a.out;assert not out.exists();out.mkdir(parents=True)
base=r/'build/male-neutral-b02/delivery-001/character_b02.blend';b03=r/'build/male-neutral-b03/shape-probe-002/candidate.blend';candidate=r/a.candidate;files={'B02':base,'B03':b03,'B04':candidate};hashes={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}
b03report=json.loads((r/'build/male-neutral-b03/shape-probe-002/report.json').read_text(encoding='utf-8'));b03cfg=json.loads((r/'configs/male-neutral-b03-elbow.json').read_text(encoding='utf-8'));supports=json.loads((base.parent/'asset-report.json').read_text(encoding='utf-8'))['supportJoints']
bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(base),load_ui=False,use_scripts=False);rig=bpy.data.objects['A03_B01_Rig'];sc=bpy.context.scene;rest={b.name:b.matrix_local.copy() for b in rig.data.bones};order=list(rest);major=[n for n in order if not n.startswith('B02_')];poses={};angles={}
for name,frame in [('idle',13.0),('walk',7.0),('run25',5.5)]:
 rig.animation_data.action=bpy.data.actions['run' if name=='run25' else name];sc.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update();poses[name]={n:rig.pose.bones[n].matrix.copy() for n in order};angles[name]={s:measure_elbow_bend(rig,s) for s in ['L','R']}
for degrees in [45,90,120]:
 mats={n:poses['run25'][n].copy() for n in major}
 for side in ['L','R']:
  n='LowerArm.'+side;u=mats['UpperArm.'+side].col[1].to_3d().normalized();v=mats[n].col[1].to_3d().normalized();axis=u.cross(v).normalized();desired=Matrix.Rotation(math.radians(degrees),4,axis).to_3x3()@u;q=v.rotation_difference(desired);old=mats[n];new=q.to_matrix().to_4x4()@old.to_3x3().to_4x4();new.translation=old.translation;change=new@old.inverted()
  for child in major:
   if child==n or any(b.name==n for b in rig.data.bones[child].parent_recursive):mats[child]=change@mats[child]
 update_support_matrices(mats,rest,supports);poses['flex'+str(degrees)]=mats
views=[];states={};camera_foci={}
for label,file in files.items():
 (out/label).mkdir();bpy.ops.wm.open_mainfile(filepath=str(file),load_ui=False,use_scripts=False);sc=bpy.context.scene;rig=bpy.data.objects['A03_B01_Rig'];body=bpy.data.objects['M01_body'];cam=sc.camera;assert len(rig.data.bones)==58;rig.animation_data.action=None;sc.cycles.device='CPU';sc.cycles.samples=a.samples;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=6;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';states[label]={}
 for name,mats in poses.items():
  for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
  for n in major+[s['bone'] for s in supports]:rig.pose.bones[n].matrix=mats[n];bpy.context.view_layer.update()
  weights=apply_activation(rig,body,b03report['corrective'],b03cfg) if label=='B03' else None;bpy.context.view_layer.update();states[label][name]={'elbowAngles':{s:measure_elbow_bend(rig,s) for s in ['L','R']},'B03Weights':weights}
  for side in ['L','R']:
   key=name+'_'+side
   if label=='B02':camera_foci[key]=rig.matrix_world@rig.pose.bones['LowerArm.'+side].matrix.translation
   focus=camera_foci[key]
   for angle in ['front','outer']:
    sign=1 if side=='L' else -1;offset=Vector((sign*.55,-1,.25)) if angle=='front' else Vector((sign*1,.20,.18));cam.data.type='ORTHO';cam.data.ortho_scale=.31;cam.location=focus+offset;cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=sc.render.resolution_y=640;filename=name+'_'+side+'_'+angle+'.png';sc.render.filepath=str(out/label/filename);bpy.ops.render.render(write_still=True);views.append({'version':label,'pose':name,'side':side,'angle':angle,'file':label+'/'+filename,'focus':list(focus),'camera':list(cam.location),'orthoScale':.31,'resolution':[640,640]})
 # Exact requested art camera on runreference, no additional body/animation change.
 for n in major+[s['bone'] for s in supports]:rig.pose.bones[n].matrix=poses['run25'][n];bpy.context.view_layer.update()
 if label=='B03':apply_activation(rig,body,b03report['corrective'],b03cfg)
 bpy.context.view_layer.update();focus=Vector((0,0,.875));az=math.radians(35);el=math.radians(50);cam.data.type='PERSP';cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=32;cam.data.lens=32/(2*math.tan(math.radians(40)/2));cam.location=focus+Vector((math.sin(az)*math.cos(el)*16,-math.cos(az)*math.cos(el)*16,math.sin(el)*16));cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.filepath=str(out/label/'game16m.png');bpy.ops.render.render(write_still=True);views.append({'version':label,'pose':'run25','file':label+'/game16m.png','cameraType':'perspective','distanceMeters':(cam.location-focus).length,'elevationDegrees':50,'azimuthDegrees':35,'verticalFovDegrees':40,'resolution':[1280,720],'actualGameWorld':False})
 assert hashlib.sha256(file.read_bytes()).hexdigest()==hashes[label]
result={'schema':'male-b04-mandatory-visual-gate-1','candidateCount':1,'sourceHashes':hashes,'poses':states,'views':views,'render':'ActualCPU Cycles'+str(a.samples)+'samples,sameA03stageworld/lights,commonB02derivedposes/cameratargets, noimage/pose retouch','idleNote':'Actualexistingidleframe13, notsilentlystraightened; measuredanglesincluded. Animationdataunchanged.','angleNote':'Physicaldirection45/90/120intheactualrunhingeplane, upperarmfixed; B03activationevaluatedfromitsoriginalrecipe','gameCamera':'50pitch/16m/40verticalFOV/azimuth35artproxy; notgameproject','exportOrUnityRun':False};(out/'report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print('B04_GATE_RENDERED',len(views),flush=True)
