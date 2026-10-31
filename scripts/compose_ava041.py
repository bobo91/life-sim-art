"""Package actual ART-041 renders without cropping, retouching or color changes.

Usage: python scripts/compose_ava041.py --build build/ava041-final-001 --out evidence/ava041
Pillow is the only non-standard-library dependency. Game frames retain 1280x720
native pixels; the 1200-pixel preview cap applies to the other standalone views.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont


VIEWS = (
    "front", "side", "back", "three_quarter", "isometric", "face_front",
    "face_three_quarter", "cafe_daylight_full", "cafe_daylight_face",
    "game_16m_front", "game_16m_back", "ava_a03_same_scale",
)
GAME_VIEWS = {"game_16m_front", "game_16m_back"}
CREDIT = (
    "A03 comparison: modified Snow v4 | Snow Rig (CC) Blender Foundation | studio.blender.org",
    "CC BY 4.0: https://creativecommons.org/licenses/by/4.0/",
    "Source: https://studio.blender.org/characters/snow/v4/ | Ava: original procedural ART-041 candidate",
)
PAPER = (237, 235, 230)
INK = (43, 46, 45)
GUTTER = (126, 129, 131)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dimensions(path):
    with Image.open(path) as opened:
        return list(opened.size)


def font(size, bold=False):
    names = (["C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold else
             ["C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"])
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def opaque_rgb(path):
    with Image.open(path) as source:
        if source.mode in {"RGBA", "LA"} and source.getchannel("A").getextrema() != (255, 255):
            raise ValueError(f"Unexpected transparency; cannot flatten without changing colors: {path}")
        return source.convert("RGB")


def fit(image, max_width, max_height=None):
    scale = min(1, max_width / image.width,
                max_height / image.height if max_height else 1)
    size = (round(image.width * scale), round(image.height * scale))
    return image if size == image.size else image.resize(size, Image.Resampling.LANCZOS)


def label(draw, xy, text, size=18, bold=False):
    draw.text(xy, text, fill=INK, font=font(size, bold))


def write_image(image, path):
    image.save(path, format="PNG", optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source_dir = args.build / "renders"
    output = args.out / "previews"
    sources = {name: source_dir / (name + ".png") for name in VIEWS}
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("All twelve actual renders are required: " + ", ".join(missing))
    source_hashes = {name: sha(path) for name, path in sources.items()}
    output.mkdir(parents=True, exist_ok=True)
    records = []

    def record(name, path, image_size, operation, source_names, extra=None):
        item = {
            "path": path.relative_to(args.out).as_posix(),
            "sha256": sha(path), "bytes": path.stat().st_size,
            "dimensions": list(image_size), "operation": operation,
            "sources": [{"name": n, "path": (Path("renders") / (n + ".png")).as_posix(),
                         "sha256": source_hashes[n],
                         "dimensions": dimensions(sources[n])} for n in source_names],
            "crop": None, "retouch": False, "sourceColorAdjustment": False,
        }
        if extra:
            item.update(extra)
        records.append(item)

    for name, source in sources.items():
        destination = output / (name + ".png")
        with Image.open(source) as opened:
            size = opened.size
        if name in GAME_VIEWS:
            if size != (1280, 720):
                raise ValueError(f"Expected native game frame 1280x720, received {size}: {source}")
            shutil.copyfile(source, destination)
            record(name, destination, size, "byte-identical native game frame", [name])
        elif name == "ava_a03_same_scale":
            image = fit(opaque_rgb(source), 1200)
            footer_height = 100
            canvas = Image.new("RGB", (image.width, image.height + footer_height), PAPER)
            canvas.paste(image, (0, 0))
            draw = ImageDraw.Draw(canvas)
            label(draw, (18, image.height + 10), "AVA MORGAN + A03 | Same scale, unchanged A03 reference", 18, True)
            for index, line in enumerate(CREDIT):
                label(draw, (18, image.height + 37 + index * 18), line, 13)
            write_image(canvas, destination)
            record(name, destination, canvas.size, "proportional downsample plus separate attribution footer", [name],
                   {"renderRectangle": [0, 0, image.width, image.height], "credit": list(CREDIT)})
        elif size[0] <= 1200:
            shutil.copyfile(source, destination)
            record(name, destination, size, "byte-identical standalone preview", [name])
        else:
            image = fit(opaque_rgb(source), 1200)
            write_image(image, destination)
            record(name, destination, image.size, "proportional downsample only", [name])

    # A uniform three-view contact sheet: complete frames, equal proportional size.
    width, margin, gap, title_height, label_height, footer_height = 1200, 20, 14, 62, 34, 42
    panel_width = (width - 2 * margin - 2 * gap) // 3
    panels = [(name, fit(opaque_rgb(sources[name]), panel_width)) for name in ("front", "side", "back")]
    image_height = max(image.height for _, image in panels)
    canvas = Image.new("RGB", (width, title_height + label_height + image_height + footer_height), GUTTER)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, title_height - 1), fill=PAPER)
    label(draw, (20, 12), "AVA MORGAN | Phase A visual candidate", 25, True)
    label(draw, (20, 41), "Actual Blender renders | Complete frames | Owner visual approval pending", 14)
    rectangles = []
    for index, (name, image) in enumerate(panels):
        x = margin + index * (panel_width + gap)
        draw.rectangle((x, title_height, x + panel_width - 1, title_height + label_height - 1), fill=PAPER)
        label(draw, (x + 12, title_height + 6), {"front": "FRONT", "side": "SIDE", "back": "BACK"}[name], 18, True)
        y = title_height + label_height
        canvas.paste(image, (x + (panel_width - image.width) // 2, y))
        rectangles.append({"source": name, "renderRectangle": [x, y, image.width, image.height]})
    y = canvas.height - footer_height
    draw.rectangle((0, y, width, canvas.height), fill=PAPER)
    label(draw, (20, y + 12), "ART-041 | Original procedural geometry | Static candidate; no rig or animation approval", 15)
    destination = output / "turnaround.png"
    write_image(canvas, destination)
    record("turnaround", destination, canvas.size, "labelled contact sheet; proportional full-frame downsample", [n for n, _ in panels],
           {"panels": rectangles})

    # Preserve both game frames exactly at native resolution in a vertical pair.
    title_height, label_height, footer_height = 60, 34, 40
    canvas = Image.new("RGB", (1280, title_height + 2 * (label_height + 720) + footer_height), PAPER)
    draw = ImageDraw.Draw(canvas)
    label(draw, (18, 10), "AVA MORGAN | Normal game-camera distance", 25, True)
    label(draw, (18, 39), "Blender camera proxy | 16 m distance, 50 degree elevation, 40 degree vertical FOV | Native 1280 x 720 frames", 14)
    rectangles = []
    for index, name in enumerate(("game_16m_front", "game_16m_back")):
        top = title_height + index * (label_height + 720)
        label(draw, (18, top + 6), "FRONT" if index == 0 else "BACK", 18, True)
        image = opaque_rgb(sources[name])
        canvas.paste(image, (0, top + label_height))
        rectangles.append({"source": name, "renderRectangle": [0, top + label_height, 1280, 720]})
    label(draw, (18, canvas.height - 28), "Complete, unretouched frames; no crop or enlargement. This is not a Unity integration test.", 15)
    destination = output / "game-camera-pair.png"
    write_image(canvas, destination)
    record("game-camera-pair", destination, canvas.size, "labelled vertical pair; native source pixels unchanged", ["game_16m_front", "game_16m_back"],
           {"panels": rectangles})

    if {name: sha(path) for name, path in sources.items()} != source_hashes:
        raise RuntimeError("Source renders changed while composing previews")
    # Pixel checks establish that copies and native game panels were not retouched.
    for item in records:
        if item["operation"].startswith("byte-identical") and item["sha256"] != item["sources"][0]["sha256"]:
            raise RuntimeError("Preview copy hash differs from source")
    with Image.open(output / "game-camera-pair.png") as pair:
        for rect in rectangles:
            x, y, w, h = rect["renderRectangle"]
            if pair.crop((x, y, x + w, y + h)).tobytes() != opaque_rgb(sources[rect["source"]]).tobytes():
                raise RuntimeError("Native game-frame panel pixels changed")
    manifest = {
        "schema": "ava-art041-preview-transforms-1", "sourceBuild": args.build.as_posix(),
        "renderInputs": 12, "previewImages": len(records),
        "policy": "Complete source frames; no crop, retouch, source-color adjustment or enlargement. Game frames remain native 1280x720; other standalone previews at most 1200 pixels wide.",
        "resampling": "Pillow LANCZOS for proportional downsamples only",
        "a03ComparisonAttribution": list(CREDIT), "files": records,
        "checks": {"sourceHashesUnchanged": True, "byteCopyHashesMatch": True, "nativeGamePanelPixelsMatch": True},
    }
    manifest_path = args.out / "preview-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sourceRenders": 12, "previewImages": len(records),
                      "previewBytes": sum(r["bytes"] for r in records),
                      "manifest": manifest_path.as_posix(), "output": output.as_posix(),
                      "checks": manifest["checks"]}, indent=2))


if __name__ == "__main__":
    main()
