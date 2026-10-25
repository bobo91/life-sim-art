"""Original closed-mesh cafe tin and cup/saucer; no external geometry or textures.

Called by the bounded cafe-pack builder in an isolated Blender process. Dimensions
are authored in metres, Blender Z-up/-Y-front; root pivots are bottom-centred.
"""
import json
import math

import bmesh
import bpy

from props_cafe_table import _Geometry, _linear, _rounded_rect


def _finish(config, geometry, roles, smooth_parts=()):
    if bpy.app.version[:3] != tuple(map(int, config['blenderVersion'].split('.'))):
        raise ValueError('Configured Blender version is required')
    prefix = config['assetId']
    mesh = bpy.data.meshes.new(prefix + '__mesh')
    mesh.from_pydata(geometry.vertices, [], geometry.faces)
    for role in roles:
        spec = config['palette'][role]
        material = bpy.data.materials.new(prefix + '__' + role)
        material.use_nodes = True
        shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        shader.inputs['Base Color'].default_value = _linear(spec['color'])
        shader.inputs['Roughness'].default_value = spec['roughness']
        shader.inputs['Metallic'].default_value = spec['metallic']
        material.diffuse_color = _linear(spec['color'])
        mesh.materials.append(material)
    for polygon, material in zip(mesh.polygons, geometry.material_indices):
        polygon.material_index = material
        polygon.use_smooth = any(begin <= polygon.index < end for begin, end in smooth_parts)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    asset = bpy.data.objects.new(prefix, mesh)
    bpy.context.collection.objects.link(asset)
    asset['assetId'] = prefix
    asset['generator'] = 'scripts/props_cafe_smallwares.py:build_' + ('tin' if prefix == 'prop_tin_001' else 'cafe_cup')
    asset['seed'] = config['seed']
    asset['provenance'] = 'Original procedural vertices/materials; no external content'
    asset['constructionParts'] = json.dumps(geometry.parts)
    asset['constructionNotes'] = 'Closed construction shells intentionally overlap at attachments; no exhaustive solid-intersection proof.'
    asset['sourceAxes'] = 'Blender Z-up / -Y-forward; export +Y-up/+Z-forward'
    return asset


def _rect_loft(g, name, levels, radius, material, segments=4):
    g.loft(name, [[(x, y, z) for x, y in _rounded_rect(width, depth, radius, segments)]
                 for z, width, depth in levels], material)


def _front_emblem(g, name, outline, back_y, front_y, material):
    """Closed thin geometric enamel appliqué; projected silhouette is original."""
    g.loft(name, [[(x, y, z) for x, z in outline] for y in (back_y, front_y)], material)


def build_tin(config):
    """Closed vintage cafe tea tin with lid rim and a broad original leaf seal."""
    g = _Geometry()
    _rect_loft(g, 'rolled_bottom_rim', [(0, .130, .100), (.002, .136, .106),
               (.007, .136, .106), (.009, .132, .102)], .012, 2)
    _rect_loft(g, 'cream_tin_shell', [(.005, .128, .098), (.009, .132, .102),
               (.174, .132, .102), (.178, .128, .098)], .012, 0)
    # Each band is a closed shell slightly proud of the tin, never a coplanar decal.
    _rect_loft(g, 'broad_terracotta_band', [(.073, .1326, .1026), (.076, .1328, .1028),
               (.120, .1328, .1028), (.123, .1326, .1026)], .012, 1)
    _rect_loft(g, 'brass_lid_rolled_rim', [(.175, .134, .104), (.177, .140, .110),
               (.181, .140, .110), (.183, .138, .108)], .013, 2)
    _rect_loft(g, 'sage_lid', [(.180, .136, .106), (.183, .140, .110),
               (.187, .140, .110), (.190, .136, .106)], .013, 3)
    seal = [(.019 * math.cos(i * math.tau / 24), .098 + .022 * math.sin(i * math.tau / 24))
            for i in range(24)]
    _front_emblem(g, 'cream_oval_seal', seal, -.0518, -.0530, 0)
    # Two broad leaves stay recognizable in the close clue view without typography.
    left = [(-.001, .087), (-.011, .095), (-.010, .105), (-.004, .104), (.002, .093)]
    right = [(.000, .093), (.002, .106), (.012, .111), (.012, .100), (.005, .092)]
    _front_emblem(g, 'sage_leaf_left', left, -.0528, -.0537, 3)
    _front_emblem(g, 'sage_leaf_right', right, -.0528, -.0537, 3)
    return _finish(config, g, ('cream', 'terracotta', 'brass', 'sage'))


