"""Remap actual Rain source textures for static core PBR; no generated concepts."""
from PIL import Image
from pathlib import Path
import argparse,hashlib,json,colorsys,random,math
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();src=Path(a.source);out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
atlas=Image.new('RGB',(2048,2048),(178,135,108));record={}
for tile,pos in [(1001,(0,1024)),(1002,(1024,1024)),(1003,(0,0))]:
    f=src/f'TEX-rain_body_diffuse.{tile}.png';im=Image.open(f).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
    # Keep source painted anatomical variation; gentle warm tint rather than flat skin.
    im=im.point([min(255,round(i*.99)) for i in range(256)]+[min(255,round(i*.98)) for i in range(256)]+[min(255,round(i*.97)) for i in range(256)])
    atlas.paste(im,pos);record[str(tile)]={'sourceSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'uvScale':[.5,.5],'uvOffset':[pos[0]/2048,(2048-pos[1]-1024)/2048]}
atlas.save(out/'ava_skin_atlas.png',optimize=True)
eyes=Image.open(src/'TEX-rain_eyes.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS);pixels=eyes.load()
for y in range(1024):
 for x in range(1024):
    r,g,b=pixels[x,y]
    if b>r*1.12 and b>g*.95 and b>35:
        # Preserve radial iris texture/luminance, shift the source blue pigment to brown.
        h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255);rr,gg,bb=colorsys.hsv_to_rgb(.073,max(.35,s*.86),v*.70);pixels[x,y]=(round(rr*255),round(gg*255),round(bb*255))
eyes.save(out/'ava_eyes_brown.png',optimize=True)
jeans=Image.open(src/'TEX-rain_jeans_diffuse.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
jeans=jeans.point([round(i*.56) for i in range(256)]+[round(i*.59) for i in range(256)]+[round(i*.63) for i in range(256)]);jeans.save(out/'ava_denim.png',optimize=True)
normal=Image.open(src/'TEX-rain_jeans_normal.png').resize((1024,1024),Image.Resampling.LANCZOS);normal.save(out/'ava_denim_normal.png',optimize=True)
record['images']={f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'size':list(Image.open(f).size)} for f in out.glob('*.png')}
(out/'textures.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');print(json.dumps(record['images'],indent=2))
