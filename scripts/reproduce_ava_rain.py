"""Small sequential static prototype recipe; Blender 4.5.14, Pillow 12.3.0."""
import argparse,sys,subprocess,hashlib,zipfile,shutil
from pathlib import Path
from urllib.request import urlopen

def main():
    p=argparse.ArgumentParser();p.add_argument('--blender',required=True);p.add_argument('--out',required=True);p.add_argument('--a03',help='Optional pinned approved static character.blend; otherwise fetched from its unchanged release');a=p.parse_args()
    out=Path(a.out).resolve();assert not out.exists();out.mkdir(parents=True);scripts=Path(__file__).resolve().parent
    def run(name,*args,blender=False):
        cmd=[a.blender,'--background','--factory-startup','--offline-mode','--disable-autoexec','--python-exit-code','1','--python',str(scripts/name),'--'] if blender else [sys.executable,str(scripts/name)]
        with (out/(name+'.log')).open('w',encoding='utf8') as log:subprocess.run(cmd+list(map(str,args)),check=True,stdout=log,stderr=subprocess.STDOUT)
    run('acquire_ava_rain.py','--out',out/'source')
    source=out/'source'/'original'/'Rain v3.3'/'rain_v3.2.blend'
    run('audit_rain_source.py','--source',source,'--out',out/'audit',blender=True)
    run('prepare_ava_rain.py','--source',source,'--out',out/'static','--lids','.32','--smile','.09','--views','none',blender=True)
    run('prepare_ava_rain_textures.py','--source',source.parent/'textures','--out',out/'textures')
    run('build_ava_rain.py','--source',out/'static'/'static-source.blend','--textures',out/'textures','--out',out/'candidate','--samples','36','--optimize',blender=True)
    ref=Path(a.a03).resolve() if a.a03 else out/'a03'/'character.blend'
    if not a.a03:
        ref.parent.mkdir();archive=ref.parent/'approved-static.zip'
        with urlopen('https://github.com/bobo91/life-sim-art/releases/download/male-neutral-a03-v0.3/male-neutral-a03-v0.3-review.zip',timeout=180) as r,archive.open('xb') as f:shutil.copyfileobj(r,f)
        assert hashlib.sha256(archive.read_bytes()).hexdigest()=='3ae53894ae1aef5c909a82d1c3d60b3f153005ca8dee0b11cfb646b2b09da6fc'
        with zipfile.ZipFile(archive) as z:ref.write_bytes(z.read('character.blend'))
    run('review_ava_rain.py','--candidate',out/'candidate','--a03',ref,'--samples','36',blender=True)
    print(out/'candidate')

if __name__=='__main__':main()
