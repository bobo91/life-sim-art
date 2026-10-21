"""CLI wrapper runs Blender in an isolated process, then verifies its actual GLB."""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import struct
import sys
from pathlib import Path

from .config import canonical_json, load_config, sha256_file
from .benchmark_checks import streetlamp_frame
from .validation import validate_bundle, validate_glb

ROOT = Path(__file__).resolve().parents[1]


def normalize_png_metadata(path):
    """Remove volatile text/time metadata without decoding or changing rendered pixels."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Renderer did not produce PNG")
    clean = bytearray(data[:8])
    offset = 8
    while offset < len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        end = offset+12+length
        if end > len(data):
            raise ValueError("Truncated renderer PNG")
        if data[offset+4:offset+8] not in (b"tEXt", b"iTXt", b"zTXt", b"tIME"):
            clean.extend(data[offset:end])
        offset = end
    path.write_bytes(clean)


def blender_binary(value):
    candidate = value or os.environ.get("BLENDER_BIN") or shutil.which("blender")
    if not candidate or not Path(candidate).is_file():
        raise ValueError("Blender not found. Supply --blender or BLENDER_BIN (see docs/PIPELINE.md)")
    return str(Path(candidate).resolve())


def source_identity():
    digest = hashlib.sha256()
    for path in sorted((ROOT / "art_pipeline").glob("*.py")):
        digest.update(path.relative_to(ROOT).as_posix().encode()+b"\0"+path.read_bytes()+b"\0")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=ROOT,
                                text=True, capture_output=True, check=True).stdout.strip())
    return commit, digest.hexdigest(), dirty


def build(args):
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    binary = blender_binary(args.blender)
    output = Path(args.output).resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Output must be a new or empty directory; use a different path for each build")
    output.mkdir(parents=True, exist_ok=True)
    commit, digest, dirty = source_identity()
    command = [binary, "--background", "--factory-startup", "--threads", "1", "--python-exit-code", "1",
               "--python", str(ROOT / "art_pipeline/blender_build.py"), "--",
               "--config", str(config_path), "--output", str(output)]
    try:
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=1800, text=True, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        (output / "blender.log").write_text(str(exc.stdout or ""), encoding="utf-8")
        raise ValueError("Blender exceeded 30 minute limit; see blender.log") from exc
    (output / "blender.log").write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        raise ValueError(f"Blender failed ({result.returncode}); see {output / 'blender.log'}")
    if "ART_PIPELINE_BUILD_OK " not in result.stdout:
        raise ValueError("Blender did not confirm build completion")
    for name in ("front", "isometric"):
        normalize_png_metadata(output / (name+".png"))
    model = output / (config["assetId"]+".glb")
    geometry = validate_glb(model, config["dimensionsMeters"], config["maxTriangles"],
                            expected_materials=["metal", "edge", "glass", "fastener"])
    report = json.loads((output / "build_report.json").read_text(encoding="utf-8"))
    config_arg = config_path.relative_to(ROOT).as_posix() if config_path.is_relative_to(ROOT) else str(config_path)
    manifest = {
        "schemaVersion":"1.0", "requestId":config["requestId"], "assetId":config["assetId"],
        "version":config["version"], "category":config["category"], "seed":config["seed"],
        "sourceCommit":commit, "sourceDigest":digest, "sourceDirty":dirty,
        "config":config, "configSHA256":hashlib.sha256(canonical_json(config)).hexdigest(),
        "units":"meters", "axes":{"sourceUp":"+Z", "sourceForward":"-Y", "exportUp":"+Y", "exportForward":"+Z"},
        "pivot":"bottom-center", "dimensionsMeters":config["dimensionsMeters"], "maxTriangles":config["maxTriangles"],
        "model":{"file":model.name, "sha256":sha256_file(model), "bytes":model.stat().st_size},
        "geometry":geometry, "materials":geometry["materials"],
        "previews":{name:{"file":name+".png", "sha256":sha256_file(output / (name+".png")),
                           "width":config["preview"]["resolution"], "height":config["preview"]["resolution"]}
                    for name in ("front", "isometric")},
        "provenance":{"method":"procedural-blender-python", "thirdPartyAssets":[],
                      "generator":"art_pipeline/blender_build.py", "license":"original-project-content"},
        "tooling":{key:report[key] for key in ("blender","blenderBuildHash","platform","python","engine","device")},
        "blenderMeshHealth":report["meshHealth"], "forwardProbe":streetlamp_frame(model, config),
        "command":f'python -m art_pipeline build --blender <Blender-{config["blenderVersion"]}> --config "{config_arg}" --output <new-directory>',
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    validated = validate_bundle(output)
    print(json.dumps({"status":"passed", "output":str(output), "modelSHA256":manifest["model"]["sha256"],
                      "triangles":geometry["triangles"], "validation":validated}, indent=2))


def compare(first, second):
    for directory in (first, second):
        validate_bundle(directory)
    a, b = [json.loads((Path(directory) / "manifest.json").read_text(encoding="utf-8")) for directory in (first,second)]
    for key in ("assetId", "version", "seed", "configSHA256", "sourceDigest", "tooling"):
        if a[key] != b[key]:
            raise ValueError("Reproducibility inputs differ: " + key)
    differences = ["model"] if a["model"]["sha256"] != b["model"]["sha256"] else []
    differences += [name for name in ("front","isometric") if a["previews"][name]["sha256"] != b["previews"][name]["sha256"]]
    if differences:
        raise ValueError("Reproducibility failed: different bytes for " + ", ".join(differences))
    print(json.dumps({"status":"passed", "modelSHA256":a["model"]["sha256"], "byteIdentical":["model","front","isometric"]}, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("build", help="Generate, render and validate one isolated asset bundle")
    generate.add_argument("--blender")
    generate.add_argument("--config", required=True)
    generate.add_argument("--output", required=True)
    validate = sub.add_parser("validate", help="Independently verify a delivered bundle")
    validate.add_argument("directory")
    comparison = sub.add_parser("compare", help="Require byte-identical GLB and CPU renders from two fresh runs")
    comparison.add_argument("first")
    comparison.add_argument("second")
    audit = sub.add_parser("audit", help="Report actual host Python and Blender binary version")
    audit.add_argument("--blender")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            build(args)
        elif args.command == "validate":
            print(json.dumps(validate_bundle(args.directory), indent=2))
        elif args.command == "compare":
            compare(args.first, args.second)
        else:
            binary = blender_binary(args.blender)
            version = subprocess.run([binary, "--version"], text=True, capture_output=True, check=True).stdout.splitlines()[0]
            print(json.dumps({"hostPython":platform.python_version(), "platform":platform.platform(),
                              "blenderBinary":binary, "blenderVersion":version, "renderDevice":"CPU"}, indent=2))
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        print("art-pipeline: " + str(exc), file=sys.stderr)
        return 1
