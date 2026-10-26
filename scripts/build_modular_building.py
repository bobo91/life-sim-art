"""Bounded original module build, persistence checks and real house previews.

Blender4.5.14 only. Existing Walter props are regenerated from unchanged pinned
project sources; they are presentation references, not new module variants.
"""
import argparse, hashlib, json, math, platform, sys
from pathlib import Path
import bmesh
import bpy
from mathutils import Vector,Matrix,Euler
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from art_pipeline.blender_build import aim,make_material
from art_pipeline.cli import normalize_png_metadata
from building_core import BUILDERS
from building_roof import build_roof_half,build_roof_ridge,build_gable_end,build_gable_trim,build_porch_canopy
from building_openings import build_window,build_door
from props_walter import BUILDERS as PROP_BUILDERS
from walter_mailbox_reference import build_mailbox
BUILDERS.update(dict(zip(('bld_roof_half_200_001','bld_roof_ridge_200_001','bld_gable_end_600_001','bld_gable_trim_600_001','bld_porch_canopy_200_001','bld_window_110_001','bld_door_100_001'),
    (build_roof_half,build_roof_ridge,build_gable_end,build_gable_trim,build_porch_canopy,build_window,build_door))))
CFG=json.loads((ROOT/'configs/modular-building.json').read_text())


def dump(path,v):Path(path).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def clear():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in list(bpy.data.materials):bpy.data.materials.remove(mat)
def tree(root):return [root]+[x for child in root.children for x in tree(child)]
def meshes(root):return [o for o in tree(root) if o.type=='MESH']
def points(objects):return [o.matrix_world@v.co for o in objects if o.type=='MESH' for v in o.data.vertices]
def bounds(objects):
    bpy.context.view_layer.update();p=points(objects)
    return {'min':[min(v[i] for v in p) for i in range(3)],'max':[max(v[i] for v in p) for i in range(3)]}
def signature(objects):
    bpy.context.view_layer.update()
    return {'positions':sorted(set(tuple(round(x,5) for x in v) for v in points(objects))),
        'triangles':sum(len(p.vertices)-2 for o in objects if o.type=='MESH' for p in o.data.polygons)}
def health(objects):
    result=[]
    for obj in objects:
        bm=bmesh.new();bm.from_mesh(obj.data)
        faces=[tuple(sorted(tuple(round(x,8) for x in v.co) for v in f.verts)) for f in bm.faces]
        r={'mesh':obj.name,'vertices':len(bm.verts),'triangles':sum(len(f.verts)-2 for f in bm.faces),
           'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'looseVertices':sum(not v.link_faces for v in bm.verts),
           'degenerateFaces':sum(f.calc_area()<1e-12 for f in bm.faces),'duplicateFaces':len(faces)-len(set(faces)),
           'nonFiniteVertices':sum(not all(math.isfinite(x) for x in v.co) for v in bm.verts),'signedVolume':bm.calc_volume(signed=True)}
        bm.free()
        if any(r[k] for k in ('nonManifoldEdges','looseVertices','degenerateFaces','duplicateFaces','nonFiniteVertices')) or r['signedVolume']<=0:raise ValueError(r)
        result.append(r)
    return result
def export(objects,path,extras=True):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,
        export_normals=True,export_materials='EXPORT',export_extras=extras)
def make(config):
    return BUILDERS[config['assetId']](dict(config,palette=CFG['palette']))


