"""ART-041: original static Ava garments and limbs, all geometry authored here.

No source mesh, rig, image or external geometry is loaded. Coordinates are metres,
Blender Z-up, front -Y. This is a visual review outfit, not deformation topology.
"""
import math
import bpy
import bmesh
from mathutils import Vector

ASSET_ID = 'chr_ava_morgan_041'


def _mesh(name, verts, faces, mat, smooth=True, subdiv=0):
    me = bpy.data.meshes.new(name + '_mesh')
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob['asset_id'] = ASSET_ID
    ob['construction'] = 'Original procedural geometry; static Phase A visual review'
    me.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    if subdiv:
        mod = ob.modifiers.new('Authored surface smoothing', 'SUBSURF')
        mod.levels = subdiv; mod.render_levels = subdiv
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob


def _loft(name, rows, mat, sides=20, subdiv=1, caps=True):
    """Horizontal elliptical rings: z, centre-x, centre-y, half-width, half-depth.

    A seeded-looking fixed cloth wave is analytic, hence fully reproducible.
    Optional sixth field supplies a small cross-section irregularity amplitude.
    """
    verts = []
    for j, row in enumerate(rows):
        z, cx, cy, rx, ry = row[:5]
        wave = row[5] if len(row) > 5 else 0
        for k in range(sides):
            a = math.tau*k/sides
            d = 1 + wave*(.6*math.cos(5*a+j*.75)+.4*math.sin(3*a-j*.65))
            verts.append((cx+rx*math.cos(a)*d, cy+ry*math.sin(a)*d, z))
    faces = []
    for j in range(len(rows)-1):
        for k in range(sides):
            a=j*sides+k; b=j*sides+(k+1)%sides
            faces.append((a,b,b+sides,a+sides))
    if caps:
        faces.append(tuple(reversed(range(sides))))
        faces.append(tuple((len(rows)-1)*sides+k for k in range(sides)))
    return _mesh(name,verts,faces,mat,subdiv=subdiv)


def _tube(name, points, radii, mat, sides=10, subdiv=1):
    """Continuous tapered sweep; frame follows centre-line, avoiding glued spheres."""
    verts=[]
    pp=[Vector(p) for p in points]
    for j,p in enumerate(pp):
        tangent=(pp[min(j+1,len(pp)-1)]-pp[max(j-1,0)]).normalized()
        ref=Vector((0,1,0))
        if abs(tangent.dot(ref))>.9: ref=Vector((1,0,0))
        u=tangent.cross(ref).normalized(); v=tangent.cross(u).normalized()
        rad=radii[j]
        rx,ry=rad if isinstance(rad,(tuple,list)) else (rad,rad)
        for k in range(sides):
            a=math.tau*k/sides
            verts.append(tuple(p+u*(rx*math.cos(a))+v*(ry*math.sin(a))))
    faces=[]
    for j in range(len(pp)-1):
        for k in range(sides):
            a=j*sides+k; b=j*sides+(k+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple((len(pp)-1)*sides+k for k in range(sides)))
    return _mesh(name,verts,faces,mat,subdiv=subdiv)


def _ribbon(name, points, width, mat, thickness=.002, subdiv=1):
    """Solid rectangular curved ribbon, width follows a local surface direction."""
    pp=[Vector(p) for p in points]; verts=[]
    for j,p in enumerate(pp):
        tangent=(pp[min(j+1,len(pp)-1)]-pp[max(j-1,0)]).normalized()
        # A strap along torso front/back is locally horizontal across its width.
        across=Vector((1,0,0))
        if abs(tangent.dot(across))>.9: across=Vector((0,0,1))
        across=(across-tangent*tangent.dot(across)).normalized()
        normal=tangent.cross(across).normalized()
        for aa,bb in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            verts.append(tuple(p+across*(aa*width/2)+normal*(bb*thickness/2)))
    faces=[]
    for j in range(len(pp)-1):
        for k in range(4):
            faces.append((4*j+k,4*j+(k+1)%4,4*(j+1)+(k+1)%4,4*(j+1)+k))
    faces += [(3,2,1,0),tuple(4*(len(pp)-1)+k for k in range(4))]
    return _mesh(name,verts,faces,mat,subdiv=subdiv)


