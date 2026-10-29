"""Encode actual Unity PNG sequences via installed Blender VSE/FFmpeg; no model scene loaded."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--layout',required=True);p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);layout=json.loads(Path(a.layout).read_text());output=Path(a.out).resolve();assert not output.exists()
s=bpy.context.scene;ed=s.sequence_editor_create();cursor=1
s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=768;s.render.resolution_y=848;s.render.resolution_percentage=100;s.render.fps=layout['fps'];s.render.fps_base=1;s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.ffmpeg.ffmpeg_preset='GOOD';s.render.ffmpeg.audio_codec='NONE';s.render.filepath=str(output);s.render.use_file_extension=True
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1;s.render.use_sequencer=True
native=[]
for sequence in layout['sequences']:
 frames=[Path(f) for f in sequence['frames']];count=len(frames)
 strip=ed.strips.new_image(sequence['clip'],str(frames[0]),channel=1,frame_start=cursor)
 for f in frames[1:]:strip.elements.append(f.name)
 strip.frame_final_duration=count;strip.transform.offset_y=40
 text=ed.strips.new_effect('Label_'+sequence['clip'],type='TEXT',channel=2,frame_start=cursor,frame_end=cursor+count);text.text='A03 | '+sequence['clip']+' | actual Unity URP';text.font_size=24;text.location=(.02,.065);text.alignment_x='LEFT';text.anchor_x='LEFT';text.anchor_y='TOP';text.blend_type='ALPHA_OVER';text.color=(.93,.91,.85,1)
 credit=ed.strips.new_effect('Credit_'+sequence['clip'],type='TEXT',channel=3,frame_start=cursor,frame_end=cursor+count);credit.text='Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified';credit.font_size=15;credit.location=(.02,.025);credit.alignment_x='LEFT';credit.anchor_x='LEFT';credit.anchor_y='TOP';credit.blend_type='ALPHA_OVER';credit.color=(.82,.83,.80,1)
 native.append({'clip':sequence['clip'],'firstFrame':cursor,'lastFrame':cursor+count-1,'frames':count,'fps':layout['fps']});cursor+=count
s.frame_start=1;s.frame_end=cursor-1;bpy.ops.render.render(animation=True)
assert output.is_file() and output.stat().st_size>1000
# Reopen encoded movie in a new VSE scene to inspect actual dimensions/frame duration.
probe=bpy.data.scenes.new('EncodedMovieVerification');pe=probe.sequence_editor_create();movie=pe.strips.new_movie('actual_review',str(output),channel=1,frame_start=1)
verification={'schema':'male-b01-motion-video-1','encoder':'Blender '+bpy.app.version_string+' VSE FFmpeg H264/MPEG4','path':output.name,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'fps':layout['fps'],'frames':s.frame_end,'durationSeconds':s.frame_end/layout['fps'],'reopenedFrames':movie.frame_duration,'width':movie.elements[0].orig_width,'height':movie.elements[0].orig_height,'segments':native,'processing':'All actual Unity PNG frames, sequential clips at original fps, labels/credit, vertical canvas extension only. No image retouch, camera interpolation or synthesized frames.','audio':'none','license':'CC-BY-4.0 attributed Snow derivative; original procedural clip motions by Willow Creek'}
assert movie.frame_duration==s.frame_end,(movie.frame_duration,s.frame_end)
output.with_suffix('.json').write_bytes((json.dumps(verification,indent=2)+'\n').encode());print(json.dumps(verification),flush=True)
