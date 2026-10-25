"""One isolated static GLB/URP import probe; no game-project changes."""
import argparse,hashlib,json,os,shutil,struct,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ASSETS={'prop_mailbox_001':'b243a55a5d92da3cd3a51c3957d0b1e1f1b9737ad8f6ed988121bae69e654698',
        'prop_cafe_table_001':'6e122d9a172952fe237e9b24fe9c94b4eff70151e346f3ead95803a86a71ee54'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def under(value):p=Path(value).resolve();p.relative_to(ROOT);return p

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--editor',required=True);parser.add_argument('--input',default='build/first-playable-props/run-004')
    parser.add_argument('--project',default='build/first-playable-props-unity/probe-001');parser.add_argument('--run',action='store_true')
    args=parser.parse_args();source=under(args.input);project=under(args.project);editor=Path(args.editor).resolve()
    if not editor.is_file():raise FileNotFoundError('Unity Editor missing')
    running=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-Process Unity -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True,check=True)
    if running.stdout.strip()!='0':raise RuntimeError('Existing Unity Editor process; do not disturb it')
    if project.exists():raise FileExistsError('Preserve previous probe; choose new project')
    expected=[]
    for asset_id,digest in ASSETS.items():
        model=source/asset_id/(asset_id+'.glb');manifest=json.loads((source/asset_id/'manifest.json').read_text(encoding='utf-8'))
        if sha(model)!=digest or manifest['model']['sha256']!=digest:raise ValueError('Source GLB hash mismatch')
        raw=model.read_bytes();length,kind=struct.unpack_from('<II',raw,12);document=json.loads(raw[20:20+length])
        materials=[{'name':m['name'],'baseColor':m['pbrMetallicRoughness']['baseColorFactor'],
                    'metallic':m['pbrMetallicRoughness']['metallicFactor'],'roughness':m['pbrMetallicRoughness']['roughnessFactor']}for m in document['materials']]
        expected.append({'id':asset_id,'dimensions':manifest['dimensionsMeters'],'triangles':manifest['geometry']['triangles'],
            'frontPoint':manifest['forwardProbe'].get('expectedExportXYZ',[]),'materials':materials})
    for name in ('Assets/Editor','Assets/Props','Inputs','Packages','ProjectSettings'): (project/name).mkdir(parents=True,exist_ok=True)
    dump(project/'Packages/manifest.json',{'dependencies':{'com.unity.cloud.gltfast':'6.20.0','com.unity.render-pipelines.universal':'17.5.0',
        'com.unity.modules.jsonserialize':'1.0.0','com.unity.modules.physics':'1.0.0'}})
    (project/'ProjectSettings/ProjectVersion.txt').write_text('m_EditorVersion: 6000.5.8f1\n',encoding='utf-8')
    checker=ROOT/'scripts/PropsStaticGlbImportCheck.cs';shutil.copy2(checker,project/'Assets/Editor'/checker.name)
    for asset_id in ASSETS:shutil.copy2(source/asset_id/(asset_id+'.glb'),project/'Inputs'/(asset_id+'.glb'))
    dump(project/'expected.json',{'assets':expected});report=project/'unity-import-report.json';log=project/'unity-import.log'
    command=[str(editor),'-batchmode','-nographics','-projectPath',str(project),'-logFile',str(log),'-executeMethod','PropsStaticGlbImportCheck.Run',
        '-propsReport',str(report),'-propsExpected',str(project/'expected.json')]
    record={'schema':'props-unity-static-import-command-1','startedUTC':datetime.now(timezone.utc).isoformat(),'preparedOnly':not args.run,
        'command':command,'project':project.relative_to(ROOT).as_posix(),'inputHashes':ASSETS,
        'checkerSHA256':sha(checker),'hostSHA256':sha(__file__),'scope':'Isolated art-only static GLB/URP probe; no game integration or contract acceptance.'}
    dump(project/'command.json',record)
    if not args.run:print('Prepared isolated props probe');return
    start=time.monotonic()
    with (project/'launcher.log').open('xb') as launcher:
        process=subprocess.Popen(command,cwd=ROOT,stdout=launcher,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:code=process.wait(timeout=480)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            code=124
    unchanged=all(sha(source/a/(a+'.glb'))==digest and sha(project/'Inputs'/(a+'.glb'))==digest for a,digest in ASSETS.items())
    imported_present=all((project/'Assets/Props'/(a+'.glb')).is_file() for a in ASSETS)
    imported_match=all(not (project/'Assets/Props'/(a+'.glb')).exists() or sha(project/'Assets/Props'/(a+'.glb'))==digest for a,digest in ASSETS.items())
    record.update(exitCode=code,elapsedSeconds=round(time.monotonic()-start,3),originalsAndCopiesUnchanged=unchanged,
        importedGlbFilesPresent=imported_present,importedGlbHashesMatchIfPresent=imported_match,reportExists=report.is_file())
    if report.is_file():
        value=json.loads(report.read_text(encoding='utf-8'));value['importedFilesUnchanged']=unchanged and imported_present and imported_match;dump(report,value);record['reportSHA256']=sha(report)
    dump(project/'command.json',record)
    print(json.dumps({'exitCode':code,'elapsedSeconds':record['elapsedSeconds'],'originalsAndCopiesUnchanged':unchanged,'reportExists':report.is_file()}))
    if code or not unchanged or not imported_present or not imported_match or not report.is_file():raise SystemExit(code or 1)

if __name__=='__main__':main()
