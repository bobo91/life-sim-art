"""Verify an actual changed-seed bundle and exported semantic forward orientation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from art_pipeline.benchmark_checks import streetlamp_frame
from art_pipeline.validation import validate_bundle


def main():
    baseline, variant = (Path(value) for value in sys.argv[1:])
    manifests = []
    probes = []
    for directory in (baseline, variant):
        validate_bundle(directory)
        manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
        probes.append(streetlamp_frame(directory/manifest["model"]["file"], manifest["config"]))
        manifests.append(manifest)
    a, b = manifests
    config_a, config_b = (dict(item["config"]) for item in manifests)
    seed_a, seed_b = config_a.pop("seed"), config_b.pop("seed")
    if seed_a == seed_b or config_a != config_b:
        raise ValueError("Expected identical configs with different seeds")
    if a["sourceDigest"] != b["sourceDigest"] or a["model"]["sha256"] == b["model"]["sha256"]:
        raise ValueError("Changed seed must change actual GLB geometry for the same source")
    print(json.dumps({"status":"passed", "seedChangesGeometry":True, "exportedForwardProbes":probes}, indent=2))


if __name__ == "__main__":
    main()
