"""Small static head review: same-camera A03, normal game view, source and GLB.

No rigging, actions, morph production, Unity import or game repository access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy

sys.path.insert(0,str(Path(__file__).parent))
from ava_rain_tools import sha,render,write


def geometry(objects):
    digest=hashlib.sha256()
    for obj in sorted(objects,key=lambda o:o.name):
        digest.update(obj.name.encode())
        for v in obj.data.vertices:digest.update(struct.pack('<3f',*(obj.matrix_world@v.co)))
    return digest.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--a03',required=True);p.add_argument('--samples',type=int,default=48)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.candidate).resolve();ref=Path(a.a03).resolve()
    expected='dcd7681255f49fa704844492b0ffc6964e434ccb4ae59aaba7788b0af56ffd90';assert sha(ref)==expected
    src=out/'ava_b_head_authoring.blend';src_sha=sha(src)
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
    scene=bpy.context.scene;scene.cycles.samples=a.samples;cam=scene.camera
    root=bpy.data.objects['AVA_B_HEAD_REVIEW_V01'];all_meshes=[o for o in scene.objects if o.type=='MESH' and o.parent==root]
    before_geometry=geometry(all_meshes)
    # Purge orphan source payload. Keep only materials/images used by the
    # actual authoring objects; do not ship native embedded software or 4K maps.
    for _ in range(3):
        for datablocks in [bpy.data.meshes,bpy.data.materials,bpy.data.node_groups,bpy.data.images]:
            for block in list(datablocks):
                if block.users==0:datablocks.remove(block)
    images=[]
    for image in bpy.data.images:
        if image.users and image.source!='TILED' and image.type!='RENDER_RESULT':
            image.pack();images.append({'name':image.name,'size':list(image.size)})
    assert not bpy.data.armatures and not bpy.data.actions and not bpy.data.texts
    canonical=out/'ava_b_head_review.blend';bpy.ops.wm.save_as_mainfile(filepath=str(canonical))
    # Head-only disposable export. Native edit cages remain unchanged.
    selected=[o for o in all_meshes if o.name!='AvaB_ContinuousSkin_Preview' and not o.name.startswith(('Rain_body_nomask','Rain_top','Rain_jeans','Rain_shoes'))]
    export_objects=[]
    for o in selected:
        c=o.copy();c.data=o.data.copy();scene.collection.objects.link(c);c.parent=None;export_objects.append(c)
        # Translate prototype feather opacity into core glTF vertex RGBA.
        opacity=c.data.attributes.get('ava_b_brow_opacity')
        if opacity:
            original=c.data.materials[0];s=next(n for n in original.node_tree.nodes if n.type=='BSDF_PRINCIPLED');color=s.inputs['Base Color'].default_value
            attr=c.data.color_attributes.new(name='BrowRGBA',type='FLOAT_COLOR',domain='POINT')
            for v,datum in zip(c.data.vertices,attr.data):datum.color=(*color[:3],opacity.data[v.index].value)
            mat=bpy.data.materials.new('ReviewExport_BrowFeather');mat.use_nodes=True
            shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');shader.inputs['Roughness'].default_value=.86
            vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name=attr.name
            mat.node_tree.links.new(vc.outputs['Color'],shader.inputs['Base Color']);mat.node_tree.links.new(vc.outputs['Alpha'],shader.inputs['Alpha'])
            prop=mat.bl_rna.properties.get('surface_render_method')
            if prop and 'DITHERED' in {e.identifier for e in prop.enum_items}:mat.surface_render_method='DITHERED'
            c.data.materials.clear();c.data.materials.append(mat)
    eroot=bpy.data.objects.new('AVA_B_HEAD_REVIEW_ONLY',None);scene.collection.objects.link(eroot)
    for key in root.keys():eroot[key]=root[key]
    eroot['notProductionAsset']=True
    for obj in export_objects:obj.parent=eroot;obj.hide_render=False;obj.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT');eroot.select_set(True)
    for obj in export_objects:obj.select_set(True)
    glb=out/'ava_b_head_review_only.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False)
    for obj in export_objects+[eroot]:bpy.data.objects.remove(obj,do_unlink=True)
    raw=glb.read_bytes();size,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+size]);assert kind==0x4e4f534a
    assert not doc.get('skins') and not doc.get('animations')
    export_triangles=sum(doc['accessors'][p['indices']]['count']//3 for mesh in doc['meshes'] for p in mesh['primitives'])
    # A03 is rendered at the SAME location, camera and studio lights as Ava.
    # Separate frames are composed side by side without head-size normalization.
    views=[render(cam,out/'renders','comparison_ava_three_quarter','face',35,focus=(0,-.028,1.50),scale=.70)]
    visibility={o:o.hide_render for o in all_meshes}
    for o in all_meshes:o.hide_render=True
    with bpy.data.libraries.load(str(ref),link=False) as (source,target):target.objects=[n for n in source.objects if n.startswith('M01_')]
    refs=[]
    for obj in target.objects:
        if obj and obj.type=='MESH':
            world=obj.matrix_world.copy();obj.parent=None;obj.matrix_world=world;scene.collection.objects.link(obj);refs.append(obj)
    assert refs
    reference_geometry=geometry(refs)
    for name,az in [('a03_face_front',0),('a03_face_three_quarter',35)]:views.append(render(cam,out/'renders',name,'face',az,focus=(0,-.028,1.50),scale=.70))
    assert geometry(refs)==reference_geometry
    for obj in refs:bpy.data.objects.remove(obj,do_unlink=True)
    for obj,value in visibility.items():obj.hide_render=value
    views.append(render(cam,out/'renders','normal_game_camera','game',0))
    assert geometry(all_meshes)==before_geometry and sha(ref)==expected and sha(src)==src_sha
    write(out/'review-report.json',{'canonicalBlend':canonical.name,'canonicalSha256':sha(canonical),'headOnlyReviewGlb':glb.name,'glbSha256':sha(glb),'glbTriangles':export_triangles,'glbSkins':len(doc.get('skins',[])),'glbAnimations':len(doc.get('animations',[])),'glbIsFinalGameAsset':False,'sourceAndA03Preserved':True,'geometryPreservedDuringReview':True,'a03Sha256':expected,'a03Comparison':'Same camera, location, metre scale and studio lights; separately rendered and uniformly composed, no head normalization','images':images,'gameCamera':{'distanceMetres':16,'elevationDegrees':50,'verticalFovDegrees':40,'resolution':[1280,720],'pose':'Unchanged native Rain rest/T pose, unfinished context outfit'},'neckPreview':'Original edit cages preserved; disposable continuous-skin preview joins the approximately13um source-shell seam at20um weld tolerance','renders':views,'unityTested':False,'approval':'pending separate visual GO/NO-GO'})
    print(json.dumps({'reviewBlendSha256':sha(canonical),'headReviewTriangles':export_triangles,'a03Unchanged':True,'images':images}))


if __name__=='__main__':main()
