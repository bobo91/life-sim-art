"""Verify and package the bounded First Neighborhood review delivery."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.0'
VIEWS = ('overview.png', 'walter-street.png', 'cafe-terrace.png',
         'game-16m.png', 'walking-route.png', 'top-down.png')
CONFIGS = ('configs/neighborhood-assets.json', 'configs/neighborhood-layout.json',
           'configs/neighborhood-reference-locks.json')
DOCS = ('docs/neighborhood/IMPORT_HANDOFF.md', 'docs/neighborhood/DEPENDENCY_PINS.md',
        'reports/neighborhood-v0.1.0/quality-report.md',
        'reports/neighborhood-v0.1.0/technical-results.json',
        '.github/workflows/neighborhood.yml')
MAIN_TESTS = ('__init__.py', 'test_benchmark.py', 'test_cli.py',
              'test_config.py', 'test_validation.py')
ALLOWED = {'.py', '.json', '.png', '.blend', '.md', '.glb', '.yml'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(path):
    path = Path(path)
    path.resolve().relative_to(ROOT)
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing regular artifact input: '+path.relative_to(ROOT).as_posix())
    return path


def read_json(path):
    value = json.loads(require(path).read_text(encoding='utf-8'))
    def inspect(item):
        if isinstance(item, str) and (PurePosixPath(item).is_absolute() or PureWindowsPath(item).is_absolute()):
            raise ValueError('Absolute host path in packaged JSON: '+path.relative_to(ROOT).as_posix())
        if isinstance(item, dict):
            for child in item.values():inspect(child)
        elif isinstance(item, list):
            for child in item:inspect(child)
    inspect(value)
    return value


def record_file(folder, record, name):
    if not isinstance(record, dict) or record.get('file') != name:
        raise ValueError('Manifest filename mismatch: '+name)
    if sha(require(folder/name)) != record.get('sha256'):
        raise ValueError('Manifest SHA256 mismatch: '+(folder/name).relative_to(ROOT).as_posix())


def excluded(path):
    return (any(p in {'__pycache__', '.git', '.cache'} or 'private' in p.lower()
                or 'isolated-profile' in p.lower() for p in path.parts)
            or bool(re.search(r'\.blend\d+$', path.name))
            or path.suffix.lower() in {'.log', '.pyc', '.tmp'})


def source_path(name, pinned):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise ValueError('Invalid recorded source path')
    permitted = (name in pinned or name in CONFIGS or name in ('scripts/building_validation.py',)
                 or bool(re.fullmatch(r'scripts/[a-z_]*neighborhood[a-z_]*\.py', name))
                 or bool(re.fullmatch(r'art_pipeline/[a-z_]+\.py', name)))
    if not permitted:
        raise ValueError('Unrelated recorded source is outside this pack: '+name)
    return require(ROOT/name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True);parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source, output = ((ROOT/value).resolve() for value in (args.input, args.output))
    for path in (source, output):path.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve existing versioned archive')
    if source in output.parents:raise ValueError('Archive output must be outside the build input')
    validation = read_json(source/'validation.json')
    if validation.get('status') != 'passed':raise ValueError('Require completed successful neighborhood validation')
    pack = read_json(source/'pack-manifest.json')
    config = read_json(ROOT/CONFIGS[0]);read_json(ROOT/CONFIGS[1])
    locks = read_json(ROOT/CONFIGS[2])
    if config.get('version') != VERSION:raise ValueError('Unexpected neighborhood version')
    ids = {a['assetId'] for a in config['assets']}
    if not ids or len(ids) != len(config['assets']):raise ValueError('Require unique configured asset IDs')
    reference_ids = set(locks['references'])
    if len(reference_ids) != 21:raise ValueError('Require the twenty-one pinned existing references')
    for group, expected in (('assets', ids), ('reference', reference_ids)):
        folders = {p.name for p in (source/group).iterdir() if p.is_dir()}
        if folders != expected:raise ValueError('Asset inventory mismatch in '+group)
        for asset in sorted(expected):
            if not re.fullmatch(r'[a-z][a-z0-9_-]*', asset):raise ValueError('Invalid stable asset ID')
            folder = source/group/asset;m = read_json(folder/'manifest.json')
            if m.get('assetId') != asset:raise ValueError('Manifest asset ID mismatch')
            record_file(folder, m.get('model'), asset+'.glb')
            record_file(folder, m.get('sourceBlend'), asset+'.blend')
            if group == 'assets':
                for view in ('front', 'isometric'):record_file(folder, m.get('previews', {}).get(view), view+'.png')
            else:
                entry = locks['references'][asset];report = read_json(folder/'build_report.json')
                if report.get('referenceLockSHA256') != sha(ROOT/CONFIGS[2]) or not report.get('geometryRoundtrip'):
                    raise ValueError('Reference lock or roundtrip check failed: '+asset)
                if entry['kind'] == 'house':
                    if not entry.get('expectedWorldGeometrySHA256') or report.get('worldGeometrySHA256') != entry['expectedWorldGeometrySHA256']:
                        raise ValueError('House reference geometry fingerprint mismatch: '+asset)
                if entry['kind'] == 'prop' and m['model']['sha256'] != entry['approvedGLBSHA256']:
                    raise ValueError('Approved reference prop changed: '+asset)
    cafe = pack['assemblies']['cafe-building']
    record_file(source/'assemblies', cafe.get('model'), 'cafe-building.glb')
    record_file(source/'assemblies', cafe.get('sourceBlend'), 'cafe-building.blend')
    record_file(source/'scene', pack['scene'].get('sourceBlend'), 'neighborhood.blend')
    record_file(source/'scene', pack['scene'].get('layout'), 'layout.json')
    presentation = read_json(source/'presentation.json')
    if sha(source/'presentation.json') != pack.get('presentationSHA256'):raise ValueError('Presentation record changed')
    for name in VIEWS:record_file(source/'previews', presentation['views'][name.removesuffix('.png')], name)
    contact = read_json(source/'review/contact-layout.json')
    if sha(require(source/'review/contact-sheet.png')) != contact.get('outputSHA256'):raise ValueError('Contact sheet changed')
    hashes = pack.get('sourceHashes')
    if not isinstance(hashes, dict) or not hashes:raise ValueError('Pack manifest must record sourceHashes')
    pinned = locks['sourceFilesSHA256'];inputs = []
    for name, digest in {**pinned, **hashes}.items():
        path = source_path(name, pinned)
        if sha(path) != digest:raise ValueError('Generator input changed: '+name)
        if name in pinned and digest != pinned[name]:raise ValueError('Pinned source override: '+name)
        inputs.append(path)
    files = [p for p in source.rglob('*') if p.is_file() and not excluded(p)]
    files += inputs + [ROOT/name for name in (*CONFIGS, *DOCS)]
    files += list((ROOT/'art_pipeline').glob('*.py'))
    files += [ROOT/'tests'/name for name in MAIN_TESTS]
    files += [ROOT/'tests'/name for name in ('test_building_validation.py', 'test_modular_building.py') if (ROOT/'tests'/name).is_file()]
    files += list((ROOT/'tests').glob('test_neighborhood*.py'))
    files += list((ROOT/'reports/neighborhood-v0.1.0').glob('*.png'))
    files = sorted(set(require(p) for p in files))
    for path in files:
        if path.suffix.lower() not in ALLOWED:raise ValueError('Unexpected artifact extension: '+path.relative_to(ROOT).as_posix())
        if path.suffix == '.json':read_json(path)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    output.parent.mkdir(parents=True, exist_ok=True);index = []
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            data = path.read_bytes();name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0));info.compress_type = zipfile.ZIP_DEFLATED;info.external_attr = 0o100644 << 16
            archive.writestr(info, data);index.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or len(archive.infolist()) != len(index):raise ValueError('Archive read-back failed')
        for item in index:
            data = archive.read(item['path'])
            if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:raise ValueError('Archived bytes differ: '+item['path'])
    digest = sha(output)
    result = {'schema': 'neighborhood-review-artifact-1', 'version': VERSION,
              'sourceCommit': commit, 'githubSHA': os.environ.get('GITHUB_SHA'),
              'sourceHashes': {p.relative_to(ROOT).as_posix(): sha(p) for p in files if p.suffix in {'.py', '.yml'}},
              'sha256': digest, 'bytes': output.stat().st_size, 'files': index,
              'archiveReadBackVerified': True, 'scope': 'Owner visual review; no Unity/game integration or merge.'}
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n', encoding='utf-8')
    output.with_suffix('.zip.index.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('files', 'sourceHashes')}, indent=2))


if __name__ == '__main__':main()
