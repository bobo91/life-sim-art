"""Generate one bounded neighborhood and independently verify every delivered model."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from art_pipeline.validation import validate_glb,_read_glb
from building_validation import validate_building_glb
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def record(p):return {'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size}
SOURCES=tuple('scripts/'+n+'.py' for n in ('build_neighborhood','neighborhood_street','neighborhood_greenery','neighborhood_cafe','neighborhood_references','run_neighborhood','compose_neighborhood','package_neighborhood','building_validation'))
CONFIGS=('configs/neighborhood-assets.json','configs/neighborhood-layout.json','configs/neighborhood-reference-locks.json')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--blender',default=os.environ.get('BLENDER_BIN','blender'));p.add_argument('--output',required=True);a=p.parse_args()
    output=Path(a.output).resolve();output.relative_to(ROOT);replay=output.parent/(output.name+'-replay');profile=output.parent/(output.name+'-isolated-profile')
    for f in (output,replay,profile):
        if f.exists():raise FileExistsError('Preserve previous evidence '+f.name)
    profile.mkdir(parents=True)
    config=json.loads((ROOT/CONFIGS[0]).read_text());locks=json.loads((ROOT/CONFIGS[2]).read_text());sources={n:sha(ROOT/n) for n in (*SOURCES,*CONFIGS,*locks['sourceFilesSHA256'])}
    start=time.monotonic()
    for folder,extra in ((replay,['--geometry-only']),(output,[])):
        cmd=[a.blender,'--background','--factory-startup','--offline-mode','--disable-autoexec','--threads','4','--python-exit-code','1','--python',str(ROOT/'scripts/build_neighborhood.py'),'--','--output',str(folder),*extra]
        log=output.parent/(folder.name+'-private.log')
        with log.open('xb') as stream:r=subprocess.run(cmd,cwd=ROOT,env=dict(os.environ,BLENDER_USER_RESOURCES=str(profile),PYTHONHASHSEED='0'),stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
        if r.returncode or 'NEIGHBORHOOD_OK' not in log.read_text(encoding='utf-8',errors='replace'):raise RuntimeError('Build failed; inspect '+log.name)
    if sources!={n:sha(ROOT/n) for n in sources}:raise ValueError('Source changed during generation')
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    dirty=bool(subprocess.run(['git','status','--porcelain','--untracked-files=normal'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip())
    models={};results={};reproduced={}
    for c in config['assets']:
        asset=c['assetId'];folder=output/'assets'/asset;model=folder/(asset+'.glb');report=json.loads((folder/'build_report.json').read_text())
        metric=validate_building_glb(model,c['dimensionsMeters'],c['maxTriangles'],report['materials'],c['expectedBounds'])
        if len(report['materials'])>4:raise ValueError('Material budget exceeded')
        reproduced[asset]=sha(model)==sha(replay/'assets'/asset/(asset+'.glb'))
        if not reproduced[asset]:raise ValueError('Fresh geometry replay differs '+asset)
        m={'schema':'neighborhood-asset-manifest-1','assetId':asset,'version':'0.1.0','seed':c['seed'],'dimensionsMeters':c['dimensionsMeters'],'config':c,'geometry':metric,'blenderMeshHealth':report,
            'model':record(model),'sourceBlend':record(folder/(asset+'.blend')),'previews':{v:record(folder/(v+'.png')) for v in ('front','isometric')},'sourceHashes':sources,'sourceCommit':commit,'sourceDirty':dirty,
            'provenance':'Original procedural project geometry/materials; no external meshes, textures or fonts.','command':'python scripts/run_neighborhood.py --blender <Blender4.5.14> --output <fresh-directory>'}
        dump(folder/'manifest.json',m);models[asset]=dict(file='assets/'+asset+'/'+model.name,sha256=sha(model));results[asset]=metric
    refs={}
    for asset,lock in locks['references'].items():
        folder=output/'reference'/asset;model=folder/(asset+'.glb');report=json.loads((folder/'build_report.json').read_text());_,doc,_=_read_glb(model)
        if lock['kind']=='house':
            length=8 if asset=='walter-house' else 4;bb={'min':[-3.35,0,-length-.171],'max':[3.35,5.3,2.9]}
            g=validate_building_glb(model,[6.7,5.3,length+3.071],100000,[m['name'] for m in doc['materials']],bb)
        else:
            rc=json.loads((ROOT/lock['config']).read_text());g=validate_glb(model,rc['dimensionsMeters'],rc['maxTriangles'],[m['name'] for m in doc['materials']])
        m=dict(report,model=record(model),sourceBlend=record(folder/(asset+'.blend')),geometry=g)
        dump(folder/'manifest.json',m);refs[asset]=m;models[asset]=dict(file='reference/'+asset+'/'+model.name,sha256=sha(model))
    cafe=output/'assemblies/cafe-building.glb';_,doc,_=_read_glb(cafe);c=config['assemblies']['cafe-building']
    cafe_geometry=validate_building_glb(cafe,c['dimensionsMeters'],c['maxTriangles'],[m['name'] for m in doc['materials']],c['expectedBounds'])
    models['cafe-building']=dict(file='assemblies/cafe-building.glb',sha256=sha(cafe))
    layout=json.loads((output/'scene/layout.json').read_text())
    for asset,spec in layout['assetCatalog'].items():
        if spec['file']!=models[asset]['file']:raise ValueError('Scene asset path disagrees')
        spec['modelSHA256']=models[asset]['sha256']
    dump(output/'scene/layout.json',layout)
    presentation=json.loads((output/'presentation.json').read_text())
    for view in presentation['views'].values():
        if sha(output/'previews'/view['file'])!=view['sha256']:raise ValueError('Capture hash differs')
    validation={'status':'passed','newAssets':results,'references':{k:v['geometry'] for k,v in refs.items()},'freshGeometryReplayByteIdentical':reproduced,'cafe':cafe_geometry,'sceneTriangles':presentation['triangles'],
        'sceneInstances':presentation['instances'],'sourceHashes':sources,'sourceCommit':commit,'sourceDirty':dirty,'elapsedSeconds':round(time.monotonic()-start,3),
        'scope':'Actual mesh checks, independent GLB validation, source-pinned references, persistence, roundtrips and Blender renders. Route/obstacle regressions are geometric proposals; no Unity/nav/collision simulation.'}
    dump(output/'validation.json',validation)
    dump(output/'pack-manifest.json',{'schema':'neighborhood-pack-manifest-1','version':'0.1.0','sourceHashes':sources,'sourceCommit':commit,'sourceDirty':dirty,'newAssets':models,
        'assemblies':{'cafe-building':{'model':record(cafe),'sourceBlend':record(output/'assemblies/cafe-building.blend')}},
        'scene':{'sourceBlend':record(output/'scene/neighborhood.blend'),'layout':record(output/'scene/layout.json')},'presentationSHA256':sha(output/'presentation.json')})
    print(json.dumps({'status':'passed','newAssets':len(results),'references':len(refs),'sceneTriangles':presentation['triangles'],'sceneInstances':presentation['instances'],'elapsedSeconds':validation['elapsedSeconds']},indent=2))
if __name__=='__main__':main()
