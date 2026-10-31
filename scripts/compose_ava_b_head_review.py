"""Compose real Ava B head review renders beside the frozen 2D design.

python scripts/compose_ava_b_head_review.py --candidate build/... --outdir evidence/.../previews

Pillow layout, equal uniform scaling and labels only. No face painting, warping,
head-size registration, Blender execution or fabricated render comparisons.
The output directory must be new, to preserve earlier review evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / 'evidence/ava-b-design-sheet-v01/ava-b-neutral-views.png'
DESIGN_SHA256 = '08ca41f86d7ba806bcc5d5433ac4e0aa4b3f0f725fe2e962ab0a0ac421f77452'
BG = '#eeece6'
INK = '#26372f'
CREDIT = 'Rain Rig / Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | Ava-bearbetning: life-sim-art'
CONTEXT = 'Endast huvud och hår bedöms. Befintlig Rain-kropp i rest-T-pose; kläderna är inte färdig caféklädsel.'


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _font(size):
    return ImageFont.truetype('arial.ttf', size)


def _display_path(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _record(path):
    with Image.open(path) as image:
        dimensions = list(image.size)
    return {'path': _display_path(path), 'bytes': path.stat().st_size,
            'sha256': _sha(path), 'size': dimensions}


def _load(path, expected):
    with Image.open(path) as source:
        source.load()
        if source.size != expected:
            raise ValueError(f'{path}: expected {expected}, got {source.size}')
        return source.convert('RGB')


def _save(image, path):
    image.save(path, optimize=True)


def _face_views(faces, out):
    canvas = Image.new('RGB', (1800, 696), BG)
    d = ImageDraw.Draw(canvas)
    d.text((22, 12), 'AVA B | HUVUDPROTOTYP | FAKTISKA BLENDER-RENDERINGAR', font=_font(29), fill=INK)
    d.text((22, 49), CONTEXT, font=_font(19), fill=INK)
    for i, (name, label) in enumerate([
        ('face_front', 'Neutral | front'),
        ('face_profile', 'Neutral | ren profil'),
        ('face_three_quarter', 'Neutral | trekvart'),
    ]):
        # Same 0.54 scale for all three complete square renders; no recropping.
        canvas.paste(faces[name].resize((540, 540), Image.Resampling.LANCZOS), (30 + 600*i, 81))
        d.text((30 + 600*i, 631), label, font=_font(22), fill=INK)
    d.text((22, 670), CREDIT, font=_font(17), fill=INK)
    _save(canvas, out / 'face-views.png')


def _design_comparison(design, faces, out):
    canvas = Image.new('RGB', (1536, 1300), BG)
    d = ImageDraw.Draw(canvas)
    d.text((16, 13), 'AVA B | LÅST 2D-DESIGN OCH FAKTISK 3D-ÖVERSÄTTNING', font=_font(27), fill=INK)
    d.text((16, 51), 'Övre rad: godkänd 2D-formreferens. Nedre rad: neutral Blender-prototyp. Leende används inte som standardpose.', font=_font(18), fill=INK)
    for i, label in enumerate(['Front', 'Ren profil', 'Trekvart']):
        d.text((16 + 512*i, 90), label, font=_font(22), fill=INK)
    # Exact locked source pixels at 1:1; no independent edits to its three views.
    canvas.paste(design, (0, 122))
    d.text((16, 647), 'Faktisk 3D | samma proportioner ska läsas i volym; bilderna har inte ansiktsregistrerats eller förvrängts.', font=_font(19), fill=INK)
    for i, name in enumerate(['face_front', 'face_profile', 'face_three_quarter']):
        canvas.paste(faces[name].resize((512, 512), Image.Resampling.LANCZOS), (512*i, 681))
    d.text((16, 1208), '2D-raden är designunderlag, inte modellbevis eller en fysisk måttstock. 3D-raden visar de faktiska kompletta renderingarna.', font=_font(18), fill=INK)
    d.text((16, 1238), CONTEXT, font=_font(18), fill=INK)
    d.text((16, 1271), CREDIT, font=_font(17), fill=INK)
    _save(canvas, out / 'design-vs-model.png')


def _a03_comparison(faces, out):
    canvas = Image.new('RGB', (1600, 920), BG)
    d = ImageDraw.Draw(canvas)
    d.text((24, 13), 'AVA B OCH A03 | SAMMA KAMERA, LJUS OCH METERSKALA', font=_font(29), fill=INK)
    d.text((24, 51), 'Båda kompletta renderingarna skalas lika. Ingen separat normalisering av huvudstorlek, färg eller material.', font=_font(19), fill=INK)
    for x, key, label in [
        (40, 'comparison_ava_three_quarter', 'Ava B | ny separat huvud- och hårkandidat'),
        (840, 'a03_face_three_quarter', 'A03 | godkänd modell, oförändrad källa'),
    ]:
        d.text((x, 85), label, font=_font(21), fill=INK)
        canvas.paste(faces[key].resize((720, 720), Image.Resampling.LANCZOS), (x, 116))
    d.text((24, 852), CONTEXT, font=_font(18), fill=INK)
    d.text((24, 885), CREDIT, font=_font(17), fill=INK)
    _save(canvas, out / 'A03same-scale.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--outdir', required=True, type=Path)
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    out = args.outdir.resolve()
    if _sha(DESIGN) != DESIGN_SHA256:
        raise ValueError('Approved Ava B neutral reference changed; stop instead of silently adopting a new design')
    design = _load(DESIGN, (1536, 508))
    names = ['face_front', 'face_profile', 'face_three_quarter',
             'a03_face_front', 'a03_face_three_quarter','comparison_ava_three_quarter']
    paths = {name: candidate / 'renders' / (name + '.png') for name in names}
    paths['normal_game_camera'] = candidate / 'renders/normal_game_camera.png'
    faces = {name: _load(paths[name], (1000, 1000)) for name in names}
    _load(paths['normal_game_camera'], (1280, 720))
    # Validate every input before creating any deliverable directory.
    inputs = {name: _record(path) for name, path in paths.items()}
    inputs['approved_neutral_2d'] = _record(DESIGN)
    out.mkdir(parents=True, exist_ok=False)
    _face_views(faces, out)
    _design_comparison(design, faces, out)
    _a03_comparison(faces, out)
    # Native resolution, byte-for-byte copy; no caption is burned into this PNG.
    native_out = out / 'normal_game_camera.png'
    shutil.copyfile(paths['normal_game_camera'], native_out)
    if _sha(native_out) != inputs['normal_game_camera']['sha256']:
        raise ValueError('Native game-camera copy differs from input')
    output_names = ['face-views.png', 'design-vs-model.png', 'A03same-scale.png', 'normal_game_camera.png']
    manifest = {
        'phase': 'Ava B limited head/hair prototype; visual GO/NO-GO pending',
        'approvedDesignSha256': DESIGN_SHA256,
        'command': 'python scripts/compose_ava_b_head_review.py --candidate <candidate> --outdir <new-output-directory>',
        'inputs': inputs,
        'outputs': {name: _record(out / name) for name in output_names},
        'operations': 'Pillow labels, placement and uniform whole-image resizing only; locked 2D source pasted at 1:1; no facial warp, repaint, recolour, crop or separate head normalization',
        'scales': {'faceViews': 0.54, 'designRow': 1.0, 'modelVsDesign': 0.512,
                   'a03AndAvaComparison': 0.72, 'nativeGameCamera': 1.0},
        'comparisonBasis': 'Producer supplies the Ava/A03 complete 1000-square renders with identical camera, lighting and metre-scale scene. This layout applies the same scale to both and does not infer physical scale from pixels.',
        'context': CONTEXT,
        'credit': CREDIT,
        'licenceUrl': 'https://creativecommons.org/licenses/by/4.0/',
        'rainSourceUrl': 'https://studio.blender.org/characters/rain/v3/',
        'snowSourceUrl': 'https://studio.blender.org/characters/snow/v4/',
        'blenderInvokedByThisScript': False,
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    print(json.dumps({'outdir': str(out), 'outputs': output_names,
                      'approvedDesignUnchanged': True, 'gameCameraByteIdentical': True}))


if __name__ == '__main__':
    main()
