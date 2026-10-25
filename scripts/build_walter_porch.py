"""Walter pack worker. Original project inspection/preview methods copied from PR34
to avoid importing or branching from unmerged PR34/35. Main's validation/material
tools remain shared. No game scene/code or third-party mesh dependencies.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bmesh
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from art_pipeline.blender_build import aim, make_material
from props_walter import BUILDERS
from walter_mailbox_reference import build_mailbox
from walter_common import G, box, finish

def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')

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


def config(asset):
    return json.loads((ROOT/'configs'/(asset+'.json')).read_text(encoding='utf-8'))


def export(objects,path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,
                              export_normals=True,export_materials='EXPORT',export_extras=False)


def audit(output):
    prefs=bpy.context.preferences.addons['cycles'].preferences
    devices={}
    for backend in ('CUDA','OPTIX','HIP','ONEAPI','METAL'):
        try:devices[backend]=[d.type for d in prefs.get_devices_for_type(backend)]
        except Exception as error:devices[backend]={'unavailable':type(error).__name__}
    write_json(output/'blender-audit.json',{'blender':bpy.app.version_string,'embeddedPython':sys.version.split()[0],
        'background':bpy.app.background,'onlineAccess':bpy.app.online_access,'plannedRenderDevice':'CPU',
        'gpuComputeTested':False,'reportedDeviceTypes':devices})


def preflight(output):
    result={}
    for asset,builder in BUILDERS.items():
        clear();c=config(asset);obj=builder(c);report=health(obj,c);bpy.context.view_layer.update()
        report['dimensionsXYZ']=[float(obj.dimensions[i]) for i in (0,2,1)]
        report['materials']=[m.name for m in obj.data.materials]
        export([obj],output/(asset+'.glb'));result[asset]=report
    write_json(output/'preflight.json',result)


def hero(scene,camera,objects,path,scale=None,target=None,render_image=True):
    points=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
    lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
    target=Vector(target) if target is not None else (lo+hi)/2
    camera.data.type='ORTHO';camera.data.sensor_fit='VERTICAL'
    camera.location=target+Vector((7,-10,8));aim(camera,target);bpy.context.view_layer.update()
    coords=[camera.matrix_world.inverted()@p for p in points]
    low=[min(p[i] for p in coords) for i in (0,1)];high=[max(p[i] for p in coords) for i in (0,1)]
    aspect=scene.render.resolution_x/scene.render.resolution_y
    camera.data.ortho_scale=scale or max(high[1]-low[1],(high[0]-low[0])/aspect)*1.14
    if scale is None:camera.location+=camera.rotation_euler.to_matrix()@Vector(((low[0]+high[0])/2,(low[1]+high[1])/2,0))
    bpy.context.view_layer.update()
    if render_image:render(scene,path)
    return {o.name:screen_bounds(scene,camera,o) for o in objects}


def presentation(output,geometry_only=False):
    clear();templates={asset:builder(config(asset)) for asset,builder in BUILDERS.items()}
    mailboxConfig=json.loads((ROOT/'configs/walter-mailbox-reference.json').read_text())
    mailbox=build_mailbox(mailboxConfig);health(mailbox,mailboxConfig)
    export([mailbox],output/'reused_prop_mailbox_001.glb')
    digest=hashlib.sha256((output/'reused_prop_mailbox_001.glb').read_bytes()).hexdigest()
    if digest!='b243a55a5d92da3cd3a51c3957d0b1e1f1b9737ad8f6ed988121bae69e654698':raise ValueError('Approved mailbox changed')
    templates['prop_mailbox_001']=mailbox
    objects=[];instances=[]
    def inst(asset,position,yaw=0,pitch=0):
        obj=bpy.data.objects.new(asset+'__porch',templates[asset].data);bpy.context.collection.objects.link(obj)
        obj.location=position;obj.rotation_euler=(math.radians(pitch),0,math.radians(yaw));obj['assetId']=asset
        objects.append(obj);instances.append({'object':obj.name,'assetId':asset,'positionUnityXYZ':[position[0],position[2],-position[1]],
            'sourceEulerDegrees':[pitch,0,yaw],'unityEulerDegrees':[pitch,yaw,0]})
        return obj
    rocker=inst('prop_porch_rocking_chair_001',(-1.65,.55,.42),12)
    inst('prop_porch_bench_001',(1.85,.52,.42))
    inst('prop_flower_pot_001',(-2.35,-.40,.42))
    inst('prop_old_watering_can_001',(-1.80,-.35,.42),-10)
    # Upturned crate: the existing bottom boards become a real plant-stand surface.
    inst('prop_wooden_crate_001',(2.53,-.22,.74),pitch=180)
    inst('prop_flower_pot_002',(2.53,-.22,.7405))
    inst('prop_welcome_mat_001',(.15,1.08,.4205))
    lampTemplate=templates['prop_porch_lantern_001']
    back=max(v.co.y for v in lampTemplate.data.vertices)
    lantern=inst('prop_porch_lantern_001',(.83,1.40-back,2.02))
    inst('prop_mailbox_001',(-1.16,-2.37,0))
    for x in (-2.25,2.25):inst('prop_wooden_fence_001',(x,-2.5,0))
    for x in (-3,-1.5,1.5,3):inst('prop_fence_post_001',(x,-2.5,0))
    for obj in templates.values():bpy.data.objects.remove(obj,do_unlink=True)
    bpy.context.view_layer.update()
    # Temporary presentation architecture is excluded from the ten-asset library.
    from art_pipeline.blender_build import Geometry
    temp=[]
    materials={role:make_material('TEMP_'+role,spec) for role,spec in {
        'deck':{'color':'#9C8469','roughness':.88,'metallic':0},'deck_faded':{'color':'#A68E74','roughness':.9,'metallic':0},
        'wall':{'color':'#C0B79F','roughness':.89,'metallic':0},'trim':{'color':'#D0C5AB','roughness':.83,'metallic':0},
        'door':{'color':'#596A5F','roughness':.83,'metallic':0},'window':{'color':'#768B8F','roughness':.56,'metallic':0},
        'stone':{'color':'#A29D8C','roughness':.94,'metallic':0}}.items()}
    def stage(name,center,size,role):
        g=Geometry();g.box(center,size,0);mesh=bpy.data.meshes.new('TEMP_'+name);mesh.from_pydata(g.vertices,[],g.faces)
        mesh.materials.append(materials[role]);obj=bpy.data.objects.new('TEMP_'+name,mesh);bpy.context.collection.objects.link(obj);temp.append(obj)
        return obj
    stage('porch_foundation',(0,.35,.175),(5.8,2.15,.35),'stone')
    for i in range(21):stage('deck_board',(-2.76+i*.276,.35,.385),(.269,2.15,.07),'deck_faded' if i%5==0 else 'deck')
    stage('facade_fragment',(0,1.46,1.64),(6.5,.12,2.44),'wall')
    stage('door_frame',(.15,1.365,1.46),(1.10,.065,2.08),'trim')
    stage('door',(.15,1.322,1.44),(.96,.030,2.02),'door')
    for z in (1.0,1.86):stage('door_inset',(.15,1.300,z),(.74,.018,.59),'deck')
    stage('door_handle',(.505,1.275,1.45),(.025,.030,.115),'trim')
    for x in (-1.8,1.9):
        stage('window_trim',(x,1.355,1.82),(1.11,.075,.96),'trim')
        stage('opaque_window',(x,1.309,1.82),(.965,.022,.81),'window')
        stage('window_mullion',(x,1.287,1.82),(.036,.025,.81),'trim')
        stage('window_crossbar',(x,1.285,1.82),(.965,.025,.036),'trim')
        stage('window_sill',(x,1.265,1.32),(1.18,.21,.055),'deck')
    stage('upper_step',(.15,-.90,.14),(1.35,.35,.28),'stone')
    stage('lower_step',(.15,-1.23,.07),(1.35,.31,.14),'stone')
    stage('walkway',(.15,-2.43,-.012),(1.3,2.15,.025),'stone')
    scene,camera=setup_scene((1400,1050),32)
    record={'scope':'Temporary presentation porch/facade, not a production house or final game layout. Blender studio lighting, not Unity.',
            'mailboxSHA256':digest,'instances':instances,'lanternBackPlaneSourceY':back,'views':[]}
    record['overview']=hero(scene,camera,objects+temp,output/'porch_scene.png',render_image=not geometry_only)
    camera.data.type='PERSP';camera.data.sensor_fit='VERTICAL';camera.data.lens=camera.data.sensor_height/(2*math.tan(math.radians(40)/2))
    scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.cycles.samples=24
    for distance in (6,16):
        focus=Vector((0,-.35,1));camera.location=focus+Vector((0,-math.cos(math.radians(50))*distance,math.sin(math.radians(50))*distance))
        aim(camera,focus);bpy.context.view_layer.update();name=f'porch_game_{distance}m.png'
        if not geometry_only:render(scene,output/name)
        bounds={o.name:screen_bounds(scene,camera,o) for o in objects}
        record['views'].append({'file':name,'distanceMeters':distance,'verticalFovDegrees':40,'pitchDegrees':50,'yawDegrees':180,
                                'resolution':[1280,720],'allPropsInsideFrame':all(b['insideFrame'] for b in bounds.values()),'assets':bounds})
    scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.cycles.samples=32
    hero(scene,camera,[rocker],output/'rocking_chair_closeup.png',1.48,rocker.location+Vector((0,0,.53)),not geometry_only)
    hero(scene,camera,[lantern],output/'porch_lantern_closeup.png',.82,lantern.location+Vector((0,0,.205)),not geometry_only)
    if not next(v for v in record['views'] if v['distanceMeters']==16)['allPropsInsideFrame']:raise ValueError('Default16m view clips props')
    if not all(v['insideFrame'] for v in record['overview'].values()):raise ValueError('Overview framing clips objects')
    if not geometry_only:
        export(objects+temp,output/'porch-presentation-review.glb')
        bpy.ops.wm.save_as_mainfile(filepath=str(output/'porch-presentation.blend'),compress=True)
    write_json(output/('presentation-preflight.json' if geometry_only else 'presentation.json'),record)


def fence_closeup(output):
    clear();c=config('prop_wooden_fence_001');p=config('prop_fence_post_001');objects=[]
    for x,y,angle in ((0,0,0),(1.5,0,0),(2.25,.75,90)):
        obj=BUILDERS[c['assetId']](c);obj.location=(x,y,0);obj.rotation_euler.z=math.radians(angle);objects.append(obj)
    for x,y in ((-.75,0),(.75,0),(2.25,0),(2.25,1.5)):
        obj=BUILDERS[p['assetId']](p);obj.location=(x,y,0);objects.append(obj)
    scene,camera=setup_scene((1280,960),32);bpy.context.view_layer.update()
    hero(scene,camera,objects,output/'fence_module_joints.png')
    write_json(output/'fence-joint-check.json',{'moduleCenterSpacingMeters':1.5,'railLengthMeters':1.38,'postShaftWidthMeters':.12,
        'computedButtGapMeters':1.5-1.38-.12,'straightAndCornerSamePost':True,
        'scope':'Geometric seam contract + actual joint render, not Unity collision/nav verification.'})
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'fence-joints.blend'),compress=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--geometry-only',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if bpy.app.version!=(4,5,14) or not bpy.app.background or bpy.app.online_access:raise RuntimeError('Require isolated offline Blender4.5.14')
    output=Path(args.output).resolve();output.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve previous outputs')
    output.mkdir(parents=True);audit(output)
    if args.geometry_only:
        preflight(output);presentation(output,True)
    else:
        for asset in BUILDERS:
            folder=output/asset;folder.mkdir();inspect_one(config(asset),folder)
        presentation(output);fence_closeup(output)
    print('WALTER_PORCH_BUILD_OK',flush=True)


if __name__=='__main__':main()
