"""Original props + real Blender previews; run only in isolated headless Blender."""
import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from art_pipeline.blender_build import aim, make_material
from props_mailbox import build_mailbox
from props_cafe_table import build_cafe_table

BUILDERS = {'prop_mailbox_001': build_mailbox, 'prop_cafe_table_001': build_cafe_table}


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for datablock in list(bpy.data.materials):
        bpy.data.materials.remove(datablock)


def signature(objects):
    points, triangles = set(), 0
    for obj in objects:
        points.update(tuple(round(x, 5) for x in obj.matrix_world @ v.co) for v in obj.data.vertices)
        triangles += sum(len(face.vertices) - 2 for face in obj.data.polygons)
    return {'uniquePositions': sorted(points), 'triangles': triangles}


def health(obj, config):
    mesh = obj.data
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free(); mesh.update()
    bm = bmesh.new(); bm.from_mesh(mesh)
    faces = [tuple(sorted(tuple(round(x, 8) for x in v.co) for v in f.verts)) for f in bm.faces]
    result = {
        'triangles': len(bm.faces), 'vertices': len(bm.verts),
        'nonManifoldEdges': sum(not e.is_manifold for e in bm.edges),
        'looseVertices': sum(not v.link_faces for v in bm.verts),
        'degenerateFaces': sum(f.calc_area() <= 1e-12 for f in bm.faces),
        'duplicateFaces': len(faces) - len(set(faces)),
        'nonFiniteVertices': sum(not all(math.isfinite(x) for x in v.co) for v in bm.verts),
        'signedVolumeCubicMetersSum': bm.calc_volume(signed=True),
    }
    pending = set(bm.verts); components = 0
    while pending:
        stack = [pending.pop()]; components += 1
        while stack:
            for edge in stack.pop().link_edges:
                for vertex in edge.verts:
                    if vertex in pending:
                        pending.remove(vertex); stack.append(vertex)
    result['closedConstructionComponents'] = components
    bm.free()
    for key in ('nonManifoldEdges', 'looseVertices', 'degenerateFaces', 'duplicateFaces', 'nonFiniteVertices'):
        if result[key]:
            raise ValueError(f'{obj.name}: {key}={result[key]}')
    if not 0 < result['triangles'] <= config['maxTriangles']:
        raise ValueError('Triangle budget exceeded')
    if result['signedVolumeCubicMetersSum'] <= 0:
        raise ValueError('Inverted/zero total volume')
    if obj.location.length > 1e-8 or any(abs(x - 1) > 1e-8 for x in obj.scale):
        raise ValueError('Nonidentity asset transform')
    result['limitations'] = ['Closed construction components intentionally meet/overlap at attachments; no exhaustive solid-intersection proof.', 'No collider or runtime interaction is included.']
    return result


