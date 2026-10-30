"""Acquire and hash-pin the owner's approved official Rain bundle, unchanged."""
from pathlib import Path
from urllib.request import urlopen,Request
import argparse,hashlib,json,zipfile,datetime

PAGE='https://studio.blender.org/characters/rain/v3/'
URL='https://studio.blender.org/download-source/files/ee/a7/eea73e55dba1cea31c09848df6a794b2-4.zip'
ZIP_SHA='80217f163f6392dc829233d63c2cfb5e1376775bc34101ad14f39631fea70d24'
BLEND_SHA='831ab6d837c679040285862b15dc9ee5180b018442a88aeaf92aaa7509b80258'

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();base=Path(a.out);base.mkdir(parents=True,exist_ok=False)
    record={'page':PAGE,'downloadUrl':URL,'retrievedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    for target,address in [('rain-v3-page.html',PAGE),('rain-v3-original.zip',URL)]:
        with urlopen(Request(address,headers={'User-Agent':'Mozilla/5.0'}),timeout=180) as response:data=response.read()
        digest=hashlib.sha256(data).hexdigest()
        if target.endswith('.zip'):assert digest==ZIP_SHA,'Official bundle changed: stop, re-audit licence/version before accepting'
        (base/target).write_bytes(data);record[target]={'bytes':len(data),'sha256':digest}
    with zipfile.ZipFile(base/'rain-v3-original.zip') as z:
        assert z.testzip() is None;record['entries']=[]
        for item in z.infolist():
            if item.is_dir():continue
            relative=Path(item.filename);assert not relative.is_absolute() and '..' not in relative.parts
            data=z.read(item);dest=base/'original'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            record['entries'].append({'path':item.filename,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    assert hashlib.sha256((base/'original'/'Rain v3.3'/'rain_v3.2.blend').read_bytes()).hexdigest()==BLEND_SHA
    (base/'acquisition.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    # No transient signed CDN URL or executable source code is logged or executed.
    print(json.dumps({'zipSha256':ZIP_SHA,'blendSha256':BLEND_SHA,'files':len(record['entries'])}))

if __name__=='__main__':main()
