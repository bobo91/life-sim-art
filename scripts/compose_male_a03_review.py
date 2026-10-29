"""Matched A02/A03 and high/optimized actual-render comparisons; no retouching."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--a02',required=True);p.add_argument('--a03',required=True);p.add_argument('--out',required=True);p.add_argument('--urp');a=p.parse_args();old=Path(a.a02);new=Path(a.a03);out=Path(a.out);out.mkdir(parents=True,exist_ok=False);report=json.loads((new/'asset-report.json').read_text())
def font(size):
 for n in ['DejaVuSans.ttf','LiberationSans-Regular.ttf','Arial.ttf']:
  try:return ImageFont.truetype(n,size)
  except OSError:pass
 return ImageFont.load_default(size=size)
def sheet(name,items,cols,size):
 w,h=size;rows=(len(items)+cols-1)//cols;canvas=Image.new('RGB',(w*cols,rows*(h+35)+66),(34,39,42));d=ImageDraw.Draw(canvas)
 for i,(path,label) in enumerate(items):
  im=Image.open(path).convert('RGB');im.thumbnail((w,h),Image.Resampling.LANCZOS);x=i%cols*w+(w-im.width)//2;y=i//cols*(h+35);canvas.paste(im,(x,y));d.text((i%cols*w+12,y+h+6),label,font=font(18),fill=(235,230,216))
 d.text((14,canvas.height-52),'Willow Creek | A03 focused polish | matched camera/light within each comparison',font=font(16),fill=(236,231,218));d.text((14,canvas.height-28),'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified',font=font(16),fill=(203,207,201));canvas.save(out/name)
o=old/'renders';r=new/'renders'
sheet('a02-a03-face-comparison.png',[(o/'face_front.png','A02 front'),(r/'face_front.png','A03 front'),(o/'face_three_quarter.png','A02 three-quarter'),(r/'face_three_quarter.png','A03 three-quarter')],4,(510,510))
sheet('a03-body-views.png',[(r/'front.png','A03 front'),(r/'side.png','A03 side'),(r/'three_quarter.png','A03 three-quarter')],3,(500,500))
sheet('optimization-body-comparison.png',[(r/'high_three_quarter.png','A03 high / '+str(report['highTriangles'])+' tris'),(r/'three_quarter.png','A03 optimized / '+str(report['triangles'])+' tris'),(r/'high_side.png','High side'),(r/'side.png','Optimized side')],4,(430,430))
sheet('optimization-shoe-comparison.png',[(r/'high_shoe_close.png','High shoe QC close-up'),(r/'shoe_close.png','Optimized shoe QC close-up')],2,(700,700))
sheet('optimization-hand-comparison.png',[(r/'high_hand_close.png','High hand QC close-up'),(r/'hand_close.png','Optimized hand QC close-up')],2,(550,550))
sheet('a02-a03-game16m.png',[(o/'game_16m_front.png','A02 / 16 m'),(r/'game_16m_front.png','A03 optimized / 16 m')],2,(1280,720))
sheet('optimization-game16m.png',[(r/'high_game_16m_front.png','A03 high / 16 m'),(r/'game_16m_front.png','A03 optimized / 16 m')],2,(1280,720))
records=[]
for p in sorted(r.glob('*.png')):
 dest=out/p.name;shutil.copy2(p,dest);records.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'nativeFileUnchanged':True})
if a.urp:
 u=Path(a.urp);sheet('a02-a03-urp.png',[(u/'A02_unity_face.png','A02 / matched URP'),(u/'A03_unity_face.png','A03 optimized / matched URP')],2,(620,620))
 sheet('a02-a03-urp16m.png',[(u/'A02_unity_game16m.png','A02 / actual URP 16 m proxy'),(u/'A03_unity_game16m.png','A03 / actual URP 16 m proxy')],2,(1280,720))
 for p in u.glob('*.png'):shutil.copy2(p,out/p.name)
(out/'layout.json').write_bytes((json.dumps({'schema':'male-a03-review-layout-1','nativeBlenderRenders':records,'composites':'Resize/layout and labels only, no retouch or recolor.'},indent=2)+'\n').encode())
