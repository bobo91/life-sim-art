"""Package the validated ten props + reference presentation as a versioned review artifact."""
import argparse,hashlib,json,zipfile
from pathlib import Path
from run_walter_porch import ASSETS,SOURCES

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--sheets',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();source,sheets,output=((ROOT/p).resolve() for p in (args.input,args.sheets,args.output))
    for p in (source,sheets,output):p.relative_to(ROOT)
    if output.exists():raise FileExistsError('Preserve versioned archive')
    if json.loads((source/'validation.json').read_text())['status']!='passed':raise ValueError('Require validated build')
    files=list(source.rglob('*'))+list(sheets.glob('*'))+[ROOT/p for p in SOURCES]
    files += list((ROOT/'art_pipeline').glob('*.py'))
    files += [ROOT/'scripts'/p for p in ('compose_walter_porch.py','package_walter_porch.py','verify_walter_contacts.py')]
    files += [ROOT/'configs'/(a+'.json') for a in (*ASSETS,'walter-mailbox-reference','walters-house-pack')]
    files += [ROOT/'docs/props/WALTERS_HOUSE_PACK.md']
    files=sorted(set(p for p in files if p.is_file()))
    if any(p.suffix not in ('.py','.json','.png','.blend','.md','.glb') for p in files):raise ValueError('Unexpected artifact entry')
    output.parent.mkdir(parents=True,exist_ok=True);index=[]
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            name=p.relative_to(ROOT).as_posix();item=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,p.read_bytes())
            index.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
    digest=sha(output);output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n',encoding='utf-8')
    record={'schema':'walters-house-review-artifact-1','sha256':digest,'bytes':output.stat().st_size,'files':index,
            'status':'Owner visual review; no game integration/merge. TEMP presentation architecture is not a production house.'}
    output.with_suffix('.zip.index.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='files'},indent=2))


if __name__=='__main__':main()
