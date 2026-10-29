"""Prepare the one approved Snow-derived static male PoC texture set.

Reads original PNGs only. A fresh output directory is required. Optional recipe-driven portable tint bakes reproduce existing linear shader multipliers.
No source edits or normal-vector renormalization occur.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image


SOURCE_URL = "https://studio.blender.org/characters/snow/v4/"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
CREDIT = "Snow Rig (CC) Blender Foundation | studio.blender.org"
TILES = {
    1001: {"source_uv_origin": [0, 0], "scale": [0.5, 0.5], "offset": [0, 0]},
    1002: {"source_uv_origin": [1, 0], "scale": [0.5, 0.5], "offset": [0.5, 0]},
    1003: {"source_uv_origin": [2, 0], "scale": [0.5, 0.5], "offset": [0, 0.5]},
}
COPIES = (
    ("eyes_diffuse.png", 2048, "sRGB"),
    ("eyes_normal.png", 2048, "Non-Color"),
    ("shirt_normal.png", 2048, "Non-Color"),
    ("pants_diffuse.png", 2048, "sRGB"),
    ("pants_normal.png", 2048, "Non-Color"),
    ("pants_roughness.png", 2048, "Non-Color"),
    ("shoes_diffuse.png", 2048, "sRGB"),
    ("shoes_normal.png", 2048, "Non-Color"),
    ("shoes_roughness.png", 2048, "Non-Color"),
    ("shoes_metalness.png", 2048, "Non-Color"),
    ("hair_roughness.png", 1024, "Non-Color"),
)
PADDING_RGB = (128, 128, 128)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_record(path: Path) -> dict:
    with Image.open(path) as im:
        size, mode = list(im.size), im.mode
        im.verify()
    return {
        "file": path.name,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "dimensions": size,
        "mode": mode,
    }


def save_png(im: Image.Image, path: Path, icc_profile: bytes | None = None) -> None:
    kwargs = {"icc_profile": icc_profile} if icc_profile else {}
    im.save(path, format="PNG", compress_level=9, optimize=False, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-size", type=int, default=2048)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    if args.max_size < 2 or args.max_size % 2:
        parser.error("--max-size must be an even positive integer of at least 2")
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if not source.is_dir():
        raise NotADirectoryError(source)
    if output.exists():
        raise FileExistsError("Preserve previous outputs; select a fresh directory: " + str(output))
    if output == source or source in output.parents:
        raise ValueError("Output must not be inside the immutable source directory")

    source_names = [f"skin_{kind}.{tile}.png" for kind in ("diffuse", "roughness") for tile in TILES]
    source_names += [name for name, _, _ in COPIES]
    sources = {name: image_record(source / name) for name in source_names}
    output.mkdir(parents=True, exist_ok=False)
    atlas_size = min(args.max_size, 2048)
    tile_size = atlas_size // 2
    outputs = []
    for kind, colour_space in (("diffuse", "sRGB"), ("roughness", "Non-Color")):
        atlas = Image.new("RGB", (atlas_size, atlas_size), PADDING_RGB)
        profiles = []
        for tile, mapping in TILES.items():
            with Image.open(source / f"skin_{kind}.{tile}.png") as original:
                profiles.append(original.info.get("icc_profile"))
                cell = original.convert("RGB").resize((tile_size, tile_size), Image.Resampling.LANCZOS)
            # UV is bottom-left origin; Pillow paste positions are top-left origin.
            x = round(mapping["offset"][0] * atlas_size)
            y = round((1.0 - mapping["offset"][1]) * atlas_size) - tile_size
            atlas.paste(cell, (x, y))
        if len(set(profiles)) != 1:
            raise ValueError("Source skin tiles have differing ICC profiles; no implicit conversion allowed")
        path = output / f"skin_{kind}_atlas.png"
        save_png(atlas, path, profiles[0])
        record = image_record(path)
        record.update({"colour_space": colour_space, "source_files": [f"skin_{kind}.{tile}.png" for tile in TILES]})
        outputs.append(record)

    for name, cap, colour_space in COPIES:
        path = output / name
        limit = min(args.max_size, cap)
        with Image.open(source / name) as original:
            if max(original.size) <= limit:
                copy_unchanged = True
            else:
                copy_unchanged = False
                resized = original.copy()
                resized.thumbnail((limit, limit), Image.Resampling.LANCZOS)
                save_png(resized, path, original.info.get("icc_profile"))
        if copy_unchanged:
            shutil.copyfile(source / name, path)
        record = image_record(path)
        record.update({"colour_space": colour_space, "source_files": [name], "original_png_bytes_preserved": copy_unchanged})
        outputs.append(record)

    if args.config:
        recipe=json.loads(args.config.read_text(encoding='utf-8'))
        tints={'skin_darker_diffuse_atlas.png':('skin_diffuse_atlas.png',[.65,.58,.54]),'skin_upper_lip_diffuse_atlas.png':('skin_diffuse_atlas.png',[.90,.71,.68]),'skin_lower_lip_diffuse_atlas.png':('skin_diffuse_atlas.png',[.96,.80,.76]),'pants_tinted_diffuse.png':('pants_diffuse.png',recipe['materials']['pantsTint'])}
        for name,(base,factors) in tints.items():
            table=[]
            for factor in factors:
                for code in range(256):
                    v=code/255;linear=v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
                    linear*=factor;encoded=12.92*linear if linear<=.0031308 else 1.055*linear**(1/2.4)-.055
                    table.append(round(max(0,min(1,encoded))*255))
            with Image.open(output/base) as im:
                save_png(im.convert('RGB').point(table),output/name,im.info.get('icc_profile'))
            record=image_record(output/name);record.update({'colour_space':'sRGB','operation':'sRGB decode -> fixed existing linear tint -> sRGB encode, round to 8-bit','input_prepared_image':base,'linear_multiplier':factors});outputs.append(record)
    if len(outputs) != (17 if args.config else 13):
        raise AssertionError("The bounded PoC set must contain exactly 13 textures")
    for name, original in sources.items():
        if sha256(source / name) != original["sha256"]:
            raise RuntimeError("Source changed during preparation: " + name)
    for tile, mapping in TILES.items():
        mapping["atlas_pixel_origin_top_left"] = [
            round(mapping["offset"][0] * atlas_size),
            round((1.0 - mapping["offset"][1]) * atlas_size) - tile_size,
        ]
    manifest = {
        "schema": "male-neutral-a01-textures-v1",
        "license": "CC-BY-4.0",
        "credit": CREDIT,
        "source_url": SOURCE_URL,
        "license_url": LICENSE_URL,
        "modifications": "Skin UDIMs repacked/downsampled; selected maps downsized; optional existing linear tint multipliers baked to 8-bit sRGB for portable PBR.",
        "resampling": "Pillow LANCZOS on encoded channel values; no normal-vector renormalization. Fitting source maps retain exact PNG bytes.",
        "atlas_dimensions": [atlas_size, atlas_size],
        "tile_dimensions": [tile_size, tile_size],
        "padding_rgb": list(PADDING_RGB),
        "uv_formula": "atlas_uv = (source_uv - source_uv_origin) * scale + offset",
        "tiles": {str(tile): mapping for tile, mapping in TILES.items()},
        "source_files": sources,
        "output_files": outputs,
        "source_hashes_unchanged_after_processing": True,
        "pillow_version": Image.__version__,
    }
    (output / "atlas-mapping.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "textures": len(outputs), "atlas_dimensions": [atlas_size, atlas_size], "source_files_unchanged": True}))


if __name__ == "__main__":
    main()
