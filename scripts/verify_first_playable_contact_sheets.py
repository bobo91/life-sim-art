"""Recompose real prop renders with host/default fonts and verify image provenance.

No Blender process or mesh generation is run. Existing evidence is read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ('prop_mailbox_001', 'prop_cafe_table_001')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(directory):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}


def same_pixels(actual, expected):
    assert actual.size == expected.size
    assert ImageChops.difference(actual.convert('RGB'), expected.convert('RGB')).getbbox() is None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source, output = (Path(value).resolve() for value in (args.input, args.output))
    source.relative_to(ROOT); output.relative_to(ROOT)
    reviewed = ROOT/'evidence/first-playable-props'
    if output.exists() or output.is_relative_to(reviewed):
        raise ValueError('Use a fresh build directory; preserve reviewed evidence')
    evidence_before, source_before = snapshot(reviewed), snapshot(source)
    models = {}
    for asset_id in ASSETS:
        expected = json.loads((reviewed/asset_id/'manifest.json').read_text(encoding='utf-8'))
        current = json.loads((source/asset_id/'manifest.json').read_text(encoding='utf-8'))
        model = source/asset_id/current['model']['file']
        assert sha(model) == current['model']['sha256'] == expected['model']['sha256'], asset_id
        assert current['sourceFilesSHA256'] == expected['sourceFilesSHA256'], 'Production source changed'
        models[asset_id] = sha(model)
    output.mkdir(parents=True)
    results = {}
    for mode, extra in (('auto', []), ('embedded', ['--font', 'default'])):
        target = output/mode
        command = ['scripts/compose_first_playable_props.py', '--input', source.relative_to(ROOT).as_posix(),
            '--output', target.relative_to(ROOT).as_posix(), *extra]
        subprocess.run([sys.executable, *command], cwd=ROOT, check=True)
        layout = json.loads((target/'comparison-layout.json').read_text(encoding='utf-8'))
        for path, digest in layout['inputs'].items(): assert sha(ROOT/path) == digest
        for asset_id in ASSETS: assert layout['models'][asset_id]['sha256'] == models[asset_id]
        hero = Image.open(target/'quality-sheet.png').convert('RGB')
        game = Image.open(target/'game-camera-comparison.png').convert('RGB')
        assert hero.size == (1400,1400) and game.size == (1400,1220)
        assert len(layout['heroPanels']) == 4 and len(layout['gameCrops']) == 8
        for panel in layout['heroPanels']:
            raw = Image.open(ROOT/panel['source']).convert('RGB')
            raw.thumbnail((640,570), Image.Resampling.LANCZOS)
            assert list(raw.size) == panel['size']
            x,y = panel['position']; w,h = raw.size
            same_pixels(hero.crop((x,y,x+w,y+h)), raw)
        raw = Image.open(source/'game_distance_16m.png').convert('RGB')
        same_pixels(game.crop((60,100,60+raw.width,100+raw.height)), raw)
        for crop in layout['gameCrops']:
            assert crop['displayScale'] == 1
            raw = Image.open(ROOT/crop['source']).convert('RGB').crop(crop['boxTopLeftPixels'])
            x,y = crop['position']; w,h = raw.size
            same_pixels(game.crop((x,y,x+w,y+h)), raw)
        if mode == 'embedded': assert layout['font']['selection'] == 'pillow-embedded-default'
        results[mode] = {'font':layout['font'], 'pillowVersion':layout['pillowVersion'],
            'heroPanelsVerified':4, 'nativeGameCropsVerified':8, 'fullGameFrameVerified':True,
            'sheets': {name:sha(target/name) for name in ('quality-sheet.png','game-camera-comparison.png')}}
    assert snapshot(reviewed) == evidence_before, 'Reviewed evidence changed'
    assert snapshot(source) == source_before, 'Source renders/meshes changed'
    result = {'status':'passed', 'verificationHostFamily':sys.platform,
        'scope':'Contact sheets only; actual meshes, source renders and reviewed evidence unchanged.',
        'meshSHA256':models, 'existingEvidenceUnchanged':True, 'inputBundleUnchanged':True,
        'originalComparisonSHA256': {name:evidence_before['evidence/first-playable-props/'+name]
            for name in ('quality-sheet.png','game-camera-comparison.png')},
        'variants':results}
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
