"""Nine original fixed-grid architectural modules. Actual openings, no booleans."""
from building_geometry import G, box, beam, finish


def wall(config, opening=None):
    g=G()
    # Separate closed jamb/header/sill solids make genuine interior-through holes.
    regions=[(-1,1,0,2.8)] if not opening else [(-1,-.55,0,2.8),(.55,1,0,2.8),(-.55,.55,opening[1],2.8)]
    if opening and opening[0]>0:regions.append((-.55,.55,0,opening[0]))
    for i,(a,b,c,d) in enumerate(regions):
        box(g,f'wall_structural_{i}',b-a,.18,c,d,1,center=((a+b)/2,0),bevel=.001)
    # Coarse 200mm siding courses, clipped to the same opening.
    for i in range(14):
        lo,hi=i*.2,(i+1)*.2
        spans=[(-1,1)]
        if opening and lo<opening[1] and hi>opening[0]:spans=[(-1,-.55),(.55,1)]
        pieces=[(a,b,lo,hi) for a,b in spans]
        if opening and lo<opening[0]<hi:pieces.append((-.55,.55,lo,opening[0]))
        if opening and lo<opening[1]<hi:pieces.append((-.55,.55,opening[1],hi))
        for j,(a,b,lo_,hi_) in enumerate(pieces):
            # Closed tapered clapboards overlap structure, not neighboring panels.
            g.loft(f'clapboard_{i}_{j}',[[(a,-.116,lo_),(b,-.116,lo_),(b,-.082,lo_),(a,-.082,lo_)],
                [(a,-.099,hi_),(b,-.099,hi_),(b,-.082,hi_),(a,-.082,hi_)]],0)
    obj=finish(config,g,('siding','interior'))
    if opening:obj['openingSourceXZ']=[-.55,.55,*opening]
    return obj


def build_corner(config):
    g=G();p=[(-.14,-.145),(.145,-.145),(.145,.14),(.105,.14),(.105,-.105),(-.14,-.105)]
    g.loft('closed_L_corner_board',[[(x,y,z) for x,y in p] for z in (0,2.8)],0)
    return finish(config,g,('trim',))


def build_floor(config):
    g=G();box(g,'solid_floor_tile',2,2,0,.18,0,bevel=.001)
    return finish(config,g,('wood',))


def build_foundation(config):
    g=G();box(g,'closed_foundation_strip',2,.28,0,.37,0,bevel=.008)
    # A single broad cap remains legible without stone microdetail.
    box(g,'plinth_cap',2,.32,.36,.42,0,bevel=.004)
    return finish(config,g,('stone',))


def build_porch(config):
    g=G();box(g,'porch_closed_base',2,2,0,.52,1,bevel=.005)
    for i in range(8):
        box(g,f'deck_board_{i}',2,.247,.52,.60,0,center=(0,-.875+i*.25),bevel=.006)
    box(g,'front_apron',2,.06,.36,.53,2,center=(0,-.985),bevel=.006)
    return finish(config,g,('wood','stone','trim'))


def build_steps(config):
    g=G()
    for i in range(3):
        # Back at Y0; front at -0.90. No decorative slab across a doorway.
        box(g,f'closed_step_{i}',1.40,.30,0,(i+1)*.20-.025,0,center=(0,-.75+i*.3),bevel=.012)
        box(g,f'wood_tread_{i}',1.43,.295,(i+1)*.2-.025,(i+1)*.2,1,center=(0,-.75+i*.3),bevel=.004)
    return finish(config,g,('stone','wood'))


def build_post(config):
    g=G();box(g,'square_timber_column',.13,.13,0,1.96,0,bevel=.009)
    box(g,'post_foot',.19,.19,0,.16,0,bevel=.007)
    box(g,'post_cap',.19,.19,1.92,2.00,0,bevel=.007)
    # Simple paired knee braces under the canopy, no invisible joinery.
    beam(g,'left_knee_brace',(0,0,1.57),(-.30,0,1.96),.07,0)
    beam(g,'right_knee_brace',(0,0,1.57),(.30,0,1.96),.07,0)
    return finish(config,g,('trim',))


BUILDERS={
 'bld_wall_solid_200_001':lambda c:wall(c),
 'bld_wall_window_200_001':lambda c:wall(c,(.85,2.10)),
 'bld_wall_door_200_001':lambda c:wall(c,(0,2.20)),
 'bld_corner_trim_001':build_corner,'bld_floor_200_001':build_floor,
 'bld_foundation_200_001':build_foundation,'bld_porch_200_001':build_porch,
 'bld_porch_steps_001':build_steps,'bld_porch_post_001':build_post}
