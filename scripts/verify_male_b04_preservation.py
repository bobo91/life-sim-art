"""Read-only preservation proof for the single frozen, visually rejected B04.

Reads two saved .blend files with embedded scripts disabled. Never saves a blend,
alters the frozen candidate, exports a GLB, or claims new Unity verification.
"""
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

CLIPS = ("idle", "walk", "run", "turn")


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def matrix(value):
    return [list(row) for row in value]


def simple(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bpy.types.ID):
        return {"idType": value.bl_rna.identifier, "name": value.name}
    try:
        return [simple(item) for item in value]
    except TypeError:
        return str(value)


def rna_values(value):
    """Canonical writable scalar/array parameters, without memory addresses."""
    result = {}
    for prop in value.bl_rna.properties:
        if prop.identifier in {"rna_type", "name", "name_full"} or prop.is_readonly:
            continue
        if prop.type in {"BOOLEAN", "INT", "FLOAT", "ENUM", "STRING"}:
            result[prop.identifier] = simple(getattr(value, prop.identifier))
    return result


def node_tree_snapshot(tree, image_names, seen=None):
    if not tree:
        return None
    seen = set() if seen is None else seen
    if tree.name in seen:
        return {"recursiveNodeTree": tree.name}
    seen.add(tree.name)
    nodes = []
    for node in sorted(tree.nodes, key=lambda item: item.name):
        row = {"name": node.name, "type": node.bl_idname, "parameters": rna_values(node)}
        row["inputs"] = [{"name": sock.name, "identifier": sock.identifier,
                          "default": simple(sock.default_value) if hasattr(sock, "default_value") else None}
                         for sock in node.inputs]
        row["outputs"] = [{"name": sock.name, "identifier": sock.identifier,
                           "default": simple(sock.default_value) if hasattr(sock, "default_value") else None}
                          for sock in node.outputs]
        if hasattr(node, "image") and node.image:
            image_names.add(node.image.name)
            row["image"] = node.image.name
        if hasattr(node, "node_tree") and node.node_tree:
            row["group"] = node_tree_snapshot(node.node_tree, image_names, seen.copy())
        nodes.append(row)
    links = sorted([link.from_node.name, link.from_socket.identifier,
                    link.to_node.name, link.to_socket.identifier] for link in tree.links)
    return {"name": tree.name, "nodes": nodes, "links": links}


def appearance_snapshot(mesh_objects):
    materials = {slot.material.name: slot.material for obj in mesh_objects
                 for slot in obj.material_slots if slot.material}
    image_names = set()
    rows = {name: {"parameters": rna_values(mat),
                   "nodeTree": node_tree_snapshot(mat.node_tree, image_names)}
            for name, mat in sorted(materials.items())}
    images = {}
    for name in sorted(image_names):
        image = bpy.data.images[name]
        packed = [hashlib.sha256(item.packed_file.data).hexdigest()
                  for item in image.packed_files]
        if not packed and image.packed_file:
            packed = [hashlib.sha256(image.packed_file.data).hexdigest()]
        row = {"source": image.source, "size": list(image.size),
               "channels": image.channels, "depth": image.depth,
               "alphaMode": image.alpha_mode, "colorSpace": image.colorspace_settings.name,
               "packedBytesSha256": packed, "filepath": image.filepath}
        if not packed:
            pixels = array("f", [0.0]) * len(image.pixels)
            image.pixels.foreach_get(pixels)
            row["pixelsFloat32Sha256"] = hashlib.sha256(pixels.tobytes()).hexdigest()
        images[name] = row
    return {"materials": rows, "images": images}


