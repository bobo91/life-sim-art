"""Four original, bounded foliage assets for the first Willow Creek block.

Broad softly lobed crowns, rather than individual leaves, keep the silhouettes
readable from the game camera. All geometry starts as deterministic vertices.
No imported mesh, texture, manual sculpting, particle system or external API.
"""
import math

from building_geometry import G, finish


def _crown(g, name, centre, radii, material, sides=16, lean=0):
    """Closed ellipsoidal crown with restrained lobing and small capped tips."""
    cx, cy, cz = centre
    rx, ry, rz = radii
    loops = []
    for h in (-.98, -.85, -.61, -.32, 0, .32, .61, .85, .98):
        radius = math.sqrt(1-h*h)
        loop = []
        for i in range(sides):
            angle = i*math.tau/sides
            lobe = 1+.025*math.sin(3*angle)+.015*math.cos(5*angle)
            loop.append((cx+lean*h+rx*radius*lobe*math.cos(angle),
                         cy+ry*radius*lobe*math.sin(angle), cz+rz*h))
        loops.append(loop)
    g.loft(name, loops, material)


def _trunk(g, name, levels, material=0, sides=12):
    """Closed tapered curved trunk/fork; horizontal rings follow rising paths."""
    g.loft(name, [[(x+r*math.cos(i*math.tau/sides),
                   y+r*math.sin(i*math.tau/sides), z)
                  for i in range(sides)] for x, y, z, r in levels], material)


def _anchor(g):
    """Greenery pivots use bottom-centre bounds; architecture anchors stay intact."""
    lo = [min(v[i] for v in g.vertices) for i in range(3)]
    hi = [max(v[i] for v in g.vertices) for i in range(3)]
    offset = ((lo[0]+hi[0])/2, (lo[1]+hi[1])/2, lo[2])
    g.vertices = [tuple(v[i]-offset[i] for i in range(3)) for v in g.vertices]
    return g


def deciduous_geometry():
    g = G()
    _trunk(g, 'flared_gently_curved_trunk',
           [(0, 0, 0, .27), (0, 0, .12, .25), (.02, .01, .45, .18),
            (.04, .03, 1.30, .135), (.10, .02, 2.20, .105),
            (.13, .03, 3.05, .065), (.10, .02, 3.65, .025)])
    for name, levels in (
        ('left_fork', [(.07, .01, 1.65, .10), (-.28, -.02, 2.25, .09),
                       (-.78, -.03, 2.90, .055), (-1.05, -.05, 3.42, .02)]),
        ('right_fork', [(.08, .01, 2.05, .085), (.53, .12, 2.62, .07),
                        (.91, .18, 3.14, .04), (1.05, .20, 3.56, .018)]),
        ('rear_fork', [(.10, .03, 2.32, .075), (.05, .54, 2.78, .06),
                       (-.04, .94, 3.27, .02)]),
        ('front_fork', [(.01, .01, 2.24, .065), (.12, -.51, 2.72, .052),
                        (.22, -.96, 3.14, .018)])):
        _trunk(g, name, levels, sides=10)
    # Overlapping large lobes form a single broad, uneven maple-like envelope.
    for name, centre, radii, material, lean in (
        ('central_high_crown', (.04, .10, 3.91), (1.35, 1.18, 1.13), 1, .07),
        ('left_crown', (-1.04, .03, 3.40), (1.01, 1.02, 1.02), 1, -.03),
        ('right_crown', (1.00, .18, 3.58), (1.01, 1.00, 1.05), 2, .04),
        ('front_low_crown', (.13, -.92, 3.40), (1.14, .91, .93), 1, .04),
        ('rear_crown', (-.10, .93, 3.60), (1.14, .94, .98), 2, -.03),
        ('left_upper_crown', (-.64, .34, 4.12), (.90, .87, .96), 2, -.03)):
        _crown(g, name, centre, radii, material, lean=lean)
    return _anchor(g)


def small_tree_geometry():
    g = G()
    _trunk(g, 'small_tree_flared_stem',
           [(0, 0, 0, .18), (0, 0, .10, .17), (-.02, 0, .50, .115),
            (-.06, .02, 1.22, .085), (-.02, .03, 2.02, .045),
            (.02, .02, 2.60, .018)], sides=10)
    _trunk(g, 'small_tree_left_fork',
           [(-.04, .02, 1.14, .07), (-.33, .03, 1.66, .05),
            (-.51, .08, 2.12, .018)], sides=8)
    _trunk(g, 'small_tree_right_fork',
           [(-.03, .03, 1.52, .06), (.29, -.08, 1.94, .045),
            (.44, -.14, 2.28, .015)], sides=8)
    # Narrower upright/pear silhouette differs from the large spreading crown.
    for name, centre, radii, material, lean in (
        ('upright_top_crown', (.02, .03, 2.58), (.67, .64, .88), 2, -.02),
        ('full_lower_crown', (-.04, .02, 1.98), (.91, .77, .81), 1, .03),
        ('left_round_shoulder', (-.48, .11, 2.15), (.57, .61, .70), 1, -.02),
        ('front_right_shoulder', (.41, -.27, 2.12), (.57, .54, .69), 2, .02)):
        _crown(g, name, centre, radii, material, lean=lean)
    return _anchor(g)


