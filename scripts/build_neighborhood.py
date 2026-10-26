"""One bounded neighborhood, assembled from separate reusable project assets."""
import argparse,hashlib,json,math,platform,sys
from pathlib import Path
import bpy
from mathutils import Vector,Matrix,Euler
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import build_modular_building as b
from art_pipeline.blender_build import aim,make_material
from neighborhood_references import build_references,geometry_fingerprint
from neighborhood_street import BUILDERS as STREET
from neighborhood_greenery import BUILDERS as GREEN
from neighborhood_cafe import BUILDERS as CAFE
NEW=dict(STREET,**GREEN,**CAFE)
CONFIG=json.loads((ROOT/'configs/neighborhood-assets.json').read_text())
LAYOUT=json.loads((ROOT/'configs/neighborhood-layout.json').read_text())
ORIGINAL_MAKE=b.make
def make(c):return NEW[c['assetId']](dict(c,palette=CONFIG['palette']))
b.make=lambda c:make(c) if c['assetId'] in NEW else ORIGINAL_MAKE(c)
ORIGINAL_SETUP=b.setup
def asset_preview_setup(*args,**kwargs):
    scene,camera_=ORIGINAL_SETUP(*args,**kwargs)
    sources=[o for o in bpy.data.objects if o.type=='MESH' and o.get('assetId') in NEW]
    if sources:
        low=b.bounds(sources)['min'][2]
        # Authored awning/road anchors have geometry below Z0. Do not hide it
        # behind the generic prop-preview floor. The world setup removes it.
        for floor_ in bpy.data.objects:
            if floor_.name.startswith('PREVIEW_ground'):floor_.location.z=low+.004
    return scene,camera_
b.setup=asset_preview_setup
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cafe(output):
    b.clear();templates={c['assetId']:ORIGINAL_MAKE(c) for c in b.CFG['assets']}
    root,instances,_=b.house('walter',templates);root.name='cafe-building';root['assetId']='cafe-building';root['floorLevelMeters']=.12
    root['temporaryCafeName']=LAYOUT['cafeName'];root['entrySourceXYZ']=[0,-.5,.12]
    for obj in list(root.children):
        id=obj.get('moduleId','');group=obj.get('hideGroup','')
        shop_side=group=='wall.east' and obj.location.y in (1,3) and id in ('bld_wall_window_200_001','bld_wall_solid_200_001','bld_window_110_001')
        if group=='porch' or id=='bld_porch_canopy_200_001' or group=='wall.south' and id in ('bld_wall_window_200_001','bld_window_110_001') or shop_side:
            for o in reversed(b.tree(obj)):bpy.data.objects.remove(o,do_unlink=True)
        else:obj.location.z-=.48
    for c in CONFIG['assets']:
        if c['assetId'] not in CAFE:continue
        t=make(c)
        locs=[(-2,0,.12),(2,0,.12)] if 'storefront' in c['assetId'] else [(-2,0,2.72),(0,0,2.72),(2,0,2.72)] if 'fascia' in c['assetId'] else [(0,-.16,2.76)]
        for loc in locs:b.instance(t,root,loc,0,'wall.south')
        side_locs=[(3,1,.12),(3,3,.12)] if 'storefront' in c['assetId'] else [(3,1,2.72),(3,3,2.72)] if 'fascia' in c['assetId'] else [(3.16,2,2.76)]
        for loc in side_locs:b.instance(t,root,loc,90,'wall.east')
        bpy.data.objects.remove(t,do_unlink=True)
    for template in templates.values():
        for obj in reversed(b.tree(template)):bpy.data.objects.remove(obj,do_unlink=True)
    # Distinct terracotta roof/cream commercial facade, without mesh edits.
    materials={}
    for obj in b.meshes(root):
        for slot in obj.material_slots:
            role=slot.material.name.split('__')[-1]
            if role in CONFIG['palette']:
                if role not in materials:materials[role]=make_material('cafe__'+role,CONFIG['palette'][role])
                slot.link='OBJECT';slot.material=materials[role]
    bpy.context.view_layer.update();report={'health':b.health(b.meshes(root)),'boundsSourceXYZ':b.bounds(b.meshes(root)),'worldGeometrySHA256':geometry_fingerprint(b.meshes(root))}
    folder=output/'assemblies';folder.mkdir(exist_ok=True);b.export(b.tree(root),folder/'cafe-building.glb')
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'cafe-building.blend'),compress=True)
    before=b.signature(b.meshes(root));bpy.ops.wm.open_mainfile(filepath=str(folder/'cafe-building.blend'),load_ui=False,use_scripts=False)
    after=b.signature(b.meshes(bpy.data.objects['cafe-building']));report['saveReopenExactGeometry']=before==after
    b.clear();bpy.ops.import_scene.gltf(filepath=str(folder/'cafe-building.glb'));report['glbRoundtripExactGeometry']=before==b.signature([o for o in bpy.data.objects if o.type=='MESH'])
    if not report['saveReopenExactGeometry'] or not report['glbRoundtripExactGeometry']:raise ValueError('Cafe persistence failed')
    b.dump(folder/'cafe-build-report.json',report)


