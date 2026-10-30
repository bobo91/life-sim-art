"""ART-041 static original visual candidate. Never edits A03 or the game repo."""
import argparse,hashlib,json,math,platform,struct,sys,time
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ava041_geometry as g
from ava041_head import build as build_head

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8')
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()

def metrics(objects):
    items=[]
    for o in objects:
        me=o.data;me.calc_loop_triangles();pts=[o.matrix_world@v.co for v in me.vertices];d=hashlib.sha256()
        for v in pts:d.update(struct.pack('<3f',*v))
        for t in me.loop_triangles:d.update(struct.pack('<3I',*t.vertices))
        items.append({'name':o.name,'vertices':len(pts),'triangles':len(me.loop_triangles),
                      'min':[min(p[k] for p in pts) for k in range(3)],'max':[max(p[k] for p in pts) for k in range(3)],
                      'geometrySha256':d.hexdigest(),'materials':[m.name for m in me.materials]})
    return items

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--a03');ap.add_argument('--views',default='all');ap.add_argument('--head-only',action='store_true');ap.add_argument('--samples',type=int)
    a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);cfg=json.loads(Path(a.config).read_text());out=Path(a.out).resolve()
    assert not out.exists(),'Use a fresh output path';out.mkdir(parents=True);(out/'renders').mkdir();start=time.time()
    bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    devices=[]
    try:
        pref=bpy.context.preferences.addons['cycles'].preferences
        for typ in ['HIP','CUDA','OPTIX']:
            try:
                pref.compute_device_type=typ;pref.get_devices();devices.extend([{'name':d.name,'type':d.type,'probe':typ} for d in pref.devices])
            except Exception as e:devices.append({'probe':typ,'unavailable':str(e)[:200]})
    except Exception as e:devices.append({'error':str(e)})
    write(out/'environment.json',{'blender':bpy.app.version_string,'buildHash':bpy.app.build_hash.decode(),'python':sys.version,'platform':platform.platform(),
          'background':bpy.app.background,'devicesEnumerated':devices,'actualRenderDevice':'CPU','gpuRenderTested':False})
    mats={k:g.material(k) for k in g.PALETTE};objects=build_head(mats,cfg['seed'])
    if not a.head_only:
        from ava041_outfit import build_outfit
        objects.extend(build_outfit(mats))
    for o in objects:
        if not o.data.color_attributes.get('Color'):g.paint(o)
    g.enable_vertex_colors(mats)
    # Consolidate disconnected construction pieces into editable semantic meshes.
    # Preserves authored geometry/colours while avoiding one draw per hair strand.
    groups={}
    for o in objects:
        if o.name.startswith('AVA_'):
            if any(t in o.name for t in ('HairCap','LooseBun','SweptLock','TempleWisp','NapeWisp')):key='Hair'
            elif 'GoldHoop' in o.name:key='Jewelry'
            elif 'Neck' in o.name:key='BodySkin'
            else:key='Face'
        else:
            key={'skin':'BodySkin','cream':'KnitAndSoles','olive':'Apron','denim':'Jeans',
                 'shoe':'SneakerUppers','leather':'ApronStraps','detail':'Jewelry'}[o.data.materials[0].name.removeprefix('AVA041_')]
        groups.setdefault(key,[]).append(o)
    objects=[]
    for key,parts in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:o.select_set(True)
        bpy.context.view_layer.objects.active=parts[0]
        if len(parts)>1:bpy.ops.object.join()
        ob=bpy.context.object;ob.name='AVA041_'+key;ob['component']=key;ob['asset_id']=cfg['assetId'];objects.append(ob)
    root=bpy.data.objects.new('CHR_AvaMorgan_041',None);scene.collection.objects.link(root);root['asset_id']=cfg['assetId'];root['phase']='A: unrigged visual review only'
    root['version']=cfg['version'];root['provenance']='Original Python-authored geometry; see ART041_PROVENANCE.md'
    for o in objects:o.parent=root;o['asset_id']=cfg['assetId']
    bpy.context.view_layer.update()
    # Contract bottom-centre pivot, applied to geometry only; never rescale adult identity.
    before=metrics(objects);lo=[min(m['min'][k] for m in before) for k in range(3)];hi=[max(m['max'][k] for m in before) for k in range(3)]
    shift=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2] if not a.head_only else 0))
    if a.head_only:shift.x=shift.y=0
    for o in objects:
        for v in o.data.vertices:v.co+=shift
        o.data.update()
    bpy.context.view_layer.update();items=metrics(objects);lo=[min(m['min'][k] for m in items) for k in range(3)];hi=[max(m['max'][k] for m in items) for k in range(3)]
    actual_mats={m.name for o in objects for m in o.data.materials}
    report={'assetId':cfg['assetId'],'version':cfg['version'],'seed':cfg['seed'],'geometrySource':'original parametric Python surfaces',
            'blender':bpy.app.version_string,'meshes':items,'meshCount':len(objects),'triangles':sum(m['triangles'] for m in items),
            'materialCount':len(actual_mats),'textureImages':0,'boundsSource':{'min':lo,'max':hi},'dimensionsSourceXYZ':[hi[k]-lo[k] for k in range(3)],
            'dimensionsExportXYZ':[hi[0]-lo[0],hi[2]-lo[2],hi[1]-lo[1]],'pivotShiftApplied':list(shift),
            'rigsDelivered':0,'animationsDelivered':0,'phase':'A','approval':'pending owner visual review',
            'limits':cfg['limits'],'a03Comparison':cfg['a03Comparison'],
            'sourceFiles':{p.name:sha(p) for p in sorted(Path(__file__).parent.glob('*ava041*.py'))},'configSha256':sha(a.config),
            'limitations':['Static pose only; no deformation, animation, Unity runtime or body contact dynamics evaluated.',
                           'Layered original garment/hair/face components intentionally overlap; automated mesh checks cannot prove all visible contacts.',
                           'Vertex colour face detail and core PBR only; no image textures.']}
    write(out/'asset-report.json',report)
    bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.gltf(filepath=str(out/(cfg['assetId']+'.glb')),export_format='GLB',use_selection=True,
        export_extras=True,export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False)
    # The same CPU Cycles/AgX studio method used by A03; no downloaded lighting assets.
    world=bpy.data.worlds.new('AVA_ReviewWorld');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.58,.61,.66,1);bg.inputs['Strength'].default_value=.35
    studio=[];h=1.70;target=Vector((0,0,h*.50))
    for name,xyz,power,size in [('Key',(-1.5,-2,2.2),500,.95),('Fill',(1.8,-.7,1.3),180,1.25),('Rim',(1,1.5,2),300,1)]:
        d=bpy.data.lights.new('AVA_Studio'+name,'AREA');d.energy=power*h*h*.55;d.shape='DISK';d.size=size*h
        o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=target+Vector(xyz)*h;aim(o,target);studio.append(o)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.003));floor=bpy.context.object;floor.name='ReviewFloor_NOT_ASSET'
    fm=bpy.data.materials.new('ReviewFloor');fm.diffuse_color=(.30,.32,.30,1);fm.use_nodes=True
    bs=next(n for n in fm.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.30,.32,.30,1);bs.inputs['Roughness'].default_value=.9;floor.data.materials.append(fm)
    cd=bpy.data.cameras.new('AVA_ReviewCamera');camera=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(camera);scene.camera=camera
    rc=cfg['render'];scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=a.samples or rc['samples'];scene.cycles.use_denoising=True;scene.cycles.seed=cfg['seed']
    scene.render.threads_mode='FIXED';scene.render.threads=rc['threads'];scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0;scene.view_settings.gamma=1;meta=[]
    def render(name,kind,az=0):
        requested=set(a.views.split(','))
        if a.views!='all' and name not in requested:return
        focus=Vector((0,shift.y,1.521 if kind=='face' else (.95 if kind=='game' else .86)))
        if kind=='game':focus.z=cfg['gameCamera']['focusHeight']
        cd.type='PERSP' if kind=='game' else 'ORTHO';ang=math.radians(az)
        if kind=='game':
            cd.sensor_fit='VERTICAL';cd.sensor_height=32;cd.lens=32/(2*math.tan(math.radians(40)/2));dist=16;elev=math.radians(50)
            camera.location=focus+Vector((math.sin(ang)*dist*math.cos(elev),-math.cos(ang)*dist*math.cos(elev),dist*math.sin(elev)))
        else:
            cd.ortho_scale=.40 if kind=='face' else (3.15 if kind=='compare' else 1.95)
            camera.location=focus+Vector((math.sin(ang)*5,-math.cos(ang)*5,.10 if kind=='full34' else 0))
            if kind=='iso':camera.location=focus+Vector((3,-3,3));cd.ortho_scale=2.0
        if kind=='compare':focus=Vector((0,0,.87));camera.location=focus+Vector((0,-5,.08))
        scene.render.resolution_x,scene.render.resolution_y=rc['face' if kind=='face' else ('game' if kind=='game' else 'full')]
        if kind=='compare':scene.render.resolution_x=1500;scene.render.resolution_y=1100
        aim(camera,focus);scene.render.filepath=str(out/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True)
        meta.append({'name':name,'cameraType':cd.type,'locationSource':list(camera.location),'focusSource':list(focus),
                     'distanceMeters':(camera.location-focus).length,'orthoScale':cd.ortho_scale if cd.type=='ORTHO' else None,
                     'verticalFov':math.degrees(cd.angle_y) if cd.type=='PERSP' else None,'resolution':[scene.render.resolution_x,scene.render.resolution_y],
                     'lighting':'Juniper outdoor daylight proxy' if name.startswith('cafe') or kind=='game' else 'A03-method studio',
                     'imageSha256':sha(scene.render.filepath)})
    for name,kind,az in [('front','full',0),('side','full',90),('back','full',180),('three_quarter','full34',30),('isometric','iso',45),('face_front','face',0),('face_three_quarter','face',30)]:render(name,kind,az)
    # Source contains Ava alone with review camera/lights, no A03 data blocks.
    camera.location=(2,-5,1);aim(camera,(0,0,.85));bpy.ops.wm.save_as_mainfile(filepath=str(out/'character.blend'))
    # Match documented game sun direction/colors, with explicit Blender approximation.
    for o in studio:o.hide_render=True
    bg.inputs['Color'].default_value=(*cfg['daylight']['ambientColor'],1);bg.inputs['Strength'].default_value=cfg['daylight']['ambientStrengthBlender']
    sd=bpy.data.lights.new('JuniperSunProxy','SUN');sd.energy=cfg['daylight']['sunEnergyBlender'];sd.color=cfg['daylight']['sunColor'];sd.angle=math.radians(8)
    so=bpy.data.objects.new(sd.name,sd);scene.collection.objects.link(so)
    # Unity sun ray from Euler(50,150,0), handedness expressed in source coordinates.
    # Unity forward ray=(+.321394,-.766044,-.556670). glTFast mirrors X;
    # source conversion is UnityXYZ=(-BlenderX,BlenderZ,-BlenderY).
    sun_ray=Vector((-.3213938048,.5566703992,-.7660444431))
    so.rotation_euler=sun_ray.to_track_quat('-Z','Y').to_euler()
    render('cafe_daylight_full','full34',30);render('cafe_daylight_face','face',30)
    render('game_16m_front','game',0);render('game_16m_back','game',180)
    so.hide_render=True
    for o in studio:o.hide_render=False
    bg.inputs['Color'].default_value=(.58,.61,.66,1);bg.inputs['Strength'].default_value=.35
    if a.a03:
        source=Path(a.a03).resolve();assert sha(source)==cfg['a03Comparison']['blendSha256'],'Wrong comparison input'
        with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('M01_')]
        comp=[]
        for o in dst.objects:
            if o and o.type=='MESH':scene.collection.objects.link(o);o.parent=None;o.location.x+=.78;comp.append(o)
        original_locations={o:o.location.copy() for o in objects}
        for o in objects:o.location=original_locations[o]+Vector((-.78,0,0))
        bpy.context.view_layer.update();render('ava_a03_same_scale','compare',0)
        for o in objects:o.location=original_locations[o]
        bpy.context.view_layer.update()
        assert sha(source)==cfg['a03Comparison']['blendSha256'],'Comparison input changed'
        report['a03Comparison']['inputBlendSha256Verified']=sha(source);report['a03Comparison']['readOnlyComparisonMeshCount']=len(comp)
        for o in comp:bpy.data.objects.remove(o,do_unlink=True)
    assert [m['geometrySha256'] for m in metrics(objects)]==[m['geometrySha256'] for m in items],'Render changed geometry'
    report['glbSha256']=sha(out/(cfg['assetId']+'.glb'));report['blendSha256']=sha(out/'character.blend');write(out/'asset-report.json',report)
    write(out/'render-metadata.json',{'views':meta,'seed':cfg['seed'],'renderer':'Cycles CPU / AgX','samples':scene.cycles.samples,'imageRetouching':False,
          'lightProxyLimitation':'Blender energy/AgX approximates URP sun/flat ambient; no Unity screenshot or integration claim.',
          'sourceAxes':'Z up / -Y front; export glTF +Y up / +Z front','elapsedSeconds':time.time()-start})
    print(json.dumps({'triangles':report['triangles'],'materials':len(actual_mats),'meshes':len(objects),'renders':len(meta),'seconds':time.time()-start}),flush=True)

if __name__=='__main__':main()
