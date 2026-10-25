"""Actual Blender regression check for optional coffee and unchanged default models."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import build_cafe_environment as pack
from art_pipeline.validation import validate_glb


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    reference,output=(Path(p).resolve() for p in (args.reference,args.output))
    for p in (reference,output):p.relative_to(ROOT)
    if bpy.app.version!=(4,5,14) or not bpy.app.background or bpy.app.online_access:raise RuntimeError('Require isolated offline Blender4.5.14')
    if output.exists():raise FileExistsError('Preserve previous check')
    output.mkdir(parents=True)
    pack.preflight(output)
    defaults={}
    for asset in pack.BUILDERS:
        manifest=json.loads((reference/asset/'manifest.json').read_text(encoding='utf-8'))
        model=output/(asset+'.glb');config=pack.configuration(asset)
        validate_glb(model,config['dimensionsMeters'],config['maxTriangles'],manifest['blenderMeshHealth']['materials'])
        defaults[asset]={'sha256':sha(model),'referenceSHA256':manifest['model']['sha256'],
                         'byteIdentical':sha(model)==manifest['model']['sha256']}
    if not all(v['byteIdentical'] for v in defaults.values()):raise ValueError('Default delivered model changed')
    config=copy.deepcopy(pack.configuration('prop_cafe_cup_001'))
    config['geometry']['includeCoffee']=False
    pack.base.clear();obj=pack.build_cafe_cup(config)
    health=pack.base.health(obj,config)
    materials=[m.name for m in obj.data.materials]
    path=output/'coffee-free-diagnostic.glb';pack.export([obj],path)
    geometry=validate_glb(path,config['dimensionsMeters'],config['maxTriangles'],materials)
    if len(materials)!=2 or any('coffee' in m for m in materials):raise ValueError('Unused coffee material retained')
    result={'schema':'cafe-cup-options-check-1','status':'passed','blender':bpy.app.version_string,
        'scope':'Geometry/export regression only; no new render or production variant. Original render manifests retain their original source hashes.',
        'allSixDefaultModelsByteIdentical':True,'defaults':defaults,
        'coffeeFree':{'includeCoffee':False,'materials':materials,'geometry':geometry,'health':health},
        'sourceSHA256':{'scripts/props_cafe_smallwares.py':sha(ROOT/'scripts/props_cafe_smallwares.py'),
                        'scripts/verify_cafe_cup_options.py':sha(Path(__file__))}}
    pack.base.write_json(output/'coffee-options-verification.json',result)
    print('CAFE_CUP_OPTIONS_CHECK_PASSED',flush=True)


if __name__=='__main__':main()
