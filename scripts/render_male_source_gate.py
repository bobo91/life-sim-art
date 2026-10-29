"""Unmodified-source geometry presentation; no rig/UI code executed."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];source=Path(args[0]).resolve();out=Path(args[1]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.use_preferences_save=False
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
scene=bpy.context.scene;scene.frame_set(1)
subjects=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('GEO') and not o.hide_render and o.visible_camera and not any(s in o.name for s in ['helper','deformer','_anim'])]
report={'geometryModified':False,'sourceScriptsExecuted':False,'objects':[]}
for o in scene.objects:
 if o.type=='MESH' and o.name.startswith('GEO'):
  report['objects'].append({'name':o.name,'hideRender':o.hide_render,'visibleCamera':o.visible_camera,'visibleGet':o.visible_get(),'collections':[c.name for c in o.users_collection],'objectMaterials':[s.material.name if s.material else None for s in o.material_slots]})
# Keep the source render visibility and deformation settings, adding only review environment.
deps=bpy.context.evaluated_depsgraph_get();points=[]
for o in subjects:
 e=o.evaluated_get(deps);points.extend(e.matrix_world@Vector(c) for c in e.bound_box)
lo=Vector(tuple(min(p[k] for p in points) for k in range(3)));hi=Vector(tuple(max(p[k] for p in points) for k in range(3)));h=hi.z-lo.z;center=(lo+hi)*.5
report['sourceBounds']={'min':list(lo),'max':list(hi),'height':h};report['subjects']=[o.name for o in subjects]
print(json.dumps({'bounds':report['sourceBounds'],'subjects':report['subjects']}),flush=True)
world=bpy.data.worlds.new('WC_SourceReview_World');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.58,.61,.66,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35;scene.world=world
for o in list(scene.objects):
 if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,xyz,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size*h;ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=center+Vector(xyz)*h;aim(ob,center)
area('WC_Key',(-1.5,-2,2.2),500*h*h,.95);area('WC_Fill',(1.8,-.7,1.3),180*h*h,1.25);area('WC_Rim',(1,1.5,2),300*h*h,1)
mat=bpy.data.materials.new('WC_ReviewFloor');mat.use_nodes=True;bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.56,.52,.45,1);bs.inputs['Roughness'].default_value=.9
bpy.ops.mesh.primitive_plane_add(size=h*200,location=(0,0,lo.z-.003));floor=bpy.context.object;floor.name='WC_PresentationFloor_NotAsset';floor.data.materials.append(mat)
camdata=bpy.data.cameras.new('WC_ReviewCamera');cam=bpy.data.objects.new('WC_ReviewCamera',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=h*1.17
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.seed=28102026;scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=768;scene.render.resolution_y=1024;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0;scene.view_settings.gamma=1
for name,azimuth,close in [('three_quarter',35,False),('face_front',0,True)]:
 a=math.radians(azimuth);target=Vector((center.x,center.y,lo.z+h*(.89 if close else .50)));cam.location=target+Vector((math.sin(a)*h*3,-math.cos(a)*h*3,h*(.02 if close else .08)));aim(cam,target);camdata.ortho_scale=h*(.29 if close else 1.17)
 scene.render.resolution_x=960 if close else 768;scene.render.resolution_y=960 if close else 1024
 scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'source-gate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
