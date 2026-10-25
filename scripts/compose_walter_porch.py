"""Contact sheet from actual validated renders; portable embedded font, layout only."""
import argparse,hashlib,json
from pathlib import Path
import PIL
from PIL import Image,ImageDraw,ImageFont
from run_walter_porch import ASSETS

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();source,target=(Path(p).resolve() for p in (args.input,args.output))
    for p in (source,target):p.relative_to(ROOT)
    if target.exists():raise FileExistsError('Preserve original review images')
    target.mkdir(parents=True);font=lambda size:ImageFont.load_default(size=size)
    sheet=Image.new('RGB',(1800,1140),'#EFECE3');draw=ImageDraw.Draw(sheet)
    draw.text((24,20),"WILLOW CREEK / WALTER'S HOUSE & PORCH",fill='#344A48',font=font(34))
    draw.text((24,70),'Ten original props / actual Blender Cycles CPU renders / awaiting owner visual approval',fill='#625B50',font=font(22))
    draw.text((24,108),'Each model is framed individually; tile sizes do not indicate relative scale. Reused mailbox is shown in the porch scene.',fill='#625B50',font=font(19))
    record={'schema':'walter-contact-layout-1','scope':'Actual render inputs; resizing/layout only, no repainting or AI enhancement.',
            'pillowVersion':PIL.__version__,'font':'Pillow embedded scalable default','inputs':{},'models':{},'panels':[]}
    for i,asset in enumerate(ASSETS):
        folder=source/asset;manifest=json.loads((folder/'manifest.json').read_text())
        if sha(folder/(asset+'.glb'))!=manifest['model']['sha256']:raise ValueError('Model/manifest mismatch')
        record['models'][asset]=manifest['model']['sha256'];x=i%5*360+10;y=i//5*440+158
        draw.rounded_rectangle((x,y,x+340,y+405),radius=12,fill='#E4DFD4')
        draw.text((x+10,y+17),asset,fill='#344A48',font=font(18))
        for j,view in enumerate(('front','isometric')):
            path=folder/(view+'.png')
            if sha(path)!=manifest['previews'][view]['sha256']:raise ValueError('Render/manifest mismatch')
            record['inputs'][path.relative_to(ROOT).as_posix()]=sha(path)
            image=Image.open(path).convert('RGB');image.thumbnail((160,160),Image.Resampling.LANCZOS)
            pos=(x+7+j*166,y+80);sheet.paste(image,pos)
            draw.text((pos[0],y+53),view,fill='#625B50',font=font(15))
            record['panels'].append({'source':path.relative_to(ROOT).as_posix(),'position':pos,'size':image.size,'resampling':'LANCZOS'})
        dims=manifest['dimensionsMeters']
        draw.text((x+10,y+264),f'{dims[0]:.3f} W / {dims[1]:.3f} H / {dims[2]:.3f} D m',fill='#344A48',font=font(17))
        draw.text((x+10,y+302),f'{manifest["geometry"]["triangles"]:,} triangles / {len(manifest["blenderMeshHealth"]["materials"])} materials',fill='#625B50',font=font(17))
        draw.text((x+10,y+341),'GLB + editable Blender source',fill='#625B50',font=font(16))
        draw.text((x+10,y+369),'Bottom-centre pivot / metre scale',fill='#625B50',font=font(16))
    draw.text((24,1080),'Aged warm timber / muted sage / terracotta / cream. No purchased assets, external textures or manual modeling.',fill='#625B50',font=font(21))
    sheet.save(target/'contact-sheet.png',optimize=True)
    record['outputSHA256']=sha(target/'contact-sheet.png')
    (target/'contact-layout.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'composed','modelsVerified':10,'sha256':record['outputSHA256']}))


if __name__=='__main__':main()
