import bpy,json,sys
from pathlib import Path
from mathutils import Vector
source=Path(sys.argv[-2]).resolve();out=Path(sys.argv[-1]);bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
rig=bpy.data.objects['RIG-Snow']; bones=[]
for p in rig.pose.bones:
 if any(w in p.name.lower() for w in ['settings','upperarm','eyelid','brow','lips','hand_ik','ik-hand','ik_hand']):
  bones.append({'name':p.name,'loc':list(p.location),'rotMode':p.rotation_mode,'rotation':list(p.rotation_euler),'head':list(p.head),'parent':p.parent.name if p.parent else None,'properties':{k:str(v) for k,v in p.items() if not k.startswith('_')},'constraints':[c.type for c in p.constraints]})
hair=bpy.data.objects['GEO-snow-hair_base'].data;adj=[set() for _ in hair.vertices]
for e in hair.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
left=set(range(len(adj)));components=[]
while left:
 start=next(iter(left));seen={start};q=[start];left.remove(start)
 for i in q:
  for j in adj[i]:
   if j not in seen:seen.add(j);q.append(j);left.discard(j)
 pts=[hair.vertices[i].co for i in seen];components.append({'vertices':len(seen),'min':[min(v[k] for v in pts) for k in range(3)],'max':[max(v[k] for v in pts) for k in range(3)],'indices':sorted(seen)})
objects=[]
for o in bpy.context.scene.objects:
 if o.name.startswith('GEO'):
  objects.append({'name':o.name,'hideRender':o.hide_render,'camera':o.visible_camera,'visible':o.visible_get(),'materials':[s.material.name if s.material else None for s in o.material_slots],'collections':[c.name for c in o.users_collection]})
out.write_text(json.dumps({'bones':bones,'hairComponents':components,'objects':objects},indent=2)+'\n',encoding='utf-8')
print('haircomponents',[(c['vertices'],c['min'],c['max']) for c in components]);print('controlbones',len(bones))
