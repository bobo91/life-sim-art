"""Render and verify the controlled ART-002 streetlamp palette comparison.

Run from any directory with --output <new-or-empty-directory>. Both variants use
the same original procedural mesh, seed, camera, light setup and CPU renderer.
Complete independently validated bundles and a comparison.json remain on disk.
"""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from art_pipeline.cli import blender_binary
from art_pipeline.config import load_config, sha256_file, validate_config
from art_pipeline.validation import _accessor, _read_glb, validate_bundle

PALETTES = ("civic_sage", "harbor_slate")
MATERIALS = {"metal", "edge", "glass", "fastener"}


def validate_library(library):
    """Validate the complete authored library before creating any output files."""
    if (not isinstance(library, dict) or set(library) != {"schemaVersion", "palettes"}
            or library["schemaVersion"] != "1.0"):
        raise ValueError("Material library requires schemaVersion 1.0 and palettes")
    palettes = library["palettes"]
    if not isinstance(palettes, dict) or set(palettes) != set(PALETTES):
        raise ValueError("Material library must define civic_sage and harbor_slate")
    for name, palette in palettes.items():
        if (not isinstance(palette, dict) or set(palette) != {"description", "materials"}
                or not isinstance(palette["description"], str) or not palette["description"].strip()):
            raise ValueError(f"Palette {name} requires a description and materials")
        materials = palette["materials"]
        if not isinstance(materials, dict) or set(materials) != MATERIALS:
            raise ValueError(f"Palette {name} requires metal, edge, glass, fastener")
        for material in materials.values():
            if (not isinstance(material, dict) or set(material) != {"color", "roughness", "metallic"}
                    or not isinstance(material["color"], str)
                    or not re.fullmatch(r"#[0-9A-Fa-f]{6}", material["color"])):
                raise ValueError(f"Palette {name} has an invalid PBR material or color")
            for key in ("roughness", "metallic"):
                value = material[key]
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError(f"Palette {name} {key} must be finite in [0,1]")
    if palettes[PALETTES[0]]["materials"] == palettes[PALETTES[1]]["materials"]:
        raise ValueError("Comparison palettes must have different materials")
    for material in MATERIALS:
        for factor in ("roughness", "metallic"):
            if palettes[PALETTES[0]]["materials"][material][factor] != palettes[PALETTES[1]]["materials"][material][factor]:
                raise ValueError("Color comparison must preserve PBR factors: " + material + "." + factor)
    return library


def load_library(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate material library key: " + key)
            result[key] = value
        return result
    return validate_library(json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_keys))


def derive_configs(base, library):
    """Create isolated configs whose only differences are asset ID and palette."""
    validate_config(base)
    validate_library(library)
    if base["seed"] != 1701:
        raise ValueError("ART-002 comparison requires the reference seed 1701")
    result = {}
    for palette in PALETTES:
        config = copy.deepcopy(base)
        config.update(requestId="ART-002", assetId="prop_streetlamp_benchmark_" + palette,
                      version="0.1.0", preview={"resolution": 640, "samples": 64},
                      palette=copy.deepcopy(library["palettes"][palette]["materials"]))
        result[palette] = validate_config(config)
    return result


def geometry_fingerprint(path):
    """Hash decoded positions, normals and topology, excluding names/materials.

    The streetlamp generator bakes one mesh in exported coordinates. Refuse a
    hierarchy or transforms rather than silently hash untransformed positions.
    Accessor storage widths/padding, JSON names and PBR colors do not enter this
    digest. It proves exact generated vertex/topology equality for this benchmark.
    """
    _, document, binary = _read_glb(path)
    nodes = document.get("nodes", [])
    if (len(nodes) != 1 or nodes[0].get("mesh") != 0 or
            any(key in nodes[0] for key in ("matrix", "translation", "rotation", "scale", "children"))):
        raise ValueError("Geometry comparison requires one identity-transform streetlamp mesh")
    primitives = document["meshes"][0]["primitives"]
    digest = hashlib.sha256(b"ART-002-decoded-static-mesh-v1\0")
    digest.update(struct.pack("<I", len(primitives)))
    for primitive in primitives:
        for semantic in ("POSITION", "NORMAL"):
            values, _ = _accessor(document, binary, primitive["attributes"][semantic], "VEC3", {5126})
            digest.update(semantic.encode("ascii") + struct.pack("<I", len(values)))
            for value in values:
                digest.update(struct.pack("<3d", *value))
        indices, _ = _accessor(document, binary, primitive["indices"], "SCALAR", {5121, 5123, 5125})
        digest.update(b"INDICES" + struct.pack("<I", len(indices)))
        for index in indices:
            digest.update(struct.pack("<I", index[0]))
    return digest.hexdigest()


