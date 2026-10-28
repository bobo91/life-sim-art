"""Matched A01/A02 actual-render layout, with no image retouching."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--a01',required=True);p.add_argument('--a02',required=True);p.add_argument('--out',required=True);p.add_argument('--urp');a=p.parse_args();old=Path(a.a01);new=Path(a.a02);out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
def font(size):
 for name in ['DejaVuSans.ttf','LiberationSans-Regular.ttf','Arial.ttf']:
  try:return ImageFont.truetype(name,size)
  except OSError:pass
 return ImageFont.load_default(size=size)
def sheet(name,items,cols,size):
 w,h=size;rows=(len(items)+cols-1)//cols;canvas=Image.new('RGB',(cols*w,rows*(h+35)+66),(34,39,42));d=ImageDraw.Draw(canvas)
 for i,(path,label) in enumerate(items):
  im=Image.open(path).convert('RGB');im.thumbnail((w,h),Image.Resampling.LANCZOS);x=(i%cols)*w+(w-im.width)//2;y=(i//cols)*(h+35);canvas.paste(im,(x,y));d.text(((i%cols)*w+12,y+h+6),label,font=font(19),fill=(235,230,216))
 d.text((14,canvas.height-52),'Willow Creek | A02 static visual revision | matched A01 camera and lights',font=font(17),fill=(236,231,218));d.text((14,canvas.height-28),'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified',font=font(16),fill=(203,207,201));canvas.save(out/name)
r=new/'renders';o=old/'renders'
sheet('a01-a02-face-comparison.png',[(o/'face_front.png','A01 front'),(r/'face_front.png','A02 front'),(o/'face_three_quarter.png','A01 three-quarter'),(r/'face_three_quarter.png','A02 three-quarter')],4,(510,510))
sheet('a01-a02-clay-comparison.png',[(r/'A01_clay_face_front.png','A01 clay front'),(r/'A02_clay_face_front.png','A02 clay front'),(r/'A01_clay_face_three_quarter.png','A01 clay three-quarter'),(r/'A02_clay_face_three_quarter.png','A02 clay three-quarter')],4,(510,510))
sheet('a02-body-views.png',[(r/'front.png','A02 front'),(r/'side.png','A02 side'),(r/'three_quarter.png','A02 three-quarter')],3,(500,500))
sheet('a01-a02-full-front.png',[(o/'front.png','A01'),(r/'front.png','A02 / body geometry unchanged')],2,(540,540))
sheet('a01-a02-game16m.png',[(o/'game_16m_front.png','A01 / 16 m native framing'),(r/'game_16m_front.png','A02 / 16 m native framing')],2,(1280,720))
records=[]
for p in sorted(r.glob('*.png')):
 dest=out/p.name;shutil.copy2(p,dest);digest=hashlib.sha256(p.read_bytes()).hexdigest();assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest;records.append({'file':p.name,'sha256':digest,'nativePixelsAndFileUnchanged':True})
if a.urp:
 u=Path(a.urp);sheet('a01-a02-urp.png',[(u/'A01_unity_face.png','A01 / same URP lighting'),(u/'A02_unity_face.png','A02 / same URP lighting')],2,(620,620))
 for path in u.glob('*.png'):shutil.copy2(path,out/path.name)
(out/'layout.json').write_bytes((json.dumps({'schema':'male-a02-review-layout-1','nativeRenders':records,'composites':'Resize/layout/labels only; no color changes or retouch. Both revisions use identical Blender light/camera recipes.'},indent=2)+'\n').encode())