def shrub_geometry():
    g = G()
    for i, (x, y) in enumerate(((-.22, -.08), (.21, .05), (0, .19))):
        _trunk(g, 'low_shrub_stem_'+str(i),
               [(x, y, 0, .047), (x*.9, y*.9, .32, .026),
                (x*1.3, y*1.3, .55, .01)], sides=8)
    for name, centre, radii, material in (
        ('broad_central_mound', (.02, .02, .49), (.61, .50, .44), 1),
        ('low_left_shoulder', (-.39, -.02, .35), (.43, .41, .33), 1),
        ('right_shoulder', (.36, .10, .42), (.44, .39, .36), 2),
        ('front_shoulder', (.02, -.30, .31), (.47, .37, .29), 2)):
        _crown(g, name, centre, radii, material, sides=12)
    return _anchor(g)


def _flower(g, name, centre, radius=.082):
    """One broad five-petal closed rosette; no tiny individual leaf geometry."""
    x, y, z = centre
    outline = [(radius*(1 if i%2==0 else .60)*math.cos(i*math.tau/10),
                radius*(1 if i%2==0 else .60)*math.sin(i*math.tau/10))
               for i in range(10)]
    g.loft(name, [[(x+u*scale, y+v*scale, z+height) for u, v in outline]
                 for height, scale in ((-.012, .83), (0, 1), (.020, .86))], 3)


def flowering_shrub_geometry():
    g = G()
    for i, x in enumerate((-.35, 0, .34)):
        _trunk(g, 'spreading_shrub_stem_'+str(i),
               [(x, .01, 0, .035), (x*.9, .01, .25, .022),
                (x*1.1, .03, .43, .009)], sides=8)
    for name, centre, radii, material in (
        ('low_wide_mound', (.02, 0, .30), (.70, .47, .29), 1),
        ('left_mound', (-.48, -.02, .26), (.43, .37, .25), 1),
        ('right_mound', (.46, .04, .30), (.43, .37, .28), 2),
        ('rear_high_mound', (-.13, .23, .37), (.46, .36, .29), 2)):
        _crown(g, name, centre, radii, material, sides=12)
    for i, position in enumerate(((-.62, -.10, .486), (-.36, -.23, .512),
                                  (-.10, -.13, .576), (.20, -.22, .535),
                                  (.52, -.10, .553), (.15, .20, .596),
                                  (-.20, .25, .650))):
        _flower(g, 'broad_flower_rosette_'+str(i), position)
    return _anchor(g)


GEOMETRY = {
    'env_deciduous_tree_001': deciduous_geometry,
    'env_small_tree_001': small_tree_geometry,
    'env_shrub_001': shrub_geometry,
    'env_shrub_002': flowering_shrub_geometry,
}


def _build(config):
    asset = config['assetId']
    roles = ('trunk', 'foliage', 'foliageLight', 'flower') if asset=='env_shrub_002' else ('trunk', 'foliage', 'foliageLight')
    geometry = GEOMETRY[asset]()
    obj = finish(config, geometry, roles, smooth=True)
    obj['pivotPolicy'] = 'bottom-centre'
    obj['collisionPolicy'] = 'Tree trunk capsule proposal only; foliage and shrubs decorative'
    obj['variationPolicy'] = 'Reuse with positive uniform scale, Z rotation and material overrides; no mesh variants'
    if asset in ('env_deciduous_tree_001', 'env_small_tree_001'):
        sides = 12 if asset=='env_deciduous_tree_001' else 10
        obj['trunkBaseSourceXY'] = [sum(p[i] for p in geometry.vertices[:sides])/sides for i in (0, 1)]
    return obj


BUILDERS = {asset: _build for asset in GEOMETRY}

# Frozen independently from generated source-space positions by a pure-Python
# geometry audit. Values are not inferred from an exported GLB during validation.
BOUNDS = {
    'env_deciduous_tree_001': {'min': [-2.03, -1.849625, 0], 'max': [2.03, 1.849625, 5.0608]},
    'env_small_tree_001': {'min': [-1.015, -.797125, 0], 'max': [1.015, .797125, 3.4424]},
    'env_shrub_001': {'min': [-.810075, -.593375, 0], 'max': [.810075, .593375, .9212]},
    'env_shrub_002': {'min': [-.9, -.531375, 0], 'max': [.9, .531375, .67]},
}
