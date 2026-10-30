"""Export one static Rain-derived candidate and render its review context.

No source rig, source scripts, A03 modifications or Unity integration.
"""
import argparse,sys,hashlib,json,math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ava_rain_tools import sha,write,aim,material,linear,render
from art_pipeline.validation import validate_glb

A03_SHA='dcd7681255f49fa704844492b0ffc6964e434ccb4ae59aaba7788b0af56ffd90'

def geometry(objects):
    import struct
    h=hashlib.sha256()
    for o in sorted(objects,key=lambda o:o.name):
        h.update(o.name.encode())
        for v in o.data.vertices:h.update(struct.pack('<3f',*(o.matrix_world@v.co)))
        for p in o.data.polygons:h.update(struct.pack('<%dI'%len(p.vertices),*p.vertices))
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--a03',required=True);ap.add_argument('--samples',type=int,default=36);ap.add_argument('--export-only',action='store_true');ap.add_argument('--max-triangles',type=int,default=30000);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    out=Path(a.candidate).resolve();source=out/'character.blend';before=sha(source);ref=Path(a.a03).resolve();assert sha(ref)==A03_SHA
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    s=bpy.context.scene;s.cycles.samples=a.samples;cam=s.camera
    root=bpy.data.objects['CHR_AvaMorgan_Rain_V01'];objects=[o for o in s.objects if o.type=='MESH' and o.parent==root];assert objects
    assert not bpy.data.armatures and not bpy.data.actions and not bpy.data.texts
    drivers=[d.name for collection in [bpy.data.objects,bpy.data.meshes,bpy.data.shape_keys,bpy.data.materials,bpy.data.node_groups,bpy.data.scenes] for d in collection if getattr(d,'animation_data',None) and d.animation_data.drivers]
    assert not drivers,drivers
    if not a.export_only:render(cam,out/'renders','isometric','isometric',45)
    bpy.context.view_layer.update();original=geometry(objects)
    # Consolidate only disposable export copies, by material, to eight draw meshes.
    eroot=bpy.data.objects.new('CHR_AvaMorgan_Rain_Export',None);s.collection.objects.link(eroot)
    eroot.matrix_world=root.matrix_world.copy()
    for k in root.keys():eroot[k]=root[k]
    grouped={}
    for o in objects:
        key=o.data.materials[0].name;grouped.setdefault(key,[])
        c=o.copy();c.data=o.data.copy();s.collection.objects.link(c);c.parent=eroot
        # Join must keep each garment's active UVs, including newly mapped cuffs.
        # Different layer names otherwise create empty UVs on part of a group.
        if c.data.uv_layers.active:c.data.uv_layers.active.name='AvaExportUV'
        grouped[key].append(c)
    exported=[]
    for mat,group in grouped.items():
        bpy.ops.object.select_all(action='DESELECT')
        for c in group:c.select_set(True)
        bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join();ob=group[0];ob.name=mat.replace('Ava_','AvaMesh_');exported.append(ob)
    bpy.ops.object.select_all(action='DESELECT');eroot.select_set(True)
    for o in exported:o.select_set(True)
    path=out/'chr_npc_ava_morgan_001.glb'
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False)
    for o in exported+[eroot]:bpy.data.objects.remove(o,do_unlink=True)
    points=[o.matrix_world@v.co for o in objects for v in o.data.vertices];lo=[min(p[k] for p in points) for k in range(3)];hi=[max(p[k] for p in points) for k in range(3)]
    validation=validate_glb(path,[hi[0]-lo[0],hi[2]-lo[2],hi[1]-lo[1]],a.max_triangles)
    write(out/'glb-validation.json',validation)
    if a.export_only:
        assert sha(source)==before and sha(ref)==A03_SHA;return
    # Reimport the actual export once, and inspect its core-PBR appearance.
    old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));imported=set(bpy.data.objects)-old
    for o in objects:o.hide_render=True
    render(cam,out/'renders','glb_roundtrip_front','full',0)
    report=json.loads((out/'report.json').read_text());offset=report['offset'];sc=report['scale']
    render(cam,out/'renders','glb_roundtrip_face','face',35,focus=(0,offset[1]*sc,1.477*sc))
    for o in imported:bpy.data.objects.remove(o,do_unlink=True)
    for o in objects:o.hide_render=False
    # Append meshes only from the unchanged approved STATIC A03 source.
    with bpy.data.libraries.load(str(ref),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('M01_')]
    refs=[]
    for o in dst.objects:
        if o and o.type=='MESH':s.collection.objects.link(o);o.parent=None;refs.append(o)
    bpy.context.view_layer.update();ref_geometry=geometry(refs)
    stored={o:o.location.copy() for o in objects+refs}
    for o in objects:o.location.x=-1.00
    for o in refs:o.location.x=1.00
    bpy.context.view_layer.update();cam.data.type='ORTHO';cam.data.ortho_scale=4.15;cam.data.sensor_fit='AUTO';cam.location=(0,-6,.90);aim(cam,(0,0,.90));s.render.resolution_x=1800;s.render.resolution_y=1050;s.render.filepath=str(out/'renders'/'ava_a03_same_scale.png');bpy.ops.render.render(write_still=True)
    for o,loc in stored.items():o.location=loc
    bpy.context.view_layer.update();assert geometry(refs)==ref_geometry;assert geometry(objects)==original
    for o in refs:bpy.data.objects.remove(o,do_unlink=True)
    # A compact cafe LIGHTING PROXY, not a reconstruction or Unity screenshot.
    for o in s.objects:
        if o.type=='LIGHT':o.hide_render=True
    # Use the authored game ambient RGB swatch as Blender world color. This is
    # a readable material proxy, not a photometric Unity-to-Cycles conversion.
    bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.52,.57,.61,1);bg.inputs['Strength'].default_value=1
    floor=bpy.data.objects.get('ReviewFloor');floor.data.materials.clear();floor.data.materials.append(material('CafeProxy_Paving',(.57,.55,.50),.91))
    def cube(name,loc,scale,mat):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat);return o
    wall=material('CafeProxy_CreamWall',(.74,.71,.63),.88);wood=material('CafeProxy_Wood',(.34,.22,.13),.81)
    cube('LIGHTING_PROXY_BackWall',(0,2,1.5),(8,.12,3),wall)
    cube('LIGHTING_PROXY_Counter',(2.0,.1,.45),(1.4,.65,.9),wood)
    cube('LIGHTING_PROXY_CounterTop',(2.0,.1,.92),(1.5,.72,.06),wood)
    sun_data=bpy.data.lights.new('JuniperProxy_Sun','SUN');sun_data.energy=1.2;sun_data.color=(1,.94,.82);sun_data.angle=math.radians(3)
    sun=bpy.data.objects.new(sun_data.name,sun_data);s.collection.objects.link(sun);sun.rotation_euler=Vector((-.3213938048,.5566703992,-.7660444431)).to_track_quat('-Z','Y').to_euler()
    views=[render(cam,out/'renders','game_camera_daylight','game',0)]
    sun.hide_render=True;views.append(render(cam,out/'renders','game_camera_shade','game',0))
    # A close material view is additional evidence, never labelled normal game camera.
    sun.hide_render=False;views.append(render(cam,out/'renders','cafe_material_daylight','three',35))
    sun.hide_render=True;views.append(render(cam,out/'renders','cafe_material_shade','three',35))
    bpy.context.view_layer.update();assert geometry(objects)==original;assert sha(source)==before;assert sha(ref)==A03_SHA
    write(out/'review-report.json',{'sourceSha256':before,'a03Sha256':A03_SHA,'sourceAndA03Preserved':True,'geometryPreservedDuringReview':True,'exportSha256':sha(path),'exportMeshes':len(grouped),'staticOnly':True,'unityTested':False,'gameCamera':{'yawUnity':180,'pitchDegrees':50,'distanceMetres':16,'focusHeightMetres':1,'verticalFovDegrees':40,'nativeResolution':[1280,720]},'lighting':'Blender daylight/ambient-only shade proxy using Juniper sun direction/color/intensity; not photometrically equivalent to Unity','renders':views})
    print(json.dumps({'exportBytes':path.stat().st_size,'exportMeshes':len(grouped),'a03Unchanged':True,'visualApproval':'pending'}))

if __name__=='__main__':main()
