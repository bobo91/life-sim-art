"""Bounded B02-only gait fit: contact-speed authored run4 and lower-stick walk.

No mesh, weight, material, rest-skeleton or elbow correction. Idle remains exact.
New keys are baked at96Hz in the scene's original24fps timebase. The exporter
uses direct linear Fcurves so fractional-frame keys survive without retiming idle.
"""
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "scripts"))
from male_b02_joint_weights import update_support_matrices


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_bytes((json.dumps(value, indent=2) + "\n").encode())


def normalize_clip_times(path, rate):
    """Direct glTF export retains positive Blender frame1. Remove that padding.

    Change only animation-input seconds, never TRS values/mesh/skins. All authored
    keys lie on the declared96Hz lattice (including preserved24Hz idle).
    """
    raw = path.read_bytes()
    count = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+count])
    binary = bytearray(raw[20+count+8:])
    inputs = {s['input'] for a in doc['animations'] for s in a['samplers']}
    for index in inputs:
        acc = doc['accessors'][index]
        view = doc['bufferViews'][acc['bufferView']]
        assert acc['componentType'] == 5126 and acc['type'] == 'SCALAR'
        start = view.get('byteOffset', 0)+acc.get('byteOffset', 0)
        stride = view.get('byteStride', 4)
        values = [struct.unpack_from('<f', binary, start+i*stride)[0] for i in range(acc['count'])]
        assert abs(values[0]-1/24) < 1e-6
        shifted = [round((v-values[0])*rate)/rate for v in values]
        for i, value in enumerate(shifted):
            struct.pack_into('<f', binary, start+i*stride, value)
        acc['min'], acc['max'] = [min(shifted)], [max(shifted)]
    text = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode()
    text += b' '*((-len(text)) % 4)
    payload = struct.pack('<I4s', len(text), b'JSON')+text+struct.pack('<I4s', len(binary), b'BIN\x00')+binary
    path.write_bytes(struct.pack('<4sII', b'glTF', 2, 12+len(payload))+payload)


def smooth(t):
    t = max(0., min(1., t))
    return t*t*t*(10+t*(-15+6*t))


