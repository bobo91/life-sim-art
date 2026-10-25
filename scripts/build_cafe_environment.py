"""Build only the six original cafe props and two compositions; isolated Blender."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
import build_first_playable_props as base
from art_pipeline.blender_build import aim
from props_cafe_table import build_cafe_table
from props_cafe_furniture import build_cafe_counter, build_cafe_chair
from props_cafe_smallwares import build_tin, build_cafe_cup
from props_cafe_softgoods import build_cafe_tablecloth, build_cafe_parasol

BUILDERS = dict(zip(('prop_cafe_counter_001', 'prop_cafe_chair_001', 'prop_tin_001',
                    'prop_cafe_cup_001', 'prop_cafe_tablecloth_001', 'prop_cafe_parasol_001'),
                   (build_cafe_counter, build_cafe_chair, build_tin, build_cafe_cup,
                    build_cafe_tablecloth, build_cafe_parasol)))
base.BUILDERS.update(BUILDERS)
TABLE = 'prop_cafe_table_001'


def configuration(asset):
    return json.loads((ROOT / 'configs' / (asset + '.json')).read_text(encoding='utf-8'))


def export(objects, path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_yup=True, export_normals=True, export_materials='EXPORT', export_extras=False)


def preflight(output):
    results = {}
    for asset, builder in BUILDERS.items():
        base.clear(); config = configuration(asset); obj = builder(config)
        report = base.health(obj, config)
        bpy.context.view_layer.update()
        report['actualDimensionsXYZ'] = [float(obj.dimensions[i]) for i in (0, 2, 1)]
        export([obj], output / (asset + '.glb'))
        results[asset] = report
    base.write_json(output / 'preflight.json', results)


def framed_hero(scene, camera, objects, path, fit_objects=None, render_image=True):
    points = [obj.matrix_world @ v.co for obj in (fit_objects or objects) for v in obj.data.vertices]
    low = Vector(tuple(min(v[i] for v in points) for i in range(3)))
    high = Vector(tuple(max(v[i] for v in points) for i in range(3)))
    target = (low + high) / 2
    camera.data.type = 'ORTHO'; camera.data.sensor_fit='VERTICAL'
    camera.location = target + Vector((6, -9, 8))
    aim(camera, target); bpy.context.view_layer.update()
    coords = [camera.matrix_world.inverted() @ v for v in points]
    lo = [min(v[i] for v in coords) for i in (0, 1)]
    hi = [max(v[i] for v in coords) for i in (0, 1)]
    aspect = scene.render.resolution_x / scene.render.resolution_y
    camera.data.ortho_scale = max(hi[1]-lo[1], (hi[0]-lo[0])/aspect) * 1.17
    camera.location += camera.rotation_euler.to_matrix() @ Vector(((lo[0]+hi[0])/2, (lo[1]+hi[1])/2, 0))
    bpy.context.view_layer.update()
    framing = {obj.name: base.screen_bounds(scene, camera, obj) for obj in objects}
    if not all(v['insideFrame'] for v in framing.values()): raise ValueError('Clipped composition')
    if render_image:base.render(scene, path)
    return framing


def compositions(output, geometry_only=False):
    pack = configuration('cafe-environment-pack')
    base.clear()
    templates = {asset: builder(configuration(asset)) for asset, builder in BUILDERS.items()}
    templates[TABLE] = build_cafe_table(configuration(TABLE))
    export([templates[TABLE]], output / 'shared_approved_table.glb')
    if hashlib.sha256((output/'shared_approved_table.glb').read_bytes()).hexdigest() != pack['sharedTable']['approvedGlbSHA256']:
        raise ValueError('Approved table bytes changed')
    for obj in templates.values(): obj.hide_render = True; obj.hide_set(True)
    all_objects, instances = [], []

    def instance(asset, position, yaw=0, state='display'):
        obj = bpy.data.objects.new(asset + '__' + state, templates[asset].data)
        bpy.context.collection.objects.link(obj)
        obj.location = position; obj.rotation_euler.z = math.radians(yaw)
        obj['assetId'] = asset; obj['arrangement'] = state
        all_objects.append(obj)
        instances.append({'object': obj.name, 'assetId': asset, 'state': state,
                          'positionUnityXYZ': [position[0], position[2], -position[1]], 'yaw': yaw})
        return obj

    states = {}
    for state, center in (('bare', (-1.22, -.85, 0)), ('set', (1.22, -.85, 0))):
        origin = Vector(center); members = [instance(TABLE, origin, state=state)]
        for child in pack['tableStates'][state]['children']:
            x,y,z=child['position']
            members.append(instance(child['assetId'],origin+Vector((x,-z,y)),child.get('yaw',0),state))
        if state=='set':
            cloth=next(o for o in members if o['assetId']=='prop_cafe_tablecloth_001')
            underside=cloth.location.z+float(templates['prop_cafe_tablecloth_001']['supportUndersideLocalMeters'])
            if abs(underside-.741)>.00001:raise ValueError('Cloth support height differs from recipe')
        states[state] = members
    counter = instance('prop_cafe_counter_001', (0, 1.35, 0))
    instance('prop_tin_001', (-.46, 1.26, 1.0205))
    instance('prop_cafe_cup_001', (.47, 1.28, 1.0205), 15)
    # Templates are not scene objects/export candidates; all instances share their mesh data.
    for obj in templates.values(): bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()
    scene, camera = base.setup_scene((1400, 1050), 48)
    record = {'scope': 'Actual Blender Cycles CPU preview; no Unity/game integration.',
              'tableIdentity': pack['sharedTable'], 'instances': instances, 'views': []}
    record['tableInstancesShareMeshData']=states['bare'][0].data is states['set'][0].data
    if not record['tableInstancesShareMeshData']:raise ValueError('Two table meshes were created')
    def surface_intersections(a,b):
        def tree(obj):
            return BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],
                [tuple(p.vertices) for p in obj.data.polygons],all_triangles=True,epsilon=1e-7)
        return len(tree(a).overlap(tree(b)))
    table=states['set'][0]
    cloth=next(o for o in states['set'] if o['assetId']=='prop_cafe_tablecloth_001')
    checked=[(cloth,table)]
    checked += [(o,cloth) for o in states['set'] if o['assetId']=='prop_cafe_cup_001']
    checked += [(o,table) for o in states['set'] if o['assetId']=='prop_cafe_chair_001']
    record['targetedSurfaceIntersectionChecks']=[{'a':a.name,'b':b.name,'triangleIntersections':surface_intersections(a,b)} for a,b in checked]
    if any(c['triangleIntersections'] for c in record['targetedSurfaceIntersectionChecks']):
        raise ValueError('Unintended table/cloth/cup/chair surface intersection')
    record['overviewFraming'] = framed_hero(scene, camera, all_objects, output/'cafe_scene.png',render_image=not geometry_only)
    # Two state previews keep identical camera/light/resolution and exclude only other displays.
    for state in ('bare', 'set'):
        for obj in all_objects: obj.hide_render = obj not in states[state]
        # Move bare display temporarily to the set display's center; match camera exactly.
        shift=Vector((2.44,0,0)) if state=='bare' else Vector((0,0,0))
        for obj in states[state]:obj.location+=shift
        bpy.context.view_layer.update()
        record[state+'Framing'] = framed_hero(scene, camera, states[state], output/('table_'+state+'.png'), states['set'],not geometry_only)
        for obj in states[state]:obj.location-=shift
        bpy.context.view_layer.update()
    for obj in all_objects: obj.hide_render = False
    if geometry_only:
        base.write_json(output/'composition-preflight.json',record)
        return
    scene.render.resolution_x=1280; scene.render.resolution_y=720
    camera.data.type='PERSP'; camera.data.sensor_fit='VERTICAL'
    camera.data.lens = camera.data.sensor_height/(2*math.tan(math.radians(40)/2))
    camera.data.clip_start=.3; camera.data.clip_end=1000
    focus=Vector((.25,0,1))
    for distance in (16, 6):
        camera.location=focus+Vector((0,-math.cos(math.radians(50))*distance,math.sin(math.radians(50))*distance))
        aim(camera, focus); bpy.context.view_layer.update()
        bounds={obj.name:base.screen_bounds(scene,camera,obj) for obj in all_objects}
        name=f'cafe_game_{distance}m.png'
        if distance==16 and not all(v['insideFrame'] for v in bounds.values()):raise ValueError('Default game view clips an asset')
        base.render(scene,output/name)
        record['views'].append({'file':name,'distanceMeters':distance,'verticalFovDegrees':40,'pitchDegrees':50,
            'unityYawDegrees':180,'focusHeightMeters':1,'resolution':[1280,720],
            'allInsideFrame':all(v['insideFrame'] for v in bounds.values()),'assets':bounds})
    export(all_objects, output/'cafe-arrangements-review.glb')
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'cafe-arrangements.blend'),compress=True)
    base.write_json(output/'arrangements.json',record)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--geometry-only',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if bpy.app.version!=(4,5,14) or not bpy.app.background or bpy.app.online_access:raise RuntimeError('Require pinned isolated offline Blender')
    output=Path(args.output).resolve();output.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve prior build')
    output.mkdir(parents=True)
    if args.geometry_only:
        preflight(output)
        compositions(output,True)
    else:
        for asset in BUILDERS:
            folder=output/asset;folder.mkdir()
            base.inspect_one(configuration(asset),folder)
        compositions(output)
    print('CAFE_ENVIRONMENT_BUILD_OK',flush=True)


if __name__=='__main__':main()
