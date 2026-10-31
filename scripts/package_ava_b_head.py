"""Package one frozen static head review; no model rebuilding or test platform."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    candidate=a.candidate.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    evidence=ROOT/'evidence/ava-b-head-v01';report=json.loads((candidate/'report.json').read_text());review=json.loads((candidate/'review-report.json').read_text())
    assert report['bodyCoordinatesPreserved'] and report['neckJunctionPreserved'] and report['staticOnly']
    assert review['sourceAndA03Preserved'] and not review['glbSkins'] and not review['glbAnimations']
    config=json.loads((ROOT/'configs/ava_b_head_v01.json').read_text())
    for name,key in [('ava-b-neutral-views.png','neutral'),('ava-b-model-sheet.png','sheet')]:assert sha(ROOT/'evidence/ava-b-design-sheet-v01'/name)==config['design'][key]
    # The boards were composed in a fresh build directory then copied to their
    # final repo location. Record the actual published output paths.
    board_manifest=json.loads((evidence/'manifest.json').read_text(encoding='utf8'))
    for name,r in board_manifest['outputs'].items():
        assert sha(evidence/name)==r['sha256'];r['path']='evidence/ava-b-head-v01/'+name
    (evidence/'manifest.json').write_text(json.dumps(board_manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    head_mats={m for x in report['headHairMeshes'] for m in x['materials']}
    metrics={'version':'ava-b-head-v0.1','designApprovedAndLocked':config['design'],
             'prototypeBaseHeadHairTriangles':report['headHairTriangles'],'nativeFaceBaseTriangles':12634,
             'nativeFaceVertices':6395,'previewSubdivisionHeadTriangles':report['evaluatedHeadTriangles'],
             'headOnlyReviewGlbTriangles':review['glbTriangles'],'unfinishedNativeContextTriangles':report['contextTriangles'],
             'headMaterialCount':len(head_mats),'imageTextures':review['images'],
             'bodyEditCoordinatesUnchanged':report['bodyCoordinatesPreserved'],'neckEditCoordinatesUnchanged':report['neckJunctionPreserved'],
             'maximumHeadEditMetres':report['maxHeadVertexChangeMetres'],'neckPreviewWeldToleranceMetres':.000020,
             'rainSourceSha256':report['originalRainSha256'],'a03Sha256':review['a03Sha256'],
             'canonicalBlendSha256':review['canonicalSha256'],'headOnlyGlbSha256':review['glbSha256'],
             'glbSkins':review['glbSkins'],'glbAnimations':review['glbAnimations'],
             'expectedFinalBudget':config['finalBudgetPlan'],'sourceRigOrEmbeddedTextsDelivered':False,
             'blender':report['blender'],'renderer':'Cycles CPU,48 samples,AgX','unityTested':False,
             'quality':'Still below A03 finish; head/hair prototype only, owner visual GO/NO-GO pending'}
    (evidence/'prototype-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    payload=out/'payload';payload.mkdir()
    files={candidate/'ava_b_head_review.blend':'ava_b_head_review.blend',candidate/'ava_b_head_review_only.glb':'ava_b_head_review_only.glb',candidate/'report.json':'provenance/geometry-report.json',candidate/'review-report.json':'provenance/review-report.json',ROOT/'build/ava-b-head-v01/native-neutral/extraction.json':'provenance/fresh-extraction.json',ROOT/'build/ava-rain-v01/textures/textures.json':'provenance/source-textures.json'}
    for path in (candidate/'renders').glob('*.png'):files[path]='renders/'+path.name
    names=['build_ava_b_head.py','review_ava_b_head.py','ava_b_hair.py','ava_b_brows.py','compose_ava_b_head_review.py','package_ava_b_head.py','ava_rain_tools.py','prepare_ava_rain.py','prepare_ava_rain_textures.py','acquire_ava_rain.py']
    for name in names:files[ROOT/'scripts'/name]='scripts/'+name
    repo_files=['configs/ava_b_head_v01.json','docs/characters/ava-morgan/AVA_B_REFERENCE_LOCK.json','docs/characters/ava-morgan/RAIN_SOURCE_LICENSE.md','evidence/ava-rain/Rain-ReadMe.txt','evidence/ava-rain/source-provenance.json']
    repo_files += ['evidence/ava-b-design-sheet-v01/'+n for n in ['ava-b-neutral-views.png','ava-b-model-sheet.png','ava-b-warm-smile.png']]
    repo_files += ['evidence/ava-b-head-v01/'+n for n in ['README.md','REPRODUCE.md','prototype-metrics.json','manifest.json','face-views.png','design-vs-model.png','A03same-scale.png','normal_game_camera.png']]
    for name in repo_files:files[ROOT/name]=name
    records=[]
    for src,dest in sorted(files.items(),key=lambda x:x[1]):
        path=payload/dest;path.parent.mkdir(parents=True,exist_ok=True)
        data=src.read_bytes()
        if src.is_relative_to(ROOT) and src.relative_to(ROOT).parts[0]!='build' and src.suffix in {'.py','.md','.json'}:data=data.replace(b'\r\n',b'\n')
        path.write_bytes(data)
        records.append({'file':dest,'bytes':path.stat().st_size,'sha256':sha(path)})
    manifest={'version':'ava-b-head-v0.1','scope':'Static head/hair review only; not a production game asset','files':records,
              'licence':'Rain derivative CC BY4.0; Rain Rig (CC) Blender Foundation | studio.blender.org. Snow/A03 renders comparison only, same credit/licence. See bundled source licence and modification notice.',
              'approval':'pending owner visual GO/NO-GO','originalRainNativeOrEmbeddedSoftwareIncluded':False,
              'sourceTextLineEndings':'Versioned py/md/json files normalized to LF, matching Git blobs; raw source provenance and images unchanged'}
    (payload/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    archive=out/'ava-b-head-v0.1-review.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for file in sorted(payload.rglob('*')):
            if file.is_file():
                info=zipfile.ZipInfo(file.relative_to(payload).as_posix(),date_time=(2026,10,31,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,file.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for record in records:assert hashlib.sha256(z.read(record['file'])).hexdigest()==record['sha256']
    bundle={'version':'ava-b-head-v0.1','releaseTag':'ava-b-head-v0.1','draft':True,'asset':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'payloadFiles':len(records),'prototypeOnly':True,'finalTriangleCap':30000,'approval':'pending separate visual GO/NO-GO'}
    (evidence/'bundle.json').write_text(json.dumps(bundle,indent=2)+'\n',encoding='utf8')
    print(json.dumps(bundle))


if __name__=='__main__':main()