def _ellipsoid(name,center,scale,mat,segs=16,rings=8):
    verts=[(center[0],center[1],center[2]-scale[2])]
    for j in range(1,rings):
        ph=-math.pi/2+math.pi*j/rings
        for k in range(segs):
            a=math.tau*k/segs
            verts.append((center[0]+scale[0]*math.cos(ph)*math.cos(a),center[1]+scale[1]*math.cos(ph)*math.sin(a),center[2]+scale[2]*math.sin(ph)))
    top=len(verts);verts.append((center[0],center[1],center[2]+scale[2]))
    faces=[]
    for k in range(segs): faces.append((0,1+(k+1)%segs,1+k))
    for j in range(rings-2):
        for k in range(segs):
            a=1+j*segs+k;b=1+j*segs+(k+1)%segs
            faces.append((a,b,b+segs,a+segs))
    for k in range(segs): faces.append((top,1+(rings-2)*segs+k,1+(rings-2)*segs+(k+1)%segs))
    return _mesh(name,verts,faces,mat)


def _bow_loop(name,sign,mat):
    """Small closed flat cloth loop with a constant face normal, no frame twist."""
    n=20;verts=[]
    for j in range(n):
        a=math.tau*j/n
        p=Vector((sign*.026+sign*.027*math.cos(a),.114,1.046+.012*math.sin(a)))
        normal=Vector((sign*math.cos(a)/.027,0,math.sin(a)/.012)).normalized()
        for w,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            verts.append(tuple(p+normal*(w*.003)+Vector((0,y*.001,0))))
    faces=[]
    for j in range(n):
        nxt=(j+1)%n
        for k in range(4):faces.append((j*4+k,j*4+(k+1)%4,nxt*4+(k+1)%4,nxt*4+k))
    return _mesh(name,verts,faces,mat,smooth=False)


def _union_hand(parts,name):
    """Voxel union limited to a hand removes all finger/palm intersection seams."""
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join(); ob=bpy.context.object;ob.name=name
    rem=ob.modifiers.new('Original hand surface union','REMESH')
    rem.mode='VOXEL';rem.voxel_size=.0025;rem.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    sm=ob.modifiers.new('Soft hand transitions','SMOOTH');sm.factor=.6;sm.iterations=3
    bpy.ops.object.modifier_apply(modifier=sm.name)
    ob.data.calc_loop_triangles()
    de=ob.modifiers.new('Static hand budget','DECIMATE');de.ratio=min(1.0,750/max(1,len(ob.data.loop_triangles)))
    bpy.ops.object.modifier_apply(modifier=de.name)
    for p in ob.data.polygons:p.use_smooth=True
    return ob


