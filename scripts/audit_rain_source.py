"""Read-only Rain inventory; never run embedded code or save the source."""
import argparse,hashlib,json,sys,re
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);(out/'texts').mkdir()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=sha(source)
bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
def props(x):return {k:str(x[k])[:2000] for k in x.keys() if k!='_RNA_UI'}
def meta(x):
 m=getattr(x,'asset_data',None)
 return {k:getattr(m,k,None) for k in ['author','description','copyright','license']} if m else None
meshes=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 m=o.data;m.calc_loop_triangles();pp=[o.matrix_world@v.co for v in m.vertices]
 meshes.append({'name':o.name,'vertices':len(m.vertices),'rawTriangles':len(m.loop_triangles),'dimensions':list(o.dimensions),'location':list(o.location),'scale':list(o.scale),'parent':o.parent.name if o.parent else None,
  'bounds':{'min':[min(p[k] for p in pp) for k in range(3)],'max':[max(p[k] for p in pp) for k in range(3)]} if pp else None,
  'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hidden':o.hide_get(),'materials':[m.name if m else None for m in m.materials],
  'modifiers':[{'name':x.name,'type':x.type,'viewport':x.show_viewport,'render':x.show_render,**({'levels':x.levels,'renderLevels':x.render_levels} if x.type=='SUBSURF' else {}),**({'object':x.object.name if x.object else None} if x.type=='ARMATURE' else {})} for x in o.modifiers],
  'uv':[{'name':u.name,'activeRender':u.active_render} for u in m.uv_layers],
  'shapeKeys':{k.name:k.value for k in m.shape_keys.key_blocks} if m.shape_keys else {},'properties':props(o),'assetMetadata':meta(o)})
texts=[]
for t in bpy.data.texts:
 data=t.as_string();name=re.sub('[^a-zA-Z0-9_.-]','_',t.name)
 (out/'texts'/(name+'.txt')).write_bytes(data.encode('utf8'))
 texts.append({'name':t.name,'bytes':len(data.encode()),'sha256':hashlib.sha256(data.encode()).hexdigest(),'useModule':t.use_module,
  'licenceLines':[line for line in data.splitlines() if any(k in line.lower() for k in ['licen','copyright','cc-by','creative commons','blender foundation','gpl'])][:50]})
devices=[]
try:
 pref=bpy.context.preferences.addons['cycles'].preferences
 for typ in ['HIP','CUDA','OPTIX']:
  try:devices.extend([{'name':d.name,'type':d.type,'probe':typ} for d in pref.get_devices_for_type(typ)])
  except Exception as e:devices.append({'probe':typ,'error':str(e)[:150]})
except Exception as e:devices.append({'error':str(e)})
report={'sourceFile':source.name,'sha256':before,'blender':bpy.app.version_string,'buildHash':bpy.app.build_hash.decode(),'python':sys.version,'autoexecEnabled':bpy.context.preferences.filepaths.use_scripts_auto_execute,'devicesEnumerated':devices,
 'scene':{'name':bpy.context.scene.name,'frame':bpy.context.scene.frame_current,'unitScale':bpy.context.scene.unit_settings.scale_length},'meshes':meshes,'texts':texts,
 'collections':[{'name':c.name,'properties':props(c),'metadata':meta(c),'hideRender':c.hide_render,'hideViewport':c.hide_viewport} for c in bpy.data.collections],
 'armatures':[{'name':o.name,'properties':props(o),'dataProperties':props(o.data),'posePosition':o.data.pose_position,'bones':len(o.data.bones),'worldMatrix':[list(r) for r in o.matrix_world]} for o in bpy.data.objects if o.type=='ARMATURE'],
 'materials':[{'name':m.name,'properties':props(m),'nodes':[{'name':n.name,'type':n.type,**({'image':n.image.name if n.image else None} if n.type=='TEX_IMAGE' else {})} for n in m.node_tree.nodes] if m.use_nodes else []} for m in bpy.data.materials],
 'images':[{'name':i.name,'source':i.source,'path':i.filepath,'size':list(i.size),'packed':bool(i.packed_file),'tiles':[t.number for t in i.tiles] if i.source=='TILED' else []} for i in bpy.data.images]}
assert sha(source)==before;report['sourcePreserved']=True
(out/'source.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({'meshes':len(meshes),'texts':texts,'armatures':report['armatures'],'meshSummary':[{k:m[k] for k in ['name','vertices','rawTriangles','bounds','materials','modifiers']} for m in meshes if not m['name'].startswith('WGT')],'sourcePreserved':True},indent=2))
