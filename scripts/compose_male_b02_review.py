"""B02 actual Unity evidence layout; no mesh, pose or image retouching."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--previews');p.add_argument('--fps',type=int,default=24);a=p.parse_args();source=Path(a.input).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
report=json.loads((source/'unity-animation-report.json').read_text());assert report['status']=='passed-art-skin-animation-import-reopen';clips=['idle','walk','run','turn'];by_name={x['name']:x for x in report['clips']};records={}
def font(size):
 for name in ['DejaVuSans.ttf','LiberationSans-Regular.ttf','Arial.ttf']:
  try:return ImageFont.truetype(name,size)
  except OSError:pass
 return ImageFont.load_default(size=size)
def record(path):
 key=path.relative_to(source).as_posix();records[key]={'file':key,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def sheet(name,items,cols,size,subtitle):
 w,h=size;rows=(len(items)+cols-1)//cols;im=Image.new('RGB',(cols*w,rows*(h+32)+84),(34,39,42));d=ImageDraw.Draw(im)
 for i,(path,label) in enumerate(items):
  record(path)
  with Image.open(path) as native:tile=native.convert('RGB');tile.thumbnail((w,h),Image.Resampling.LANCZOS)
  x=i%cols*w+(w-tile.width)//2;y=i//cols*(h+32);im.paste(tile,(x,y));d.text((i%cols*w+10,y+h+6),label,font=font(17),fill=(235,230,216))
 d.text((12,im.height-70),'Willow Creek | A03 B02 | Actual Unity URP | Integration NO-GO',font=font(17),fill=(235,230,216));d.text((12,im.height-47),subtitle,font=font(15),fill=(213,214,203));d.text((12,im.height-25),'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified',font=font(15),fill=(203,207,201));im.save(out/name)
items=[];sequences=[];sequences16m=[]
for clip in clips:
 frames=sorted((source/'frames'/clip).glob('frame_*.png'));far=sorted((source/'frames16m'/clip).glob('frame_*.png'));cr=by_name[clip];assert len(frames)==len(far)==cr['frameCount']
 for f in frames+far:record(f)
 for i in [0,len(frames)//4,len(frames)//2,3*len(frames)//4]:items.append((frames[i],f'{clip} | {i/a.fps:.2f}s'))
 meta={'clip':clip,'fps':a.fps,'frameCount':len(frames),'encodedDurationSeconds':len(frames)/a.fps,'importedClipDurationSeconds':cr['duration']}
 sequences.append({**meta,'frames':[str(f) for f in frames]});sequences16m.append({**meta,'frames':[str(f) for f in far]})
sheet('motion-four-clips.png',items,4,(384,384),'Four real phases per clip. Layout/downscale/labels only; no synthesized frames.')
sheet('joint-closeups.png',[(source/(c+'_'+j+'.png'),c+' | '+j+' | 25% clip') for j in ['hand','elbow','knee'] for c in clips],4,(400,400),'Actual B02 close-ups; elbow crease/knee pinching remain visible.')
sheet('game16m-four-clips.png',[(source/(c+'_game16m.png'),c+' | 16m art proxy') for c in clips],2,(960,540),'16m / elevation50deg / verticalFOV40deg. Isolated art camera, not game integration.')
comparison=source/'comparison'
for clip in ['run','walk','idle']:
 items=[]
 for joint in ['elbow','knee','wrist','hand']:
  for version in ['B01','B02']:items.append((comparison/(version+'_'+clip+'_'+joint+'.png'),version+' | '+clip+' | '+joint))
 sheet('b01-b02-'+clip+'-joints.png',items,4,(400,400),'Paired cameras/lighting; same25% B01 clip pose. No changes made for capture.')
sheet('b01-b02-face-identity.png',[(comparison/(v+'_face_'+angle+'.png'),v+' | face '+angle.replace('_',' ')) for angle in ['front','three_quarter'] for v in ['B01','B02']],4,(400,400),'Bind-face views: actual decoded RGB8 pixels are identical in both pairs.')
# Keep the actual native stills and matched comparisons accessible.
for clip in clips:
 for suffix in ['full','game16m','hand','elbow','knee']:
  src=source/(clip+'_'+suffix+'.png');record(src);shutil.copy2(src,out/src.name)
(out/'comparison').mkdir()
for src in sorted(comparison.glob('*.png')):record(src);shutil.copy2(src,out/'comparison'/src.name)
gif=[];durations=[];elapsed=0;encoded_ms=0
for sequence in sequences:
 for i,filename in enumerate(sequence['frames']):
  if i%2:continue
  elapsed+=min(2,len(sequence['frames'])-i)/a.fps;target=round(elapsed*100)*10;durations.append(target-encoded_ms);encoded_ms=target
  with Image.open(filename) as native:tile=native.convert('RGB');tile.thumbnail((384,384),Image.Resampling.LANCZOS)
  canvas=Image.new('RGB',(384,430),(34,39,42));canvas.paste(tile,((384-tile.width)//2,0));d=ImageDraw.Draw(canvas);d.text((10,390),'A03 B02 | '+sequence['clip']+' | actual URP',font=font(15),fill=(235,230,216));d.text((10,410),'Snow Rig (CC) Blender Foundation',font=font(13),fill=(203,207,201));gif.append(canvas)
gif[0].save(out/'motion-preview.gif',save_all=True,append_images=gif[1:],duration=durations,loop=0,optimize=False,disposal=2)
layout={'schema':'male-b02-review-layout-1','source':str(source),'fps':a.fps,'sourceStatus':report['status'],'sequences':sequences,'sequences16m':sequences16m,'sourceFrames':list(records.values()),'gifFrameDurationsMs':durations,'gifTotalDurationMs':encoded_ms,'processing':'PNG: layout, proportional downscale and labels. GIF: every second real frame, proportional downscale, native speed rounded to10ms timing, palette quantization. No pose/geometry/recolor/retouch/frame synthesis.','gameCamera':'16m art proxy, not game-world view','identityEvidence':json.loads((source/'identity-comparison.json').read_text()),'credit':'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY4.0 | modified'}
(out/'layout.json').write_bytes((json.dumps(layout,indent=2)+'\n').encode())
if a.previews:
 dest=Path(a.previews);dest.mkdir(parents=True,exist_ok=True)
 for src in out.rglob('*'):
  if not src.is_file() or src.suffix.lower() not in ['.png','.gif','.json']:continue
  target=dest/src.relative_to(out);assert not target.exists(),target;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
print(json.dumps({'sheets':7,'nativeStills':48,'gifFrames':len(gif),'sourceRecorded':len(records),'fullFrames':sum(x['frameCount'] for x in sequences),'game16mFrames':sum(x['frameCount'] for x in sequences16m),'out':str(out)}))
