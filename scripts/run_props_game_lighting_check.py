"""Prepare/run one pinned, isolated game-lighting verification; never open the game repo."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
GAME_COMMIT='9a85db5cb69ccf01ae584f42c9237703be4e2327'
SNAPSHOT_SHA='001063dba9be7403067354596460cf60c6837fdfa24fa3acecb3212f66d4ebf3'
ASSETS={'prop_mailbox_001':'b243a55a5d92da3cd3a51c3957d0b1e1f1b9737ad8f6ed988121bae69e654698',
    'prop_cafe_table_001':'6e122d9a172952fe237e9b24fe9c94b4eff70151e346f3ead95803a86a71ee54'}
SCENE='Assets/LifeSim/Scenes/Bootstrap.unity'
CHECKER='scripts/PropsGameLightingCheck.cs'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def under(value):p=Path(value).resolve();p.relative_to(ROOT);return p

def prepare(args,project,output):
    snapshot=under(args.snapshot);source=under(args.input)
    if project.exists() or output.exists():raise FileExistsError('Preserve previous project/results; choose fresh paths')
    if sha(snapshot)!=SNAPSHOT_SHA:raise ValueError('Pinned game snapshot hash mismatch')
    project.mkdir(parents=True);output.mkdir(parents=True)
    with zipfile.ZipFile(snapshot) as archive:
        for item in archive.infolist():
            path=(project/item.filename).resolve();path.relative_to(project)
            if item.is_dir():continue
            if item.filename.split('/')[0] not in ('Assets','Packages','ProjectSettings'):raise ValueError('Unexpected snapshot root')
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(item))
    baseline={p.relative_to(project).as_posix():sha(p) for p in project.rglob('*') if p.is_file()}
    package=project/'Packages/manifest.json';manifest=json.loads(package.read_text(encoding='utf-8'))
    if manifest['dependencies']['com.unity.render-pipelines.universal']!='17.5.0':raise ValueError('Pinned URP mismatch')
    manifest['dependencies']['com.unity.cloud.gltfast']='6.20.0';dump(package,manifest)
    (project/'Assets/Editor').mkdir(parents=True,exist_ok=True);(project/'Inputs').mkdir()
    shutil.copy2(ROOT/CHECKER,project/'Assets/Editor/PropsGameLightingCheck.cs')
    expected=[]
    for asset_id,digest in ASSETS.items():
        model=source/asset_id/(asset_id+'.glb');asset=json.loads((source/asset_id/'manifest.json').read_text(encoding='utf-8'))
        if sha(model)!=digest or asset['model']['sha256']!=digest:raise ValueError('Reviewed model changed')
        raw=model.read_bytes();size,kind=struct.unpack_from('<II',raw,12);document=json.loads(raw[20:20+size])
        expected.append({'id':asset_id,'dimensions':asset['dimensionsMeters'],'triangles':asset['geometry']['triangles'],
            'frontPoint':asset['forwardProbe'].get('expectedExportXYZ',[]),
            'materials':[{'name':m['name'],'baseColor':m['pbrMetallicRoughness']['baseColorFactor'],
                'metallic':m['pbrMetallicRoughness']['metallicFactor'],'roughness':m['pbrMetallicRoughness']['roughnessFactor']}for m in document['materials']]})
        shutil.copy2(model,project/'Inputs'/(asset_id+'.glb'))
    config={'sourceGameCommit':GAME_COMMIT,'sourceArchiveSHA256':SNAPSHOT_SHA,'scenePath':SCENE,
        'urpAssetPath':'Assets/LifeSim/Settings/LifeSim_URP.asset','tablePosition':[14.2,0,-6.5],'assets':expected}
    dump(project/'expected.json',config)
    record={'schema':'props-game-lighting-preparation-1','project':project.relative_to(ROOT).as_posix(),
        'output':output.relative_to(ROOT).as_posix(),'input':source.relative_to(ROOT).as_posix(),
        'gameCommit':GAME_COMMIT,'snapshotSHA256':SNAPSHOT_SHA,'originalSnapshotFilesSHA256':baseline,
        'checkerSHA256':sha(ROOT/CHECKER),'hostSHA256':sha(__file__),'expectedSHA256':sha(project/'expected.json'),
        'modelSHA256':ASSETS,'scope':'Read-only game snapshot, no PlayMode, no aesthetic/model edits, candidate collisions only.'}
    dump(project/'art-validation-prepared.json',record)
    print(json.dumps({'status':'prepared-not-launched','project':record['project'],'output':record['output'],
        'checkerSHA256':record['checkerSHA256'],'gameCommit':GAME_COMMIT,'snapshotSHA256':SNAPSHOT_SHA},indent=2))

def run(args,project,output):
    prepared=json.loads((project/'art-validation-prepared.json').read_text(encoding='utf-8'))
    if output!=ROOT/prepared['output']:raise ValueError('Prepared output mismatch')
    if (project/'graphics-run-command.json').exists():raise FileExistsError('One launch per prepared project; preserve evidence')
    editor=Path(args.editor).resolve()
    if not editor.is_file():raise FileNotFoundError('Unity Editor missing')
    active=subprocess.run(['powershell','-NoProfile','-Command','@(Get-Process Unity -ErrorAction SilentlyContinue).Count'],capture_output=True,text=True,check=True)
    if active.stdout.strip()!='0':raise RuntimeError('Existing Unity Editor; do not disturb it')
    if sha(ROOT/CHECKER)!=prepared['checkerSHA256'] or sha(project/'Assets/Editor/PropsGameLightingCheck.cs')!=prepared['checkerSHA256'] or sha(__file__)!=prepared['hostSHA256']:
        raise ValueError('Prepared/tested source changed; prepare a fresh project')
    if sha(project/'expected.json')!=prepared['expectedSHA256']:raise ValueError('Expected input changed')
    for asset_id,digest in ASSETS.items():
        if sha(project/'Inputs'/(asset_id+'.glb'))!=digest:raise ValueError('Staged model changed')
    command=[str(editor),'-batchmode','-force-d3d11','-projectPath',str(project),'-logFile',str(project/'unity-graphics-private.log'),
        '-executeMethod','PropsGameLightingCheck.Run','-propsExpected',str(project/'expected.json'),'-propsOutput',str(output)]
    record={'schema':'props-game-lighting-command-1','startedUTC':datetime.now(timezone.utc).isoformat(),
        'command':command,'project':project.relative_to(ROOT).as_posix(),'output':output.relative_to(ROOT).as_posix(),
        'checkerSHA256':prepared['checkerSHA256'],'hostSHA256':prepared['hostSHA256'],'inputModels':ASSETS,
        'scope':'One graphics-enabled isolated game snapshot validation; no game integration or contract acceptance.'}
    dump(project/'graphics-run-command.json',record)
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    start=time.monotonic()
    with (project/'launcher-private.log').open('xb') as log:
        process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,startupinfo=startup,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:code=process.wait(timeout=600)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            code=124
    record.update(exitCode=code,elapsedSeconds=round(time.monotonic()-start,3))
    source=ROOT/prepared['input'];record['originalModelsUnchanged']=all(sha(source/a/(a+'.glb'))==digest for a,digest in ASSETS.items())
    record['sourceBootstrapCopyUnchanged']=sha(project/SCENE)==prepared['originalSnapshotFilesSHA256'][SCENE]
    record['allModelCopiesUnchanged']=all(sha(project/'Inputs'/(a+'.glb'))==digest and (project/'Assets/ArtValidation'/(a+'.glb')).is_file() and sha(project/'Assets/ArtValidation'/(a+'.glb'))==digest for a,digest in ASSETS.items())
    report=output/'unity-game-lighting-report.json'
    if report.is_file():
        result=json.loads(report.read_text(encoding='utf-8'));result['originalBootstrapBytesUnchanged']=record['sourceBootstrapCopyUnchanged'];result['originalGlbBytesUnchanged']=record['originalModelsUnchanged'] and record['allModelCopiesUnchanged'];dump(report,result)
        record['reportSHA256']=sha(report)
    dump(project/'graphics-run-command.json',record)
    print(json.dumps({k:v for k,v in record.items() if k in ('exitCode','elapsedSeconds','originalModelsUnchanged','sourceBootstrapCopyUnchanged','allModelCopiesUnchanged','reportSHA256')},indent=2))
    if code or not record['originalModelsUnchanged'] or not record['sourceBootstrapCopyUnchanged'] or not record['allModelCopiesUnchanged'] or not report.is_file():raise SystemExit(code or 1)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',default='build/first-playable-props-unity/game-9a85db5-source.zip')
    parser.add_argument('--input',default='build/first-playable-props/run-004')
    parser.add_argument('--project',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--editor');parser.add_argument('--run',action='store_true')
    args=parser.parse_args();project=under(args.project);output=under(args.output)
    if project==output or output.is_relative_to(project) or project.is_relative_to(output):raise ValueError('Keep public capture output separate from private project')
    if args.run and not args.editor:parser.error('--editor is required for --run')
    run(args,project,output) if args.run else prepare(args,project,output)

if __name__=='__main__':main()
