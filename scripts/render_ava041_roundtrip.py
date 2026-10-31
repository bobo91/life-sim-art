"""Render the exported static GLB in the saved source's exact studio setup."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--build',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);build=Path(a.build).resolve();out=Path(a.out).resolve()
assert not out.exists(),'Fresh output required';out.mkdir(parents=True)
blend=build/'character.blend';glb=build/'chr_ava_morgan_041.glb';before={'blend':sha(blend),'glb':sha(glb)}
bpy.context.preferences.use_preferences_save=False
bpy.ops.wm.open_mainfile(filepath=str(blend),load_ui=False,use_scripts=False)
for ob in list(bpy.context.scene.objects):
    if ob.get('asset_id')=='chr_ava_morgan_041':bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(glb));scene=bpy.context.scene;camera=scene.camera;cd=camera.data
metadata=json.loads((build/'render-metadata.json').read_text());checks=[]
for view in [v for v in metadata['views'] if v['name'] in ('front','face_three_quarter')]:
    name=view['name'];cd.type=view['cameraType'];cd.ortho_scale=view['orthoScale'];camera.location=view['locationSource']
    camera.rotation_euler=(Vector(view['focusSource'])-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x,scene.render.resolution_y=view['resolution'];scene.render.filepath=str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    source=bpy.data.images.load(str(build/'renders'/(name+'.png')),check_existing=False)
    target=bpy.data.images.load(scene.render.filepath,check_existing=False)
    p=np.empty(len(source.pixels),dtype=np.float32);q=np.empty(len(target.pixels),dtype=np.float32)
    source.pixels.foreach_get(p);target.pixels.foreach_get(q);delta=np.abs(p.reshape(-1,4)[:,:3]-q.reshape(-1,4)[:,:3])
    checks.append({'view':name,'sourceSha256':sha(build/'renders'/(name+'.png')),'reimportSha256':sha(scene.render.filepath),
                   'meanAbsoluteImageFloatDifference':float(delta.mean()),'maxAbsoluteImageFloatDifference':float(delta.max()),
                   'pixelSpace':'Blender loaded PNG float RGB, display-encoded source images; no alignment or retouching',
                   'meanDifferenceLimit':.002,'pass':float(delta.mean())<.002})
report={'schema':'ava041-static-glb-render-roundtrip-1','checks':checks,'inputHashes':before,
        'inputFilesPreserved':before=={'blend':sha(blend),'glb':sha(glb)},
        'limitation':'Static Blender-to-Blender visual roundtrip; not Unity runtime, skinning or animation proof.'}
report['status']='pass' if report['inputFilesPreserved'] and len(checks)==2 and all(c['pass'] for c in checks) else 'fail'
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report),flush=True)
assert report['status']=='pass','Static GLB visual roundtrip differs; inspect actual renders'
