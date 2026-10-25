"""Layout real renders and native-pixel game crops; no generative image edits."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont
import PIL

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ('prop_mailbox_001', 'prop_cafe_table_001')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_font(preferred=None):
    """Use an explicit font, a host font, or Pillow's size-aware embedded font."""
    candidates = [preferred] if preferred and preferred != 'default' else []
    if not preferred:
        candidates = ['arial.ttf', 'DejaVuSans.ttf', 'LiberationSans-Regular.ttf']
    for candidate in candidates:
        try:
            probe = ImageFont.truetype(candidate, 20)
        except OSError:
            if preferred:
                raise ValueError('The explicitly requested font could not be opened') from None
            continue
        path = Path(probe.path)
        info = {'selection': 'explicit' if preferred else 'available-host-font',
            'file': path.name, 'family': list(probe.getname()),
            'sha256': sha(path) if path.is_file() else None}
        return lambda size: ImageFont.truetype(candidate, size), info
    # Pillow >=10.1 embeds a scalable font, so a minimal Linux host needs no font package.
    probe = ImageFont.load_default(size=20)
    return lambda size: ImageFont.load_default(size=size), {
        'selection': 'pillow-embedded-default', 'family': list(probe.getname())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', default='evidence/first-playable-props')
    parser.add_argument('--font', help='Optional font path/name, or "default" for the embedded fallback; requires Pillow >=10.1')
    args = parser.parse_args()
    source = Path(args.input).resolve(); target = Path(args.output).resolve()
    source.relative_to(ROOT); target.relative_to(ROOT)
    if target.exists(): raise FileExistsError('Choose a fresh output directory; preserve existing render evidence')
    font, font_info = resolve_font(args.font)
    target.mkdir(parents=True)
    layout = {'scope':'Actual Blender renders; layout/crops only, no repainting or AI enhancement.',
        'pillowVersion': PIL.__version__, 'font': font_info, 'inputs':{}, 'models':{}, 'heroPanels':[], 'gameCrops':[]}
    sheet = Image.new('RGB', (1400, 1400), '#EFECE3'); draw = ImageDraw.Draw(sheet)
    draw.text((32,20), 'WILLOW CREEK / FIRST PLAYABLE DAY', fill='#344A48', font=font(30))
    draw.text((32,62), 'Original Blender geometry / quality proofs v0.1.0 / awaiting visual approval', fill='#625B50',font=font(20))
    for column, asset_id in enumerate(ASSETS):
        config = json.loads((ROOT/'configs'/(asset_id+'.json')).read_text(encoding='utf-8'))
        manifest = json.loads((source/asset_id/'manifest.json').read_text(encoding='utf-8'))
        model = source/asset_id/manifest['model']['file']
        if sha(model) != manifest['model']['sha256']: raise ValueError('Input mesh does not match manifest: '+asset_id)
        layout['models'][asset_id] = {'sha256':sha(model), 'bytes':model.stat().st_size}
        folder = target/asset_id; folder.mkdir(exist_ok=True)
        for row, view in enumerate(('front','isometric')):
            path = source/asset_id/(view+'.png'); image = Image.open(path).convert('RGB')
            if sha(path) != manifest['previews'][view]['sha256']: raise ValueError('Input render does not match manifest')
            layout['inputs'][path.relative_to(ROOT).as_posix()] = sha(path)
            image.thumbnail((640,570), Image.Resampling.LANCZOS)
            x=column*700+(700-image.width)//2; y=140+row*620
            sheet.paste(image,(x,y))
            layout['heroPanels'].append({'source':path.relative_to(ROOT).as_posix(),
                'position':[x,y], 'size':list(image.size), 'resampling':'LANCZOS', 'maximumSize':[640,570]})
            draw.text((column*700+32,y-35),asset_id+' / '+view,fill='#344A48',font=font(21))
            shutil.copy2(path,folder/(view+'.png'))
        dims=config['dimensionsMeters']
        draw.text((column*700+32,1345),f'{dims[0]:.2f} W x {dims[1]:.2f} H x {dims[2]:.2f} D m / {manifest["geometry"]["triangles"]:,} tris / 4 materials',fill='#625B50',font=font(18))
        for name in ('manifest.json','build_report.json'):
            shutil.copy2(source/asset_id/name,folder/name)
    sheet.save(target/'quality-sheet.png', optimize=True)

    camera=json.loads((source/'game-camera.json').read_text(encoding='utf-8'))
    sheet=Image.new('RGB',(1400,1220),'#EFECE3'); draw=ImageDraw.Draw(sheet)
    draw.text((32,18),'GAME CAMERA / perspective 40 deg / pitch 50 deg',fill='#344A48',font=font(29))
    draw.text((32,58),'Default 16 m, yaw 180 / 1280 x 720 original pixels / Blender reconstruction, not Unity',fill='#625B50',font=font(19))
    full=Image.open(source/'game_distance_16m.png').convert('RGB')
    sheet.paste(full,(60,100))
    for column, view in enumerate(camera['views']):
        path=source/view['file']; image=Image.open(path).convert('RGB')
        layout['inputs'][path.relative_to(ROOT).as_posix()]=sha(path)
        xbase=column*350
        draw.text((xbase+20,855),f'{view["distanceMeters"]:g} m / yaw {view["unityYawDegrees"]}',fill='#344A48',font=font(22))
        draw.text((xbase+20,886),'Native pixel crops (100%)',fill='#625B50',font=font(17))
        for index, asset_id in enumerate(ASSETS):
            x,y,w,h=view['assets'][asset_id]['xywhPixelsBottomLeft']
            box=(max(0,int(x)-7),max(0,int(image.height-y-h)-7),min(image.width,int(x+w)+8),min(image.height,int(image.height-y)+8))
            crop=image.crop(box)
            position=(xbase+28+index*158,930+210-crop.height)
            sheet.paste(crop,position)
            draw.text((xbase+20+index*158,1155),f'{"mailbox" if index==0 else "table"}: {w:.0f} x {h:.0f}px',fill='#625B50',font=font(15))
            layout['gameCrops'].append({'source':path.relative_to(ROOT).as_posix(),'assetId':asset_id,'boxTopLeftPixels':box,'displayScale':1,'position':position})
    draw.text((32,1192),'Neutral preview ground grid: 0.5 m. Game lighting, collisions, cafe context and terrace setup states are not tested.',fill='#625B50',font=font(16))
    sheet.save(target/'game-camera-comparison.png',optimize=True)
    for name in ('game_distance_16m.png','game_distance_16m_yaw225.png','game-camera.json','validation.json','tooling.json'):
        shutil.copy2(source/name,target/name)
    (target/'comparison-layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
    print('Actual-render sheets written to',target)


if __name__=='__main__': main()
