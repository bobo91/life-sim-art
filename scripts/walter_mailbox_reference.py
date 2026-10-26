"""Original procedural mailbox; import inside Blender and call build_mailbox.

No scene reset, imported assets, textures, cameras, rendering or export.  Parts
are built as closed surfaces, deliberately intersect where attached, and are
combined into one identity-transform mesh at a bottom-centre origin.
"""
from __future__ import annotations

import json
import math
import random

import bmesh
import bpy
from mathutils import Vector


def _linear_rgba(hex_colour):
    value = hex_colour.lstrip("#")
    if len(value) != 6:
        raise ValueError("Mailbox colours must be six-digit sRGB hex values")
    srgb = [int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
                 for c in srgb) + (1.0,)


class _Assembly:
    """Accumulate independently closed, bevelled construction components."""

    def __init__(self):
        self.vertices = []
        self.faces = []
        self.face_materials = []
        self.face_smooth = []
        self.parts = []

    def add(self, name, vertices, faces, material, bevel=0.0, segments=1,
            smooth_roof=False):
        bm = bmesh.new()
        try:
            verts = [bm.verts.new(v) for v in vertices]
            for face in faces:
                bm.faces.new([verts[i] for i in face])
            bm.normal_update()
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            if bevel > 0:
                # Preserve the broad curved tunnel faces; bevel construction
                # corners and cap rims rather than every shallow roof segment.
                edges = [edge for edge in bm.edges
                         if edge.is_manifold and
                         edge.calc_face_angle(0) > math.radians(25)]
                bmesh.ops.bevel(bm, geom=edges, offset=bevel,
                                offset_type="OFFSET", segments=segments,
                                profile=.5, affect="EDGES", clamp_overlap=True)
                bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.normal_update()
            bm.verts.ensure_lookup_table()
            bm.verts.index_update()
            start = len(self.vertices)
            self.vertices.extend(tuple(v.co) for v in bm.verts)
            self.faces.extend(tuple(start + v.index for v in f.verts)
                              for f in bm.faces)
            self.face_materials.extend([material] * len(bm.faces))
            self.face_smooth.extend(
                smooth_roof and abs(f.normal.y) < .1 and f.normal.z > .025
                for f in bm.faces)
            self.parts.append({"name": name, "vertexStart": start,
                               "vertices": len(bm.verts),
                               "polygons": len(bm.faces)})
        finally:
            bm.free()

    def box(self, name, center, size, material, bevel=.003, segments=1):
        center = Vector(center)
        half = Vector(size) / 2
        corners = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                   (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
        vertices = [tuple(center + Vector((x * half.x, y * half.y, z * half.z)))
                    for x, y, z in corners]
        self.add(name, vertices,
                 [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
                 material, bevel, segments)

    def tunnel(self, name, width, wall_height, bottom, y_center, depth,
               material, roof_segments=14, bevel=.0025):
        radius = width / 2
        # CCW outline in the X/Z section: flat bottom, straight lower walls,
        # semicircular roof. End caps and wall quads make a closed solid.
        outline = [(-radius, bottom), (radius, bottom)]
        outline.extend((radius * math.cos(i * math.pi / roof_segments),
                        bottom + wall_height + radius * math.sin(i * math.pi / roof_segments))
                       for i in range(roof_segments + 1))
        n = len(outline)
        vertices = [(x, y, z) for y in (y_center - depth / 2,
                                       y_center + depth / 2)
                    for x, z in outline]
        faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
        faces.extend((i, n + i, n + (i + 1) % n, (i + 1) % n)
                     for i in range(n))
        self.add(name, vertices, faces, material, bevel, 2, smooth_roof=True)

    def cylinder(self, name, center, radius, depth, axis, material, sides=10,
                 phase=0.0, bevel=.0008):
        normal = Vector(axis).normalized()
        tangent = normal.cross(Vector((0, 0, 1)))
        if tangent.length < 1e-5:
            tangent = normal.cross(Vector((0, 1, 0)))
        tangent.normalize()
        bitangent = normal.cross(tangent).normalized()
        center = Vector(center)
        vertices = [tuple(center + normal * end * depth / 2 +
                          radius * (math.cos(phase + i * math.tau / sides) * tangent +
                                    math.sin(phase + i * math.tau / sides) * bitangent))
                    for end in (-1, 1) for i in range(sides)]
        faces = [tuple(reversed(range(sides))), tuple(range(sides, 2 * sides))]
        faces.extend((i, (i + 1) % sides, sides + (i + 1) % sides, sides + i)
                     for i in range(sides))
        self.add(name, vertices, faces, material, bevel, 1)

    def beam(self, name, start, end, width, thickness, material, bevel=.003,
             face_normal=None):
        a, b = Vector(start), Vector(end)
        direction = (b - a).normalized()
        if face_normal is not None:
            side = Vector(face_normal).normalized().cross(direction)
        else:
            side = direction.cross(Vector((0, 0, 1)))
            if side.length < 1e-6:
                side = direction.cross(Vector((0, 1, 0)))
        side.normalize()
        other = direction.cross(side).normalized()
        vertices = [tuple(p + s * side * width / 2 + t * other * thickness / 2)
                    for p in (a, b) for s, t in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.add(name, vertices, faces, material, bevel, 1)

    def tapered_post(self, name, material):
        vertices = [(x * half, y * half, z)
                    for half, z in ((.072, .065), (.059, 1.075))
                    for x, y in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
        self.add(name, vertices,
                 [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
                 material, .007, 2)


def _materials(prefix, palette):
    materials = []
    for role in ("paint", "edge", "wood", "accent"):
        spec = palette[role]
        material = bpy.data.materials.new(prefix + "__" + role)
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = _linear_rgba(spec["color"])
        shader.inputs["Roughness"].default_value = float(spec["roughness"])
        shader.inputs["Metallic"].default_value = float(spec["metallic"])
        material.diffuse_color = _linear_rgba(spec["color"])
        materials.append(material)
    return materials


def build_mailbox(config):
    """Build and return one mailbox mesh. Source +Z-up, door faces -Y.

    Geometry is already authored at the proposed 0.36 x 1.43 x 0.62 exported
    X/Y/Z metre envelope. Only one common centring translation is applied; no
    silhouette fitting or scaling to the streetlamp benchmark occurs.
    """
    asset_id = config.get("assetId", "prop_mailbox_001")
    if bpy.data.objects.get(asset_id):
        raise ValueError("Mailbox object already exists: " + asset_id)
    dimensions = config.get("dimensionsMeters", [.36, 1.43, .62])
    if len(dimensions) != 3 or any(abs(a - b) > 1e-8
                                    for a, b in zip(dimensions, (.36, 1.43, .62))):
        raise ValueError("Mailbox 0.1.0 is authored for proposed dimensions [.36,1.43,.62]")
    seed = int(config.get("seed", 2401))
    rng = random.Random(seed)
    geometry = _Assembly()
    paint, edge, wood, accent = range(4)
    name = lambda part: asset_id + "__" + part

    # Warm timber rises out of a broad, quiet chamfered stone footing. The
    # balanced foot controls overall width and provides a true ground contact.
    geometry.box(name("stone_foot"), (0, 0, .04), (.36, .32, .08), edge, .014, 2)
    geometry.box(name("stone_post_collar"), (0, 0, .09), (.20, .19, .055), edge, .007)
    geometry.tapered_post(name("tapered_timber_post"), wood)
    geometry.box(name("timber_saddle"), (0, -.005, 1.052), (.143, .46, .067), wood, .006, 2)
    geometry.beam(name("timber_front_brace"), (0, -.054, .755),
                  (0, -.206, 1.025), .065, .055, wood, .004)
    geometry.box(name("painted_mount_plate"), (0, 0, 1.086),
                 (.25, .48, .022), paint, .004)

    # Main shell is a closed authored tunnel, not a rotated cylinder or open
    # half-cylinder. A thinner independent front door sits on the front cap.
    geometry.tunnel(name("rounded_tunnel_shell"), .32, .165, 1.085, 0, .58,
                    paint, roof_segments=14, bevel=.0028)
    geometry.tunnel(name("front_door_seal"), .309, .162, 1.090, -.294, .009,
                    paint, roof_segments=14, bevel=.0012)
    geometry.tunnel(name("front_door"), .293, .163, 1.095, -.303, .012,
                    edge, roof_segments=14, bevel=.0024)
    # The centre handle has the most-forward point at Y=-.330; with the back
    # at +.290 it fixes the .620 m depth. Hinge is a visible dark lower roll.
    geometry.cylinder(name("lower_hinge_barrel"), (0, -.303, 1.101),
                      .010, .204, (1, 0, 0), paint, sides=10)
    geometry.box(name("front_latch"), (0, -.319, 1.332),
                 (.035, .022, .025), paint, .003)
    geometry.box(name("latch_grip"), (0, -.321, 1.345),
                 (.052, .018, .012), accent, .002)

    # Two broad lower hinge knuckles and two flush timber fasteners explain
    # construction while remaining a small accent, rather than surface noise.
    for index, x in enumerate((-.093, .093)):
        geometry.cylinder(name("hinge_knuckle_" + str(index)), (x, -.303, 1.101),
                          .012, .025, (1, 0, 0), paint, sides=10)
    for index, z in enumerate((.79, .958)):
        geometry.cylinder(name("timber_bolt_" + str(index)), (0, -.066, z),
                          .011, .009, (0, 1, 0), edge, sides=8,
                          phase=rng.random() * math.tau)

    # Raised flag on the right side is a coherent closed extruded silhouette.
    # Its paddle's upper horizontal edge fixes the full 1.430 m height.
    geometry.cylinder(name("flag_pivot"), (.164, .070, 1.235), .024, .024,
                      (1, 0, 0), edge, sides=12)
    geometry.cylinder(name("flag_pivot_cap"), (.175, .070, 1.235), .010, .008,
                      (1, 0, 0), paint, sides=8,
                      phase=rng.random() * math.tau)
    geometry.box(name("raised_flag_stem"), (.170, .070, 1.320),
                 (.012, .019, .186), accent, .002)
    flag_outline = [(.060, 1.367), (.166, 1.367), (.151, 1.398),
                    (.166, 1.430), (.060, 1.430)]
    n = len(flag_outline)
    # Enclose the overlapping stem's X faces (.164/.176), rather than sharing
    # their planes: the coplanar overlap made a dark rectangle in run-001/002.
    vertices = [(x, y, z) for x in (.162, .178) for y, z in flag_outline]
    faces = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    faces.extend((i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n))
    geometry.add(name("flag_paddle"), vertices, faces, accent, .002, 1)

    # Original geometric address mark, not an external font or a texture.
    # The number can disappear at distant gameplay scale without harming the
    # door/box/post/flag silhouette; it is deliberately secondary detail.
    if config.get("addressMark", "17") != "17":
        raise ValueError("Only original procedural address mark '17' is defined")
    strokes = [((-.043, 1.274), (-.033, 1.284)),
               ((-.033, 1.284), (-.033, 1.224)),
               ((-.044, 1.224), (-.022, 1.224)),
               ((.003, 1.284), (.044, 1.284)),
               ((.044, 1.284), (.014, 1.224))]
    for index, ((x0, z0), (x1, z1)) in enumerate(strokes):
        geometry.beam(name("address_stroke_" + str(index)),
                      (x0, -.311, z0), (x1, -.311, z1), .0065, .003,
                      paint, .00065, face_normal=(0, -1, 0))

    # One translation yields the actual common bounding-box bottom centre;
    # every part retains its designed relative size and attachment positions.
    mins = [min(v[axis] for v in geometry.vertices) for axis in range(3)]
    maxs = [max(v[axis] for v in geometry.vertices) for axis in range(3)]
    offset = ((mins[0] + maxs[0]) / 2, (mins[1] + maxs[1]) / 2, mins[2])
    vertices = [tuple(v[i] - offset[i] for i in range(3)) for v in geometry.vertices]
    mesh = bpy.data.meshes.new(asset_id + "__mesh")
    mesh.from_pydata(vertices, [], geometry.faces)
    for material in _materials(asset_id, config["palette"]):
        mesh.materials.append(material)
    for polygon, material_index, smooth in zip(mesh.polygons, geometry.face_materials,
                                                geometry.face_smooth):
        polygon.material_index = material_index
        polygon.use_smooth = bool(smooth)
    mesh.update()
    asset = bpy.data.objects.new(asset_id, mesh)
    bpy.context.collection.objects.link(asset)
    asset["sourceAxisUp"] = "+Z"
    asset["sourceAxisForward"] = "-Y"
    asset["forwardProbe"] = "Front tunnel-profile pale door, latch and geometric 17 face Blender -Y"
    door = next(p for p in geometry.parts if p["name"] == name("front_door"))
    door_indices = range(door["vertexStart"], door["vertexStart"] + door["vertices"])
    door_front_y = min(vertices[i][1] for i in door_indices)
    candidates = [i for i in door_indices if abs(vertices[i][1] - door_front_y) < 1e-7]
    probe_index = min(candidates, key=lambda i: abs(vertices[i][0]) +
                      .25 * abs(vertices[i][2] - 1.25))
    asset["forwardProbeSourcePoint"] = list(vertices[probe_index])
    asset["forwardProbeSourceVertexIndex"] = probe_index
    asset["provenance"] = "Original procedural vertices/faces/materials; no imported mesh, font or texture"
    asset["seed"] = seed
    asset["constructionParts"] = json.dumps(geometry.parts, separators=(",", ":"))
    asset["geometryNotes"] = "Individually closed parts intentionally overlap at construction attachments; static closed mailbox, no opening animation or collider"
    return asset
