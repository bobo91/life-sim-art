"""One static visual refinement of the preserved Rain Ava v0.1 authoring copy."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from ava_rain_tools import sha,write,render
from build_ava_rain import metrics,surface_normals
from ava_rain_outfit import apply
from refine_ava_rain_face import refine as face

def fingerprint(o):
    import struct
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--before',required=True);p.add_argument('--metadata',required=True);p.add_argument('--native-edits',required=True);p.add_argument('--source-static',required=True);p.add_argument('--out',required=True);p.add_argument('--face-only',action='store_true');p.add_argument('--samples',type=int,default=32);p.add_argument('--views',default='all');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    before=Path(a.before).resolve();original=sha(before);out=Path(a.out).resolve();assert not out.exists();out.mkdir(parents=True);(out/'renders').mkdir();meta=json.loads(Path(a.metadata).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(before),load_ui=False,use_scripts=False);s=bpy.context.scene;s.cycles.samples=a.samples
    root=bpy.data.objects['CHR_AvaMorgan_Rain_V01'];objects=[o for o in s.objects if o.type=='MESH' and o.parent==root];body=bpy.data.objects['Rain_body_nomask'];protected=fingerprint(body);eyes=fingerprint(bpy.data.objects['Rain_eyes'])
    changes=[face(objects,meta,a.native_edits,Path(a.source_static).resolve())]
    if not a.face_only:
        from refine_ava_rain_clothes import refine as clothes
        from refine_ava_rain_hair import refine as hair
        changes.append(clothes(objects,meta));result=hair(objects,meta,Path(a.source_static).resolve());objects=result['objects'];changes.append(result['changes'])
    assert fingerprint(body)==protected and fingerprint(bpy.data.objects['Rain_eyes'])==eyes
    root['version']='rain-visual-v0.2';root['scope']='Final static appearance refinement; owner GO/NO-GO pending';root['sourceUrl']='https://studio.blender.org/characters/rain/v3/';root['licenceUrl']='https://creativecommons.org/licenses/by/4.0/';root['modifications']='Adult face/lid/lip/jaw edits; wrapped bun; fitted knit/canvas garments; static only'
    normals=surface_normals(objects);bpy.context.view_layer.update();high=metrics(objects);body_preserved=fingerprint(body)==protected
    # The lower, tucked bun changes the depth bounds. Normalize the asset root
    # by translation only; authored body/neck vertices and scale stay intact.
    root.location.x=-(min(m['min'][0] for m in high)+max(m['max'][0] for m in high))/2
    root.location.y=-(min(m['min'][1] for m in high)+max(m['max'][1] for m in high))/2
    pivot=list(root.location);bpy.context.view_layer.update();high=metrics(objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'character_high.blend'))
    # Reuse the preceding delivery's single static reduction pass. No new LOD,
    # optimiser or performance work; retain extra geometry for the wrapped bun.
    targets={'Rain_head':8700,'Rain_eyes':1600,'Rain_eyebrows':400,'Rain_eyelashes':472,'Rain_hair_main':3000,'Ava_LooseBun_FromRainPonytail':800,'Ava_LooseBun_FromRainPonytail_Refined':2400,'Ava_BunTuckedCentre_FromRainPonytail':600,'Rain_hair_strand':500,'Ava_RightFramingStrand':500,'Rain_hairband':150,'Rain_body_nomask':3000,'Ava_CreamTop_RainSurface':2400,'Rain_jeans':3300,'Rain_shoes':2200,'Ava_FittedCafeApron':1300,'Ava_ApronPocket':200,'Ava_ApronTie':150}
    for o in objects:
        o.data.calc_loop_triangles();n=len(o.data.loop_triangles);target=targets.get(o.name,150 if 'RolledSleeve' in o.name else 120)
        if n>target:apply(o,'DECIMATE',ratio=target/n,use_collapse_triangulate=True)
        for poly in o.data.polygons:poly.use_smooth=True
    normals=surface_normals(objects);final_metrics=metrics(objects)
    focus=Vector((0,meta['offset'][1]*meta['scale'],1.477*meta['scale']))+root.location;views=[('front','full',0),('side','full',90),('back','full',180),('three_quarter','three',35),('face_front','face',0),('face_profile','face',90),('face_three_quarter','face',35),('hair_rear_three_quarter','face',145),('clothes_detail','face',35)]
    rendered=[]
    for name,kind,az in views:
        if a.views=='all' or name in a.views.split(','):rendered.append(render(s.camera,out/'renders',name,kind,az,focus=Vector((0,0,1.13))+root.location if name=='clothes_detail' else focus if kind=='face' else Vector((0,-.02,.86))+root.location,scale=1.05 if name=='clothes_detail' else None))
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'character.blend'))
    write(out/'report.json',{'assetId':'chr_npc_ava_morgan_001','version':'rain-visual-v0.2','beforeAuthoringSha256':original,'scale':meta['scale'],'offset':meta['offset'],'pivotTranslationMetres':pivot,'changes':changes,'triangleCount':sum(m['triangles'] for m in final_metrics),'materialCount':len({m for o in objects for m in o.data.materials}),'meshes':final_metrics,'highMeshes':high,'flatNormalCorrections':normals,'bodyVerticesUnchangedByArtistEdits':body_preserved,'eyeGlobesUnchangedByArtistEdits':True,'renderViews':rendered,'approval':'pending final visual owner GO/NO-GO'})
    assert sha(before)==original;print(json.dumps({'out':str(out),'triangles':sum(m['triangles'] for m in final_metrics),'bodyUnchangedByArtistEdits':body_preserved}))

if __name__=='__main__':main()
