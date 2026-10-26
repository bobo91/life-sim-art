"""Original cafe table geometry, built from vertices in a caller-owned Blender scene.

The public entry point is build_cafe_table(config). It returns one mesh object at
the bottom-centre origin in Blender Z-up coordinates. No scene, render, exporter,
selection, or unrelated datablock is changed. The source contains no external
meshes, images, shaders or texture dependencies.
"""

import json
import math
import random

import bmesh
import bpy


def _linear(hex_color):
    values = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    return tuple(value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
                 for value in values) + (1.0,)


def _material(name, spec):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = _linear(spec["color"])
    shader.inputs["Roughness"].default_value = spec["roughness"]
    shader.inputs["Metallic"].default_value = spec["metallic"]
    material.diffuse_color = _linear(spec["color"])
    return material


class _Geometry:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.material_indices = []
        self.parts = []

    def part(self, name, vertices, faces, materials):
        offset = len(self.vertices)
        self.vertices.extend(vertices)
        self.faces.extend(tuple(offset + index for index in face) for face in faces)
        if isinstance(materials, int):
            self.material_indices.extend([materials] * len(faces))
        else:
            self.material_indices.extend(materials)
        self.parts.append(name)

    def loft(self, name, loops, material, cap_material=None):
        count = len(loops[0])
        if any(len(loop) != count for loop in loops):
            raise ValueError("Loft loops must have the same vertex count")
        vertices = [point for loop in loops for point in loop]
        faces = [tuple(reversed(range(count)))]
        materials = [material if cap_material is None else cap_material]
        for level in range(len(loops) - 1):
            for index in range(count):
                other = (index + 1) % count
                faces.append((level * count + index, level * count + other,
                              (level + 1) * count + other, (level + 1) * count + index))
                materials.append(material)
        faces.append(tuple((len(loops) - 1) * count + index for index in range(count)))
        materials.append(material if cap_material is None else cap_material)
        self.part(name, vertices, faces, materials)

    def radial(self, name, levels, sides, material, phase=0):
        self.loft(name, [[(radius * math.cos(phase + index * math.tau / sides),
                            radius * math.sin(phase + index * math.tau / sides), height)
                           for index in range(sides)] for height, radius in levels], material)


def _rounded_rect(width, depth, radius, corner_segments=6):
    """A counter-clockwise convex outline without duplicate corner endpoints."""
    points = []
    for x, y, angle in ((width / 2 - radius, depth / 2 - radius, 0),
                         (-width / 2 + radius, depth / 2 - radius, 90),
                         (-width / 2 + radius, -depth / 2 + radius, 180),
                         (width / 2 - radius, -depth / 2 + radius, 270)):
        for index in range(corner_segments + 1):
            theta = math.radians(angle + index * 90 / corner_segments)
            point = (x + radius * math.cos(theta), y + radius * math.sin(theta))
            if not points or math.dist(points[-1], point) > 1e-10:
                points.append(point)
    return points


def _clip_x(polygon, boundary, keep_greater):
    result = []
    for point, previous in zip(polygon, polygon[-1:] + polygon[:-1]):
        inside = point[0] >= boundary - 1e-12 if keep_greater else point[0] <= boundary + 1e-12
        was_inside = previous[0] >= boundary - 1e-12 if keep_greater else previous[0] <= boundary + 1e-12
        if inside != was_inside:
            t = (boundary - previous[0]) / (point[0] - previous[0])
            result.append((boundary, previous[1] + t * (point[1] - previous[1])))
        if inside:
            result.append(point)
    clean = []
    for point in result:
        if not clean or math.dist(point, clean[-1]) > 1e-10:
            clean.append(point)
    if len(clean) > 1 and math.dist(clean[0], clean[-1]) < 1e-10:
        clean.pop()
    return clean


def _inset_convex(polygon, outer_amount, join_amount, joins):
    """Intersect inward-offset lines; plank joins get a much smaller edge break."""
    lines = []
    for point, following in zip(polygon, polygon[1:] + polygon[:1]):
        dx, dy = following[0] - point[0], following[1] - point[1]
        length = math.hypot(dx, dy)
        nx, ny = -dy / length, dx / length
        at_join = any(abs(point[0] - value) < 1e-9 and abs(following[0] - value) < 1e-9
                      for value in joins)
        amount = join_amount if at_join else outer_amount
        lines.append(((point[0] + nx * amount, point[1] + ny * amount), (dx, dy)))
    result = []
    for previous, current in zip(lines[-1:] + lines[:-1], lines):
        p, direction = previous
        q, other = current
        determinant = direction[0] * other[1] - direction[1] * other[0]
        if abs(determinant) < 1e-12:
            result.append(q)
            continue
        delta = (q[0] - p[0], q[1] - p[1])
        t = (delta[0] * other[1] - delta[1] * other[0]) / determinant
        result.append((p[0] + t * direction[0], p[1] + t * direction[1]))
    return result


def _plank(geometry, name, outline, bottom, top, edge_break, joins, face_material):
    lower = _inset_convex(outline, edge_break * .65, .00035, joins)
    upper = _inset_convex(outline, edge_break, .00065, joins)
    # A narrow bevel and credible 45 mm solid edge are geometry, not painted highlights.
    levels = ((bottom, lower), (bottom + edge_break * .65, outline),
              (top - edge_break, outline), (top, upper))
    count = len(outline)
    vertices = [(x, y, height) for height, loop in levels for x, y in loop]
    faces = [tuple(reversed(range(count)))]
    materials = [2]
    for level in range(len(levels) - 1):
        for index in range(count):
            other = (index + 1) % count
            faces.append((level * count + index, level * count + other,
                          (level + 1) * count + other, (level + 1) * count + index))
            materials.append(face_material if level == 2 else 2)
    faces.append(tuple(3 * count + index for index in range(count)))
    materials.append(face_material)
    geometry.part(name, vertices, faces, materials)


