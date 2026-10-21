"""Copy actual ART-002 evidence while keeping generated GLB files out of Git."""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from art_pipeline.validation import validate_bundle
from scripts.render_benchmark import PALETTES, compare_manifests, geometry_fingerprint


def main():
    source, output = ROOT/"build/art-002", ROOT/"evidence/art-002"
    if output.exists():
        raise ValueError("Evidence already exists; preserve old results")
    manifests, configs, hashes, validation = {}, {}, {}, {}
    for name in PALETTES:
        bundle = source/name
        validation[name] = validate_bundle(bundle)
        manifests[name] = json.loads((bundle/"manifest.json").read_text(encoding="utf-8"))
        configs[name] = json.loads((source/"configs"/(name+".json")).read_text(encoding="utf-8"))
        hashes[name] = geometry_fingerprint(bundle/manifests[name]["model"]["file"])
    controls = compare_manifests(manifests, configs, hashes)
    recorded = json.loads((source/"comparison.json").read_text(encoding="utf-8"))
    if any(recorded[key] != value for key, value in controls.items()):
        raise ValueError("Recorded comparison disagrees with independent recheck")
    output.mkdir(parents=True)
    shutil.copytree(source/"configs", output/"configs")
    for name in PALETTES:
        (output/name).mkdir()
        for image in ("front.png", "isometric.png"):
            shutil.copy2(source/name/image, output/name/image)
        shutil.copy2(source/name/"manifest.json", output/name/"manifest.record.json")
    shutil.copy2(source/"comparison.json", output/"comparison.record.json")
    shutil.copy2(source/"unit-tests.txt", output/"unit-tests.txt")
    (output/"validation.json").write_text(json.dumps(validation,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"passed","sameGeometry":True,"output":str(output)},indent=2))


if __name__ == "__main__":
    main()
