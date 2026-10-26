"""Small geometry helpers for Walter's pack; original project code, no mesh imports.

Loft/rounded-outline conventions reuse the project-authored café method (PR35),
copied here to keep this main-based pack independent of that unmerged branch.
"""
import json
import math

import bmesh
import bpy
from mathutils import Vector
from art_pipeline.blender_build import make_material, linear_color


class G:
    def __init__(self):
        self.vertices=[];self.faces=[];self.materials=[];self.parts=[]

    def part(self,name,vertices,faces,material):
        offset=len(self.vertices);self.vertices.extend(vertices)
        self.faces.extend(tuple(offset+i for i in f) for f in faces)
        self.materials.extend([material]*len(faces) if isinstance(material,int) else material)
        self.parts.append(name)

    def loft(self,name,loops,material,cap_material=None):
        count=len(loops[0])
        if count<3 or any(len(loop)!=count for loop in loops):raise ValueError('Invalid closed loft')
        vertices=[p for loop in loops for p in loop]
        faces=[tuple(reversed(range(count)))];mats=[material if cap_material is None else cap_material]
        for level in range(len(loops)-1):
            for i in range(count):
                j=(i+1)%count
                faces.append((level*count+i,level*count+j,(level+1)*count+j,(level+1)*count+i));mats.append(material)
        faces.append(tuple((len(loops)-1)*count+i for i in range(count)))
        mats.append(material if cap_material is None else cap_material)
        self.part(name,vertices,faces,mats)

    def radial(self,name,levels,sides,material,phase=0):
        self.loft(name,[[(r*math.cos(phase+i*math.tau/sides),r*math.sin(phase+i*math.tau/sides),z)
                         for i in range(sides)] for z,r in levels],material)


def rounded_rect(width,depth,radius,segments=4):
    radius=min(radius,width*.499,depth*.499);points=[]
    for x,y,angle in ((width/2-radius,depth/2-radius,0),(-width/2+radius,depth/2-radius,90),
                       (-width/2+radius,-depth/2+radius,180),(width/2-radius,-depth/2+radius,270)):
        for i in range(segments+1):
            a=math.radians(angle+i*90/segments);p=(x+radius*math.cos(a),y+radius*math.sin(a))
            if not points or math.dist(points[-1],p)>1e-10:points.append(p)
    return points


def box(g,name,width,depth,zmin,zmax,material,center=(0,0),bevel=.006):
    b=min(bevel,(zmax-zmin)*.24,width*.12,depth*.12)
    radius=min(max(b*1.8,.001),width*.24,depth*.24)
    outer=rounded_rect(width,depth,radius,3)
    inner=rounded_rect(width-2*b,depth-2*b,max(radius-b,.0001),3)
    loops=[[(x+center[0],y+center[1],z) for x,y in outline]
           for z,outline in ((zmin,inner),(zmin+b,outer),(zmax-b,outer),(zmax,inner))]
    g.loft(name,loops,material)


def beam(g,name,a,b,width,material):
    a,b=Vector(a),Vector(b);direction=(b-a).normalized()
    u=direction.cross(Vector((0,0,1)))
    if u.length<.001:u=direction.cross(Vector((1,0,0)))
    u.normalize();v=direction.cross(u).normalized()
    section=((-0.32,-.5),(.32,-.5),(.5,-.32),(.5,.32),(.32,.5),(-.32,.5),(-.5,.32),(-.5,-.32))
    g.loft(name,[[tuple(p+u*x*width+v*y*width) for x,y in section] for p in (a,b)],material)


def finish(config,g,roles,smooth=False):
    if bpy.app.version!=(4,5,14):raise ValueError('Pin Blender4.5.14')
    if len(roles)>4 or len(g.materials)!=len(g.faces):raise ValueError('Invalid material assignment')
    # Place the root at the measured bottom-centre without changing any proportions.
    lo=[min(v[i] for v in g.vertices) for i in range(3)];hi=[max(v[i] for v in g.vertices) for i in range(3)]
    shift=((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2])
    vertices=[tuple(v[i]-shift[i] for i in range(3)) for v in g.vertices]
    prefix=config['assetId'];mesh=bpy.data.meshes.new(prefix+'__mesh');mesh.from_pydata(vertices,[],g.faces)
    for role in roles:
        spec=config['palette'][role];mat=make_material(prefix+'__'+role,spec)
        emission=spec.get('emissionColor',spec.get('emission'))
        if emission:
            node=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            node.inputs['Emission Color'].default_value=linear_color(emission)
            node.inputs['Emission Strength'].default_value=spec.get('emissionStrength',1)
        mesh.materials.append(mat)
    for p,index in zip(mesh.polygons,g.materials):p.material_index=index;p.use_smooth=smooth
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bm.to_mesh(mesh);bm.free();mesh.update()
    obj=bpy.data.objects.new(prefix,mesh);bpy.context.collection.objects.link(obj)
    obj['assetId']=prefix;obj['seed']=config['seed'];obj['constructionParts']=json.dumps(g.parts)
    obj['provenance']='Original procedural project geometry/materials; no external mesh/texture'
    obj['geometryRecenteringSourceXYZ']=list(shift)
    return obj
