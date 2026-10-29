"""Layout actual art-side Unity motion frames, with fingerprints and metrics."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def font(size):
    for name in ('DejaVuSans.ttf','LiberationSans-Regular.ttf','Arial.ttf'):
        try:return ImageFont.truetype(name,size)
        except OSError:pass
    return ImageFont.load_default(size=size)

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--previews',required=True);a=p.parse_args()
    src=Path(a.input).resolve();out=Path(a.out).resolve();previews=Path(a.previews).resolve()
    assert not out.exists() and not previews.exists();out.mkdir(parents=True);previews.mkdir(parents=True)
    report=json.loads((src/'motion-report.json').read_text(encoding='utf-8'))
    assert report['status']=='passed-art-playmode-trajectory-capture' and report['actualPlayMode']
    assert report['frames']==240 and len(report['samples'])==240
    records=[]
    for f in sorted(src.rglob('*.png')):records.append({'file':f.relative_to(src).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    def sheet(name,items,cols,size):
        w,h=size;rows=(len(items)+cols-1)//cols;im=Image.new('RGB',(cols*w,rows*(h+30)+76),(34,39,42));d=ImageDraw.Draw(im)
        for i,(f,label) in enumerate(items):
            with Image.open(f) as native:tile=native.convert('RGB');tile.thumbnail(size,Image.Resampling.LANCZOS)
            x=i%cols*w+(w-tile.width)//2;y=i//cols*(h+30);im.paste(tile,(x,y));d.text((i%cols*w+7,y+h+5),label,font=font(16),fill=(235,230,216))
        d.text((10,im.height-66),'A03 locomotion fit | actual Unity URP / PlayMode | art-only scripted trajectory',font=font(16),fill=(235,230,216))
        d.text((10,im.height-42),'Layout/resize/labels only. B02 elbows retained; no game controller or integration.',font=font(15),fill=(213,214,203))
        d.text((10,im.height-21),'Snow Rig (CC) Blender Foundation | studio.blender.org | CC BY 4.0 | modified',font=font(14),fill=(203,207,201));im.save(previews/name)
    picked=[18,30,36,48,64,72,76,96,121,125,136,140,151,156,168,172,192,216]
    for camera in ['full','game16m']:
        items=[(src/'frames'/camera/f'frame_{i:04d}.png',f"{report['samples'][i]['scenario']} | {i/24:.2f}s") for i in picked]
        sheet('motion-storyboard.png' if camera=='full' else 'game16m-storyboard.png',items,3,(480,360) if camera=='full' else (640,360))
    sheet('elbows-retained.png',[(src/'closeups'/f'elbow_{side}_{i:04d}.png',f"{side} | {report['samples'][i]['scenario']} {i/24:.2f}s") for i in [18,36,48,64] for side in ['L','R']],4,(360,360))
    sheet('feet-start-stop-turn.png',[(src/'closeups'/f'feet_{i:04d}.png',f"{report['samples'][i]['scenario']} | {i/24:.2f}s") for i in [18,36,48,72,76,121,125,136,140,168,172,192]],3,(480,320))
    # Include the measured worst transition frames, not just attractive poses.
    crops=[];crop_records=[]
    for label in ['straight4','stop1','restart4','stop2','walk1p4','walkStop']:
        worst=min((row for row in report['samples'] if row['scenario']==label),key=lambda row:row['minFootY'])['frame']
        for index in [max(0,worst-1),worst,min(239,worst+1)]:
            path=out/f'foot_crop_{label}_{index:04d}.png'
            with Image.open(src/'frames'/'full'/f'frame_{index:04d}.png') as native:native.crop((250,350,700,700)).save(path)
            crops.append((path,f"{label} {index/24:.2f}s | {report['samples'][index]['minFootY']*1000:.1f}mm"))
            crop_records.append({'scenario':label,'frame':index,'source':f'frames/full/frame_{index:04d}.png','cropPixels':[250,350,700,700],'purpose':'Worst measured transition plus adjacentframes; native Unity pixels, not new3Drender'})
    sheet('transition-worst-frames.png',crops,3,(450,350))
    groups=[]
    for label,rows in itertools.groupby(report['samples'],lambda x:x['scenario']):
        rows=list(rows);groups.append((label,[x['frame'] for x in rows]))
    sequences={}
    for key,camera in [('sequences','full'),('sequences16m','game16m')]:
        sequences[key]=[{'clip':label,'fps':24,'frames':[str(src/'frames'/camera/f'frame_{i:04d}.png') for i in indices],'frameCount':len(indices)} for label,indices in groups]
    layout={'schema':'a03-locomotion-fit-layout-1','fps':24,'source':str(src),'processing':'Only proportional resizing, labels and layout; transition-worst sheet additionally crops native full frames as recorded. Videos preserve every native frame at24fps. No frame interpolation, retouch, time-warp or synthesized movement.','sourceFrames':records,'transitionCrops':crop_records,**sequences}
    (out/'layout.json').write_bytes((json.dumps(layout,indent=2)+'\n').encode());(previews/'layout.json').write_bytes((json.dumps(layout,indent=2)+'\n').encode())
    summaries=[]
    for label,indices in groups:
        rows=[report['samples'][i] for i in indices]
        def maximum(key):return max(x[key] for x in rows)
        summaries.append({'scenario':label,'frames':len(rows),'durationSeconds':len(rows)/24,'commandedSpeeds':sorted({x['commandedSpeed'] for x in rows}),'rootSpeedMaxErrorMps':max(abs(x['commandedSpeed']-x['measuredRootSpeed']) for x in rows),'maxYawRateDegps':maximum('yawDegreesPerSecond'),'minimumSoleMeters':min(x['minFootY'] for x in rows),'stableContactVertexMaxWorldSpeedMps':maximum('stableGroundContactMaxMps'),'contactVertexPairs':sum(x['stableGroundContactVertexPairs'] for x in rows),'normalizedTimeFirst':rows[0]['normalizedTime'],'normalizedTimeLast':rows[-1]['normalizedTime']})
    summary={'schema':'a03-locomotion-fit-unity-metrics-1','actualPlayMode':True,'scenarios':summaries,'metricDefinition':'Same sole vertex lies within3mmground atboth adjacent24Hzsamples; planarworldvelocity. Includes footroll/transition/yaw, not a terrain/physics tolerance. Zero pairs meansno measurement. groundedCentreMaxMps legacycolumn isunused/ignored.','rootMotion':False,'controller':'Art-side immediate speed command; desired direction translates instantly, visualheading RotateTowards720deg/s. Actualgamecontroller not run.'}
    (out/'metrics.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode());print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