def _apron(mats):
    # Broad enough to read at distance, with a shaped bib and naturally flared hem.
    rows=[(.695,.184,.103),(.703,.192,.106),(.72,.194,.110),(.79,.188,.117),(.88,.179,.125),(.965,.157,.107),(1.035,.143,.106),(1.10,.111,.107),(1.185,.096,.113),(1.224,.092,.102),(1.232,.091,.100)]
    n=20;verts=[]
    for j,(z,width,depth) in enumerate(rows):
        for k in range(n+1):
            t=-1+2*k/n
            wrap=.14 if z>=1.10 else .43
            y=-depth*(1-wrap*t*t)
            y-=.0025*math.sin(math.pi*t*3+.35)*math.sin(math.pi*j/(len(rows)-1))
            zz=z+(.005*t*t if j<3 else 0)
            verts.append((width*t,y,zz))
    faces=[]
    for j in range(len(rows)-1):
        for k in range(n):
            a=j*(n+1)+k;faces.append((a,a+1,a+n+2,a+n+1))
    ob=_mesh('Ava_apron_shaped_front',verts,faces,mats['olive'],subdiv=0)
    so=ob.modifiers.new('Apron folded edge thickness','SOLIDIFY');so.thickness=.003;so.offset=0
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=so.name)
    result=[ob]
    # Patch pocket with a gently rounded base, shaped to the apron surface.
    pocket=[(.794,.102,.120),(.798,.114,.123),(.82,.117,.129),(.89,.117,.134),(.924,.116,.130),(.928,.116,.130)]
    vv=[]
    for z,w,dep in pocket:
        for k in range(13):
            t=-1+2*k/12;vv.append((w*t,-dep+.033*t*t,z))
    ff=[]
    for j in range(len(pocket)-1):
        for k in range(12):
            a=j*13+k;ff.append((a,a+1,a+14,a+13))
    p=_mesh('Ava_apron_large_patch_pocket',vv,ff,mats['olive'],subdiv=0)
    so=p.modifiers.new('Pocket material thickness','SOLIDIFY');so.thickness=.002;so.offset=0
    bpy.context.view_layer.objects.active=p;bpy.ops.object.modifier_apply(modifier=so.name)
    result.append(p)
    for s in (-1,1):
        # Leather straps rise over each shoulder and fasten at the back waist.
        pts=[(s*.079,-.104,1.215),(s*.085,-.089,1.24),(s*.096,-.069,1.28),(s*.101,-.046,1.313),(s*.105,-.019,1.329),(s*.109,.025,1.328),(s*.111,.068,1.305),(s*.108,.088,1.255),(s*.094,.104,1.18),(s*.085,.100,1.10),(s*.075,.092,1.043)]
        result.append(_ribbon('Ava_leather_shoulder_strap_'+str(s),pts,.016,mats['leather'],.0025,0))
        # Flat brass loops on bib: tiny, controlled accents, no branding.
        for xoff in (-.010,.010):
            result.append(_tube('Ava_bib_buckle_side',[(s*.079+xoff,-.105,1.214),(s*.079+xoff,-.105,1.237)],[.0016,.0016],mats['detail'],6,0))
        for z in (1.215,1.236):
            result.append(_tube('Ava_bib_buckle_bar',[(s*.079-.010,-.105,z),(s*.079+.010,-.105,z)],[.0016,.0016],mats['detail'],6,0))
        result.append(_ellipsoid('Ava_apron_pocket_rivet',(s*.109,-.105,.922),(.0023,.0015,.0023),mats['detail'],8,4))
    # Waist tie follows sweater waist, and an intentional back knot/two short tails.
    result.append(_loft('Ava_apron_waist_tie',[(1.032,0,.002,.149,.106),(1.034,0,.002,.150,.107),(1.054,0,.002,.150,.107),(1.056,0,.002,.149,.106)],mats['olive'],32,0,False))
    result.append(_ellipsoid('Ava_apron_back_knot',(0,.112,1.043),(.015,.006,.012),mats['olive'],12,6))
    for s in (-1,1):
        result.append(_bow_loop('Ava_apron_bow_loop',s,mats['olive']))
        result.append(_ribbon('Ava_apron_back_tie_tail',[(s*.006,.116,1.039),(s*.017,.117,1.015),(s*.026,.119,.968),(s*.023,.118,.928)],.019,mats['olive'],.002,0))
    return result


