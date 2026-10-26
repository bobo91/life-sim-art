"""Original Willow Creek cafe counter/chair; no imported geometry or scene edits.

The approved table's small vertex-loft helpers are reused, not its mesh. Each
builder returns one closed-component, triangulated mesh with an identity root.
"""
import json
import math

import bmesh
import bpy
from mathutils import Vector

from props_cafe_table import _Geometry, _rounded_rect, _plank, _clip_x, _linear


def _rounded_box(g, name, width, depth, bottom, top, radius, bevel, material,
                 center=(0.0, 0.0), top_material=None):
    """Four deliberately bevelled outline rings; independently closed part."""
    bevel = min(bevel, (top-bottom)*.3, min(width, depth)*.2)
    radius = min(radius, min(width, depth)*.45)
    inner = _rounded_rect(width-2*bevel, depth-2*bevel,
                          max(.0005, radius-bevel), 3)
    outer = _rounded_rect(width, depth, radius, 3)
    rings = [(bottom, inner), (bottom+bevel, outer),
             (top-bevel, outer), (top, inner)]
    loops = [[(x+center[0], y+center[1], z) for x, y in ring] for z, ring in rings]
    g.loft(name, loops, material, top_material)


def _beam(g, name, start, end, radius, material):
    """Octagonal closed cast-metal rail, caps overlap their structural joints."""
    a, b = Vector(start), Vector(end)
    direction = (b-a).normalized()
    across = direction.cross(Vector((0, 0, 1)))
    if across.length < .01:
        across = direction.cross(Vector((0, 1, 0)))
    across.normalize()
    other = direction.cross(across).normalized()
    loops = []
    for center, size in ((a, radius*.86), (a+direction*.004, radius),
                          (b-direction*.004, radius), (b, radius*.86)):
        loops.append([tuple(center+size*(across*math.cos(i*math.tau/8)
                                        +other*math.sin(i*math.tau/8))) for i in range(8)])
    g.loft(name, loops, material)


def _material(name, spec):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    color = _linear(spec['color'])
    shader.inputs['Base Color'].default_value = color
    shader.inputs['Roughness'].default_value = spec['roughness']
    shader.inputs['Metallic'].default_value = spec['metallic']
    mat.diffuse_color = color
    return mat


def _finish(g, config, function, notes):
    mesh = bpy.data.meshes.new(config['assetId']+'__mesh')
    mesh.from_pydata(g.vertices, [], g.faces)
    for role in ('wood', 'woodVariation', 'woodEdge', 'metal'):
        mesh.materials.append(_material(config['assetId']+'__'+role, config['palette'][role]))
    for polygon, index in zip(mesh.polygons, g.material_indices):
        polygon.material_index = index
        polygon.use_smooth = False
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(config['assetId'], mesh)
    bpy.context.collection.objects.link(obj)
    obj['assetId'] = config['assetId']
    obj['seed'] = config['seed']
    obj['generator'] = 'scripts/props_cafe_furniture.py:'+function
    obj['provenance'] = 'Original procedural vertices/materials; no external content'
    obj['constructionParts'] = json.dumps(g.parts)
    obj['constructionNotes'] = notes
    obj['sourceAxes'] = 'Blender Z-up / -Y-forward; GLB +Y-up / +Z-forward'
    return obj


def _check(config):
    if bpy.app.version[:3] != tuple(int(x) for x in config['blenderVersion'].split('.')):
        raise ValueError('Configured Blender version required')
    if not all(math.isfinite(x) and x > 0 for x in config['dimensionsMeters']):
        raise ValueError('Finite positive dimensions required')


