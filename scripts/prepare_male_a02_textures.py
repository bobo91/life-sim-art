"""Bake the fixed A02 skin look from immutable prepared A01 maps.

Only the three occupied skin-atlas tiles are remapped. Existing render-UV tile
coordinates are copied; unused fourth-quadrant pixels and non-skin PNG bytes
are retained. This is a texture look recipe, not facial identity geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil

from PIL import Image, ImageChops

SKIN_MAPS = {
    "skin_diffuse_atlas.png": None,
    "skin_darker_diffuse_atlas.png": "darkerTintLinear",
    "skin_upper_lip_diffuse_atlas.png": "upperLipTintLinear",
    "skin_lower_lip_diffuse_atlas.png": "lowerLipTintLinear",
}
DEFAULT_RECIPE = {
    "sourceMedianSrgb8": [111, 81, 59],
    "targetMedianSrgb8": [169, 130, 110],
    "exponent": 0.55,
    "darkerTintLinear": [0.82, 0.78, 0.76],
    "upperLipTintLinear": [0.96, 0.88, 0.86],
    "lowerLipTintLinear": [0.99, 0.92, 0.91],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_srgb(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def encode_srgb(value: float) -> float:
    return 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055


def image_record(path: Path) -> dict:
    with Image.open(path) as image:
        dimensions, mode = list(image.size), image.mode
        image.verify()
    return {"file": path.name, "bytes": path.stat().st_size,
            "sha256": sha(path), "dimensions": dimensions, "mode": mode}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if not source.is_dir():
        raise NotADirectoryError(source)
    if output.exists():
        raise FileExistsError("Keep prior outputs; use a fresh directory: " + str(output))
    if source == output or source in output.parents:
        raise ValueError("Output must be outside the immutable input directory")

    recipe = {key: list(value) if isinstance(value, list) else value
              for key, value in DEFAULT_RECIPE.items()}
    config_record = None
    if args.config:
        config_path = args.config.resolve(strict=True)
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        overrides = config.get("materials", {}).get("skinRemap", {})
        unknown = set(overrides) - set(recipe)
        if unknown:
            raise ValueError("Unknown skinRemap settings: " + ", ".join(sorted(unknown)))
        recipe.update(overrides)
        config_record = {"path": str(config_path), "sha256": sha(config_path)}
    for key in ("sourceMedianSrgb8", "targetMedianSrgb8"):
        value = recipe[key]
        if not isinstance(value, list) or len(value) != 3 or not all(
                isinstance(v, (int, float)) and math.isfinite(v) and 0 < v <= 255 for v in value):
            raise ValueError(key + " must be three positive sRGB8 channel values")
    if not isinstance(recipe["exponent"], (int, float)) or not math.isfinite(recipe["exponent"]) or not 0 < recipe["exponent"] <= 1:
        raise ValueError("exponent must be finite and in (0,1]")
    for key in ("darkerTintLinear", "upperLipTintLinear", "lowerLipTintLinear"):
        value = recipe[key]
        if not isinstance(value, list) or len(value) != 3 or not all(
                isinstance(v, (int, float)) and math.isfinite(v) and 0 < v <= 1 for v in value):
            raise ValueError(key + " must be three linear multipliers in (0,1]")
    # Keep the newly proposed lip contrast no stronger than the A01 recipe.
    if any(v < floor for v, floor in zip(recipe["upperLipTintLinear"], [0.90, 0.71, 0.68])) or any(
            v < floor for v, floor in zip(recipe["lowerLipTintLinear"], [0.96, 0.80, 0.76])):
        raise ValueError("Lip multipliers may not darken more strongly than A01")

    mapping_path = source / "atlas-mapping.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8-sig"))
    tiles = mapping["tiles"]
    if set(tiles) != {"1001", "1002", "1003"}:
        raise ValueError("Expected the three inspected source skin tiles")
    input_pngs = sorted(source.glob("*.png"))
    for name in [*SKIN_MAPS, "pants_tinted_diffuse.png"]:
        if not (source / name).is_file():
            raise FileNotFoundError("Required prepared A01 map missing: " + name)
    input_records = [image_record(path) for path in input_pngs]
    input_hashes = {record["file"]: record["sha256"] for record in input_records}
    with Image.open(source / "skin_diffuse_atlas.png") as image:
        if image.mode != "RGB" or image.width != image.height or image.width % 2:
            raise ValueError("Expected an even square RGB skin atlas")
        base = image.copy()
        profile = image.info.get("icc_profile")
    width, height = base.size
    tile_size = width // 2
    boxes = []
    for key in sorted(tiles):
        tile = tiles[key]
        if tile["scale"] != [0.5, 0.5]:
            raise ValueError("Unexpected source tile scale")
        x = round(tile["offset"][0] * width)
        y = round((1 - tile["offset"][1]) * height) - tile_size
        boxes.append((x, y, x + tile_size, y + tile_size))
    expected_boxes = {(0, tile_size, width // 2, height),
                      (width // 2, tile_size, width, height),
                      (0, 0, width // 2, height // 2)}
    if set(boxes) != expected_boxes:
        raise ValueError("Unexpected occupied skin-atlas quadrants")
    unused_box = (tile_size, 0, width, tile_size)
    source_linear = [decode_srgb(v / 255) for v in recipe["sourceMedianSrgb8"]]
    target_linear = [decode_srgb(v / 255) for v in recipe["targetMedianSrgb8"]]
    output.mkdir(parents=True, exist_ok=False)
    output_records = []
    for path in input_pngs:
        destination = output / path.name
        if path.name not in SKIN_MAPS:
            shutil.copy2(path, destination)
            record = image_record(destination)
            record.update(operation="byte-for-byte copy", inputFile=path.name,
                          inputBytesUnchanged=record["sha256"] == input_hashes[path.name])
            if not record["inputBytesUnchanged"]:
                raise RuntimeError("Non-skin copy differs: " + path.name)
        else:
            tint_key = SKIN_MAPS[path.name]
            tint = recipe[tint_key] if tint_key else [1.0, 1.0, 1.0]
            table = []
            for channel in range(3):
                for code in range(256):
                    old = decode_srgb(code / 255)
                    remapped = target_linear[channel] * (old / source_linear[channel]) ** recipe["exponent"]
                    remapped = max(0.0, min(1.0, remapped * tint[channel]))
                    table.append(round(max(0.0, min(1.0, encode_srgb(remapped))) * 255))
            with Image.open(path) as original:
                if original.mode != "RGB" or original.size != base.size:
                    raise ValueError("Prepared skin-map layout differs: " + path.name)
                result = original.copy()
                original_unused = original.crop(unused_box)
            for box in boxes:
                result.paste(base.crop(box).point(table), box)
            if ImageChops.difference(original_unused, result.crop(unused_box)).getbbox() is not None:
                raise AssertionError("Unused quadrant changed")
            save_args = {"icc_profile": profile} if profile else {}
            result.save(destination, format="PNG", compress_level=9, optimize=False, **save_args)
            record = image_record(destination)
            record.update(operation="fixed linear skin remap and optional linear tint; one final 8-bit quantization",
                          inputFile="skin_diffuse_atlas.png", originalUnusedQuadrantFile=path.name,
                          unusedQuadrantPixelsUnchanged=True, linearTint=tint)
        output_records.append(record)
    # The rendering UV map stays exactly the same; do not publish stale A01 map hashes as A02 outputs.
    out_mapping = {
        "schema": "male-neutral-a02-atlas-mapping-1", "tiles": tiles,
        "atlas_dimensions": list(base.size), "tile_dimensions": [tile_size, tile_size],
        "uv_formula": mapping.get("uv_formula", "atlas_uv = (source_uv - source_uv_origin) * scale + offset"),
        "sourceMappingSha256": sha(mapping_path), "processingManifest": "texture-processing.json",
        "license": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "credit": "Snow Rig (CC) Blender Foundation | studio.blender.org",
        "source_url": "https://studio.blender.org/characters/snow/v4/",
    }
    (output / "atlas-mapping.json").write_bytes((json.dumps(out_mapping, indent=2) + "\n").encode())
    for record in input_records:
        if sha(source / record["file"]) != record["sha256"]:
            raise RuntimeError("Input texture changed: " + record["file"])
    if sha(mapping_path) != out_mapping["sourceMappingSha256"]:
        raise RuntimeError("Input UV mapping changed")
    manifest = {
        "schema": "male-neutral-a02-texture-processing-1", "recipe": recipe,
        "sourceMedianLinear": source_linear, "targetMedianLinear": target_linear,
        "formula": "srgb_encode(clamp(targetLinear * (srgb_decode(source)/sourceMedianLinear)^exponent * linearTint,0,1)); round to 8-bit",
        "sourcePreparedDirectory": str(source), "config": config_record,
        "sourceMapping": {"file": "atlas-mapping.json", "sha256": sha(mapping_path)},
        "outputMapping": {"file": "atlas-mapping.json", "sha256": sha(output / "atlas-mapping.json")},
        "occupiedPixelBoxes": [list(box) for box in boxes], "unusedPixelBox": list(unused_box),
        "inputs": input_records, "outputs": output_records,
        "allInputsUnchanged": True,
        "nonSkinMapsCopiedByteForByte": True,
        "pantsTintedMapByteForByte": sha(source / "pants_tinted_diffuse.png") == sha(output / "pants_tinted_diffuse.png"),
        "eyeColorChanged": False,
        "pixelEditingScope": "Only three occupied skin-color quadrants; existing source variation compressed, no painted facial features. Source topology/UV coordinates untouched.",
        "license": "CC-BY-4.0", "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
        "sourceUrl": "https://studio.blender.org/characters/snow/v4/",
        "credit": "Snow Rig (CC) Blender Foundation | studio.blender.org",
        "pillowVersion": Image.__version__,
    }
    manifest_path = output / "texture-processing.json"
    manifest_path.write_bytes((json.dumps(manifest, indent=2) + "\n").encode())
    print(json.dumps({"status": "completed", "output": str(output), "pngCount": len(output_records),
                      "changedSkinMaps": len(SKIN_MAPS), "copiedMaps": len(output_records)-len(SKIN_MAPS),
                      "allInputsUnchanged": True, "manifestSha256": sha(manifest_path),
                      "skinAtlasSha256": sha(output / "skin_diffuse_atlas.png")}))


if __name__ == "__main__":
    main()
