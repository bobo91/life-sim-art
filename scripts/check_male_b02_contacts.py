"""B02 paired sole-contact diagnostic: same B01 vertex selection and threshold."""
import argparse,bpy,json,math,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--after',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=Path.cwd();out=r/a.out;assert not out.exists()

def run(file,label,fps):
 bpy.ops.wm.open_mainfile(filepath=str(file),load_ui=False,use_scripts=False);rig=bpy.data.objects['A03_B01_Rig'];sole=bpy.data.objects['M01_shoes_bottom'];sc=bpy.context.scene;ids={s:[v.index for v in sole.data.vertices if v.co.z<.004 and (v.co.x>0 if s=='L' else v.co.x<0)] for s in ['L','R']};result={}
 for name,speed in [('idle',0),('walk',.32/.58),('run',.46/(.4*.75)),('turn',0)]:
  ac=bpy.data.actions[name];rig.animation_data.action=ac;lo,hi=ac.frame_range;duration=(hi-lo)/24;count=round(duration*fps);rows=[]
  for i in range(count+1):
   f=lo+(hi-lo)*i/count;sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update();ev=sole.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();row={'time':i/fps}
   for side,ind in ids.items():
    pts=[ev.matrix_world@me.vertices[j].co for j in ind];row[side]={'center':[sum(v[k] for v in pts)/len(pts) for k in range(3)],'minZ':min(v.z for v in pts)}
   ev.to_mesh_clear();rows.append(row)
  stance=[];vel=[]
  for prev,cur in zip(rows,rows[1:]):
   for side in ids:
    diff=[(cur[side]['center'][k]-prev[side]['center'][k])*fps for k in range(3)];vel.append({'side':side,'velocity':diff})
    if max(prev[side]['minZ'],cur[side]['minZ'])<.003:stance.append({'side':side,'time':cur['time'],'planarFootSpeedMps':math.hypot(diff[0],diff[1]),'residualIfRootTranslatedForwardAtSuggestedSpeedMps':math.hypot(diff[0],diff[1]-speed)})
  result[name]={'sampledFrames':len(rows),'fps':fps,'lowSoleVertices':{s:len(ids[s]) for s in ids},'groundMinimumMeters':min(row[s]['minZ'] for row in rows for s in ids),'stanceSpeedMaxMps':max((s['planarFootSpeedMps'] for s in stance),default=0),'suggestedInPlaceRootSpeedMps':speed,'maxResidualAtSuggestedSpeedMps':max((s['residualIfRootTranslatedForwardAtSuggestedSpeedMps'] for s in stance),default=0),'maxSoleCenterSpeedMps':max(math.sqrt(sum(v*v for v in x['velocity'])) for x in vel),'stanceSamples':stance}
 return result
base=run(r/'build/male-neutral-b01/bind-005/character_b01.blend','B01',24);after=run(r/a.after/'character_b02.blend','B02',24);dense=run(r/a.after/'character_b02.blend','B02',96);result={'schema':'male-b02-paired-foot-contact-1','method':'Same B01 sole bottom vertices per bind side, contact candidate when both adjacent sample minZ<3mm. Main comparison24fps; additional96fps checks between exported keyframes. Inplace stance motion expected for walk/run; turn shouldplant.','before':base,'after':after,'afterDense96fps':dense,'turnReductionPercent':100*(1-after['turn']['stanceSpeedMaxMps']/base['turn']['stanceSpeedMaxMps'])};out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({'turnBefore':base['turn']['stanceSpeedMaxMps'],'turnAfter':after['turn']['stanceSpeedMaxMps'],'turnAfter96fps':dense['turn']['stanceSpeedMaxMps'],'minGround96fps':dense['turn']['groundMinimumMeters'],'reductionPercent':result['turnReductionPercent']}),flush=True)
