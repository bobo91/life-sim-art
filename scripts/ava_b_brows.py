"""Natural tapered Ava B brows on the already-shaped Rain head.

Public API: build(head, hair_material, collection) -> (objects, metadata).
This module creates only surface-conforming eyebrow strips. It never edits the
head, creates a rig, changes an expression, or writes an external texture.
Coordinates are metres in the prototype's world space (front is negative Y).
"""
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


_ALPHA = 'ava_b_brow_opacity'
_OFFSET = 0.00035
_SEGMENTS = 24
_ACROSS = 6


def _smooth(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def _centre(t):
    """Continuous inner/arch/tail contour from the locked neutral B design."""
    x = 0.018 + 0.061 * t
    # Gentle rising inner brow; a longer, softly falling outer third.
    if t <= 0.53:
        z = 1.523 + 0.007 * math.sin((t / 0.53) * math.pi / 2.0)
    else:
        z = 1.530 - 0.012 * _smooth(0.53, 1.0, t)
    # Full vertical width, not radius. Never a cylindrical/tubular cross-section.
    # Feathered edges make only the middle ~60% read as visible pigment.
    # A wider soft envelope gives B's natural 2–4 mm coverage in the render
    # instead of the initial very faint pencil-line appearance.
    width = 1.4 * (0.0033 + 0.0010 * math.sin(math.pi * t))
    width *= 1.0 - 0.84 * _smooth(0.64, 1.0, t)
    return x, z, width


def _material(hair_material):
    """Lower-contrast brown with interpolated feathered surface opacity."""
    colour = (0.060, 0.028, 0.014, 1.0)
    if hair_material and hair_material.use_nodes:
        source = next((n for n in hair_material.node_tree.nodes
                       if n.type == 'BSDF_PRINCIPLED'), None)
        if source:
            base = source.inputs['Base Color'].default_value
            # Modest warm lightening; do not alter the supplied hair material.
            colour = tuple(0.75 * float(base[i]) + 0.25 * colour[i]
                           for i in range(3)) + (1.0,)
    mat = bpy.data.materials.new('AvaB_NaturalBrows_FeatheredBrown')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    surface = nodes.new('ShaderNodeBsdfPrincipled')
    surface.inputs['Base Color'].default_value = colour
    surface.inputs['Roughness'].default_value = 0.86
    opacity = nodes.new('ShaderNodeAttribute')
    opacity.attribute_name = _ALPHA
    clear = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    out = nodes.new('ShaderNodeOutputMaterial')
    links = mat.node_tree.links
    links.new(opacity.outputs['Fac'], mix.inputs[0])
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(surface.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs['Surface'])
    # Enable the available transparent surface mode without relying on version-
    # specific RNA enum values. Cycles also uses the transparent shader directly.
    prop = mat.bl_rna.properties.get('surface_render_method')
    if prop:
        choices = {item.identifier for item in prop.enum_items}
        if 'DITHERED' in choices:
            mat.surface_render_method = 'DITHERED'
    mat.diffuse_color = colour
    mat['purpose'] = 'Ava B natural brows; feathered low-contrast surface pigment'
    mat['externalTextures'] = 0
    return mat


def build(head, hair_material, collection):
    """Project two soft tapered brow surfaces onto the current head mesh.

    The caller must provide the final shaped head at its intended metre scale.
    A missing ray hit is an error, never a silently floating fallback brow.
    The BVH contains only head geometry, so hair/eyelashes cannot intercept it.
    """
    if head.type != 'MESH':
        raise TypeError('Ava B brows require a shaped mesh head')
    matrix = head.matrix_world.copy()
    evaluated=head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    surface=evaluated.to_mesh()
    points = [matrix @ v.co for v in surface.vertices]
    polygons = [tuple(p.vertices) for p in surface.polygons]
    bvh = BVHTree.FromPolygons(points, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    mat = _material(hair_material)
    objects, records = [], []
    for sign, side in [(1, 'L'), (-1, 'R')]:
        vertices, faces, opacity = [], [], []
        for i in range(_SEGMENTS + 1):
            t = i / _SEGMENTS
            x, centre, width = _centre(t)
            # The root and tail dissolve in opacity instead of ending abruptly.
            end = _smooth(0.0, 0.11, t) * (1.0 - _smooth(0.86, 1.0, t))
            for j in range(_ACROSS + 1):
                cross = -1.0 + 2.0 * j / _ACROSS
                # Tiny edge irregularity prevents a perfectly drawn graphic bar.
                fringe = 0.00014 * math.sin(19.0 * t + 1.7 * j)
                z = centre + cross * width * 0.5 + fringe * abs(cross)
                hit, normal, index, distance = bvh.ray_cast(
                    Vector((sign * x, -1.0, z)), Vector((0, 1, 0)), 2.0)
                if hit is None:
                    raise ValueError(f'Ava B brow {side} missed head at x={sign*x:.6f}, z={z:.6f}')
                # Orient the offset towards the incident camera/front, even if
                # an isolated source polygon has inverted winding.
                if normal.y > 0:
                    normal = -normal
                normal.normalize()
                vertices.append(tuple(hit + normal * _OFFSET))
                feather = max(0.0, 1.0 - cross * cross) ** 1.4
                variation = 0.86 + 0.14 * math.sin(37.0 * t + 2.3 * j) ** 2
                opacity.append(0.82 * end * feather * variation)
        row = _ACROSS + 1
        for i in range(_SEGMENTS):
            for j in range(_ACROSS):
                a = i * row + j
                face = (a, a + row, a + row + 1, a + 1)
                faces.append(face if sign > 0 else tuple(reversed(face)))
        mesh = bpy.data.meshes.new(f'AvaB_Brow_{side}_Surface')
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        attr = mesh.attributes.new(_ALPHA, 'FLOAT', 'POINT')
        for datum, alpha in zip(attr.data, opacity):
            datum.value = alpha
        obj = bpy.data.objects.new(f'AvaB_NaturalBrow_{side}', mesh)
        collection.objects.link(obj)
        obj.data.materials.append(mat)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        if hasattr(obj, 'visible_shadow'):
            obj.visible_shadow = False
        obj['source'] = 'Ava B locked design contour; surface-projected onto shaped Rain head'
        obj['surfaceOffsetMetres'] = _OFFSET
        obj['scope'] = 'static visual head prototype; no rig or expression work'
        objects.append(obj)
        records.append({'object': obj.name, 'vertices': len(vertices),
                        'triangles': len(faces) * 2, 'rayMisses': 0,
                        'maximumSurfaceOffsetMetres': _OFFSET,
                        'maximumOpacity': max(opacity),
                        'minimumZ': min(v[2] for v in vertices),
                        'maximumZ': max(v[2] for v in vertices)})
    return objects, {'method': 'Tapered feather-opacity mesh strips, BVH front-projected onto actual shaped head',
                     'contourMetres': {'inner': [0.018, 1.523], 'arch': [0.050, 1.530],
                                       'tail': [0.079, 1.518]},
                     'headGeometryModified': False, 'externalTextures': 0,
                     'brows': records, 'triangles': sum(r['triangles'] for r in records)}
