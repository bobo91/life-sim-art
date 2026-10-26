"""Publish the validated modular houses, editable sources and actual review renders."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
CONFIG = "configs/modular-building.json"
SOURCES = tuple("scripts/" + name + ".py" for name in (
    "building_geometry", "building_core", "building_roof", "building_openings",
    "building_validation", "build_modular_building", "run_modular_building",
    "compose_modular_building", "package_modular_building", "walter_common",
    "props_walter", "walter_mailbox_reference"))
VIEWS = ("walter-three-quarter.png", "walter-game-16m.png", "walter-entry-6m.png",
         "walter-roof-hidden.png", "walter-cutaway.png", "alternate-house.png")
ALLOWED = {".py", ".json", ".png", ".blend", ".md", ".glb", ".yml"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    def reject_absolute(item):
        if isinstance(item, str) and (PurePosixPath(item).is_absolute() or PureWindowsPath(item).is_absolute()):
            raise ValueError("Absolute path in packaged JSON: " + path.relative_to(ROOT).as_posix())
        if isinstance(item, dict):
            for nested in item.values():
                reject_absolute(nested)
        elif isinstance(item, list):
            for nested in item:
                reject_absolute(nested)
    reject_absolute(value)
    return value


def require(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing regular artifact input: " + path.relative_to(ROOT).as_posix())
    path.resolve().relative_to(ROOT)
    return path


def excluded(path):
    return (any(part in {"__pycache__", ".git", ".cache"} or "private" in part.lower()
                or "isolated-profile" in part.lower() for part in path.parts)
            or bool(re.search(r"\.blend\d+$", path.name))
            or path.suffix.lower() in {".log", ".pyc", ".tmp"})


def record_file(folder, record, expected_name):
    if not isinstance(record, dict) or record.get("file") != expected_name:
        raise ValueError("Manifest filename mismatch: " + expected_name)
    path = require(folder / expected_name)
    if sha(path) != record.get("sha256"):
        raise ValueError("Manifest SHA256 mismatch: " + path.relative_to(ROOT).as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source, output = ((ROOT / value).resolve() for value in (args.input, args.output))
    for path in (source, output):
        path.relative_to(ROOT)
    if output.exists():
        raise FileExistsError("Preserve the existing versioned archive")
    if source in output.parents:
        raise ValueError("Archive output must be outside the input build directory")
    validation = read_json(require(source / "validation.json"))
    if validation.get("status") != "passed":
        raise ValueError("Require a successfully validated modular build")
    pack_manifest=read_json(require(source / "pack-manifest.json"))
    config = read_json(require(ROOT / CONFIG))
    if config.get("version") != VERSION:
        raise ValueError("Unexpected modular building version")

    expected_ids = {asset["assetId"] for asset in config["assets"]}
    actual_ids = {path.name for path in (source / "modules").iterdir() if path.is_dir()}
    if actual_ids != expected_ids:
        raise ValueError("Packaged modules do not match configured asset IDs")
    reference_folders = sorted(path for path in (source / "references").iterdir() if path.is_dir())
    if not reference_folders:
        raise ValueError("Require original reused porch/mailbox references")
    for folder in [source / "modules" / asset for asset in sorted(expected_ids)] + reference_folders:
        asset = folder.name
        if not re.fullmatch(r"[a-z][a-z0-9_]*", asset):
            raise ValueError("Invalid artifact asset ID")
        manifest = read_json(require(folder / "manifest.json"))
        if manifest.get("assetId") != asset:
            raise ValueError("Manifest asset ID mismatch")
        record_file(folder, manifest.get("model"), asset + ".glb")
        record_file(folder, manifest.get("sourceBlend"), asset + ".blend")
        if folder.parent.name == "modules":
            for view in ("front", "isometric"):
                record_file(folder, manifest.get("previews", {}).get(view), view + ".png")
    for house in ("walter-house", "alternate-house"):
        for extension in (".glb", ".blend"):
            require(source / "assemblies" / (house + extension))
        record_file(source / "assemblies", pack_manifest["assemblies"][house.removesuffix("-house")], house+".glb")
    for view in VIEWS:
        require(source / "previews" / view)
    presentation=read_json(require(source / "presentation.json"))
    if sha(source / "presentation.json")!=pack_manifest["presentationSHA256"]:
        raise ValueError("Presentation record changed after validation")
    for view in VIEWS:
        record_file(source / "previews",presentation["views"][view.removesuffix(".png")],view)
    layout=read_json(require(source / "review/contact-layout.json"))
    if sha(require(source / "review/contact-sheet.png"))!=layout["outputSHA256"]:
        raise ValueError("Contact sheet changed after composition")

    # Validate exact generator inputs recorded by the worker, then include them.
    source_hashes = validation.get("sourceHashes")
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise ValueError("Validation must record generator sourceHashes")
    for name, digest in source_hashes.items():
        path = require(ROOT / name)
        if sha(path) != digest:
            raise ValueError("Generator input changed after validation: " + name)
    files = [path for path in source.rglob("*") if path.is_file() and not excluded(path)]
    files += [require(ROOT / name) for name in SOURCES]
    files += [require(ROOT / name) for name in source_hashes]
    files += list((ROOT / "art_pipeline").glob("*.py"))
    files += [ROOT / CONFIG, ROOT / "configs/walter-mailbox-reference.json"]
    files += [ROOT / "configs" / (path.name + ".json") for path in reference_folders
              if path.name != "prop_mailbox_001"]
    files += [ROOT / "docs/buildings/MODULAR_BUILDING_SYSTEM.md",
              ROOT / "reports/modular-building-v0.1.0/quality-report.md",
              ROOT / "reports/modular-building-v0.1.0/technical-results.json",
              ROOT / "tests/test_building_validation.py",
              ROOT / ".github/workflows/modular-building.yml"]
    files += list((ROOT / "reports/modular-building-v0.1.0").glob("*.png"))
    files += list((ROOT / "tests").glob("test_*.py")) + [ROOT / "tests/__init__.py"]
    files = sorted(set(require(path) for path in files))
    for path in files:
        if path.suffix.lower() not in ALLOWED:
            raise ValueError("Unexpected artifact extension: " + path.relative_to(ROOT).as_posix())
        if path.suffix.lower() == ".json":
            read_json(path)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                            capture_output=True, text=True).stdout.strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    index = []
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            payload = path.read_bytes()
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload)
            index.append({"path": name, "bytes": len(payload),
                          "sha256": hashlib.sha256(payload).hexdigest()})
    # Read back the published archive contents rather than trusting writes alone.
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or len(archive.infolist()) != len(index):
            raise ValueError("Archive verification failed")
        for item in index:
            payload = archive.read(item["path"])
            if len(payload) != item["bytes"] or hashlib.sha256(payload).hexdigest() != item["sha256"]:
                raise ValueError("Archive read-back mismatch: " + item["path"])
    digest = sha(output)
    record = {"schema": "modular-building-review-artifact-1", "version": VERSION,
              "sourceCommit": commit, "githubSHA": os.environ.get("GITHUB_SHA"),
              "sourceHashes": {path.relative_to(ROOT).as_posix(): sha(path)
                               for path in files if path.suffix in {".py", ".yml"}},
              "sha256": digest, "bytes": output.stat().st_size, "files": index,
              "archiveReadBackVerified": True,
              "scope": "Owner visual review; no Unity/game integration or merge."}
    output.with_suffix(".zip.sha256").write_text(digest + "  " + output.name + "\n", encoding="utf-8")
    output.with_suffix(".zip.index.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key not in {"files", "sourceHashes"}}, indent=2))


if __name__ == "__main__":
    main()
