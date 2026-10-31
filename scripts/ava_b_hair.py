"""Artist-authored Ava B hair, fitted to the current actual Rain-derived head.

No old Ava hair, primitive bun, imported library or body/head edits are used.
One continuous cap samples the supplied Rain head's surface and carries six
shallow integrated flow fields, with no separate raised patch ends. A closed
artist-lofted folded volume forms the low bun; two slender tapered locks form
the face-framing wisps. All coordinates are world metres.

API: build(head, hair_material, scene_collection) -> (objects, provenance)
No operators, scene resets, modifier stacks, rigging or animation are used.
"""
import math

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _cat(points, t):
    u = max(0.0, min(1.0, t)) * (len(points) - 1)
    i = min(len(points) - 2, int(u))
    u -= i
    p0, p1, p2, p3 = [Vector(points[max(0, min(len(points) - 1, j))])
                       for j in (i - 1, i, i + 1, i + 2)]
    return .5 * ((2 * p1) + (-p0 + p2) * u
                 + (2*p0 - 5*p1 + 4*p2 - p3) * u*u
                 + (-p0 + 3*p1 - 3*p2 + p3) * u*u*u)


def _value(values, t):
    x = max(0.0, min(1.0, t)) * (len(values) - 1)
    i = min(len(values) - 2, int(x))
    return values[i] * (1 - (x-i)) + values[i+1] * (x-i)


def _cubic(values, t):
    x = max(0.0, min(1.0, t)) * (len(values)-1)
    i = min(len(values)-2, int(x))
    u = x-i
    a, b, c, d = [values[max(0, min(len(values)-1, j))]
                  for j in (i-1, i, i+1, i+2)]
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u
                +(-a+3*b-3*c+d)*u*u*u)


def _mesh(name, vertices, faces, material, collection):
    data = bpy.data.meshes.new(name + '_Mesh')
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    data.materials.append(material)
    for face in data.polygons:
        face.use_smooth = True
    obj['assetId'] = 'chr_npc_ava_morgan_001'
    obj['design'] = 'Owner-approved Ava B head sheet; no v0.2 hair reuse'
    return obj


def _tree(head):
    head.data.calc_loop_triangles()
    return BVHTree.FromPolygons(
        [head.matrix_world @ v.co for v in head.data.vertices],
        [tuple(t.vertices) for t in head.data.loop_triangles],
        all_triangles=True)


def _near(tree, point):
    hit, normal, _, distance = tree.find_nearest(Vector(point))
    if hit is None:
        raise RuntimeError('Rain head surface query failed while fitting Ava B hair')
    return hit, normal.normalized(), distance


def _flow_tone(obj, tones, material):
    """Broad painted value groups only; no strand/photographic texture."""
    attr=obj.data.color_attributes.new(name='AvaB_HairFlowTone',type='FLOAT_COLOR',domain='POINT')
    shader=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    base=shader.inputs['Base Color'].default_value
    for datum,tone in zip(attr.data,tones):datum.color=(base[0]*tone,base[1]*tone,base[2]*tone,1)
    mat=bpy.data.materials.get('AvaB_Hair_BroadFlowValues')
    if mat is None:
        mat=material.copy();mat.name='AvaB_Hair_BroadFlowValues'
        p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name=attr.name
        mat.node_tree.links.new(vc.outputs['Color'],p.inputs['Base Color'])
    obj.data.materials.clear();obj.data.materials.append(mat)


