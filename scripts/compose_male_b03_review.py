"""Layout-only matched B02/B03 isolated elbow proof images; no image retouch."""
from pathlib import Path
import argparse,json,hashlib,shutil
from PIL import Image,ImageDraw,ImageFont,ImageChops
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=Path.cwd();src=r/a.input;out=r/a.out;assert not out.exists();out.mkdir(parents=True)
def font(size):
 for name in ['DejaVuSans.ttf','LiberationSans-Regular.ttf','Arial.ttf']:
  try:return ImageFont.truetype(name,size)
  except OSError:pass
 return ImageFont.load_default(size=size)
records=[];identical={}
for pose,label in [('run25','run25%'),('elbow90','physical90deg'),('near_straight10','nearstraight10deg')]:
 im=Image.new('RGB',(1680,530),(34,39,42));d=ImageDraw.Draw(im)
 for i,(side,version) in enumerate([('L','B02'),('L','B03'),('R','B02'),('R','B03')]):
  path=src/version/(pose+'_'+side+'.png');native=Image.open(path).convert('RGB');tile=native.resize((420,420),Image.Resampling.LANCZOS);im.paste(tile,(i*420,0));d.text((i*420+8,427),version+' | '+side+' | '+label,font=font(18),fill=(235,230,216));records.append({'path':path.relative_to(r).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()});dest=out/'native'/version/path.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
 d.text((12,470),'A03 B03 | actual Blender CPU Cycles12samples | matched pose/camera/lights | visual NO-GO',font=font(17),fill=(235,230,216));d.text((12,500),'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified',font=font(16),fill=(205,209,201));im.save(out/(pose+'-comparison.png'))
 if pose=='near_straight10':
  for side in ['L','R']:
   aa=Image.open(src/'B02'/(pose+'_'+side+'.png')).convert('RGB');bb=Image.open(src/'B03'/(pose+'_'+side+'.png')).convert('RGB');identical[side]=ImageChops.difference(aa,bb).getbbox() is None
meta={'schema':'male-b03-comparison-layout-1','input':str(src),'sourceImages':records,'nearStraightDecodedPixelsIdentical':identical,'processing':'Only equal proportionalresize,layout,labels; no recolor/retouch/crop/posechanges.','selectedPoseRun':'Exactrun25% sourceframe5.5','correctedDiagnosticPlane':'Physical90/10degrees with actualrunupperarm andhingeplane, sourceprototype002'};(out/'layout.json').write_bytes((json.dumps(meta,indent=2)+'\n').encode());print(json.dumps({'sourceImages':len(records),'nearStraightPixelsIdentical':identical}))