def mesh_snapshot(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    points = [tuple(vertex.co) for vertex in mesh.vertices]
    triangles = [{"vertices": list(tri.vertices), "loops": list(tri.loops),
                  "material": tri.material_index} for tri in mesh.loop_triangles]
    uvs = {layer.name: [tuple(uv.uv) for uv in layer.data] for layer in mesh.uv_layers}
    weights = [{obj.vertex_groups[item.group].name: item.weight for item in vertex.groups}
               for vertex in mesh.vertices]
    slots = [{"material": slot.material.name if slot.material else None, "link": slot.link}
             for slot in obj.material_slots]
    shape_keys = None if not mesh.shape_keys else {
        key.name: {"points": [tuple(vertex.co) for vertex in key.data],
                   "value": key.value, "relative": key.relative_key.name}
        for key in mesh.shape_keys.key_blocks}
    return {"dataName": mesh.name, "points": points,
            "edges": [list(edge.vertices) for edge in mesh.edges], "triangles": triangles,
            "polygons": [{"vertices": list(poly.vertices), "material": poly.material_index,
                          "smooth": poly.use_smooth} for poly in mesh.polygons],
            "loopVertexIndices": [loop.vertex_index for loop in mesh.loops],
            "uvs": uvs, "weights": weights, "vertexGroups": [group.name for group in obj.vertex_groups],
            "materialSlots": slots, "shapeKeys": shape_keys,
            "customNormals": mesh.has_custom_normals,
            "cornerNormals": [tuple(normal.vector) for normal in mesh.corner_normals],
            "modifiers": [{"name": mod.name, "type": mod.type, "parameters": rna_values(mod),
                           "object": mod.object.name if hasattr(mod, "object") and mod.object else None}
                          for mod in obj.modifiers]}


def action_snapshot(action):
    curves = []
    for curve in action.fcurves:
        keys = [{"co": list(key.co), "left": list(key.handle_left),
                 "right": list(key.handle_right), "parameters": rna_values(key)}
                for key in curve.keyframe_points]
        curves.append({"path": curve.data_path, "index": curve.array_index,
                       "group": curve.group.name if curve.group else None,
                       "parameters": rna_values(curve), "keys": keys,
                       "samples": [list(point.co) for point in curve.sampled_points],
                       "modifiers": [{"type": mod.type, "parameters": rna_values(mod)}
                                     for mod in curve.modifiers]})
    return {"frameRange": list(action.frame_range), "parameters": rna_values(action),
            "curves": curves}


def file_snapshot():
    objects = sorted((obj for obj in bpy.context.scene.objects
                      if obj.type == "MESH" and obj.name.startswith("M01_")), key=lambda obj: obj.name)
    rig = bpy.data.objects["A03_B01_Rig"]
    paths = {obj.name: {"type": obj.type, "data": obj.data.name if obj.data else None,
                        "parent": obj.parent.name if obj.parent else None,
                        "parentType": obj.parent_type, "parentBone": obj.parent_bone,
                        "matrixBasis": matrix(obj.matrix_basis),
                        "matrixParentInverse": matrix(obj.matrix_parent_inverse)}
             for obj in [bpy.data.objects["CHR_PlayerMale_A01"], rig] + objects}
    bones = {bone.name: {"parent": bone.parent.name if bone.parent else None,
                          "matrix": matrix(bone.matrix_local), "head": list(bone.head_local),
                          "tail": list(bone.tail_local), "parameters": rna_values(bone)}
             for bone in rig.data.bones}
    actions = {name: action_snapshot(bpy.data.actions[name]) for name in CLIPS}
    return {"meshes": {obj.name: mesh_snapshot(obj) for obj in objects},
            "objects": paths, "appearance": appearance_snapshot(objects), "bones": bones,
            "actions": actions, "actionNames": sorted(bpy.data.actions.keys()),
            "rigDataName": rig.data.name,
            "animation": {"drivers": len(rig.animation_data.drivers),
                          "nla": [{"name": track.name, "mute": track.mute,
                                   "strips": [{"name": strip.name,
                                               "action": strip.action.name if strip.action else None,
                                               "parameters": rna_values(strip)} for strip in track.strips]}
                                  for track in rig.animation_data.nla_tracks]},
            "embeddedTexts": len(bpy.data.texts)}


def feet_samples():
    """Same frame grid/contact definition as check_male_b02_contacts.py, full feet too."""
    rig = bpy.data.objects["A03_B01_Rig"]
    scene = bpy.context.scene
    feet = sorted((obj for obj in scene.objects if obj.type == "MESH"
                   and obj.name.startswith("M01_") and "shoes" in obj.name), key=lambda obj: obj.name)
    sole = bpy.data.objects["M01_shoes_bottom"]
    low_ids = {side: [vertex.index for vertex in sole.data.vertices if vertex.co.z < .004
                     and (vertex.co.x > 0 if side == "L" else vertex.co.x < 0)] for side in ("L", "R")}
    assert all(low_ids.values()) and len(feet) >= 2
    result = {}
    for fps in (24, 96):
        clips = {}
        for name in CLIPS:
            action = bpy.data.actions[name]
            rig.animation_data.action = action
            lo, hi = action.frame_range
            count = round((hi - lo) / 24 * fps)
            samples, rows = [], []
            for index in range(count + 1):
                frame = lo + (hi - lo) * index / count
                scene.frame_set(math.floor(frame), subframe=frame % 1)
                bpy.context.view_layer.update()
                graph = bpy.context.evaluated_depsgraph_get()
                frame_points, row = {}, {"time": index / fps}
                for obj in feet:
                    evaluated = obj.evaluated_get(graph)
                    mesh = evaluated.to_mesh()
                    points = [tuple(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices]
                    frame_points[obj.name] = points
                    if obj == sole:
                        for side, ids in low_ids.items():
                            selected = [points[vertex] for vertex in ids]
                            row[side] = {"center": [sum(point[axis] for point in selected) / len(selected)
                                                    for axis in range(3)],
                                         "minZ": min(point[2] for point in selected)}
                    evaluated.to_mesh_clear()
                samples.append(frame_points)
                rows.append(row)
            speeds = []
            for previous, current in zip(rows, rows[1:]):
                for side in low_ids:
                    if max(previous[side]["minZ"], current[side]["minZ"]) < .003:
                        velocity = [(current[side]["center"][axis] - previous[side]["center"][axis]) * fps
                                    for axis in range(3)]
                        speeds.append(math.hypot(velocity[0], velocity[1]))
            metrics = {"sampledFrames": len(rows), "fps": fps,
                       "groundMinimumMeters": min(row[side]["minZ"] for row in rows for side in low_ids),
                       "stanceSpeedMaxMps": max(speeds, default=0),
                       "lowSoleVertices": {side: len(ids) for side, ids in low_ids.items()}}
            clips[name] = {"samples": samples, "metrics": metrics}
        result[str(fps)] = clips
    return result


def boundary_snapshot(mesh):
    counts = {tuple(sorted(edge)): 0 for edge in mesh["edges"]}
    for poly in mesh["polygons"]:
        vertices = poly["vertices"]
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            counts[tuple(sorted((a, b)))] += 1
    return {"boundaryEdges": sorted(edge for edge, count in counts.items() if count == 1),
            "nonManifoldEdgeCount": sum(count > 2 for count in counts.values())}


def canonical_body(mesh):
    """Compare generated surface independent of inconsequential BMesh index order."""
    vertices = sorted((point, tuple(sorted(weights.items())))
                      for point, weights in zip(mesh["points"], mesh["weights"]))
    triangles = []
    for tri in mesh["triangles"]:
        corners = [(mesh["points"][vi], tuple((name, values[li]) for name, values in mesh["uvs"].items()))
                   for vi, li in zip(tri["vertices"], tri["loops"])]
        corners = min(corners[index:] + corners[:index] for index in range(3))
        triangles.append((tri["material"], corners))
    return {"weightedVertices": vertices, "orientedUvTriangles": sorted(triangles),
            "materialSlots": mesh["materialSlots"], "vertexGroups": mesh["vertexGroups"],
            "shapeKeys": mesh["shapeKeys"], "dataName": mesh["dataName"],
            "modifiers": mesh["modifiers"]}


def verify_replay(root, args, out):
    """Replay the exact same approved recipe in memory, without saving a model."""
    output = out / "replay.json"
    assert out.is_dir() and not output.exists(), "Preserve all previous outputs"
    topology = json.loads((root / args.topology_report).read_text(encoding="utf-8"))
    cfg = topology["config"]
    paths = {"B02": root / args.source, "B04": root / args.candidate,
             "A03high": root / cfg["highReference"]}
    hashes = {name: file_sha(path) for name, path in paths.items()}
    assert hashes["B02"] == topology["sourceSha256"]
    assert hashes["A03high"] == topology["highReferenceSha256"]
    bpy.context.preferences.use_preferences_save = False
    bpy.ops.wm.open_mainfile(filepath=str(paths["B04"]), load_ui=False, use_scripts=False)
    frozen = mesh_snapshot(bpy.data.objects["M01_body"])
    bpy.ops.wm.open_mainfile(filepath=str(paths["A03high"]), load_ui=False, use_scripts=False)
    high = [tuple(vertex.co) for vertex in bpy.data.objects["M01_body"].data.vertices]
    bpy.ops.wm.open_mainfile(filepath=str(paths["B02"]), load_ui=False, use_scripts=False)
    sys.path.insert(0, str(root / "scripts"))
    from male_b04_elbow_topology import recover
    replay_report = recover(bpy.data.objects["M01_body"], bpy.data.objects["A03_B01_Rig"], high, cfg)
    replay = mesh_snapshot(bpy.data.objects["M01_body"])
    raw_exact = frozen == replay
    geometric_exact = canonical_body(frozen) == canonical_body(replay)
    final_hashes = {name: file_sha(path) for name, path in paths.items()}
    result = {"schema": "male-b04-memory-replay-1", "status": "PASS" if geometric_exact and hashes == final_hashes else "FAIL",
              "sameRecipeSameConfigInMemoryOnly": True, "savedOrExported": False,
              "sourceHashesBefore": hashes, "sourceHashesAfter": final_hashes,
              "sourceFilesUnchanged": hashes == final_hashes,
              "rawMeshDataIncludingIndexOrderExactlyEqual": raw_exact,
              "canonicalCoordinatesWeightsOrientedTrianglesUvMaterialsExactlyEqual": geometric_exact,
              "frozenRawSha256": digest(frozen), "replayRawSha256": digest(replay),
              "frozenCanonicalSha256": digest(canonical_body(frozen)),
              "replayCanonicalSha256": digest(canonical_body(replay)),
              "verticesAdded": replay_report["verticesAdded"], "trianglesAdded": replay_report["trianglesAdded"],
              "uvInterpolationMaxError": replay_report["newLoopUvDiagnosticMaxDifference"],
              "generatorSha256": file_sha(root / "scripts/male_b04_elbow_topology.py"),
              "configSha256": file_sha(root / "configs/male-neutral-b04-elbow.json"),
              "limits": "Reproduction of the one frozen rejected candidate, not a new candidate or correction. Local visual defects remain NO-GO. In-memory read-only replay permits derived-data changes only in disposable Blender memory."}
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    assert result["status"] == "PASS", "Frozen candidate reproduction differs"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="build/male-neutral-b02/delivery-001/character_b02.blend")
    parser.add_argument("--candidate", default="build/male-neutral-b04/topology-001/candidate.blend")
    parser.add_argument("--topology-report", default="build/male-neutral-b04/topology-001/report.json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--replay-only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    root = Path.cwd()
    paths = {"B02": root / args.source, "B04": root / args.candidate}
    out = root / args.out
    if args.replay_only:
        verify_replay(root, args, out)
        return
    assert not out.exists(), "Preserve previous verification outputs"
    out.mkdir(parents=True)
    before_hashes = {name: file_sha(path) for name, path in paths.items()}
    topology = json.loads((root / args.topology_report).read_text(encoding="utf-8"))
    assert before_hashes["B02"] == topology["sourceSha256"]
    bpy.context.preferences.use_preferences_save = False
    snapshots, feet = {}, {}
    for name, path in paths.items():
        bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
        snapshots[name] = file_snapshot()
        feet[name] = feet_samples()
    source, candidate = snapshots["B02"], snapshots["B04"]
    failures = []

    def check(condition, message):
        if not condition:
            failures.append(message)
        return bool(condition)

    check(len(source["meshes"]) == len(candidate["meshes"]) == 10, "ten asset meshes")
    other_meshes = {}
    for name in source["meshes"]:
        if name == "M01_body":
            continue
        a, b = source["meshes"][name], candidate["meshes"][name]
        other_meshes[name] = {"vertices": len(a["points"]), "triangles": len(a["triangles"]),
                              "sourceSha256": digest(a), "candidateSha256": digest(b),
                              "exact": check(a == b, name + " raw mesh/UV/weights/materials/normals")}
    equalities = {key: check(source[key] == candidate[key], key + " changed")
                  for key in ("objects", "appearance", "bones", "actions", "actionNames",
                              "rigDataName", "animation", "embeddedTexts")}
    check(len(source["bones"]) == len(candidate["bones"]) == 58, "58 bones")
    body_a, body_b = source["meshes"]["M01_body"], candidate["meshes"]["M01_body"]
    for key in ("dataName", "vertexGroups", "materialSlots", "shapeKeys", "modifiers"):
        check(body_a[key] == body_b[key], "body " + key + " changed")
    check(body_b["shapeKeys"] is None, "rejected B03 morphs must be absent")
    mapping = {int(old): new for old, new in topology["oldVertexIndexMap"].items()}
    old_points = [Vector(point) for point in body_a["points"]]
    new_ids = sorted(set(range(len(body_b["points"]))) - set(mapping.values()))
    check(new_ids == topology["newVertexIds"], "new vertex IDs mismatch")
    old_position_errors = [(old_points[old] - Vector(body_b["points"][new])).length
                           for old, new in mapping.items()]
    old_exact = check(max(old_position_errors, default=0) == 0, "old neutral points moved")
    tree = BVHTree.FromPolygons(old_points, [tri["vertices"] for tri in body_a["triangles"]],
                                all_triangles=True)
    surface_errors = [tree.find_nearest(Vector(body_b["points"][index]))[3] for index in new_ids]
    max_surface = max(surface_errors, default=0)
    check(max_surface < .000002, "new neutral vertex exceeds 2micron surface tolerance")
    zones = {side: {"center": Vector(zone["center"]), "axis": Vector(zone["axis"])}
             for side, zone in topology["guide"].items()}
    cfg = topology["config"]

    def local(point, half_width):
        for zone in zones.values():
            delta = point - zone["center"]
            distance = delta.dot(zone["axis"])
            if abs(distance) < half_width and (delta - zone["axis"] * distance).length < cfg["radialLimitMeters"]:
                return True
        return False

    weight_changes = [old for old, new in mapping.items() if body_a["weights"][old] != body_b["weights"][new]]
    check(all(local(old_points[index], cfg["weightHalfWidthMeters"]) for index in weight_changes),
          "body weight change outside elbow band")
    check(all(local(Vector(body_b["points"][index]), cfg["localFaceHalfWidthMeters"]) for index in new_ids),
          "new vertex outside local elbow band")
    after_faces = {tuple(sorted(poly["vertices"])): poly for poly in body_b["polygons"]}
    outside_count = 0
    for poly in body_a["polygons"]:
        if any(local(old_points[index], cfg["localFaceHalfWidthMeters"]) for index in poly["vertices"]):
            continue
        key = tuple(sorted(mapping[index] for index in poly["vertices"]))
        match = after_faces.get(key)
        check(match is not None and match["material"] == poly["material"] and match["smooth"] == poly["smooth"],
              "outside elbow polygon changed")
        outside_count += 1
    boundaries_a, boundaries_b = boundary_snapshot(body_a), boundary_snapshot(body_b)
    check(boundaries_a == boundaries_b, "body boundary/nonmanifold edges changed")
    uv_errors = []
    for layer, values in body_b["uvs"].items():
        for poly in body_b["triangles"]:
            for index, loop in zip(poly["vertices"], poly["loops"]):
                point = Vector(body_b["points"][index])
                got = Vector((*values[loop], 0))
                options = []
                for near, _, tri_index, _ in tree.find_nearest_range(point, 1e-6):
                    tri = body_a["triangles"][tri_index]
                    if tri["material"] != poly["material"]:
                        continue
                    source_uvs = [Vector((*body_a["uvs"][layer][li], 0)) for li in tri["loops"]]
                    want = barycentric_transform(near, *[old_points[vi] for vi in tri["vertices"]], *source_uvs)
                    options.append((want - got).length)
                check(bool(options), "body loop has no source chart/material match")
                if options:
                    uv_errors.append(min(options))
    check(max(uv_errors, default=0) < 1e-5, "body UV interpolation error")
    foot_report = {}
    evaluated_vertex_samples = 0
    for fps in ("24", "96"):
        foot_report[fps] = {}
        for name in CLIPS:
            a, b = feet["B02"][fps][name], feet["B04"][fps][name]
            exact = check(a["samples"] == b["samples"], fps + "fps " + name + " evaluated foot mesh changed")
            max_error = max((math.dist(pa, pb) for fa, fb in zip(a["samples"], b["samples"])
                             for mesh in fa for pa, pb in zip(fa[mesh], fb[mesh])), default=0)
            evaluated_vertex_samples += sum(len(points) for sample in a["samples"] for points in sample.values())
            foot_report[fps][name] = {"source": a["metrics"], "candidate": b["metrics"],
                                      "allEvaluatedWorldVerticesExactlyEqual": exact,
                                      "maxPositionErrorMeters": max_error,
                                      "sourceSampleSha256": digest(a["samples"]),
                                      "candidateSampleSha256": digest(b["samples"])}
    after_hashes = {name: file_sha(path) for name, path in paths.items()}
    check(before_hashes == after_hashes, "source/candidate files changed on disk")
    action_report = {name: {"fcurves": len(source["actions"][name]["curves"]),
                            "keyframes": sum(len(curve["keys"]) for curve in source["actions"][name]["curves"]),
                            "frameRange": source["actions"][name]["frameRange"],
                            "sourceSha256": digest(source["actions"][name]),
                            "candidateSha256": digest(candidate["actions"][name])} for name in CLIPS}
    result = {"schema": "male-b04-readonly-preservation-1", "status": "PASS" if not failures else "FAIL",
              "visualDecision": "NO-GO; separate mandatory visual gate failed; no export authorized",
              "blenderVersion": bpy.app.version_string, "sourceHashesBefore": before_hashes,
              "sourceHashesAfter": after_hashes, "sourceFilesUnchanged": before_hashes == after_hashes,
              "candidateReopened": True, "noBlendSaveGLBExportOrUnityRun": True,
              "equalities": equalities, "otherNineMeshes": other_meshes,
              "appearance": {"sourceSha256": digest(source["appearance"]),
                             "candidateSha256": digest(candidate["appearance"]),
                             "materialNames": sorted(source["appearance"]["materials"]),
                             "images": source["appearance"]["images"]},
              "skeleton": {"bones": len(source["bones"]), "names": list(source["bones"]),
                           "sourceSha256": digest(source["bones"]), "candidateSha256": digest(candidate["bones"])},
              "objectPaths": source["objects"], "actions": action_report,
              "body": {"objectName": "M01_body", "dataName": body_b["dataName"],
                       "verticesBefore": len(body_a["points"]), "verticesAfter": len(body_b["points"]),
                       "verticesAdded": len(new_ids), "trianglesBefore": len(body_a["triangles"]),
                       "trianglesAfter": len(body_b["triangles"]),
                       "trianglesAdded": len(body_b["triangles"]) - len(body_a["triangles"]),
                       "originalNeutralVerticesExact": old_exact,
                       "maxOriginalNeutralPositionErrorMeters": max(old_position_errors, default=0),
                       "maxNewVertexSourceSurfaceErrorMeters": max_surface,
                       "oldVerticesWithChangedWeights": len(weight_changes),
                       "changedOldWeightsOnlyWithinHalfWidthMeters": cfg["weightHalfWidthMeters"],
                       "newVerticesOnlyWithinHalfWidthMeters": cfg["localFaceHalfWidthMeters"],
                       "radialLimitMeters": cfg["radialLimitMeters"],
                       "outsideLocalFacesPreserved": outside_count,
                       "boundaryEdgesBefore": len(boundaries_a["boundaryEdges"]),
                       "boundaryEdgesAfter": len(boundaries_b["boundaryEdges"]),
                       "nonManifoldEdgesBefore": boundaries_a["nonManifoldEdgeCount"],
                       "nonManifoldEdgesAfter": boundaries_b["nonManifoldEdgeCount"],
                       "uvCornersChecked": len(uv_errors), "maxUvInterpolationError": max(uv_errors, default=0),
                       "bodyNeutralNormalsNotRequiredIdentical": "Retriangulation changes local interpolation; visual gate found visible ridges."},
              "feet": foot_report, "evaluatedFootVertexSamplesPerSource": evaluated_vertex_samples,
              "method": "Saved B02 and frozen B04 independently reopened with embedded scripts disabled; canonical raw data equality; all source body vertices mapped; new corners barycentrically checked against all valid source UV charts within1micron; full shoe mesh world positions sampled on B02contact24/96fps grids.",
              "limitations": ["Technical preservation only; does not overturn visual NO-GO.",
                              "Foot equality retains B02 behavior and its known contact limits; not new Unity or game-world verification.",
                              "New vertex neutral surface tolerance2microns; unchanged original neutral coordinates required exactly.",
                              "Visual deformation quality, transitions and integration are not certified by raw data equality."],
              "failures": failures}
    (out / "report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "otherMeshesExact": all(row["exact"] for row in other_meshes.values()),
                      "equalities": equalities, "body": result["body"],
                      "evaluatedFootVertexSamplesPerSource": evaluated_vertex_samples,
                      "sourceFilesUnchanged": result["sourceFilesUnchanged"], "failures": failures}, indent=2), flush=True)
    assert not failures, "Read-only preservation check failed: " + "; ".join(failures)


if __name__ == "__main__":
    main()
