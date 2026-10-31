"""Arrange two AI concept PNGs beside the unchanged approved A03 render.

No character painting, retouching, AI generation, Blender or mesh operations.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'evidence/ava-design-ab'
font=ImageFont.truetype('arial.ttf',25);small=ImageFont.truetype('arial.ttf',17)
canvas=Image.new('RGB',(1800,770),(237,235,229));draw=ImageDraw.Draw(canvas)
draw.text((18,12),'AVA MORGAN | A / A03 / B | Val av ansiktsriktning',font=font,fill='#242a24')
items=[('ava-a-natural.png','A | AI-design: varm och naturlig'),('a03-style-reference.png','A03 | Godkänd Blender-stilreferens'),('ava-b-confident.png','B | AI-design: tydligare karaktär')]
records=[]
for i,(name,label) in enumerate(items):
    path=folder/name;im=Image.open(path).convert('RGB');size=list(im.size);im.thumbnail((600,600),Image.Resampling.LANCZOS)
    canvas.paste(im,(i*600+(600-im.width)//2,55+(600-im.height)//2));draw.text((i*600+16,666),label,font=small,fill='#242a24')
    records.append({'file':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':size})
draw.text((18,709),'AI-bilder = designunderlag. A03 = befintlig riktig rendering, ingen AI-omritning. Bildrutor anger inte fysisk skala.',font=small,fill='#42473e')
draw.text((18,741),'A03-källa: Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0. AI-koncept: life-sim-art.',font=small,fill='#42473e')
out=folder/'a-b-a03-comparison.png';canvas.save(out,optimize=True)
manifest={'phase':'2D concept choice, no 3D production','generatedWith':'built-in image_gen','selected':records,'comparison':{'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'size':list(canvas.size)},'layout':'Uniform resizing/placement/labels only; no portrait retouch or recolor; A03 original file unchanged','modelArtifactsCreated':False,'approval':'pending owner A/B selection'}
manifest['approval']='Owner selected B as official direction on 2026-10-31; A unselected, not quality-rejected. Next 2D sheet awaits approval; no 3D production GO.'
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
print(json.dumps({'comparison':out.name,'selectedImages':2,'a03ImageUnmodified':True}))
