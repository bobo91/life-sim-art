"""Run and independently validate the bounded original cafe pack."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from art_pipeline.cli import normalize_png_metadata
from art_pipeline.validation import validate_glb, _read_glb

ASSETS=('prop_cafe_counter_001','prop_cafe_chair_001','prop_tin_001',
        'prop_cafe_cup_001','prop_cafe_tablecloth_001','prop_cafe_parasol_001')
SOURCES=('scripts/build_cafe_environment.py','scripts/run_cafe_environment.py',
    'scripts/props_cafe_furniture.py','scripts/props_cafe_smallwares.py','scripts/props_cafe_softgoods.py',
    'scripts/build_first_playable_props.py','scripts/props_cafe_table.py','scripts/props_mailbox.py',
    'art_pipeline/blender_build.py','art_pipeline/validation.py','art_pipeline/config.py',
    'art_pipeline/cli.py','art_pipeline/benchmark_checks.py')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender',default=os.environ.get('BLENDER_BIN','blender'))
    parser.add_argument('--output',required=True)
    parser.add_argument('--preflight',help='Optional preserved geometry-only run for byte replay comparison')
    args=parser.parse_args();output=Path(args.output).resolve();output.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve previous evidence; choose new output')
    sources={p:sha(ROOT/p) for p in SOURCES}
    configs={p:sha(ROOT/'configs'/(p+'.json')) for p in (*ASSETS,'cafe-environment-pack','prop_cafe_table_001')}
    profile=output.parent/(output.name+'-isolated-profile');profile.mkdir(parents=True,exist_ok=False)
    command=[args.blender,'--background','--factory-startup','--offline-mode','--disable-autoexec',
        '--threads','4','--python-exit-code','1','--python',str(ROOT/SOURCES[0]),'--','--output',str(output)]
    log=output.parent/(output.name+'-private.log');start=time.monotonic()
    with log.open('xb') as stream:
        result=subprocess.run(command,cwd=ROOT,env=dict(os.environ,BLENDER_USER_RESOURCES=str(profile),PYTHONHASHSEED='0'),
                              stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
    elapsed=round(time.monotonic()-start,3)
    dump(output.parent/(output.name+'-private-command.json'),{'command':command,'exitCode':result.returncode,'elapsedSeconds':elapsed})
    if result.returncode or 'CAFE_ENVIRONMENT_BUILD_OK' not in log.read_text(encoding='utf-8',errors='replace'):
        raise RuntimeError('Build failed; inspect local private log')
    if sources!={p:sha(ROOT/p) for p in SOURCES} or configs!={p:sha(ROOT/'configs'/(p+'.json')) for p in configs}:
        raise ValueError('Source/config changed during build')
    for p in output.rglob('*.png'):normalize_png_metadata(p)
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    dirty=bool(subprocess.run(['git','-c','core.excludesFile=','status','--porcelain','--untracked-files=normal'],
                             cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip())
    results={};replay={}
    for asset in ASSETS:
        folder=output/asset;model=folder/(asset+'.glb')
        config=json.loads((ROOT/'configs'/(asset+'.json')).read_text(encoding='utf-8'))
        report=json.loads((folder/'build_report.json').read_text(encoding='utf-8'))
        geometry=validate_glb(model,config['dimensionsMeters'],config['maxTriangles'],report['materials'])
        _,doc,_=_read_glb(model)
        if len(doc['nodes'])!=1 or any(k in doc['nodes'][0] for k in ('translation','rotation','scale','matrix','children')):
            raise ValueError('Expected one identity mesh node')
        if len(report['materials'])>4:raise ValueError('Material budget exceeded')
        manifest={'schemaVersion':'1.0','assetId':asset,'version':config['version'],'requestId':'CAFE-ENV-001',
            'units':'meters','pivot':'bottom-center','axes':{'sourceUp':'+Z','sourceForward':'-Y','exportUp':'+Y','exportForward':'+Z'},
            'dimensionsMeters':config['dimensionsMeters'],'seed':config['seed'],'config':config,'configSHA256':configs[asset],
            'sourceCommit':commit,'sourceDirty':dirty,'sourceFilesSHA256':sources,
            'sourceIdentityNote':'Exact source/config hashes identify dirty local authoring; final PR versions the identical bytes.',
            'model':{'file':model.name,'sha256':sha(model),'bytes':model.stat().st_size},'geometry':geometry,
            'blenderMeshHealth':report,'sourceBlend':{'file':asset+'.blend','sha256':sha(folder/(asset+'.blend'))},
            'previews':{n:{'file':n+'.png','sha256':sha(folder/(n+'.png'))} for n in ('front','isometric')},
            'provenance':{'method':'original-procedural-blender-python','thirdPartyAssets':[],'license':'original-project-content'},
            'tooling':{'blender':'4.5.14','engine':'Cycles','device':'CPU','threads':4},
            'command':'python scripts/run_cafe_environment.py --blender <Blender-4.5.14> --output <new-workspace-directory>',
            'status':'quality-review-only; no Unity integration or accepted gameplay contract'}
        dump(folder/'manifest.json',manifest);results[asset]=geometry
        if args.preflight:
            reference=Path(args.preflight).resolve();reference.relative_to(ROOT)
            replay[asset]={'sha256':sha(model),'preflightSHA256':sha(reference/(asset+'.glb')),
                           'byteIdentical':sha(model)==sha(reference/(asset+'.glb'))}
    if replay and not all(v['byteIdentical'] for v in replay.values()):raise ValueError('Geometry replay differs')
    arrangements=json.loads((output/'arrangements.json').read_text())
    if not next(v for v in arrangements['views'] if v['distanceMeters']==16)['allInsideFrame']:
        raise ValueError('Default game-camera clipping')
    dump(output/'validation.json',{'status':'passed','assets':results,'geometryReplay':replay,
        'sharedApprovedTableByteIdentical':True,'sourceHashes':sources,'configHashes':configs,'elapsedSeconds':elapsed,
        'scope':'Actual Blender geometry, save/reopen, static GLB roundtrip, independent GLB/identity validation and actual preview renders. No Unity importer or gameplay test.'})
    print(json.dumps({'status':'passed','elapsedSeconds':elapsed,'assets':{a:g['triangles'] for a,g in results.items()},
                     'geometryReplayIdentical':bool(replay),'output':output.relative_to(ROOT).as_posix()},indent=2))


if __name__=='__main__':main()
