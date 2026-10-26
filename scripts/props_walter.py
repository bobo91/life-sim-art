"""Ten original porch/garden props; no external meshes, fonts or textures."""
import math
import random

from mathutils import Vector
from walter_common import G, box, beam, finish, rounded_rect


def tube(g,name,path,radius,material,sides=8):
    path=[Vector(p) for p in path];loops=[];previous_u=None
    for i,p in enumerate(path):
        tangent=path[min(i+1,len(path)-1)]-path[max(i-1,0)]
        tangent.normalize()
        u=(previous_u-tangent*previous_u.dot(tangent)) if previous_u is not None else tangent.cross(Vector((0,0,1)))
        if u.length<.001:u=tangent.cross(Vector((1,0,0)))
        u.normalize();previous_u=u;v=tangent.cross(u).normalized()
        r=radius[i] if isinstance(radius,list) else radius
        loops.append([tuple(p+r*(u*math.cos(a*math.tau/sides)+v*math.sin(a*math.tau/sides))) for a in range(sides)])
    g.loft(name,loops,material)


def sphere(g,name,center,radii,material,sides=10,rings=6):
    loops=[]
    for j in range(rings+1):
        theta=.07+(math.pi-.14)*j/rings
        loops.append([(center[0]+radii[0]*math.sin(theta)*math.cos(i*math.tau/sides),
                       center[1]+radii[1]*math.sin(theta)*math.sin(i*math.tau/sides),
                       center[2]-radii[2]*math.cos(theta)) for i in range(sides)])
    g.loft(name,loops,material)


def leaf(g,name,base,tip,width,material,bend=.035):
    base,tip=Vector(base),Vector(tip);d=(tip-base).normalized();u=d.cross(Vector((0,0,1)))
    if u.length<.001:u=Vector((1,0,0))
    u.normalize();v=u.cross(d).normalized();loops=[]
    for t in (0,.2,.5,.8,1):
        center=base+(tip-base)*t+Vector((0,0,bend*math.sin(math.pi*t)))
        w=.0007+width*.5*math.sin(math.pi*t);h=.0005+.004*math.sin(math.pi*t)
        loops.append([tuple(center+u*w*math.cos(i*math.tau/8)+v*h*math.sin(i*math.tau/8)) for i in range(8)])
    g.loft(name,loops,material)


def build_porch_bench(c):
    g=G()
    # Quiet variation across broad slats, rounded knees and a gently reclined back.
    for i,y in enumerate((-.213,-.071,.071,.213)):
        box(g,'seat_slat_'+str(i),1.35,.132,.425,.466,(0,1,0,0)[i],center=(0,y),bevel=.010)
    for side in (-1,1):
        for y in (-.22,.22):beam(g,'aged_leg',(side*.56,y,0),(side*.535,y*.88,.438),.065,2)
        beam(g,'seat_bearer',(side*.54,-.255,.403),(side*.54,.24,.403),.045,2)
        beam(g,'back_stile',(side*.54,.20,.42),(side*.54,.268,.895),.048,2)
    for j,z in enumerate((.575,.704,.833)):
        loops=[]
        for x in (-.665,-.35,0,.35,.665):
            y=.225+.035*(x/.665)**2+(z-.575)*.12
            loops.append([(x,y-.018,z-.049),(x,y+.018,z-.049),(x,y+.018,z+.049),(x,y-.018,z+.049)])
        g.loft('bowed_back_slat_'+str(j),loops,(0,1,0)[j])
    beam(g,'lower_crossbar',(-.56,.19,.18),(.56,.19,.18),.039,2)
    return finish(c,g,('timber','faded','frame'))


def build_porch_rocking_chair(c):
    g=G()
    # Broad closed curved runners; contact is at the centre of their arc.
    for side in (-1,1):
        loops=[]
        for i in range(17):
            y=-.435+i*.87/16;z=.025+.105*(y/.435)**2
            x=side*.285
            loops.append([(x-.033,y,z-.023),(x+.033,y,z-.023),(x+.033,y,z+.023),(x-.033,y,z+.023)])
        g.loft('curved_runner_'+str(side),loops,2)
        for y in (-.235,.205):beam(g,'splayed_leg',(side*.285,y,.058),(side*.245,y*.84,.442),.045,2)
        beam(g,'rear_stile',(side*.246,.19,.43),(side*.247,.317,1.055),.039,2)
        beam(g,'arm_front',(side*.245,-.195,.432),(side*.29,-.165,.657),.032,2)
        box(g,'soft_armrest',.078,.535,.655,.695,0,center=(side*.29,.048),bevel=.012)
    for i in range(5):
        x=-.208+i*.104
        box(g,'seat_board_'+str(i),.097,.49,.425,.462,1 if i==1 else 0,center=(x,-.014),bevel=.009)
    beam(g,'seat_front_support',(-.26,-.219,.408),(.26,-.219,.408),.039,2)
    beam(g,'seat_rear_support',(-.26,.204,.408),(.26,.204,.408),.039,2)
    # Slats stop in the cap rails; supporting stiles remain behind their visible faces.
    for i in range(7):
        x=-.213+i*.071
        beam(g,'back_slat',(x,.218,.49),(x,.307,1.013),.036,0 if i%3 else 1)
    box(g,'top_cap',.582,.070,1.01,1.085,0,center=(0,.318),bevel=.013)
    box(g,'lower_back_rail',.555,.055,.475,.52,2,center=(0,.224),bevel=.008)
    beam(g,'lower_front_brace',(-.275,-.22,.23),(.275,-.22,.23),.026,2)
    return finish(c,g,('timber','faded','frame'))