def _profile(g, name, levels, sides, materials):
    """Revolve an outer/rim/inner profile, cap both ends, preserve real wall thickness."""
    loops = [[(r * math.cos(i * math.tau / sides), r * math.sin(i * math.tau / sides), z)
              for i in range(sides)] for r, z in levels]
    vertices = [p for loop in loops for p in loop]
    faces = [tuple(reversed(range(sides)))]
    face_materials = [materials[0]]
    for level in range(len(loops)-1):
        for i in range(sides):
            j = (i+1) % sides
            faces.append((level*sides+i, level*sides+j, (level+1)*sides+j, (level+1)*sides+i))
            face_materials.append(materials[level])
    faces.append(tuple((len(loops)-1)*sides+i for i in range(sides)))
    face_materials.append(materials[-1])
    start = len(g.faces)
    g.part(name, vertices, faces, face_materials)
    # Caps remain flat; only continuous profile side faces are smooth-shaded.
    return start+1, len(g.faces)-1


def build_cafe_cup(config):
    """Cream ceramic cafe cup, curved handle, terracotta-edged saucer and optional coffee."""
    g = _Geometry()
    smooth = []
    sides = config['geometry'].get('sides', 32)
    if type(sides) is not int or not 24 <= sides <= 48 or sides % 4:
        raise ValueError('Cup radial sides must be a multiple of four from24 to48')
    saucer = [(.030, .000), (.050, .000), (.063, .002), (.075, .008),
              (.079, .012), (.079, .015), (.075, .017), (.059, .011),
              (.041, .009), (.026, .009)]
    smooth.append(_profile(g, 'ceramic_saucer', saucer, sides, (0, 0, 0, 1, 1, 1, 0, 0, 0)))
    body = [(.027, .008), (.030, .010), (.033, .017), (.039, .090),
            (.040, .100), (.0395, .105), (.0355, .105), (.035, .100),
            (.030, .023), (.025, .018)]
    smooth.append(_profile(g, 'hollow_ceramic_cup', body, sides, (0,) * (len(body)-1)))
    # Elliptical torus: closed 24x8 sweep, left arc buried in the cup wall at the joins.
    loops = []
    for i in range(24):
        a = i * math.tau / 24
        x, z = .043 + .021*math.cos(a), .054 + .032*math.sin(a)
        nx, nz = math.cos(a)/.021, math.sin(a)/.032
        length = math.hypot(nx, nz)
        nx, nz = nx/length, nz/length
        loops.append([(x + .005*math.cos(j*math.tau/8)*nx,
                       .005*math.sin(j*math.tau/8),
                       z + .005*math.cos(j*math.tau/8)*nz) for j in range(8)])
    vertices = [p for loop in loops for p in loop]
    faces = []
    for i in range(24):
        for j in range(8):
            faces.append((i*8+j, i*8+(j+1)%8, ((i+1)%24)*8+(j+1)%8, ((i+1)%24)*8+j))
    start = len(g.faces)
    g.part('curved_ceramic_handle', vertices, faces, 0)
    smooth.append((start, len(g.faces)))
    if config['geometry'].get('includeCoffee', True):
        smooth.append(_profile(g, 'static_coffee_surface', [(.0341, .0870), (.0344, .0880),
                               (.0344, .0890)], sides, (2, 2)))
    roles = ('cream', 'terracotta', 'coffee') if config['geometry'].get('includeCoffee', True) else ('cream', 'terracotta')
    result = _finish(config, g, roles, smooth)
    result['assemblyNotes'] = 'Single cup+saucer static prop; coffee is config-driven geometry, no liquid simulation or detachable saucer.'
    return result
