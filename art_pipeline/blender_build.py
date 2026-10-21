"""Run only in a fresh headless Blender. All production geometry starts as vertices."""
import argparse
import json
import math
import platform
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from art_pipeline.config import load_config


class Geometry:
    def __init__(self):
        self.vertices, self.faces, self.materials = [], [], []

    def part(self, vertices, faces, material):
        offset = len(self.vertices)
        self.vertices.extend(vertices)
        self.faces.extend([tuple(v + offset for v in face) for face in faces])
        self.materials.extend([material] * len(faces))

    def box(self, center, size, material):
        x, y, z = center
        a, b, c = (v / 2 for v in size)
        vertices = [(x+dx*a, y+dy*b, z+dz*c) for dx, dy, dz in
                    [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                     (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.part(vertices, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], material)

    def rings(self, levels, sides, material, center=(0, 0), phase=0):
        vertices = [(center[0]+r*math.cos(phase+i*math.tau/sides),
                     center[1]+r*math.sin(phase+i*math.tau/sides), z)
                    for z, r in levels for i in range(sides)]
        faces = [tuple(reversed(range(sides))), tuple((len(levels)-1)*sides+i for i in range(sides))]
        for level in range(len(levels)-1):
            for i in range(sides):
                a, b = level*sides+i, level*sides+(i+1)%sides
                faces.append((a, b, b+sides, a+sides))
        self.part(vertices, faces, material)


def linear_color(hex_color):
    srgb = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in srgb) + (1,)


def make_material(name, spec):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = linear_color(spec["color"])
    shader.inputs["Roughness"].default_value = spec["roughness"]
    shader.inputs["Metallic"].default_value = spec["metallic"]
    material.diffuse_color = linear_color(spec["color"])
    return material


def streetlamp(config):
    """Flared base, tapered octagonal shaft, framed lantern, service plate and bolts."""
    rng = random.Random(config["seed"])
    geometry = Geometry()
    geometry.rings([(0,.24),(.025,.24),(.055,.215),(.11,.215),(.15,.17)], 8, 0, phase=math.pi/8)
    geometry.rings([(.14,.15),(.22,.145),(.30,.10),(2.32,.061),(2.38,.085)], 8, 0, phase=math.pi/8)
    geometry.rings([(.30,.106),(.325,.106),(.345,.09)], 8, 1, phase=math.pi/8)
    geometry.rings([(2.26,.078),(2.29,.09),(2.34,.09),(2.38,.12)], 8, 1, phase=math.pi/8)
    # Square lantern is closed geometry. Glass is deliberately opaque amber for distance readability.
    geometry.rings([(2.38,.19),(2.44,.24),(2.98,.31)], 4, 2, phase=math.pi/4)
    for xsign in (-1, 1):
        for ysign in (-1, 1):
            # Bars slope outward to follow the lantern frustum.
            z0, z1 = 2.42, 3.01
            p0 = Vector((xsign*.17, ysign*.17, z0))
            p1 = Vector((xsign*.225, ysign*.225, z1))
            direction = (p1-p0).normalized()
            side = direction.cross(Vector((0, 1, 0))).normalized()*.018
            other = direction.cross(side).normalized()*.018
            vertices = [tuple(p+s*side+t*other) for p in (p0,p1) for s,t in [(-1,-1),(1,-1),(1,1),(-1,1)]]
            geometry.part(vertices, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], 0)
    geometry.rings([(2.38,.27),(2.42,.285),(2.45,.26)], 4, 0, phase=math.pi/4)
    geometry.rings([(2.98,.36),(3.015,.36),(3.09,.285),(3.16,.065)], 4, 0, phase=math.pi/4)
    geometry.rings([(3.015,.363),(3.035,.34)], 4, 1, phase=math.pi/4)
    geometry.rings([(3.15,.037),(3.19,.037),(3.2,.022)], 8, 3)
    # Front is Blender -Y. This asymmetric plate establishes a visible forward direction.
    geometry.box((0,-.101,.59), (.088,.018,.19), 1)
    for x in (-.028,.028):
        for z in (.522,.658):
            # Tiny seeded fastener variation makes the seed a real geometry input.
            geometry.rings([(z-.008,.009),(z+.008,.009)], 6, 3,
                           center=(x,-.115), phase=rng.random()*math.tau)
    mesh = bpy.data.meshes.new(config["assetId"])
    mesh.from_pydata(geometry.vertices, [], geometry.faces)
    for name in ("metal", "edge", "glass", "fastener"):
        mesh.materials.append(make_material(name, config["palette"][name]))
    for polygon, index in zip(mesh.polygons, geometry.materials):
        polygon.material_index = index
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    # Explicit exported X,Y,Z dimensions map to Blender X,Z,-Y.
    target = (config["dimensionsMeters"][0], config["dimensionsMeters"][2], config["dimensionsMeters"][1])
    mins = [min(v.co[i] for v in mesh.vertices) for i in range(3)]
    maxs = [max(v.co[i] for v in mesh.vertices) for i in range(3)]
    for vertex in mesh.vertices:
        for i in range(3):
            origin = mins[i] if i == 2 else (mins[i]+maxs[i])/2
            vertex.co[i] = (vertex.co[i]-origin)*target[i]/(maxs[i]-mins[i])
    mesh.update()
    asset = bpy.data.objects.new(config["assetId"], mesh)
    bpy.context.collection.objects.link(asset)
    return asset