def build_cafe_counter(config):
    """1.6 m service counter: timber top, framed sage front, open shelf rear."""
    _check(config)
    width, height, depth = config['dimensionsMeters']
    if (width, height, depth) != (1.6, 1.02, .65):
        raise ValueError('This authored counter is specified at1.6 x1.02 x.65m')
    g = _Geometry()
    # Recessed kick base is grounded; body and sides meet it as closed pieces.
    _rounded_box(g, 'recessed_kick_plinth', 1.39, .47, 0, .115, .022, .008, 2)
    _rounded_box(g, 'front_sage_carcass', 1.48, .065, .105, .973, .014, .006, 3,
                 center=(0, -.2325))
    for side in (-1, 1):
        # Return panels tuck behind the face, rather than sharing its front and
        # outside planes. FrontY -.255 vs face -.265; outerX .734 vs face .740.
        # The6mm side inset also removes the exposed coplanar side-face patch.
        # RearY remains+.265; overall bounds are still set by the unchanged top.
        _rounded_box(g, 'sage_side_'+str(side), .055, .52, .103, .973, .013, .006, 3,
                     center=(side*.7065, .005))
    # Shelf and division remain open from +Y; customer sees the framed -Y face.
    for z, name in ((.145, 'rear_bottom_shelf'), (.525, 'rear_middle_shelf')):
        _rounded_box(g, name, 1.38, .465, z-.025, z+.015, .012, .004, 2,
                     center=(0, .0225))
    _rounded_box(g, 'two_bay_center_divider', .035, .46, .13, .967, .006, .003, 2,
                 center=(0, .025))
    # Three broad raised panels are readable masses; tiny mouldings are omitted.
    for x in (-.465, 0, .465):
        _rounded_box(g, 'raised_front_panel_'+str(x), .410, .022, .235, .850,
                     .009, .005, 3, center=(x, -.275))
    for z, name in ((.165, 'lower_timber_rail'), (.925, 'upper_timber_rail')):
        _rounded_box(g, name, 1.46, .026, z-.022, z+.022, .008, .006, 0,
                     center=(0, -.272))
    # Warm solid top is made from three closed planks with the approved table bevel.
    outline = _rounded_rect(width, depth, .055, 5)
    cuts = [-width/2, -.27, .27, width/2]
    for i in range(3):
        left, right = cuts[i]+(.0007 if i else 0), cuts[i+1]-(.0007 if i<2 else 0)
        polygon = _clip_x(_clip_x(outline, left, True), right, False)
        joins = ([left] if i else [])+([right] if i<2 else [])
        _plank(g, 'rounded_timber_countertop_'+str(i+1), polygon, height-.055,
               height, .007, joins, (0, 1, 0)[i])
    return _finish(g, config, 'build_cafe_counter',
        'Rounded three-plank solid top; raised sage customer panels; open rear shelves. '
        'Individually closed components intentionally overlap at structural joints.')


def _bowed_back(g, name, width, bottom, top, material):
    # Swept octagonal cross-sections give a shallow embracing bow and eased edges.
    loops = []
    section = ((-.5, -.40), (-.35, -.5), (.35, -.5), (.5, -.40),
               (.5, .40), (.35, .5), (-.35, .5), (-.5, .40))
    for i in range(13):
        t = -1+2*i/12
        x = width*t/2
        y = .220+.010*t*t
        lower, upper = bottom+.008*t*t, top-.012*t*t
        center, thickness = (lower+upper)/2, upper-lower
        loops.append([(x, y+dy*.05, center+dz*thickness) for dy, dz in section])
    g.loft(name, loops, material, 2)


def build_cafe_chair(config):
    """Adult cafe chair; .46m seat, bowed timber back, tapered cast sage frame."""
    _check(config)
    if tuple(config['dimensionsMeters']) != (.46, .86, .51):
        raise ValueError('This authored chair is specified at.46 x.86 x.51m')
    g = _Geometry()
    # Closed timber cushion uses the table's real, restrained bevel treatment.
    outline = [(x, y-.035) for x, y in _rounded_rect(.46, .43, .060, 5)]
    _plank(g, 'rounded_solid_timber_seat', outline, .418, .460, .0065, [], 0)
    # Thin secondary back rail opens the silhouette above the seat.
    _bowed_back(g, 'bowed_timber_backrest', .430, .655, .860, 0)
    _bowed_back(g, 'lower_bowed_back_rail', .405, .558, .616, 1)
    for side in (-1, 1):
        front = [(0, .0205, side*.205, -.2345), (.025, .0215, side*.204, -.232),
                 (.435, .017, side*.182, -.174)]
        # Bend behind the visible timber face before the lower rail begins.
        # The former shallow rise crossed that face and made pointed green slivers.
        # Rear extent remains.255m: top center.238 + radius.017.
        rear = [(0, .0195, side*.203, .223), (.035, .021, side*.201, .222),
                (.430, .018, side*.181, .171), (.540, .016, side*.186, .235),
                (.818, .017, side*.191, .238)]
        for title, levels in (('front_leg_', front), ('rear_leg_and_back_post_', rear)):
            loops = [[(x+r*math.cos(i*math.tau/8), y+r*math.sin(i*math.tau/8), z)
                      for i in range(8)] for z, r, x, y in levels]
            g.loft(title+str(side), loops, 3)
        _beam(g, 'side_seat_support_'+str(side), (side*.181, -.185, .407),
              (side*.181, .180, .407), .017, 3)
        _beam(g, 'low_side_stretcher_'+str(side), (side*.194, -.207, .200),
              (side*.194, .200, .200), .012, 3)
    _beam(g, 'front_seat_apron', (-.190, -.177, .405), (.190, -.177, .405), .019, 3)
    _beam(g, 'rear_seat_apron', (-.190, .174, .405), (.190, .174, .405), .017, 3)
    _beam(g, 'rear_low_stretcher', (-.196, .197, .200), (.196, .197, .200), .012, 3)
    return _finish(g, config, 'build_cafe_chair',
        'Adult46cm seat; original swept bowed timber back and tapered sage frame. '
        'Closed construction parts overlap at joins; no seating/animation anchor or gameplay collider.')