def pot_shell(g,name,profile,sides,material):
    g.loft(name,[[(rx*math.cos(i*math.tau/sides),ry*math.sin(i*math.tau/sides),z)
                 for i in range(sides)] for z,rx,ry in profile],material)


def build_flower_pot_large(c):
    g=G();rng=random.Random(c['seed'])
    pot_shell(g,'terracotta_body',[(0,.155,.155),(.025,.17,.17),(.295,.213,.213),(.315,.23,.23),
        (.35,.23,.23),(.355,.214,.214),(.343,.194,.194),(.060,.145,.145),(.035,.145,.145)],24,0)
    g.radial('garden_soil',[(.304,.188),(.314,.191)],24,1)
    for i in range(12):
        a=i*math.tau/12+rng.uniform(-.09,.09);r=.23+rng.uniform(-.025,.015)
        tip=(math.cos(a)*r,math.sin(a)*r,.43+rng.uniform(-.03,.10))
        leaf(g,'broad_leaf_'+str(i),(math.cos(a)*.04,math.sin(a)*.04,.315),tip,.095,2,.06)
    for i,(x,y,z) in enumerate(((-.09,.04,.64),(.07,.06,.69),(.04,-.09,.59))):
        beam(g,'flower_stem',(x*.25,y*.25,.315),(x,y,z),.012,2)
        for j in range(5):
            a=j*math.tau/5
            sphere(g,'muted_petals',(x+.031*math.cos(a),y+.031*math.sin(a),z),(.029,.029,.014),3,8,3)
        sphere(g,'flower_centre',(x,y,z+.011),(.018,.018,.010),1,8,3)
    return finish(c,g,('pot','soil','leaf','flower'),True)


def build_flower_pot_small(c):
    g=G();rng=random.Random(c['seed'])
    pot_shell(g,'rounded_ceramic',[(0,.085,.085),(.012,.103,.103),(.05,.132,.132),(.13,.139,.139),
        (.17,.125,.125),(.178,.116,.116),(.168,.103,.103),(.034,.080,.080),(.024,.080,.080)],24,0)
    g.radial('soil',[(.146,.101),(.152,.103)],20,1)
    for ring,count,radius,z in ((0,9,.171,.214),(1,7,.123,.29),(2,5,.064,.35)):
        for i in range(count):
            a=i*math.tau/count+ring*.41+rng.uniform(-.04,.04)
            leaf(g,'succulent_rosette',(0,0,.15+ring*.022),(radius*math.cos(a),radius*math.sin(a),z),.073 if ring<2 else .047,2,.026)
    return finish(c,g,('pot','soil','leaf'),True)


def build_old_watering_can(c):
    g=G()
    pot_shell(g,'oval_can',[(0,.106,.076),(.02,.116,.082),(.22,.115,.080),(.243,.103,.074),
        (.252,.086,.063),(.252,.070,.047),(.229,.070,.047),(.035,.089,.057),(.025,.089,.057)],28,0)
    pot_shell(g,'rolled_rim',[(.247,.084,.061),(.256,.088,.065),(.265,.084,.061),(.261,.077,.054),(.248,.077,.054)],28,1)
    # A restrained faded base strip is geometry at the rolled seam, not random scratches.
    pot_shell(g,'base_seam',[(.009,.114,.081),(.018,.120,.086),(.028,.119,.085),(.034,.115,.081)],28,1)
    spout=[(.083,-.013,.08),(.14,-.02,.105),(.232,-.032,.247),(.274,-.037,.287)]
    tube(g,'rising_spout',spout,[.027,.025,.019,.020],0,12)
    direction=(Vector(spout[-1])-Vector(spout[-2])).normalized()
    tube(g,'rose_head',[Vector(spout[-1])-direction*.008,Vector(spout[-1])+direction*.018],[.037,.042],1,16)
    tube(g,'rose_dark_face',[Vector(spout[-1])+direction*.0182,Vector(spout[-1])+direction*.020],[.035,.035],3,16)
    path=[(-.083*math.cos(i*math.pi/14),0,.235+.137*math.sin(i*math.pi/14)) for i in range(15)]
    tube(g,'carrying_handle',path,.012,2,8)
    path=[(-.105-.078*math.sin(i*math.pi/12),0,.08+.15*i/12) for i in range(13)]
    tube(g,'rear_grip',path,.012,2,8)
    return finish(c,g,('metal','rim','handle','inside'),True)