def _cap(tree, material, collection, flows):
    # Boundary heights leave the ears clear. The visible hairline falls from
    # 1.600 at the forehead to just above the ear and then down to the gather.
    near_boundary = [1.593, 1.600, 1.578, 1.543, 1.513, 1.486, 1.449, 1.438]
    far_boundary = [1.587, 1.559, 1.524, 1.503, 1.510, 1.486, 1.449, 1.438]
    centre = Vector((0, -.018, 1.553))
    segments, rings = 80, 20
    vertices, faces, tones = [], [], []
    hits = 0
    flow_samples = []
    for _, points, widths, lifts in flows:
        samples = []
        for sample in range(97):
            t = sample/96
            p, _, _ = _near(tree, _cat(points, t))
            samples.append((p, max(.009, _value(widths, t)),
                            min(.012, _value(lifts, t)*.70)))
        flow_samples.append(samples)
    part_path = [(.033,-.135,1.600),(.039,-.088,1.644),
                 (.036,-.026,1.665),(.031,.024,1.655)]
    part_samples = [_near(tree, _cat(part_path, i/31))[0] for i in range(32)]

    def height(point, t):
        ridge_fields = []
        for samples in flow_samples:
            p, width, amplitude = min(samples, key=lambda s: (point-s[0]).length_squared)
            distance_squared = (point-p).length_squared
            ridge_fields.append(amplitude*math.exp(-distance_squared/(width*width*.30)))
        # Smooth maximum of per-flow fields retains readable broad ridges.
        # Averaging all samples flattened the previous probe into a swim cap.
        ridges = sum(f**6 for f in ridge_fields)**(1/6)
        lift = .0038 + .0070*t*t + min(.012, ridges)
        part_distance = min((point-p).length_squared for p in part_samples)
        lift -= .004*math.exp(-part_distance/(.006*.006))
        border = max(0.0, min(1.0, t/.13))
        border = border*border*(3-2*border)
        # The open hairline boundary is seated flush, not a raised cut ledge.
        return .0007 + (max(.0022, lift)-.0007)*border

    for row in range(rings):
        t = row / rings
        for j in range(segments):
            theta = 2 * math.pi * j / segments
            signed_angle = (theta + math.pi) % (2*math.pi) - math.pi
            angle = abs(signed_angle)
            edge = _value(near_boundary if signed_angle >= 0 else far_boundary,
                          angle / math.pi)
            # Elliptical radius is a direction estimate only. Every point is
            # obtained by a ray intersection with the actual Rain head mesh.
            radius = math.sqrt((.093*math.sin(theta))**2
                               + (.119*math.cos(theta))**2)
            lower_phi = math.atan2(edge-centre.z, radius)
            phi = lower_phi + (math.pi/2-lower_phi)*t
            direction = Vector((math.sin(theta)*math.cos(phi),
                                -math.cos(theta)*math.cos(phi), math.sin(phi)))
            point, normal, _, _ = tree.ray_cast(centre, direction, .5)
            if point is None:
                raise RuntimeError('Rain scalp radial ray missed the supplied head')
            hits += 1
            # A continuous radial frame avoids faceted offsets from the edit
            # cage's individual BVH triangle normals at the hair crown.
            normal=Vector((direction.x/.093,direction.y/.119,direction.z/.112)).normalized()
            volume=.021*math.sin(math.pi*t)**.8
            vertices.append(tuple(point + normal*(height(point, t)+volume)))
            nearflow=max(math.exp(-min((point-p).length_squared for p,w,a in samples)/(.019*.019)) for samples in flow_samples)
            tones.append(.78+.25*nearflow)
    top, normal, _, _ = tree.ray_cast(centre, Vector((0, 0, 1)), .5)
    if top is None:
        raise RuntimeError('Rain crown ray missed the supplied head')
    pole = len(vertices)
    vertices.append(tuple(top + normal.normalized()*height(top, 1)))
    tones.append(.94)
    for row in range(rings-1):
        for j in range(segments):
            a = row*segments+j
            b = row*segments+(j+1) % segments
            faces.append((a, b, b+segments, a+segments))
    for j in range(segments):
        faces.append(((rings-1)*segments+j,
                      (rings-1)*segments+(j+1) % segments, pole))
    obj = _mesh('AvaB_Hair_ScalpFit', vertices, faces, material, collection)
    bm=bmesh.new();bm.from_mesh(obj.data)
    inner=[v for v in bm.verts if not v.is_boundary]
    for _ in range(7):bmesh.ops.smooth_vert(bm,verts=inner,factor=.30,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
    _flow_tone(obj,tones,material)
    obj['method'] = 'Continuous actual-Rain-fitted cap with six blended shallow flow fields and closed left-part furrow'
    return obj, hits + 1


def _sculpted_bun(material, collection):
    """Single closed, broad-folded low-bun loft, embedded into the gather.

    Hand-set section radii/centres form the silhouette; low-amplitude twisted
    lobe fields suggest folded hair without any torus or open centre.
    """
    sections, sides = 24, 32
    vertices, faces, tones = [], [], []
    radii_x = [.009,.030,.043,.048,.042,.029,.003]
    radii_z = [.013,.032,.045,.049,.044,.032,.004]
    centre_z = [1.447,1.445,1.439,1.434,1.431,1.433,1.437]
    for i in range(sections+1):
        t = i/sections
        y = .058 + .128*t
        rx, rz = max(.002, _cubic(radii_x, t))*1.10, max(.003, _cubic(radii_z, t))*1.28
        z = _cubic(centre_z, t)-.010*math.sin(math.pi*t)
        twist = 2.4*math.pi*t
        for j in range(sides):
            theta = 2*math.pi*j/sides
            phase = theta + twist
            # Three broad, smooth folds in one closed surface. Their shallow
            # furrows stay filled; there is no central hole or detached knot.
            fold = 1 + .070*math.cos(3*phase) + .035*math.cos(2*phase+.5)
            seam = min(abs((phase-a+math.pi) % (2*math.pi)-math.pi)
                       for a in (.55, 2.64, 4.73))
            fold -= .075*math.exp(-(seam/.22)**2)
            x = rx*math.cos(theta)*fold + .003*math.sin(math.pi*t)
            yy = y + .0025*math.sin(3*phase)*math.sin(math.pi*t)**2
            zz = z + rz*math.sin(theta)*fold
            vertices.append((x, yy, zz))
            tones.append(.89+.12*math.cos(3*phase))
    for i in range(sections):
        for j in range(sides):
            a = i*sides+j
            b = i*sides+(j+1) % sides
            faces.append((a, a+sides, b+sides, b))
    front, back = len(vertices), len(vertices)+1
    vertices.extend([(0,.056,1.447), (0,.188,1.437)])
    tones.extend([.90,.90])
    for j in range(sides):
        k = (j+1) % sides
        faces.append((front, j, k))
        faces.append((back, sections*sides+k, sections*sides+j))
    obj = _mesh('AvaB_Hair_LowSculptedBun', vertices, faces, material, collection)
    bm=bmesh.new();bm.from_mesh(obj.data)
    for _ in range(4):bmesh.ops.smooth_vert(bm,verts=list(bm.verts),factor=.24,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
    _flow_tone(obj,tones,material)
    obj['method'] = 'Single closed artist-lofted low bun with broad integrated folds; front root at y .056 m overlaps scalp gather'
    return obj




def _loft(name, points, widths, depths, preferred_normal, steps, sides,
          material, collection, tree=None, clearance=.002, surface_frame=False):
    vertices, faces = [], []
    hint = Vector(preferred_normal)
    previous_normal = None
    for i in range(steps+1):
        t = i/steps
        point = _cat(points, t)
        tangent = (_cat(points, min(1, t+.001))
                   - _cat(points, max(0, t-.001))).normalized()
        local_hint = _near(tree, point)[1] if surface_frame and tree is not None else hint
        normal = local_hint-tangent*local_hint.dot(tangent)
        if normal.length < 1e-5:
            normal = Vector((1, 0, 0))-tangent*tangent.x
        normal.normalize()
        if previous_normal is not None and normal.dot(previous_normal) < 0:
            normal.negate()
        previous_normal = normal.copy()
        width_axis = normal.cross(tangent).normalized()
        width, depth = _value(widths, t), _value(depths, t)
        for j in range(sides):
            angle = 2*math.pi*j/sides
            p = point+width_axis*(width*math.cos(angle))+normal*(depth*math.sin(angle))
            if tree is not None:
                skin, n, distance = _near(tree, p)
                signed = (p-skin).dot(n)
                if distance < .014 and signed < clearance:
                    p += n*(clearance-signed)
            vertices.append(tuple(p))
    for i in range(steps):
        for j in range(sides):
            a = i*sides+j
            b = i*sides+(j+1) % sides
            faces.append((a, b, b+sides, a+sides))
    start, end = len(vertices), len(vertices)+1
    vertices += [tuple(_cat(points, 0)), tuple(_cat(points, 1))]
    for j in range(sides):
        k = (j+1) % sides
        faces.append((start, k, j))
        faces.append((end, steps*sides+j, steps*sides+k))
    return _mesh(name, vertices, faces, material, collection)




def _part_line(cap, material, collection):
    # A hair-coloured narrow groove insert reinforces the real cap furrow.
    # It is a seated surface accent, never a hole or exposed dark gap.
    tree = _tree(cap)
    path = [(.033,-.135,1.600),(.039,-.088,1.644),
            (.036,-.026,1.665),(.031,.024,1.655)]
    vertices, faces = [], []
    for i in range(33):
        t = i/32
        point, normal, _ = _near(tree, _cat(path, t))
        tangent = _cat(path, min(1,t+.002))-_cat(path, max(0,t-.002))
        tangent -= normal*tangent.dot(normal)
        tangent.normalize()
        across = normal.cross(tangent).normalized()
        width = .00080*(.6+.4*math.sin(math.pi*t))
        for sign in (-1,1):
            p, n, _ = _near(tree, point+across*(width*sign))
            vertices.append(tuple(p+n*.00065))
    for i in range(32):
        a = i*2
        faces.append((a,a+2,a+3,a+1))
    accent = material.copy()
    accent.name = 'AvaB_Hair_PartShadow'
    if accent.use_nodes:
        shader = next(n for n in accent.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        rgba = shader.inputs['Base Color'].default_value
        shader.inputs['Base Color'].default_value = (rgba[0]*.65,rgba[1]*.65,rgba[2]*.65,rgba[3])
    obj = _mesh('AvaB_Hair_LeftPartGroove', vertices, faces, accent, collection)
    obj['method'] = 'Narrow brown surface accent seated in continuous left-part furrow; no holes'
    return obj


def build(head, hair_material, scene_collection):
    """Build hair fitted to finalized Rain head; never modify that head.

    Input object geometry is read in world coordinates. Returned hair uses
    world coordinates with identity transforms. Collection must be a Blender
    Collection (for example bpy.context.scene.collection).
    """
    tree = _tree(head)
    objects = []
    # Six main flows, deliberately asymmetric about a left side part. Paths
    # locate the flow on the supplied skull; _flow_patch resolves actual fit.
    flows = [
        ('Forelock', [( .031,-.135,1.601),(.003,-.145,1.633),(-.038,-.135,1.635),
                      (-.074,-.113,1.591),(-.087,-.088,1.531)],
         [.005,.025,.030,.022,.003], [.004,.021,.022,.013,.001]),
        ('FarSweep', [(.037,-.101,1.645),(-.006,-.108,1.664),(-.057,-.075,1.645),
                      (-.090,-.017,1.571),(-.078,.053,1.497),(-.026,.089,1.454)],
         [.004,.025,.028,.023,.017,.004], [.004,.027,.021,.013,.009,.001]),
        ('FarGather', [(.034,-.036,1.665),(-.018,-.023,1.662),(-.069,.023,1.616),
                       (-.079,.069,1.537),(-.044,.092,1.474),(-.012,.099,1.448)],
         [.003,.024,.027,.025,.017,.003], [.003,.025,.020,.013,.008,.001]),
        ('NearTemple', [(.043,-.130,1.600),(.071,-.099,1.590),(.091,-.050,1.553),
                        (.092,.010,1.509),(.059,.069,1.468),(.024,.098,1.446)],
         [.003,.023,.026,.025,.018,.004], [.003,.014,.016,.014,.009,.002]),
        ('NearSweep', [(.044,-.089,1.646),(.077,-.046,1.631),(.097,.014,1.586),
                       (.084,.061,1.526),(.049,.092,1.474),(.012,.103,1.447)],
         [.003,.024,.028,.026,.018,.003], [.003,.020,.020,.015,.009,.002]),
        ('BackGather', [(.038,-.019,1.667),(.056,.031,1.650),(.063,.075,1.597),
                        (.039,.096,1.526),(0,.102,1.455)],
         [.003,.025,.031,.027,.006], [.003,.024,.019,.011,.001]),
    ]
    cap, scalp_samples = _cap(tree, hair_material, scene_collection, flows)
    objects.append(cap)
    # The forelock is integrated into the asymmetrical cap silhouette and flow
    # fields; a separate lifted slab cast an incorrect dark gap in probe-003.
    objects.append(_part_line(cap, hair_material, scene_collection))
    objects.append(_sculpted_bun(hair_material, scene_collection))
    wisps = [
        ('Near', [(.087,-.070,1.552),(.101,-.053,1.505),(.106,-.045,1.453),
                  (.104,-.049,1.407),(.099,-.064,1.358),(.103,-.075,1.325)]),
        ('Far', [(-.086,-.108,1.535),(-.100,-.114,1.484),(-.106,-.105,1.437),
                 (-.104,-.098,1.394),(-.096,-.113,1.351),(-.096,-.122,1.332)]),
    ]
    for label, points in wisps:
        obj = _loft('AvaB_Hair_FramingWisp_' + label, points,
                    [.0021,.0023,.0020,.0018,.0011,.00015],
                    [.0008,.0009,.0008,.0007,.0004,.00010],
                    (0, -1, 0), 24, 6, hair_material, scene_collection,
                    tree=tree, clearance=.0020)
        obj['method'] = 'Thin tapered authored face-framing lock; skin clearance only'
        objects.append(obj)
    triangles = 0
    for obj in objects:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
    provenance = {
        'headFitObject': head.name,
        'headModified': False,
        'originalRainHairOrRejectedAvaHairUsed': False,
        'method': 'Actual Rain head BVH sampling; continuous loose scalp with six broad flow fields and vertex-tone groups; integrated asymmetric forelock boundary; left-part furrow; closed broad-folded low bun',
        'scalpRaySamples': scalp_samples,
        'primaryFlowGroups': 6,
        'part': 'Anatomical left / positive X, root approximately (+.033,-.135,1.600) metres',
        'bun': 'Closed low upper-nape authored loft, approximately .12 x .13 x .13 m; root y .056 m overlaps scalp gather',
        'framingWisps': 2,
        'triangles': triangles,
        'style': 'Broad matte shapes and shallow flow folds; no photographic strand texture',
        'topologyNote': 'Single continuous scalp shell with hidden nape boundary; closed bun; no detached patch ends or bun hole; static visual prototype only',
    }
    return objects, provenance
