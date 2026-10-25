"""Compare preserved Blender renders with actual URP captures; layout only."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw
from compose_first_playable_props import resolve_font

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ('prop_mailbox_001', 'prop_cafe_table_001')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', default='build/first-playable-props/run-004')
    parser.add_argument('--unity', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--font')
    args = parser.parse_args()
    source, unity, target = ((ROOT / p).resolve() for p in (args.blender, args.unity, args.output))
    for path in (source, unity, target):
        path.relative_to(ROOT)
    if target.exists():
        raise FileExistsError('Preserve previous evidence; choose a fresh output')
    report = json.loads((unity / 'unity-game-lighting-report.json').read_text(encoding='utf-8'))
    if report['status'] != 'passed-graphics-import-validation-only' or not report['uiDisabledForAssetReview']:
        raise ValueError('Requires actual successful UI-free graphics capture')
    views = {view['file']: view for view in report['views']}
    camera = json.loads((source / 'game-camera.json').read_text(encoding='utf-8'))
    font, font_info = resolve_font(args.font)
    target.mkdir(parents=True)
    record = {'scope': 'Actual renders; layout/resizing/crops only, no repainting or color adjustment.',
              'font': font_info, 'sourceGameCommit': report['sourceGameCommit'],
              'inputs': {}, 'models': {}, 'panels': [], 'nativeCrops': [], 'outputs': {}}

    def read(path):
        record['inputs'][path.relative_to(ROOT).as_posix()] = sha(path)
        return Image.open(path).convert('RGB')

    for asset in ASSETS:
        manifest = json.loads((source / asset / 'manifest.json').read_text(encoding='utf-8'))
        if sha(source / asset / (asset + '.glb')) != manifest['model']['sha256']:
            raise ValueError('Model differs from approved Blender manifest')
        record['models'][asset] = manifest['model']['sha256']
        sheet = Image.new('RGB', (1400, 1800), '#EFECE3')
        draw = ImageDraw.Draw(sheet)
        draw.text((30, 20), asset + ' / BLENDER AND ACTUAL UNITY URP', fill='#344A48', font=font(29))
        draw.text((30, 64), 'Same approved mesh/material values. Different lighting, framing and tone mapping; no visual retuning.',
                  fill='#625B50', font=font(20))
        for path, box, position, label in (
            (source / asset / 'isometric.png', (450, 450), (40, 135), 'Approved Blender studio / resized'),
            (unity / (asset + '_game6m.png'), (800, 450), (550, 135), 'Actual game URP / 6 m / resized 62.5%')):
            picture = read(path)
            picture.thumbnail(box, Image.Resampling.LANCZOS)
            sheet.paste(picture, position)
            draw.text((position[0], 104), label, fill='#344A48', font=font(20))
            record['panels'].append({'asset': asset, 'source': path.relative_to(ROOT).as_posix(),
                                     'position': position, 'size': picture.size, 'resampling': 'LANCZOS'})
        draw.text((30, 613), 'NATIVE PIXEL CROPS / 100% / 40 deg FOV, pitch 50 deg, yaw 180 deg / 1280 x 720',
                  fill='#344A48', font=font(22))
        for column, (engine, distance) in enumerate((('Blender', 6), ('Unity', 6), ('Blender', 16), ('Unity', 16))):
            if engine == 'Blender':
                view = next(v for v in camera['views'] if v['distanceMeters'] == distance and v['unityYawDegrees'] == 180)
                path = source / view['file']
                x, y, w, h = view['assets'][asset]['xywhPixelsBottomLeft']
            else:
                path = unity / (asset + '_game' + str(distance) + 'm.png')
                x, y, w, h = views[path.name]['propRoi']
            picture = read(path)
            crop_box = (max(0, math.floor(x) - 7), max(0, math.floor(720-y-h) - 7),
                        min(1280, math.ceil(x+w) + 7), min(720, math.ceil(720-y) + 7))
            crop = picture.crop(crop_box)
            position = (column * 350 + 30, 705)
            draw.text((column * 350 + 30, 660), f'{engine} / {distance} m', fill='#344A48', font=font(23))
            sheet.paste(crop, position)
            draw.text((column * 350 + 30, 950), f'ROI {w:.0f} x {h:.0f} px + margin', fill='#625B50', font=font(17))
            record['nativeCrops'].append({'asset': asset, 'source': path.relative_to(ROOT).as_posix(),
                                          'boxTopLeftPixels': crop_box, 'position': position, 'displayScale': 1})
            if sheet.crop((position[0], position[1], position[0]+crop.width, position[1]+crop.height)).tobytes() != crop.tobytes():
                raise ValueError('Native crop pixels changed')
        draw.text((30, 992), 'Actual game URP / default 16 m / full frame at 100% / scene UI disabled for asset review',
                  fill='#344A48', font=font(22))
        path = unity / (asset + '_game16m.png')
        picture = read(path)
        sheet.paste(picture, (60, 1040))
        draw.text((30, 1770), 'Table location is provisional. Game UI/actions/navigation are not tested by these EditMode renders.',
                  fill='#625B50', font=font(18))
        output = target / (asset + '_comparison.png')
        sheet.save(output, optimize=True)
        record['outputs'][output.name] = sha(output)
    record['inputs'][(unity / 'unity-game-lighting-report.json').relative_to(ROOT).as_posix()] = sha(unity / 'unity-game-lighting-report.json')
    (target / 'comparison-layout.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'composed', 'outputs': record['outputs'], 'nativeCropsVerified': len(record['nativeCrops'])}, indent=2))


if __name__ == '__main__':
    main()
