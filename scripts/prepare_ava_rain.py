"""Extract actual Rain authored meshes to a static, script-free source copy."""
import argparse,sys,hashlib,json
from pathlib import Path
import bpy
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).parent))
from ava_rain_tools import *
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--lids',type=float,default=0);p.add_argument('--smile',type=float,default=0);p.add_argument('--views',default='all');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False);(out/'renders').mkdir()
expected='831ab6d837c679040285862b15dc9ee5180b018442a88aeaf92aaa7509b80258';assert sha(source)==expected
bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
for arm in bpy.data.armatures:arm.pose_position='REST'
for o in bpy.data.objects:
    if o.type=='MESH':
        if o.data.shape_keys:
            o.data.shape_keys.animation_data_clear()
            for k in o.data.shape_keys.key_blocks:k.value=0
            if o.name=='GEO-rain-head':
                for side in ['L','R']:
                    o.data.shape_keys.key_blocks['EyelidsClose.'+side].value=a.lids
                    o.data.shape_keys.key_blocks['Smile.'+side].value=a.smile
        for m in o.modifiers:
            if m.type in ('ARMATURE','LATTICE','CORRECTIVE_SMOOTH','MASK','VERTEX_WEIGHT_MIX','SUBSURF'):m.show_viewport=False;m.show_render=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
names=['body_nomask','head','eyes','eyebrows','eyelashes','hair_main','hair_ponytail','hair_strand','hairband','jeans','top','shoes']
copies=[];mapping=[]
for suffix in names:
    old=bpy.data.objects['GEO-rain-'+suffix];me=bpy.data.meshes.new_from_object(old.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);me.transform(old.matrix_world)
    ob=bpy.data.objects.new('Rain_'+suffix,me);copies.append(ob);ob['rainSourceObject']=old.name
    for poly in me.polygons:poly.use_smooth=True
    mapping.append({'object':ob.name,'source':old.name,'vertices':len(me.vertices)})
new=bpy.data.scenes.new('Ava_Rain_Static_WorkingCopy');bpy.context.window.scene=new
for o in copies:new.collection.objects.link(o)
for scene in list(bpy.data.scenes):
    if scene!=new:bpy.data.scenes.remove(scene)
for o in list(bpy.data.objects):
    if o not in copies:bpy.data.objects.remove(o,do_unlink=True)
for t in list(bpy.data.texts):bpy.data.texts.remove(t)
for arm in list(bpy.data.armatures):bpy.data.armatures.remove(arm)
for act in list(bpy.data.actions):bpy.data.actions.remove(act)
for key in list(bpy.data.shape_keys):
    if key.users==0:bpy.data.shape_keys.remove(key)
# Plain PBR for geometry-first baseline. Source meshes/UVs remain intact.
skin=material('Rain_SourcePreview_Skin',(.68,.45,.31),.7);hair=material('Rain_SourcePreview_Hair',(.19,.10,.055),.8);cream=material('Rain_SourcePreview_Top',(.86,.82,.72),.84);denim=material('Rain_SourcePreview_Denim',(.18,.23,.29),.87);shoe=material('Rain_SourcePreview_Shoe',(.76,.74,.68),.82);eye=material('Rain_SourcePreview_Eyes',(.89,.87,.78),.35)
for o in copies:
    assign(o,skin if o.name in ('Rain_body_nomask','Rain_head') else hair if any(t in o.name for t in ('hair','eyebrow','eyelash')) else denim if 'jeans' in o.name else cream if 'top' in o.name else shoe if 'shoes' in o.name else eye)
cam,lights,bg=studio(out,16)
meta=[]
for name,kind,az in [('front','full',0),('side','full',90),('face_front','face',0),('face_three_quarter','face',35)]:
    if a.views=='all':meta.append(render(cam,out/'renders',name,kind,az,focus=(0,-.03,1.47) if kind=='face' else None))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'static-source.blend'))
assert sha(source)==expected
write(out/'extraction.json',{'sourceSha256':expected,'staticSha256':sha(out/'static-source.blend'),'sourcePreserved':True,'existingStaticShapeValues':{'EyelidsClose.L/R':a.lids,'Smile.L/R':a.smile},'meshMap':mapping,'rigs':len(bpy.data.armatures),'embeddedTexts':len(bpy.data.texts),'views':meta})
print(json.dumps({'meshCount':len(copies),'rigs':len(bpy.data.armatures),'texts':len(bpy.data.texts),'staticSource':str(out/'static-source.blend')}))
