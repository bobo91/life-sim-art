"""Bounded B02 animated A03 import in a fresh isolated art-only Unity project."""
import argparse,datetime,hashlib,json,shutil,struct,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def local(p):
 p=Path(p).resolve();p.relative_to(ROOT);return p
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--project',required=True);p.add_argument('--editor',required=True);p.add_argument('--package-cache',required=True);p.add_argument('--baseline',default='build/male-neutral-b01/bind-005/chr_player_male_poc_001.glb');p.add_argument('--clips',default='idle,walk,run,turn');p.add_argument('--fps',type=int,default=24);a=p.parse_args()
source=local(a.input);project=local(a.project);editor=Path(a.editor).resolve();cache=Path(a.package_cache).resolve()
assert not project.exists(),'Use fresh project; preserve earlier results'
assert editor.is_file()
report=json.loads((source/'asset-report.json').read_text());asset_id=report['assetId'];glb=source/(asset_id+'.glb');digest=sha(glb)
for n in ['Assets/Editor','Assets/Character','Inputs','Packages','ProjectSettings']: (project/n).mkdir(parents=True,exist_ok=True)
packages={}
for folder in cache.iterdir():
 f=folder/'package.json'
 if f.is_file():packages[json.loads(f.read_text(encoding='utf-8-sig'))['name']]='file:'+folder.as_posix()
for name in ['com.unity.modules.animation','com.unity.modules.imageconversion','com.unity.modules.unitywebrequesttexture']:
 folder=editor.parent/'Data/Resources/PackageManager/BuiltInPackages'/name
 assert (folder/'package.json').is_file(),folder
 packages[name]='file:'+folder.as_posix()
assert all(n in packages for n in ['com.unity.cloud.gltfast','com.unity.render-pipelines.universal'])
dump(project/'Packages/manifest.json',{'dependencies':packages});(project/'ProjectSettings/ProjectVersion.txt').write_bytes(b'm_EditorVersion: 6000.5.8f1\n')
checker=ROOT/'scripts/MaleNeutralB02AnimationCheck.cs';shutil.copy2(checker,project/'Assets/Editor'/checker.name);shutil.copy2(glb,project/'Inputs'/glb.name)
dump(project/'expected.json',{'assetId':asset_id,'triangles':report['triangles'],'materials':report.get('materialCount',9),'bones':report.get('bones',52),'clips':a.clips.split(','),'videoFps':a.fps})
output=project/'evidence';cmd=[str(editor),'-batchmode','-force-d3d11','-projectPath',str(project),'-logFile',str(project/'unity-animation.log'),'-executeMethod','MaleNeutralB02AnimationCheck.Run','-b02Output',str(output),'-b02Expected',str(project/'expected.json'),'-b02Baseline',str(local(a.baseline))]
record={'schema':'male-b02-unity-command-1','startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'sourceGlbSha256':digest,'baselineGlbSha256':sha(local(a.baseline)),'checkerSha256':sha(checker),'runnerSha256':sha(__file__),'scope':'Isolated art-only B02 skin/clip proof and matched B01 comparison; no game changes or Humanoid avatar','packagesManifest':json.loads((project/'Packages/manifest.json').read_text())};dump(project/'command.json',record)
start=time.monotonic()
with (project/'launcher.log').open('xb') as loghandle:
 process=subprocess.Popen(cmd,cwd=ROOT,stdout=loghandle,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 try: code=process.wait(timeout=900)
 except subprocess.TimeoutExpired:
  process.terminate()
  try: process.wait(timeout=15)
  except subprocess.TimeoutExpired: process.kill();process.wait()
  code=124
unchanged=sha(glb)==digest and sha(project/'Inputs'/glb.name)==digest
imported=project/'Assets/Character'/glb.name;unchanged &= imported.is_file() and sha(imported)==digest
out=output/'unity-animation-report.json';record.update(exitCode=code,elapsedSeconds=time.monotonic()-start,sourceAndImportedGlbUnchanged=unchanged,reportExists=out.is_file())
if out.is_file():record['reportSha256']=sha(out)
dump(project/'command.json',record);print(json.dumps({k:record[k] for k in ['exitCode','elapsedSeconds','sourceAndImportedGlbUnchanged','reportExists']}))
raise SystemExit(code or (0 if unchanged and out.is_file() else 1))