def _foot(geometry, angle, span, height):
    """Swept cast-metal outrigger with a rising toe and a real ground contact."""
    direction = (math.cos(angle), math.sin(angle))
    across = (-direction[1], direction[0])
    # Perpendicular octagonal cross sections create deliberate bevels on the feet.
    section = ((-.36, -.5), (.36, -.5), (.5, -.26), (.5, .26),
               (.36, .5), (-.36, .5), (-.5, .26), (-.5, -.26))
    levels = ((.025, height * .080, .058, .058),
              (.085, height * .065, .063, .052),
              (span / 2 - .027, .018, .053, .036),
              (span / 2, .020, .040, .022))
    loops = []
    for radius, z, width, thickness in levels:
        loops.append([(direction[0] * radius + across[0] * lateral * width,
                       direction[1] * radius + across[1] * lateral * width,
                       z + vertical * thickness) for lateral, vertical in section])
    geometry.loft("cast_foot_" + str(round(math.degrees(angle))), loops, 3)


def build_cafe_table(config):
    """Build one warm timber/pedestal cafe table; config dimensions are export X/Y/Z."""
    if bpy.app.version[:3] != tuple(int(value) for value in config["blenderVersion"].split(".")):
        raise ValueError("Cafe table generator requires the configured Blender version")
    width, height, depth = config["dimensionsMeters"]
    if not all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0
               for value in (width, height, depth)):
        raise ValueError("Table dimensions must be finite, positive metres")
    spec = config["geometry"]
    thickness, radius, bevel = (spec[key] for key in ("topThicknessMeters", "cornerRadiusMeters", "edgeBevelMeters"))
    board_count, gap = spec["plankCount"], spec["plankGapMeters"]
    foot_span = spec["footSpanMeters"]
    if not (.025 <= thickness <= .07 and .002 <= bevel < thickness / 3
            and bevel * 2 < radius < min(width, depth) / 3
            and type(board_count) is int and 2 <= board_count <= 6
            and 0 <= gap <= .003 and .4 <= foot_span <= min(width, depth)
            and height > thickness + .4):
        raise ValueError("Table construction dimensions are outside the supported authoring range")
    rng = random.Random(config["seed"])
    geometry = _Geometry()
    outline = _rounded_rect(width, depth, radius, spec.get("cornerSegments", 6))
    cuts = [-width / 2]
    cuts.extend(-width / 2 + width * index / board_count + rng.uniform(-.004, .004)
                for index in range(1, board_count))
    cuts.append(width / 2)
    for index in range(board_count):
        left = cuts[index] + (gap / 2 if index else 0)
        right = cuts[index + 1] - (gap / 2 if index < board_count - 1 else 0)
        plank_outline = _clip_x(_clip_x(outline, left, True), right, False)
        joins = ([left] if index else []) + ([right] if index < board_count - 1 else [])
        _plank(geometry, "timber_plank_" + str(index + 1), plank_outline,
               height - thickness, height, bevel, joins, (0, 1, 0, 1, 0, 1)[index])
    # A quiet cast base leaves room for two adult chairs and ordinary knee clearance.
    geometry.radial("central_hub", [(0.025, .063), (.043, .067), (.084, .051), (.101, .042)], 12, 3,
                    phase=math.pi / 12)
    geometry.radial("tapered_pedestal", [(.075, .043), (.115, .039),
                     (height - thickness - .072, .034),
                     (height - thickness - .029, .048)], 12, 3, phase=math.pi / 12)
    geometry.radial("upper_collar", [(height - thickness - .052, .043),
                     (height - thickness - .037, .058),
                     (height - thickness - .021, .066)], 12, 3, phase=math.pi / 12)
    plate_outline = _rounded_rect(.275, .275, .022, 3)
    geometry.loft("underside_mounting_plate",
                  [[(x, y, z) for x, y in plate_outline]
                   for z in (height - thickness - .025, height - thickness + .003)], 3)
    for index in range(4):
        _foot(geometry, index * math.pi / 2 + math.pi / 4, foot_span, height)
    prefix = config["assetId"]
    mesh = bpy.data.meshes.new(prefix + "__mesh")
    mesh.from_pydata(geometry.vertices, [], geometry.faces)
    for role in ("wood", "woodVariation", "woodEdge", "metal"):
        mesh.materials.append(_material(prefix + "__" + role, config["palette"][role]))
    for polygon, material_index in zip(mesh.polygons, geometry.material_indices):
        polygon.material_index = material_index
        polygon.use_smooth = False
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    asset = bpy.data.objects.new(prefix, mesh)
    bpy.context.collection.objects.link(asset)
    asset["assetId"] = prefix
    asset["generator"] = "scripts/props_cafe_table.py:build_cafe_table"
    asset["seed"] = config["seed"]
    asset["provenance"] = "Original procedural vertices/materials; no external content"
    asset["constructionParts"] = json.dumps(geometry.parts)
    asset["constructionNotes"] = ("Four closed bevelled planks with real narrow joins; closed cast-metal "
                                  "assembly components intentionally overlap at structural joints.")
    asset["sourceAxes"] = "Blender Z-up / -Y-forward; symmetric table has no unique visual front"
    return asset
