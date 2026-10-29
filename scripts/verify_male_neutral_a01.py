"""Independently reopen the one approved static male PoC and roundtrip its GLB.

Blender invocation: --background --factory-startup --disable-autoexec --python
this_file.py -- --blend character.blend --glb character.glb --expected
asset-report.json --out fresh-verification.json

The saved sources are never repaired, saved or rendered by this script. Boundary
edges are measured rather than treated as a blanket failure: separate garments,
eyes and body parts can intentionally have open edges. No rig/animation, complete
intersection coverage or visual approval is inferred from a passing result.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct
import sys
import time

import bpy


ASSET_ID = "chr_player_male_poc_001"
POSITION_EPSILON = 1e-5
BOUNDS_EPSILON = 1e-4
DEGENERATE_AREA = 1e-14


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(report, stage, name, condition, actual, expected):
    report["checks"].append({"stage": stage, "name": name,
        "status": "pass" if condition else "fail", "actual": actual, "expected": expected})


def bounds(points):
    finite = [point for point in points if all(math.isfinite(x) for x in point)]
    if not finite:
        return {"min": None, "max": None}
    return {"min": [min(p[i] for p in finite) for i in range(3)],
            "max": [max(p[i] for p in finite) for i in range(3)]}


def dimensions(box):
    return [b - a for a, b in zip(box["min"], box["max"])] if box["min"] else None


def bounds_error(first, second):
    try:
        values = [abs(float(a) - float(b)) for key in ("min", "max")
                  for a, b in zip(first[key], second[key])]
        return max(values) if len(values) == 6 and all(math.isfinite(v) for v in values) else None
    except (KeyError, TypeError, ValueError):
        return None


def active_drivers(owner):
    if owner is None:
        return []
    animation = getattr(owner, "animation_data", None)
    if not animation:
        return []
    return [{"owner": owner.name, "path": curve.data_path,
             "index": curve.array_index, "muted": bool(curve.mute),
             "driverValid": bool(curve.driver.is_valid)}
            for curve in animation.drivers if not curve.mute]


def snapshot(obj, report, stage):
    mesh = obj.data
    mesh.calc_loop_triangles()
    points = [tuple(obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    nonfinite = sum(not all(math.isfinite(x) for x in p) for p in points)
    digest = hashlib.sha256()
    for point in points:
        digest.update(struct.pack("<3f", *point))
    for triangle in triangles:
        digest.update(struct.pack("<3I", *triangle))
    edge_faces = Counter()
    for polygon in mesh.polygons:
        indices = list(polygon.vertices)
        for a, b in zip(indices, indices[1:] + indices[:1]):
            edge_faces[tuple(sorted((a, b)))] += 1
    areas = []
    for triangle in triangles:
        a, b, c = [points[i] for i in triangle]
        u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        cross = (u[1]*v[2] - u[2]*v[1], u[2]*v[0] - u[0]*v[2], u[0]*v[1] - u[1]*v[0])
        areas.append(0.5 * math.sqrt(sum(x*x for x in cross)))
    vertex_normals = [tuple(vertex.normal) for vertex in mesh.vertices]
    corner_normals = [tuple(normal.vector) for normal in mesh.corner_normals]
    bad_normals = sum(not all(math.isfinite(x) for x in normal)
                      for normal in vertex_normals + corner_normals)
    degenerate = sum(not math.isfinite(a) or a < DEGENERATE_AREA for a in areas)
    edge_uses = [edge_faces.get(tuple(sorted(edge.vertices)), 0) for edge in mesh.edges]
    record = {"name": obj.name, "vertices": len(points), "triangles": len(triangles),
        "boundsWorld": bounds(points), "geometrySha256": digest.hexdigest(),
        "nonfiniteVertices": nonfinite, "nonfiniteNormals": bad_normals,
        "zeroLengthVertexNormals": sum(sum(x*x for x in n) < 1e-20 for n in vertex_normals),
        "zeroLengthCornerNormals": sum(sum(x*x for x in n) < 1e-20 for n in corner_normals),
        "degenerateTriangles": degenerate, "degenerateAreaThresholdM2": DEGENERATE_AREA,
        "minimumTriangleAreaM2": min((a for a in areas if math.isfinite(a)), default=None),
        "boundaryEdges": sum(count == 1 for count in edge_uses),
        "nonManifoldEdgesExcludingBoundaries": sum(count > 2 for count in edge_uses),
        "wireEdges": sum(count == 0 for count in edge_uses),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "modifiers": [{"name": m.name, "type": m.type,
                       "viewport": bool(m.show_viewport), "render": bool(m.show_render)} for m in obj.modifiers]}
    check(report, stage, obj.name + ": surface geometry", bool(points and triangles),
          {"vertices": len(points), "triangles": len(triangles)}, "nonempty surface")
    check(report, stage, obj.name + ": finite coordinates and normals",
          not nonfinite and not bad_normals, {"vertices": nonfinite, "normals": bad_normals}, 0)
    check(report, stage, obj.name + ": nondegenerate triangles", degenerate == 0, degenerate, 0)
    check(report, stage, obj.name + ": manifold edge junctions",
          record["nonManifoldEdgesExcludingBoundaries"] == 0,
          record["nonManifoldEdgesExcludingBoundaries"], 0)
    if record["boundaryEdges"] or record["wireEdges"] or record["zeroLengthVertexNormals"]:
        report["diagnostics"].append({"stage": stage, "mesh": obj.name,
            "boundaryEdges": record["boundaryEdges"], "wireEdges": record["wireEdges"],
            "zeroLengthVertexNormals": record["zeroLengthVertexNormals"],
            "note": "Open part boundaries are not an automatic failure; counts do not certify visible seams or anatomical contacts."})
    return {"report": record, "points": points}


def material_checks(objects, report, stage):
    for obj in objects:
        slots = [slot.material for slot in obj.material_slots]
        check(report, stage, obj.name + ": material assignments", bool(slots) and all(slots),
              [material.name if material else None for material in slots], "at least one assigned material; no empty slots")
    materials = {slot.material for obj in objects for slot in obj.material_slots if slot.material}
    records = []
    for material in sorted(materials, key=lambda m: m.name):
        nodes = list(material.node_tree.nodes) if material.use_nodes else []
        pbr = [node for node in nodes if node.type == "BSDF_PRINCIPLED"]
        outputs = [node for node in nodes if node.type == "OUTPUT_MATERIAL" and node.is_active_output]
        check(report, stage, material.name + ": PBR surface", bool(pbr and outputs)
              and any(n.inputs["Surface"].is_linked for n in outputs),
              {"principled": len(pbr), "activeOutputs": len(outputs)}, "Principled surface linked to active material output")
        values = []
        for node in pbr:
            for name in ("Base Color", "Roughness", "Metallic", "Alpha"):
                value = node.inputs[name].default_value
                values.extend([float(value)] if isinstance(value, (float, int)) else list(value))
        check(report, stage, material.name + ": finite PBR values", all(math.isfinite(v) for v in values),
              {"scalarComponents": len(values)}, "all finite")
        textures, pending, seen = [], [material.node_tree] if material.use_nodes else [], set()
        while pending:
            tree = pending.pop()
            if tree.as_pointer() in seen:
                continue
            seen.add(tree.as_pointer())
            for node in tree.nodes:
                if node.type == "GROUP" and node.node_tree:
                    pending.append(node.node_tree)
                if node.type != "TEX_IMAGE":
                    continue
                image = node.image
                if image is None:
                    check(report, stage, material.name + ": image assigned " + node.name, False, None, "image datablock")
                    continue
                packed = bool(image.packed_file) or bool(getattr(image, "packed_files", []))
                filepaths = []
                if image.source in {"FILE", "TILED", "MOVIE", "SEQUENCE"} and not packed:
                    path = bpy.path.abspath(image.filepath, library=image.library)
                    filepaths = [path.replace("<UDIM>", str(tile.number)) for tile in image.tiles] if image.source == "TILED" else [path]
                missing = [path for path in filepaths if not Path(path).is_file()]
                check(report, stage, material.name + ": texture " + image.name,
                      not missing and (packed or bool(filepaths) or image.source == "GENERATED"),
                      {"packed": packed, "missingFiles": missing, "source": image.source}, "packed/generated image or existing files")
                textures.append({"image": image.name, "source": image.source, "packed": packed,
                    "dimensionsPixels": list(image.size), "colorspace": image.colorspace_settings.name,
                    "filepaths": filepaths, "missingFiles": missing})
        records.append({"name": material.name, "textures": textures})
    return records


def point_cloud_comparison(source, target):
    """Allow UV/normal seam duplicates, never hide a displaced or omitted point.

    Adjacent-bin fallback accepts coordinates within 1e-5 per component when
    float32 roundtrip moves a value across a quantization boundary. It does not
    increase the stated spatial tolerance.
    """
    def grouped(points):
        result = defaultdict(set)
        for point in points:
            result[tuple(round(v / POSITION_EPSILON) for v in point)].add(point)
        return result
    first, second = grouped(source), grouped(target)
    same_keys = first.keys() == second.keys()
    directions = []
    for origin, destination in ((first, second), (second, first)):
        missing, examples = 0, []
        for key in origin.keys() - destination.keys():
            candidates = [point for offset in itertools.product((-1, 0, 1), repeat=3)
                          for point in destination.get(tuple(a+b for a, b in zip(key, offset)), ())]
            for point in origin[key]:
                matched = any(max(abs(a-b) for a, b in zip(point, other)) <= POSITION_EPSILON for other in candidates)
                if not matched:
                    missing += 1
                    if len(examples) < 8:
                        examples.append(list(point))
        directions.append({"unmatchedPoints": missing, "examples": examples})
    return {"positionEpsilonMetersPerComponent": POSITION_EPSILON,
        "sourceUniqueQuantizedPositions": len(first), "importedUniqueQuantizedPositions": len(second),
        "quantizedCoordinateSetsEqual": same_keys,
        "neighborBinFallbackUsed": not same_keys,
        "sourceToImported": directions[0], "importedToSource": directions[1],
        "equivalentWithinTolerance": all(d["unmatchedPoints"] == 0 for d in directions)}


def run(args, report):
    blend, glb, expected_path = [Path(p).resolve(strict=True) for p in (args.blend, args.glb, args.expected)]
    expected = json.loads(expected_path.read_text(encoding="utf-8-sig"))
    expected_meshes = {m["name"]: m for m in expected["meshes"]}
    if not expected_meshes or len(expected_meshes) != len(expected["meshes"]):
        raise ValueError("Expected mesh names must be nonempty and unique")
    report["inputs"] = {"blend": str(blend), "blendSha256": sha256(blend),
        "glb": str(glb), "glbSha256": sha256(glb), "expected": str(expected_path), "expectedSha256": sha256(expected_path)}
    bpy.context.preferences.use_preferences_save = False
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False, use_scripts=False)
    stage = "savedBlendReopen"
    tagged = [obj for obj in bpy.context.scene.objects if obj.get("wc_asset_id") == ASSET_ID]
    asset_nodes = set(tagged) | {obj for obj in bpy.context.scene.objects if obj.name.startswith("M01_")}
    pending = list(asset_nodes)
    while pending:
        for child in pending.pop().children:
            if child not in asset_nodes:
                asset_nodes.add(child)
                pending.append(child)
    objects = sorted([obj for obj in asset_nodes if obj.type == "MESH"], key=lambda obj: obj.name)
    check(report, stage, "asset mesh names", {obj.name for obj in objects} == expected_meshes.keys(),
          sorted(obj.name for obj in objects), sorted(expected_meshes))
    check(report, stage, "stable asset tags", bool(objects) and all(obj.get("wc_asset_id") == ASSET_ID for obj in objects),
          {obj.name: obj.get("wc_asset_id") for obj in objects}, ASSET_ID)
    armatures = sorted(obj.name for obj in bpy.data.objects if obj.type == "ARMATURE")
    check(report, stage, "no rig objects or armature datablocks", not armatures and not len(bpy.data.armatures),
          {"objects": armatures, "datablocks": len(bpy.data.armatures)}, 0)
    texts = [{"name": t.name, "autoRun": bool(t.use_module)} for t in bpy.data.texts]
    scripts = [t for t in texts if t["autoRun"] or t["name"].lower().endswith(".py")
               or any(word in t["name"].lower() for word in ("cloudrig", "post_generation"))]
    check(report, stage, "no embedded rig or autorun scripts", not scripts, scripts, [])
    report["embeddedTextBlocks"] = texts
    drivers = []
    for obj in asset_nodes:
        owners = [obj, getattr(obj, "data", None)]
        if obj.type == "MESH" and obj.data.shape_keys:
            owners.append(obj.data.shape_keys)
        for slot in getattr(obj, "material_slots", ()):
            if slot.material:
                owners.extend([slot.material, slot.material.node_tree] if slot.material.use_nodes else [slot.material])
        for owner in owners:
            drivers.extend(active_drivers(owner))
    check(report, stage, "no active asset drivers", not drivers, drivers, [])
    check(report, stage, "no armature modifiers on asset", not any(m.type == "ARMATURE" for o in objects for m in o.modifiers),
          [o.name for o in objects if any(m.type == "ARMATURE" for m in o.modifiers)], [])
    report["autoExecution"] = {"openMainfileUseScripts": False,
        "preferenceAutoExecutionEnabled": bool(bpy.context.preferences.filepaths.use_scripts_auto_execute)}
    saved = {obj.name: snapshot(obj, report, stage) for obj in objects}
    for name, value in saved.items():
        if name not in expected_meshes:
            continue
        item, exp = value["report"], expected_meshes[name]
        for field in ("vertices", "triangles", "geometrySha256"):
            check(report, stage, name + ": exact " + field, item[field] == exp[field], item[field], exp[field])
        error = bounds_error(item["boundsWorld"], exp["boundsWorld"])
        check(report, stage, name + ": expected AABB", error is not None and error <= BOUNDS_EPSILON,
              error, {"maximumErrorMeters": BOUNDS_EPSILON})
    report["savedMeshes"] = [v["report"] for v in saved.values()]
    report["savedMaterials"] = material_checks(objects, report, stage)
    saved_bounds = bounds([p for value in saved.values() for p in value["points"]])
    report["savedGlobalBoundsWorld"] = saved_bounds
    report["savedGlobalDimensionsMeters"] = dimensions(saved_bounds)
    expected_dimensions = expected.get("dimensionsMeters")
    if not isinstance(expected_dimensions, list) or len(expected_dimensions) != 3:
        raise ValueError("Expected dimensionsMeters must contain three components")
    actual_dimensions = report["savedGlobalDimensionsMeters"]
    dimension_error = max(abs(a - float(b)) for a, b in zip(actual_dimensions, expected_dimensions)) if actual_dimensions else None
    check(report, stage, "expected global dimensionsMeters",
          dimension_error is not None and math.isfinite(dimension_error) and dimension_error <= BOUNDS_EPSILON,
          {"dimensionsMeters": actual_dimensions, "maximumErrorMeters": dimension_error}, expected_dimensions)
    expected_bounds = {"min": [min(m["boundsWorld"]["min"][i] for m in expected_meshes.values()) for i in range(3)],
                       "max": [max(m["boundsWorld"]["max"][i] for m in expected_meshes.values()) for i in range(3)]}
    error = bounds_error(saved_bounds, expected_bounds)
    check(report, stage, "expected global AABB", error is not None and error <= BOUNDS_EPSILON, error, BOUNDS_EPSILON)
    # A factory-clean import prevents matching against leftover source objects.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.use_preferences_save = False
    bpy.context.preferences.filepaths.use_scripts_auto_execute = False
    bpy.ops.import_scene.gltf(filepath=str(glb))
    stage = "actualGlbReimport"
    imported_objects = sorted([obj for obj in bpy.context.scene.objects if obj.type == "MESH"], key=lambda obj: obj.name)
    check(report, stage, "exact imported mesh names (no extras or omissions)",
          {obj.name for obj in imported_objects} == expected_meshes.keys(),
          {"names": [obj.name for obj in imported_objects],
           "extras": sorted({o.name for o in imported_objects} - expected_meshes.keys()),
           "missing": sorted(expected_meshes.keys() - {o.name for o in imported_objects})}, sorted(expected_meshes))
    check(report, stage, "static import contains no armatures", not len(bpy.data.armatures), len(bpy.data.armatures), 0)
    imported = {obj.name: snapshot(obj, report, stage) for obj in imported_objects}
    comparisons = []
    for name, value in imported.items():
        if name not in saved or name not in expected_meshes:
            continue
        item, original = value["report"], saved[name]["report"]
        check(report, stage, name + ": triangle count", item["triangles"] == original["triangles"], item["triangles"], original["triangles"])
        error = bounds_error(item["boundsWorld"], original["boundsWorld"])
        check(report, stage, name + ": world AABB", error is not None and error <= BOUNDS_EPSILON, error, BOUNDS_EPSILON)
        if item["nonfiniteVertices"] or original["nonfiniteVertices"]:
            continue
        cloud = point_cloud_comparison(saved[name]["points"], value["points"])
        check(report, stage, name + ": bidirectional point cloud", cloud["equivalentWithinTolerance"], cloud, "same positions within stated epsilon; UV/normal seam duplication allowed")
        comparisons.append({"name": name, "sourceVertices": original["vertices"],
            "importedVertices": item["vertices"], "vertexCountEqualityRequired": False, **cloud})
    report["importedMeshes"] = [v["report"] for v in imported.values()]
    report["importedMaterials"] = material_checks(imported_objects, report, stage)
    report["roundtripPointClouds"] = comparisons
    imported_bounds = bounds([p for value in imported.values() for p in value["points"]])
    report["importedGlobalBoundsWorld"] = imported_bounds
    report["importedGlobalDimensionsMeters"] = dimensions(imported_bounds)
    error = bounds_error(imported_bounds, saved_bounds)
    check(report, stage, "global world AABB", error is not None and error <= BOUNDS_EPSILON, error, BOUNDS_EPSILON)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("blend", "glb", "expected", "out"):
        parser.add_argument("--" + name, required=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    out = Path(args.out).resolve()
    if out.exists():
        raise FileExistsError("Preserve the prior report; choose a fresh --out: " + str(out))
    if out in {Path(value).resolve() for value in (args.blend, args.glb, args.expected)}:
        raise ValueError("Report path must not replace a source or expected file")
    started = time.monotonic()
    report = {"schema": "male-neutral-a01-static-validation-v1", "assetId": ASSET_ID,
        "blender": bpy.app.version_string, "startedUtc": datetime.now(timezone.utc).isoformat(),
        "checks": [], "diagnostics": [], "pass": False,
        "notVerified": ["visual quality/identity", "complete self-intersection or anatomical contact coverage",
            "rigging/animation", "Unity import/runtime", "UV, tangent and rendered material equivalence"]}
    try:
        run(args, report)
        report["pass"] = bool(report["checks"]) and all(c["status"] == "pass" for c in report["checks"])
    except Exception as exc:
        report["fatalError"] = {"type": type(exc).__name__, "message": str(exc)}
    report["durationSeconds"] = time.monotonic() - started
    report["finishedUtc"] = datetime.now(timezone.utc).isoformat()
    report["passedChecks"] = sum(c["status"] == "pass" for c in report["checks"])
    report["failedChecks"] = sum(c["status"] == "fail" for c in report["checks"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "passedChecks": report["passedChecks"],
        "failedChecks": report["failedChecks"], "fatalError": report.get("fatalError"), "report": str(out)}))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
