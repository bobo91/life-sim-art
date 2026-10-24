"""Build and independently validate the two original First Playable quality props."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from art_pipeline.cli import normalize_png_metadata
from art_pipeline.validation import validate_glb, _accessor, _read_glb

ASSETS = ('prop_mailbox_001', 'prop_cafe_table_001')
SOURCES = ['scripts/build_first_playable_props.py', 'scripts/run_first_playable_props.py',
    'scripts/props_mailbox.py', 'scripts/props_cafe_table.py',
    'art_pipeline/blender_build.py', 'art_pipeline/validation.py', 'art_pipeline/config.py', 'art_pipeline/cli.py',
    'art_pipeline/benchmark_checks.py']


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path, value): Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--blender', default=os.environ.get('BLENDER_BIN', 'blender'))
    args = parser.parse_args()
    output = Path(args.output).resolve(); output.relative_to(ROOT)
    if output.exists(): raise FileExistsError('Choose a new output directory')
    profile = ROOT/'build/first-playable-props/isolated-profile'; profile.mkdir(parents=True, exist_ok=True)
    sources = {name: sha(ROOT/name) for name in SOURCES}
    source_digest = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    source_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    source_dirty = bool(subprocess.run(['git', '-c', 'core.excludesFile=', 'status', '--porcelain', '--untracked-files=normal'],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip())
    command = [args.blender, '--background', '--factory-startup', '--offline-mode', '--disable-autoexec',
        '--threads', '4', '--python-exit-code', '1', '--python', str(ROOT/SOURCES[0]), '--', '--output', str(output)]
    env = dict(os.environ, BLENDER_USER_RESOURCES=str(profile), PYTHONHASHSEED='0')
    output.parent.mkdir(parents=True, exist_ok=True)
    logpath = output.parent/(output.name+'-launcher.log')
    record = {'startedUTC': datetime.now(timezone.utc).isoformat(), 'command': command,
        'environment': {'BLENDER_USER_RESOURCES': str(profile), 'PYTHONHASHSEED': '0'},
        'sourceCommit': source_commit, 'sourceDirty': source_dirty, 'sourceFilesSHA256': sources,
        'sourceDigest': source_digest}
    start = time.monotonic()
    with logpath.open('wb') as log:
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
    record.update({'exitCode': completed.returncode, 'elapsedSeconds': round(time.monotonic()-start, 3)})
    dump(output.parent/(output.name+'-command.json'), record)
    if completed.returncode or 'FIRST_PLAYABLE_PROPS_OK' not in logpath.read_text(encoding='utf-8', errors='replace'):
        raise RuntimeError('Blender failed; see '+str(logpath))
    if {name: sha(ROOT/name) for name in SOURCES} != sources:
        raise RuntimeError('A generator changed during the build')
    all_results = {}
    for asset_id in ASSETS:
        config_path = ROOT/'configs'/(asset_id+'.json')
        config = json.loads(config_path.read_text(encoding='utf-8'))
        directory = output/asset_id
        report = json.loads((directory/'build_report.json').read_text(encoding='utf-8'))
        for name in ('front', 'isometric'): normalize_png_metadata(directory/(name+'.png'))
        model = directory/(asset_id+'.glb')
        geometry = validate_glb(model, config['dimensionsMeters'], config['maxTriangles'], report['materials'])
        _, document, binary = _read_glb(model)
        nodes = document['nodes']
        if len(nodes) != 1 or any(k in nodes[0] for k in ('matrix','translation','rotation','scale','children')):
            raise ValueError('Require one identity-transform mesh at the origin')
        forward = {'source': '-Y', 'export': '+Z', 'identityMeshOrigin': True}
        if 'forwardProbeSourcePoint' in report:
            x,y,z = report['forwardProbeSourcePoint']; expected = (x,z,-y)
            points = []
            for primitive in document['meshes'][0]['primitives']:
                positions, _ = _accessor(document, binary, primitive['attributes']['POSITION'], 'VEC3', {5126})
                points.extend(positions)
            nearest = min(math.dist(expected, p) for p in points)
            if nearest > .0001 or expected[2] <= 0: raise ValueError('Mailbox front feature failed export orientation')
            forward.update({'feature': 'front door vertex', 'expectedExportXYZ': expected, 'nearestVertexErrorMeters': nearest})
        else: forward['limitation'] = 'Symmetric table has no unique semantic front feature'
        manifest = {'schemaVersion':'1.0', 'assetId':asset_id, 'requestId':config['requestId'], 'version':config['version'],
            'category':'prop', 'seed':config['seed'], 'units':'meters', 'pivot':'bottom-center',
            'axes':{'sourceUp':'+Z','sourceForward':'-Y','exportUp':'+Y','exportForward':'+Z'},
            'dimensionsMeters':config['dimensionsMeters'], 'maxTriangles':config['maxTriangles'],
            'sourceCommit':source_commit, 'sourceDirty':source_dirty, 'sourceDigest':source_digest, 'sourceFilesSHA256':sources,
            'sourceNote':'Exact source-file hashes identify the build inputs; sourceDirty records tracked or untracked workspace changes.',
            'config':config, 'configSHA256':sha(config_path), 'geometry':geometry, 'blenderMeshHealth':report,
            'forwardProbe':forward, 'model':{'file':model.name,'sha256':sha(model),'bytes':model.stat().st_size},
            'provenance':{'method':'procedural-blender-python','thirdPartyAssets':[], 'license':'original-project-content', 'generator':SOURCES[0]},
            'tooling':{'blender':'4.5.14','engine':'Cycles','device':'CPU','threads':4},
            'previews':{n:{'file':n+'.png','sha256':sha(directory/(n+'.png'))} for n in ('front','isometric')},
            'sourceBlend':{'file':asset_id+'.blend','sha256':sha(directory/(asset_id+'.blend'))},
            'command':'python scripts/run_first_playable_props.py --blender <Blender-4.5.14> --output <new-workspace-directory>',
            'status':'quality proof awaiting owner visual review; not game integrated'}
        dump(directory/'manifest.json',manifest)
        all_results[asset_id] = geometry
    for name in ('game_distance_6m','game_distance_16m','game_distance_30m','game_distance_16m_yaw225'):
        normalize_png_metadata(output/(name+'.png'))
    dump(output/'validation.json',{'status':'passed','assets':all_results,
        'scope':'Independent actual GLB validation, Blender geometry/save/reopen/roundtrip; no Unity importer/render test'})
    print(json.dumps({'status':'passed','output':str(output),'elapsedSeconds':record['elapsedSeconds'],'assets':all_results},indent=2))


if __name__ == '__main__': main()
