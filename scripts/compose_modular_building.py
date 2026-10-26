"""Compose the 16 modules from verified actual renders; resize/layout only."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import PIL
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'configs/modular-building.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(folder, record, expected):
    if not isinstance(record, dict) or record.get('file') != expected:
        raise ValueError('Unexpected manifest filename: ' + expected)
    path = folder / expected
    path.resolve().relative_to(folder.resolve())
    if not path.is_file() or path.is_symlink() or sha(path) != record.get('sha256'):
        raise ValueError('Missing or SHA256-mismatched artifact: ' + str(path))
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source, target = ((ROOT / value).resolve() for value in (args.input, args.output))
    for path in (source, target):
        path.relative_to(ROOT)
    if target.exists():
        raise FileExistsError('Preserve existing review images')
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    assets = [asset['assetId'] for asset in config['assets']]
    if len(assets) != 16 or len(set(assets)) != 16:
        raise ValueError('This bounded contact sheet requires exactly 16 unique modules')
    inputs = []
    for asset in assets:
        folder = source / 'modules' / asset
        manifest_path = folder / 'manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['assetId'] != asset:
            raise ValueError('Manifest asset ID mismatch: ' + asset)
        model = checked(folder, manifest['model'], asset + '.glb')
        blend = checked(folder, manifest['sourceBlend'], asset + '.blend')
        views = {view: checked(folder, manifest['previews'][view], view + '.png')
                 for view in ('front', 'isometric')}
        geometry = manifest['geometry']
        dims = geometry['dimensionsMeters']
        triangles = geometry['triangles']
        if len(dims) != 3 or not all(math.isfinite(x) and x > 0 for x in dims) or triangles <= 0:
            raise ValueError('Invalid actual geometry measurements: ' + asset)
        inputs.append((asset, manifest_path, model, blend, views, dims, triangles))
    font = lambda size: ImageFont.load_default(size=size)
    sheet = Image.new('RGB', (2000, 1600), '#EFECE3')
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), 'WILLOW CREEK / MODULAR BUILDING SYSTEM', fill='#344A48', font=font(35))
    draw.text((24, 67), 'Sixteen original modules / actual Blender renders / owner visual review', fill='#625B50', font=font(23))
    draw.text((24, 104), 'Individually framed; image size does not indicate relative scale. Dimensions are measured from the exported GLB.', fill='#625B50', font=font(19))
    record = {'schema': 'modular-building-contact-layout-1', 'pillowVersion': PIL.__version__,
              'scope': 'Actual verified render inputs; resizing/layout only, no repainting or AI enhancement.',
              'font': 'Pillow embedded scalable default', 'canvasPixels': list(sheet.size),
              'configSHA256': sha(CONFIG), 'models': {}, 'inputs': {}, 'panels': []}
    for i, (asset, manifest, model, blend, views, dims, triangles) in enumerate(inputs):
        x, y = i % 4 * 500 + 10, i // 4 * 350 + 145
        draw.rounded_rectangle((x, y, x + 480, y + 338), radius=12, fill='#E4DFD4')
        draw.text((x + 12, y + 10), asset, fill='#344A48', font=font(20))
        record['models'][asset] = {'source': model.relative_to(ROOT).as_posix(), 'sha256': sha(model),
                                  'sourceBlendSHA256': sha(blend), 'manifestSHA256': sha(manifest),
                                  'dimensionsMetersWHD': dims, 'triangles': triangles}
        for j, (view, path) in enumerate(views.items()):
            with Image.open(path) as original:
                original_size = original.size
                image = original.convert('RGB')
            image.thumbnail((225, 225), Image.Resampling.LANCZOS)
            pos = (x + 10 + j * 235 + (225 - image.width) // 2,
                   y + 59 + (225 - image.height) // 2)
            draw.text((x + 12 + j * 235, y + 37), view, fill='#625B50', font=font(16))
            sheet.paste(image, pos)
            name = path.relative_to(ROOT).as_posix()
            record['inputs'][name] = sha(path)
            record['panels'].append({'assetId': asset, 'view': view, 'source': name,
                                     'sourcePNG_SHA256': record['inputs'][name],
                                     'modelSHA256': record['models'][asset]['sha256'],
                                     'sourcePixels': list(original_size), 'positionPixels': list(pos),
                                     'resizedPixels': list(image.size), 'resampling': 'LANCZOS'})
        draw.text((x + 12, y + 291), f'{dims[0]:.3f} W / {dims[1]:.3f} H / {dims[2]:.3f} D m', fill='#344A48', font=font(19))
        draw.text((x + 12, y + 316), f'{triangles:,} triangles / authored modular anchor', fill='#625B50', font=font(17))
    draw.text((24, 1563), 'Warm timber / muted sage / cream. Original procedural meshes; no purchased models. Unity import remains a separate handoff.', fill='#625B50', font=font(21))
    target.mkdir(parents=True)
    sheet.save(target / 'contact-sheet.png', optimize=True)
    record['outputSHA256'] = sha(target / 'contact-sheet.png')
    (target / 'contact-layout.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'composed', 'modelsVerified': len(inputs), 'sha256': record['outputSHA256']}))


if __name__ == '__main__':
    main()
