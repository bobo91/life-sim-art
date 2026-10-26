"""Seven bounded original street/ground modules for one walkable neighborhood."""
import math
from building_geometry import G,box,beam,finish

def ground(c):
    g=G();box(g,'soil_and_grass_tile',4,4,-.12,0,0,bevel=.001)
    return finish(c,g,('grass',))
def road(c):
    g=G();box(g,'quiet_residential_asphalt',6,6,-.10,.02,0,bevel=.001)
    return finish(c,g,('asphalt',))
def sidewalk(c):
    g=G();box(g,'broad_concrete_walk',2,2,0,.12,0,bevel=.006)
    return finish(c,g,('paving',))
def curb(c):
    g=G();box(g,'rounded_curb',2,.15,0,.15,0,bevel=.012)
    return finish(c,g,('curb',))
def corner(c):
    g=G();p=[(-.55,-1),(1,-1),(1,1),(-1,1),(-1,-.55)]
    p += [(-.55+.45*math.cos(math.radians(180+i*90/8)),-.55+.45*math.sin(math.radians(180+i*90/8))) for i in range(1,8)]
    g.loft('walk_outer_round_corner',[[(x,y,z) for x,y in p] for z in (0,.12)],0)
    loops=[]
    for i in range(9):
        a=math.radians(180+i*90/8)
        loops.append([(-.55+r*math.cos(a),-.55+r*math.sin(a),z) for r,z in ((.445,0),(.30,0),(.30,.15),(.445,.15))])
    g.loft('rounded_quarter_curb',loops,1)
    box(g,'front_curb_tail',1.545,.15,0,.15,1,center=(.2225,-.92),bevel=.006)
    box(g,'left_curb_tail',.15,1.545,0,.15,1,center=(-.92,.2225),bevel=.006)
    return finish(c,g,('paving','curb'))
def crossing(c):
    g=G()
    for i in range(7):box(g,f'crosswalk_bar_{i}',.32,5.6,0,.006,0,center=(-1.2+i*.4,0),bevel=.001)
    return finish(c,g,('marking',))
def ramp(c):
    g=G();profile=[(-1,-.01),(1,-.01),(1,.12),(.2,.12),(-1,.02)]
    g.loft('continuous_curb_cut_ramp',[[(x,y,z) for y,z in profile] for x in (-1,1)],0)
    return finish(c,g,('paving',))
def soil_bed(c):
    g=G();outline=[(1.5*math.cos(i*math.tau/24),math.sin(i*math.tau/24)) for i in range(24)]
    g.loft('soft_raised_garden_soil',[[(x*s,y*s,z) for x,y in outline] for s,z in ((.96,0),(1,.035),(.96,.06))],0)
    return finish(c,g,('soil',),smooth=True)
def street_sign(c):
    from neighborhood_cafe import add_label
    g=G();g.radial('tapered_metal_post',[(0,.055),(.08,.055),(.12,.035),(2.65,.035)],10,0)
    box(g,'streetname_plate',1.65,.065,2.36,2.66,1,center=(0,-.025),bevel=.015)
    add_label(g,c.get('streetName','WILLOW ST'),width=1.46,height=.19,bottom=2.415,y=-.07,material=2)
    o=finish(c,g,('metal','signPaint','marking'));o['temporaryStreetName']=c.get('streetName','WILLOW ST');return o

BUILDERS={'env_ground_400_001':ground,'env_road_600_001':road,'env_sidewalk_200_001':sidewalk,
 'env_curb_200_001':curb,'env_sidewalk_corner_001':corner,'env_crosswalk_001':crossing,'env_curb_ramp_001':ramp,'prop_street_name_001':street_sign,'env_soil_bed_001':soil_bed}
BOUNDS={'env_ground_400_001':([-2,-2,-.12],[2,2,0]),'env_road_600_001':([-3,-3,-.1],[3,3,.02]),
 'env_sidewalk_200_001':([-1,-1,0],[1,1,.12]),'env_curb_200_001':([-1,-.075,0],[1,.075,.15]),
 'env_sidewalk_corner_001':([-1,-1,0],[1,1,.15]),'env_crosswalk_001':([-1.36,-2.8,0],[1.36,2.8,.006]),
 'prop_street_name_001':([-.825,-.078517,0],[.825,.052308,2.66]),'env_curb_ramp_001':([-1,-1,-.01],[1,1,.12]),'env_soil_bed_001':([-1.5,-1,0],[1.5,1,.06])}
