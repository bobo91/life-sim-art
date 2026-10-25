"""Replay only the frozen prop geometry and compare the exported GLB bytes.

Host Python launches isolated Blender; Blender imports the original builders and
health function. No render, save, source change, or reference rewrite occurs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ("prop_mailbox_001", "prop_cafe_table_001")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def workspace_path(value):
    path = Path(value).resolve()
    path.relative_to(ROOT)
    return path


def frozen_inputs(reference):
    results = {}
    for asset_id in ASSETS:
        manifest_path = reference / asset_id / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        observed = {name: sha(ROOT / name) for name in manifest["sourceFilesSHA256"]}
        if observed != manifest["sourceFilesSHA256"]:
            raise ValueError("Frozen source SHA mismatch: " + asset_id)
        digest = hashlib.sha256(json.dumps(observed, sort_keys=True).encode()).hexdigest()
        if digest != manifest["sourceDigest"]:
            raise ValueError("Frozen source digest mismatch: " + asset_id)
        config_path = ROOT / "configs" / (asset_id + ".json")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if sha(config_path) != manifest["configSHA256"] or config != manifest["config"]:
            raise ValueError("Frozen config SHA/content mismatch: " + asset_id)
        model_path = reference / asset_id / manifest["model"]["file"]
        if sha(model_path) != manifest["model"]["sha256"]:
            raise ValueError("Reference GLB SHA mismatch: " + asset_id)
        results[asset_id] = {
            "manifestPath": str(manifest_path.relative_to(ROOT)),
            "manifestSHA256": sha(manifest_path),
            "sourceFilesSHA256": observed,
            "sourceDigest": digest,
            "configPath": str(config_path.relative_to(ROOT)),
            "configSHA256": sha(config_path),
            "referenceGlbPath": str(model_path.relative_to(ROOT)),
            "referenceGlbSHA256": sha(model_path),
        }
    return results


def blender_worker(args):
    import bpy

    if bpy.app.version != (4, 5, 14):
        raise RuntimeError("Pin Blender 4.5.14")
    if not bpy.app.background or bpy.app.online_access:
        raise RuntimeError("Require background/offline mode")
    reference, output = workspace_path(args.reference), workspace_path(args.output)
    before = frozen_inputs(reference)
    if output.exists():
        raise FileExistsError("Preserve existing results; use a new output directory")
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_first_playable_props import BUILDERS, clear, health

    output.mkdir(parents=True)
    assets = {}
    for asset_id in ASSETS:
        config = json.loads((ROOT / "configs" / (asset_id + ".json")).read_text(encoding="utf-8"))
        clear()
        obj = BUILDERS[asset_id](config)
        report = health(obj, config)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        destination = output / (asset_id + ".glb")
        # Keep the original export settings exactly; the output directory is new.
        bpy.ops.export_scene.gltf(
            filepath=str(destination), export_format="GLB", use_selection=True,
            export_yup=True, export_normals=True, export_materials="EXPORT", export_extras=False,
        )
        actual_sha = sha(destination)
        assets[asset_id] = {
            "replayGlbPath": str(destination.relative_to(ROOT)),
            "bytes": destination.stat().st_size,
            "sha256": actual_sha,
            "referenceSHA256": before[asset_id]["referenceGlbSHA256"],
            "byteIdentical": actual_sha == before[asset_id]["referenceGlbSHA256"],
            "health": report,
        }
    after = frozen_inputs(reference)
    result = {
        "blender": bpy.app.version_string,
        "blenderBuildHash": bpy.app.build_hash.decode(),
        "python": sys.version,
        "background": bpy.app.background,
        "onlineAccess": bpy.app.online_access,
        "inputsUnchanged": before == after,
        "assets": assets,
    }
    dump(output / "worker-result.json", result)
    if before != after or not all(item["byteIdentical"] for item in assets.values()):
        raise ValueError("Geometry replay/source identity mismatch; see worker-result.json")
    print("FIRST_PLAYABLE_GEOMETRY_REPLAY_OK", flush=True)


def host(args):
    reference, output, evidence = (workspace_path(value)
                                   for value in (args.reference, args.output, args.report))
    if output.exists() or evidence.exists():
        raise FileExistsError("Preserve existing replay and evidence")
    inputs = frozen_inputs(reference)
    profile = output.parent / (output.name + "-isolated-profile")
    profile.mkdir(parents=True, exist_ok=False)
    command = [args.blender, "--background", "--factory-startup", "--offline-mode", "--disable-autoexec",
               "--threads", "4", "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
               "--", "--worker", "--reference", str(reference), "--output", str(output)]
    env_settings = {"BLENDER_USER_RESOURCES": str(profile), "PYTHONHASHSEED": "0"}
    log_path = output.parent / (output.name + "-launcher.log")
    record = {
        "schemaVersion": "first-playable-props-geometry-replay-1",
        "startedUTC": datetime.now(timezone.utc).isoformat(),
        "scope": "One geometry-only replay after the frozen flag correction; no new asset version or rendering.",
        "hostCommand": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
        "blenderCommand": command,
        "cwd": str(ROOT),
        "environment": env_settings,
        "verificationScriptSHA256": sha(__file__),
        "inputs": inputs,
        "launcherLogPath": str(log_path.relative_to(ROOT)),
        "limitations": ["Tests exact GLB bytes on this pinned Blender/OS only; does not claim cross-platform determinism.",
                        "No preview replay, new save/reopen, Unity test or exhaustive intersection test.",
                        "Verification script is additional evidence tooling, not an alteration of the frozen production SOURCES."],
    }
    started = time.monotonic()
    with log_path.open("xb") as log:
        completed = subprocess.run(command, cwd=ROOT, env=dict(os.environ, **env_settings),
                                   stdout=log, stderr=subprocess.STDOUT, timeout=120)
    record.update(exitCode=completed.returncode, elapsedSeconds=round(time.monotonic() - started, 3),
                  launcherLogSHA256=sha(log_path))
    worker_path = output / "worker-result.json"
    if worker_path.exists():
        record["result"] = json.loads(worker_path.read_text(encoding="utf-8"))
    record["sourceAndReferenceUnchangedAfterRun"] = frozen_inputs(reference) == inputs
    record["status"] = "passed" if (
        completed.returncode == 0 and record["sourceAndReferenceUnchangedAfterRun"]
        and record.get("result", {}).get("inputsUnchanged")
        and all(record["result"]["assets"][asset_id]["byteIdentical"] for asset_id in ASSETS)
    ) else "failed"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    dump(evidence, record)
    if record["status"] != "passed":
        raise RuntimeError("Replay failed; inspect " + str(evidence))
    print("FIRST_PLAYABLE_GEOMETRY_REPLAY_PASSED " + json.dumps({
        "report": str(evidence), "elapsedSeconds": record["elapsedSeconds"],
        "assets": {asset_id: record["result"]["assets"][asset_id]["sha256"] for asset_id in ASSETS},
    }))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", default=str(ROOT / "build/first-playable-props/run-003"))
    parser.add_argument("--output", default=str(ROOT / "build/first-playable-props/replay-001"))
    parser.add_argument("--report", default=str(ROOT / "evidence/first-playable-props/geometry-replay.json"))
    parser.add_argument("--blender", default=os.environ.get("BLENDER_BIN", "blender"))
    parser.add_argument("--worker", action="store_true")
    parameters = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(parameters)
    blender_worker(args) if args.worker else host(args)


if __name__ == "__main__":
    main()