def setup_scene(resolution, samples):
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'; scene.unit_settings.scale_length = 1
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'
    scene.cycles.samples = samples; scene.cycles.seed = 5101
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'; scene.render.threads = 4
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = 0; scene.view_settings.gamma = 1
    world = bpy.data.worlds.new('PREVIEW_world'); world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.40, .43, .46, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .45
    scene.world = world
    for name, position, energy, size, color in [
        ('key', (-3, -4, 6), 650, 4, (1, .89, .74)),
        ('fill', (4, -1, 4), 260, 5, (.80, .88, 1)),
        ('rim', (1, 4, 5), 450, 3, (1, .95, .84)),
    ]:
        data = bpy.data.lights.new('PREVIEW_' + name, 'AREA')
        data.energy, data.shape, data.size, data.color = energy, 'DISK', size, color
        light = bpy.data.objects.new(data.name, data); scene.collection.objects.link(light)
        light.location = position; aim(light, (0, 0, .7))
    mesh = bpy.data.meshes.new('PREVIEW_floor')
    mesh.from_pydata([(-200, -200, -.004), (200, -200, -.004), (200, 200, -.004), (-200, 200, -.004)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new(mesh.name, mesh); scene.collection.objects.link(floor)
    mesh.materials.append(make_material('PREVIEW_floor', {'color': '#CEC6B2', 'roughness': .92, 'metallic': 0}))
    data = bpy.data.cameras.new('PREVIEW_camera')
    camera = bpy.data.objects.new(data.name, data); scene.collection.objects.link(camera)
    scene.camera = camera
    return scene, camera


def render(scene, path):
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def inspect_one(config, output):
    clear()
    obj = BUILDERS[config['assetId']](config)
    report = health(obj, config)
    report['sourceDimensionsBlenderXYZ'] = list(obj.dimensions)
    report['materials'] = [m.name for m in obj.data.materials]
    report['customProperties'] = {k: str(obj[k]) for k in obj.keys()}
    if 'forwardProbeSourcePoint' in obj:
        report['forwardProbeSourcePoint'] = list(obj['forwardProbeSourcePoint'])
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(output / (obj.name + '.glb')),
        export_format='GLB', use_selection=True, export_yup=True,
        export_normals=True, export_materials='EXPORT', export_extras=False)
    resolution = config['preview']['resolution']
    scene, camera = setup_scene((resolution, resolution), config['preview']['samples'])
    scene.cycles.seed = config['seed']
    height = config['dimensionsMeters'][1]
    target = (0, 0, height * .48)
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = max(height, config['dimensionsMeters'][0]) * 1.30
    for name, position in [('front', (0, -3, target[2])),
                           ('isometric', (2.3, -2.3, target[2] + 2.3))]:
        camera.location = position; aim(camera, target)
        bpy.context.view_layer.update()
        camera_points = [camera.matrix_world.inverted() @ (obj.matrix_world @ v.co) for v in obj.data.vertices]
        low = [min(v[i] for v in camera_points) for i in (0, 1)]
        high = [max(v[i] for v in camera_points) for i in (0, 1)]
        camera.location += camera.rotation_euler.to_matrix() @ Vector(((low[0]+high[0])/2, (low[1]+high[1])/2, 0))
        camera.data.ortho_scale = max(high[i]-low[i] for i in (0, 1)) * 1.18
        bpy.context.view_layer.update()
        framing = screen_bounds(scene, camera, obj)
        if not framing['insideFrame']: raise ValueError('Preview framing clipped asset')
        report.setdefault('previewCameras', {})[name] = {'orthoScale':camera.data.ortho_scale, 'location':list(camera.location), 'framing':framing}
        render(scene, output / (name + '.png'))
    before = signature([obj])
    blend = output / (obj.name + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False, use_scripts=False)
    reopened = bpy.data.objects[config['assetId']]
    after = signature([reopened])
    report['saveReopenExactGeometry'] = before == after
    bpy.data.objects.remove(reopened, do_unlink=True)
    old = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(output / (config['assetId'] + '.glb')))
    imported = [o for o in bpy.data.objects if o not in old and o.type == 'MESH']
    roundtrip = signature(imported)
    report['glbRoundtripExactPositions5DecimalsAndTriangles'] = after == roundtrip
    report['glbImportedMeshCount'] = len(imported)
    report['positionSignatureSHA256'] = hashlib.sha256(json.dumps(before, separators=(',', ':')).encode()).hexdigest()
    if not report['saveReopenExactGeometry'] or not report['glbRoundtripExactPositions5DecimalsAndTriangles']:
        raise ValueError('Persistence or GLB roundtrip mismatch')
    write_json(output / 'build_report.json', report)
    return report


def screen_bounds(scene, camera, obj):
    projected = [world_to_camera_view(scene, camera, obj.matrix_world @ v.co) for v in obj.data.vertices]
    width, height = scene.render.resolution_x, scene.render.resolution_y
    lo = [min(v[i] for v in projected) for i in range(2)]
    hi = [max(v[i] for v in projected) for i in range(2)]
    return {'xywhPixelsBottomLeft': [round(lo[0]*width, 2), round(lo[1]*height, 2), round((hi[0]-lo[0])*width, 2), round((hi[1]-lo[1])*height, 2)],
            'insideFrame': all(v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 for v in projected)}