def setup(resolution=(1280,960),samples=24):
    s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=samples;s.cycles.seed=7401;s.cycles.use_denoising=True
    s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x,s.render.resolution_y=resolution;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='AgX'
    w=bpy.data.worlds.new('PREVIEW_world');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.42,.47,.53,1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value=.55;s.world=w
    for name,pos,energy,size,col in [('key',(-6,-8,12),2100,8,(1,.89,.73)),('fill',(8,-1,9),1200,9,(.79,.88,1)),('rim',(0,10,10),1800,6,(1,.94,.82))]:
        d=bpy.data.lights.new('PREVIEW_'+name,'AREA');d.energy=energy;d.size=size;d.color=col
        o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.location=pos;aim(o,(0,2,1))
    m=bpy.data.meshes.new('PREVIEW_ground');m.from_pydata([(-200,-200,-.008),(200,-200,-.008),(200,200,-.008),(-200,200,-.008)],[],[(0,1,2,3)])
    m.materials.append(make_material('PREVIEW_ground',{'color':'#B6B49A','roughness':.95,'metallic':0}))
    o=bpy.data.objects.new(m.name,m);s.collection.objects.link(o)
    d=bpy.data.cameras.new('PREVIEW_camera');c=bpy.data.objects.new(d.name,d);s.collection.objects.link(c);s.camera=c
    return s,c
def render(s,path):
    s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    normalize_png_metadata(Path(path))
def fit(s,c,objects,direction=(1,-1,.8),padding=1.18):
    p=points(objects);lo=Vector([min(v[i] for v in p) for i in range(3)]);hi=Vector([max(v[i] for v in p) for i in range(3)])
    target=(lo+hi)/2;c.data.type='ORTHO';c.location=target+Vector(direction).normalized()*25;aim(c,target);bpy.context.view_layer.update()
    v=[c.matrix_world.inverted()@x for x in p];low=[min(x[i] for x in v) for i in (0,1)];high=[max(x[i] for x in v) for i in (0,1)]
    c.location+=c.rotation_euler.to_matrix()@Vector(((low[0]+high[0])/2,(low[1]+high[1])/2,0))
    aspect=s.render.resolution_x/s.render.resolution_y;c.data.ortho_scale=max(high[0]-low[0],(high[1]-low[1])*aspect)*padding
    bpy.context.view_layer.update()
def camera_record(s,c,objects):
    p=[world_to_camera_view(s,c,x) for x in points(objects)]
    return {'locationSourceXYZ':list(c.location),'rotationRadiansXYZ':list(c.rotation_euler),'type':c.data.type,
        'orthoScale':c.data.ortho_scale,'verticalFovDegrees':math.degrees(c.data.angle_y),
        'resolution':[s.render.resolution_x,s.render.resolution_y],
        'allGeometryInsideFrame':all(0<=v.x<=1 and 0<=v.y<=1 and v.z>0 for v in p)}


def inspect_module(config,folder,previews=True):
    clear();folder.mkdir(parents=True);root=make(config);objects=tree(root);mesh=meshes(root)
    report={'assetId':config['assetId'],'health':health(mesh),'boundsSourceXYZ':bounds(mesh),
        'materials':sorted(set(m.name for o in mesh for m in o.data.materials)),'sourceHierarchy':[{ 'name':o.name,'parent':o.parent.name if o.parent else None,'location':list(o.location)} for o in objects]}
    if config['assetId'] in ('bld_wall_window_200_001','bld_wall_door_200_001'):
        heights=(.90,1.4,2.05) if 'window' in config['assetId'] else (.05,1.0,2.15)
        tests=[not root.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),distance=2)[0] for x in (-.50,0,.50) for z in heights]
        if not all(tests):raise ValueError('Wall geometry blocks declared opening')
        report['openingRaySamplesClear']=len(tests)
    if config['assetId']=='bld_door_100_001':
        frame=next(o for o in mesh if o.get('component')=='frame')
        tests=[not frame.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),distance=2)[0] for x in (-.48,0,.48) for z in (.03,1,2.13)]
        if not all(tests):raise ValueError('Door frame blocks declared passage')
        report['framePassageRaySamplesClearWithLeafExcluded']=len(tests)
    export(objects,folder/(root.name+'.glb'));before=signature(mesh)
    if previews:
        s,c=setup((384,384),16)
        for name,d in [('front',(0,-1,.03)),('isometric',(1,-1,.85))]:
            fit(s,c,mesh,d);render(s,folder/(name+'.png'))
            report.setdefault('previewCameras',{})[name]=camera_record(s,c,mesh)
    blend=folder/(config['assetId']+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend),load_ui=False,use_scripts=False)
    reopened=bpy.data.objects[config['assetId']];after=signature(meshes(reopened));hierarchy=[(o.name,o.parent.name if o.parent else None,tuple(o.location)) for o in tree(reopened)]
    original=[(o['name'],o['parent'],tuple(o['location'])) for o in report['sourceHierarchy']]
    report['saveReopenExactGeometryAndHierarchy']=before==after and hierarchy==original
    for o in reversed(tree(reopened)):bpy.data.objects.remove(o,do_unlink=True)
    old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(folder/(config['assetId']+'.glb')))
    imported=[o for o in bpy.data.objects if o not in old and o.type=='MESH'];again=signature(imported)
    report['glbRoundtripExactPositions5DecimalsAndTriangles']=before==again
    report['positionSignatureSHA256']=hashlib.sha256(json.dumps(before,separators=(',',':')).encode()).hexdigest()
    if not report['saveReopenExactGeometryAndHierarchy'] or before!=again:raise ValueError('Module persistence failed '+config['assetId'])
    dump(folder/'build_report.json',report)