def imported(path,asset):
    old=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));new=[o for o in bpy.data.objects if o not in old];roots=[o for o in new if o.parent not in new]
    if len(roots)!=1:raise ValueError('Expected one imported root '+asset)
    roots[0]['assetId']=asset;return roots[0]
def clone(source,parent):
    o=source.copy();bpy.context.collection.objects.link(o);o.parent=parent;o.hide_render=False
    for child in source.children:clone(child,o)
    return o
def setup():
    scene,camera=b.setup((1400,1050),24)
    for o in list(bpy.data.objects):
        if o.type=='LIGHT' or o.name.startswith('PREVIEW_ground'):bpy.data.objects.remove(o,do_unlink=True)
    d=bpy.data.lights.new('PREVIEW_sun','SUN');d.energy=2.0;d.angle=math.radians(28);d.color=(1,.91,.78)
    o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.rotation_euler=(math.radians(24),math.radians(-18),math.radians(-35))
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
    scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=45
    return scene,camera
def camera(s,c,pos,target,*,fov=40):
    c.data.type='PERSP';c.data.sensor_fit='VERTICAL';c.data.lens=c.data.sensor_height/(2*math.tan(math.radians(fov)/2));c.location=pos;aim(c,target);bpy.context.view_layer.update()
def shot(s,c,path,objects,record):
    b.render(s,path);record[path.stem]=dict(b.camera_record(s,c,objects),file=path.name,sha256=sha(path))


