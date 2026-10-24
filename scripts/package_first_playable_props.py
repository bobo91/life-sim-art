"""Package the reviewed original props as a versioned artifact, never Git blobs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source=Path(args.input).resolve(); output=Path(args.output).resolve()
    source.relative_to(ROOT); output.relative_to(ROOT)
    if output.exists(): raise FileExistsError('Preserve versioned artifacts; choose a new filename')
    if json.loads((source/'validation.json').read_text(encoding='utf-8'))['status']!='passed':
        raise ValueError('Require completed validated build')
    files=list(source.rglob('*'))
    files += list((ROOT/'evidence/first-playable-props').rglob('*'))
    files += list((ROOT/'docs/props').glob('*.md'))
    files += list((ROOT/'art_pipeline').glob('*.py'))
    for name in ('props_mailbox.py','props_cafe_table.py','build_first_playable_props.py',
                 'run_first_playable_props.py','compose_first_playable_props.py',
                 'verify_first_playable_props.py','package_first_playable_props.py',
                 'probe_ava_neutral_feasibility.py','sanitize_first_playable_evidence.py'):
        files.append(ROOT/'scripts'/name)
    for asset_id in ('prop_mailbox_001','prop_cafe_table_001'):
        files.append(ROOT/'configs'/(asset_id+'.json'))
    files=sorted(set(p.resolve() for p in files if p.is_file() and p.name not in ('artifact.record.json','review-pr.json')))
    for p in files: p.relative_to(ROOT)
    output.parent.mkdir(parents=True,exist_ok=True)
    index=[]
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            name=path.relative_to(ROOT).as_posix()
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
            archive.writestr(info,path.read_bytes())
            index.append({'path':name,'bytes':path.stat().st_size,'sha256':sha(path)})
    digest=sha(output)
    output.with_suffix(output.suffix+'.sha256').write_text(digest+'  '+output.name+'\n',encoding='utf-8')
    record={'schema':'first-playable-props-artifact-1','file':output.relative_to(ROOT).as_posix(),
        'sha256':digest,'bytes':output.stat().st_size,'status':'review artifact only; no production release or game integration',
        'files':index,'reproduction':'Run source scripts from the art PR checkout; this archive is an auditable workspace mirror, not a git checkout.'}
    output.with_suffix(output.suffix+'.index.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='files'},indent=2))


if __name__=='__main__': main()
