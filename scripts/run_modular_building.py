"""Reproduce and independently validate the bounded modular building pack."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from art_pipeline.cli import normalize_png_metadata
from art_pipeline.validation import validate_glb,_read_glb
from building_validation import validate_building_glb
SOURCES=tuple('scripts/'+n+'.py' for n in ('building_geometry','building_core','building_roof','building_openings','building_validation','build_modular_building','run_modular_building','compose_modular_building','package_modular_building','walter_common','props_walter','walter_mailbox_reference'))+tuple('art_pipeline/'+n+'.py' for n in ('blender_build','validation','cli','config','benchmark_checks'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def record(p):return {'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--blender',default=os.environ.get('BLENDER_BIN','blender'));p.add_argument('--output',required=True)
    p.add_argument('--validate-existing',action='store_true',help='Recheck existing evidence when only this validation runner changed; no geometry or render input may differ.');a=p.parse_args()
    out=Path(a.output).resolve();out.relative_to(ROOT)
    replay=out.parent/(out.name+'-replay');profile=out.parent/(out.name+'-isolated-profile')
    if not a.validate_existing:
        for folder in (out,replay,profile):
            if folder.exists():raise FileExistsError('Preserve previous evidence: '+folder.name)
        profile.mkdir(parents=True)
    c=json.loads((ROOT/'configs/modular-building.json').read_text())
    hashes={n:sha(ROOT/n) for n in (*SOURCES,'configs/modular-building.json')}
    configs={n.name:sha(n) for n in [*sorted((ROOT/'configs').glob('prop_*_001.json')),*sorted((ROOT/'configs').glob('prop_flower_pot_002.json'))] if n.stem in ('prop_porch_bench_001','prop_flower_pot_001','prop_flower_pot_002','prop_welcome_mat_001','prop_porch_lantern_001','prop_wooden_fence_001','prop_fence_post_001','prop_old_watering_can_001','prop_wooden_crate_001','prop_porch_rocking_chair_001')}
    configs['walter-mailbox-reference.json']=sha(ROOT/'configs/walter-mailbox-reference.json')
    hashes.update({'configs/'+n:v for n,v in configs.items()})
    render_hashes=hashes.copy()
    if a.validate_existing:
        first=out/'modules'/c['assets'][0]['assetId']/'manifest.json'
        previous=json.loads(first.read_text());render_hashes=previous.get('renderInputSourceHashes',previous['sourceHashes'])
        if set(render_hashes)!=set(hashes) or any(hashes[n]!=v for n,v in render_hashes.items() if n!='scripts/run_modular_building.py'):
            raise ValueError('A render/geometry input changed; require a fresh build')
        for asset in c['assets']:
            folder=out/'modules'/asset['assetId'];m=json.loads((folder/'manifest.json').read_text())
            for record_ in (m['model'],m['sourceBlend'],*m['previews'].values()):
                if sha(folder/record_['file'])!=record_['sha256']:raise ValueError('Existing module evidence was modified')
    start=time.monotonic()
    for target,extra in (() if a.validate_existing else ((replay,['--geometry-only']),(out,[]))):
        command=[a.blender,'--background','--factory-startup','--offline-mode','--disable-autoexec','--threads','4','--python-exit-code','1','--python',str(ROOT/'scripts/build_modular_building.py'),'--','--output',str(target),*extra]
        log=out.parent/(target.name+'-private.log')
        with log.open('xb') as stream:r=subprocess.run(command,cwd=ROOT,env=dict(os.environ,BLENDER_USER_RESOURCES=str(profile),PYTHONHASHSEED='0'),stdout=stream,stderr=subprocess.STDOUT,timeout=1500)
        if r.returncode or 'MODULAR_BUILDING_OK' not in log.read_text(encoding='utf-8',errors='replace'):raise RuntimeError('Blender failed; inspect '+log.name)
    if hashes!={n:sha(ROOT/n) for n in hashes}:raise ValueError('Sources changed during build')
    for image in out.rglob('*.png'):normalize_png_metadata(image)
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    dirty=bool(subprocess.run(['git','status','--porcelain','--untracked-files=normal'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip())
    results={};reproduced={}
    for asset in c['assets']:
        id=asset['assetId'];folder=out/'modules'/id;model=folder/(id+'.glb');r=json.loads((folder/'build_report.json').read_text())
        metrics=validate_building_glb(model,asset['dimensionsMeters'],asset['maxTriangles'],r['materials'],asset['expectedBounds'])
        if len(r['materials'])>4:raise ValueError('More than4materials')
        reproduced[id]=sha(model)==sha(replay/'modules'/id/(id+'.glb'))
        if not reproduced[id]:raise ValueError('Geometry replay differs '+id)
        manifest={'schema':'modular-module-manifest-1','assetId':id,'version':c['version'],'seed':asset['seed'],'config':asset,
            'dimensionsMeters':asset['dimensionsMeters'],'pivot':'authored-module-anchor','units':'meters','axes':{'sourceUp':'+Z','sourceFront':'-Y','exportUp':'+Y','exportFront':'+Z'},
            'model':record(model),'sourceBlend':record(folder/(id+'.blend')),'previews':{v:record(folder/(v+'.png')) for v in ('front','isometric')},
            'geometry':metrics,'blenderMeshHealth':r,'sourceCommit':commit,'sourceDirty':dirty,'sourceHashes':hashes,'renderInputSourceHashes':render_hashes,
            'provenance':'Original procedural project geometry and materials; no external meshes or textures','command':'python scripts/run_modular_building.py --blender <Blender4.5.14> --output <fresh-directory>'}
        dump(folder/'manifest.json',manifest);results[id]=metrics
    references={}
    for folder in sorted((out/'references').iterdir()):
        id=folder.name;model=folder/(id+'.glb');name='walter-mailbox-reference' if id=='prop_mailbox_001' else id
        rc=json.loads((ROOT/'configs'/(name+'.json')).read_text());r=json.loads((folder/'build_report.json').read_text())
        metrics=validate_glb(model,rc['dimensionsMeters'],rc['maxTriangles'],r['materials'])
        # Pinned exact approved/previous GLBs, independent of live local build paths.
        expected=c['referenceGLBSHA256'][id]
        if sha(model)!=expected:raise ValueError('Reference mesh/export changed '+id)
        references[id]={'assetId':id,'model':record(model),'sourceBlend':record(folder/(id+'.blend')),'geometry':metrics,'unchangedPinnedGLB':True}
        dump(folder/'manifest.json',references[id])
    view=json.loads((out/'presentation.json').read_text())
    for camera in view['views'].values():
        if sha(out/'previews'/camera['file'])!=camera['sha256']:raise ValueError('House render does not match its Blender capture record')
    if not view['alternate']['sharedMeshData'] or view['alternate']['newModuleIds']:raise ValueError('Alternate does not reuse same modules')
    # Assemblies contain many materials; use full shared validator via configured anchor.
    assemblies={}
    for name,length in (('walter',8),('alternate',4)):
        model=out/'assemblies'/(name+'-house.glb');_,doc,_=_read_glb(model)
        bounds={'min':[-3.35,0,-length-.171],'max':[3.35,5.30,2.90]}
        # Rear gable vent reaches+.171, beyond the foundation cap's+.16.
        materials=[m['name'] for m in doc['materials']]
        # Front gable/ridge tops actual5.30, steps frontY-2.90.
        dims=[bounds['max'][i]-bounds['min'][i] for i in range(3)]
        assemblies[name]=validate_building_glb(model,dims,250000,materials,bounds)
    status={'status':'passed','sourceHashes':hashes,'renderInputSourceHashes':render_hashes,'revalidatedExistingEvidence':a.validate_existing,'configHashes':configs,'sourceCommit':commit,'sourceDirty':dirty,'elapsedSeconds':round(time.monotonic()-start,3),
        'modules':results,'moduleGeometryReplayByteIdentical':reproduced,'references':references,'assemblies':assemblies,
        'limits':['No Unity import, URP appearance, runtime collision/navigation or gameplay tests.','Closed construction solids overlap at intended joints; no exhaustive intersection/UV/lightmap proof.']}
    dump(out/'validation.json',status)
    dump(out/'pack-manifest.json',{'schema':'modular-building-pack-manifest-1','version':c['version'],'sourceHashes':hashes,'modules':{k:v['sha256'] for k,v in results.items()},
        'assemblies':{n:record(out/'assemblies'/(n+'-house.glb')) for n in ('walter','alternate')},'referenceProps':references,'presentationSHA256':sha(out/'presentation.json'),'sourceCommit':commit,'sourceDirty':dirty,'status':'awaiting owner visual approval; no merge'})
    print(json.dumps({'status':'passed','modules':len(results),'referenceProps':len(references),'moduleTriangles':sum(v['triangles'] for v in results.values()),'elapsedSeconds':status['elapsedSeconds']},indent=2))
if __name__=='__main__':main()
