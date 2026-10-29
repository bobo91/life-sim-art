"""Read-only authored gait contact measurement on the actual B02 skinned soles."""
import argparse, bpy, json, math, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    folder=Path(a.input);out=Path(a.out);assert not out.exists()
    spec=json.loads((folder/'asset-report.json').read_text(encoding='utf-8'))
    bpy.context.preferences.use_preferences_save=False;bpy.ops.wm.open_mainfile(filepath=str((folder/'character_locomotion_fit.blend').resolve()),load_ui=False,use_scripts=False)
    rig=bpy.data.objects['A03_B01_Rig'];sole=bpy.data.objects['M01_shoes_bottom'];sc=bpy.context.scene
    ids={s:[v.index for v in sole.data.vertices if v.co.z<.004 and (v.co.x>0 if s=='L' else v.co.x<0)] for s in ['L','R']}
    results={}
    for name in ['idle','walk','run']:
        rig.animation_data.action=bpy.data.actions[name];lo,hi=rig.animation_data.action.frame_range;duration=(hi-lo)/24
        speed=0 if name=='idle' else spec['config'][name]['designSpeedMps'];fps=192;count=round(duration*fps);rows=[]
        for i in range(count+1):
            t=duration*i/count;f=lo+t*24;sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update();ev=sole.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
            rows.append({s:[list(ev.matrix_world@me.vertices[j].co) for j in indices] for s,indices in ids.items()});ev.to_mesh_clear()
        stable=[];centres=[]
        for i in range(1,len(rows)):
            for side in ids:
                before,after=rows[i-1][side],rows[i][side]
                for p0,p1 in zip(before,after):
                    if max(p0[2],p1[2])<=.003:
                        stable.append(math.hypot((p1[0]-p0[0])*fps,(p1[1]-p0[1])*fps-speed))
                if max(min(p[2] for p in before),min(p[2] for p in after))<=.003:
                    c0=[sum(p[k] for p in before)/len(before) for k in range(3)];c1=[sum(p[k] for p in after)/len(after) for k in range(3)]
                    centres.append(math.hypot((c1[0]-c0[0])*fps,(c1[1]-c0[1])*fps-speed))
        stable.sort()
        results[name]={'seconds':duration,'speedMps':speed,'fps':fps,'frames':len(rows),'soleVerticesPerSide':{s:len(x) for s,x in ids.items()},'minSoleMeters':min(p[2] for row in rows for pts in row.values() for p in pts),'stableContactVertexSamples':len(stable),'stableContactMaxWorldSpeedMps':max(stable,default=0),'stableContactP95WorldSpeedMps':stable[round(.95*(len(stable)-1))] if stable else None,'stableContactRmsWorldSpeedMps':math.sqrt(sum(v*v for v in stable)/len(stable)) if stable else None,'soleCentreMaxWorldSpeedMpsWhenNearGround':max(centres,default=0),'sameFootStrideMeters':duration*speed,'stepsPerMinute':0 if name=='idle' else 120/duration}
    result={'schema':'a03-locomotion-fit-dense-contact-1','samples':results,'method':'Actual saved Blender skin,192Hz. Translate world root along Blender-Y at declaredspeed. Stable contact uses SAME sole vertex <=3mmfloor inbothadjacentsamples; planarvelocity afterroottranslation. Foot-centre metric separatelyreported because heel/toe roll movescentres naturally. Maxima include boundaries/roll; notterrainphysics orcontinuousproof.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))

if __name__=='__main__':main()