def instance(template,parent,loc,rot,group):
    def clone(o,p):
        n=o.copy();n.hide_render=False;n.hide_viewport=False;bpy.context.collection.objects.link(n);n.parent=p
        for child in o.children:clone(child,n)
        return n
    n=clone(template,parent);n.location=loc;n.rotation_euler=(0,0,math.radians(rot));n['hideGroup']=group;n['moduleId']=template['assetId']
    return n
def house(name,templates):
    h=CFG['houses'][name];length=h['lengthMeters'];floor=.6
    root=bpy.data.objects.new(name+'-house',None);bpy.context.collection.objects.link(root)
    root['assetId']=name+'-house';root['floorLevelMeters']=floor;root['gridMeters']=2;root['interiorPolicy']='Empty ground-floor shell; no finished rooms or upper floor'
    records=[];instances=[]
    def put(asset,loc,rot=0,group='floor'):
        n=instance(templates['bld_'+asset],root,loc,rot,group);instances.append(n)
        records.append({'moduleId':'bld_'+asset,'location':list(loc),'rotationZDegrees':rot,'hideGroup':group});return n
    for y in range(1,length,2):
        for x in (-2,0,2):put('floor_200_001',(x,y,.42))
        for x,rot,side in ((3,90,'east'),(-3,-90,'west')):
            put('foundation_200_001',(x,y,0),rot,'foundation')
            kind='window' if (y-1)//2 in h['sideWindowBays'] else 'solid'
            put('wall_'+kind+'_200_001',(x,y,floor),rot,'wall.'+side)
            if kind=='window':put('window_110_001',(x,y,floor+.85),rot,'wall.'+side)
    for x,kind in zip((-2,0,2),h['frontWallModules']):
        for y,rot,side,k in ((0,0,'south',kind),(length,180,'north','window' if x else 'solid')):
            put('foundation_200_001',(x,y,0),rot,'foundation');put('wall_'+k+'_200_001',(x,y,floor),rot,'wall.'+side)
            if k=='window':put('window_110_001',(x,y,floor+.85),rot,'wall.'+side)
            if k=='door':put('door_100_001',(x,y,floor),rot,'wall.'+side)
    for x,y,rot,group in ((3,0,0,'south.east'),(-3,0,-90,'south.west'),(3,length,90,'north.east'),(-3,length,180,'north.west')):
        put('corner_trim_001',(x,y,floor),rot,'corner.'+group)
    for y in range(1,length,2):
        put('roof_half_200_001',(0,y,3.4),0,'roof');put('roof_half_200_001',(0,y,3.4),180,'roof');put('roof_ridge_200_001',(0,y,3.4),0,'roof')
    for y,rot,side in ((0,0,'south'),(length,180,'north')):
        put('gable_end_600_001',(0,y,3.4),rot,'wall.'+side);put('gable_trim_600_001',(0,y,3.4),rot,'roof')
    for x in h['porchCentersX']:
        put('porch_200_001',(x,-1,0),0,'porch');put('porch_canopy_200_001',(x,0,3.1),0,'roof')
    for x in sorted(set(v+d for v in h['porchCentersX'] for d in (-1,1))):put('porch_post_001',(x,-1.94,.60),0,'porch')
    put('porch_steps_001',(h['doorCenterX'],-2,0),0,'porch')
    entry=bpy.data.objects.new(name+'__entry',None);bpy.context.collection.objects.link(entry);entry.parent=root;entry.location=(h['doorCenterX'],-.5,floor);entry['role']='proposed-entry-anchor'
    # Share palette roles inside each house without changing any module mesh.
    replacements={}
    for o in meshes(root):
        for slot in o.material_slots:
            role=slot.material.name.split('__')[-1]
            if role not in replacements:
                spec=dict(CFG['palette'][role])
                if name=='alternate' and role in CFG['alternatePalette']:spec['color']=CFG['alternatePalette'][role]
                replacements[role]=make_material(name+'__'+role,spec)
            slot.link='OBJECT';slot.material=replacements[role]
    bpy.context.view_layer.update()
    return root,instances,records


