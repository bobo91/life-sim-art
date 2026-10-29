"""Layout-only B02 everyday/transition checks from existing actual rendered images."""
import argparse,json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
r=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--previews',required=True);a=p.parse_args();out=r/a.out;assert not out.exists();out.mkdir(parents=True);dest=r/a.previews;dest.mkdir(parents=True,exist_ok=True);records={}
def font(size):
 for name in ['DejaVuSans.ttf','LiberationSans-Regular.ttf','Arial.ttf']:
  try:return ImageFont.truetype(name,size)
  except OSError:pass
 return ImageFont.load_default(size=size)
def sheet(name,items,cols,w,h,note):
 im=Image.new('RGB',(cols*w,((len(items)+cols-1)//cols)*(h+30)+75),(34,39,42));d=ImageDraw.Draw(im)
 for i,(path,label) in enumerate(items):
  records[path.relative_to(r).as_posix()]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  with Image.open(path) as src:tile=src.convert('RGB');tile.thumbnail((w,h),Image.Resampling.LANCZOS)
  x=i%cols*w;y=i//cols*(h+30);im.paste(tile,(x+(w-tile.width)//2,y+(h-tile.height)//2));d.text((x+8,y+h+5),label,font=font(16),fill=(235,230,216))
 d.text((10,im.height-67),'A03 B02 | actual matched diagnostic / runtime renders',font=font(17),fill=(235,230,216));d.text((10,im.height-43),note,font=font(15),fill=(215,213,200));d.text((10,im.height-22),'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified',font=font(14),fill=(205,209,201));im.save(out/name);shutil.copy2(out/name,dest/name)
daily=r/'build/male-neutral-b02/daily-001';items=[]
for pose in ['reach_full','gesture_full','reach_hand','gesture_hand']:
 for label in ['B01','B02']:items.append((daily/label/(pose+'.png'),label+' | '+pose))
sheet('everyday-comparison.png',items,4,440,440,'Same original52bone pose / camera / lighting; supports evaluated on B02.')
sheet('natural-knee-comparison.png',[(daily/'B01/knee_flex90.png','B01 | natural knee +90flexion'),(daily/'B02/knee_flex90.png','B02 | natural knee +90flexion')],2,600,600,'Positive90degree flexion, separately from historical negative90 hyperextension.')
t=r/'build/male-neutral-b02/unity-001/playmode-evidence/transitions';items=[]
for pair in ['idle_to_walk','walk_to_run','run_to_walk','walk_to_idle','idle_to_turn']:
 frames=sorted(t.glob(pair+'*.png'))
 if not frames:frames=sorted(t.glob(pair.replace('_to_','_')+'*.png'))
 if not frames:continue
 for index in [0,len(frames)//2,len(frames)-1]:items.append((frames[index],pair+' | capture '+str(index+1)))
assert len(items)==15,sorted(p.name for p in t.iterdir());sheet('playmode-crossfades.png',items,3,360,360,'Actual0.2second crossfades; finite/targetstate pass is not a smoothness/contact approval.')
meta={'schema':'male-b02-extra-check-layout-1','sourceFiles':records,'processing':'Only proportional resize/layout/labels; no pose/recolor/retouch.','out':str(out)};(out/'additional-layout.json').write_bytes((json.dumps(meta,indent=2)+'\n').encode());shutil.copy2(out/'additional-layout.json',dest/'additional-layout.json');print('Wrote actual everyday, natural-knee and PlayMode transition sheets.')
