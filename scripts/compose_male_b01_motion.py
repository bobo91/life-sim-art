"""Layout-only review of actual Unity B01 animation captures; no image retouching."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--previews');p.add_argument('--fps',type=int,default=24)
a=p.parse_args();source=Path(a.input).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
report=json.loads((source/'unity-animation-report.json').read_text());assert report['status']=='passed-art-skin-animation-import-reopen',report['status']
clips=['idle','walk','run','turn'];by_name={x['name']:x for x in report['clips']};records={}
def font(size):
 for n in ['DejaVuSans.ttf','LiberationSans-Regular.ttf','Arial.ttf']:
  try:return ImageFont.truetype(n,size)
  except OSError:pass
 return ImageFont.load_default(size=size)
def record(path):
 k=path.relative_to(source).as_posix();records[k]={'file':k,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def sheet(name,items,cols,size,subtitle):
 w,h=size;rows=(len(items)+cols-1)//cols;im=Image.new('RGB',(cols*w,rows*(h+32)+84),(34,39,42));d=ImageDraw.Draw(im)
 for i,(path,label) in enumerate(items):
  record(path)
  with Image.open(path) as native:tile=native.convert('RGB');tile.thumbnail((w,h),Image.Resampling.LANCZOS)
  x=i%cols*w+(w-tile.width)//2;y=i//cols*(h+32);im.paste(tile,(x,y));d.text((i%cols*w+10,y+h+6),label,font=font(17),fill=(235,230,216))
 d.text((12,im.height-70),'Willow Creek | A03 Phase B01 | Actual Unity URP skin/clip samples',font=font(17),fill=(235,230,216));d.text((12,im.height-47),subtitle,font=font(15),fill=(213,214,203));d.text((12,im.height-25),'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified',font=font(15),fill=(203,207,201));im.save(out/name)
items=[];sequences=[]
for clip in clips:
 frames=sorted((source/'frames'/clip).glob('frame_*.png'));cr=by_name[clip];assert len(frames)==cr['frameCount'],(clip,len(frames),cr['frameCount']);assert len(frames)>3
 for f in frames:record(f)
 for i in [0,len(frames)//4,len(frames)//2,3*len(frames)//4]:items.append((frames[i],f'{clip} | {i/a.fps:.2f}s'))
 sequences.append({'clip':clip,'fps':a.fps,'frames':[str(f) for f in frames],'frameCount':len(frames),'encodedDurationSeconds':len(frames)/a.fps,'importedClipDurationSeconds':cr['duration']})
sheet('motion-four-clips.png',items,4,(384,384),'Four phases per clip; layout/resize/labels only. No pose/image retouching.')
sheet('joint-closeups.png',[(source/(c+'_'+j+'.png'),c+' | '+j+' | 25% clip') for j in ['hand','elbow','knee'] for c in clips],4,(400,400),'Joint cameras follow sampled bones. See native files for full-resolution inspection.')
sheet('game16m-four-clips.png',[(source/(c+'_game16m.png'),c+' | 16m art proxy | 25% clip') for c in clips],2,(960,540),'Perspective 16m / elevation50deg / verticalFOV40deg. Art proxy, not game-world integration.')
for clip in clips:
 for suffix in ['full','game16m','hand','elbow','knee']:
  src=source/(clip+'_'+suffix+'.png');record(src);shutil.copy2(src,out/src.name)
# Small looping visual motion preview: native sampled frames, reduced resolution, original sampling speed.
# MP4 is encoded separately at all original frames; GIF intentionally samples every second frame.
gif=[];gif_durations=[];gif_elapsed=0;gif_encoded_ms=0
for sequence in sequences:
 for i,filename in enumerate(sequence['frames']):
  if i%2:continue
  gif_elapsed+=min(2,len(sequence['frames'])-i)/a.fps;target_ms=round(gif_elapsed*100)*10;gif_durations.append(target_ms-gif_encoded_ms);gif_encoded_ms=target_ms
  path=Path(filename);record(path)
  with Image.open(path) as native:tile=native.convert('RGB');tile.thumbnail((384,384),Image.Resampling.LANCZOS)
  canvas=Image.new('RGB',(384,430),(34,39,42));canvas.paste(tile,((384-tile.width)//2,0));d=ImageDraw.Draw(canvas);d.text((10,390),'A03 | '+sequence['clip']+' | actual URP',font=font(15),fill=(235,230,216));d.text((10,410),'Snow Rig (CC) Blender Foundation',font=font(13),fill=(203,207,201));gif.append(canvas)
gif[0].save(out/'motion-preview.gif',save_all=True,append_images=gif[1:],duration=gif_durations,loop=0,optimize=False,disposal=2)
layout={'schema':'male-b01-motion-layout-1','source':str(source),'fps':a.fps,'sourceStatus':report['status'],'sequences':sequences,'sourceFrames':list(records.values()),'gifFrameDurationsMs':gif_durations,'gifTotalDurationMs':gif_encoded_ms,'processing':'PNG: layout, proportional downscale and labels only. GIF: every second native frame, proportional downscale, original sampling speed rounded to GIF10ms timing, palette quantization. No geometry/pose/recolor/retouch.','gameCamera':'16m art proxy, not game-world view','credit':'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY4.0 | modified'}
(out/'layout.json').write_bytes((json.dumps(layout,indent=2)+'\n').encode())
if a.previews:
 dest=Path(a.previews);dest.mkdir(parents=True,exist_ok=False)
 for path in out.iterdir():
  if path.suffix.lower() in ['.png','.gif','.json']:shutil.copy2(path,dest/path.name)
print(json.dumps({'sheets':3,'nativeStillCopies':20,'gifFrames':len(gif),'sourceRecorded':len(records),'out':str(out)}))