def build_outfit(mats):
    """Return static original mesh objects; caller owns parenting and export."""
    objects=[]
    objects.append(_loft('Ava_ivory_sweater_torso',[
        (.925,0,.002,.177,.113,.006),(.936,0,.002,.179,.114,.006),
        (.962,0,.001,.174,.106,.010),(1.005,0,0,.157,.099,.012),
        (1.054,0,.002,.146,.101,.012),(1.105,0,.006,.154,.109,.012),
        (1.165,0,.006,.174,.116,.010),(1.220,0,.010,.181,.105,.008),
        (1.267,0,.010,.190,.090,.007),(1.293,0,.009,.183,.081,.005),
        (1.319,0,.007,.129,.064,0),(1.337,0,.006,.063,.050,0),
        (1.340,0,.006,.058,.047,0)],mats['cream'],10,1,True))
    # Collar is a visible rolled knit ring. Top opening is hidden by the neck.
    objects.append(_loft('Ava_sweater_ribbed_neckline',[
        (1.328,0,.006,.068,.054),(1.334,0,.006,.068,.054),
        (1.343,0,.006,.060,.049),(1.346,0,.006,.056,.046)],mats['cream'],32,0,False))
    # Continuous jeans seat and soft tailored legs; apron covers the front waist.
    objects.append(_loft('Ava_dark_denim_hip',[
        (.824,0,.008,.100,.058),(.852,0,.009,.146,.091),
        (.878,0,.010,.171,.102),(.925,0,.008,.166,.094),
        (.965,0,.006,.150,.088),(.977,0,.006,.145,.085)],mats['denim'],32,0))
    # Shape the seat into two soft adult buttock masses instead of a central cap.
    # The centre seam recedes continuously into the crotch under the sweater.
    for v in objects[-1].data.vertices:
        if v.co.y>.009:
            v.co.y-=.023*math.exp(-(v.co.x/.040)**2)*math.exp(-((v.co.z-.855)/.060)**2)
    objects[-1].data.update()
    for s in (-1,1):
        objects.append(_loft('Ava_cuffed_jeans_leg_'+str(s),[
            (.135,s*.098,.001,.044,.048),(.141,s*.098,.001,.046,.048),
            (.169,s*.098,0,.044,.045,.018),(.208,s*.097,.003,.045,.047,.026),
            (.290,s*.096,.013,.054,.054,.018),(.385,s*.096,.015,.057,.059,.016),
            (.459,s*.093,-.006,.053,.061,.016),(.490,s*.092,-.009,.056,.062,.013),
            (.550,s*.089,-.003,.065,.067,.012),(.652,s*.086,.005,.073,.074,.012),
            (.748,s*.084,.009,.080,.083,.008),(.819,s*.083,.009,.083,.089,.006),
            (.879,s*.082,.010,.082,.090,0)],mats['denim'],20,0))
        objects.append(_loft('Ava_jeans_rolled_cuff_'+str(s),[
            (.131,s*.098,.001,.047,.052),(.135,s*.098,.001,.049,.053),
            (.157,s*.098,.001,.049,.052),(.163,s*.098,.001,.046,.049)],mats['denim'],20,0))
        # Continuous sleeve sweep with subtle compression folds near the cuff.
        sleeve_pts=[(s*.133,.011,1.254),(s*.178,.010,1.253),(s*.205,.010,1.235),(s*.229,.010,1.189),(s*.248,.005,1.133),(s*.258,.001,1.095),(s*.261,-.001,1.079),(s*.263,-.002,1.063)]
        sleeve_r=[(.068,.077),(.071,.075),(.069,.070),(.064,.066),(.061,.063),(.061,.064),(.057,.060),(.048,.052)]
        objects.append(_tube('Ava_soft_rolled_sweater_sleeve_'+str(s),sleeve_pts,sleeve_r,mats['cream'],10,1))
        objects.append(_tube('Ava_sleeve_rolled_cuff_'+str(s),[(s*.257,-.001,1.096),(s*.258,-.001,1.088),(s*.263,-.002,1.069),(s*.266,-.002,1.062)],[(.060,.064),(.062,.066),(.059,.063),(.051,.055)],mats['cream'],20,0))
        forearm=_tube('Ava_forearm_'+str(s),[(s*.260,-.001,1.096),(s*.269,-.003,1.054),(s*.280,-.008,1.008),(s*.292,-.011,.952),(s*.300,-.013,.910),(s*.302,-.013,.895)],[(.037,.041),(.038,.040),(.034,.036),(.027,.030),(.021,.024),(.020,.022)],mats['skin'],16,0)
        # Original palm, four tapered fingers and thumb; merged into one smooth hand.
        palm=_loft('Ava_hand_palm',[(.835,s*.306,-.013,.023,.013),(.844,s*.306,-.013,.027,.015),(.866,s*.305,-.013,.026,.016),(.888,s*.303,-.013,.020,.020),(.908,s*.302,-.013,.020,.022)],mats['skin'],16,1)
        hp=[palm,forearm]
        for j,(offset,length) in enumerate([(-.023,.044),(-.008,.054),(.008,.051),(.023,.040)]):
            x=s*(.306+offset)
            hp.append(_tube('Ava_hand_finger',[(x,-.014,.847),(x+s*.001,-.016,.827),(x+s*.002,-.019,.847-length),(x+s*.001,-.019,.843-length)],[.008,.0075,.0058,.0035],mats['skin'],8,1))
        hp.append(_tube('Ava_hand_thumb',[(s*.284,-.012,.878),(s*.276,-.016,.864),(s*.269,-.023,.846),(s*.268,-.028,.839)],[.010,.009,.007,.004],mats['skin'],8,1))
        objects.append(_union_hand(hp,'Ava_original_hand_'+str(s)))
        # Shoes have a real layered sole, toe box, instep and collar profile.
        cx=s*.098
        objects.append(_loft('Ava_sneaker_sole_'+str(s),[
            (0,cx,-.042,.048,.116),(.004,cx,-.043,.055,.124),
            (.013,cx,-.043,.057,.125),(.027,cx,-.043,.057,.124),
            (.032,cx,-.043,.054,.119)],mats['cream'],28,0))
        objects.append(_loft('Ava_sneaker_upper_'+str(s),[
            (.027,cx,-.042,.054,.119),(.038,cx,-.041,.055,.119),
            (.058,cx,-.034,.053,.110),(.077,cx,-.023,.046,.093),
            (.101,cx,-.006,.039,.070),(.120,cx,.008,.036,.050),
            (.132,cx,.012,.035,.043),(.136,cx,.012,.035,.042)],mats['shoe'],28,0,False))
        # Collar and tongue tuck under trouser cuff, preventing an ankle hole.
        objects.append(_loft('Ava_sneaker_soft_collar_'+str(s),[(.124,cx,.010,.038,.047),(.130,cx,.010,.039,.047),(.140,cx,.010,.035,.042),(.143,cx,.010,.033,.040)],mats['cream'],20,0,False))
        for j in range(4):
            y=-.080+j*.018;z=.080+j*.009
            pts=[(cx-.027,y,z),(cx-.014,y-.004,z+.006),(cx+.014,y-.004,z+.006),(cx+.027,y,z)]
            objects.append(_tube('Ava_sneaker_lace_'+str(s)+'_'+str(j),pts,[.0017]*4,mats['cream'],6,0))
        # Rear pockets omitted in this static candidate: the former planar patches
        # visibly failed to follow the curved seat in the actual side/back renders.
    # The original seat/leg surfaces are joined to remove every thigh seam.
    # Rolled cuffs and pockets remain distinct garment construction components.
    pants=[o for o in objects if o.name.startswith('Ava_dark_denim_hip') or o.name.startswith('Ava_cuffed_jeans_leg_')]
    for o in pants: objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in pants:o.select_set(True)
    bpy.context.view_layer.objects.active=pants[0]
    bpy.ops.object.join();denim=bpy.context.object;denim.name='Ava_original_tailored_jeans'
    rem=denim.modifiers.new('Original closed denim surface union','REMESH');rem.mode='VOXEL';rem.voxel_size=.005;rem.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    sm=denim.modifiers.new('Soft tailored transitions','SMOOTH');sm.factor=.6;sm.iterations=8
    bpy.ops.object.modifier_apply(modifier=sm.name)
    denim.data.calc_loop_triangles()
    de=denim.modifiers.new('Denim static review budget','DECIMATE');de.ratio=min(1.0,2050/max(1,len(denim.data.loop_triangles)))
    bpy.ops.object.modifier_apply(modifier=de.name)
    for p in denim.data.polygons:p.use_smooth=True
    objects.append(denim)
    # A single closed knit surface eliminates the cap points and underarm seams
    # found in the actual first front/back evidence. Cuffs remain separate rolls.
    knit=[o for o in objects if o.name.startswith('Ava_ivory_sweater_torso') or o.name.startswith('Ava_soft_rolled_sweater_sleeve_')]
    for o in knit:objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in knit:o.select_set(True)
    bpy.context.view_layer.objects.active=knit[0]
    bpy.ops.object.join();sweater=bpy.context.object;sweater.name='Ava_original_continuous_sweater'
    rem=sweater.modifiers.new('Original knit surface union','REMESH');rem.mode='VOXEL';rem.voxel_size=.004;rem.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=rem.name)
    sm=sweater.modifiers.new('Soft shoulder transitions','SMOOTH');sm.factor=.6;sm.iterations=3
    bpy.ops.object.modifier_apply(modifier=sm.name)
    sweater.data.calc_loop_triangles()
    de=sweater.modifiers.new('Static knit surface budget','DECIMATE');de.ratio=min(1.0,2200/max(1,len(sweater.data.loop_triangles)))
    bpy.ops.object.modifier_apply(modifier=de.name)
    for p in sweater.data.polygons:p.use_smooth=True
    objects.append(sweater)
    objects.extend(_apron(mats))
    # Clothing overlaps are purposeful static construction. All hands are unions.
    for ob in objects:
        ob['asset_id']=ASSET_ID
        ob['component']='outfit_body_original'
    return objects
