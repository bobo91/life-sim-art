"""Small shared static review tools for the Rain-derived Ava prototype."""
import bpy,math,hashlib,json
from pathlib import Path
from mathutils import Vector

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def linear(rgb):return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb)
def material(name,color,rough=.78,texture=None,normal=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');b.inputs['Base Color'].default_value=(*linear(color),1);b.inputs['Roughness'].default_value=rough;m.diffuse_color=(*linear(color),1)
    if texture:
        i=bpy.data.images.load(str(texture),check_existing=True);i.pack();n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=i;m.node_tree.links.new(n.outputs['Color'],b.inputs['Base Color'])
    if normal:
        i=bpy.data.images.load(str(normal),check_existing=True);i.colorspace_settings.name='Non-Color';i.pack();n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=i;nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.4;m.node_tree.links.new(n.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],b.inputs['Normal'])
    return m
def assign(o,m):
    o.data.materials.clear();o.data.materials.append(m)
    for p in o.data.polygons:p.material_index=0
def studio(out,samples=24):
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=samples;s.cycles.use_denoising=True;s.cycles.seed=41032;s.render.threads_mode='FIXED';s.render.threads=6;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.view_settings.gamma=1
    world=bpy.data.worlds.new('ReviewWorld');world.use_nodes=True;s.world=world;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.58,.61,.66,1);bg.inputs['Strength'].default_value=.35
    target=Vector((0,0,.85));lights=[]
    for name,xyz,power,size in [('Key',(-2.55,-3.4,4.59),795,1.62),('Fill',(3.06,-1.19,3.06),286,2.125),('Rim',(1.7,2.55,4.25),477,1.7)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=xyz;aim(o,target);lights.append(o)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.003));floor=bpy.context.object;floor.name='ReviewFloor';floor.data.materials.append(material('ReviewFloorMat',(.57,.59,.57),.9))
    d=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new(d.name,d);s.collection.objects.link(cam);s.camera=cam
    return cam,lights,bg
def render(cam,out,name,kind='full',az=0,focus=None,scale=None):
    s=bpy.context.scene;cd=cam.data;ang=math.radians(az);f=Vector(focus or (0,-.02,1.515 if kind=='face' else .86))
    cd.type='PERSP' if kind=='game' else 'ORTHO'
    if kind=='game':
        f=Vector((0,0,1));cd.sensor_fit='VERTICAL';cd.sensor_height=32;cd.lens=32/(2*math.tan(math.radians(40)/2));dist=16;el=math.radians(50);cam.location=f+Vector((math.sin(ang)*dist*math.cos(el),-math.cos(ang)*dist*math.cos(el),dist*math.sin(el)));s.render.resolution_x=1280;s.render.resolution_y=720
    else:
        cd.sensor_fit='AUTO';cd.ortho_scale=scale or (.48 if kind=='face' else 2.12 if kind=='isometric' else 1.98);cam.location=f+Vector((5*math.sin(ang),-5*math.cos(ang),5/math.sqrt(2) if kind=='isometric' else .04 if kind=='three' else 0));s.render.resolution_x=1000 if kind=='face' else 960;s.render.resolution_y=1000 if kind=='face' else 1120
    aim(cam,f);p=Path(out)/(name+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    return {'name':name,'kind':kind,'camera':list(cam.location),'focus':list(f),'orthoScale':cd.ortho_scale if kind!='game' else None,'verticalFov':math.degrees(cd.angle_y) if kind=='game' else None,'resolution':[s.render.resolution_x,s.render.resolution_y],'sha256':sha(p)}