def scene(output,draft=False):
    b.clear();templates={}
    for c in CONFIG['assets']:
        asset=c['assetId']
        templates[asset]=make(c) if draft else imported(output/'assets'/asset/(asset+'.glb'),asset)
    refs=json.loads((ROOT/'configs/neighborhood-reference-locks.json').read_text())['references']
    for asset in refs:templates[asset]=imported(output/'reference'/asset/(asset+'.glb'),asset)
    templates['cafe-building']=imported(output/'assemblies/cafe-building.glb','cafe-building')
    allobjects=[];instances=[]
    for item in LAYOUT['instances']:
        t=templates[item['assetId']];o=clone(t,None);o.name=item['instanceId'];o['instanceId']=item['instanceId'];o['assetId']=item['assetId'];o['environmentGroup']=item['group'];o['futureInteractive']=not item['static']
        angle=Euler((math.radians(item.get('rotationXDegrees',0)),0,math.radians(item['rotationZDegrees'])),'XYZ')
        o.matrix_world=Matrix.Translation(item['positionSourceXYZ'])@angle.to_matrix().to_4x4()@Matrix.Scale(item['uniformScale'],4)@t.matrix_world
        if item.get('attachment'):
            o['mountedToInstanceId']=item['attachment']['parentInstanceId'];o['hideWithGroup']=item['attachment']['hideWithGroup']
        allobjects+=b.meshes(o);instances.append(o)
    for t in templates.values():
        for o in reversed(b.tree(t)):bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.view_layer.update();s,c=setup();s.cycles.samples=12 if draft else 24
    previews=output/'previews';previews.mkdir();views={}
    c.data.sensor_fit='HORIZONTAL';b.fit(s,c,allobjects,(-1,-1.3,1.3),1.04);shot(s,c,previews/'overview.png',allobjects,views)
    if draft:
        b.dump(output/'presentation.json',{'scope':'Early actual layout render; no final asset validation claim','views':views});return
    camera(s,c,(-21,-1.8,2.1),(-10.8,8,2.0),fov=52);shot(s,c,previews/'walter-street.png',allobjects,views)
    camera(s,c,(19,3,5.8),(10,-8,1.65),fov=48);shot(s,c,previews/'cafe-terrace.png',allobjects,views)
    s.render.resolution_x,s.render.resolution_y=1280,720
    settings=LAYOUT['cameras']['game16m'];focus=Vector(settings['focusSourceXYZ']);d=settings['distanceMeters'];pitch=math.radians(settings['pitchDegrees'])
    camera(s,c,focus+Vector((0,-math.cos(pitch)*d,math.sin(pitch)*d)),focus);shot(s,c,previews/'game-16m.png',allobjects,views)
    s.render.resolution_x,s.render.resolution_y=1400,1050
    # Review overlay is a separate removable collection, not a gameplay asset.
    from building_geometry import G,beam,finish
    g=G();route=LAYOUT['routes'][0]['pointsSourceXYZ']
    for i,(a,z) in enumerate(zip(route,route[1:])):beam(g,'proposed_path_'+str(i),Vector(a)+Vector((0,0,.05)),Vector(z)+Vector((0,0,.05)),.09,0)
    marker=finish({'assetId':'REVIEW_ROUTE','seed':8801,'palette':{'mark':{'color':'#E3B354','roughness':.6,'metallic':0}}},g,('mark',))
    c.data.sensor_fit='HORIZONTAL';b.fit(s,c,allobjects,(-1,-1.3,1.3),1.04);shot(s,c,previews/'walking-route.png',allobjects,views);marker.hide_render=True
    c.data.type='ORTHO';c.location=(0,0,70);aim(c,(0,0,0));c.data.ortho_scale=52
    # Top-down annotations use builtin Bfont in the review only, never asset text.
    labels=[]
    for name,loc in [('WALTER',(-11,11,6)),('NEIGHBOR',(2,10,6)),('JUNIPER CAFE',(10,-12,6)),('WILLOW ST',(-2,0,1)),('ENTRY',(-11,7.5,6.2)),('ENTRY',(10,-7.5,6.2))]:
        data=bpy.data.curves.new('REVIEW_'+name,'FONT');data.body=name;data.align_x='CENTER';data.size=.65;data.extrude=0;obj=bpy.data.objects.new(data.name,data);s.collection.objects.link(obj);obj.location=loc;labels.append(obj)
    shot(s,c,previews/'top-down.png',allobjects,views)
    for o in labels:bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.objects.remove(marker,do_unlink=True)
    folder=output/'scene';folder.mkdir();b.dump(folder/'layout.json',LAYOUT)
    b.fit(s,c,allobjects,(-1,-1.3,1.3),1.04)
    before=b.signature(allobjects);bpy.ops.wm.save_as_mainfile(filepath=str(folder/'neighborhood.blend'),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(folder/'neighborhood.blend'),load_ui=False,use_scripts=False)
    objects=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('PREVIEW_')]
    reopened=before==b.signature(objects)
    if not reopened:raise ValueError('Neighborhood save/reopen changed geometry')
    b.dump(output/'presentation.json',{'views':views,'sceneSaveReopenExactGeometry':reopened,'instances':len(instances),'triangles':before['triangles'],
        'scope':'Actual Blender previews. Route line/top-down labels are review overlays only. No Unity/game/nav verification.'})


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--draft',action='store_true');p.add_argument('--geometry-only',action='store_true');args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    output=Path(args.output).resolve();output.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve prior output')
    if bpy.app.version!=(4,5,14) or not bpy.app.background or bpy.app.online_access:raise ValueError('Pinned isolated offline Blender required')
    output.mkdir(parents=True);cp=bpy.context.preferences.addons['cycles'].preferences;cp.get_devices()
    b.dump(output/'environment.json',{'blender':bpy.app.version_string,'python':platform.python_version(),'devices':[{'name':d.name,'type':d.type} for d in cp.devices],'actualRenderDevice':'CPU','threads':4})
    if not args.draft:
        for config in CONFIG['assets']:b.inspect_module(config,output/'assets'/config['assetId'],not args.geometry_only)
    if not args.geometry_only:
        build_references(output);cafe(output);scene(output,args.draft)
    print('NEIGHBORHOOD_OK',flush=True)
if __name__=='__main__':main()