def reference_sources(output):
    folder=output/'references';folder.mkdir(exist_ok=True)
    for asset,builder in [*PROP_BUILDERS.items(),('prop_mailbox_001',build_mailbox)]:
        clear()
        c=json.loads((ROOT/'configs'/('walter-mailbox-reference.json' if asset=='prop_mailbox_001' else asset+'.json')).read_text())
        o=builder(c)
        # Match the approved prop worker's explicit Blender triangulation,
        # including the mailbox generator's original quads.
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
        f=folder/asset;f.mkdir(exist_ok=True);r={'health':health([o]),'materials':[m.name for m in o.data.materials]}
        export([o],f/(asset+'.glb'),False);bpy.ops.wm.save_as_mainfile(filepath=str(f/(asset+'.blend')),compress=True)
        dump(f/'build_report.json',r)


def add_references(output,geometry_only=False):
    refs={};records=[]
    for asset in (*PROP_BUILDERS,'prop_mailbox_001'):
        old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(output/'references'/asset/(asset+'.glb')))
        refs[asset]=next(o for o in bpy.data.objects if o not in old and o.type=='MESH');refs[asset]['assetId']=asset
    def put(a,loc,rot=0,pitch=0):
        o=refs[a].copy();o.hide_render=False;bpy.context.collection.objects.link(o)
        # Compose with the import transform; glTF meshes can use quaternion mode.
        o.matrix_world=Matrix.Translation(loc)@Euler((math.radians(pitch),0,math.radians(rot)),'XYZ').to_matrix().to_4x4()@refs[a].matrix_world
        records.append({'assetId':a,'location':list(loc),'rotationZDegrees':rot,'rotationXDegrees':pitch});return o
    put('prop_porch_rocking_chair_001',(-2.25,-.70,.6),-8)
    put('prop_porch_bench_001',(-1.20,-.46,.6))
    put('prop_flower_pot_001',(-2.63,-1.57,.6))
    put('prop_old_watering_can_001',(-1.97,-1.45,.6),-20)
    put('prop_wooden_crate_001',(.62,-.52,.92),pitch=180)
    put('prop_flower_pot_002',(.62,-.52,.9205))
    put('prop_welcome_mat_001',(0,-.43,.6005))
    put('prop_porch_lantern_001',(.78,-.248,2.3))['wallMountGroup']='wall.south'
    put('prop_mailbox_001',(-3.8,-3.4,0),-12)
    for x in (-2.55,1.95):put('prop_wooden_fence_001',(x,-3.7,0))
    for x in (-3.3,-1.8,1.2,2.7):put('prop_fence_post_001',(x,-3.7,0))
    for o in refs.values():bpy.data.objects.remove(o,do_unlink=True)
    return records


