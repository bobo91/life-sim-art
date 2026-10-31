"""2D crop/layout/annotation only; no portrait repaint, warping, Blender or meshes.

First extraction: python scripts/compose_ava_b_sheet.py --extract build/ava-b-design-sheet-v01/corrected-six-view.png
Repeat layout:    python scripts/compose_ava_b_sheet.py
"""
from pathlib import Path
import argparse
import hashlib
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/ava-b-design-sheet-v01'
AB = ROOT / 'evidence/ava-design-ab'
FONT = 'arial.ttf'
BG = '#eeece6'
INK = '#26372f'
ACCENT = '#467b70'


def font(size):
    return ImageFont.truetype(FONT, size)


def record(path):
    return {'file': path.name, 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'size': list(Image.open(path).size)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', type=Path)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    extraction_path = OUT / 'extraction.json'
    if args.extract:
        source = Image.open(args.extract).convert('RGB')
        if source.size != (1536, 1024):
            raise ValueError(f'Expected 1536x1024 source, got {source.size}')
        source.crop((0, 0, 1536, 508)).save(OUT / 'ava-b-neutral-views.png', optimize=True)
        source.crop((1024, 508, 1536, 1016)).save(OUT / 'ava-b-warm-smile.png', optimize=True)
        extraction = {'sourceSize': list(source.size),
                      'sourceSha256': hashlib.sha256(args.extract.read_bytes()).hexdigest(),
                      'neutralCrop': [0, 0, 1536, 508],
                      'threeQuarterSmileCrop': [1024, 508, 1536, 1016],
                      'operations': 'Lossless rectangular crops only; no repaint, warp or facial registration',
                      'excluded': 'Redundant smiling front/profile; not modeling references'}
        extraction_path.write_text(json.dumps(extraction, indent=2) + '\n', encoding='utf8')

    neutral = Image.open(OUT / 'ava-b-neutral-views.png').convert('RGB')
    smile = Image.open(OUT / 'ava-b-warm-smile.png').convert('RGB')
    a03 = Image.open(AB / 'a03-style-reference.png').convert('RGB')
    # Uniform scale + crop for similar eye/chin screen height; no physical-scale claim.
    a03_display = a03.crop((50, 73, 1050, 1073)).resize((512, 512), Image.Resampling.LANCZOS)
    x_positions = [20, 544, 1068]
    labels = ['Neutral | front 0°', 'Neutral | ren vänsterprofil 90°', 'Neutral | trekvart cirka 35°']
    canvas = Image.new('RGB', (1600, 1332), BG)
    d = ImageDraw.Draw(canvas)
    d.text((20, 15), 'AVA MORGAN  /  VALD B-DESIGN  /  2D-REFERENS v01', font=font(31), fill=INK)
    d.text((20, 57), 'Vuxen identitet • samma huvud i tre neutrala vyer • separat uttrycksreferens • inväntar godkännande', font=font(20), fill=INK)
    for i, (x, label) in enumerate(zip(x_positions, labels)):
        d.text((x, 91), label, font=font(22), fill=INK)
        canvas.paste(neutral.crop((512*i, 0, 512*(i+1), 508)), (x, 123))
    d.text((20, 645), 'Proportioner styrs av neutralraden. Snedbena: hennes vänster / bildens höger framifrån. Knut: bakom nedre örat vid nacken.', font=font(19), fill=INK)
    d.text((20, 684), 'Uttryck | varmt, diskret leende', font=font(22), fill=INK)
    d.text((544, 684), 'A03 | befintlig Blender-rendering', font=font(22), fill=INK)
    canvas.paste(smile, (20, 718))
    canvas.paste(a03_display, (544, 718))
    d.text((1080, 721), 'FÖRENKLAT FÖR SPELSTILEN', font=font(24), fill=INK)
    notes = [
        ('1  HÅR', 'Breda svepta huvudformer och få grunda spår. Finstrån och tät hårstruktur borttagna; tunna fria slingor behållna.'),
        ('2  HUD', 'Slät matt yta utan porer och mikrokorn. Fräknar samlade diskret över näsa och övre kinder.'),
        ('3  ANSIKTE', 'Mjukare sammanhållna plan och lugna läppar. B:s avlånga form, kindben och naturligt avsmalnade bryn behålls.'),
    ]
    y = 770
    for title, body in notes:
        d.text((1080, y), title, font=font(21), fill=ACCENT)
        y += 29
        for line in textwrap.wrap(body, width=45):
            d.text((1080, y), line, font=font(19), fill=INK)
            y += 25
        y += 22
    for n, (x, y) in enumerate([(1190, 180), (1326, 400), (1271, 446)], 1):
        d.ellipse((x-13, y-13, x+13, y+13), fill=BG, outline=ACCENT, width=2)
        d.text((x-5, y-10), str(n), font=font(17), fill=INK)
    d.text((20, 1250), 'Ava: AI-genererat 2D-designunderlag. A03: originalbildens pixlar beskurna/skalade, ingen AI-omritning. Ingen fysisk skala anges.', font=font(17), fill=INK)
    d.text((20, 1278), 'A03: Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0. Källor, ändringar och promptar: README / manifest / prompts.', font=font(17), fill=INK)
    d.text((20, 1305), 'STOPP FÖR DESIGNGODKÄNNANDE  •  Ingen ny 3D-modell, riggning, animation eller integration.', font=font(18), fill=INK)
    canvas.save(OUT / 'ava-b-model-sheet.png', optimize=True)

    # A second sheet exposes approximate 2D landmark bands without changing portraits.
    guide = Image.new('RGB', (1800, 750), BG)
    g = ImageDraw.Draw(guide)
    g.text((20, 16), 'AVA B  /  NEUTRALA NIVÅGUIDER', font=font(30), fill=INK)
    g.text((20, 59), 'Visuell 2D-kontroll: gemensamma nivåband, inte uppmätt 3D-ortografi. Huvudbilderna är oförvrängda.', font=font(20), fill=INK)
    for i, (x, label) in enumerate(zip(x_positions, labels)):
        g.text((x, 94), label, font=font(22), fill=INK)
        guide.paste(neutral.crop((512*i, 0, 512*(i+1), 508)), (x, 128))
    bands = [(108, 'Hårfäste 105–110'), (176, 'Bryn cirka 175–178'), (206, 'Ögon 205–208'),
             (274, 'Näsbas 272–277'), (302, 'Munsöm 301–304'), (365, 'Haka 362–367')]
    overlay = Image.new('RGBA', guide.size, (0, 0, 0, 0))
    o = ImageDraw.Draw(overlay)
    for level, label in bands:
        for x in range(20, 1580, 12):
            o.line((x, 128+level, x+5, 128+level), fill=(42, 111, 101, 110), width=1)
        g.text((1592, 128+level-8), label, font=font(16), fill=INK)
    guide = Image.alpha_composite(guide.convert('RGBA'), overlay).convert('RGB')
    g = ImageDraw.Draw(guide)
    g.text((20, 659), 'Nivåerna är ungefärligt avlästa i källbildens pixlar (y från överkant). Öronens nederkant: cirka 279–282.', font=font(19), fill=INK)
    g.text((20, 691), 'Lås samma ansiktsstruktur vid en senare godkänd Rain-bearbetning; leendet är endast uttrycksmål.', font=font(19), fill=INK)
    guide.save(OUT / 'ava-b-proportion-guide.png', optimize=True)

    files = [record(OUT / name) for name in ['ava-b-neutral-views.png', 'ava-b-warm-smile.png',
             'ava-b-model-sheet.png', 'ava-b-proportion-guide.png']]
    manifest = {
        'phase': 'Selected Ava B / 2D head sheet pending owner approval / no 3D production',
        'generatedWith': 'built-in image_gen', 'modelId': None, 'seed': None,
        'generationReproducible': False, 'layoutCommand': 'python scripts/compose_ava_b_sheet.py',
        'files': files, 'extraction': json.loads(extraction_path.read_text(encoding='utf8')),
        'identitySource': record(AB / 'ava-b-confident.png'),
        'styleSource': record(AB / 'a03-style-reference.png'),
        'a03Display': {'crop': [50, 73, 1050, 1073], 'displaySize': [512, 512],
                       'operations': 'Uniform resizing and cropping only; no recolor/repaint', 'physicalScaleClaimed': False},
        'actualBlenderOrUnityRuns': 0, 'modelArtifactsCreated': False,
        'status': {'directionB': 'owner GO', 'sheet': 'awaiting owner approval',
                   'alternativeA': 'unselected, not quality-rejected', 'rainV02': 'visual NO-GO',
                   'pr42': 'draft', 'threeDimensionalProduction': 'paused', 'triangleCap': 30000}
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'outputs': [r['file'] for r in files], 'sourceA03Sha256': manifest['styleSource']['sha256']}))


if __name__ == '__main__':
    main()
