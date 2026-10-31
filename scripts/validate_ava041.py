"""Read-only source and static GLB validation for ART-041's visual candidate.

Run with Blender --background --factory-startup --offline-mode
--disable-autoexec --python-exit-code 1 --python scripts/validate_ava041.py --
--blend <candidate.blend> --glb <candidate.glb> --out <fresh-report.json>.

Opening a source and importing an export are separate checks. Neither repairs or
saves the model. Open garment boundaries and intersecting closed construction
parts are reported, not interpreted as proof of visible gaps or solid contact.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import traceback

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from art_pipeline.validation import _read_glb, validate_glb

ASSET_ID = "chr_ava_morgan_041"
ROOT_NAME = "CHR_AvaMorgan_041"
TRIANGLE_CAP = 29367  # Actual approved A03 cost, not an invented performance claim.
MATERIAL_CAP = 9
BOUND_EPSILON = 1e-4
DEGENERATE_AREA_M2 = 1e-14


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_check(report, stage, name, condition, actual, expected):
    report["checks"].append({"stage": stage, "name": name,
        "status": "pass" if condition else "fail", "actual": actual,
        "expected": expected})


def bounding(points):
    if not points or any(not math.isfinite(x) for p in points for x in p):
        return None
    return {"min": [min(p[k] for p in points) for k in range(3)],
            "max": [max(p[k] for p in points) for k in range(3)]}


def bound_error(first, second):
    if not first or not second:
        return None
    return max(abs(a - b) for key in ("min", "max")
               for a, b in zip(first[key], second[key]))


def mesh_record(obj, report, stage):
    mesh = obj.data
    mesh.calc_loop_triangles()
    points = [tuple(obj.matrix_world @ v.co) for v in mesh.vertices]
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
    used = {i for p in mesh.polygons for i in p.vertices}
    edge_uses = Counter()
    face_keys = Counter()
    for polygon in mesh.polygons:
        indices = list(polygon.vertices)
        face_keys[tuple(sorted(indices))] += 1
        for a, b in zip(indices, indices[1:] + indices[:1]):
            edge_uses[tuple(sorted((a, b)))] += 1
    areas = []
    for tri in mesh.loop_triangles:
        a, b, c = [obj.matrix_world @ mesh.vertices[i].co for i in tri.vertices]
        areas.append((b-a).cross(c-a).length * 0.5)
    normals = [tuple(v.normal) for v in mesh.vertices]
    normals += [tuple(n.vector) for n in mesh.corner_normals]
    finite_points = all(math.isfinite(x) for p in points for x in p)
    finite_normals = all(math.isfinite(x) for n in normals for x in n)
    zero_normals = sum(sum(x*x for x in n) < 1e-16 for n in normals)
    degenerate = sum(not math.isfinite(area) or area <= DEGENERATE_AREA_M2
                     for area in areas)
    uses = [edge_uses.get(tuple(sorted(e.vertices)), 0) for e in mesh.edges]
    loose = len(mesh.vertices) - len(used)
    duplicate_faces = sum(count-1 for count in face_keys.values() if count > 1)
    h = hashlib.sha256()
    for p in points:
        h.update(struct.pack("<3f", *p))
    for t in triangles:
        h.update(struct.pack("<3I", *t))
    record = {"name": obj.name, "meshDataName": mesh.name,
        "vertices": len(points), "triangles": len(triangles),
        "boundsWorldBlenderXYZ": bounding(points),
        "geometrySha256": h.hexdigest(), "finiteVertices": finite_points,
        "finiteNormals": finite_normals, "zeroLengthNormals": zero_normals,
        "degenerateTriangles": degenerate,
        "minimumTriangleAreaM2": min((area for area in areas if math.isfinite(area)), default=None),
        "degenerateAreaThresholdM2": DEGENERATE_AREA_M2,
        "looseVertices": loose, "wireEdges": sum(n == 0 for n in uses),
        "boundaryEdges": sum(n == 1 for n in uses),
        "nonManifoldJunctionEdges": sum(n > 2 for n in uses),
        "duplicateIndexedFaces": duplicate_faces,
        "materials": [m.name if m else None for m in mesh.materials],
        "modifiers": [{"name": m.name, "type": m.type} for m in obj.modifiers],
        "shapeKeys": len(mesh.shape_keys.key_blocks) if mesh.shape_keys else 0}
    add_check(report, stage, obj.name + ": nonempty finite mesh",
              bool(points and triangles) and finite_points and finite_normals,
              {"vertices": len(points), "triangles": len(triangles),
               "finiteVertices": finite_points, "finiteNormals": finite_normals},
              "nonempty; finite coordinates and normals")
    add_check(report, stage, obj.name + ": surface integrity",
              degenerate == loose == duplicate_faces == record["wireEdges"]
              == record["nonManifoldJunctionEdges"] == zero_normals == 0,
              {key: record[key] for key in ("degenerateTriangles", "looseVertices",
               "wireEdges", "nonManifoldJunctionEdges", "duplicateIndexedFaces",
               "zeroLengthNormals")}, "all zero")
    add_check(report, stage, obj.name + ": material assignments",
              bool(mesh.materials) and all(mesh.materials), record["materials"],
              "at least one material, no empty slots")
    if record["boundaryEdges"]:
        report["diagnostics"].append({"stage": stage, "mesh": obj.name,
            "boundaryEdges": record["boundaryEdges"],
            "classification": "review: open part/garment boundaries; inspect renders",
            "note": "Counts alone do not establish a visible gap, internal hole, contact or clipping."})
    return record, points


def has_animation(owner):
    animation = getattr(owner, "animation_data", None)
    return bool(animation and (animation.action or animation.nla_tracks
                               or animation.drivers))


def descendant_of(obj, root):
    parent, seen = obj.parent, set()
    while parent and parent not in seen:
        if parent == root:
            return True
        seen.add(parent)
        parent = parent.parent
    return False


def snapshot(objects, report, stage):
    records, points = [], []
    for obj in sorted(objects, key=lambda obj: obj.name):
        record, coordinates = mesh_record(obj, report, stage)
        records.append(record)
        points.extend(coordinates)
    materials = {m for obj in objects for m in obj.data.materials if m}
    images = {node.image for mat in materials if mat.use_nodes
              for node in mat.node_tree.nodes
              if node.type == "TEX_IMAGE" and node.image}
    triangle_count = sum(item["triangles"] for item in records)
    animation_owners = [owner.name for owner in
        list(bpy.data.objects) + list(bpy.data.shape_keys) + list(bpy.data.materials)
        if has_animation(owner)]
    counts = {"armatures": len(bpy.data.armatures), "actions": len(bpy.data.actions),
              "embeddedTexts": len(bpy.data.texts),
              "animationOwners": animation_owners}
    add_check(report, stage, "static scene with no executable texts",
              not any((counts["armatures"], counts["actions"], counts["embeddedTexts"],
                       animation_owners)), counts, "zero armatures/actions/texts/animation")
    add_check(report, stage, "A03-relative triangle/material budget",
              0 < triangle_count <= TRIANGLE_CAP and 0 < len(materials) <= MATERIAL_CAP,
              {"triangles": triangle_count, "materials": len(materials)},
              {"maxTriangles": TRIANGLE_CAP, "maxMaterials": MATERIAL_CAP})
    image_records = [{"name": im.name, "size": list(im.size),
                      "colorspace": im.colorspace_settings.name,
                      "packed": bool(im.packed_file)}
                     for im in sorted(images, key=lambda im: im.name)]
    add_check(report, stage, "texture size limit",
              len(images) <= 2 and all(0 < max(im.size) <= 1024 for im in images),
              image_records, "zero textures or at most two <=1024px images")
    box = bounding(points)
    return {"meshes": records, "meshCount": len(records),
        "triangles": triangle_count, "materialCount": len(materials),
        "materialNames": sorted(m.name for m in materials), "images": image_records,
        "boundsWorldBlenderXYZ": box,
        "dimensionsBlenderXYZ": [b-a for a,b in zip(box["min"], box["max"])] if box else None,
        "sceneCounts": counts}


def run(args, report):
    blend, glb = Path(args.blend).resolve(), Path(args.glb).resolve()
    original_hashes = {"blend": digest(blend), "glb": digest(glb)}
    report["inputs"] = {"blend": {"name": blend.name, "sha256": original_hashes["blend"]},
                        "glb": {"name": glb.name, "sha256": original_hashes["glb"]}}
    bpy.context.preferences.use_preferences_save = False
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False, use_scripts=False)
    root = bpy.data.objects.get(ROOT_NAME)
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"
               and (obj.get("asset_id") == ASSET_ID
                    or (root and descendant_of(obj, root)))]
    add_check(report, "source", "named asset root and mesh selection",
              root is not None and bool(objects),
              {"rootFound": root is not None, "selectedMeshes": len(objects)},
              ROOT_NAME + " with descendant or asset_id-tagged meshes")
    if not objects:
        raise ValueError("No Ava meshes found; refusing to validate presentation geometry")
    if root:
        root_identity_error = max(abs(root.matrix_world[row][col] - (1 if row == col else 0))
                                  for row in range(4) for col in range(4))
        add_check(report, "source", "identity asset root", root_identity_error < 1e-6,
                  root_identity_error, "world matrix identity within 1e-6")
    report["source"] = snapshot(objects, report, "source")
    source_box = report["source"]["boundsWorldBlenderXYZ"]
    gltf_expected_dimensions = [report["source"]["dimensionsBlenderXYZ"][k]
                               for k in (0, 2, 1)]
    raw, document, binary = _read_glb(glb)
    report["glbStructure"] = {"bytes": len(raw), "jsonMeshes": len(document.get("meshes", [])),
        "nodes": len(document.get("nodes", [])), "skins": len(document.get("skins", [])),
        "animations": len(document.get("animations", [])),
        "images": len(document.get("images", [])),
        "materials": len(document.get("materials", [])),
        "extensionsUsed": document.get("extensionsUsed", []),
        "extensionsRequired": document.get("extensionsRequired", [])}
    add_check(report, "glb", "static export only",
              not document.get("skins") and not document.get("animations")
              and not any("skin" in node for node in document.get("nodes", []))
              and not any(p.get("targets") for mesh in document.get("meshes", [])
                          for p in mesh.get("primitives", [])),
              report["glbStructure"], "no skins, animations or morph targets")
    try:
        report["independentGlb"] = validate_glb(glb, gltf_expected_dimensions,
            TRIANGLE_CAP, report["source"]["materialNames"])
        add_check(report, "glb", "independent binary geometry validation", True,
                  {"triangles": report["independentGlb"]["triangles"],
                   "pivotErrorMeters": report["independentGlb"]["pivotErrorMeters"]},
                  "finite dense accessors, valid indices, normals/winding, bounds and bottom-center pivot")
    except Exception as exc:
        report["independentGlb"] = {"error": str(exc)}
        add_check(report, "glb", "independent binary geometry validation", False,
                  str(exc), "valid static GLB matching source dimensions/materials")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.use_preferences_save = False
    bpy.ops.import_scene.gltf(filepath=str(glb))
    imported = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    report["reimport"] = snapshot(imported, report, "reimport")
    difference = bound_error(source_box, report["reimport"]["boundsWorldBlenderXYZ"])
    add_check(report, "roundtrip", "source/export/reimport bounds",
              difference is not None and difference <= BOUND_EPSILON,
              difference, {"maxAbsoluteErrorMeters": BOUND_EPSILON})
    add_check(report, "roundtrip", "triangle and material counts",
              report["source"]["triangles"] == report["reimport"]["triangles"]
              and report["source"]["materialCount"] == report["reimport"]["materialCount"],
              {stage: {key: report[stage][key] for key in ("triangles", "materialCount")}
               for stage in ("source", "reimport")}, "same counts; mesh splitting at material boundaries allowed")
    add_check(report, "preservation", "source files unchanged",
              original_hashes == {"blend": digest(blend), "glb": digest(glb)},
              {"blend": digest(blend), "glb": digest(glb)}, original_hashes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blend", required=True)
    parser.add_argument("--glb", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    output = Path(args.out).resolve()
    if output.exists():
        raise FileExistsError("Fresh report path required: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"schema": "ava-art041-static-validation-1", "assetId": ASSET_ID,
        "blender": bpy.app.version_string, "background": bpy.app.background,
        "onlineAccess": bpy.app.online_access, "checks": [], "diagnostics": [],
        "scope": "Saved source reopen, independent GLB binary checks and fresh Blender reimport; no source repair/save/render.",
        "limitations": ["No exhaustive self-intersection, solid contact or visible-gap proof.",
            "Boundary edges require visual/context review; closed components may intentionally overlap.",
            "Axes are checked by source/export bounds and exporter convention; semantic front needs renders.",
            "No Unity import, gameplay, rig, deformation or performance certification."]}
    try:
        run(args, report)
    except Exception as exc:
        report["fatalError"] = {"type": type(exc).__name__, "message": str(exc),
                                "traceback": traceback.format_exc()}
    report["passed"] = sum(check["status"] == "pass" for check in report["checks"])
    report["failed"] = sum(check["status"] == "fail" for check in report["checks"])
    report["status"] = "pass" if not report["failed"] and "fatalError" not in report else "fail"
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "passed": report["passed"],
                      "failed": report["failed"], "report": str(output)}, sort_keys=True))
    if report["status"] != "pass":
        raise RuntimeError("ART-041 validation failed; inspect " + str(output))


if __name__ == "__main__":
    main()
