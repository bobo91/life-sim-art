"""Artist-directed static hair revision on actual Rain hair surfaces only.

The original long ponytail is bent into a tucked coil using an orthogonal
moving cross-section frame. Existing main hair, band and framing locks remain
Rain-derived; the head and body are never edited here.
"""
import math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _smooth(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3-2*t)


def _cat(points,t):
    t=max(0,min(len(points)-1-1e-6,t));i=int(t);u=t-i
    p=[Vector(points[max(0,min(len(points)-1,j))]) for j in [i-1,i,i+1,i+2]]
    return .5*((2*p[1])+(-p[0]+p[2])*u+(2*p[0]-5*p[1]+4*p[2]-p[3])*u*u+(-p[0]+3*p[1]-3*p[2]+p[3])*u*u*u)


def _normals(ob):
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data);bm.free();ob.data.update()
    for p in ob.data.polygons:p.use_smooth=True
    if ob.data.has_custom_normals:ob.data.normals_split_custom_set([(0,0,0)]*len(ob.data.loops))


def _tree_native(ob,scale,offset):
    ob.data.calc_loop_triangles()
    return BVHTree.FromPolygons([v.co/scale-offset for v in ob.data.vertices],[t.vertices for t in ob.data.loop_triangles],all_triangles=True)


def refine(objects,scale_metadata,source_static_path):
    """Return updated object list/change note; input may be a list or name map."""
    objects=list(objects.values()) if isinstance(objects,dict) else list(objects)
    by={o.name:o for o in objects};scale=float(scale_metadata['scale']);offset=Vector(scale_metadata['offset'])
    old=by['Ava_LooseBun_FromRainPonytail'];main=by['Rain_hair_main'];mat=old.data.materials[0];parent=old.parent
    source=Path(source_static_path).resolve()
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):
        assert 'Rain_hair_ponytail' in src.objects
        dst.objects=['Rain_hair_ponytail']
    bun=dst.objects[0];bpy.context.scene.collection.objects.link(bun)
    bun.name='Ava_LooseBun_FromRainPonytail_Refined';bun.parent=parent
    bun.data.materials.clear();bun.data.materials.append(mat)
    for p in bun.data.polygons:p.material_index=0
    points=[v.co.copy() for v in bun.data.vertices]
    # Source-section midlines use the envelope rather than vertex density,
    # retaining Rain's asymmetric cross-section and authored surface ridges.
    centers=[]
    for i in range(33):
        y=.081+(.509-.081)*i/32
        near=[p for p in points if abs(p.y-y)<.017]
        if len(near)<8:near=sorted(points,key=lambda p:abs(p.y-y))[:16]
        centers.append(Vector(((min(p.x for p in near)+max(p.x for p in near))/2,y,(min(p.z for p in near)+max(p.z for p in near))/2)))
    # The two ends tuck into the gather and the centre respectively. A compact
    # coil with a filled centre avoids both the previous egg and an open donut.
    path=[(0,.100,1.582),(.031,.119,1.592),(.043,.127,1.627),(.011,.134,1.653),(-.029,.133,1.643),(-.039,.126,1.608),(-.008,.121,1.594),(.018,.139,1.615),(.005,.146,1.629)]
    path=[(x*.84,.112+(y-.125)*.80,z-.023) for x,y,z in path]
    for v in bun.data.vertices:
        p=v.co.copy();t=max(0,min(1,(p.y-.081)/(.509-.081)));u=t*32;i=min(31,int(u));c=centers[i].lerp(centers[i+1],u-i)
        pt=t*(len(path)-1);q=_cat(path,pt)
        tangent=(_cat(path,pt+.001)-_cat(path,pt-.001)).normalized()
        depth=Vector((0,1,0));depth=(depth-tangent*depth.dot(tangent)).normalized();radial=depth.cross(tangent).normalized()
        # Controlled roll keeps the source section's ridges changing naturally
        # around the pinned mass without abrupt cross-section inversions.
        angle=.22*math.sin(math.pi*t)
        dx=(p.x-c.x)*.72;dz=(p.z-c.z)*.92
        rr=dx*math.cos(angle)-dz*math.sin(angle);dd=dx*math.sin(angle)+dz*math.cos(angle)
        native=q+radial*rr+depth*dd
        v.co=(native+offset)*scale
    bun['rainSourceObject']='GEO-rain-hair_ponytail';bun['assetId']='chr_npc_ava_morgan_001'
    bun['edit']='Actual Rain ponytail recontoured in an orthogonal frame into one tucked, loosely pinned coil; no primitive replacement'
    # Source root openings were hidden inside the old ponytail gather. Close
    # those existing boundaries now that the same surface is tucked inward.
    bm=bmesh.new();bm.from_mesh(bun.data);boundary=[e for e in bm.edges if e.is_boundary]
    if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
    bm.to_mesh(bun.data);bm.free()
    _normals(bun)
    bpy.context.view_layer.objects.active=bun
    mod=bun.modifiers.new('RainSurfaceFinish','SUBSURF');mod.levels=1;mod.render_levels=1
    bpy.ops.object.modifier_apply(modifier=mod.name)
    _normals(bun)
    objects.remove(old);bpy.data.objects.remove(old,do_unlink=True);objects.append(bun)
    # A tucked continuation of the same authored ponytail surface fills the
    # coil's centre. Offset/roll avoid aligned hollow ends and keep the outer
    # wrap's silhouette intact; the overlap is hidden inside the pinned mass.
    core=bun.copy();core.data=bun.data.copy();bpy.context.scene.collection.objects.link(core)
    core.name='Ava_BunTuckedCentre_FromRainPonytail';center=Vector((0,.114,1.608));ca=math.cos(.70);sa=math.sin(.70)
    for v in core.data.vertices:
        p=v.co/scale-offset;d=p-center;d=Vector((ca*d.x+sa*d.z,d.y,-sa*d.x+ca*d.z))*.49
        v.co=(center+d+Vector((.005,.018,.002))+offset)*scale
    core['rainSourceObject']='GEO-rain-hair_ponytail';core['edit']='Tucked inner continuation copied from the same deformed Rain hair surface, closing the wrap centre'
    _normals(core);objects.append(core)
    # Weld only the tucked bun contact into a continuous sculpted surface.
    # This preserves the volume made from Rain's source while removing a hard
    # visible crossing where the inner continuation goes under the outer wrap.
    bpy.ops.object.select_all(action='DESELECT');bun.select_set(True);core.select_set(True);bpy.context.view_layer.objects.active=bun
    bpy.ops.object.join();objects.remove(core)
    weld=bun.modifiers.new('TuckedContactWeld','REMESH');weld.mode='VOXEL';weld.voxel_size=.0012;weld.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=weld.name)
    smooth=bun.modifiers.new('SoftPinnedContact','SMOOTH');smooth.factor=.65;smooth.iterations=10
    bpy.ops.object.modifier_apply(modifier=smooth.name);_normals(bun)
    bun['edit']='Actual Rain ponytail recontoured into compact outer wrap and tucked inner continuation; 1.2 mm contact weld and soft surface finish'
    # Keep the actual source band, repositioned at the gather rather than
    # exposing a narrow stem between scalp hair and bun volume.
    band=by.get('Rain_hairband')
    if band:
        center=Vector((0,.1005,1.5775));target=Vector((0,.102,1.574))
        for v in band.data.vertices:
            p=v.co/scale-offset;d=p-center;d.x*=1.08;d.z*=.86
            v.co=(target+d+offset)*scale
        _normals(band)
    # Preserve the authored curved roots with a slight outward ease. Lower
    # loose curls retain their shape and stay clear of the face/temple surface.
    head=_tree_native(by['Rain_head'],scale,offset)
    locks=[by.get('Rain_hair_strand'),by.get('Ava_RightFramingStrand')]
    for lock in locks:
        if lock is None:continue
        native=[v.co/scale-offset for v in lock.data.vertices];lo=min(p.z for p in native);hi=max(p.z for p in native);sign=-1 if sum(p.x for p in native)<0 else 1
        for v,p in zip(lock.data.vertices,native):
            root=_smooth(lo+.66*(hi-lo),hi,p.z)
            # Keep the authored curved section intact. Per-vertex projection
            # flattens its thin root into an artificial cut edge.
            near,n,_,d=head.find_nearest(p)
            # Preserve the source attachment exactly. Only the lower loose curl
            # gets a soft clearance correction, without flattening the root.
            if near is not None and d<.010 and (p-near).dot(n)<.0015:
                p=p.lerp(near+n*.0015,1-root)
            v.co=(p+offset)*scale
        _normals(lock)
    # Softer directional highlights keep the hair brunette under the warm key.
    bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Roughness'].default_value=.67
    if 'Anisotropic IOR Level' in bsdf.inputs:bsdf.inputs['Anisotropic IOR Level'].default_value=.22
    if 'Specular IOR Level' in bsdf.inputs:bsdf.inputs['Specular IOR Level'].default_value=.34
    if 'Sheen Weight' in bsdf.inputs:bsdf.inputs['Sheen Weight'].default_value=.09
    bpy.context.view_layer.update()
    return {'objects':objects,'changes':['Actual Rain ponytail bent into compact wrap with continuous cross-section frame and tucked inner continuation','Existing hairband seated at gather; authored framing-lock root curvature retained','Native loose curl shapes retained; near-face clearance corrected','Brunette material softer anisotropic highlights']}