def game_views(configs, output):
    clear()
    objects = [BUILDERS[c['assetId']](c) for c in configs]
    for obj, position in zip(objects, [(-1.35, .0, 0), (1.25, .0, 0)]):
        obj.location = position
    scene, camera = setup_scene((1280, 720), 32)
    # Neutral half-meter ground grid is a preview scale aid, not exported game art.
    gridmat = make_material('PREVIEW_grid', {'color': '#B9B19D', 'roughness': .96, 'metallic': 0})
    for axis in range(2):
        for i in range(-12, 13):
            coordinate = i*.5
            verts = [(-6, coordinate-.006, -.002), (6, coordinate-.006, -.002), (6, coordinate+.006, -.002), (-6, coordinate+.006, -.002)]
            if axis: verts = [(y, x, z) for x, y, z in verts]
            mesh = bpy.data.meshes.new('PREVIEW_gridline'); mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
            line = bpy.data.objects.new(mesh.name, mesh); scene.collection.objects.link(line); mesh.materials.append(gridmat)
    camera.data.type = 'PERSP'; camera.data.sensor_fit = 'VERTICAL'
    camera.data.lens = camera.data.sensor_height / (2 * math.tan(math.radians(40)/2))
    camera.data.clip_start = .3; camera.data.clip_end = 1000
    focus = Vector((0, 0, 1.0))
    records = []
    for distance, yaw in ((6.0, 180), (16.0, 180), (30.0, 180), (16.0, 225)):
        # Unity yaw 180, pitch 50, focus playerY+1; Unity(X,Y,Z)->Blender(X,-Z,Y).
        horizontal = math.cos(math.radians(50))*distance
        camera.location = focus + Vector((-horizontal*math.sin(math.radians(yaw)), horizontal*math.cos(math.radians(yaw)), math.sin(math.radians(50))*distance))
        aim(camera, focus); bpy.context.view_layer.update()
        name = 'game_distance_' + str(int(distance)) + 'm'
        if yaw != 180: name += '_yaw' + str(yaw)
        render(scene, output / (name + '.png'))
        records.append({'file': name+'.png', 'distanceMeters': distance, 'verticalFovDegrees': 40,
            'unityYawDegrees': yaw, 'pitchDegrees': 50, 'focusHeightMeters': 1,
            'resolution': [1280, 720], 'blenderLocation': list(camera.location),
            'assets': {o.name: screen_bounds(scene, camera, o) for o in objects}})
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'game-camera-preview.blend'), compress=True)
    write_json(output / 'game-camera.json', {'scope': 'Actual Blender renders with game camera reconstructed from pinned game code; neutral preview scene, not a Unity screenshot or final game lighting.',
        'previewGridMeters': .5, 'views': records})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if bpy.app.version != (4, 5, 14): raise RuntimeError('Pin Blender 4.5.14')
    output = Path(args.output).resolve(); output.relative_to(ROOT)
    if output.exists() and any(output.iterdir()): raise FileExistsError('Preserve existing results; use new output')
    output.mkdir(parents=True, exist_ok=True)
    configs = [json.loads((ROOT/'configs'/(asset_id+'.json')).read_text(encoding='utf-8')) for asset_id in BUILDERS]
    reports = {}
    for config in configs:
        directory = output / config['assetId']; directory.mkdir()
        reports[config['assetId']] = inspect_one(config, directory)
    game_views(configs, output)
    write_json(output / 'tooling.json', {'blender': bpy.app.version_string, 'buildHash': bpy.app.build_hash.decode(),
        'python': sys.version, 'platform': platform.platform(), 'renderer': 'Cycles CPU', 'renderThreads': 4,
        'thirdPartyMeshesTexturesHdri': [], 'reports': reports})
    print('FIRST_PLAYABLE_PROPS_OK', flush=True)


if __name__ == '__main__': main()
