"""One isolated art-only static GLB import; use installed editor and cached packages."""
import argparse,datetime,hashlib,json,shutil,struct,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+"\n",encoding="utf-8")
def local(p):p=Path(p).resolve();p.relative_to(ROOT);return p
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--project',required=True);p.add_argument('--editor',required=True);p.add_argument('--package-cache',required=True);a=p.parse_args()
source=local(a.input);project=local(a.project);editor=Path(a.editor).resolve();cache=Path(a.package_cache).resolve()
if project.exists():raise FileExistsError('Preserve previous Unity probe')
if not editor.is_file():raise FileNotFoundError(editor)
running=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-Process Unity -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True,check=True)
# A fresh isolated project has no lock; other editors are left running and untouched.
other_unity_processes=int(running.stdout.strip())
report=json.loads((source/'asset-report.json').read_text());asset_id=report['assetId'];glb=source/(asset_id+'.glb');digest=sha(glb);raw=glb.read_bytes();n=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+n]);mats=[]
for m in gltf['materials']:
 v=m['pbrMetallicRoughness'];mats.append({'name':m['name'],'baseColor':v.get('baseColorFactor',[1,1,1,1]),'baseTextureExpected':'baseColorTexture' in v,'metallic':v.get('metallicFactor',1),'roughness':v.get('roughnessFactor',1)})
for name in ['Assets/Editor','Assets/Props','Inputs','Packages','ProjectSettings']:(project/name).mkdir(parents=True,exist_ok=True)
packages={}
for folder in cache.iterdir():
 f=folder/'package.json'
 if f.is_file():
  v=json.loads(f.read_text(encoding='utf-8-sig'));packages[v['name']]='file:'+folder.as_posix()
for name in ['com.unity.modules.imageconversion','com.unity.modules.unitywebrequesttexture']:
 folder=editor.parent/'Data/Resources/PackageManager/BuiltInPackages'/name
 if not (folder/'package.json').is_file():raise FileNotFoundError('Installed builtin texture module missing: '+str(folder))
 packages[name]='file:'+folder.as_posix()
if not all(n in packages for n in ['com.unity.cloud.gltfast','com.unity.render-pipelines.universal']):raise RuntimeError('Required cached packages unavailable; no network install attempted')
dump(project/'Packages/manifest.json',{'dependencies':packages});(project/'ProjectSettings/ProjectVersion.txt').write_text('m_EditorVersion: 6000.5.8f1\n',encoding='utf-8')
checker=ROOT/'scripts/MaleNeutralA01ImportCheck.cs';shutil.copy2(checker,project/'Assets/Editor'/checker.name);shutil.copy2(glb,project/'Inputs'/glb.name)
dims=report['dimensionsMeters'];dump(project/'expected.json',{'assets':[{'id':asset_id,'dimensions':[dims[0],dims[2],dims[1]],'triangles':report['triangles'],'frontPoint':[],'materials':mats}]})
out=project/'unity-import-report.json';log=project/'unity-import.log';cmd=[str(editor),'-batchmode','-force-d3d11','-projectPath',str(project),'-logFile',str(log),'-executeMethod','MaleNeutralA01ImportCheck.Run','-propsReport',str(out),'-propsExpected',str(project/'expected.json')]
record={'schema':'male-neutral-a01-unity-command-1','startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'sourceGlbSha256':digest,'checkerSha256':sha(checker),'runnerSha256':sha(__file__),'otherUnityProcessesAtStart':other_unity_processes,'scope':'Art-only isolated static import, cached local packages, no game or rig','packagesManifest':json.loads((project/'Packages/manifest.json').read_text())};dump(project/'command.json',record)
start=time.monotonic()
with (project/'launcher.log').open('xb') as loghandle:
 process=subprocess.Popen(cmd,cwd=ROOT,stdout=loghandle,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 try:code=process.wait(timeout=480)
 except subprocess.TimeoutExpired:
  process.terminate()
  try:process.wait(timeout=15)
  except subprocess.TimeoutExpired:process.kill();process.wait()
  code=124
unchanged=sha(glb)==digest and sha(project/'Inputs'/glb.name)==digest;imported=project/'Assets/Props'/glb.name;unchanged=unchanged and imported.is_file() and sha(imported)==digest
record.update(exitCode=code,elapsedSeconds=time.monotonic()-start,sourceAndImportedGlbUnchanged=unchanged,reportExists=out.is_file())
if out.is_file():
 result=json.loads(out.read_text());result['importedFilesUnchanged']=unchanged;dump(out,result);record['reportSha256']=sha(out)
dump(project/'command.json',record);print(json.dumps({k:record[k] for k in ['exitCode','elapsedSeconds','sourceAndImportedGlbUnchanged','reportExists']}))
raise SystemExit(code or (0 if unchanged and out.is_file() else 1))
