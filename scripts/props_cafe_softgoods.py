"""Original deterministic cloth and freestanding parasol for the cafe pack.

No simulation, purchased mesh, image, manual sculpt or external content. The
cloth fits the approved .78 m table without altering that table's geometry.
"""
import json
import math

import bmesh
import bpy

from props_cafe_table import _Geometry, _material


def _finish(geometry, config, smooth=False):
    if bpy.app.version[:3] != tuple(map(int, config['blenderVersion'].split('.'))):
        raise ValueError('Use the configured Blender version')
    prefix = config['assetId']
    mesh = bpy.data.meshes.new(prefix + '__mesh')
    mesh.from_pydata(geometry.vertices, [], geometry.faces)
    for role, spec in config['palette'].items():
        mesh.materials.append(_material(prefix + '__' + role, spec))
    for face, material in zip(mesh.polygons, geometry.material_indices):
        face.material_index = material
        face.use_smooth = smooth
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(mesh); bm.free(); mesh.update()
    obj = bpy.data.objects.new(prefix, mesh)
    bpy.context.collection.objects.link(obj)
    obj['assetId'] = prefix
    obj['seed'] = config['seed']
    obj['generator'] = 'scripts/props_cafe_softgoods.py:' + config['generator']
    obj['constructionParts'] = json.dumps(geometry.parts)
    obj['provenance'] = 'Original deterministic vertices/materials; no external content or simulation'
    obj['sourceAxes'] = 'Blender Z-up / -Y-forward; bottom-center origin'
    return obj


def _outline_ray(theta, half_extent, corner):
    """Ray intersection with a rounded square, with stable angular sampling."""
    c, s = abs(math.cos(theta)), abs(math.sin(theta))
    low, high = 0.0, half_extent * math.sqrt(2)
    for _ in range(48):
        distance = (low + high) / 2
        x, y = distance * c, distance * s
        dx, dy = max(x - half_extent + corner, 0), max(y - half_extent + corner, 0)
        inside = x <= half_extent and y <= half_extent and dx*dx + dy*dy <= corner*corner
        if inside: low = distance
        else: high = distance
    return low


def build_cafe_tablecloth(config):
    """A closed 2 mm shell with a flat support area and broad hanging folds."""
    spec = config['geometry']
    n, thickness = spec['perimeterSamples'], spec['thicknessMeters']
    top_z = spec['supportTopLocalMeters'] - thickness
    half_support = spec['supportWidthMeters'] / 2
    half_outer = config['dimensionsMeters'][0] / 2
    if n % 8 or n < 32 or not (0 < thickness < .006):
        raise ValueError('Cloth needs an eight-fold sample count and thin positive shell')
    geometry = _Geometry()
    # (interior support fraction, drape interpolation, height, four-fold height).
    levels = ((.30, 0, top_z, 0), (.78, 0, top_z, 0),
              (1, 0, top_z, 0), (1, .14, top_z-.006, 0),
              (1, .45, .132, .004), (1, .75, .074, .010),
              (1, .90, .045, .014), (1, 1, .020, .020))
    rings = []
    for interior, drape, z, wave in levels:
        ring = []
        for i in range(n):
            theta = math.tau * i / n
            supported = _outline_ray(theta, half_support, spec['supportCornerRadiusMeters'])
            outer = _outline_ray(theta, half_outer, spec['outerCornerRadiusMeters'])
            distance = supported * interior * (1-drape) + outer * drape
            ring.append((distance*math.cos(theta), distance*math.sin(theta),
                         z + wave*math.cos(4*theta)))
        rings.append(ring)
    top = [point for ring in rings for point in ring]
    # A uniform shift puts the lowest underside exactly on local Z=0.
    lift = thickness - min(v[2] for v in top)
    top = [(x, y, z+lift) for x, y, z in top]
    bottom = [(x, y, z-thickness) for x, y, z in top]
    vertices = top + [(0, 0, top_z+lift)] + bottom + [(0, 0, top_z+lift-thickness)]
    top_center, bottom_offset = len(top), len(top)+1
    bottom_center = len(vertices)-1
    faces, materials = [], []
    for i in range(n):
        j = (i+1) % n
        faces.append((top_center, i, j)); materials.append(0)
        faces.append((bottom_center, bottom_offset+j, bottom_offset+i)); materials.append(0)
    for ring in range(len(rings)-1):
        for i in range(n):
            j = (i+1) % n
            a, b, c, d = ring*n+i, (ring+1)*n+i, (ring+1)*n+j, ring*n+j
            faces.append((a, b, c, d)); materials.append(1 if ring == len(rings)-2 else 0)
            faces.append(tuple(bottom_offset+k for k in (d, c, b, a)))
            materials.append(1 if ring == len(rings)-2 else 0)
    edge = (len(rings)-1)*n
    for i in range(n):
        j = (i+1) % n
        faces.append((edge+i, bottom_offset+edge+i, bottom_offset+edge+j, edge+j)); materials.append(1)
    geometry.part('closed_draped_cloth_and_woven_hem', vertices, faces, materials)
    obj = _finish(geometry, config, smooth=True)
    obj['supportTopLocalMeters'] = top_z+lift
    obj['supportUndersideLocalMeters'] = top_z+lift-thickness
    obj['placementOriginHeightMeters'] = spec['tableHeightMeters'] + spec['tableClearanceMeters'] - (top_z+lift-thickness)
    obj['constructionNotes'] = 'One closed 2 mm shell; no cloth solver. Broad corner drops and quiet contrasting hem.'
    return obj


