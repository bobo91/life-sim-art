"""Package real static renders/source/export; make labelled review contact sheets."""
import argparse,hashlib,json,zipfile,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=['acquire_ava_rain.py','audit_rain_source.py','prepare_ava_rain.py','prepare_ava_rain_textures.py','ava_rain_tools.py','ava_rain_outfit.py','build_ava_rain.py','review_ava_rain.py','reproduce_ava_rain.py','package_ava_rain.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--out',required=True);ap.add_argument('--reproduction',required=True);a=ap.parse_args()
    src=Path(a.candidate).resolve();out=Path(a.out).resolve();assert not out.exists();out.mkdir(parents=True)
    evidence=ROOT/'evidence'/'ava-rain';preview=evidence/'previews';preview.mkdir(exist_ok=True)
    font=ImageFont.truetype('arial.ttf',20) if Path('C:/Windows/Fonts/arial.ttf').exists() else ImageFont.load_default(size=20)
    small=ImageFont.truetype('arial.ttf',15) if Path('C:/Windows/Fonts/arial.ttf').exists() else ImageFont.load_default(size=15)
    def board(name,views,width,height,heading):
        sheet=Image.new('RGB',(len(views)*width,height+100),(237,235,229));draw=ImageDraw.Draw(sheet);draw.text((14,7),heading,fill=(33,38,32),font=font)
        for i,(file,label) in enumerate(views):
            im=Image.open(src/'renders'/file).convert('RGB');im.thumbnail((width,height-4),Image.Resampling.LANCZOS);sheet.paste(im,(i*width+(width-im.width)//2,38));draw.text((i*width+12,height+40),label,fill=(33,38,32),font=font)
        draw.text((12,height+74),'Actual Blender renders | Rain Rig (CC) Blender Foundation | CC BY 4.0 | Ava adaptation: life-sim-art',fill=(50,53,48),font=small)
        sheet.save(preview/name,optimize=True)
    board('face-views.png',[('face_front.png','Front'),('face_profile.png','Profile'),('face_three_quarter.png','Three-quarter')],560,560,'Ava Morgan | Rain visual v0.1 | Static appearance review')
    board('turnaround.png',[('front.png','Front'),('side.png','Side'),('back.png','Back')],410,490,'Ava Morgan | Authored Rain anatomy, fitted cafe outfit')
    board('game-camera.png',[('game_camera_daylight.png','Daylight proxy | 16 m / 50 deg / vFOV 40'),('game_camera_shade.png','Ambient shade proxy | same camera')],640,360,'Normal game-camera framing | Blender lighting proxy, not Unity')
    board('cafe-materials.png',[('cafe_material_daylight.png','Daylight proxy'),('cafe_material_shade.png','Ambient shade proxy')],480,560,'Close material views | These are NOT the normal game camera')
    for file in ['ava_a03_same_scale.png','face_three_quarter.png','isometric.png','front.png']:
        im=Image.open(src/'renders'/file);im.thumbnail((1440,1050),Image.Resampling.LANCZOS);im.save(preview/file,optimize=True)
    for f in src.rglob('*'):
        if f.is_file() and f.suffix not in ['.blend1','.blend2']:
            dest=out/f.relative_to(src);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
    for file in SCRIPTS:
        d=out/'scripts'/file;d.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/'scripts'/file,d)
    for file in ['__init__.py','validation.py']:
        d=out/'art_pipeline'/file;d.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/'art_pipeline'/file,d)
    for file in ['RAIN_SOURCE_LICENSE.md','RAIN_VISUAL_REVIEW.md','RAIN_REPRODUCE.md']:
        shutil.copy2(ROOT/'docs'/'characters'/'ava-morgan'/file,out/file)
    doc=out/'RAIN_VISUAL_REVIEW.md';doc.write_text(doc.read_text(encoding='utf8').replace('../../../evidence/ava-rain/metrics.json','glb-validation.json'),encoding='utf8')
    for file in ['source-provenance.json','Rain-ReadMe.txt']:
        shutil.copy2(evidence/file,out/file)
    shutil.copy2(a.reproduction,out/'reproduction.json')
    shutil.copy2(ROOT/'configs'/'ava_rain_v01.json',out/'recipe.json')
    validation=json.loads((src/'glb-validation.json').read_text());review=json.loads((src/'review-report.json').read_text())
    manifest={'assetId':'chr_npc_ava_morgan_001','version':'rain-visual-v0.1','status':'Owner appearance GO/NO-GO pending; static only; not production/integration approval','geometrySource':'Actual Blender Studio Rain v3 download (Rain v3.3/rain_v3.2.blend), edited mesh copies','licence':'CC BY 4.0','credit':'Rain Rig (CC) Blender Foundation | studio.blender.org','licenceUrl':'https://creativecommons.org/licenses/by/4.0/','sourceUrl':'https://studio.blender.org/characters/rain/v3/','tooling':{'blender':'4.5.14 LTS','buildHash':'62c1db4208e8','embeddedPython':'3.11.15','texturePython':'3.14.6','pillow':'12.3.0','engine':'Cycles','device':'CPU','samples':36,'colorManagement':'AgX'},'seed':{'render':41032,'freckles':41033},'staticPoseSourceValues':{'EyelidsClose.L/R':.32,'Smile.L/R':.09},'geometry':validation,'review':review,'files':{str(f.relative_to(out)).replace('\\','/'):{'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(out.rglob('*')) if f.is_file()}}
    write(out/'manifest.json',manifest)
    archive=out.parent/(out.name+'.zip');assert not archive.exists()
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(out.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(out).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,info in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==info['sha256']
    result={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'payloadFilesVerified':len(manifest['files']),'glbSha256':validation['sha256'],'approval':'pending owner visual GO/NO-GO'}
    write(evidence/'bundle.json',result)
    write(evidence/'metrics.json',{'geometry':validation,'review':review,'flatNormalCorrections':json.loads((src/'report.json').read_text())['flatNormalCorrections']})
    print(json.dumps(result))

if __name__=='__main__':main()
