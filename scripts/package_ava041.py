"""Package and read back ART-041's static review artifact; no release publishing.

The manifest indexes every payload with its SHA256 and size. ZIP timestamps and
permissions are fixed. Existing output artifacts are never replaced. A03 binary
inputs are deliberately outside the payload; only comparison renders and source
pin/provenance records belong in this independent Ava candidate package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "ava-morgan-visual-v0.1.0-review.1"
ASSET_ID = "chr_ava_morgan_041"
REQUIRED_GENERATED = ("character.blend", ASSET_ID + ".glb", "asset-report.json",
                      "render-metadata.json", "environment.json")
A03_PIN = {
    "purpose": "Unmodified same-scale comparison only; not an Ava mesh source",
    "tag": "male-neutral-a03-v0.3",
    "sourceCommit": "3ae0723b1c450d41ab42f83875164af495949fee",
    "zipSha256": "3ae53894ae1aef5c909a82d1c3d60b3f153005ca8dee0b11cfb646b2b09da6fc",
    "blendSha256": "dcd7681255f49fa704844492b0ffc6964e434ccb4ae59aaba7788b0af56ffd90",
    "license": "CC-BY-4.0",
    "credit": "Snow Rig (CC) Blender Foundation | studio.blender.org",
    "sourceUrl": "https://studio.blender.org/characters/snow/v4/",
    "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
            + "\n").encode("utf-8")


def git_record():
    def run(*args):
        result = subprocess.run(["git", "-C", str(ROOT), *args],
            check=True, capture_output=True, text=True, encoding="utf-8")
        return result.stdout.strip()
    try:
        return {"commit": run("rev-parse", "HEAD"),
                "workingTreeDirty": bool(run("status", "--porcelain", "--untracked-files=normal"))}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "workingTreeDirty": None,
                "note": "Git identity unavailable; exact bundled input hashes remain authoritative"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True, help="Fresh generator output directory")
    parser.add_argument("--validation", required=True, help="Passing validate_ava041 JSON")
    parser.add_argument("--out", required=True, help="New versioned ZIP path")
    args = parser.parse_args()
    build = Path(args.build).resolve()
    validation_path = Path(args.validation).resolve()
    output = Path(args.out).resolve()
    sidecar = output.with_suffix(output.suffix + ".sha256")
    verification_path = output.with_suffix(output.suffix + ".verification.json")
    for target in (output, sidecar, verification_path):
        if target.exists():
            raise FileExistsError("Preserve prior artifacts; choose a fresh output: " + str(target))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("status") != "pass" or validation.get("failed", 1) != 0:
        raise ValueError("A passing static source/GLB validation is required")
    producer = json.loads((build / "asset-report.json").read_text(encoding="utf-8"))
    for name, expected in producer["sourceFiles"].items():
        if sha((ROOT / "scripts" / name).read_bytes()) != expected:
            raise ValueError("Producer source differs from generated model: " + name)
    if sha((ROOT / "configs/ava041.json").read_bytes()) != producer["configSha256"]:
        raise ValueError("Producer config differs from generated model")
    payload = {}

    def add_file(source, archive_name):
        source = Path(source)
        name = PurePosixPath(archive_name)
        if name.is_absolute() or ".." in name.parts or "\\" in str(name):
            raise ValueError("Unsafe archive path: " + str(name))
        key = str(name)
        if key in payload:
            raise ValueError("Duplicate archive path: " + key)
        if not source.is_file() or source.is_symlink():
            raise ValueError("Expected a regular file: " + str(source))
        payload[key] = source.read_bytes()

    for name in REQUIRED_GENERATED:
        add_file(build / name, "model/" + name)
    for path in sorted(build.glob("*.json")):
        if path.name not in REQUIRED_GENERATED:
            add_file(path, "model/" + path.name)
    for key, filename in (("blend", "character.blend"), ("glb", ASSET_ID + ".glb")):
        expected = validation.get("inputs", {}).get(key, {}).get("sha256")
        if not expected or sha(payload["model/" + filename]) != expected:
            raise ValueError("Validation does not describe this exact " + key + " file")
    renders = sorted((build / "renders").glob("*.png"))
    if not renders:
        raise ValueError("Actual candidate render PNGs are required")
    for path in renders:
        add_file(path, "model/renders/" + path.name)
    add_file(validation_path, "validation.json")
    required_sources = ("scripts/build_ava041.py", "scripts/validate_ava041.py",
        "scripts/package_ava041.py", "configs/ava041.json",
        ".github/workflows/ava041.yml", "AGENTS.md", "docs/ART_CONTRACT.md",
        "docs/ART_DIRECTION.md", "docs/characters/ava-morgan/ART041_PREFLIGHT.md")
    repository_files = {ROOT / name for name in required_sources}
    for pattern in ("scripts/*ava041*.py", "configs/ava041*.json",
                    "art_pipeline/*.py", "docs/characters/ava-morgan/ART041*",
                    "evidence/ava041/**/*", "reports/ava041/**/*"):
        repository_files.update(path for path in ROOT.glob(pattern) if path.is_file())
    for path in sorted(repository_files):
        relative = path.relative_to(ROOT).as_posix()
        # Models remain generated outputs; prevent accidental binary source intake.
        if path.suffix.lower() in (".blend", ".glb", ".zip"):
            raise ValueError("Do not place model binaries in source/evidence paths: " + relative)
        add_file(path, "source/" + relative)
    notice = (
        "ART-041 Ava Morgan — static visual review candidate, not production approval.\n"
        "Ava geometry and materials are generated by the bundled original procedural scripts.\n"
        "No rig, skin weights or animations are delivered. See bundled ART041 documents\n"
        "for provenance, limitations and owner review requirements.\n\n"
        "If an A03 comparison render is present, its separate character is an unmodified\n"
        "Willow Creek A03 derivative of Blender Studio Snow v4. Ava does not use its mesh.\n"
        "Snow Rig (CC) Blender Foundation | studio.blender.org\n"
        "Source: https://studio.blender.org/characters/snow/v4/\n"
        "Licence: Creative Commons Attribution 4.0 International (CC BY 4.0)\n"
        "https://creativecommons.org/licenses/by/4.0/\n"
        "A03 was previously modified for Willow Creek identity, hair, materials and\n"
        "static simplification. This package adds comparison rendering only, no A03 edits.\n"
        "No Blender Foundation endorsement is implied. Preserve this attribution with\n"
        "the comparison renders. No upstream rig/UI source code is included.\n"
    )
    payload["NOTICE.txt"] = notice.encode("utf-8")
    manifest = {"schema": "ava-art041-indexed-review-artifact-1", "assetId": ASSET_ID,
        "version": VERSION, "phase": "A: static visual candidate",
        "approval": {"appearanceApproved": False, "integrationApproved": False,
                     "riggingAuthorized": False, "mergeAuthorized": False},
        "source": git_record(), "a03ComparisonPin": A03_PIN,
        "validation": {"status": validation["status"], "passed": validation.get("passed"),
                       "failed": validation["failed"]},
        "files": [{"path": name, "bytes": len(data), "sha256": sha(data)}
                  for name, data in sorted(payload.items())]}
    payload["manifest.json"] = encoded(manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=6)
    # Independent read-back of every entry, including exact manifest bytes.
    with zipfile.ZipFile(output) as archive:
        if sorted(archive.namelist()) != sorted(payload):
            raise ValueError("Archive payload names differ from the planned manifest")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC integrity check failed")
        for record in manifest["files"]:
            actual = archive.read(record["path"])
            if len(actual) != record["bytes"] or sha(actual) != record["sha256"]:
                raise ValueError("Archive entry hash mismatch: " + record["path"])
        if archive.read("manifest.json") != payload["manifest.json"]:
            raise ValueError("Archive manifest differs from the generated manifest")
    checksum = sha(output.read_bytes())
    sidecar.write_text(checksum + "  " + output.name + "\n", encoding="utf-8")
    verification = {"schema": "ava-art041-local-artifact-readback-1", "file": output.name,
        "bytes": output.stat().st_size, "sha256": checksum,
        "payloadHashesVerified": len(manifest["files"]),
        "entries": len(payload), "zipCrcPassed": True,
        "manifestExact": True, "downloadVerified": False,
        "note": "Local archive creation/read-back only; remote download requires a separate check"}
    verification_path.write_bytes(encoded(verification))
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