def validate_mesh(asset, budget):
    mesh = asset.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    issues = {
        "nonManifoldEdges": sum(not edge.is_manifold for edge in bm.edges),
        "looseVertices": sum(not vertex.link_faces for vertex in bm.verts),
        "degenerateFaces": sum(face.calc_area() <= 1e-12 for face in bm.faces),
        "nonFiniteVertices": sum(not all(math.isfinite(v) for v in vertex.co) for vertex in bm.verts),
    }
    faces = [tuple(sorted(v.index for v in face.verts)) for face in bm.faces]
    issues["duplicateFaces"] = len(faces)-len(set(faces))
    triangles = len(bm.faces)
    bm.free()
    if any(issues.values()) or not 0 < triangles <= budget:
        raise ValueError(f"Blender mesh validation failed: {issues}, triangles={triangles}, budget={budget}")
    if asset.location.length > 1e-8 or any(abs(v-1) > 1e-8 for v in asset.scale):
        raise ValueError("Asset transform must be applied at the bottom-center origin")
    return {**issues, "triangles": triangles, "vertices": len(mesh.vertices), "closedComponentsMayIntersect": True}


def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()


def previews(asset, config, output):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = config["preview"]["samples"]
    scene.cycles.seed = config["seed"]
    scene.cycles.use_denoising = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 1
    scene.render.resolution_x = scene.render.resolution_y = config["preview"]["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    world = bpy.data.worlds.new("benchmark_world")
    world.use_nodes = True
    background = next(node for node in world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs["Color"].default_value = (.32,.36,.40,1)
    background.inputs["Strength"].default_value = .45
    scene.world = world
    ground = bpy.data.meshes.new("preview_ground")
    ground.from_pydata([(-200,-200,-.005),(200,-200,-.005),(200,200,-.005),(-200,200,-.005)], [], [(0,1,2,3)])
    floor = bpy.data.objects.new("preview_ground", ground)
    scene.collection.objects.link(floor)
    floor.data.materials.append(make_material("preview_ground", {"color":"#D6D1C3", "roughness":.9,"metallic":0}))
    h = config["dimensionsMeters"][1]
    for name, position, energy, size, color in [
        ("key",(-3,-4,6),650,4,(1,.89,.74)),
        ("fill",(4,-1,4),350,5,(.75,.85,1)),
        ("rim",(1,4,5),500,3,(1,.95,.84))]:
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(name, data)
        scale = h/3.2
        light.location = tuple(value*scale for value in position)
        data.energy *= scale*scale
        data.size *= scale
        scene.collection.objects.link(light)
        aim(light, (0,0,h/2))
    camera_data = bpy.data.cameras.new("preview_camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = h*1.25
    camera = bpy.data.objects.new("preview_camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    target = (0,0,h*.49)
    for name, location in [("front", (0,-h*2.5,h*.49)),
                           ("isometric", (h*2,-h*2,target[2]+h*2))]:
        camera.location = location
        aim(camera, target)
        scene.render.filepath = str(output / (name+".png"))
        bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    config = load_config(args.config)
    actual_version = ".".join(map(str, bpy.app.version))
    if actual_version != config["blenderVersion"]:
        raise ValueError(f"Blender version mismatch: expected {config['blenderVersion']}, got {actual_version}")
    output = Path(args.output).resolve()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1
    asset = streetlamp(config)
    health = validate_mesh(asset, config["maxTriangles"])
    bpy.context.view_layer.objects.active = asset
    asset.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(output / (config["assetId"]+".glb")), export_format="GLB",
                              use_selection=True, export_yup=True, export_materials="EXPORT",
                              export_normals=True, export_extras=False)
    previews(asset, config, output)
    report = {"blender":actual_version, "blenderBuildHash":bpy.app.build_hash.decode(),
              "platform":platform.platform(), "python":sys.version.split()[0], "engine":"CYCLES", "device":"CPU",
              "meshHealth":health, "forwardProbe":{"sourceAxis":"-Y", "feature":"service plate on front of shaft"}}
    (output / "build_report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("ART_PIPELINE_BUILD_OK " + json.dumps(report))


if __name__ == "__main__":
    main()
