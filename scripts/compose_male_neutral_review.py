"""Label/lay out actual Blender PNGs; no retouching, color edits or generated imagery."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--source-gate',required=True);p.add_argument('--out',required=True);a=p.parse_args();src=Path(a.input);out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
def font(size):
 for name in ['DejaVuSans.ttf','LiberationSans-Regular.ttf','Arial.ttf']:
  try:return ImageFont.truetype(name,size)
  except OSError:pass
 return ImageFont.load_default(size=size)
def sheet(name,items,cols,size):
 w,h=size;rows=(len(items)+cols-1)//cols;canvas=Image.new('RGB',(cols*w,rows*(h+36)+70),(34,39,42));d=ImageDraw.Draw(canvas)
 for i,(path,label) in enumerate(items):
  im=Image.open(path).convert('RGB');im.thumbnail((w,h),Image.Resampling.LANCZOS);x=(i%cols)*w+(w-im.width)//2;y=(i//cols)*(h+36);canvas.paste(im,(x,y));d.text(((i%cols)*w+12,y+h+6),label,font=font(19),fill=(235,230,216))
 d.text((14,canvas.height-56),'MALE-NEUTRAL-A01 | Phase A static review; same final mesh',font=font(18),fill=(236,231,218));d.text((14,canvas.height-31),'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified',font=font(16),fill=(203,207,201));canvas.save(out/name)
r=src/'renders';sheet('four-views.png',[(r/(n+'.png'),label) for n,label in [('front','Front'),('side','Side'),('back','Back'),('three_quarter','Three-quarter')]],4,(430,430));sheet('face-and-near.png',[(r/'face_front.png','Front face'),(r/'face_three_quarter.png','Three-quarter face'),(r/'near_third_person.png','Near perspective / 3.2 m')],3,(520,520));sheet('source-comparison.png',[(Path(a.source_gate)/'face_front.png','Unmodified Snow / source materials'),(r/'face_front.png','A01 / edited hair, pose and PBR')],2,(560,560))
records=[]
for f in sorted(r.glob('*.png')):
 dest=out/f.name;shutil.copy2(f,dest);records.append({'file':f.name,'sourceSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'previewSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'nativePixelsUnchanged':True})
(out/'preview-layout.json').write_text(json.dumps({'schema':'male-neutral-a01-preview-layout-1','nativeImages':records,'composites':'Resize and layout only; no retouching or recoloring. Source comparison cameras, subdivision and lights differ; see report.','pillow':Image.__version__},indent=2)+'\n',encoding='utf-8')
