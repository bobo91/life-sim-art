"""Original parametric geometry helpers for ART-041; metres, Z up, -Y front."""
import math
import bpy
import bmesh
from mathutils import Vector

ASSET = 'chr_ava_morgan_041'

def linear(c):
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in c)

PALETTE = {
    'skin': linear((.73,.49,.36)), 'lip': linear((.59,.345,.28)),
    'hair': linear((.19,.105,.065)), 'cream': linear((.85,.81,.70)),
    'olive': linear((.27,.33,.21)), 'denim': linear((.18,.22,.26)),
    'shoe': linear((.72,.71,.65)), 'leather': linear((.33,.20,.115)),
    'detail': linear((.65,.48,.22)),
}

def material(key):
    m = bpy.data.materials.new('AVA041_'+key)
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value = (*PALETTE[key],1)
    bs.inputs['Roughness'].default_value = {'skin':.72,'lip':.62,'hair':.8,'detail':.43}.get(key,.85)
    if key == 'detail': bs.inputs['Metallic'].default_value = .45
    m.diffuse_color = (*PALETTE[key],1)
    return m

def mesh(name, verts, faces, mat, smooth=True):
    me = bpy.data.meshes.new(name+'_mesh'); me.from_pydata(verts,[],faces); me.update()
    ob = bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat); ob['asset_id'] = ASSET
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    for p in me.polygons: p.use_smooth = smooth
    return ob

def tube(name, points, radii, mat, sides=8, depth=None):
    pts=[Vector(p) for p in points]; verts=[]; faces=[]
    for i,p in enumerate(pts):
        t=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        ref=Vector((0,1,0)) if abs(t.y)<.9 else Vector((1,0,0))
        u=t.cross(ref).normalized();v=t.cross(u).normalized()
        rad=radii[i] if isinstance(radii,(list,tuple)) else radii
        dep=depth[i] if isinstance(depth,(list,tuple)) else (depth if depth is not None else rad)
        for j in range(sides):
            a=2*math.pi*j/sides;verts.append(p+u*math.cos(a)*rad+v*math.sin(a)*dep)
    for i in range(len(pts)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
    faces.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))])
    return mesh(name,verts,faces,mat)

def interp(table,z):
    if z<=table[0][0]:return table[0][1:]
    if z>=table[-1][0]:return table[-1][1:]
    for i in range(len(table)-1):
        if table[i][0]<=z<=table[i+1][0]:
            dz=table[i+1][0]-table[i][0];t=(z-table[i][0])/dz
            # Cubic Hermite with a continuous slope, avoiding stacked profile bands.
            p0=table[max(0,i-1)];p1=table[i];p2=table[i+1];p3=table[min(len(table)-1,i+2)]
            return tuple((2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*(b0-a0)/(p2[0]-p0[0])*dz
                         +(-2*t**3+3*t*t)*b+(t**3-t*t)*(b1-a1)/(p3[0]-p1[0])*dz
                         for a,b,a0,b0,a1,b1 in zip(p1[1:],p2[1:],p0[1:],p2[1:],p1[1:],p3[1:]))

def paint(ob, func=None):
    """Explicit linear COLOR_0, matching core glTF vertex-colour multiplication."""
    attr=ob.data.color_attributes.get('Color') or ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
    for poly in ob.data.polygons:
        mat=ob.data.materials[poly.material_index];key=mat.name.removeprefix('AVA041_')
        col=PALETTE.get(key,PALETTE['detail'])
        for li in poly.loop_indices:
            p=ob.data.vertices[ob.data.loops[li].vertex_index].co
            attr.data[li].color=(*(func(p,col) if func else col),1)
    ob.data.color_attributes.active_color=attr

def enable_vertex_colors(mats):
    for mat in mats.values():
        bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Color'
        bs.inputs['Base Color'].default_value=(1,1,1,1)
        mat.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color'])

def solidify(ob,thickness=.002):
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    m=ob.modifiers.new('Original garment thickness','SOLIDIFY');m.thickness=thickness
    bpy.ops.object.modifier_apply(modifier=m.name);ob.select_set(False)
    return ob