def assembly(output,draft=False):
    clear();templates={c['assetId']:make(c) for c in CFG['assets']}
    for t in templates.values():
        for o in tree(t):o.hide_render=True
    root,instances,records=house('walter',templates);objects=meshes(root)
    out=output/'assemblies';out.mkdir(exist_ok=True)
    export(tree(root),out/'walter-house.glb');bpy.ops.wm.save_as_mainfile(filepath=str(out/'walter-house.blend'),compress=True)
    # Source/reimport check before lighting/props are added; retain hierarchy.
    before=signature(objects);saved_groups=[(o.name,o.get('hideGroup')) for o in instances]
    bpy.ops.wm.open_mainfile(filepath=str(out/'walter-house.blend'),load_ui=False,use_scripts=False)
    root=bpy.data.objects['walter-house'];instances=[o for o in root.children if 'moduleId' in o];templates={c['assetId']:bpy.data.objects[c['assetId']] for c in CFG['assets']}
    reopened=before==signature(meshes(root)) and sorted(saved_groups)==sorted((o.name,o.get('hideGroup')) for o in instances)
    old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(out/'walter-house.glb'))
    imported=[o for o in bpy.data.objects if o not in old];roundtrip=before==signature(imported)
    for o in reversed(imported):bpy.data.objects.remove(o,do_unlink=True)
    if not reopened or not roundtrip:
        dump(output/'persistence-debug.json',{'reopened':reopened,'roundtrip':roundtrip,'before':before,'imported':signature([o for o in bpy.data.objects if o not in old and o.type=='MESH'])})
        raise ValueError('House persistence failed '+str((reopened,roundtrip)))
    refs=add_references(output,draft)
    for t in templates.values():
        for o in tree(t):o.hide_render=True
    s,c=setup((1280,960),12 if draft else 32);previews=output/'previews';previews.mkdir(exist_ok=True);views={}
    visible=lambda:[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('PREVIEW_')]
    fit(s,c,visible(),(1,-1.4,.95));render(s,previews/'walter-three-quarter.png');views['walter-three-quarter']=camera_record(s,c,visible())
    if draft:return dump(output/'draft.json',{'scope':'Early actual house silhouette render','instances':records,'views':views})
    s.render.resolution_x,s.render.resolution_y=1280,720
    c.data.type='PERSP';c.data.sensor_fit='VERTICAL';c.data.lens=c.data.sensor_height/(2*math.tan(math.radians(40)/2))
    for name,d,focus,pitch,yaw in [('walter-game-16m',16,CFG['camera']['buildingFocusSourceXYZ'],50,180),('walter-entry-6m',6,(-.8,-.7,1.65),15,168)]:
        p,y=math.radians(pitch),math.radians(yaw)
        c.location=Vector(focus)+Vector((math.sin(y)*math.cos(p)*d,math.cos(y)*math.cos(p)*d,math.sin(p)*d));aim(c,focus);bpy.context.view_layer.update()
        render(s,previews/(name+'.png'));views[name]=dict(camera_record(s,c,visible()),distanceMeters=d,pitchDegrees=pitch,yawDegrees=yaw,focusSourceXYZ=list(focus))
        if name=='walter-game-16m' and not views[name]['allGeometryInsideFrame']:raise ValueError('16m review view clips geometry')
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'walter-presentation.blend'),compress=True)
    s.render.resolution_x,s.render.resolution_y=1280,960
    for name,hide in [('walter-roof-hidden',lambda g:g=='roof'),('walter-cutaway',lambda g:g=='roof' or g in ('wall.south','wall.west') or g.startswith('corner.') and ('south' in g or 'west' in g))]:
        for instance_ in instances:
            if hide(instance_.get('hideGroup','')):
                for o in tree(instance_):o.hide_render=True
        for o in bpy.data.objects:
            if o.get('wallMountGroup') and hide(o['wallMountGroup']):o.hide_render=True
        fit(s,c,meshes(root),(-1,-1.2,1.25));render(s,previews/(name+'.png'));views[name]=camera_record(s,c,visible())
    for o in tree(root):o.hide_render=True
    for o in bpy.data.objects:
        if o.get('assetId','').startswith('prop_'):o.hide_render=True
    alt,altinstances,altrecords=house('alternate',templates)
    export(tree(alt),out/'alternate-house.glb');bpy.ops.wm.save_as_mainfile(filepath=str(out/'alternate-house.blend'),compress=True)
    fit(s,c,meshes(alt),(1,-1.4,.95));render(s,previews/'alternate-house.png');views['alternate-house']=camera_record(s,c,meshes(alt))
    # A material override must never duplicate source mesh geometry.
    def linked_template(o):
        for source in tree(templates[o['assetId']]):
            if source.type=='MESH' and source.get('component')==o.get('component'):return o.data is source.data
        return False
    linked=all(linked_template(o) for o in meshes(alt))
    alt_before=signature(meshes(alt));bpy.ops.wm.open_mainfile(filepath=str(out/'alternate-house.blend'),load_ui=False,use_scripts=False)
    alt_reopened=alt_before==signature(meshes(bpy.data.objects['alternate-house']))
    old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(out/'alternate-house.glb'))
    alt_roundtrip=alt_before==signature([o for o in bpy.data.objects if o not in old])
    if not linked or not alt_reopened or not alt_roundtrip:raise ValueError('Alternate persistence or shared mesh failed')
    for name,view in views.items():
        view['file']=name+'.png';view['sha256']=hashlib.sha256((previews/view['file']).read_bytes()).hexdigest()
    dump(output/'presentation.json',{'scope':'Actual Blender house prototypes. No Unity runtime/camera/import test. Ground floor empty; attic expression only, no upper floor.',
        'views':views,'walter':{'instances':records,'saveReopenGeometryAndGroups':reopened,'glbRoundtripExactPositions5DecimalsAndTriangles':roundtrip},
        'alternate':{'instances':altrecords,'sharedMeshData':linked,'saveReopenExactGeometry':alt_reopened,'glbRoundtripExactPositions5DecimalsAndTriangles':alt_roundtrip,'newModuleIds':sorted(set(x['moduleId'] for x in altrecords)-set(x['moduleId'] for x in records))},'reusedProps':refs})


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--draft',action='store_true');p.add_argument('--geometry-only',action='store_true')
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);output=Path(a.output).resolve();output.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve prior evidence')
    if bpy.app.version!=(4,5,14) or not bpy.app.background or bpy.app.online_access:raise ValueError('Pinned offline Blender required')
    output.mkdir(parents=True)
    devices=[]
    try:
        cp=bpy.context.preferences.addons['cycles'].preferences;cp.get_devices();devices=[{'name':d.name,'type':d.type} for d in cp.devices]
    except Exception as e:devices=[{'enumerationError':type(e).__name__}]
    dump(output/'environment.json',{'blender':bpy.app.version_string,'python':platform.python_version(),'background':bpy.app.background,'onlineAccess':bpy.app.online_access,'devicesEnumerated':devices,'actualRenderDevice':'CPU','threads':4})
    if not a.draft:
        for config in CFG['assets']:inspect_module(config,output/'modules'/config['assetId'],not a.geometry_only)
    if not a.geometry_only:
        reference_sources(output);assembly(output,a.draft)
    print('MODULAR_BUILDING_OK',flush=True)
if __name__=='__main__':main()
