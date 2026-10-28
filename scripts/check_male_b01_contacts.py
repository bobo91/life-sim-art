import bpy,json,math
from pathlib import Path
r=Path.cwd();p=r/'build/male-neutral-b01/bind-005';bpy.ops.wm.open_mainfile(filepath=str(p/'character_b01.blend'),load_ui=False,use_scripts=False);rig=bpy.data.objects['A03_B01_Rig'];sole=bpy.data.objects['M01_shoes_bottom'];sc=bpy.context.scene;ids={s:[v.index for v in sole.data.vertices if v.co.z<.004 and (v.co.x>0 if s=='L' else v.co.x<0)] for s in ['L','R']};result={}
for name,frames,expectedSpeed in [('idle',48,0),('walk',24,.32/.58),('run',18,.46/(.4*.75)),('turn',36,0)]:
 rig.animation_data.action=bpy.data.actions[name];rows=[]
 for f in range(frames+1):
  sc.frame_set(1+f);bpy.context.view_layer.update();ev=sole.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();row={'t':f/24}
  for s,ind in ids.items():
   pts=[ev.matrix_world@me.vertices[i].co for i in ind];row[s]={'center':[sum(v[k] for v in pts)/len(pts) for k in range(3)],'minZ':min(v.z for v in pts)}
  ev.to_mesh_clear();rows.append(row)
 samples=[]
 for prev,cur in zip(rows,rows[1:]):
  for s in ['L','R']:
   if max(prev[s]['minZ'],cur[s]['minZ'])<.003:
    diff=[cur[s]['center'][i]-prev[s]['center'][i] for i in range(2)];samples.append({'side':s,'time':cur['t'],'planarFootSpeedMps':math.hypot(*diff)*24,'residualIfRootTranslatedForwardAtSuggestedSpeedMps':math.hypot(diff[0]*24,diff[1]*24-expectedSpeed)})
 result[name]={'sampledFrames':len(rows),'lowSoleVertices':{s:len(ind) for s,ind in ids.items()},'groundMinimumMeters':min(row[s]['minZ'] for row in rows for s in ids),'stanceSpeedMaxMps':max((x['planarFootSpeedMps'] for x in samples),default=0),'suggestedInPlaceRootSpeedMps':expectedSpeed,'maxResidualAtSuggestedSpeedMps':max((x['residualIfRootTranslatedForwardAtSuggestedSpeedMps'] for x in samples),default=0),'stanceSamples':samples}
d={'schema':'male-b01-foot-contact-diagnostic-1','method':'Sole bottom vertices by bind side, 24fps everykey. Contact candidate when min sole z<3mm. Inplace stance speed is expected; forward speed is recipe estimate, not gameplay integration proof. Turn uses no root translation and shows actual sliding.','clips':result};out=r/'build/male-neutral-b01/foot-contact-001.json';out.write_bytes((json.dumps(d,indent=2)+'\n').encode());print(json.dumps({n:{k:v for k,v in c.items() if k!='stanceSamples'} for n,c in result.items()},indent=2))
