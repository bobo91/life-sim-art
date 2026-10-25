"""Package only validated cafe outputs and their original sources as review artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from run_cafe_environment import ASSETS, SOURCES

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True);parser.add_argument('--sheets',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();source,sheets,output=((ROOT/p).resolve() for p in (args.input,args.sheets,args.output))
    for p in (source,sheets,output):p.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve versioned review artifact')
    if json.loads((source/'validation.json').read_text())['status']!='passed':raise ValueError('Require validated build')
    files=list(source.rglob('*'))+list(sheets.glob('*'))
    files += [ROOT/p for p in SOURCES]
    files += [ROOT/'scripts'/p for p in ('package_cafe_environment.py','compose_cafe_environment.py','compose_first_playable_props.py')]
    files += [ROOT/'configs'/(p+'.json') for p in (*ASSETS,'cafe-environment-pack','prop_cafe_table_001')]
    files += [ROOT/'docs/props/CAFE_ENVIRONMENT_PACK.md']
    files=sorted(set(p for p in files if p.is_file()))
    if any(p.suffix not in ('.py','.json','.md','.blend','.glb','.png') for p in files):raise ValueError('Unexpected artifact content')
    index=[];output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for p in files:
            name=p.relative_to(ROOT).as_posix();entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o100644<<16
            archive.writestr(entry,p.read_bytes());index.append({'path':name,'sha256':sha(p),'bytes':p.stat().st_size})
    digest=sha(output)
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n',encoding='utf-8')
    record={'schema':'cafe-environment-review-artifact-1','sha256':digest,'bytes':output.stat().st_size,
            'status':'Review only; no game integration, accepted gameplay contract or automatic merge',
            'files':index,'privateHostLogsIncluded':False}
    output.with_suffix('.zip.index.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='files'},indent=2))


if __name__=='__main__':main()
