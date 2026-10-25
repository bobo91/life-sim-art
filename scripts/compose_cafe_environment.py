"""Layout actual cafe-pack Blender renders only; never alter model/render inputs."""
import argparse
import hashlib
import json
from pathlib import Path

import PIL
from PIL import Image, ImageDraw

from compose_first_playable_props import resolve_font

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ('prop_cafe_counter_001', 'prop_cafe_chair_001', 'prop_tin_001',
          'prop_cafe_cup_001', 'prop_cafe_tablecloth_001', 'prop_cafe_parasol_001')
APPROVED_TABLE_SHA256 = '6e122d9a172952fe237e9b24fe9c94b4eff70151e346f3ead95803a86a71ee54'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--font', help='Optional font path/name, or default for portable Pillow embedded font')
    args = parser.parse_args()
    source, target = Path(args.input).resolve(), Path(args.output).resolve()
    source.relative_to(ROOT)
    target.relative_to(ROOT)
    if target.exists():
        raise FileExistsError('Preserve previous evidence; choose a new output directory')
    font, font_info = resolve_font(args.font)
    layout = {'schema': 'cafe-environment-contact-layout-1',
              'scope': 'Actual Blender Cycles CPU renders; resizing/layout only, no repainting, relighting or AI enhancement.',
              'approvalStatus': 'Awaiting owner visual approval for the six new props.',
              'pillowVersion': PIL.__version__, 'font': font_info,
              'inputs': {}, 'models': {}, 'panels': [], 'outputs': {}}
    manifests = {}
    for asset in ASSETS:
        folder = source / asset
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        model = folder / manifest['model']['file']
        if sha(model) != manifest['model']['sha256']:
            raise ValueError('Actual model differs from manifest: ' + asset)
        layout['models'][asset] = {'sha256': sha(model), 'dimensionsMeters': manifest['dimensionsMeters'],
                                    'triangles': manifest['geometry']['triangles']}
        layout['inputs'][(folder / 'manifest.json').relative_to(ROOT).as_posix()] = sha(folder / 'manifest.json')
        for view in ('front', 'isometric'):
            path = folder / (view + '.png')
            if sha(path) != manifest['previews'][view]['sha256']:
                raise ValueError('Actual render differs from manifest: ' + asset + '/' + view)
            layout['inputs'][path.relative_to(ROOT).as_posix()] = sha(path)
        manifests[asset] = manifest
    arrangements = json.loads((source / 'arrangements.json').read_text(encoding='utf-8'))
    if arrangements['tableIdentity']['approvedGlbSHA256'] != APPROVED_TABLE_SHA256:
        raise ValueError('Arrangement no longer identifies the approved shared table')
    if sha(source / 'shared_approved_table.glb') != APPROVED_TABLE_SHA256:
        raise ValueError('Arrangement has changed the approved shared table')
    layout['sharedTable'] = {'assetId': 'prop_cafe_table_001', 'sha256': APPROVED_TABLE_SHA256,
                             'reuse': 'Identical table geometry in bare and dressed arrangements; dressing is separate instances.'}
    layout['inputs'][(source / 'arrangements.json').relative_to(ROOT).as_posix()] = sha(source / 'arrangements.json')
    for state in ('bare', 'set'):
        path = source / ('table_' + state + '.png')
        if not path.is_file():
            raise FileNotFoundError('Actual table-state render is missing')
        layout['inputs'][path.relative_to(ROOT).as_posix()] = sha(path)
    target.mkdir(parents=True)

    def panel(sheet, path, box, position, purpose):
        picture = Image.open(path).convert('RGB')
        original = picture.size
        picture.thumbnail(box, Image.Resampling.LANCZOS)
        sheet.paste(picture, position)
        layout['panels'].append({'source': path.relative_to(ROOT).as_posix(), 'purpose': purpose,
                                 'sourceSize': list(original), 'position': list(position),
                                 'size': list(picture.size), 'resampling': 'LANCZOS'})

    sheet = Image.new('RGB', (1500, 1240), '#EFECE3')
    draw = ImageDraw.Draw(sheet)
    draw.text((30, 22), 'WILLOW CREEK / CAFE ENVIRONMENT PACK', fill='#344A48', font=font(33))
    draw.text((30, 70), 'Actual Blender Cycles CPU renders / original procedural meshes / awaiting visual approval',
              fill='#625B50', font=font(22))
    draw.text((30, 105), 'Views are individually framed for inspection; tile sizes do not indicate relative object scale.',
              fill='#625B50', font=font(19))
    for index, asset in enumerate(ASSETS):
        col, row = index % 3, index // 3
        x, y = col * 500 + 12, row * 500 + 160
        draw.rounded_rectangle((x, y, x + 476, y + 466), radius=18, fill='#E5E0D5', outline='#D5CEBE', width=1)
        draw.text((x + 18, y + 18), asset, fill='#344A48', font=font(22))
        for view_index, view in enumerate(('front', 'isometric')):
            left = x + 10 + view_index * 234
            draw.text((left + 6, y + 60), view, fill='#625B50', font=font(18))
            panel(sheet, source / asset / (view + '.png'), (224, 224), (left, y + 92), asset + '/' + view)
        manifest = manifests[asset]
        dims = manifest['dimensionsMeters']
        draw.text((x + 18, y + 338), f'{dims[0]:.3f} W x {dims[1]:.3f} H x {dims[2]:.3f} D m',
                  fill='#344A48', font=font(21))
        draw.text((x + 18, y + 377), f'{manifest["geometry"]["triangles"]:,} triangles / bottom-centre pivot / metre scale',
                  fill='#625B50', font=font(17))
        draw.text((x + 18, y + 411), 'GLB + editable Blender source / no game integration',
                  fill='#625B50', font=font(17))
    draw.text((30, 1185), 'Warm timber / sage metal / cream ceramic / terracotta accents. Contact sheet uses resizing and labels only.',
              fill='#625B50', font=font(21))
    contact = target / 'contact-sheet.png'
    sheet.save(contact, optimize=True)
    layout['outputs'][contact.name] = sha(contact)

    sheet = Image.new('RGB', (1400, 740), '#EFECE3')
    draw = ImageDraw.Draw(sheet)
    draw.text((30, 20), 'ONE APPROVED TABLE / TWO MODULAR ARRANGEMENTS', fill='#344A48', font=font(30))
    draw.text((30, 65), 'Same table mesh, camera, lighting and framing. Cloth, cups, chairs and freestanding parasol remain separate assets.',
              fill='#625B50', font=font(18))
    for index, state in enumerate(('bare', 'set')):
        x = index * 700
        draw.text((x + 24, 105), 'BARE / neutral table' if state == 'bare' else 'DRESSED / separate cloth, cups and parasol',
                  fill='#344A48', font=font(23))
        panel(sheet, source / ('table_' + state + '.png'), (700, 525), (x, 145), 'table-state/' + state)
    draw.text((30, 700), 'Actual Blender renders, resized50%. Placement/seating/collision conventions are proposals, not a gameplay implementation.',
              fill='#625B50', font=font(18))
    states = target / 'table-states.png'
    sheet.save(states, optimize=True)
    layout['outputs'][states.name] = sha(states)
    (target / 'contact-layout.json').write_text(json.dumps(layout, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'composed', 'outputs': layout['outputs'], 'modelsVerified': len(layout['models']),
                      'approvedSharedTableVerified': True}, indent=2))


if __name__ == '__main__':
    main()
