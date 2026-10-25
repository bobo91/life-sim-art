"""Bounded Walter pack build and independent GLB validation, based on main tools."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from art_pipeline.cli import normalize_png_metadata
from art_pipeline.validation import validate_glb,_read_glb

ASSETS=('prop_porch_bench_001','prop_flower_pot_001','prop_flower_pot_002','prop_welcome_mat_001',
    'prop_porch_lantern_001','prop_wooden_fence_001','prop_fence_post_001','prop_old_watering_can_001',
    'prop_wooden_crate_001','prop_porch_rocking_chair_001')
SOURCES=('scripts/build_walter_porch.py','scripts/run_walter_porch.py','scripts/props_walter.py','scripts/walter_common.py',
    'scripts/walter_mailbox_reference.py','art_pipeline/blender_build.py','art_pipeline/validation.py',
    'art_pipeline/config.py','art_pipeline/cli.py','art_pipeline/benchmark_checks.py')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--blender',default=os.environ.get('BLENDER_BIN','blender'))
    parser.add_argument('--output',required=True);parser.add_argument('--preflight',required=True)
    args=parser.parse_args();output,reference=(Path(p).resolve() for p in (args.output,args.preflight))
    for p in (output,reference):p.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve previous render results')
    sources={p:sha(ROOT/p) for p in SOURCES}
    configs={a:sha(ROOT/'configs'/(a+'.json')) for a in (*ASSETS,'walter-mailbox-reference')}
    profile=output.parent/(output.name+'-isolated-profile');profile.mkdir(parents=True,exist_ok=False)
    command=[args.blender,'--background','--factory-startup','--offline-mode','--disable-autoexec','--threads','4',
             '--python-exit-code','1','--python',str(ROOT/SOURCES[0]),'--','--output',str(output)]
    log=output.parent/(output.name+'-private.log');start=time.monotonic()
    with log.open('xb') as stream:
        process=subprocess.run(command,cwd=ROOT,env=dict(os.environ,BLENDER_USER_RESOURCES=str(profile),PYTHONHASHSEED='0'),
                               stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
    elapsed=round(time.monotonic()-start,3)
    dump(output.parent/(output.name+'-private-command.json'),{'command':command,'exitCode':process.returncode,
            'elapsedSeconds':elapsed,'sourceHashes':sources,'configHashes':configs})
    if process.returncode or 'WALTER_PORCH_BUILD_OK' not in log.read_text(encoding='utf-8',errors='replace'):
        raise RuntimeError('Walter build failed; inspect private log')
    if sources!={p:sha(ROOT/p) for p in SOURCES} or configs!={a:sha(ROOT/'configs'/(a+'.json')) for a in configs}:
        raise ValueError('Source/config changed during build')
    for p in output.rglob('*.png'):normalize_png_metadata(p)
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    dirty=bool(subprocess.run(['git','-c','core.excludesFile=','status','--porcelain','--untracked-files=normal'],
                             cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip())
    results={};replay={}
    for asset in ASSETS:
        folder=output/asset;model=folder/(asset+'.glb');c=json.loads((ROOT/'configs'/(asset+'.json')).read_text())
        report=json.loads((folder/'build_report.json').read_text())
        geometry=validate_glb(model,c['dimensionsMeters'],c['maxTriangles'],report['materials'])
        _,doc,_=_read_glb(model)
        if len(doc['nodes'])!=1 or any(k in doc['nodes'][0] for k in ('translation','rotation','scale','matrix','children')):
            raise ValueError('Expected one identity mesh node')
        if len(report['materials'])>4:raise ValueError('More than four material slots')
        digest=sha(model);old=sha(reference/(asset+'.glb'))
        replay[asset]={'sha256':digest,'preflightSHA256':old,'byteIdentical':digest==old}
        manifest={'schemaVersion':'1.0','assetId':asset,'version':c['version'],'requestId':'WALTER-PORCH-001',
            'units':'meters','pivot':'bottom-center','axes':{'sourceUp':'+Z','sourceForward':'-Y','exportUp':'+Y','exportForward':'+Z'},
            'dimensionsMeters':c['dimensionsMeters'],'config':c,'configSHA256':configs[asset],'seed':c['seed'],
            'sourceCommit':commit,'sourceDirty':dirty,'sourceFilesSHA256':sources,
            'sourceNote':'Exact source hashes identify actual build inputs; original local workspace may contain unrelated dirty files.',
            'geometry':geometry,'blenderMeshHealth':report,'model':{'file':model.name,'sha256':digest,'bytes':model.stat().st_size},
            'sourceBlend':{'file':asset+'.blend','sha256':sha(folder/(asset+'.blend'))},
            'previews':{n:{'file':n+'.png','sha256':sha(folder/(n+'.png'))} for n in ('front','isometric')},
            'provenance':{'method':'original-procedural-Blender-Python','thirdPartyAssets':[],'license':'original-project-content'},
            'tooling':{'blender':'4.5.14','renderer':'Cycles CPU','threads':4},
            'command':'python scripts/run_walter_porch.py --blender <Blender4.5.14> --preflight <fresh-geometry-preflight> --output <fresh-build-directory>',
            'status':'owner visual review required; no game integration'}
        dump(folder/'manifest.json',manifest);results[asset]=geometry
    if not all(v['byteIdentical'] for v in replay.values()):raise ValueError('Geometry replay mismatch')
    view=json.loads((output/'presentation.json').read_text())
    if not next(v for v in view['views'] if v['distanceMeters']==16)['allPropsInsideFrame']:raise ValueError('Default camera clips props')
    dump(output/'validation.json',{'status':'passed','assets':results,'geometryReplay':replay,'sourceHashes':sources,
        'configHashes':configs,'elapsedSeconds':elapsed,'originalMailboxSHA256':view['mailboxSHA256'],
        'scope':'Actual Blender mesh checks, save/reopen, GLB roundtrip, independent GLB validation and renders. No Unity import, collisions, seating, rocking or navigation tests.'})
    print(json.dumps({'status':'passed','elapsedSeconds':elapsed,'assets':{a:g['triangles'] for a,g in results.items()},
                     'allGeometryReplayByteIdentical':True},indent=2))


if __name__=='__main__':main()
