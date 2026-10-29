"""Layout actual B04 gate images only: no recolouring, synthesis or retouch."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def font(size):
    for name in ("DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source, out = Path(args.input), Path(args.out)
    assert not out.exists(), "Choose a fresh output directory"
    out.mkdir(parents=True)
    versions = ("B02", "B03", "B04")
    poses = ("idle", "walk", "run25", "flex45", "flex90", "flex120")
    records = []
    for version in versions:
        for path in sorted((source / version).glob("*.png")):
            dest = out / "native" / version / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            records.append({"path": f"native/{version}/{path.name}",
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    assert len(records) == 75

    def sheet(name, rows, tile):
        # Each row is the same camera/pose/side for all three versions.
        width, height = tile
        image = Image.new("RGB", (width * 3, (height + 32) * len(rows) + 72), (34, 39, 42))
        draw = ImageDraw.Draw(image)
        for j, (filename, label) in enumerate(rows):
            for i, version in enumerate(versions):
                with Image.open(source / version / filename) as native:
                    tile_image = native.convert("RGB").resize(tile, Image.Resampling.LANCZOS)
                    image.paste(tile_image, (i * width, j * (height + 32)))
                draw.text((i * width + 8, j * (height + 32) + height + 5),
                          f"{version} | {label}", font=font(18), fill=(235, 230, 216))
        y = (height + 32) * len(rows)
        draw.text((12, y + 8), "Actual Blender Cycles | identical pose, camera, lights | B04 visual NO-GO",
                  font=font(17), fill=(235, 230, 216))
        draw.text((12, y + 38), "Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified",
                  font=font(16), fill=(205, 209, 201))
        image.save(out / name)

    for side in ("L", "R"):
        for angle in ("front", "outer"):
            rows = [(f"{pose}_{side}_{angle}.png", f"{pose} {side} {angle}") for pose in poses]
            sheet(f"all-poses-{side}-{angle}.png", rows, (400, 400))
    sheet("run25-both-elbows.png",
          [(f"run25_{side}_{angle}.png", f"run25% {side} {angle}")
           for angle in ("front", "outer") for side in ("L", "R")], (480, 480))
    sheet("game16m-comparison.png", [("game16m.png", "50deg / 16m art camera proxy")], (960, 540))
    metadata = {"schema": "male-b04-layout-1", "sourceImages": records,
                "processing": "Equal proportional resizing, labels and layout only; native images copied byte-for-byte.",
                "versions": versions, "poseRows": poses, "visualGo": False,
                "gameCamera": "50deg pitch, 16m distance, 40deg vertical FOV; art proxy, not game project"}
    (out / "layout.json").write_bytes((json.dumps(metadata, indent=2) + "\n").encode())
    print(json.dumps({"nativeImages": len(records), "sheets": 6}))


if __name__ == "__main__":
    main()
