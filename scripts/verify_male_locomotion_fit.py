"""Focused B02-preservation and actual saved GLB roundtrip for locomotion fit.

Reads saved files with autoexec disabled. No model/weight/rig edit or export.
Meshes/materials/rest skeleton/idle are locked; only walk/run authoring may differ.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Quaternion
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_male_b04_preservation as preserved

CLIPS = ("idle", "walk", "run")
SOURCE_SHA = "8300f581fa4e5a7f012d70ae9aadd0d7ca9eb99214b5a8699a1f65f0a9c8e96c"


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glb_read(path):
    raw = path.read_bytes()
    assert raw[:4] == b"glTF"
    count = struct.unpack_from("<I", raw, 12)[0]
    data = json.loads(raw[20:20 + count])
    start = 20 + count
    assert raw[start + 4:start + 8] == b"BIN\x00"
    binary = raw[start + 8:]
    formats = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
               5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
    widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

    def accessor(index):
        info = data["accessors"][index]
        assert "sparse" not in info
        view = data["bufferViews"][info["bufferView"]]
        code, size = formats[info["componentType"]]
        width = widths[info["type"]]
        stride = view.get("byteStride", size * width)
        offset = view.get("byteOffset", 0) + info.get("byteOffset", 0)
        return [struct.unpack_from("<" + code * width, binary, offset + i * stride)
                for i in range(info["count"])]

    meshes = {}
    for mesh in data["meshes"]:
        primitives = []
        for primitive in mesh["primitives"]:
            primitives.append({"mode": primitive.get("mode", 4),
                               "material": data["materials"][primitive["material"]]["name"],
                               "attributes": {name: accessor(index) for name, index
                                              in sorted(primitive["attributes"].items())},
                               "indices": accessor(primitive["indices"])})
        meshes[mesh["name"]] = primitives
    image_hashes = {}
    for index, image in enumerate(data.get("images", [])):
        view = data["bufferViews"][image["bufferView"]]
        offset = view.get("byteOffset", 0)
        image_hashes[image.get("name", str(index))] = hashlib.sha256(
            binary[offset:offset + view["byteLength"]]).hexdigest()
    joint_indices = data["skins"][0]["joints"]
    joint_names = [data["nodes"][index]["name"] for index in joint_indices]
    clips = {}
    for animation in data.get("animations", []):
        channels = {}
        for channel in animation["channels"]:
            sampler = animation["samplers"][channel["sampler"]]
            target = channel["target"]
            node = data["nodes"][target["node"]]["name"]
            channels[(node, target["path"])] = {
                "times": accessor(sampler["input"]), "values": accessor(sampler["output"]),
                "interpolation": sampler.get("interpolation", "LINEAR")}
        duration = max(time[0] for channel in channels.values() for time in channel["times"])
        endpoint_error = []
        for (_, prop), channel in channels.items():
            first, last = channel["values"][0], channel["values"][-1]
            error = max(abs(a - b) for a, b in zip(first, last))
            if prop == "rotation":
                error = min(error, max(abs(a + b) for a, b in zip(first, last)))
            endpoint_error.append(error)
        clips[animation["name"]] = {"channels": channels, "duration": duration,
                                     "maxEndpointComponentError": max(endpoint_error)}
    inverse_bind = accessor(data["skins"][0]["inverseBindMatrices"])
    material_hash = preserved.digest(data.get("materials", []))
    return {"json": data, "meshes": meshes, "images": image_hashes,
            "jointNames": joint_names, "inverseBind": inverse_bind,
            "materialsSha256": material_hash, "clips": clips}


def points():
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    result = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or not obj.name.startswith("M01_"):
            continue
        evaluated = obj.evaluated_get(graph)
        mesh = evaluated.to_mesh()
        result.extend(evaluated.matrix_world @ vertex.co for vertex in mesh.vertices)
        evaluated.to_mesh_clear()
    assert result and all(math.isfinite(component) for point in result for component in point)
    return result


def nearest_error(a, b):
    tree = KDTree(len(b))
    for index, point in enumerate(b):
        tree.insert(point, index)
    tree.balance()
    return max(tree.find(point)[2] for point in a)


def idle_glb_error(before, after):
    """Same motion despite a different exporter's key segmentation, sampled96Hz."""
    if before["channels"].keys() != after["channels"].keys():
        return None

    def value_at(channel, seconds, rotation):
        times, values = channel["times"], channel["values"]
        index = next((i for i, time in enumerate(times) if time[0] >= seconds), len(times) - 1)
        if index == 0 or times[index][0] <= seconds:
            return values[index]
        previous = index - 1
        if channel["interpolation"] == "STEP":
            return values[previous]
        blend = (seconds - times[previous][0]) / (times[index][0] - times[previous][0])
        assert channel["interpolation"] == "LINEAR"
        if rotation:
            a, b = values[previous], values[index]
            # glTF xyzw -> mathutils wxyz, shortest-path normalized slerp.
            q = Quaternion((a[3], a[0], a[1], a[2])).slerp(
                Quaternion((b[3], b[0], b[1], b[2])), blend)
            return (q.x, q.y, q.z, q.w)
        return tuple(a + (b - a) * blend for a, b in zip(values[previous], values[index]))

    duration = before["duration"]
    errors = []
    for key in before["channels"]:
        for step in range(round(duration * 96) + 1):
            time = min(duration, step / 96)
            a = value_at(before["channels"][key], time, key[1] == "rotation")
            b = value_at(after["channels"][key], time, key[1] == "rotation")
            error = max(abs(x - y) for x, y in zip(a, b))
            if key[1] == "rotation":
                error = min(error, max(abs(x + y) for x, y in zip(a, b)))
            errors.append(error)
    return max(errors, default=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="build/male-neutral-b02/delivery-001/character_b02.blend")
    parser.add_argument("--baseline-glb", default="build/male-neutral-b02/delivery-001/chr_player_male_poc_001.glb")
    parser.add_argument("--input", required=True)
    parser.add_argument("--blend", default="character_locomotion_fit.blend")
    parser.add_argument("--glb", default="chr_player_male_poc_001.glb")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    root = Path.cwd()
    directory, out = root / args.input, root / args.out
    assert not out.exists(), "Use a fresh verification output"
    out.mkdir(parents=True)
    files = {"source": root / args.source, "candidate": directory / args.blend,
             "baselineGlb": root / args.baseline_glb, "candidateGlb": directory / args.glb}
    before_hashes = {name: file_sha(path) for name, path in files.items()}
    assert before_hashes["source"] == SOURCE_SHA
    preserved.CLIPS = CLIPS
    bpy.context.preferences.use_preferences_save = False
    snapshots = {}
    for name in ("source", "candidate"):
        bpy.ops.wm.open_mainfile(filepath=str(files[name]), load_ui=False, use_scripts=False)
        snapshots[name] = preserved.file_snapshot()
        snapshots[name]["fps"] = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    a, b = snapshots["source"], snapshots["candidate"]
    mesh_rows = {name: {"vertices": len(mesh["points"]), "triangles": len(mesh["triangles"]),
                        "sourceSha256": preserved.digest(mesh),
                        "candidateSha256": preserved.digest(b["meshes"][name]),
                        "exact": mesh == b["meshes"][name]}
                 for name, mesh in a["meshes"].items()}
    equalities = {"allTenMeshesGeometryUvWeightsNormalsMaterialsModifiers": a["meshes"] == b["meshes"],
                  "appearance": a["appearance"] == b["appearance"],
                  "rest58Bones": a["bones"] == b["bones"],
                  "objectDataNamesHierarchyTransforms": a["objects"] == b["objects"],
                  "idleAction": a["actions"]["idle"] == b["actions"]["idle"],
                  "idleSeconds": (a["actions"]["idle"]["frameRange"][1] - a["actions"]["idle"]["frameRange"][0]) / a["fps"] == (b["actions"]["idle"]["frameRange"][1] - b["actions"]["idle"]["frameRange"][0]) / b["fps"],
                  "embeddedTextsAbsent": b["embeddedTexts"] == 0,
                  "sameBoneCount58": len(a["bones"]) == len(b["bones"]) == 58,
                  "sameTriangles29367": sum(row["triangles"] for row in mesh_rows.values()) == 29367}
    base_glb, new_glb = glb_read(files["baselineGlb"]), glb_read(files["candidateGlb"])
    idle_error = idle_glb_error(base_glb["clips"]["idle"], new_glb["clips"]["idle"])
    glb_equalities = {"geometrySkinUvsNormalsIndices": base_glb["meshes"] == new_glb["meshes"],
                      "jointOrderNames": base_glb["jointNames"] == new_glb["jointNames"],
                      "inverseBindMatrices": base_glb["inverseBind"] == new_glb["inverseBind"],
                      "materialJson": base_glb["materialsSha256"] == new_glb["materialsSha256"],
                      "embeddedImageBytes": base_glb["images"] == new_glb["images"],
                      "idle96HzSamplesWithin1e_6TRSComponents": idle_error is not None and idle_error < 1e-6,
                      "idleDurationSeconds": base_glb["clips"]["idle"]["duration"] == new_glb["clips"]["idle"]["duration"],
                      "onlyIdleWalkRunNoTurn": set(new_glb["clips"]) == set(CLIPS)}
    clip_rows = {}
    for name in CLIPS:
        clip = new_glb["clips"][name]
        full_trs = all((joint, prop) in clip["channels"] for joint in new_glb["jointNames"]
                       for prop in ("translation", "rotation", "scale"))
        clip_rows[name] = {"durationSeconds": clip["duration"], "channels": len(clip["channels"]),
                           "all58JointsHaveTRS": full_trs,
                           "allSixSupportsHaveTRS": all((joint, prop) in clip["channels"]
                               for joint in new_glb["jointNames"] if joint.startswith("B02_")
                               for prop in ("translation", "rotation", "scale")),
                           "maxEndpointComponentError": clip["maxEndpointComponentError"],
                           "loopEndpointsMatchWithin1e_6": clip["maxEndpointComponentError"] < 1e-6,
                           "animatedNonJointNodes": sorted({joint for joint, _ in clip["channels"]
                                                            if joint not in new_glb["jointNames"]})}
    # Actual fresh Blender import; source evaluated points and imported skin are separate data.
    reference, ranges = {}, {}
    rig = bpy.data.objects["A03_B01_Rig"]
    sample_phases = [i / 8 for i in range(9)]
    for name in CLIPS:
        action = bpy.data.actions[name]
        rig.animation_data.action = action
        low, high = action.frame_range
        ranges[name] = [float(low), float(high)]
        reference[name] = []
        for phase in sample_phases:
            frame = low + (high - low) * phase
            bpy.context.scene.frame_set(math.floor(frame), subframe=frame % 1)
            reference[name].append(points())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(files["candidateGlb"]))
    rig = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    roundtrip = {}
    for name in CLIPS:
        action = next(action for action in bpy.data.actions if action.name.lower().startswith(name))
        rig.animation_data_create()
        rig.animation_data.action = action
        if hasattr(action, "slots") and action.slots:
            rig.animation_data.action_slot = action.slots[0]
        low, high = action.frame_range
        errors = []
        for phase, expected in zip(sample_phases, reference[name]):
            frame = low + (high - low) * phase
            bpy.context.scene.frame_set(math.floor(frame), subframe=frame % 1)
            actual = points()
            errors.append(max(nearest_error(actual, expected), nearest_error(expected, actual)))
        roundtrip[name] = {"phases": sample_phases, "maxPointcloudErrorMeters": max(errors),
                           "pointcloudErrorsMeters": errors, "sourceFrames": ranges[name],
                           "importedFrames": [float(low), float(high)],
                           "passes1mmSampledSkinTolerance": max(errors) < .001}
        rig.animation_data.action = None
    after_hashes = {name: file_sha(path) for name, path in files.items()}
    passed = (all(equalities.values()) and all(glb_equalities.values()) and
              all(row["all58JointsHaveTRS"] and row["loopEndpointsMatchWithin1e_6"]
                  and not row["animatedNonJointNodes"] for row in clip_rows.values()) and
              all(row["passes1mmSampledSkinTolerance"] for row in roundtrip.values()) and
              len(rig.data.bones) == 58 and before_hashes == after_hashes)
    report = {"schema": "a03-locomotion-fit-preservation-roundtrip-1", "status": "PASS" if passed else "FAIL",
              "blenderVersion": bpy.app.version_string, "sourceHashesBefore": before_hashes,
              "sourceHashesAfter": after_hashes, "filesUnchanged": before_hashes == after_hashes,
              "savedBlendPreservation": equalities, "meshes": mesh_rows,
              "glbBaselinePreservation": glb_equalities,
              "idleGlb96HzMaxTrsComponentError": idle_error, "clips": clip_rows,
              "freshImportedBones": len(rig.data.bones), "roundtrip": roundtrip,
              "method": "Canonical saved B02/candidate data equality; raw GLB accessor/skin/material/image checks; fresh Blender glTF import, bidirectional evaluated vertex-cloud comparison at9phases per clip.",
              "limitations": ["Technical data/skin checks only; does not certify gait quality or foot sliding, transitions or Unity behaviour.",
                              "1mm maximum sampled imported skin tolerance; not continuous-time or exhaustive self-intersection proof.",
                              "No authored mesh, weight, rig or animation modification and no model save/export by verifier."]}
    (out / "report.json").write_bytes((json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps(report, indent=2), flush=True)
    assert passed, "Locomotion preservation/roundtrip check failed; inspect report"


if __name__ == "__main__":
    main()
