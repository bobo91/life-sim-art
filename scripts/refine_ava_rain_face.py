"""Artist-directed adult face refinement on the actual Rain-derived surfaces."""
import json,math,bmesh,bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
from build_ava_rain import form,smooth,bell

def refine(objects,metadata,edit_data,source_static):
    by={o.name:o for o in objects};head=by['Rain_head'];sc=metadata['scale'];off=Vector(metadata['offset'])
    edits=json.loads(open(edit_data,encoding='utf8').read())['vertices']
    with bpy.data.libraries.load(str(source_static),link=False) as (src,dst):dst.objects=['Rain_head']
    baseline=dst.objects[0];assert len(baseline.data.vertices)==len(edits)==len(head.data.vertices)
    expected=[form(v.co,'head') for v in baseline.data.vertices];tree=KDTree(len(expected))
    for i,p in enumerate(expected):tree.insert(p,i)
    tree.balance();mapping=[];max_error=0
    for v in head.data.vertices:
        p=v.co/sc-off;q,i,dist=tree.find(p);mapping.append(i);max_error=max(max_error,dist)
    assert max_error<2e-5,('Before-face correspondence',max_error)
    def lid(p,upper,lower):
        c=Vector(((1 if p.x>0 else -1)*.04624*.88,-.08863,1.47326));d=p-c
        # Rotate the authored lid selection over the unchanged globe: narrower
        # aperture with globe contact, rather than shrinking the whole eye.
        angle=.17*min(1,upper)-.030*min(1,lower)
        co,si=math.cos(angle),math.sin(angle);d.y,d.z=d.y*co-d.z*si,d.y*si+d.z*co
        return c+d
    for v,i in zip(head.data.vertices,mapping):
        p=v.co/sc-off;e=edits[i];base=baseline.data.vertices[i].co.copy()
        # Preserve the successful neck/junction exactly; chin edit is confined
        # to the projecting facial surface ahead of it.
        if p.z<1.350 and p.y>-.075:continue
        delta=Vector(e['deltas']['LipsAdjust'])+.60*(Vector(e['deltas']['LipsWide.L'])+Vector(e['deltas']['LipsWide.R']))-.13*Vector(e['deltas']['LipsPuff_Upper'])-.10*Vector(e['deltas']['LipsPuff_Lower'])
        p+=form(base+delta,'head')-form(base,'head')
        p=lid(p,e['upperLid'],e['lowerLid'])
        front=1-smooth(-.075,-.025,p.y);x,y,z=p
        # Adult malar plane over a quieter lower cheek; retain the source nose
        # bridge instead of flattening the midface into a button profile.
        p.y+=.0045*bell(abs(x),.067,.024)*bell(z,1.413,.026)*front
        p.x*=1+.075*bell(z,1.354,.029)*front+.055*bell(z,1.329,.018)*front
        p.z-=.0038*bell(z,1.335,.023)*front
        p.y-=.0038*bell(z,1.440,.026)*bell(x,0,.025)*front
        p.z-=.0020*bell(z,1.434,.021)*bell(x,0,.024)*front
        # The brow ridge and separate brow surface descend as a coherent unit.
        p.z-=.0065*min(1,e['brow'])
        v.co=(p+off)*sc
    head.data.update()
    lashes=by['Rain_eyelashes']
    for v in lashes.data.vertices:
        p=v.co/sc-off;p=lid(p,1,0);v.co=(p+off)*sc
    lashes.data.update()
    brow=by['Rain_eyebrows']
    for v in brow.data.vertices:
        p=v.co/sc-off;t=smooth(.025,.078,abs(p.x))
        p.z=1.505+(p.z-1.505)*.83-.0075
        p.z=1.4975+(p.z-1.4975)*(1-.20*t)
        v.co=(p+off)*sc
    bm=bmesh.new();bm.from_mesh(brow.data)
    ends=[v for v in bm.verts if abs(v.co.x/sc-off.x)<.024 or abs(v.co.x/sc-off.x)>.071]
    for _ in range(3):bmesh.ops.smooth_vert(bm,verts=ends,factor=.30,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    bm.to_mesh(brow.data);bm.free()
    bpy.data.objects.remove(baseline,do_unlink=True)
    return {'face':'Native lip-neutral and restrained LipsWide/Puff deltas; authored eyelid masks rotated over unchanged eye globes; lower brows; calmer lower cheeks, supported jaw/chin and continuous nasal plane','sourceCorrespondenceMaxMetres':max_error,'eyeGlobesUnchanged':True,'bodyMeshUntouched':True}
