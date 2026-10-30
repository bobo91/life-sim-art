"""Package static v0.2 and arrange unretouched real before/after renders."""
import argparse,json,hashlib,shutil,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--after',required=True);p.add_argument('--before',required=True);p.add_argument('--before-extra',required=True);p.add_argument('--out',required=True);a=p.parse_args();after=Path(a.after).resolve();before=Path(a.before).resolve();extra=Path(a.before_extra).resolve();out=Path(a.out).resolve();assert not out.exists();out.mkdir(parents=True)
    e=ROOT/'evidence/ava-rain-v02';e.mkdir(parents=True,exist_ok=True);pre=e/'previews';pre.mkdir(exist_ok=True)
    font=ImageFont.truetype('arial.ttf',22);small=ImageFont.truetype('arial.ttf',15)
    def sheet(name,rows,w,h,title):
        im=Image.new('RGB',(w*2,len(rows)*(h+32)+76),(237,235,229));d=ImageDraw.Draw(im);d.text((12,6),title,fill='#252a23',font=font)
        for r,pair in enumerate(rows):
            for c,(path,label) in enumerate(pair):
                pic=Image.open(path).convert('RGB');pic.thumbnail((w,h),Image.Resampling.LANCZOS);x=c*w+(w-pic.width)//2;y=40+r*(h+32);im.paste(pic,(x,y));d.text((c*w+12,y+h+3),label,fill='#252a23',font=font)
        d.text((12,im.height-24),'Actual Blender renders | Rain Rig (CC) Blender Foundation | CC BY 4.0 | Ava edits: life-sim-art',fill='#353830',font=small);im.save(pre/name,optimize=True)
    def pair(file,b=None):return [(b or before/'renders'/file,'BEFORE | Rain Ava v0.1'),(after/'renders'/file,'AFTER | Rain Ava v0.2')]
    sheet('face-before-after.png',[pair('face_front.png'),pair('face_three_quarter.png')],560,560,'Face | matched pose, scale, framing and studio')
    sheet('hair-before-after.png',[pair('face_profile.png'),pair('hair_rear_three_quarter.png',extra/'hair_rear_three_quarter.png')],560,560,'Hair | profile and rear three-quarter')
    sheet('body-before-after.png',[pair('front.png'),pair('side.png')],430,510,'Full body | preserved neck, shoulder and chest anatomy')
    sheet('clothes-before-after.png',[pair('clothes_detail.png',extra/'clothes_detail.png')],560,560,'Clothing | sleeve gathers, cloth grain and apron contact')
    sheet('normal-game-camera.png',[pair('game_camera_daylight.png'),pair('game_camera_shade.png')],640,360,'Normal game camera | 16 m / 50 deg / vertical FOV 40 | Blender light proxy')
    for name in ['ava_a03_same_scale.png','face_three_quarter.png','isometric.png']:
        im=Image.open(after/'renders'/name);im.thumbnail((1440,1100),Image.Resampling.LANCZOS);im.save(pre/name,optimize=True)
    shutil.copytree(pre,out/'previews');shutil.copytree(after,out/'after')
    frozen=out/'before';frozen.mkdir();shutil.copy2(before/'character_high.blend',frozen/'character_high.blend');shutil.copy2(before/'report.json',frozen/'report.json');shutil.copytree(extra,frozen/'extra-renders')
    # Include the actual baseline images used by the before/after boards.
    for f in ['front.png','side.png','face_front.png','face_profile.png','face_three_quarter.png','game_camera_daylight.png','game_camera_shade.png']:shutil.copy2(before/'renders'/f,frozen/f)
    inputs=out/'inputs';inputs.mkdir();base=ROOT/'build/ava-rain-v01';shutil.copy2(base/'static-final/static-source.blend',inputs/'static-source.blend');shutil.copy2(ROOT/'build/ava-rain-v02/native-face-edits.json',inputs/'native-face-edits.json')
    for script in ['ava_rain_tools.py','ava_rain_outfit.py','build_ava_rain.py','extract_rain_face_edit_data.py','refine_ava_rain.py','refine_ava_rain_face.py','refine_ava_rain_hair.py','refine_ava_rain_clothes.py','render_ava_rain_before.py','review_ava_rain.py','package_ava_rain_refinement.py']:
        dest=out/'scripts'/script;dest.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/'scripts'/script,dest)
    for f in ['__init__.py','validation.py']:
        dest=out/'art_pipeline'/f;dest.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/'art_pipeline'/f,dest)
    for f in ['RAIN_SOURCE_LICENSE.md']:
        shutil.copy2(ROOT/'docs/characters/ava-morgan'/f,out/f)
    for f in ['source-provenance.json','Rain-ReadMe.txt']:shutil.copy2(ROOT/'evidence/ava-rain'/f,out/f)
    shutil.copy2(e/'README.md',out/'README.md')
    doc=out/'README.md';doc.write_text(doc.read_text(encoding='utf8').replace('../../docs/characters/ava-morgan/RAIN_SOURCE_LICENSE.md','RAIN_SOURCE_LICENSE.md'),encoding='utf8')
    report=json.loads((after/'report.json').read_text());validation=json.loads((after/'glb-validation.json').read_text())
    manifest={'assetId':'chr_npc_ava_morgan_001','version':'rain-visual-v0.2','status':'Final owner visual GO/NO-GO pending; no rigging/animation/Unity approval','credit':'Rain Rig (CC) Blender Foundation | studio.blender.org','sourceUrl':'https://studio.blender.org/characters/rain/v3/','licence':'https://creativecommons.org/licenses/by/4.0/','bodyVerticesUnchangedByArtistEdits':report['bodyVerticesUnchangedByArtistEdits'],'geometry':validation,'tooling':'Blender 4.5.14 LTS, CPU Cycles 36 samples, AgX; Pillow 12.3.0 for sheets only','files':{f.relative_to(out).as_posix():{'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(out.rglob('*')) if f.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8');archive=out.parent/(out.name+'.zip');assert not archive.exists()
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(out.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(out).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,v in manifest['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==v['sha256']
    record={'file':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'payloadFilesVerified':len(manifest['files']),'glbSha256':validation['sha256'],'triangles':validation['triangles'],'materialCount':validation['materialCount'],'approval':'pending final owner visual GO/NO-GO'}
    (e/'bundle.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');print(json.dumps(record))

if __name__=='__main__':main()
