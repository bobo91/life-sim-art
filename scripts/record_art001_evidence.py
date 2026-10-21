"""Record executed ART-001 checks and copy small evidence, never generated GLB blobs."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT/"evidence/art-001"
    if output.exists():
        raise ValueError("Evidence already exists; preserve old results")
    checks = [
        ("unit-tests.txt", [sys.executable,"-m","unittest","discover","-s","tests","-v"]),
        ("reproducibility.json", [sys.executable,"-m","art_pipeline","compare","build/run-a","build/run-b"]),
        ("validation.json", [sys.executable,"-m","art_pipeline","validate","build/run-b"]),
        ("seed-and-orientation.json", [sys.executable,"scripts/verify_seed.py","build/run-a","build/run-seed"]),
    ]
    records = []
    output.mkdir(parents=True)
    for filename, command in checks:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        (output/filename).write_text(result.stdout+result.stderr, encoding="utf-8")
        records.append({"command":command, "exitCode":result.returncode, "output":filename})
        if result.returncode:
            raise ValueError(f"Check failed: {command}; see {output/filename}")
    for name in ("front.png","isometric.png"):
        shutil.copy2(ROOT/"build/run-b"/name, output/name)
    for run in ("run-a","run-b","run-seed"):
        shutil.copy2(ROOT/"build"/run/"manifest.json", output/(run+".manifest.json"))
    (output/"commands.json").write_text(json.dumps(records, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status":"passed", "checks":len(checks), "output":str(output)},indent=2))


if __name__ == "__main__":
    main()