def _parasol_canopy(geometry, spec):
    samples = spec['perimeterSamples']
    radius, crown = spec['canopyRadiusMeters'], spec['crownHeightMeters']
    if samples % 8:
        raise ValueError('Canopy sample count must divide into eight panels')
    per_panel = samples // 8
    roof = ((.04, crown), (.22, crown-.020), (.55, crown-.090),
            (.82, crown-.165), (1, crown-.230))

    def loop(fraction, z, inner=False, skirt=False):
        ring = []
        for i in range(samples):
            theta = math.tau*i/samples
            panel_t = (i % per_panel)/per_panel
            midpoint = (math.floor(i/per_panel)+.5)*math.pi/4
            edge_radius = radius*math.cos(math.pi/8)/math.cos(theta-midpoint)
            distance = edge_radius*fraction - (.004 if inner else 0)
            if skirt:
                height = crown-.285-.025*math.sin(math.pi*panel_t)
                if inner: height += .002
            else:
                height = z + .018*math.sin(math.pi*panel_t)*math.sin(math.pi*fraction)
                if inner: height -= .006
            ring.append((distance*math.cos(theta), distance*math.sin(theta), height))
        return ring

    loops = [loop(fraction, z) for fraction, z in roof]
    loops.extend((loop(1, 0, skirt=True), loop(1, 0, inner=True, skirt=True)))
    loops.extend(loop(fraction, z, inner=True) for fraction, z in reversed(roof))
    vertices = [v for ring in loops for v in ring]
    faces = [tuple(reversed(range(samples)))]; materials = [0]
    for k in range(len(loops)-1):
        for i in range(samples):
            j = (i+1) % samples
            faces.append((k*samples+i, k*samples+j, (k+1)*samples+j, (k+1)*samples+i))
            materials.append((i//per_panel) % 2)
    faces.append(tuple((len(loops)-1)*samples+i for i in range(samples))); materials.append(0)
    geometry.part('closed_eight_panel_canopy_with_scalloped_valance', vertices, faces, materials)


def build_cafe_parasol(config):
    """Freestanding octagonal shade. No hole/change in the approved table."""
    geometry = _Geometry(); spec = config['geometry']
    _parasol_canopy(geometry, spec)
    geometry.radial('bevelled_weighted_base', [(0, .190), (.012, .220), (.065, .210), (.085, .170)], 24, 2)
    geometry.radial('base_pole_socket', [(.06, .050), (.095, .050), (.115, .033)], 16, 2)
    geometry.radial('tapered_timber_pole', [(.08, .024), (.15, .025), (2.08, .021), (2.22, .017)], 16, 3)
    geometry.radial('rounded_canopy_finial', [(2.205, .026), (2.224, .024), (2.240, .017), (2.25, .006)], 16, 0)
    obj = _finish(geometry, config, smooth=False)
    # Smooth broad radial fabric while keeping base/pole edges deliberately controlled.
    canopy_vertex_count = 12 * spec['perimeterSamples']
    for face in obj.data.polygons:
        if all(index < canopy_vertex_count for index in face.vertices):
            face.use_smooth = True
    obj['constructionNotes'] = 'Closed thick octagonal roof and valance; weighted base, closed timber post and finial intentionally meet.'
    obj['assemblyRecommendation'] = 'Suggested Blender XY offset(.95,.60) from table center, clear of side chairs. Pole/base remain outside .78 m table. Canopy overhangs table corner; no table hole or mesh change.'
    return obj