def compare_manifests(manifests, configs, geometry_hashes):
    """Check comparison controls after each bundle has independently validated."""
    if any(set(items) != set(PALETTES) for items in (manifests, configs, geometry_hashes)):
        raise ValueError("Comparison requires exactly both named palette variants")
    a, b = (manifests[name] for name in PALETTES)
    for name in PALETTES:
        if manifests[name]["config"] != configs[name]:
            raise ValueError("Built config disagrees with requested palette: " + name)
    control_a, control_b = (copy.deepcopy(configs[name]) for name in PALETTES)
    for config in (control_a, control_b):
        config.pop("assetId")
        config.pop("palette")
    if control_a != control_b:
        raise ValueError("Comparison generator/seed/dimensions/budget/render controls differ")
    for key in ("sourceCommit", "sourceDigest", "sourceDirty", "tooling"):
        if a[key] != b[key]:
            raise ValueError("Comparison source or tool versions differ: " + key)
    for key in ("triangles", "vertices", "meshInstances", "bounds", "dimensionsMeters"):
        if a["geometry"][key] != b["geometry"][key]:
            raise ValueError("Comparison geometry differs: " + key)
    if geometry_hashes[PALETTES[0]] != geometry_hashes[PALETTES[1]]:
        raise ValueError("Decoded mesh positions, normals or topology differ")
    if a["model"]["sha256"] == b["model"]["sha256"]:
        raise ValueError("Different palettes must produce different GLB bytes")
    for view in ("front", "isometric"):
        if a["previews"][view]["sha256"] == b["previews"][view]["sha256"]:
            raise ValueError("Palette comparison produced identical " + view + " renders")
    return {"sameGeometry": True, "geometrySHA256": geometry_hashes[PALETTES[0]],
            "controls": control_a, "sourceCommit": a["sourceCommit"],
            "sourceDigest": a["sourceDigest"], "sourceDirty": a["sourceDirty"], "tooling": a["tooling"]}


def _reference(path):
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def run_benchmark(output, blender=None, library_path=None, config_path=None):
    output = Path(output).resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Output must be a new or empty directory; existing results are retained")
    library_path = Path(library_path or ROOT / "materials/library.json").resolve()
    config_path = Path(config_path or ROOT / "configs/streetlamp.json").resolve()
    configs = derive_configs(load_config(config_path), load_library(library_path))
    binary = blender_binary(blender)
    inputs = {"library": (library_path, sha256_file(library_path)),
              "baseConfig": (config_path, sha256_file(config_path)),
              "benchmarkScript": (Path(__file__).resolve(), sha256_file(__file__))}
    output.mkdir(parents=True, exist_ok=True)
    (output / "configs").mkdir()
    config_paths = {}
    for name in PALETTES:
        config_paths[name] = output / "configs" / (name + ".json")
        config_paths[name].write_text(json.dumps(configs[name], indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    manifests, geometry_hashes = {}, {}
    for name in PALETTES:
        bundle = output / name
        subprocess.run([sys.executable, "-m", "art_pipeline", "build", "--blender", binary,
                        "--config", str(config_paths[name]), "--output", str(bundle)],
                       cwd=ROOT, check=True, timeout=1900)
        validate_bundle(bundle)
        manifests[name] = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        geometry_hashes[name] = geometry_fingerprint(bundle / manifests[name]["model"]["file"])
    result = compare_manifests(manifests, configs, geometry_hashes)
    for path, expected in inputs.values():
        if sha256_file(path) != expected:
            raise ValueError("Comparison input changed during rendering: " + str(path))
    result.update(schemaVersion="1.0", requestId="ART-002", status="passed",
                  librarySHA256=inputs["library"][1],
                  inputs={name: {"file": _reference(path), "sha256": sha} for name, (path, sha) in inputs.items()},
                  variants={})
    for name in PALETTES:
        manifest = manifests[name]
        result["variants"][name] = {
            "assetId": manifest["assetId"], "bundle": name,
            "manifest": {"file": name + "/manifest.json", "sha256": sha256_file(output / name / "manifest.json")},
            "config": {"file": "configs/" + name + ".json", "sha256": sha256_file(config_paths[name]),
                       "canonicalSHA256": manifest["configSHA256"]},
            "model": dict(manifest["model"], file=name + "/" + manifest["model"]["file"]),
            "previews": {view: dict(info, file=name + "/" + info["file"]) for view, info in manifest["previews"].items()},
            "triangles": manifest["geometry"]["triangles"], "vertices": manifest["geometry"]["vertices"],
            "bounds": manifest["geometry"]["bounds"], "dimensionsMeters": manifest["geometry"]["dimensionsMeters"],
            "geometrySHA256": geometry_hashes[name]}
    comparison_path = output / "comparison.json"
    comparison_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    return comparison_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--blender")
    parser.add_argument("--library", help="Default: materials/library.json")
    parser.add_argument("--config", help="Default: configs/streetlamp.json")
    args = parser.parse_args(argv)
    try:
        path = run_benchmark(args.output, args.blender, args.library, args.config)
        print(json.dumps({"status": "passed", "comparison": str(path)}, indent=2))
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        print("art-benchmark: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
