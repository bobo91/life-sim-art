"""Strict, dependency-free generator configuration."""
import hashlib
import json
import math
import re
from pathlib import Path


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_config(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate config key: " + key)
            result[key] = value
        return result
    return validate_config(json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_keys))


def validate_config(config):
    """Validate a loaded object without filesystem or Blender dependencies."""
    required = {"schemaVersion", "requestId", "assetId", "version", "category", "generator", "seed",
                "dimensionsMeters", "maxTriangles", "blenderVersion", "palette", "preview"}
    if not isinstance(config, dict) or set(config) != required:
        raise ValueError("Config keys must be exactly: " + ", ".join(sorted(required)))
    if config["schemaVersion"] != "1.0" or config["generator"] != "streetlamp":
        raise ValueError("Unsupported config schema or generator")
    for key in ("assetId", "category"):
        if not isinstance(config[key], str) or not re.fullmatch(r"[a-z][a-z0-9_]{2,63}", config[key]):
            raise ValueError("Invalid " + key)
    if not isinstance(config["version"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", config["version"]):
        raise ValueError("version must be semver")
    if not isinstance(config["requestId"], str) or not re.fullmatch(r"ART-[0-9]{3}", config["requestId"]):
        raise ValueError("Invalid requestId")
    if not isinstance(config["blenderVersion"], str) or not re.fullmatch(r"4\.5\.[0-9]+", config["blenderVersion"]):
        raise ValueError("Pin an exact supported Blender 4.5 LTS patch")
    if type(config["seed"]) is not int or not 0 <= config["seed"] <= 2147483647:
        raise ValueError("seed must be a 31-bit unsigned integer")
    if type(config["maxTriangles"]) is not int or not 100 <= config["maxTriangles"] <= 100000:
        raise ValueError("maxTriangles must be 100..100000")
    dims = config["dimensionsMeters"]
    if not isinstance(dims, list) or len(dims) != 3 or any(
        type(v) not in (int, float) or not math.isfinite(v) or not 0.1 <= v <= 100 for v in dims
    ):
        raise ValueError("dimensionsMeters must be three finite positive X,Y,Z export dimensions")
    if not 3 <= dims[1] / max(dims[0], dims[2]) <= 8:
        raise ValueError("Streetlamp height/width ratio must be 3..8")
    palette = config["palette"]
    if not isinstance(palette, dict) or set(palette) != {"metal", "edge", "glass", "fastener"}:
        raise ValueError("palette must define metal, edge, glass, fastener")
    for name, material in palette.items():
        if not isinstance(material, dict) or set(material) != {"color", "roughness", "metallic"}:
            raise ValueError("Material must define color, roughness, metallic: " + name)
        color = material["color"]
        if not isinstance(color, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            raise ValueError("Color must be an sRGB hex triplet")
        for key in ("roughness", "metallic"):
            if type(material[key]) not in (int, float) or not math.isfinite(material[key]) or not 0 <= material[key] <= 1:
                raise ValueError("Material values must be finite in [0,1]")
    preview = config["preview"]
    if not isinstance(preview, dict) or set(preview) != {"resolution", "samples"}:
        raise ValueError("preview requires resolution and samples")
    if type(preview["resolution"]) is not int or not 128 <= preview["resolution"] <= 2048:
        raise ValueError("preview.resolution must be 128..2048")
    if type(preview["samples"]) is not int or not 1 <= preview["samples"] <= 256:
        raise ValueError("preview.samples must be 1..256")
    return config
