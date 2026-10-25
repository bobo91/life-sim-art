"""Remove private host details from public copies of measured prop evidence.

Raw build/audit reports remain local. This does not alter meshes, renders,
validation results, source/config hashes or measured timings.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_KEYS = {'os', 'platform', 'processor', 'logical_cpu_count', 'memory',
    'gpu_driver_metadata', 'cycles_reported_devices', 'python_executable'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', action='append', required=True)
    parser.add_argument('--blender', required=True)
    args = parser.parse_args()
    replacements = [(str(Path(args.blender).resolve()), '<BLENDER_4.5.14>'),
        (str(Path(sys.executable).resolve()), '<HOST_PYTHON>'),
        (str(ROOT), '<ART_REPO>'), (str(ROOT.parent/'life-sim-game'), '<GAME_REPO>'),
        (str(Path.home()), '<USER_HOME>')]
    replacements = sorted(set((a.replace('\\', '/'), b) for a,b in replacements), key=lambda pair: -len(pair[0]))
    changed = []

    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k,v in value.items() if k not in PRIVATE_KEYS}
        if isinstance(value, list): return [clean(v) for v in value]
        if isinstance(value, str):
            result = value
            for old,new in replacements:
                result = result.replace(old, new).replace(old.replace('/', '\\'), new)
            return result
        return value

    for name in args.directory:
        directory = Path(name).resolve(); directory.relative_to(ROOT)
        for path in sorted(directory.rglob('*')):
            if not path.is_file() or path.suffix not in ('.json','.md'): continue
            original = path.read_text(encoding='utf-8')
            if path.suffix == '.json':
                value = json.loads(original); result = clean(value)
                if result == value: continue
                result['publicationRedactions'] = 'Local executable/workspace/home paths and host hardware/OS metadata removed; technical measurements and hashes retained.'
                updated = json.dumps(result, indent=2, ensure_ascii=False)+'\n'
            else:
                updated = clean(original)
                if updated == original: continue
            path.write_text(updated, encoding='utf-8')
            changed.append(path.relative_to(ROOT).as_posix())
    print(json.dumps({'sanitizedCopies':changed, 'rawReports':'Retained locally; not uploaded.'},indent=2))


if __name__ == '__main__': main()
