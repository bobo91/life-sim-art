"""Encode B02 native full/16m Unity frames with local Blender VSE/FFmpeg only."""
import argparse,hashlib,json,sys,struct
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--layout',required=True);p.add_argument('--out',required=True);p.add_argument('--camera',choices=['full','game16m'],default='full');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);layout=json.loads(Path(a.layout).read_text());output=Path(a.out).resolve();assert not output.exists();seqs=layout['sequences' if a.camera=='full' else 'sequences16m'];width,height=(960,720) if a.camera=='full' else (1280,720);s=bpy.context.scene;ed=s.sequence_editor_create();cursor=1
s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=width;s.render.resolution_y=height+80;s.render.resolution_percentage=100;s.render.fps=layout['fps'];s.render.fps_base=1;s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.ffmpeg.ffmpeg_preset='GOOD';s.render.ffmpeg.audio_codec='NONE';s.render.filepath=str(output);s.render.use_file_extension=True;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1;s.render.use_sequencer=True;segments=[]
for seq in seqs:
 frames=[Path(f) for f in seq['frames']];count=len(frames);strip=ed.strips.new_image(seq['clip'],str(frames[0]),channel=1,frame_start=cursor)
 for f in frames[1:]:strip.elements.append(f.name)
 strip.frame_final_duration=count;strip.transform.offset_y=40
 label=ed.strips.new_effect('Label_'+seq['clip'],type='TEXT',channel=2,frame_start=cursor,frame_end=cursor+count);label.text='A03 Locomotion Fit | '+seq['clip']+' | actual Unity URP'+(' | 16m' if a.camera=='game16m' else '');label.font_size=24;label.location=(.02,.065);label.alignment_x='LEFT';label.anchor_x='LEFT';label.anchor_y='TOP';label.blend_type='ALPHA_OVER';label.color=(.93,.91,.85,1)
 credit=ed.strips.new_effect('Credit_'+seq['clip'],type='TEXT',channel=3,frame_start=cursor,frame_end=cursor+count);credit.text='Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified';credit.font_size=15;credit.location=(.02,.025);credit.alignment_x='LEFT';credit.anchor_x='LEFT';credit.anchor_y='TOP';credit.blend_type='ALPHA_OVER';credit.color=(.82,.83,.80,1);segments.append({'clip':seq['clip'],'firstFrame':cursor,'lastFrame':cursor+count-1,'frames':count,'fps':layout['fps']});cursor+=count
s.frame_start=1;s.frame_end=cursor-1;bpy.ops.render.render(animation=True);assert output.is_file() and output.stat().st_size>1000
# Inspect actual MP4 timing atoms, not merely the requested encoder settings.
def atoms(data,start,end):
 while start+8<=end:
  size,kind=struct.unpack_from('>I4s',data,start);head=8
  if size==1:size=struct.unpack_from('>Q',data,start+8)[0];head=16
  if size==0:size=end-start
  assert size>=head and start+size<=end
  yield kind,start+head,start+size;start+=size
def child(data,start,end,kind):return next((x for x in atoms(data,start,end) if x[0]==kind),None)
data=output.read_bytes();_,ms,me=child(data,0,len(data),b'moov');timing=None
for kind,ts,te in atoms(data,ms,me):
 if kind!=b'trak':continue
 _,ds,de=child(data,ts,te,b'mdia');_,hs,he=child(data,ds,de,b'hdlr')
 if data[hs+8:hs+12]!=b'vide':continue
 _,mds,mde=child(data,ds,de,b'mdhd');version=data[mds]
 if version==0:timescale,duration=struct.unpack_from('>II',data,mds+12)
 else:timescale=struct.unpack_from('>I',data,mds+20)[0];duration=struct.unpack_from('>Q',data,mds+24)[0]
 _,mins,mine=child(data,ds,de,b'minf');_,ss,se=child(data,mins,mine,b'stbl');_,sts,ste=child(data,ss,se,b'stts');entries=struct.unpack_from('>I',data,sts+4)[0];runs=[struct.unpack_from('>II',data,sts+8+8*i) for i in range(entries)];timing={'timescale':timescale,'durationTicks':duration,'durationSeconds':duration/timescale,'frames':sum(n for n,d in runs),'frameDeltaRuns':[{'frames':n,'deltaTicks':d,'fps':timescale/d} for n,d in runs]};break
assert timing and timing['frames']==s.frame_end and abs(timing['durationSeconds']-s.frame_end/layout['fps'])<1e-5;assert all(abs(x['fps']-layout['fps'])<1e-5 for x in timing['frameDeltaRuns'])
# Reset context before decoding: a secondary scene can retain stale VSE frame cache.
expected_frames=s.frame_end
bpy.ops.wm.read_factory_settings(use_empty=True)
probe=bpy.context.scene;pe=probe.sequence_editor_create();movie=pe.strips.new_movie('ActualMP4',str(output),channel=1,frame_start=1);assert movie.frame_duration==expected_frames;probe.render.engine='BLENDER_EEVEE_NEXT';probe.render.resolution_x=width;probe.render.resolution_y=height+80;probe.render.resolution_percentage=100;probe.render.fps=layout['fps'];probe.render.use_sequencer=True;probe.render.image_settings.file_format='PNG';probe.view_settings.view_transform='Standard';probe.view_settings.look='None';probe.view_settings.exposure=0;probe.view_settings.gamma=1;decoded=output.with_name(output.stem+'-decoded');decoded.mkdir(exist_ok=False);checks=[]
for seg,seq in zip(segments,seqs):
 index=min(len(seq['frames'])-1,max(0,len(seq['frames'])//4));frame=seg['firstFrame']+index;probe.frame_set(frame);dest=decoded/(seg['clip']+'.png');probe.render.filepath=str(dest);bpy.ops.render.render(write_still=True,scene=probe.name);checks.append({'clip':seg['clip'],'encodedFrame':frame,'sourceFrame':seq['frames'][index],'decodedPath':str(dest)})
verification={'schema':'a03-locomotion-fit-motion-video-1','encoder':'Blender '+bpy.app.version_string+' VSE FFmpeg H264/MPEG4','camera':a.camera,'path':output.name,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'fps':layout['fps'],'frames':expected_frames,'durationSeconds':expected_frames/layout['fps'],'containerTiming':timing,'reopenedFrames':movie.frame_duration,'width':movie.elements[0].orig_width,'height':movie.elements[0].orig_height,'segments':segments,'decodedChecks':checks,'nativeImageRegion':{'x':0,'y':0,'width':width,'height':height},'processing':'All240actualUnityPNGframes sequentially at native24fps;80pxfooter with labels/credit only. No model rerender, pose retouch, synthesis, transition interpolation or camera generation.','audio':'none','license':'CC-BY-4.0 attributed Snow derivative; original repository-authored motion.'};output.with_suffix('.json').write_bytes((json.dumps(verification,indent=2)+'\n').encode());print(json.dumps(verification),flush=True)
