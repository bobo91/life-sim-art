"""Package validated model bundles as local versioned artifacts, outside Git blobs."""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from art_pipeline.validation import validate_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    directory, output = Path(args.directory).resolve(), Path(args.output).resolve()
    validate_bundle(directory)
    if output.exists():
        raise ValueError("Artifact already exists; choose a new versioned filename")
    manifest = json.loads((directory/"manifest.json").read_text(encoding="utf-8"))
    files = [manifest["model"]["file"], "manifest.json", "front.png", "isometric.png", "build_report.json", "blender.log"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in sorted(files):
            # Fixed timestamp and permissions make packaging reproducible too.
            info = zipfile.ZipInfo(filename, date_time=(1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (directory/filename).read_bytes())
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix+".sha256").write_text(checksum+"  "+output.name+"\n",encoding="utf-8")
    print(json.dumps({"file":str(output),"sha256":checksum,"bytes":output.stat().st_size},indent=2))


if __name__ == "__main__":
    main()
