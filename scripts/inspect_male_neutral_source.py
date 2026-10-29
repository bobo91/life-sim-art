"""Inspect only the approved Snow source with auto-execution disabled."""
import bpy, json, sys, hashlib, re
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:]
source=Path(args[0]).resolve(); out=Path(args[1]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.use_preferences_save=False
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
texts=[]
for t in bpy.data.texts:
 name=re.sub(r'[^a-zA-Z0-9_.-]','_',t.name)
 data=t.as_string();p=out/'text-blocks'/name;p.parent.mkdir(exist_ok=True);p.write_text(data,encoding='utf-8')
 texts.append({'name':t.name,'file':str(p),'bytes':len(data.encode()),'sha256':hashlib.sha256(data.encode()).hexdigest(),'firstLines':data.splitlines()[:9]})
objects=[]
for o in sorted(bpy.data.objects,key=lambda o:o.name):
 item={'name':o.name,'type':o.type,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'parent':o.parent.name if o.parent else None,'locationWorld':list(o.matrix_world.translation),'scale':list(o.scale)}
 if o.type=='MESH':
  o.data.calc_loop_triangles();item.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),triangles=len(o.data.loop_triangles),materials=[m.name if m else None for m in o.data.materials],shapeKeys=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],modifiers=[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render,'levels':getattr(m,'levels',None),'renderLevels':getattr(m,'render_levels',None),'target':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers])
 if o.type=='ARMATURE':item['bones']=len(o.data.bones)
 objects.append(item)
images=[{'name':i.name,'filepath':i.filepath,'source':i.source,'size':list(i.size),'colorspace':i.colorspace_settings.name,'packed':bool(i.packed_file),'tiles':[t.number for t in i.tiles]} for i in bpy.data.images]
materials=[]
for m in bpy.data.materials:
 materials.append({'name':m.name,'nodes':[{'name':n.name,'type':n.type} for n in m.node_tree.nodes] if m.use_nodes else []})
report={'source':str(source),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'sourceFileVersion':list(bpy.data.version),'autoExecutionDisabled':not bpy.context.preferences.filepaths.use_scripts_auto_execute,'autoexecFailure':bpy.app.autoexec_fail,'autoexecMessage':bpy.app.autoexec_fail_message,'scenes':[s.name for s in bpy.data.scenes],'objects':objects,'images':images,'materials':materials,'texts':texts}
(out/'source-inspection.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'blender':report['blender'],'objects':len(objects),'meshObjects':sum(o['type']=='MESH' for o in objects),'texts':[t['name'] for t in texts],'images':len(images),'autoexecFailure':report['autoexecFailure']}))
