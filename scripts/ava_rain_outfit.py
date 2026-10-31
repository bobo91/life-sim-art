"""A fitted outfit edited from Rain's authored anatomy, not primitive body lofts."""
import bpy,bmesh,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def mesh(name,verts,faces,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);me.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    return o
def apply(o,kind,**values):
    bpy.context.view_layer.objects.active=o;m=o.modifiers.new(kind,kind)
    for k,v in values.items():setattr(m,k,v)
    bpy.ops.object.modifier_apply(modifier=m.name)
def tree(o):
    o.data.calc_loop_triangles();return BVHTree.FromPolygons([v.co for v in o.data.vertices],[t.vertices for t in o.data.loop_triangles],all_triangles=True)
def strip(name,points,width,mat,axis=(1,0,0),thickness=.002):
    u=Vector(axis).normalized();vv=[]
    for p in points:
        q=Vector(p);vv.extend([q-u*width/2,q+u*width/2])
    ff=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)]
    o=mesh(name,vv,ff,mat);apply(o,'SOLIDIFY',thickness=thickness,offset=0);apply(o,'BEVEL',width=.0007,segments=2);return o
def build(body,jeans,shoes,mats):
    # Duplicate actual neck/shoulder/chest/upper-arm topology for the garment.
    me=body.data.copy();top=bpy.data.objects.new('Ava_CreamTop_RainSurface',me);bpy.context.scene.collection.objects.link(top)
    bm=bmesh.new();bm.from_mesh(me)
    for co,no in [((0,0,.895),(0,0,1)),((.405,0,0),(-1,0,0)),((-.405,0,0),(1,0,0))]:
        geom=list(bm.verts)+list(bm.edges)+list(bm.faces)
        bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-7,plane_co=co,plane_no=no,clear_inner=True,clear_outer=False)
    # Cut a true neckline around the neck, retaining the complete shoulder tops.
    neck_faces=[f for f in bm.faces if sum((a/b)**2 for a,b in zip(f.calc_center_median()-Vector((0,.002,1.312)),(.064,.067,.087)))<1]
    bmesh.ops.delete(bm,geom=neck_faces,context='FACES')
    boundary=[v for v in bm.verts if v.is_boundary and v.co.z>1.22 and abs(v.co.x)<.13]
    for _ in range(10):
        old={v:v.co.copy() for v in boundary}
        for v in boundary:
            neighbours=[e.other_vert(v) for e in v.link_edges if e.is_boundary and e.other_vert(v) in old]
            if len(neighbours)==2:v.co=old[v].lerp((old[neighbours[0]]+old[neighbours[1]])/2,.5)
    # Retain a clean level hem instead of averaging cut and uncut triangulation.
    bm.normal_update()
    # Small garment ease follows the actual muscle/chest surface normal.
    for v in bm.verts:
        z=v.co.z;ease=.004+.007*math.exp(-((z-1.00)/.12)**2)*(1-min(1,abs(v.co.x)/.19))
        v.co+=v.normal*ease
        if v.co.y<-.025 and abs(v.co.x)<.15 and z<1.08:
            v.co.y-=.0015*math.sin(40*z+14*v.co.x)*math.exp(-((z-.98)/.08)**2)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.materials.clear();me.materials.append(mats['cream'])
    for p in me.polygons:p.material_index=0;p.use_smooth=True
    top['rainSourceObject']='GEO-rain-body_nomask';top['edit']='Fitted clothing duplicate of authored torso/shoulder/upper-arm topology, trimmed/eased; no replacement anatomy'
    apply(top,'SUBSURF',levels=1,render_levels=1)
    # Garment hem must sit outside the source jeans, including the rear seat.
    jb=tree(jeans)
    for v in top.data.vertices:
        if v.co.z<1.01:
            radial=Vector((v.co.x,v.co.y,0)).normalized();hit,n,idx,d=jb.ray_cast(radial+Vector((0,0,v.co.z)),-radial,2)
            if hit is not None:
                target=hit+radial*.009
                if Vector((target.x,target.y,0)).length>Vector((v.co.x,v.co.y,0)).length:v.co.x=target.x;v.co.y=target.y
    # A small knit edge follows the existing rounded neckline boundary.
    eb=bmesh.new();eb.from_mesh(top.data);boundary_ids={v.index for v in eb.verts if v.is_boundary};eb.free()
    # Roll the real sleeve boundary section. It retains the source arm contour.
    rolls=[]
    for sign in (-1,1):
        pts=[v.co.copy() for v in top.data.vertices if v.index in boundary_ids and abs(v.co.x-sign*.405)<.0003]
        if len(pts)<6:continue
        cy=sum(p.y for p in pts)/len(pts);cz=sum(p.z for p in pts)/len(pts)
        pts=sorted(pts,key=lambda p:math.atan2(p.z-cz,p.y-cy));n=len(pts);vv=[];ff=[]
        for k in range(8):
            a=2*math.pi*k/8
            for p in pts:
                radial=Vector((0,p.y-cy,p.z-cz)).normalized();vv.append(p+Vector((sign*.006*math.cos(a),0,0))+radial*(.005+.004*math.sin(a)))
        for k in range(8):
            for j in range(n):ff.append((k*n+j,k*n+(j+1)%n,((k+1)%8)*n+(j+1)%n,((k+1)%8)*n+j))
        rolls.append(mesh('Ava_RolledSleeve_'+str(sign),vv,ff,mats['cream']))
    apply(top,'SOLIDIFY',thickness=.0025,offset=-1)
    # Hide skin covered by actual fitted clothes; exposed authored surfaces stay.
    bm=bmesh.new();bm.from_mesh(body.data)
    remove=[]
    for f in bm.faces:
        c=f.calc_center_median()
        visible=abs(c.x)>.395 or c.z>1.245 or (.09<c.z<.155)
        if not visible:remove.append(f)
    bmesh.ops.delete(bm,geom=remove,context='FACES');unused=[v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm,geom=unused,context='VERTS');bm.to_mesh(body.data);bm.free()
    # Source jeans/shoes retain the professionally authored shape and folds.
    for ob,mat in [(jeans,mats['denim']),(shoes,mats['shoe'])]:
        ob.data.materials.clear();ob.data.materials.append(mat)
        for p in ob.data.polygons:p.material_index=0
    # Every front panel point is fitted by ray to the actual shirt/jeans surfaces.
    trees=[tree(top),tree(jeans)]
    def front(x,z):
        hits=[]
        for b in trees:
            hit,normal,idx,dist=b.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
            if hit is not None:hits.append(hit.y)
        return min(hits) if hits else -.09
    rows=[(.637,.151),(.648,.165),(.70,.166),(.78,.160),(.87,.151),(.95,.137),(1.015,.120),(1.065,.096),(1.12,.079),(1.196,.074)]
    dense=[]
    for k in range(29):
        z=.637+(1.196-.637)*k/28
        for j in range(len(rows)-1):
            if rows[j][0]<=z<=rows[j+1][0]:
                t=(z-rows[j][0])/(rows[j+1][0]-rows[j][0]);dense.append((z,rows[j][1]*(1-t)+rows[j+1][1]*t));break
    rows=dense;vv=[];ff=[];N=24
    depths=[min(front(w*(-1+2*j/16),z) for j in range(17))-.014 for z,w in rows]
    for _ in range(2):depths=[min(depths[i],sum(depths[max(0,i-1):min(len(depths),i+2)])/len(depths[max(0,i-1):min(len(depths),i+2)])) for i in range(len(depths))]
    for i,(z,w) in enumerate(rows):
        for j in range(N+1):
            t=-1+2*j/N;x=w*t;y=depths[i]+(.012 if z>1.03 else .022)*t*t
            if z<.94:y-=.0018*math.cos(t*math.pi*3)*(1-(z-.637)/.31)
            vv.append((x,y,z+.006*t*t if i<2 else z))
    for i in range(len(rows)-1):
        for j in range(N):a=i*(N+1)+j;ff.append((a,a+1,a+N+2,a+N+1))
    apron=mesh('Ava_FittedCafeApron',vv,ff,mats['olive']);apply(apron,'SOLIDIFY',thickness=.0025,offset=0)
    # Quiet patch pocket follows the apron instead of a floating rigid box.
    av=tree(apron);vv=[];ff=[]
    for i,z in enumerate([.755,.760,.79,.84,.884,.888]):
        w=.091 if i==0 else .101
        for j in range(13):
            x=w*(-1+2*j/12);hit,_,_,_=av.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2);vv.append((x,(hit.y if hit is not None else front(x,z))-.0028,z))
    for i in range(5):
        for j in range(12):a=i*13+j;ff.append((a,a+1,a+14,a+13))
    pocket=mesh('Ava_ApronPocket',vv,ff,mats['olive']);apply(pocket,'SOLIDIFY',thickness=.0015,offset=0)
    # Leather shoulder straps, projected to the fitted shirt's actual surface.
    tb=tree(top);straps=[]
    for sign in (-1,1):
        path=[(sign*.069,-.11,1.190),(sign*.075,-.09,1.225),(sign*.083,-.055,1.255),(sign*.09,0,1.265),(sign*.092,.055,1.245),(sign*.088,.08,1.19),(sign*.078,.09,1.10),(sign*.065,.09,.987)]
        fitted=[]
        for p in path:
            near,n,idx,d=tb.find_nearest(Vector(p));fitted.append(near+n*.003 if near is not None else Vector(p))
        # Keep buckle attachments on apron bib; the rest contacts shirt.
        fitted[0]=Vector((sign*.069,front(sign*.069,1.19)-.012,1.19))
        straps.append(strip('Ava_LeatherStrap_'+str(sign),fitted,.013,mats['leather'],thickness=.002))
    # Waist band follows the actual garment cross-section.
    vv=[];ff=[];N=64
    for z in [.974,.994]:
        for j in range(N):
            a=2*math.pi*j/N;v=Vector((math.cos(a),math.sin(a),0));origin=v+Vector((0,0,z));hit,n,_,_=tb.ray_cast(origin,-v,2)
            p=hit+n*.004 if hit is not None else Vector((.13*math.cos(a),.09*math.sin(a),z));vv.append(p)
    for j in range(N):ff.append((j,(j+1)%N,N+(j+1)%N,N+j))
    belt=mesh('Ava_ApronTie',vv,ff,mats['olive']);apply(belt,'SOLIDIFY',thickness=.002,offset=0)
    # Two soft tails and a small tied loop, at the true back waist.
    back=tb.ray_cast(Vector((0,1,.985)),Vector((0,-1,0)),2)[0];by=(back.y if back is not None else .09)+.008
    tails=[]
    for sign in (-1,1):
        tails.append(strip('Ava_TieTail_'+str(sign),[(sign*.006,by,.985),(sign*.018,by+.004,.956),(sign*.023,by+.005,.915),(sign*.020,by+.003,.88)],.014,mats['olive']))
        points=[(sign*(.025-.025*math.cos(a)),by+.005*math.sin(a),.985+.009*math.sin(a)) for a in [2*math.pi*j/24 for j in range(25)]]
        tails.append(strip('Ava_TieLoop_'+str(sign),points,.007,mats['olive'],axis=(0,0,1)))
    return [body,top,jeans,shoes,apron,pocket,belt]+rolls+straps+tails