def build_welcome_mat(c):
    g=G();box(g,'rounded_coir',.76,.45,0,.018,0,bevel=.004)
    # Broad subdued border and a simple original lozenge; no font or fibre noise.
    for x in (-.342,.342):box(g,'side_border',.018,.375,.0183,.0205,1,center=(x,0),bevel=.002)
    for y in (-.18,.18):box(g,'end_border',.665,.018,.0183,.0205,1,center=(0,y),bevel=.002)
    loops=[[(0,-.072,z),(.073,0,z),(0,.072,z),(-.073,0,z)] for z in (.0182,.0204)]
    g.loft('worn_woven_lozenge',loops,2)
    return finish(c,g,('coir','border','faded'))


def build_porch_lantern(c):
    g=G()
    box(g,'wall_backplate',.092,.040,.085,.318,0,center=(0,.129),bevel=.010)
    beam(g,'upper_wall_arm',(0,.129,.29),(0,-.038,.29),.028,0)
    # Closed opaque warm panels avoid a fragile transparent shader contract.
    g.loft('warm_panel',[[(x*r,y*r,z) for x,y in ((-1,-1),(1,-1),(1,1),(-1,1))]
                        for z,r in ((.061,.070),(.268,.085))],2)
    for x in (-1,1):
        for y in (-1,1):beam(g,'lantern_upright',(x*.073,y*.073,.054),(x*.088,y*.088,.275),.014,0)
    box(g,'bottom_rim',.19,.19,.030,.064,0,bevel=.007)
    g.loft('hood', [[(x*r,y*r,z) for x,y in ((-1,-1),(1,-1),(1,1),(-1,1))]
                   for z,r in ((.270,.113),(.287,.115),(.347,.040),(.363,.026))],0)
    g.radial('finial',[(.36,.017),(.39,.021),(.407,.010)],10,1)
    return finish(c,g,('metal','aged_edge','glow'))


def build_wooden_fence(c):
    g=G()
    for i in range(9):
        x=-.61+i*.1525;w=.105
        outline=[(-w/2,0),(w/2,0),(w/2,.735),(.032,.790),(0,.812),(-.032,.790),(-w/2,.735)]
        verts=[(x+xx,y,z) for y in (-.018,.018) for xx,z in outline];n=len(outline)
        faces=[tuple(reversed(range(n))),tuple(n+j for j in range(n))]
        faces += [(j,(j+1)%n,n+(j+1)%n,n+j) for j in range(n)]
        g.part('soft_picket_'+str(i),verts,faces,0 if i%4 else 1)
    for z in (.21,.61):box(g,'rear_rail',1.38,.040,z,z+.065,2,center=(0,.034),bevel=.005)
    return finish(c,g,('timber','faded','frame'))


def build_fence_post(c):
    g=G();box(g,'post_shaft',.12,.12,0,.965,0,bevel=.006)
    box(g,'cap_band',.148,.148,.926,.962,1,bevel=.008)
    outline=rounded_rect(.148,.148,.010,3)
    g.loft('weathered_pyramid_cap',[[(x,y,z) for x,y in pts] for z,pts in ((.961,outline),(1.025,[(x*.13,y*.13) for x,y in outline]))],0)
    return finish(c,g,('timber','faded'))


def build_wooden_crate(c):
    g=G()
    for i in range(4):box(g,'bottom_board',.113,.34,0,.027,0 if i%2 else 1,center=(-.18+i*.12,0),bevel=.005)
    for x in (-.213,.213):
        for y in (-.143,.143):box(g,'corner_batten',.036,.036,.025,.307,2,center=(x,y),bevel=.004)
    for i,z in enumerate((.057,.150,.243)):
        for y in (-.158,.158):box(g,'long_wall_board',.48,.024,z,z+.077,0 if i%2 else 1,center=(0,y),bevel=.004)
        for x in (-.228,.228):box(g,'end_wall_board',.024,.29,z,z+.077,0 if i%2 else 1,center=(x,0),bevel=.004)
    return finish(c,g,('timber','faded','frame'))


BUILDERS={
    'prop_porch_bench_001':build_porch_bench,'prop_flower_pot_001':build_flower_pot_large,
    'prop_flower_pot_002':build_flower_pot_small,'prop_welcome_mat_001':build_welcome_mat,
    'prop_porch_lantern_001':build_porch_lantern,'prop_wooden_fence_001':build_wooden_fence,
    'prop_fence_post_001':build_fence_post,'prop_old_watering_can_001':build_old_watering_can,
    'prop_wooden_crate_001':build_wooden_crate,'prop_porch_rocking_chair_001':build_porch_rocking_chair}