def hermite(a, b, va, vb, t):
    return (2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*va+(-2*t**3+3*t*t)*b+(t**3-t*t)*vb


def set_pose(rig, matrices, names):
    for name in names:
        rig.pose.bones[name].matrix = matrices[name]
        bpy.context.view_layer.update()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/male-locomotion-fit-v1.json")
    p.add_argument("--out", required=True)
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    out = ROOT / a.out
    assert not out.exists(), "Preserve previous results"
    out.mkdir(parents=True)
    cfg = json.loads((ROOT/a.config).read_text(encoding="utf-8"))
    source = ROOT/cfg["source"]
    source_hash = sha(source)
    assert source_hash == cfg["sourceSha256"]
    bpy.context.preferences.use_preferences_save = False
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    sc = bpy.context.scene
    assert sc.render.fps == cfg["sceneFps"] == 24
    rig = bpy.data.objects["A03_B01_Rig"]
    root = bpy.data.objects["CHR_PlayerMale_A01"]
    asset = [o for o in sc.objects if o.type == "MESH" and o.name.startswith("M01_")]
    rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    order = list(rest)
    major = [n for n in order if not n.startswith("B02_")]
    assert len(order) == 58 and len(asset) == 10
    baseline = json.loads((source.parent/"asset-report.json").read_text(encoding="utf-8"))
    supports = baseline["supportJoints"]
    old = {n: bpy.data.actions[n] for n in ("idle", "walk", "run", "turn")}
    before = {o.name: [len(o.data.vertices), sum(len(p.vertices)-2 for p in o.data.polygons)] for o in asset}
    sole = bpy.data.objects["M01_shoes_bottom"]
    bindsole = {s: [v.co.copy() for v in sole.data.vertices if v.co.z < .004 and (v.co.x > 0 if s == "L" else v.co.x < 0)] for s in ("L", "R")}
    assert all(len(x) == 188 for x in bindsole.values())
    base_poses = {}
    for name in ("walk", "run"):
        rig.animation_data.action = old[name]
        lo, hi = old[name].frame_range
        count = round(cfg[name]["durationSeconds"]*cfg["bakeFps"])
        rows = []
        for i in range(count+1):
            u = i/count if i < count else 0.
            frame = lo+(hi-lo)*u
            sc.frame_set(int(frame), subframe=frame % 1)
            bpy.context.view_layer.update()
            rows.append({n: rig.pose.bones[n].matrix.copy() for n in major})
        base_poses[name] = rows
    rig.animation_data.action = None

    def stance_target(side, phase, c):
        ankle0 = rest["Foot."+side].translation.copy()
        duty = c["stanceFraction"]
        pitch = (math.radians(c["heelStrikePitchDegrees"])*(1-smooth(phase/.22)) if phase < .22 else
                 math.radians(c["toeOffPitchDegrees"])*smooth((phase-.62)/.38) if phase > .62 else 0.)
        rot = Matrix.Rotation(pitch, 4, "X")
        pivot = (max(bindsole[side], key=lambda p: p.y) if pitch < 0 else min(bindsole[side], key=lambda p: p.y))
        target = ankle0+Vector((0, c["strikeOffsetYMeters"]+c["designSpeedMps"]*c["durationSeconds"]*duty*phase, 0))
        # Roll about the heel/toe while the corresponding contact anchor is
        # translated backward at exactly controller speed in this in-place clip.
        target += (pivot-ankle0)-rot.to_3x3()@(pivot-ankle0)
        target.z = cfg["groundClearanceMeters"]-min((rot.to_3x3()@(p-ankle0)).z for p in bindsole[side])
        return target, pitch

    def foot_target(side, ph, c):
        duty = c["stanceFraction"]
        if ph <= duty:
            return (*stance_target(side, ph/duty, c), True)
        t = (ph-duty)/(1-duty)
        start, a0 = stance_target(side, 1., c)
        end, a1 = stance_target(side, 0., c)
        sec = c["durationSeconds"]*(1-duty)
        target = start.lerp(end, smooth(t))
        target.y = hermite(start.y, end.y, c["designSpeedMps"]*sec, c["designSpeedMps"]*sec, t)
        target.z = start.z+(end.z-start.z)*smooth(t)+c["swingLiftMeters"]*math.sin(math.pi*t)**2
        return target, a0+(a1-a0)*smooth(t), False

    reach = {n: [] for n in ("walk", "run")}
    targets = {n: [] for n in ("walk", "run")}
    poses = {}
    reach_problems = []
    for name in ("walk", "run"):
        c = cfg[name]
        count = len(base_poses[name])-1
        frames = []
        for i, inherited in enumerate(base_poses[name]):
            u = i/count if i < count else 0.
            phase = 2*math.pi*u
            oldhips = inherited["Hips"]
            desired = Matrix.Rotation(math.radians(c["forwardLeanDegrees"]), 4, "X")@rest["Hips"].to_3x3().to_4x4()
            desired.translation = rest["Hips"].translation+Vector((.004*math.sin(phase), 0, -c["pelvisLowerMeters"]-c["pelvisBobMeters"]*math.cos(4*math.pi*(u-c["stanceFraction"]/2))))
            change = desired@oldhips.inverted()
            mats = {n: change@m for n, m in inherited.items()}
            row = {"normalizedTime": u}
            for side, sign in (("L", 1), ("R", -1)):
                ph = (u+(0 if side == "L" else .5)) % 1
                # Counter-swing to the corresponding forward landing foot.
                n = "UpperArm."+side
                parent = "Shoulder."+side
                m = mats[parent]@rest[parent].inverted()@rest[n]
                swing = math.radians(c["armSwingDegrees"])*math.cos(2*math.pi*ph)
                rot = Matrix.Rotation(swing, 4, "X")@Matrix.Rotation(sign*math.radians(76), 4, "Y")@m.to_3x3().to_4x4()
                rot.translation = m.translation
                mats[n] = rot
                n = "LowerArm."+side
                m = mats["UpperArm."+side]@rest["UpperArm."+side].inverted()@rest[n]
                rot = Matrix.Rotation(-math.radians(c["armBendDegrees"]), 4, "X")@m.to_3x3().to_4x4()
                rot.translation = m.translation
                mats[n] = rot
                for n in major:
                    if n == "Hand."+side or any(b.name == "Hand."+side for b in rig.data.bones[n].parent_recursive):
                        pbone = rig.data.bones[n].parent.name
                        mats[n] = mats[pbone]@rest[pbone].inverted()@rest[n]
                        if n != "Hand."+side:
                            mats[n] = mats[n]@Matrix.Rotation(math.radians(8 if n.startswith("Thumb") else 15), 4, "X")
                upper, lower, foot, toe = [x+"."+side for x in ("UpperLeg", "LowerLeg", "Foot", "Toes")]
                hip = (mats["Hips"]@rest["Hips"].inverted()@rest[upper]).translation
                ankle, pitch, contact = foot_target(side, ph, c)
                l1 = (rest[lower].translation-rest[upper].translation).length
                l2 = (rest[foot].translation-rest[lower].translation).length
                delta = ankle-hip
                distance = delta.length
                reach[name].append(distance/(l1+l2))
                if not abs(l1-l2)+1e-6 < distance < l1+l2-1e-6:
                    reach_problems.append({"clip":name,"side":side,"phase":u,"distance":distance,"legLength":l1+l2,"hip":list(hip),"ankle":list(ankle)})
                direction = delta.normalized()
                along = (l1*l1-l2*l2+distance*distance)/(2*distance)
                height = math.sqrt(max(0, l1*l1-along*along))
                forward = Vector((0, -1, 0))
                perp = (forward-direction*direction.dot(forward)).normalized()
                knee = hip+direction*along+perp*height
                for n, start, end, restend in ((upper, hip, knee, rest[lower].translation), (lower, knee, ankle, rest[foot].translation)):
                    q = (restend-rest[n].translation).rotation_difference(end-start)
                    m = q.to_matrix().to_4x4()@rest[n].to_3x3().to_4x4()
                    m.translation = start
                    mats[n] = m
                m = Matrix.Rotation(pitch, 4, "X")@rest[foot].to_3x3().to_4x4()
                m.translation = ankle
                mats[foot] = m
                mats[toe] = m@rest[foot].inverted()@rest[toe]
                row[side] = {"phase": ph, "contact": contact, "ankle": list(ankle), "pitchDegrees": math.degrees(pitch)}
            update_support_matrices(mats, rest, supports)
            frames.append((1+i*cfg["sceneFps"]/cfg["bakeFps"], mats))
            targets[name].append(row)
        poses[name] = frames
    if reach_problems:
        dump(out/"reach-preflight.json", {"exported":False,"saved":False,"problems":reach_problems,"maxReachFraction":{n:max(v) for n,v in reach.items()}})
        raise RuntimeError("Unreachable preflight; no model saved/exported: "+json.dumps(max(reach_problems,key=lambda x:x['distance'])))
    # Remove only replaced demonstration clips, retaining exact idle curves.
    for track in list(rig.animation_data.nla_tracks):
        rig.animation_data.nla_tracks.remove(track)
    for name in ("walk", "run", "turn"):
        bpy.data.actions.remove(old[name])
    actions = {"idle": old["idle"]}
    for name, frames in poses.items():
        ac = bpy.data.actions.new(name)
        rig.animation_data.action = ac
        previous = {}
        for frame, mats in frames:
            sc.frame_set(int(frame), subframe=frame % 1)
            set_pose(rig, mats, order)
            for n in order:
                pb = rig.pose.bones[n]
                pb.rotation_mode = "QUATERNION"
                if n in previous and pb.rotation_quaternion.dot(previous[n]) < 0:
                    pb.rotation_quaternion.negate()
                previous[n] = pb.rotation_quaternion.copy()
                for prop in ("location", "rotation_quaternion", "scale"):
                    pb.keyframe_insert(data_path=prop, frame=frame, group=n)
        for fc in ac.fcurves:
            for key in fc.keyframe_points:
                key.interpolation = "LINEAR"
        ac.use_fake_user = True
        actions[name] = ac
    rig.animation_data.action = None
    for ac in actions.values():
        track = rig.animation_data.nla_tracks.new()
        track.name = ac.name
        strip = track.strips.new(ac.name, 1, ac)
        strip.action_frame_start, strip.action_frame_end = ac.frame_range
        track.mute = True
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    sc.frame_set(1)
    bpy.context.view_layer.update()
    assert before == {o.name: [len(o.data.vertices), sum(len(p.vertices)-2 for p in o.data.polygons)] for o in asset}
    root["phase"] = cfg["version"]
    root["motionNote"] = "idle exact B02; walk1.4/run4mps at1x; no old turn; no root motion"
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    rig.select_set(True)
    for o in asset:
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=str(out/"chr_player_male_poc_001.glb"), export_format="GLB", use_selection=True, export_extras=True, export_animations=True, export_animation_mode="ACTIONS", export_anim_slide_to_zero=True, export_nla_strips=True, export_force_sampling=False, export_frame_range=False, export_skins=True, export_def_bones=False, export_morph=False, export_cameras=False, export_lights=False, export_influence_nb=4)
    normalize_clip_times(out/"chr_player_male_poc_001.glb", cfg["bakeFps"])
    rig.animation_data.action = actions["idle"]
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"character_locomotion_fit.blend"))
    report = {"assetId": "chr_player_male_poc_001", "version": cfg["version"], "sourceBlendSha256": source_hash, "blenderVersion": bpy.app.version_string, "triangles": sum(x[1] for x in before.values()), "meshCount": 10, "materialCount": 9, "bones": 58, "supportJoints": supports, "sceneFps": 24, "newGaitBakeFps": cfg["bakeFps"], "geometryWeightsMaterialsRestBonesEdited": False, "idleRawActionPreserved": True, "oldTurnIncluded": False, "clips": [{"name": "idle", "durationSeconds": 2., "fps": 24, "loop": True}, *[{"name": n, "durationSeconds": cfg[n]["durationSeconds"], "fps": cfg["bakeFps"], "loop": True, "designSpeedMps": cfg[n]["designSpeedMps"], "playbackSpeed": 1., "sameFootStrideMeters": cfg[n]["durationSeconds"]*cfg[n]["designSpeedMps"], "stepsPerMinute": 120/cfg[n]["durationSeconds"], "stanceFraction": cfg[n]["stanceFraction"], "stanceExcursionMeters": cfg[n]["designSpeedMps"]*cfg[n]["durationSeconds"]*cfg[n]["stanceFraction"], "maxReachFraction": max(reach[n])} for n in ("walk", "run")]], "exportForceSampling": False, "glbSha256": sha(out/"chr_player_male_poc_001.glb"), "blendSha256": sha(out/"character_locomotion_fit.blend"), "config": cfg, "targets": targets, "licence": "CC BY4.0", "credit": "Snow Rig (CC) Blender Foundation | studio.blender.org", "limitations": ["B02 elbow limitations retained deliberately, not close-up approved", "Fixed-speed instant starts/stops and720deg/s direction changes require actual Unity review", "Contact quality must be measured on exported skinned sole, not inferred from ankle target"]}
    dump(out/"asset-report.json", report)
    assert sha(source) == source_hash
    print(json.dumps({k: report[k] for k in ("version", "triangles", "bones", "clips", "glbSha256", "blendSha256")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
