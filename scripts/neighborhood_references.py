"""Small source-pinned cache of existing Willow Creek assets; no new variants.

Run inside isolated Blender. Approved asset previews are not rendered again.
The two house references retain all mesh geometry and hide-group hierarchy;
their GLB container names may differ, so world geometry is fingerprinted.
"""
import hashlib
import json
from pathlib import Path

import bmesh
import bpy

import build_modular_building as b
from art_pipeline.blender_build import streetlamp
from art_pipeline.config import load_config
from props_cafe_furniture import build_cafe_counter, build_cafe_chair
from props_cafe_smallwares import build_tin, build_cafe_cup
from props_cafe_softgoods import build_cafe_tablecloth, build_cafe_parasol
from props_cafe_table import build_cafe_table
from props_walter import BUILDERS as WALTER_BUILDERS
from walter_mailbox_reference import build_mailbox

ROOT=Path(__file__).resolve().parents[1]
LOCK_PATH=ROOT/'configs/neighborhood-reference-locks.json'
PROP_BUILDERS=dict(WALTER_BUILDERS,prop_mailbox_001=build_mailbox,
    prop_cafe_table_001=build_cafe_table,prop_cafe_counter_001=build_cafe_counter,
    prop_cafe_chair_001=build_cafe_chair,prop_tin_001=build_tin,
    prop_cafe_cup_001=build_cafe_cup,prop_cafe_tablecloth_001=build_cafe_tablecloth,
    prop_cafe_parasol_001=build_cafe_parasol,prop_streetlamp_pipeline_001=streetlamp)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry_fingerprint(objects):
    value=b.signature(objects)
    # +0/-0 compare equal geometrically but JSON encodes them differently.
    value['positions']=[[0.0 if x==0 else x for x in point] for point in value['positions']]
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def _triangulate(obj):
    # Match the original approved prop workers, including mailbox source quads.
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data);bm.free();obj.data.update()


def _house(name):
    templates={c['assetId']:b.make(c) for c in b.CFG['assets']}
    root,_instances,_records=b.house(name,templates)
    # Linked instance mesh data survives; omit the unused source object stack
    # from the standalone editable house file and its viewport.
    for template in templates.values():
        for obj in reversed(b.tree(template)):
            bpy.data.objects.remove(obj,do_unlink=True)
    return root


def build_references(output):
    """Write output/reference/<stable-id>/{id.glb,id.blend,build_report.json}.

    All scenes are cleared while generating the cache. Call before assembling
    the neighborhood. No previously supplied model/preview file is modified.
    """
    output=Path(output).resolve();output.relative_to(ROOT)
    folder=output/'reference'
    if folder.exists():raise FileExistsError('Preserve existing reference cache')
    locks=json.loads(LOCK_PATH.read_text())
    for name,digest in locks['sourceFilesSHA256'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Pinned original source/config changed: '+name)
    for asset,entry in locks['references'].items():
        if entry['kind']=='house' and not entry.get('expectedWorldGeometrySHA256'):
            raise ValueError('Record approved world geometry fingerprint before building '+asset)
    folder.mkdir(parents=True)
    results={}
    for asset,entry in locks['references'].items():
        b.clear()
        if entry['kind']=='house':
            root=_house(entry['houseName'])
        else:
            config=load_config(ROOT/entry['config']) if entry['kind']=='main-prop' else json.loads((ROOT/entry['config']).read_text())
            root=PROP_BUILDERS[asset](config)
            _triangulate(root)
            root['assetId']=asset
        bpy.context.view_layer.update()
        objects=b.tree(root);meshes=b.meshes(root)
        digest=geometry_fingerprint(meshes)
        expected=entry.get('expectedWorldGeometrySHA256')
        if expected and digest!=expected:
            raise ValueError('Approved world geometry changed: '+asset)
        health=b.health(meshes)
        target=folder/asset;target.mkdir()
        model=target/(asset+'.glb')
        b.export(objects,model,extras=entry['kind']=='house')
        actual_sha=sha(model)
        if entry['kind']=='prop' and actual_sha!=entry['approvedGLBSHA256']:
            raise ValueError('Approved prop GLB bytes changed: '+asset)
        bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        bpy.context.view_layer.objects.active=root
        blend=target/(asset+'.blend')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
        # Confirm the actual exported geometry, not just the source objects.
        b.clear();bpy.ops.import_scene.gltf(filepath=str(model))
        imported=[o for o in bpy.data.objects if o.type=='MESH']
        roundtrip=geometry_fingerprint(imported)==digest
        if not roundtrip:raise ValueError('Reference GLB roundtrip changed geometry: '+asset)
        report={'assetId':asset,'existingReference':True,'sourcePR':entry['sourcePR'],
            'sourceCommit':entry['sourceCommit'],'config':entry['config'],
            'sourceFilesSHA256':locks['sourceFilesSHA256'],
            'referenceLockSHA256':sha(LOCK_PATH),'worldGeometrySHA256':digest,
            'approvedWorldGeometrySHA256':expected,
            'approvedGLBSHA256':entry['approvedGLBSHA256'],
            'exactApprovedGLBBytes':actual_sha==entry['approvedGLBSHA256'],
            'geometryRoundtrip':roundtrip,'health':health,
            'model':{'file':model.name,'sha256':actual_sha,'bytes':model.stat().st_size},
            'sourceBlend':{'file':blend.name,'sha256':sha(blend),'bytes':blend.stat().st_size},
            'provenance':'Unchanged original project procedural geometry/materials; no external asset content',
            'scope':'Existing assets regenerated without preview rendering. House containers may differ; approved world geometry is enforced.'}
        b.dump(target/'build_report.json',report)
        results[asset]=report
    b.dump(folder/'reference-cache.json',{'schema':'neighborhood-reference-cache-1',
        'referenceLockSHA256':sha(LOCK_PATH),'references':results})
    return results
